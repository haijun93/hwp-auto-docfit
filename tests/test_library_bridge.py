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
        with patch.dict(os.environ, {"DOCFIT_LIBRARY_BRIDGE": "0"}), \
             patch("docfit_app.library_bridge._open_pipe", side_effect=AssertionError), \
             patch("subprocess.Popen", side_effect=AssertionError):
            result = bridge.library({"cmd": "box_list"})
        self.assertFalse(result["ok"])
        self.assertIsNone(bridge._library_bridge)


if __name__ == "__main__":
    unittest.main()
