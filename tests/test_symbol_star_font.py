"""설정 > 문장기호별 글꼴·크기에 '*'(대표 기호, **는 여기로 합침)가 추가됐는지 검증한다.

사용자 요청(2026-09-28): *, **도 문두기호별 글꼴·크기 설정에서 고를 수 있어야
하며, 대표 문두기호는 *이고 기본값은 ※와 같아야 한다.
"""

import copy
from pathlib import Path
import runpy
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"


class SymbolStarFontTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(SOURCE), run_name="symbol_star_font_test")

    def test_star_is_listed_among_configurable_symbols(self):
        self.assertIn("*", self.ns["문장기호_목록"])
        # 이중 별표(**)는 별도 항목이 아니라 *의 별칭이므로 목록에 없어야 한다.
        self.assertNotIn("**", self.ns["문장기호_목록"])

    def test_star_default_symbol_font_matches_note_marker(self):
        기본값 = self.ns["기본_설정"]["symbol_fonts"]
        self.assertIn("*", 기본값)
        self.assertEqual(기본값["*"], 기본값["※"])

    def test_star_default_rule_matches_note_marker_rule(self):
        규칙들 = {rule[0]: rule for rule in self.ns["표준서식_설정"]["기호_규칙"]}
        self.assertIn("*", 규칙들)
        # 기호 이름(rule[0])만 다르고 들여쓰기·글꼴·크기·굵기·특수플래그는 ※와 같다.
        self.assertEqual(규칙들["*"][1:], 규칙들["※"][1:])

    def test_lookup_resolves_single_and_double_star_to_the_star_rule(self):
        fn = self.ns["표준서식_기호규칙_찾기"]
        별표_규칙 = fn("* 참고 사항입니다")
        이중별표_규칙 = fn("** 이중 주석입니다")
        self.assertIsNotNone(별표_규칙)
        self.assertEqual(별표_규칙[0], "*")
        self.assertEqual(이중별표_규칙, 별표_규칙)

    def test_custom_symbol_font_override_applies_only_to_star(self):
        # 기호글꼴_적용은 표준서식_설정을 제자리에서 바꾸는 전역 부수효과가 있으므로,
        # 같은 클래스의 다른 테스트에 영향을 주지 않도록 끝나면 원래 규칙으로 되돌린다.
        원본_규칙 = copy.deepcopy(self.ns["표준서식_설정"]["기호_규칙"])
        try:
            fn = self.ns["기호글꼴_적용"]
            설정 = {"symbol_fonts": {"*": {"font": "굴림", "size": "11"}}}
            fn(설정)
            규칙들 = {rule[0]: rule for rule in self.ns["표준서식_설정"]["기호_규칙"]}
            self.assertEqual(규칙들["*"][2:4], ("굴림", 11))
            # 다른 기호(※)는 영향을 받지 않는다.
            self.assertEqual(규칙들["※"][2:4], ("한컴돋움", 13))
        finally:
            self.ns["표준서식_설정"]["기호_규칙"] = 원본_규칙


if __name__ == "__main__":
    unittest.main()
