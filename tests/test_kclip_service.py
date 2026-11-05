import hashlib
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from docfit_app import kagent_client as kc
from docfit_app.kclip_service import KClipService


class FakeClient:
    def __init__(self):
        self.on = False
        self.requests = []

    def running(self):
        return self.on

    def status_file(self):
        return {"pid": 1, "items": 3, "pipe": "\\\\.\\pipe\\HwpAutoDocFit.kagent.S-1"} if self.on else None

    def request(self, cmd, **payload):
        if not self.on:
            raise kc.KAgentError("몽땅클립보드가 켜져 있지 않습니다.")
        self.requests.append((cmd, payload))
        if cmd == "quit":
            self.on = False
        return {"ok": True, "cmd": cmd}


class KClipServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.exe = Path(self.tmp.name) / "kagent.exe"
        self.exe.write_bytes(b"MZ fake")
        self.client = FakeClient()
        self.calls = []

        def start(path):
            self.calls.append(("start", path))
            self.client.on = True

        self.service = KClipService(self.client, installer=lambda exe: self.calls.append(("install", exe)) or exe,
                                    starter=start, autostart=lambda on: self.calls.append(("autostart", on)),
                                    bundled=lambda: self.exe)

    def tearDown(self):
        self.tmp.cleanup()

    def test_enable_requires_consent_then_installs_starts_autostarts(self):
        self.assertEqual(self.service.command("enable", {})["code"], "KCLIP_CONSENT")
        self.assertEqual(self.calls, [])
        result = self.service.command("enable", {"consent": True})
        self.assertTrue(result["running"])
        self.assertEqual([c[0] for c in self.calls], ["install", "start", "autostart"])
        self.assertEqual(self.calls[-1], ("autostart", True))

    def test_integrity_check(self):
        self.exe.with_name("kagent.exe.sha256").write_text("00" * 32, encoding="ascii")
        self.assertEqual(self.service.command("enable", {"consent": True})["code"], "KCLIP_INTEGRITY")
        self.exe.with_name("kagent.exe.sha256").write_text(hashlib.sha256(b"MZ fake").hexdigest().upper(),
                                                           encoding="ascii")
        self.assertTrue(self.service.command("enable", {"consent": True})["running"])

    def test_forward_and_offline(self):
        self.assertEqual(self.service.command("list", {"limit": 5})["code"], "KCLIP_OFFLINE")
        self.client.on = True
        self.service.command("list", {"limit": 5, "query": "보고", "evil": 1})
        self.service.command("pin", {"id": 3, "pinned": False})
        self.assertEqual(self.client.requests, [("list", {"limit": 5, "query": "보고"}),
                                                ("pin", {"id": 3, "pinned": False})])
        self.assertEqual(self.service.command("quit")["code"], "NOT_AVAILABLE")

    def test_open_web_only_accepts_http_schemes(self):
        self.client.on = True
        self.client.request = lambda cmd, **payload: {"ok": True, "kind": "text", "data": "https://example.com/path"}
        with patch("webbrowser.open", return_value=True) as open_browser:
            self.assertTrue(self.service.command("open_web", {"id": 3})["ok"])
            open_browser.assert_called_once_with("https://example.com/path")
        self.client.request = lambda cmd, **payload: {"ok": True, "kind": "text", "data": "file:///C:/secret"}
        self.assertEqual(self.service.command("open_web", {"id": 3})["code"], "KCLIP_WEB")

    def test_scheduled_pause_resumes_on_next_status_after_expiry(self):
        import time
        self.client.on = True
        self.service._pause_file = Path(self.tmp.name) / "pause.json"
        result = self.service.command("pause", {"minutes": 30})
        self.assertEqual(result["cmd"], "pause")
        self.assertTrue(self.service.command("status")["status"]["paused"])
        self.service._pause_file.write_text('{"until": %s}' % (time.time() - 1), encoding="utf-8")
        self.service.command("status")
        self.assertEqual(self.client.requests[-1][0], "resume")
        self.assertFalse(self.service._pause_file.exists())

    def test_disable_quits_and_removes_autostart(self):
        self.client.on = True
        result = self.service.command("disable")
        self.assertFalse(result["running"])
        self.assertEqual(self.calls, [("autostart", False)])

    def test_missing_bundle(self):
        service = KClipService(self.client, bundled=lambda: None)
        self.assertFalse(service.status()["available"])
        self.assertEqual(service.command("enable", {"consent": True})["code"], "KCLIP_MISSING")


class ClientTests(unittest.TestCase):
    def test_install_retries_locked_agent_replace_and_keeps_old_file_until_success(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder, "bundled.exe")
            target = Path(folder, "data", "kagent.exe")
            source.write_bytes(b"new agent")
            target.parent.mkdir()
            target.write_bytes(b"old agent")
            real_replace = kc.os.replace
            attempts = []

            def replace_with_brief_lock(src, dst):
                attempts.append((src, dst))
                if len(attempts) < 3:
                    raise PermissionError("sharing violation")
                return real_replace(src, dst)

            with patch.object(kc.os, "replace", side_effect=replace_with_brief_lock), \
                 patch.object(kc.time, "sleep"):
                installed = kc.install(source, target.parent)

            self.assertEqual(installed, target)
            self.assertEqual(target.read_bytes(), b"new agent")
            self.assertEqual(len(attempts), 3)
            self.assertFalse(list(target.parent.glob("*.new")))

    def test_install_reports_locked_agent_after_bounded_retries(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder, "bundled.exe")
            target = Path(folder, "data", "kagent.exe")
            source.write_bytes(b"new agent")
            target.parent.mkdir()
            target.write_bytes(b"old agent")
            with patch.object(kc.os, "replace", side_effect=PermissionError("sharing violation")), \
                 patch.object(kc.time, "sleep"):
                with self.assertRaisesRegex(kc.KAgentError, "이전 몽땅클립보드가 종료됐는지"):
                    kc.install(source, target.parent)
            self.assertEqual(target.read_bytes(), b"old agent")
            self.assertFalse(list(target.parent.glob("*.new")))

    def test_status_file_and_pipe_name_check(self):
        with tempfile.TemporaryDirectory() as folder:
            client = kc.KAgentClient(folder)
            self.assertIsNone(client.status_file())
            self.assertFalse(client.running())
            Path(folder, "status.json").write_text(json.dumps({"pid": os.getpid(), "pipe": r"C:\evil"}),
                                                   encoding="utf-8")
            if os.name == "nt":
                self.assertTrue(client.running())
            with self.assertRaises(kc.KAgentError):
                client.request("status")


class KAgentPipeRetryTests(unittest.TestCase):
    def test_busy_pipe_waits_then_retries_open_once_connected(self):
        client = kc.KAgentClient(timeout=1.0)
        busy = OSError("pipe busy")
        busy.winerror = 231
        stream = object()
        with patch.object(kc.os, "name", "nt"), \
             patch("builtins.open", side_effect=[busy, stream]) as open_pipe, \
             patch.object(client, "_wait_pipe", return_value=True) as wait_pipe:
            self.assertIs(client._open_pipe(r"\\.\pipe\agent"), stream)
        self.assertEqual(open_pipe.call_count, 2)
        wait_pipe.assert_called_once()

    def test_non_busy_pipe_error_is_not_retried(self):
        client = kc.KAgentClient(timeout=1.0)
        denied = OSError("access denied")
        denied.winerror = 5
        with patch.object(kc.os, "name", "nt"), \
             patch("builtins.open", side_effect=denied) as open_pipe, \
             patch.object(client, "_wait_pipe") as wait_pipe:
            with self.assertRaises(OSError):
                client._open_pipe(r"\\.\pipe\agent")
        open_pipe.assert_called_once()
        wait_pipe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
