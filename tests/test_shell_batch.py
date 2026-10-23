"""우클릭 모아서 한 번에 처리(shell_batch) 단위 시험."""
import io
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from docfit_app import shell_batch
from docfit_app.conversion_runner import run_conversion
from pypdf import PdfWriter


class ShellBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()
        self.batch_dir = self.root / "batch_folder"
        self.batch_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_file(self, name: str, content: bytes = b"dummy") -> Path:
        path = self.root / name
        path.write_bytes(content)
        return path

    def test_natural_sort_key(self):
        files = ["file10.hwp", "file2.hwp", "file1.hwp", "file20.hwp", "file3.hwp"]
        sorted_files = sorted(files, key=shell_batch.natural_sort_key)
        self.assertEqual(sorted_files, ["file1.hwp", "file2.hwp", "file3.hwp", "file10.hwp", "file20.hwp"])

    def test_leader_and_followers_simulation(self):
        """대표 1개만 처리하고 추종자는 0으로 종료하며, 대표가 모인 파일 전체를 1회 처리하는지 검증."""
        f1 = self.make_file("doc1.hwpx")
        f2 = self.make_file("doc2.hwpx")
        f3 = self.make_file("doc3.hwpx")

        calls = []

        def mock_runner(files, target, **kwargs):
            calls.append(list(files))
            return [dict(source=f, output=f + ".pdf", status="success", error=None) for f in files]

        # 1. 프로세스 1(대표) 시작 전 파일 요청 작성
        shell_batch.write_request(self.batch_dir, f1)

        # 2. 프로세스 1이 락을 잡음
        lock = shell_batch.BatchLock(self.batch_dir / ".lock")
        self.assertTrue(lock.acquire())

        # 3. 프로세스 2, 3은 락 획득 실패하므로 추종자로서 요청만 남기고 바로 0으로 종료
        code2 = shell_batch.handle_collect(
            "batch_folder",
            [str(f2)],
            "pdf",
            base_dir=self.root,
            runner=mock_runner,
            user_profile=self.root,
        )
        self.assertEqual(code2, 0)

        code3 = shell_batch.handle_collect(
            "batch_folder",
            [str(f3)],
            "pdf",
            base_dir=self.root,
            runner=mock_runner,
            user_profile=self.root,
        )
        self.assertEqual(code3, 0)

        # 추종자들은 runner를 호출하지 않았음
        self.assertEqual(len(calls), 0)

        # 4. 이제 프로세스 1의 락을 해제하고, 대표 프로세스로서 handle_collect를 실행 (f1, f2, f3 모두 모여있음)
        lock.release()

        code1 = shell_batch.handle_collect(
            "batch_folder",
            [],  # 이미 f1, f2, f3의 요청이 파일로 작성되어 있음
            "pdf",
            base_dir=self.root,
            runner=mock_runner,
            quiet_seconds=0.05,
            user_profile=self.root,
        )
        self.assertEqual(code1, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], [str(f1), str(f2), str(f3)])

    def test_quiet_period_1_5_seconds(self):
        """가상 시각을 주입하여 1.5초 정지 후 처리가 완료되는지 검증."""
        f1 = self.make_file("a.hwpx")
        shell_batch.write_request(self.batch_dir, f1)

        sim_time = [0.0]

        def fake_time():
            return sim_time[0]

        def fake_sleep(delta):
            sim_time[0] += delta

        collected = shell_batch.collect_requests(
            self.batch_dir,
            quiet_seconds=1.5,
            max_wait_seconds=30.0,
            time_func=fake_time,
            sleep_func=fake_sleep,
        )
        self.assertEqual(len(collected), 1)
        # 마지막 요청 이후 1.5초가 경과하여 루프를 마쳤는지 확인
        self.assertGreaterEqual(sim_time[0], 1.5)

    def test_late_arrivals_handled_in_next_batch(self):
        """대표가 1차 배치 처리 중 들어온 늦은 요청이 다음 묶음으로 처리되는지 검증."""
        f1 = self.make_file("doc1.hwpx")
        f2 = self.make_file("doc2.hwpx")
        f3 = self.make_file("doc3.hwpx")

        calls = []

        def mock_runner(files, target, **kwargs):
            calls.append(list(files))
            if len(calls) == 1:
                # 1차 배치 실행 도중에 f3 요청이 늦게 도착
                shell_batch.write_request(self.batch_dir, f3)
            return [dict(source=f, output=f + ".pdf", status="success", error=None) for f in files]

        code = shell_batch.handle_collect(
            "batch_folder",
            [str(f1), str(f2)],
            "pdf",
            base_dir=self.root,
            runner=mock_runner,
            quiet_seconds=0.01,
            user_profile=self.root,
        )
        self.assertEqual(code, 0)
        # 총 2번의 배치가 실행됨
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], [str(f1), str(f2)])
        self.assertEqual(calls[1], [str(f3)])
        # 모든 요청 파일이 삭제되었는지 확인
        self.assertEqual(list(self.batch_dir.glob("*.req")), [])

    def test_broken_request_becomes_bad(self):
        """깨진 요청 파일은 .bad 로 변경되고 정상 파일은 계속 처리되는지 검증."""
        f1 = self.make_file("valid.hwpx")
        shell_batch.write_request(self.batch_dir, f1)

        bad_req = self.batch_dir / "broken.req"
        bad_req.write_text("{broken json invalid content...", encoding="utf-8")

        calls = []

        def mock_runner(files, target, **kwargs):
            calls.append(list(files))
            return [dict(source=f, output=f + ".pdf", status="success", error=None) for f in files]

        code = shell_batch.handle_collect(
            "batch_folder",
            [],
            "pdf",
            base_dir=self.root,
            runner=mock_runner,
            quiet_seconds=0.01,
            user_profile=self.root,
        )
        self.assertEqual(code, 0)
        self.assertEqual(calls[0], [str(f1)])
        # 깨진 파일은 .bad 로 변경됨
        self.assertFalse(bad_req.exists())
        self.assertTrue((self.batch_dir / "broken.bad").exists())

    def test_missing_file_excluded(self):
        """실제 존재하지 않는 파일 경로는 목록에서 제외되는지 검증."""
        f_real = self.make_file("exists.hwpx")
        shell_batch.write_request(self.batch_dir, f_real)

        missing_path = self.root / "does_not_exist.hwpx"
        shell_batch.write_request(self.batch_dir, missing_path)

        calls = []

        def mock_runner(files, target, **kwargs):
            calls.append(list(files))
            return [dict(source=f, output=f + ".pdf", status="success", error=None) for f in files]

        code = shell_batch.handle_collect(
            "batch_folder",
            [],
            "pdf",
            base_dir=self.root,
            runner=mock_runner,
            quiet_seconds=0.01,
            user_profile=self.root,
        )
        self.assertEqual(code, 0)
        self.assertEqual(calls[0], [str(f_real)])

    def test_user_profile_security(self):
        """사용자 프로필 디렉토리 외부 파일은 보안상 거부되어 .bad로 처리되는지 검증."""
        allowed_profile = self.root / "user_home"
        allowed_profile.mkdir()
        outside_folder = self.root / "outside"
        outside_folder.mkdir()

        outside_file = outside_folder / "secret.hwpx"
        outside_file.write_bytes(b"data")

        req = shell_batch.write_request(self.batch_dir, outside_file)
        self.assertIsNone(shell_batch.validate_request_file(req, user_profile=allowed_profile))
        self.assertFalse(req.exists())
        self.assertTrue(req.with_suffix(".bad").exists())

    def test_files_outside_user_folder_allowed_by_default(self):
        """기본(허용 폴더 미지정)에서는 사용자 폴더 밖(D: 드라이브·업무 폴더) 파일도 받아들인다."""
        outside = self.root / "outside"
        outside.mkdir()
        target = outside / "보고서.hwpx"
        target.write_bytes(b"data")
        req = shell_batch.write_request(self.batch_dir, target)
        with patch.dict(os.environ, {"USERPROFILE": str(self.root / "user_home")}):
            self.assertEqual(shell_batch.validate_request_file(req), target.resolve())

    def test_stale_lock_from_dead_leader_is_reclaimed(self):
        """대표가 강제 종료되어 남은 잠금(죽은 PID)은 치우고 새 대표가 된다."""
        lock_file = self.batch_dir / ".lock"
        lock_file.write_text("999999999\n0", encoding="utf-8")
        lock = shell_batch.BatchLock(lock_file)
        with patch.object(shell_batch, "_pid_alive", return_value=False):
            self.assertTrue(lock.acquire())
        lock.release()

    def test_live_leader_lock_is_respected(self):
        """살아 있는 대표의 잠금은 건드리지 않는다."""
        lock_file = self.batch_dir / ".lock"
        lock_file.write_text(f"{os.getpid()}\n0", encoding="utf-8")
        self.assertTrue(shell_batch._pid_alive(os.getpid()))
        self.assertFalse(shell_batch.BatchLock(lock_file).acquire())
        self.assertTrue(lock_file.exists())

    def test_max_files_cap_200(self):
        """200개 상한에 도달하면 즉시 수집을 끊고 묶음 처리하는지 검증."""
        files = [self.make_file(f"doc_{i:03d}.hwpx") for i in range(250)]
        for f in files:
            shell_batch.write_request(self.batch_dir, f)

        calls = []

        def mock_runner(batch, target, **kwargs):
            calls.append(len(batch))
            return [dict(source=f, output=f + ".pdf", status="success", error=None) for f in batch]

        code = shell_batch.handle_collect(
            "batch_folder",
            [],
            "pdf",
            base_dir=self.root,
            runner=mock_runner,
            quiet_seconds=0.01,
            max_files=200,
            user_profile=self.root,
        )
        self.assertEqual(code, 0)
        # 250개가 첫 묶음 200개, 둘째 묶음 50개로 처리됨
        self.assertEqual(calls, [200, 50])

    def test_pdfm_actual_merge_without_hwp(self):
        """한/글 COM 없이 실제 PDF 2개를 모아서 PDF 하나로 합치기(pdfm) 시험."""
        pdf1 = self.root / "doc1.pdf"
        w1 = PdfWriter()
        w1.add_blank_page(width=100, height=200)
        with open(pdf1, "wb") as f:
            w1.write(f)

        pdf2 = self.root / "doc2.pdf"
        w2 = PdfWriter()
        w2.add_blank_page(width=100, height=200)
        with open(pdf2, "wb") as f:
            w2.write(f)

        out = io.StringIO()
        code = shell_batch.handle_collect(
            "batch_folder",
            [str(pdf2), str(pdf1)],  # 역순으로 전달
            "pdfm",
            base_dir=self.root,
            runner=run_conversion,
            quiet_seconds=0.01,
            stdout=out,
            user_profile=self.root,
        )
        self.assertEqual(code, 0)
        # 자연 정렬 규칙에 따라 doc1이 첫 파일이 되고 "<첫 파일> 외 1개(합친 PDF).pdf"가 생성됨
        merged_pdf = self.root / "doc1 외 1개(합친 PDF).pdf"
        self.assertTrue(merged_pdf.exists())


if __name__ == "__main__":
    unittest.main()
