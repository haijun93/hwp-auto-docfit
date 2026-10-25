"""Unit tests for defensive HWPX and ZIP archive verification (S2)."""
from __future__ import annotations

import io
from pathlib import Path
import tempfile
import unittest
import zipfile

from docfit_core.hwpx import (
    HwpxLimits,
    HwpxSecurityError,
    open_hwpx_safely,
    open_zip_safely,
    validate_zip_members,
)
from docfit_core.table_catalog import _safe_archive


class HwpxSecurityTest(unittest.TestCase):
    def test_parent_path_components_rejected(self):
        for name in ('..', 'a/../b', '../b', 'a\\..\\b'):
            with self.subTest(name=name):
                path = self.dir_path / 'traversal.zip'
                with zipfile.ZipFile(path, 'w') as archive:
                    archive.writestr(name, b'x')
                with self.assertRaises(HwpxSecurityError):
                    open_zip_safely(path)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.dir_path = Path(self.temp_dir.name)

    def _create_minimal_hwpx(self, path: Path, extra_files: dict[str, bytes] | None = None):
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("Contents/header.xml", b"<header/>")
            z.writestr("Contents/section0.xml", b"<section/>")
            if extra_files:
                for name, content in extra_files.items():
                    z.writestr(name, content)

    def test_zip_bomb_compression_ratio_rejected(self):
        bomb_hwpx = self.dir_path / "bomb.hwpx"
        # Highly repetitive data compresses to tiny size, triggering ratio limit (>1000)
        repetitive = b"0" * (2 * 1024 * 1024)
        self._create_minimal_hwpx(bomb_hwpx, {"Contents/huge.bin": repetitive})

        with self.assertRaises(HwpxSecurityError) as cm:
            open_hwpx_safely(bomb_hwpx, limits=HwpxLimits(max_compression_ratio=100))
        self.assertIn("비정상 압축률", str(cm.exception))

    def test_table_catalog_safe_archive_enforces_limits(self):
        oversized = self.dir_path / "oversized.hwpx"
        # Create an archive with 2005 entries (> 2000 limit)
        with zipfile.ZipFile(oversized, "w") as z:
            z.writestr("Contents/header.xml", b"<header/>")
            z.writestr("Contents/section0.xml", b"<section/>")
            for i in range(2005):
                z.writestr(f"Contents/dummy_{i}.txt", b"x")

        with self.assertRaises(HwpxSecurityError):
            _safe_archive(oversized)

    def test_open_zip_safely_returns_valid_instance(self):
        valid = self.dir_path / "valid.zip"
        with zipfile.ZipFile(valid, "w") as z:
            z.writestr("hello.txt", b"world")

        archive = open_zip_safely(valid)
        try:
            self.assertEqual(archive.read("hello.txt"), b"world")
        finally:
            archive.close()


if __name__ == "__main__":
    unittest.main()
