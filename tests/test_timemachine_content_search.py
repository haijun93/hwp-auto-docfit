import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from docfit_core.timemachine.content_search import (ContentSearchIndex, extract_reference_date,
                                                     extract_reference_date_info, extract_text)


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
        self.assertIn("업무 실적", found[0]["snippet"])
        path.write_text("새로운 내용", encoding="utf-8")
        self.assertTrue(self.index.index_file(path)["indexed"])
        self.assertEqual(self.index.search("업무 실적"), [])

    def test_hwpx_uses_defused_xml_extractor(self):
        path = self.root / "문서.hwpx"
        with ZipFile(path, "w") as archive:
            archive.writestr("Contents/header.xml", "<head/>")
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

    def test_reference_date_info_prefers_explicit_over_quarter_over_half(self):
        info = extract_reference_date_info("2026년 상반기 2026년도 1분기\n작성 기준일: 2026. 5. 20.")
        self.assertEqual(info, {"date": "2026-05-20", "source": "explicit", "text": "작성 기준일: 2026. 5. 20."})
        info = extract_reference_date_info("2026년 하반기 실적\n2026년도 3분기")
        self.assertEqual((info["date"], info["source"], info["text"]), ("2026-09-01", "quarter", "2026년도 3분기"))
        self.assertEqual(extract_reference_date_info("없음"), {"date": None, "source": None, "text": None})

    def test_reference_date_quarter_before_explicit_still_uses_explicit(self):
        info = extract_reference_date_info("2026년도 2분기 주요업무\n기준일: 2026-06-30")
        self.assertEqual((info["date"], info["source"]), ("2026-06-30", "explicit"))

    def test_reference_date_skips_invalid_date_and_uses_next_valid(self):
        info = extract_reference_date_info("기준일: 2026.2.30\n작성 기준일: 2026.3.31")
        self.assertEqual((info["date"], info["source"]), ("2026-03-31", "explicit"))
        self.assertEqual(info["text"], "작성 기준일: 2026.3.31")

    def test_reference_date_ignores_fifth_quarter(self):
        self.assertIsNone(extract_reference_date("2026년 5분기 계획"))
        self.assertEqual(extract_reference_date("2026년 5분기, 2026년 4분기"), "2026-12-01")

    def test_reference_date_without_day_defaults_to_first(self):
        info = extract_reference_date_info("기준일: 2026. 3.")
        self.assertEqual((info["date"], info["source"]), ("2026-03-01", "explicit"))
        self.assertEqual(extract_reference_date("작성기준일 2026년 7월"), "2026-07-01")

    def test_reference_date_half_years(self):
        self.assertEqual(extract_reference_date_info("2026년 상반기 실적")["date"], "2026-06-01")
        info = extract_reference_date_info("2025년도 하반기 실적")
        self.assertEqual((info["date"], info["source"], info["text"]), ("2025-12-01", "half", "2025년도 하반기"))

    def test_reference_date_text_includes_trailing_marks(self):
        info = extract_reference_date_info("기준일: 2026. 9. 30.\n본문")
        self.assertEqual((info["date"], info["text"]), ("2026-09-30", "기준일: 2026. 9. 30."))
        info = extract_reference_date_info("작성 기준일 2026년 12월 실적")
        self.assertEqual((info["date"], info["text"]), ("2026-12-01", "작성 기준일 2026년 12월"))
        info = extract_reference_date_info("기준일: 2026. 3.")
        self.assertEqual((info["date"], info["text"]), ("2026-03-01", "기준일: 2026. 3."))

    def test_reference_date_respects_digit_boundary(self):
        # 일이 숫자 경계를 넘으면(301) 30일로도, 일 없는 9월 1일로도 판정하지 않고 그 일치를 무시한다.
        self.assertEqual(extract_reference_date_info("기준일: 2026. 9. 301"),
                         {"date": None, "source": None, "text": None})
        info = extract_reference_date_info("기준일: 2026. 9. 301\n2026년도 3분기")
        self.assertEqual((info["date"], info["source"]), ("2026-09-01", "quarter"))
        self.assertIsNone(extract_reference_date("기준일: 2026. 123. 1"))


if __name__ == "__main__":
    unittest.main()
