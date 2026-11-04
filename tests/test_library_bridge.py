import json
import os
import tempfile
import unittest
from unittest.mock import patch

from docfit_app.library_bridge import ALLOWED_COMMANDS, LibraryBridge, LibraryBridgeError


class FakePipe:
    def __init__(self, response):
        self.response = response
        self.written = b""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def write(self, data):
        self.written += data
        return len(data)

    def flush(self):
        pass

    def readline(self, _limit):
        return self.response


class LibraryBridgeTests(unittest.TestCase):
    def test_passes_request_and_returns_response(self):
        pipe = FakePipe(b'{"ok":true,"boxes":[]}\n')
        bridge = LibraryBridge(pipe_name="fake", connector=lambda _name: pipe)
        request = {"cmd": "box_list"}
        self.assertEqual(bridge.request(request), {"ok": True, "boxes": []})
        self.assertEqual(pipe.written, json.dumps(request, separators=(",", ":")).encode() + b"\n")

    def test_starts_klib_and_retries_connection(self):
        with tempfile.TemporaryDirectory() as root:
            executable = os.path.join(root, "klib.exe")
            open(executable, "wb").close()
            attempts = []
            pipe = FakePipe(b'{"ok":true}\n')

            def connect(_name):
                attempts.append(1)
                if len(attempts) == 1:
                    raise OSError("not ready")
                return pipe

            launched = []
            bridge = LibraryBridge(pipe_name="fake", executable=executable, test_root="isolated",
                                   connector=connect, popen=lambda *a, **kw: launched.append((a, kw)),
                                   retries=3, retry_delay=0)
            self.assertEqual(bridge.request({"cmd": "ping"}), {"ok": True})
            self.assertEqual(len(attempts), 2)
            self.assertEqual(launched[0][1]["env"]["KLIB_TEST_ROOT"], "isolated")

    def test_pipe_error_is_returned_as_bridge_error(self):
        bridge = LibraryBridge(pipe_name="fake", connector=lambda _name: (_ for _ in ()).throw(OSError("down")),
                               executable="missing.exe", retries=2, retry_delay=0)
        with self.assertRaises(LibraryBridgeError):
            bridge.request({"cmd": "box_list"})

    def test_rejects_unknown_and_oversized_requests_before_connect(self):
        calls = []
        bridge = LibraryBridge(pipe_name="fake", connector=lambda _name: calls.append(1))
        with self.assertRaises(LibraryBridgeError):
            bridge.request({"cmd": "quit"})
        with self.assertRaises(LibraryBridgeError):
            bridge.request({"cmd": "item_add", "content": "x" * (64 * 1024)})
        self.assertEqual(calls, [])
        self.assertIn("item_add", ALLOWED_COMMANDS)

    def test_disabled_flag_has_no_pipe_or_process_side_effect(self):
        from desktop_web_ui import DesktopWebBridge

        bridge = DesktopWebBridge.__new__(DesktopWebBridge)
        bridge._library_bridge = None
        bridge._developer_mode_enabled = lambda: False
        with patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}), \
             patch("docfit_app.library_bridge._open_pipe", side_effect=AssertionError), \
             patch("subprocess.Popen", side_effect=AssertionError):
            result = bridge.library({"cmd": "box_list"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "DEVELOPER_MODE_REQUIRED")
        self.assertIsNone(bridge._library_bridge)

    def _drop_bridge(self, responses, *, developer_mode=True):
        from desktop_web_ui import DesktopWebBridge

        requests = []
        queue = list(responses)

        class FakeLibrary:
            def request(self, request):
                requests.append(request)
                return queue.pop(0) if queue else {"ok": True}

        bridge = DesktopWebBridge.__new__(DesktopWebBridge)
        bridge._library_bridge = FakeLibrary()
        bridge._developer_mode_enabled = lambda: developer_mode
        return bridge, requests

    def test_library_drop_adds_file_and_folder_by_quadrant(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}):
            file_path = os.path.join(root, "한글 문서.txt")
            folder_path = os.path.join(root, "자료 폴더")
            open(file_path, "wb").close()
            os.mkdir(folder_path)
            denied, _ = self._drop_bridge([], developer_mode=False)
            self.assertEqual(denied.library_drop([file_path], 0.25, 0.25, 7)["code"], "DEVELOPER_MODE_REQUIRED")
            bridge, requests = self._drop_bridge([{"ok": True}, {"ok": True}])
            first = bridge.library_drop([file_path], 0.25, 0.25, 7)
            second = bridge.library_drop(folder_path, 0.5, 0.5, 7)
            self.assertTrue(first["ok"])
            self.assertTrue(second["ok"])
            self.assertEqual(len(first["added"]) + len(second["added"]), 2)
            self.assertEqual(requests[0], {
                "cmd": "item_add", "box_id": 7, "kind": "file", "source_path": file_path,
                "display_name": "한글 문서.txt", "space": "core", "x": 0.25, "y": 0.25})
            self.assertEqual(requests[1], {
                "cmd": "item_add", "box_id": 7, "kind": "folder", "source_path": folder_path,
                "display_name": "자료 폴더", "space": "temp", "x": 0.5, "y": 0.5})

    def test_library_drop_maps_remaining_quadrants(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}):
            for x, y, space in ((0.75, 0.25, "basis"), (0.25, 0.75, "reference")):
                bridge, requests = self._drop_bridge([{"ok": True}])
                bridge.library_drop([root], x, y, 1)
                self.assertEqual(requests[0]["space"], space)

    def test_library_drop_skips_missing_and_duplicate_paths(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}):
            file_path = os.path.join(root, "a.txt")
            open(file_path, "wb").close()
            missing = os.path.join(root, "없는파일.txt")
            bridge, requests = self._drop_bridge([{"ok": True}])
            result = bridge.library_drop([file_path, missing, file_path.upper()], 0.1, 0.1, 1)
            self.assertFalse(result["ok"])
            self.assertEqual(len(requests), 1)
            self.assertEqual(len(result["failed"]), 1)
            self.assertEqual(result["failed"][0]["path"], missing)
            self.assertEqual(len(result["skipped"]), 1)
            self.assertEqual(len(result["added"]), 1)

    def test_library_drop_continues_after_item_add_error(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}):
            first = os.path.join(root, "a.txt")
            second = os.path.join(root, "b.txt")
            open(first, "wb").close()
            open(second, "wb").close()
            bridge, requests = self._drop_bridge([{"ok": False, "message": "오류"}, {"ok": True}])
            result = bridge.library_drop([first, second], 0.9, 0.9, 2)
            self.assertFalse(result["ok"])
            self.assertEqual(len(requests), 2)
            self.assertEqual(len(result["added"]), 1)
            self.assertEqual(result["failed"], [{"path": first, "message": "오류"}])

    def test_library_drop_rejects_invalid_coordinates_and_box_id(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}):
            paths = [root]
            bridge, requests = self._drop_bridge([])
            for x, y, box in ((float("nan"), 0.1, 1), (0.1, float("inf"), 1), ("abc", 0.1, 1),
                              (0.1, 0.1, ""), (0.1, 0.1, None)):
                self.assertFalse(bridge.library_drop(paths, x, y, box)["ok"])
            self.assertEqual(requests, [])
            self.assertEqual(paths, [root])

    def test_library_drop_normalized_board_coordinates_pass_through(self):
        # space 생략: x,y는 보드 전체 0~1 정규화 좌표. 사분면만 판정(0.5는 오른쪽/아래)하고 값은 그대로 전달.
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}):
            cases = ((0.0, 0.0, "core"), (0.49, 0.49, "core"), (0.5, 0.0, "basis"),
                     (1.0, 0.25, "basis"), (0.1, 0.5, "reference"), (0.5, 1.0, "temp"))
            for x, y, space in cases:
                bridge, requests = self._drop_bridge([{"ok": True}])
                bridge.library_drop([root], x, y, 3)
                self.assertEqual((requests[0]["space"], requests[0]["x"], requests[0]["y"]), (space, x, y))
            bridge, requests = self._drop_bridge([])
            for x, y in ((-0.1, 0.5), (0.5, 1.1), (100, 50)):
                self.assertFalse(bridge.library_drop([root], x, y, 1)["ok"])
            self.assertEqual(requests, [])

    def test_library_drop_local_pixel_coordinates_with_space(self):
        # space 지정: x,y는 해당 사분면 캔버스의 로컬 픽셀 좌표(globalToLocal)이며 그대로 item_add로 전달.
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}):
            for space in ("core", "basis", "reference", "temp"):
                bridge, requests = self._drop_bridge([{"ok": True}])
                self.assertTrue(bridge.library_drop([root], 312.5, 140, 1, space)["ok"])
                self.assertEqual((requests[0]["space"], requests[0]["x"], requests[0]["y"]), (space, 312.5, 140.0))
            bridge, requests = self._drop_bridge([])
            for x, y, space in ((-1, 5, "core"), (5, float("nan"), "core"), (5, 5, "bogus")):
                self.assertFalse(bridge.library_drop([root], x, y, 1, space)["ok"])
            self.assertEqual(requests, [])

    def test_library_drop_box_id_converted_to_int(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}):
            for box in ("7", " 7 ", 7):
                bridge, requests = self._drop_bridge([{"ok": True}])
                bridge.library_drop([root], 0.1, 0.1, box)
                self.assertEqual(requests[0]["box_id"], 7)
                self.assertIs(type(requests[0]["box_id"]), int)
            bridge, requests = self._drop_bridge([])
            for box in ("", "  ", "abc-1", True, 1.5, None):
                self.assertFalse(bridge.library_drop([root], 0.1, 0.1, box)["ok"])
            self.assertEqual(requests, [])

    def test_library_drop_isolates_per_path_errors(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}):
            good = os.path.join(root, "a.txt")
            open(good, "wb").close()
            bridge, requests = self._drop_bridge([{"ok": True}])
            result = bridge.library_drop([123.5, "bad\0path", None, good], 0.1, 0.1, 1)
            self.assertFalse(result["ok"])
            self.assertEqual(len(requests), 1)
            self.assertEqual(len(result["added"]), 1)
            self.assertEqual(len(result["failed"]), 3)
            bridge, requests = self._drop_bridge([])
            result = bridge.library_drop(12345, 0.1, 0.1, 1)
            self.assertFalse(result["ok"])
            self.assertEqual(requests, [])
            with patch("pathlib.Path.is_file", side_effect=OSError("boom")):
                bridge, requests = self._drop_bridge([])
                result = bridge.library_drop([good], 0.1, 0.1, 1)
            self.assertEqual(len(result["failed"]), 1)
            self.assertEqual(requests, [])

    def test_library_drop_respects_disabled_flag(self):
        from desktop_web_ui import DesktopWebBridge

        bridge = DesktopWebBridge.__new__(DesktopWebBridge)
        bridge._library_bridge = None
        bridge._developer_mode_enabled = lambda: True
        with patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}), \
             patch("docfit_app.library_bridge._open_pipe", side_effect=AssertionError), \
             patch("subprocess.Popen", side_effect=AssertionError):
            result = bridge.library_drop(["x"], 0.1, 0.1, 1)
        self.assertFalse(result["ok"])
        self.assertIsNone(bridge._library_bridge)


if __name__ == "__main__":
    unittest.main()
