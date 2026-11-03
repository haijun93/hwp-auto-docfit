"""타임머신 본문 색인 라이프사이클(진행 표시, 취소, 경합 동기화) 시험."""
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

from docfit_app.timemachine_service import TimemachineService


class FakeAgent:
    def __init__(self):
        self.settings = {"timeline_roots": [], "timeline_mtime_only": False}

    def running(self):
        return False

    def status_file(self):
        return None

    def request(self, command, **payload):
        if command == "settings_set":
            self.settings = dict(payload.get("settings", {}))
        return {"ok": True, "settings": dict(self.settings)}


class StubResult:
    seen = written = removed = 0
    errors = []


def stub_scanner(store, roots, rules, progress=None):
    return StubResult()


class DelayableFakeIndexer:
    def __init__(self, result=None):
        self.calls = []
        self.enter_events = {}    # call_index -> threading.Event
        self.release_events = {}  # call_index -> threading.Event
        self.result = result if result is not None else {"indexed": True, "error": False}

    def index_file(self, path):
        idx = len(self.calls)
        self.calls.append(path)
        if idx in self.enter_events:
            self.enter_events[idx].set()
        if idx in self.release_events:
            self.release_events[idx].wait(timeout=2.0)
        return dict(self.result)


class TimemachineContentIndexLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp.name)
        self.root = self.temp_path / "문서"
        self.root.mkdir()
        self.settings = self.temp_path / "설정"
        self.agent = FakeAgent()
        self.service = TimemachineService(
            self.settings,
            db_path=self.temp_path / "timeline.db",
            agent=self.agent,
            opener=lambda p: None,
            revealer=lambda p: None,
            scanner=stub_scanner,
            thumb_dir=self.temp_path / "thumbs",
        )
        self.service.command("settings_set", {
            "roots": [str(self.root)],
            "time_mode": "max",
            "enabled": True,
        })

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def test_normal_completion_reports_final_counts(self):
        for i in range(1, 4):
            (self.root / f"file_{i}.txt").write_text(f"content {i}", encoding="utf-8")

        fake = DelayableFakeIndexer()
        self.service.content_index.index_file = fake.index_file

        started = self.service.command("content_index_all")
        self.assertTrue(started["ok"])

        worker = self.service._content_thread
        self.assertIsNotNone(worker)
        worker.join(timeout=2.0)
        self.assertFalse(worker.is_alive())

        status = self.service.command("content_index_status")
        self.assertFalse(status["running"])
        self.assertFalse(status["cancelled"])
        self.assertEqual(status["seen"], 3)
        self.assertEqual(status["indexed"], 3)
        self.assertEqual(status["errors"], 0)
        self.assertIsNotNone(status["finished_at"])
        self.assertIsNotNone(status["started_at"])
        self.assertGreaterEqual(status["finished_at"], status["started_at"])
        self.assertEqual(len(fake.calls), 3)

    def test_empty_folder_finishes_with_zero_counts(self):
        fake = DelayableFakeIndexer()
        self.service.content_index.index_file = fake.index_file

        started = self.service.command("content_index_all")
        self.assertTrue(started["ok"])

        worker = self.service._content_thread
        self.assertIsNotNone(worker)
        worker.join(timeout=2.0)
        self.assertFalse(worker.is_alive())

        status = self.service.command("content_index_status")
        self.assertFalse(status["running"])
        self.assertFalse(status["cancelled"])
        self.assertEqual(status["seen"], 0)
        self.assertEqual(status["indexed"], 0)
        self.assertEqual(status["errors"], 0)
        self.assertIsNotNone(status["finished_at"])
        self.assertEqual(len(fake.calls), 0)

    def test_progress_increments_per_completed_file(self):
        f1 = self.root / "file_1.txt"
        f2 = self.root / "file_2.txt"
        f1.write_text("one", encoding="utf-8")
        f2.write_text("two", encoding="utf-8")

        f1_enter, f1_release = threading.Event(), threading.Event()
        f2_enter, f2_release = threading.Event(), threading.Event()

        fake = DelayableFakeIndexer()
        fake.enter_events[0] = f1_enter
        fake.release_events[0] = f1_release
        fake.enter_events[1] = f2_enter
        fake.release_events[1] = f2_release
        self.service.content_index.index_file = fake.index_file

        started = self.service.command("content_index_all")
        self.assertTrue(started["ok"])

        self.assertTrue(f1_enter.wait(timeout=2.0))
        st_pre = self.service.command("content_index_status")
        self.assertEqual(st_pre["seen"], 0)
        self.assertEqual(st_pre["indexed"], 0)
        self.assertTrue(st_pre["running"])

        f1_release.set()

        self.assertTrue(f2_enter.wait(timeout=2.0))
        st_mid = self.service.command("content_index_status")
        self.assertEqual(st_mid["seen"], 1)
        self.assertEqual(st_mid["indexed"], 1)
        self.assertEqual(st_mid["errors"], 0)
        self.assertTrue(st_mid["running"])
        self.assertGreater(st_mid["seen"], st_pre["seen"])

        f2_release.set()

        worker = self.service._content_thread
        worker.join(timeout=2.0)
        self.assertFalse(worker.is_alive())

        st_post = self.service.command("content_index_status")
        self.assertEqual(st_post["seen"], 2)
        self.assertEqual(st_post["indexed"], 2)
        self.assertEqual(st_post["errors"], 0)
        self.assertFalse(st_post["running"])
        self.assertGreater(st_post["seen"], st_mid["seen"])

    def test_cancel_during_index_finishes_with_current_file_counted(self):
        with self.subTest("cancel_async_finishes_with_current_file_counted"):
            f1 = self.root / "file_1.txt"
            f2 = self.root / "file_2.txt"
            f1.write_text("one", encoding="utf-8")
            f2.write_text("two", encoding="utf-8")

            f1_enter, f1_release = threading.Event(), threading.Event()
            fake = DelayableFakeIndexer()
            fake.enter_events[0] = f1_enter
            fake.release_events[0] = f1_release
            self.service.content_index.index_file = fake.index_file

            started = self.service.command("content_index_all")
            self.assertTrue(started["ok"])

            self.assertTrue(f1_enter.wait(timeout=2.0))

            cancel_res = self.service.command("content_index_cancel")
            self.assertTrue(cancel_res["ok"])

            f1_release.set()

            worker = self.service._content_thread
            worker.join(timeout=2.0)
            self.assertFalse(worker.is_alive())

            status = self.service.command("content_index_status")
            self.assertFalse(status["running"])
            self.assertTrue(status["cancelled"])
            self.assertEqual(status["seen"], 1)
            self.assertEqual(status["indexed"], 1)
            self.assertEqual(status["errors"], 0)
            self.assertIsNotNone(status["finished_at"])

        with self.subTest("slow_indexer_cancel_timeout_reports_incomplete"):
            sub_root = self.temp_path / "문서_지연"
            sub_root.mkdir()
            (sub_root / "slow_file_1.txt").write_text("slow 1", encoding="utf-8")
            (sub_root / "slow_file_2.txt").write_text("slow 2", encoding="utf-8")
            sub_settings = self.temp_path / "설정_지연"

            service_slow = TimemachineService(
                sub_settings,
                db_path=self.temp_path / "timeline_slow.db",
                agent=self.agent,
                opener=lambda p: None,
                revealer=lambda p: None,
                scanner=stub_scanner,
                thumb_dir=self.temp_path / "thumbs_slow",
            )
            try:
                service_slow.command("settings_set", {
                    "roots": [str(sub_root)],
                    "time_mode": "max",
                    "enabled": True,
                })
                slow_enter, slow_release = threading.Event(), threading.Event()
                fake_slow = DelayableFakeIndexer()
                fake_slow.enter_events[0] = slow_enter
                fake_slow.release_events[0] = slow_release
                service_slow.content_index.index_file = fake_slow.index_file

                started_slow = service_slow.command("content_index_all")
                self.assertTrue(started_slow["ok"])
                self.assertTrue(slow_enter.wait(timeout=2.0))

                # 인덱서가 블로킹된 상태에서 timeout=0.05로 취소 대기 -> 타임아웃 미완료 반환 확인
                cancel_res = service_slow.cancel_content_index(wait=True, timeout=0.05)
                self.assertFalse(cancel_res["ok"])
                self.assertEqual(cancel_res.get("code"), "TM_CANCEL_TIMEOUT")
                self.assertTrue(cancel_res["running"])

                worker = service_slow._content_thread
                self.assertIsNotNone(worker)
                self.assertTrue(worker.is_alive())

                # 느린 인덱서 해제 후 2초 이내 정상 종료 확인
                slow_release.set()
                worker.join(timeout=2.0)
                self.assertFalse(worker.is_alive())

                st = service_slow.command("content_index_status")
                self.assertFalse(st["running"])
                self.assertTrue(st["cancelled"])
                self.assertEqual(st["seen"], 1)
                self.assertEqual(st["indexed"], 1)
                self.assertEqual(st["errors"], 0)
                self.assertIsNotNone(st["finished_at"])
            finally:
                service_slow.close()

    def test_cancel_does_not_process_next_file(self):
        with self.subTest("cancel_does_not_index_subsequent_files"):
            for i in range(1, 4):
                (self.root / f"file_{i}.txt").write_text(f"text {i}", encoding="utf-8")

            f1_enter, f1_release = threading.Event(), threading.Event()
            fake = DelayableFakeIndexer()
            fake.enter_events[0] = f1_enter
            fake.release_events[0] = f1_release
            self.service.content_index.index_file = fake.index_file

            self.service.command("content_index_all")
            self.assertTrue(f1_enter.wait(timeout=2.0))

            self.service.command("content_index_cancel")
            f1_release.set()

            worker = self.service._content_thread
            worker.join(timeout=2.0)
            self.assertFalse(worker.is_alive())

            status = self.service.command("content_index_status")
            self.assertFalse(status["running"])
            self.assertTrue(status["cancelled"])

            self.assertEqual(len(fake.calls), 1)
            unprocessed_calls = len(fake.calls[1:])
            self.assertEqual(unprocessed_calls, 0)
            self.assertEqual(status["errors"], 0)
            self.assertEqual(status["seen"], 1)

        with self.subTest("cancel_does_not_clean_skip_file"):
            sub_root = self.temp_path / "문서_스킵"
            sub_root.mkdir()
            (sub_root / "01_normal.txt").write_text("normal", encoding="utf-8")
            (sub_root / "~$02_temp.txt").write_text("skip me", encoding="utf-8")
            (sub_root / "03_normal.txt").write_text("later", encoding="utf-8")
            sub_settings = self.temp_path / "설정_스킵"

            service_skip = TimemachineService(
                sub_settings,
                db_path=self.temp_path / "timeline_skip.db",
                agent=self.agent,
                opener=lambda p: None,
                revealer=lambda p: None,
                scanner=stub_scanner,
                thumb_dir=self.temp_path / "thumbs_skip",
            )
            try:
                service_skip.command("settings_set", {
                    "roots": [str(sub_root)],
                    "time_mode": "max",
                    "enabled": True,
                })
                f1_enter, f1_release = threading.Event(), threading.Event()
                fake_skip = DelayableFakeIndexer()
                fake_skip.enter_events[0] = f1_enter
                fake_skip.release_events[0] = f1_release
                service_skip.content_index.index_file = fake_skip.index_file

                removed_paths = []
                orig_remove = service_skip.content_index.remove_file
                service_skip.content_index.remove_file = lambda p: (removed_paths.append(p), orig_remove(p))[1]

                service_skip.command("content_index_all")
                self.assertTrue(f1_enter.wait(timeout=2.0))

                service_skip.command("content_index_cancel")
                f1_release.set()

                worker = service_skip._content_thread
                worker.join(timeout=2.0)
                self.assertFalse(worker.is_alive())

                status = service_skip.command("content_index_status")
                self.assertFalse(status["running"])
                self.assertTrue(status["cancelled"])

                # 첫 파일만 인덱싱되었고, 이후 skip_file에 대한 remove_file도 호출되지 않아야 함
                self.assertEqual(len(fake_skip.calls), 1)
                self.assertEqual(len(removed_paths), 0)
                self.assertEqual(status["errors"], 0)
                self.assertEqual(status["seen"], 1)
            finally:
                service_skip.close()

    def test_cancel_racing_with_completion_keeps_terminal_state_consistent(self):
        # 서브케이스 1: 취소가 terminal commit 전에 선형화된 경우 (cancelled=True)
        with self.subTest("cancel_before_terminal_commit"):
            f1 = self.root / "race_file_1.txt"
            f1.write_text("race 1", encoding="utf-8")

            fake1 = DelayableFakeIndexer()
            self.service.content_index.index_file = fake1.index_file

            about_to_finish = threading.Event()
            cancel_issued = threading.Event()

            original_finish = self.service._finish_content_index
            def hooked_finish(cancel_event):
                about_to_finish.set()
                cancel_issued.wait(timeout=2.0)
                return original_finish(cancel_event)

            self.service._finish_content_index = hooked_finish

            self.service.command("content_index_all")
            self.assertTrue(about_to_finish.wait(timeout=2.0))

            cancel_res = self.service.cancel_content_index(wait=False)
            self.assertTrue(cancel_res["ok"])
            cancel_issued.set()

            worker = self.service._content_thread
            worker.join(timeout=2.0)
            self.assertFalse(worker.is_alive())

            st = self.service.command("content_index_status")
            self.assertFalse(st["running"])
            self.assertTrue(st["cancelled"])
            self.assertIsNotNone(st["finished_at"])
            self.assertEqual(st["seen"], len(fake1.calls))
            self.assertEqual(st["indexed"], len(fake1.calls))
            self.assertEqual(st["errors"], 0)

        # 서브케이스 2: 완료가 먼저 terminal commit된 경우 (cancelled=False)
        with self.subTest("commit_before_cancel"):
            sub_root = self.temp_path / "문서_격리"
            sub_root.mkdir()
            (sub_root / "race_file_2.txt").write_text("race 2", encoding="utf-8")
            sub_settings = self.temp_path / "설정_격리"

            service2 = TimemachineService(
                sub_settings,
                db_path=self.temp_path / "timeline2.db",
                agent=self.agent,
                opener=lambda p: None,
                revealer=lambda p: None,
                scanner=stub_scanner,
                thumb_dir=self.temp_path / "thumbs2",
            )
            try:
                service2.command("settings_set", {
                    "roots": [str(sub_root)],
                    "time_mode": "max",
                    "enabled": True,
                })
                fake2 = DelayableFakeIndexer()
                service2.content_index.index_file = fake2.index_file

                finish_committed = threading.Event()
                original_finish2 = service2._finish_content_index
                def hooked_finish2(cancel_event):
                    res = original_finish2(cancel_event)
                    finish_committed.set()
                    return res

                service2._finish_content_index = hooked_finish2

                service2.command("content_index_all")
                self.assertTrue(finish_committed.wait(timeout=2.0))

                cancel_res2 = service2.cancel_content_index(wait=True)
                self.assertTrue(cancel_res2["ok"])

                st2 = service2.command("content_index_status")
                self.assertFalse(st2["running"])
                self.assertFalse(st2["cancelled"])
                self.assertIsNotNone(st2["finished_at"])
                self.assertEqual(st2["seen"], len(fake2.calls))
                self.assertEqual(st2["indexed"], len(fake2.calls))
                self.assertEqual(st2["errors"], 0)
            finally:
                service2.close()


if __name__ == "__main__":
    unittest.main()
