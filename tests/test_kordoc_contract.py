import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from docfit_core import kordoc_bridge as kb


class KordocContractTest(unittest.TestCase):
    """kordoc 실행 계약(2026-10-10): 정확한 버전, Node 20 이상, 폐쇄망 설치본 우선, 부분 적용 표시."""

    def test_exact_version_pinned(self):
        self.assertRegex(kb.KORDOC_PACKAGE, r"^kordoc@\d+\.\d+\.\d+$")

    def test_old_node_is_refused(self):
        with patch.object(kb, "_node_major", return_value=18):
            with self.assertRaises(kb.KordocUnavailableError) as cm:
                kb._kordoc_command()
        self.assertIn("20 이상", str(cm.exception))

    def test_local_install_preferred_over_npx(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / "kordoc.cmd"
            exe.write_text("@echo off")
            with patch.object(kb, "_node_major", return_value=20), patch.dict(os.environ, {"DOCFIT_KORDOC_BIN": str(exe)}):
                self.assertEqual(kb._kordoc_command(), [str(exe)])

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
