import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from docfit_core.timemachine.content_search import ContentSearchIndex, extract_text


class ContentSearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.index = ContentSearchIndex(self.root / "content.sqlite")

    def tearDown(self):
        self.index.close()
        self.tmp.cleanup()

    def test_txt_search_snippet_and_incremental_update(self):
        path = self.root / "보고서.txt"
        path.write_text("분기별 업무 실적 검색 대상 문장", encoding="utf-8")
        self.assertTrue(self.index.index_file(path)["indexed"])
        self.assertFalse(self.index.index_file(path)["indexed"])
        found = self.index.search("업무 실적", roots=[str(self.root)])
        self.assertEqual(found[0]["name"], path.name)
        self.assertIn("[업무 실적]", found[0]["snippet"])
        path.write_text("새로운 내용", encoding="utf-8")
        self.assertTrue(self.index.index_file(path)["indexed"])
        self.assertEqual(self.index.search("업무 실적"), [])

    def test_hwpx_uses_defused_xml_extractor(self):
        path = self.root / "문서.hwpx"
        with ZipFile(path, "w") as archive:
            archive.writestr("Contents/section0.xml", '<root><p>타임머신 본문 검색</p></root>')
        self.assertIn("타임머신 본문", extract_text(path))
        self.index.index_file(path)
        self.assertEqual(len(self.index.search("타임머신")), 1)

    def test_failures_are_retained_and_trash_is_filtered(self):
        broken = self.root / "bad.docx"
        broken.write_text("not a zip", encoding="utf-8")
        self.assertIsNotNone(self.index.index_file(broken)["error"])
        self.assertEqual(len(self.index.errors([str(self.root)])), 1)
        trash = self.root / "$Recycle.Bin"
        trash.mkdir()
        hidden = trash / "hidden.txt"
        hidden.write_text("secretword", encoding="utf-8")
        self.index.index_file(hidden)
        self.assertEqual(self.index.search("secretword"), [])


if __name__ == "__main__":
    unittest.main()
