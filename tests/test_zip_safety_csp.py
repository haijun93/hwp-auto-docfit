"""S2(ZIP 상한 공용 열기)·S6(CSP) 시험. 합성 파일만 임시 폴더에서 다룬다."""
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from docfit_core.hwpx import HwpxLimits, HwpxSecurityError, open_zip_safely

ROOT = Path(__file__).resolve().parents[1]


class OpenZipSafelyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.folder = Path(self._tmp.name)

    def make(self, name, members, compression=zipfile.ZIP_DEFLATED):
        path = self.folder / name
        with zipfile.ZipFile(path, "w", compression) as archive:
            for member, data in members.items():
                archive.writestr(member, data)
        return path

    def test_normal_archive_reads_same(self):
        path = self.make("ok.docx", {"word/document.xml": b"<a>hello</a>", "x.txt": b"abc"})
        with open_zip_safely(path) as archive:
            self.assertEqual(archive.read("word/document.xml"), b"<a>hello</a>")
            self.assertEqual(sorted(archive.namelist()), ["word/document.xml", "x.txt"])

    def test_zip_bomb_by_ratio_is_blocked(self):
        path = self.make("bomb.docx", {"a.bin": b"\0" * (50 * 1024 * 1024)})
        self.assertLess(path.stat().st_size, 1024 * 1024)
        with self.assertRaises(HwpxSecurityError):
            open_zip_safely(path)

    def test_member_and_total_size_limits(self):
        path = self.make("big.docx", {"a.bin": b"abcdefgh" * 100})
        with self.assertRaises(HwpxSecurityError):
            open_zip_safely(path, HwpxLimits(max_file_size=100))
        path = self.make("two.docx", {"a": b"x" * 600, "b": b"y" * 600})
        with self.assertRaises(HwpxSecurityError):
            open_zip_safely(path, HwpxLimits(max_total_size=1000))

    def test_too_many_entries_is_blocked(self):
        path = self.make("many.docx", {f"f{i}": b"" for i in range(20)})
        with self.assertRaises(HwpxSecurityError):
            open_zip_safely(path, HwpxLimits(max_entries=10))

    def test_unsafe_path_and_not_zip(self):
        path = self.make("evil.docx", {"../evil.txt": b"x"})
        with self.assertRaises(HwpxSecurityError):
            open_zip_safely(path)
        text = self.folder / "plain.docx"
        text.write_bytes(b"not a zip")
        with self.assertRaises(HwpxSecurityError):
            open_zip_safely(text)

    def test_user_document_readers_use_safe_open(self):
        for relative in ("docfit_core/hwpx_idioms.py", "docfit_core/excel_table_hwpx.py",
                         "docfit_core/timemachine/content_search.py", "docfit_core/timemachine/thumbs.py"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("open_zip_safely", source, relative)


class WebCspTests(unittest.TestCase):
    def policy(self, relative):
        html = (ROOT / relative).read_text(encoding="utf-8")
        match = re.search(r'<meta[^>]+http-equiv="Content-Security-Policy"[^>]+content="([^"]+)"', html, re.I)
        self.assertIsNotNone(match, relative)
        return html, dict(
            (part.split()[0], part.split()[1:]) for part in match.group(1).split(";") if part.strip())

    def test_flutter_index_has_minimal_csp(self):
        html, policy = self.policy("flutter_ui/web/index.html")
        self.assertEqual(policy["object-src"], ["'none'"])
        self.assertEqual(policy["default-src"], ["'self'"])
        self.assertNotIn("'unsafe-inline'", policy["script-src"])
        self.assertNotIn("'unsafe-eval'", policy["script-src"])
        self.assertIn("'wasm-unsafe-eval'", policy["script-src"])
        for source in policy.values():
            self.assertFalse({"*", "http:", "https:"} & set(source))
        self.assertIn("blob:", policy["worker-src"])
        self.assertIn("data:", policy["img-src"])
        # 인라인 스크립트가 없어야 'self'만으로 동작한다.
        self.assertNotRegex(html, r"<script(?![^>]*\bsrc=)[^>]*>")
        self.assertTrue((ROOT / "flutter_ui/web/docfit_bridge.js").is_file())

    def test_desktop_index_csp_has_no_remote_sources(self):
        html, policy = self.policy("desktop_web/index.html")
        self.assertEqual(policy["connect-src"], ["'none'"])
        self.assertNotIn("'unsafe-inline'", policy["script-src"])
        self.assertNotRegex(html, r"<script(?![^>]*\bsrc=)[^>]*>")


if __name__ == "__main__":
    unittest.main()
