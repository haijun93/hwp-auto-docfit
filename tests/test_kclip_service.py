import hashlib
import json
import os
import tempfile
import unittest
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
            raise kc.KAgentError("K클립보드가 켜져 있지 않습니다.")
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


if __name__ == "__main__":
    unittest.main()
