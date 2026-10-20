"""빈 문서 저장 방지(save_guard) 및 COM 잠금 컨텍스트 단위 시험."""

from __future__ import annotations

from pathlib import Path
import tempfile
import threading
import time
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from docfit_core.save_guard import (
    com_test_lock,
    count_hwpx_nonspace_chars,
    verify_saved_hwpx_not_empty,
)


def _write_test_hwpx(path: Path, texts: list[str]) -> Path:
    body = "".join(
        f'<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>{t}</hp:t></hp:run></hp:p>'
        for t in texts
    )
    sec = f'<hs:sec xmlns:hs="urn:section" xmlns:hp="urn:para">{body}</hs:sec>'.encode("utf-8")
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", b"application/hwp+zip")
        archive.writestr("Contents/header.xml", b"<hh:head xmlns:hh='urn:head'/>")
        archive.writestr("Contents/section0.xml", sec)
    return path


class SaveGuardTests(unittest.TestCase):
    def test_empty_saved_hwpx_raises_runtime_error(self):
        with tempfile.TemporaryDirectory() as folder:
            ref = _write_test_hwpx(Path(folder) / "ref.hwpx", ["□ 추진 배경", " ㅇ 세부 내용입니다."])
            empty = _write_test_hwpx(Path(folder) / "empty.hwpx", ["", "   "])
            self.assertEqual(count_hwpx_nonspace_chars(empty), 0)
            with self.assertRaisesRegex(RuntimeError, "본문 글자 수가 0"):
                verify_saved_hwpx_not_empty(empty, ref)

    def test_truncated_saved_hwpx_raises_runtime_error(self):
        with tempfile.TemporaryDirectory() as folder:
            ref = _write_test_hwpx(
                Path(folder) / "ref.hwpx",
                ["□ 추진 배경과 세부 시행계획 보고서 본문입니다." * 5],
            )
            truncated = _write_test_hwpx(Path(folder) / "truncated.hwpx", ["짧은글"])
            with self.assertRaisesRegex(RuntimeError, "급감"):
                verify_saved_hwpx_not_empty(truncated, ref)

    def test_normal_saved_hwpx_passes(self):
        with tempfile.TemporaryDirectory() as folder:
            ref = _write_test_hwpx(Path(folder) / "ref.hwpx", ["□ 추진 배경", " ㅇ 본문 문장입니다."])
            saved = _write_test_hwpx(Path(folder) / "saved.hwpx", ["□ 추진 배경", "  ㅇ 본문 문장입니다."])
            info = verify_saved_hwpx_not_empty(saved, ref)
            self.assertGreater(info["saved_chars"], 0)
            self.assertEqual(info["saved_chars"], info["reference_chars"])

    def test_com_test_lock_waits_creates_and_cleans_up_on_exception(self):
        with tempfile.TemporaryDirectory() as folder:
            lock_file = Path(folder) / ".com-test.lock"
            lock_file.write_text("OtherAgent 2026-10-20T22:50:00 T1\n", encoding="utf-8")

            def release_soon():
                time.sleep(0.08)
                lock_file.unlink(missing_ok=True)

            releaser = threading.Thread(target=release_soon)
            releaser.start()
            try:
                with com_test_lock(
                    "Gemini",
                    "unit-test",
                    lock_path=lock_file,
                    timeout_sec=2.0,
                    poll_sec=0.02,
                ) as acquired_path:
                    self.assertTrue(acquired_path.is_file())
                    content = acquired_path.read_text(encoding="utf-8")
                    self.assertIn("Gemini", content)
                    self.assertIn("unit-test", content)
                self.assertFalse(lock_file.exists())
            finally:
                releaser.join()

            with self.assertRaises(ValueError):
                with com_test_lock("Gemini", "fail-case", lock_path=lock_file, timeout_sec=1.0):
                    self.assertTrue(lock_file.is_file())
                    raise ValueError("simulated failure")
            self.assertFalse(lock_file.exists())


if __name__ == "__main__":
    unittest.main()

