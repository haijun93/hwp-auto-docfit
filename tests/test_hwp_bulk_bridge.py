"""HWP → HWPX 일괄 변환 명령(2.0.7): 입력 검사, 진행 상태, 암호 비우기."""
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from desktop_web_ui import DesktopWebBridge, _BrowserApi


class HwpBulkBridgeTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.gui = Mock(files=[], running=False)
        self.bridge = DesktopWebBridge(self.gui)
        self.bridge._tk = Mock(side_effect=lambda callback, **kwargs: callback())

    def tearDown(self):
        self.folder.cleanup()

    def test_rejects_bad_input(self):
        for payload in ({}, {"roots": []}, {"roots": ["relative"]}, {"roots": [str(self.root / "없음")]},
                        {"roots": [str(self.root)], "passwords": [""]}, {"roots": [str(self.root)], "passwords": "pw"}):
            result = self.bridge.hwp_bulk("start", payload)
            self.assertFalse(result["ok"], payload)
        self.gui.running = True
        self.assertIn("다른 문서 작업", self.bridge.hwp_bulk("start", {"roots": [str(self.root)]})["message"])
        self.assertFalse(self.bridge.hwp_bulk("unknown")["ok"])

    def test_start_runs_in_background_and_clears_passwords(self):
        seen, finished = {}, threading.Event()

        def fake_run(roots, **kwargs):
            seen.update(roots=roots, passwords=list(kwargs["passwords"]), recursive=kwargs["recursive"])
            kwargs["state"].phase = "done"
            finished.set()
        passwords = ["pw1"]
        with patch("docfit_core.hwp_bulk.run_bulk", side_effect=fake_run):
            result = self.bridge.hwp_bulk("start", {"roots": [str(self.root)], "passwords": passwords,
                                                    "recursive": False})
            self.assertTrue(result["ok"])
            self.assertTrue(finished.wait(5))
        self.assertEqual(seen["roots"], [self.root.resolve()])
        self.assertEqual((seen["passwords"], seen["recursive"]), (["pw1"], False))
        for _ in range(50):
            if not passwords:
                break
            threading.Event().wait(0.05)
        self.assertEqual(passwords, [])  # 작업이 끝나면 암호를 버린다
        self.assertEqual(self.bridge.hwp_bulk("status")["bulk"]["phase"], "done")
        self.assertNotIn("pw1", repr(self.bridge.hwp_bulk("status")))

    def test_drives_and_browser_exposure(self):
        with patch("docfit_core.hwp_bulk.local_drives", return_value=["C:\\"]):
            self.assertEqual(self.bridge.hwp_bulk("drives")["drives"], ["C:\\"])
        self.assertTrue(callable(getattr(_BrowserApi(self.bridge), "hwp_bulk")))


if __name__ == "__main__":
    unittest.main()
