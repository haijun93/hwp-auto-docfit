"""문두기호별 내어쓰기 빈칸 규칙과 붙임 번호의 세로 정렬을 확인한다."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from docfit_core.hanging_rules import hanging_blank_count, is_supplement


class BlankCountTest(unittest.TestCase):
    def test_marker_blanks(self):
        self.assertEqual(hanging_blank_count("ㅇ 본문"), 1)
        self.assertEqual(hanging_blank_count("  ○ 본문"), 1)
        self.assertEqual(hanging_blank_count(" - 본문"), 3)
        self.assertIsNone(hanging_blank_count("※ 참고"))      # 부연설명은 앞 기호 값에 연동
        self.assertIsNone(hanging_blank_count("** 주"))

    def test_no_rule(self):
        for text in ("□ 제목", "일반 문장", "1. 항목", "", None):
            self.assertIsNone(hanging_blank_count(text), text)


class SupplementTest(unittest.TestCase):
    def test_roles(self):
        for text in ("* 주", "** 주", "※ 참고"):
            self.assertTrue(is_supplement(text), text)
        for text in ("ㅁ 제목", "□ 제목", "ㅇ 본문", "○ 본문", "- 세부"):
            self.assertFalse(is_supplement(text), text)
        self.assertFalse(is_supplement("일반 문장"))


class HangingValueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))

    def _value(self, text, widths):
        fn = self.ns["_기호별_내어쓰기_값"]
        marker_end = self.ns["문장부호_마커_끝위치"](text)
        measured = lambda begin, count: widths.get(count)
        with patch.dict(fn.__globals__, {"_캐럿위치_폭_실측": measured, "복사_내어쓰기_규칙": lambda t: None}):
            return fn((0, 0, 0), text), marker_end

    def test_blank_width_is_multiplied_by_rule(self):
        # 기호 끝(1글자)까지 1000, 빈칸 1칸 폭 250 → ㅇ 1칸, - 3칸
        self.assertEqual(self._value("ㅇ 본문", {1: 1000, 2: 1250})[0], -1250)
        self.assertEqual(self._value("- 본문", {1: 800, 2: 1050})[0], -(800 + 3 * 250))

    def test_supplement_is_own_text_start_plus_two_blanks(self):
        # 빈칸 폭 250: 기호 끝 900, 글 시작 1150 → -(1150 + 2×250). 앞 문장과 무관하다.
        self.assertEqual(self._value("※ 참고", {1: 900, 2: 1150})[0], -1650)
        self.assertEqual(self._value("* 주", {1: 600, 2: 850})[0], -1350)
        self.assertEqual(self._value("** 주", {2: 1400, 3: 1650})[0], -(1650 + 500))

    def test_leading_blanks_are_included_in_marker_width(self):
        value, marker_end = self._value(" ㅇ 본문", {2: 1300, 3: 1550})
        self.assertEqual(marker_end, 2)
        self.assertEqual(value, -1550)

    def test_falls_back_without_blank_label_or_rule(self):
        self.assertIsNone(self._value("ㅇ본문", {1: 1000, 2: 1250})[0])           # 기호 뒤 빈칸 없음
        self.assertIsNone(self._value("ㅇ (개요) 본문", {1: 1000, 2: 1250})[0])  # 라벨 기준은 기존 규칙
        self.assertIsNone(self._value("□ 제목", {1: 1000, 2: 1250})[0])          # 규칙 없는 기호
        self.assertIsNone(self._value("ㅇ 본문", {})[0])                          # 실측 실패


class AttachmentAlignTest(unittest.TestCase):
    def test_numbers_share_the_first_number_position(self):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))
        fn = ns["문단_내어쓰기_전체_갱신"]
        texts = ["붙임  1. 만두를 먹다 1부.", "     2. 자장면을 먹다 1부.", "     3. 짬뽕도 먹다.  끝."]
        keys = [(0, i) for i in range(3)]
        targets = {key: ((keys[0], texts[0]), step) for step, key in enumerate(keys)}
        state = {"index": 0}
        hwp = Mock()
        hwp.GetPos.side_effect = lambda: (*keys[state["index"]], 0)
        applied = []

        def advance():
            state["index"] += 1
            return state["index"] < len(keys)

        patches = {
            "hwp": hwp, "hwp_run": Mock(), "순회_시작": Mock(), "중단_요청됨": lambda: False,
            "현재_한칸표인가": lambda: False, "현재문단_텍스트": lambda: texts[state["index"]],
            "_붙임목록_내어쓰기_대상수집": lambda: targets,
            "_붙임번호_기준위치_실측": lambda *args: (5000, 700),
            "_붙임목록_번호_내어쓰기_적용": lambda pos, text, 기준: applied.append(기준) or True,
            "범위_다음_문단으로_진행": advance,
        }
        with patch.dict(fn.__globals__, patches):
            self.assertTrue(fn())
        self.assertEqual(applied, [5000, 5000, 5000])


if __name__ == "__main__":
    unittest.main()
