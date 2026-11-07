"""자료함 자료 열기(더블클릭) 시험. 실제로 파일을 열지 않도록 가짜 실행기만 쓴다."""

import os
import tempfile
import unittest
from unittest.mock import patch

from docfit_app.library_bridge import LibraryOpenError, is_risky_open_path, open_library_item


class FakeOpener:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def __call__(self, path):
        self.calls.append(path)
        if self.error:
            raise self.error


class OpenLibraryItemTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.doc = os.path.join(self.tmp.name, "보고서.hwpx")
        self.exe = os.path.join(self.tmp.name, "setup.exe")
        for path in (self.doc, self.exe):
            with open(path, "wb") as f:
                f.write(b"x")

    def _code(self, item, **kwargs):
        with self.assertRaises(LibraryOpenError) as ctx:
            open_library_item(item, opener=FakeOpener(), browser=FakeOpener(), **kwargs)
        return ctx.exception.code

    def test_opens_file_and_folder_with_opener(self):
        opener = FakeOpener()
        self.assertTrue(open_library_item({"kind": "file", "source_path": self.doc}, opener=opener))
        self.assertTrue(open_library_item({"kind": "folder", "source_path": self.tmp.name}, opener=opener))
        self.assertEqual(opener.calls, [self.doc, self.tmp.name])

    def test_opens_web_link_with_browser_only(self):
        opener, browser = FakeOpener(), FakeOpener()
        browser_calls = []
        self.assertTrue(open_library_item({"kind": "link", "source_path": "https://example.com/a"},
                                          opener=opener, browser=lambda url: browser_calls.append(url) or True))
        self.assertEqual(browser_calls, ["https://example.com/a"])
        self.assertEqual(opener.calls, [])
        self.assertEqual(self._code({"kind": "link", "source_path": "javascript:alert(1)"}), "BLOCKED")
        self.assertEqual(self._code({"kind": "file", "source_path": "file:///C:/x.txt"}), "BLOCKED")

    def test_failure_codes(self):
        self.assertEqual(self._code({"kind": "file", "source_path": ""}), "NO_SOURCE")
        self.assertEqual(self._code({"kind": "text", "source_path": None}), "NO_SOURCE")
        self.assertEqual(self._code({"kind": "file", "source_path": self.doc + "\nC:/evil.exe"}), "INVALID_PATH")
        self.assertEqual(self._code({"kind": "file", "source_path": os.path.join(self.tmp.name, "없음.pdf")}), "SOURCE_MISSING")

    def test_executable_needs_confirmation_and_is_blocked_when_unregistered(self):
        self.assertEqual(self._code({"kind": "file", "source_path": self.exe}), "CONFIRM_REQUIRED")
        self.assertEqual(self._code({"kind": "file", "source_path": self.exe, "confirmed": True}, allow_risky=False), "BLOCKED")
        opener = FakeOpener()
        open_library_item({"kind": "file", "source_path": self.exe, "confirmed": True}, opener=opener)
        self.assertEqual(opener.calls, [self.exe])
        self.assertTrue(is_risky_open_path("C:/a/B.PS1"))
        self.assertTrue(is_risky_open_path("C:/a/run.bat. "))
        self.assertFalse(is_risky_open_path("C:/a/문서.hwp"))

    def test_no_association_reported_as_no_app(self):
        error = OSError("No application is associated")
        error.winerror = 1155
        with self.assertRaises(LibraryOpenError) as ctx:
            open_library_item({"kind": "file", "source_path": self.doc}, opener=FakeOpener(error))
        self.assertEqual(ctx.exception.code, "NO_APP")


class DesktopOpenItemTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.doc = os.path.join(self.tmp.name, "붙임1.pdf")
        self.exe = os.path.join(self.tmp.name, "tool.exe")
        for path in (self.doc, self.exe):
            with open(path, "wb") as f:
                f.write(b"x")

    def _bridge(self, stored):
        from desktop_web_ui import DesktopWebBridge

        requests = []

        class FakeLibrary:
            def request(self, request):
                requests.append(request)
                return stored

        bridge = DesktopWebBridge.__new__(DesktopWebBridge)
        bridge._library_bridge = FakeLibrary()
        bridge._developer_mode_enabled = lambda: True
        bridge._library_opener = FakeOpener()
        bridge._library_browser = FakeOpener()
        return bridge, requests

    def test_open_item_uses_stored_path_not_client_path(self):
        bridge, requests = self._bridge({"ok": True, "id": 7, "kind": "file", "source_path": self.doc})
        result = bridge.library({"cmd": "open_item", "item_id": 7, "kind": "file", "source_path": "C:/다른/경로.exe"})
        self.assertEqual(result, {"ok": True, "opened": True, "path": self.doc})
        self.assertEqual(requests, [{"cmd": "item_get", "id": 7}])
        self.assertEqual(bridge._library_opener.calls, [self.doc])

    def test_open_item_reports_reason_and_path(self):
        missing = os.path.join(self.tmp.name, "옮겨진.hwp")
        bridge, _ = self._bridge({"ok": True, "id": 3, "kind": "file", "source_path": missing})
        result = bridge.library({"cmd": "open_item", "item_id": "3"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "SOURCE_MISSING")
        self.assertEqual(result["path"], missing)
        self.assertEqual(bridge._library_opener.calls, [])

    def test_open_item_unknown_item_is_not_registered(self):
        bridge, _ = self._bridge({"ok": False, "message": "해당 자료 항목을 찾을 수 없습니다."})
        result = bridge.library({"cmd": "open_item", "item_id": 99, "source_path": self.doc})
        self.assertEqual(result["code"], "NOT_REGISTERED")
        self.assertEqual(bridge._library_opener.calls, [])

    def test_registered_executable_needs_confirmation(self):
        bridge, _ = self._bridge({"ok": True, "id": 5, "kind": "file", "source_path": self.exe})
        self.assertEqual(bridge.library({"cmd": "open_item", "item_id": 5})["code"], "CONFIRM_REQUIRED")
        self.assertTrue(bridge.library({"cmd": "open_item", "item_id": 5, "confirmed": True})["ok"])
        self.assertEqual(bridge._library_opener.calls, [self.exe])

    def test_unregistered_path_opens_folder_but_blocks_executable(self):
        bridge, requests = self._bridge({"ok": True})
        self.assertTrue(bridge.library({"cmd": "open_item", "kind": "folder", "source_path": self.tmp.name})["ok"])
        blocked = bridge.library({"cmd": "open_item", "kind": "file", "source_path": self.exe, "confirmed": True})
        self.assertEqual(blocked["code"], "BLOCKED")
        self.assertEqual(requests, [])
        self.assertEqual(bridge._library_opener.calls, [self.tmp.name])

    def test_open_item_requires_developer_mode(self):
        bridge, _ = self._bridge({"ok": True})
        bridge._developer_mode_enabled = lambda: False
        with patch("os.startfile", side_effect=AssertionError, create=True):
            self.assertEqual(bridge.library({"cmd": "open_item", "item_id": 1})["code"], "DEVELOPER_MODE_REQUIRED")


if __name__ == "__main__":
    unittest.main()
