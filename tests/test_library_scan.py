import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from docfit_app.library_bridge import LibraryBridgeError
from docfit_app.library_scan import FolderScanService

KLIB = Path(__file__).resolve().parent.parent / "klib" / "target" / "release" / ("klib.exe" if os.name == "nt" else "klib")


def make_tree(base: Path):
    (base / "하위" / "깊은").mkdir(parents=True)
    for rel in ("a.hwpx", "B.HWP", "메모.txt", "하위/c.pdf", "하위/깊은/d.md",
                "무시.exe", "확장자없음", "하위/무시.dll"):
        (base / rel).write_bytes(b"x")
    return sorted(str(base / rel) for rel in ("a.hwpx", "B.HWP", "메모.txt", "하위/c.pdf", "하위/깊은/d.md"))


class OneShotKlib:
    """실제 klib 실행 파일을 `--request-json`으로 부르는 시험용 브리지(파이프는 Windows 전용)."""

    def __init__(self, data_dir):
        self.env = dict(os.environ, KLIB_DATA=str(data_dir))
        self.calls = []

    def available(self):
        return KLIB.is_file()

    def request(self, request):
        self.calls.append(request["cmd"])
        out = subprocess.run([str(KLIB), "--request-json", json.dumps(request, ensure_ascii=False)],
                             env=self.env, capture_output=True, timeout=60, check=True)
        return json.loads(out.stdout.decode("utf-8").strip().splitlines()[-1])


class FakeKlib:
    def __init__(self, scan_error=None):
        self.calls, self.scan_error = [], scan_error

    def available(self):
        return True

    def request(self, request):
        self.calls.append(request)
        if request["cmd"] == "box_scan" and self.scan_error:
            raise self.scan_error
        if request["cmd"] == "box_scan":
            return {"ok": True, "started": True}
        if request["cmd"] == "box_scan_status":
            return {"ok": True, "state": "scanning", "phase": "reconcile", "total": 10, "processed": 4,
                    "added": 3, "updated": 1, "unchanged": 0, "removed": 0}
        if request["cmd"] == "box_scan_cancel":
            return {"ok": True, "cancelling": True}
        raise AssertionError(request)


class FolderScanServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(os.path.realpath(self.temp.name))
        self.src = self.base / "자료"
        self.expected = make_tree(self.src)
        self.fallback_db = self.base / "fallback" / "scan.db"
        self.services = []

    def tearDown(self):
        for service in self.services:
            service.close()
        self.temp.cleanup()

    def python_service(self, bridge_factory=None):
        service = FolderScanService(bridge_factory, fallback_db=self.fallback_db)
        self.services.append(service)
        return service

    def wait_done(self, service, timeout=20):
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = service.status()
            if status["state"] not in ("scanning", "idle"):
                return status
            time.sleep(0.02)
        self.fail("스캔이 끝나지 않음")

    def test_falls_back_to_python_when_klib_missing(self):
        service = self.python_service(lambda: None)
        reply = service.handle({"cmd": "box_scan", "box_id": 7, "path": str(self.src)})
        self.assertEqual((reply["ok"], reply["backend"]), (True, "python"))
        status = self.wait_done(service)
        self.assertEqual((status["state"], status["backend"], status["changed"], status["total"]), ("done", "python", 5, 5))
        self.assertEqual(service.files(7, self.src), self.expected)
        again = service.handle({"cmd": "box_scan", "box_id": 7, "path": str(self.src)})
        self.assertTrue(again["ok"])
        self.assertEqual(self.wait_done(service)["changed"], 0, "증분: 바뀐 파일 없음")

    def test_falls_back_when_klib_connection_fails(self):
        fake = FakeKlib(scan_error=LibraryBridgeError("down"))
        service = self.python_service(lambda: fake)
        reply = service.start(1, str(self.src))
        self.assertEqual(reply["backend"], "python")
        self.assertEqual(self.wait_done(service)["state"], "done")

    def test_uses_klib_when_available_and_polls_status_and_cancel(self):
        fake = FakeKlib()
        service = self.python_service(lambda: fake)
        reply = service.handle({"cmd": "box_scan", "box_id": 3, "path": str(self.src) + os.sep})
        self.assertEqual(reply["backend"], "klib")
        sent = fake.calls[0]
        self.assertEqual((sent["box_id"], sent["path"]), (3, str(self.src)))
        self.assertIn(".hwpx", sent["extensions"])
        status = service.status()
        self.assertEqual((status["backend"], status["processed"], status["total"], status["changed"]), ("klib", 4, 10, 4))
        self.assertTrue(service.cancel()["cancelling"])
        self.assertFalse(self.fallback_db.exists(), "klib를 쓰면 Python 폴백 DB를 만들지 않는다")

    def test_klib_error_is_returned_without_fallback(self):
        class Refuse(FakeKlib):
            def request(self, request):
                return {"ok": False, "message": "이미 폴더 스캔이 진행 중입니다."}
        service = self.python_service(lambda: Refuse())
        reply = service.start(1, str(self.src))
        self.assertFalse(reply["ok"])
        self.assertEqual(service.status()["state"], "idle")

    def test_python_cancel_and_bad_input(self):
        service = self.python_service(None)
        self.assertFalse(service.handle({"cmd": "box_scan", "box_id": "x", "path": str(self.src)})["ok"])
        self.assertFalse(service.handle({"cmd": "box_scan", "box_id": 1, "path": str(self.src / "없음")})["ok"])
        self.assertEqual(service.status()["state"], "idle")
        self.assertEqual(service.cancel(), {"ok": True, "cancelling": False})
        self.assertFalse(service.handle({"cmd": "bogus"})["ok"])

    @unittest.skipUnless(KLIB.is_file(), "klib 실행 파일이 없어 건너뜀(cargo build --release)")
    def test_klib_and_python_paths_list_the_same_files(self):
        data = self.base / "klibdata"
        data.mkdir()
        klib = OneShotKlib(data)
        box = klib.request({"cmd": "box_create", "name": "비교"})["id"]
        via_klib = self.python_service(lambda: klib)
        self.assertEqual(via_klib.start(box, str(self.src))["backend"], "klib")
        klib_files = via_klib.files(box, self.src)
        via_python = self.python_service(lambda: None)
        via_python.start(box, str(self.src))
        self.wait_done(via_python)
        python_files = via_python.files(box, self.src)
        self.assertEqual(klib_files, python_files)
        self.assertEqual(klib_files, self.expected)
        self.assertIn("box_scan_files", klib.calls)
        # 파일을 바꾼 뒤 증분 재스캔도 두 경로가 같은 목록을 낸다.
        (self.src / "a.hwpx").unlink()
        (self.src / "새문서.docx").write_bytes(b"n")
        via_klib.start(box, str(self.src))
        via_python.start(box, str(self.src))
        self.wait_done(via_python)
        self.assertEqual(via_klib.files(box, self.src), via_python.files(box, self.src))
        self.assertIn(str(self.src / "새문서.docx"), via_python.files(box, self.src))
        self.assertNotIn(str(self.src / "a.hwpx"), via_python.files(box, self.src))


class DesktopBridgeRoutingTests(unittest.TestCase):
    def test_library_scan_commands_route_to_folder_scan_service_with_python_fallback(self):
        from desktop_web_ui import DesktopWebBridge

        with tempfile.TemporaryDirectory() as temp:
            base = Path(os.path.realpath(temp))
            src = base / "자료"
            expected = make_tree(src)
            bridge = DesktopWebBridge.__new__(DesktopWebBridge)
            bridge._developer_mode_enabled = lambda: True
            bridge._folder_scan = None
            bridge._library_bridge = type("NoKlib", (), {"available": lambda self: False,
                                                          "request": lambda self, r: self.fail()})()
            from docfit_app import library_scan
            real = library_scan.FolderScanService
            library_scan.FolderScanService = lambda factory: real(factory, fallback_db=base / "f.db")
            try:
                reply = bridge.library({"cmd": "box_scan", "box_id": 2, "path": str(src)})
                self.assertEqual((reply["ok"], reply["backend"]), (True, "python"))
                service = bridge._folder_scan
                service.wait()
                status = bridge.library({"cmd": "box_scan_status"})
                self.assertEqual((status["state"], status["total"]), ("done", len(expected)))
                self.assertEqual(bridge.library({"cmd": "box_scan_files", "box_id": 2, "path": str(src)})["files"], expected)
                self.assertEqual(bridge.library({"cmd": "box_scan_cancel"}), {"ok": True, "cancelling": False})
            finally:
                library_scan.FolderScanService = real
                if bridge._folder_scan:
                    bridge._folder_scan.close()


class BridgeAvailabilityTests(unittest.TestCase):
    def test_available_requires_executable_for_default_pipe_on_windows_only(self):
        from docfit_app.library_bridge import LibraryBridge
        bridge = LibraryBridge(pipe_name="x", executable="missing.exe")
        self.assertFalse(bridge.available())
        bridge = LibraryBridge(pipe_name="x", executable="missing.exe", connector=lambda n: None)
        self.assertTrue(bridge.available())


if __name__ == "__main__":
    unittest.main()
