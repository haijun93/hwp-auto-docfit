from pathlib import Path
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from docfit_core import HwpxSecurityError, compare_documents, export_markdown, inspect_hwpx, validate_hwpx


HEADER = b'<?xml version="1.0" encoding="UTF-8"?><hh:head xmlns:hh="urn:head" />'
SECTION = b'''<?xml version="1.0" encoding="UTF-8"?>
<hs:sec xmlns:hs="urn:section" xmlns:hp="urn:para">
  <hp:p><hp:run><hp:t>1. \xeb\xac\xb8\xec\x84\x9c \xec\xa0\x9c\xeb\xaa\xa9</hp:t></hp:run></hp:p>
  <hp:tbl><hp:tr><hp:tc><hp:p><hp:run><hp:t>\xed\x95\xad\xeb\xaa\xa9</hp:t></hp:run></hp:p></hp:tc><hp:tc><hp:p><hp:run><hp:t>\xeb\x82\xb4\xec\x9a\xa9</hp:t></hp:run></hp:p></hp:tc></hp:tr></hp:tbl>
</hs:sec>'''


def make_hwpx(path: Path, section: bytes = SECTION):
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("Contents/header.xml", HEADER)
        archive.writestr("Contents/section0.xml", section)
        archive.writestr("BinData/image.png", b"png")


class HwpxCoreTest(unittest.TestCase):
    def test_inspect_and_markdown_export(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.hwpx"
            make_hwpx(source)
            report = inspect_hwpx(source)
            self.assertEqual(report.section_count, 1)
            self.assertEqual(report.paragraph_count, 1)
            self.assertEqual(report.table_count, 1)
            self.assertEqual(report.image_count, 1)
            target = export_markdown(source)
            markdown = target.read_text(encoding="utf-8")
            self.assertIn("## 1. 문서 제목", markdown)
            self.assertIn("| 항목 | 내용 |", markdown)

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "unsafe.hwpx"
            with ZipFile(source, "w") as archive:
                archive.writestr("Contents/header.xml", HEADER)
                archive.writestr("Contents/section0.xml", SECTION)
                archive.writestr("../outside.txt", b"bad")
            with self.assertRaises(HwpxSecurityError):
                validate_hwpx(source)

    def test_integrity_comparison_detects_missing_table(self):
        no_table = b'''<hs:sec xmlns:hs="urn:section" xmlns:hp="urn:para"><hp:p><hp:run><hp:t>1. \xeb\xac\xb8\xec\x84\x9c \xec\xa0\x9c\xeb\xaa\xa9</hp:t></hp:run></hp:p></hs:sec>'''
        with tempfile.TemporaryDirectory() as folder:
            before_path = Path(folder) / "before.hwpx"
            after_path = Path(folder) / "after.hwpx"
            make_hwpx(before_path)
            make_hwpx(after_path, no_table)
            result = compare_documents(inspect_hwpx(before_path), inspect_hwpx(after_path))
            self.assertTrue(any("표 개수" in issue["message"] for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
