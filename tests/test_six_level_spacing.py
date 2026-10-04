"""6단계 계층의 문단 위 여백 기본값: 장 20 · 중제목 15 · □ 15 · ㅇ 10(2026-10-04)."""
from pathlib import Path
import runpy
import unittest

from docfit_core.document_rules import ParagraphSpacingTracker, paragraph_level

BASE = {"chapter": 20, "midtitle": 15, "box": 15, "circle": 10, "note": 3}


class SixLevelSpacingTest(unittest.TestCase):
    def test_levels(self):
        for text, level in (("제1장 개요", "chapter"), ("2장 계획", "chapter"), ("Chapter 3 결론", "chapter"),
                            ("Ⅰ. 추진 배경", "midtitle"), ("Ⅱ 추진 계획", "midtitle"), ("□ 가", "box"),
                            ("ㅇ 나", "circle"), ("- 다", "dash"), ("※ 라", "note"), ("일반 문장", None)):
            self.assertEqual(paragraph_level(text), level, text)

    def test_heading_levels_keep_their_value_without_return_multiplier(self):
        t = ParagraphSpacingTracker()
        got = [t.spacing_for(s, BASE) for s in ("제1장 개요", "Ⅰ. 배경", "□ 가", "ㅇ 나", "□ 라", "Ⅱ 계획", "제2장 x")]
        self.assertEqual(got, [20, 15, 15, 10, 22, 15, 20])
        self.assertEqual(t.spacing_for_level("midtitle", BASE), 15)     # 표 첫 칸 로마자 중제목 표

    def test_app_defaults(self):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))
        defaults = ns["기본_설정"]
        self.assertEqual([defaults[k] for k in ("std_parspace_chapter", "std_parspace_midtitle", "std_parspace_box",
                                                 "std_parspace_circle")], ["20", "15", "15", "10"])


if __name__ == "__main__":
    unittest.main()
