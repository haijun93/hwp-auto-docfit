import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from docfit_core import kordoc_bridge as kb


class KordocContractTest(unittest.TestCase):
    """kordoc 실행 계약: 정확한 버전, Node 20 이상, 셸 없는 Windows 실행, 부분 적용 표시."""

    def setUp(self):
        super().setUp()
        self._runtime_patch = patch.object(kb, "_bundled_runtime", return_value=None)
        self._runtime_patch.start()
        self.addCleanup(self._runtime_patch.stop)

    def test_exact_version_pinned(self):
        self.assertEqual(kb.KORDOC_PACKAGE, "kordoc@4.24.9")

    def test_old_node_is_refused(self):
        with patch.object(kb, "_node_major", return_value=18):
            with self.assertRaises(kb.KordocUnavailableError) as cm:
                kb._kordoc_command()
        self.assertIn("20 이상", str(cm.exception))

    def test_local_install_preferred_over_npx(self):
        with tempfile.TemporaryDirectory() as d:
            node_modules = Path(d) / "node_modules"
            exe = node_modules / ".bin" / "kordoc.cmd"
            cli = node_modules / "kordoc" / "dist" / "cli.js"
            exe.parent.mkdir(parents=True)
            cli.parent.mkdir(parents=True)
            exe.write_text("@echo off")
            cli.write_text("// cli")
            with patch.object(kb, "_node_major", return_value=20), \
                    patch.object(kb, "_node_executable", return_value="node.exe"), \
                    patch.dict(os.environ, {"DOCFIT_KORDOC_BIN": str(exe)}):
                self.assertEqual(kb._kordoc_command(), ["node.exe", str(cli)])

    def test_windows_npx_wrapper_runs_node_script_without_shell(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            wrapper = root / "npx.cmd"
            script = root / "node_modules" / "npm" / "bin" / "npx-cli.js"
            script.parent.mkdir(parents=True)
            wrapper.write_text("@echo off")
            script.write_text("// cli")
            with patch.object(kb.shutil, "which", side_effect=lambda name: str(wrapper) if name == "npx.cmd" else None), \
                    patch.object(kb, "_node_executable", return_value="node.exe"):
                self.assertEqual(kb._npx_command(), ["node.exe", str(script)])

    def test_npx_download_is_blocked_by_default(self):
        with patch.object(kb, "_node_major", return_value=20), patch.object(kb, "_local_kordoc", return_value=None), \
                patch.dict(os.environ, {"DOCFIT_ALLOW_NPX_DOWNLOAD": "0"}, clear=False):
            with self.assertRaises(kb.KordocUnavailableError):
                kb._kordoc_command()

    def test_network_install_uses_locked_ci_and_disables_lifecycle_scripts(self):
        with patch.object(kb, "_node_major", return_value=20), patch.object(kb, "_local_kordoc", return_value=None), \
                patch.object(kb, "_bundled_runtime", return_value=None), \
                patch.object(kb, "_locked_npm_install", return_value=["node.exe", "kordoc.js"]) as install, \
                patch.dict(os.environ, {"DOCFIT_ALLOW_NPX_DOWNLOAD": "1", "DOCFIT_OFFLINE": "0"}, clear=False):
            command = kb._kordoc_command()
        self.assertEqual(command, ["node.exe", "kordoc.js"])
        install.assert_called_once_with()

    def test_locked_install_invokes_npm_ci_with_scripts_disabled(self):
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(kb.shutil, "which", return_value="npm"), \
                patch.object(kb, "_node_executable", return_value="node"), \
                patch.object(kb.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run, \
                patch.dict(os.environ, {"LOCALAPPDATA": folder}):
            root = Path(folder) / "HwpAutoDocFit" / "kordoc-network"
            with patch.object(kb.Path, "is_file", autospec=True, side_effect=lambda p: True):
                command = kb._locked_npm_install()
        self.assertEqual(command[0], "node")
        self.assertEqual(run.call_args_list[0].args[0][1:3], ["ci", "--ignore-scripts"])

    def test_engine_status_reports_missing_runtime_dependency(self):
        with patch.object(kb, "_node_major", return_value=20), \
                patch.object(kb, "_node_executable", return_value="node.exe"), \
                patch.object(kb, "_local_kordoc", return_value=None), \
                patch.object(kb, "_bundled_runtime", return_value=None), \
                patch.object(kb.kordoc_runtime, "bundled_pack", return_value=None), \
                patch.dict(os.environ, {"DOCFIT_ALLOW_NPX_DOWNLOAD": "0"}, clear=False):
            status = kb.engine_status()
        self.assertFalse(status["available"])
        # 무엇을 어디에 두면 되는지 알린다.
        self.assertIn(kb.kordoc_runtime.RUNTIME_PACK_NAME, status["reason"])

    def test_missing_engine_preflight_does_not_spawn_version_process(self):
        with patch.object(kb, "_node_major", side_effect=AssertionError("version subprocess")), \
                patch.object(kb, "_node_executable", return_value="node.exe"), \
                patch.object(kb, "_local_kordoc", return_value=None), \
                patch.dict(os.environ, {"DOCFIT_ALLOW_NPX_DOWNLOAD": "0"}):
            self.assertFalse(kb.engine_status()["available"])

    def test_global_npm_wrapper_uses_installed_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            prefix = Path(folder)
            wrapper = prefix / "kordoc.cmd"
            cli = prefix / "node_modules" / "kordoc" / "dist" / "cli.js"
            cli.parent.mkdir(parents=True)
            wrapper.write_text("@echo off")
            cli.write_text("// cli")
            with patch.object(kb, "_node_executable", return_value="node.exe"):
                self.assertEqual(kb._local_kordoc_command(str(wrapper)), ["node.exe", str(cli)])

    def test_partial_patch_is_marked(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "a.hwpx"
            src.write_bytes(b"x")
            def fake(args, **kw):
                Path(args[args.index("-o") + 1]).write_bytes(b"y")
                return subprocess.CompletedProcess(args, 2, "", "")
            with patch.object(kb, "run_kordoc", side_effect=fake):
                out = kb.patch_document(src, Path(d) / "e.md")
            self.assertIn("일부미적용", out.name)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
