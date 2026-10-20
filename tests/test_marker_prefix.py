import tempfile
import unittest
from pathlib import Path

from docfit_core.marker_prefix import audit_hwpx_prefixes, expected_prefix, normalize_prefix
from docfit_core.batch_format import ParagraphStyle, apply_batch
from docfit_core.xml_hanging_indent import build_hwpx_from_text_file


RULES = (("□", 0), ("ㅇ", 1), ("-", 3), ("*", 3), ("※", 3), ("•", 3))


class MarkerPrefixTests(unittest.TestCase):
    def test_all_marker_levels_and_attachment(self):
        cases = {
            "  ㅁ 제목": "ㅁ 제목",
            "  □ 제목": "□ 제목",
            "ㅇ 본문": " ㅇ 본문",
            "\t○ 본문": " ○ 본문",
            "- 내용": "   - 내용",
            "* 주석": "   * 주석",
            "   ** 주석": "  ** 주석",
            "  붙임 : 1. 자료 1부.  끝.": "붙임 : 1. 자료 1부.  끝.",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(normalize_prefix(text, RULES), expected)
                self.assertEqual(normalize_prefix(expected, RULES), expected)

    def test_non_marker_untouched(self):
        self.assertIsNone(expected_prefix("  보통 문장", RULES))
        self.assertEqual(normalize_prefix("  보통 문장", RULES), "  보통 문장")

    def test_hwpx_audit_passes_after_normalization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            txt, source, first = (root / name for name in
                                  ("source.txt", "source.hwpx", "first.hwpx"))
            txt.write_text("  ㅁ 제목\nㅇ 내용\n* 주석\n  붙임 : 1. 자료 1부.  끝.", encoding="utf-8")
            build_hwpx_from_text_file(txt, source)
            def plan(text, _paragraph):
                corrected = normalize_prefix(text, RULES)
                return ParagraphStyle(text=corrected) if corrected != text else None

            apply_batch(source, first, plan)
            result = audit_hwpx_prefixes(first, RULES)
            self.assertEqual(result["mismatches"], [])
            self.assertTrue(first.is_file())


if __name__ == "__main__":
    unittest.main()
