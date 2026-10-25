"""Unit tests for security audit findings S1~S9 regression verification."""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from docfit_app.table_sketch_service import TableSketchService
from docfit_core.updater import powershell_encoded_command


class SecurityS1S9Test(unittest.TestCase):
    def test_portable_installer_launches_memory_command(self):
        import ast
        import os
        import subprocess
        import sys
        from unittest.mock import Mock
        from docfit_core.updater import install_script, launch_environment
        # Execute the actual nested UI method without starting Tk or Hancom COM.
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'docfit_ui/legacy.py').read_text(encoding='utf-8'))
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                      and n.name == '_자동업데이트_설치')
        namespace = dict(sys=sys, os=os, subprocess=subprocess,
                         업데이트_교체스크립트=install_script, 업데이트_실행환경=launch_environment,
                         UPDATE_STARTED_FLAG='started', UPDATE_BUSY_FLAG='busy',
                         _업데이트_기록=Mock())
        exec(compile(ast.Module(body=[method], type_ignores=[]), '<portable installer>', 'exec'), namespace)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'app.exe'
            target.write_bytes(b'MZold')
            downloaded = Path(folder) / 'new.exe'
            downloaded.write_bytes(b'MZnew')
            ui = Mock()
            with patch('docfit_app.update_service.portable_target', return_value=target), patch.object(subprocess, 'Popen') as launch:
                namespace['_자동업데이트_설치'](ui, downloaded, 'a' * 64)
            command = launch.call_args.args[0]
            self.assertIn('-EncodedCommand', command)
            self.assertNotIn('-File', command)
            decoded = base64.b64decode(command[-1]).decode('utf-16le')
            self.assertIn(str(downloaded), decoded)
            self.assertIn('a' * 64, decoded)
            self.assertEqual(list(Path(folder).glob('*.ps1')), [])
            ui.root.destroy.assert_called_once()

    def test_encoded_final_command_length_limit(self):
        import subprocess
        accepted = powershell_encoded_command('x' * 11000, {})
        self.assertLessEqual(len(subprocess.list2cmdline(accepted).encode('utf-16le')) // 2 + 1, 32000)
        with self.assertRaises(ValueError):
            powershell_encoded_command('x' * 12000, {})

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_encoded_command_escaping(self):
        script = 'Write-Output "$Installer and $Target"'
        params = {
            "Installer": "C:\\Program Files\\App's\\setup.exe",
            "Target": "D:\\Target",
        }
        cmd = powershell_encoded_command(script, params)
        self.assertEqual(cmd[0], "powershell.exe")
        self.assertIn("-EncodedCommand", cmd)

        encoded_idx = cmd.index("-EncodedCommand") + 1
        encoded_arg = cmd[encoded_idx]
        decoded_script = base64.b64decode(encoded_arg).decode("utf-16le")

        self.assertIn("'Installer' = 'C:\\Program Files\\App''s\\setup.exe'", decoded_script)
        self.assertIn("@docfitParams", decoded_script)

        # NUL byte rejection
        with self.assertRaises(ValueError) as cm:
            powershell_encoded_command(script, {"Bad": "val\x00evil"})
        self.assertIn("NUL", str(cm.exception))

        # Invalid identifier rejection
        with self.assertRaises(ValueError) as cm:
            powershell_encoded_command(script, {"123Bad": "val"})
        self.assertIn("올바르지 않은 PowerShell 매개변수", str(cm.exception))

    def test_csp_meta_tags_present(self):
        desktop_html = (self.repo_root / "desktop_web" / "index.html").read_text(encoding="utf-8")
        flutter_html = (self.repo_root / "flutter_ui" / "web" / "index.html").read_text(encoding="utf-8")
        bridge_js = self.repo_root / "flutter_ui" / "web" / "docfit_bridge.js"

        self.assertIn('http-equiv="Content-Security-Policy"', desktop_html)
        self.assertIn('http-equiv="Content-Security-Policy"', flutter_html)
        self.assertTrue(bridge_js.is_file(), "docfit_bridge.js must exist")
        self.assertIn('src="docfit_bridge.js"', flutter_html)

    def test_dll_hash_matches_security_md(self):
        dll_path = self.repo_root / "MapoHwpAutoDocFitSecurity.dll"
        self.assertTrue(dll_path.is_file(), "MapoHwpAutoDocFitSecurity.dll must exist in repo root")

        digest = hashlib.sha256(dll_path.read_bytes()).hexdigest().lower()
        self.assertEqual(digest, "9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6")

        security_md = (self.repo_root / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6", security_md)

    def test_table_sketch_service_save_cleanup_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = TableSketchService(tmp_dir)
            sketch = {
                "name": "fail_sketch",
                "grid": {"cols": 2, "rows": 2, "cell_mm": 5.0},
                "lines": [],
                "texts": [],
            }

            # Simulate failure during save (e.g. replace raises exception)
            with patch.object(Path, "replace", side_effect=OSError("Disk write error")):
                with self.assertRaises(OSError):
                    service.save("fail_sketch", sketch)

            # Ensure no lingering .tmp files in folder
            lingering = list(Path(tmp_dir).glob("*.tmp"))
            self.assertEqual(lingering, [], "Temporary files must be cleaned up on failure")


if __name__ == "__main__":
    unittest.main()
