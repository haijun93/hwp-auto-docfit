"""*(주석1)/**(주석2) 내어쓰기 규칙(2026-09-28 사용자 요청).

**의 내어쓰기 기준위치는 *와 동일하며, **의 두 번째 별표가 바로 앞줄 *의
별표 위치와 같은 자리에 오도록 맞춘다. 사이에 다른 문단(※ 포함)이 끼면
'바로 앞줄'이 아니므로 일반 규칙(부모 본문 시작에 맞춤)으로 되돌아간다.
"""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"


class SupplementIndentApplyExtraCharsTest(unittest.TestCase):
    """_부연설명_들여쓰기_적용의 여분_글자수 파라미터(** 전용) 단위 검증."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(SOURCE), run_name="supplement_indent_extra_chars_test")

    def _doc(self, left_margin=0):
        applied = []

        class Action:
            def CreateSet(self):
                values = {}
                return type("Set", (), {"SetItem": lambda self, k, v: values.__setitem__(k, v),
                                        "values": values})()

            def Execute(self, pset):
                applied.append(dict(pset.values))
                return True

        class Doc:
            pos = (0, 5, 0)
            ParaShape = type("P", (), {"Item": lambda self, key: {"LeftMargin": left_margin}[key]})()

            def GetPos(self):
                return self.pos

            def SetPos(self, *pos):
                self.pos = tuple(pos)

            def CreateAction(self, name):
                return Action()

        return Doc(), applied

    def test_extra_char_skips_one_more_character_than_leading_whitespace(self):
        fn = self.ns["_부연설명_들여쓰기_적용"]
        doc, applied = self._doc()
        측정_호출 = []

        def measure(start, n):
            측정_호출.append(n)
            return 5000  # 선행 공백(3칸) + 별표 1글자 = 4글자만큼의 폭이라고 가정

        with patch.dict(fn.__globals__, {
            "hwp": doc, "hwp_run": lambda cmd: True, "현재_한칸표인가": lambda: False,
            "_캐럿위치_폭_실측": measure, "진단로그": Mock(), "로그": Mock(),
        }):
            self.assertTrue(fn((0, 5, 0), "   ** 내용", 15160, 여분_글자수=1))
        # 선행 공백 3칸 + 여분 1글자 = 4글자만큼의 폭을 실측해야 한다.
        self.assertEqual(측정_호출, [4])
        self.assertEqual(applied, [{"LeftMargin": 10160}])

    def test_default_extra_chars_is_zero_for_backward_compatibility(self):
        fn = self.ns["_부연설명_들여쓰기_적용"]
        doc, applied = self._doc()
        측정_호출 = []

        def measure(start, n):
            측정_호출.append(n)
            return 5000

        with patch.dict(fn.__globals__, {
            "hwp": doc, "hwp_run": lambda cmd: True, "현재_한칸표인가": lambda: False,
            "_캐럿위치_폭_실측": measure, "진단로그": Mock(), "로그": Mock(),
        }):
            fn((0, 5, 0), "    * 내용", 15160)
        self.assertEqual(측정_호출, [4])  # 여분_글자수 생략 시 선행 공백 4칸만


class SupplementIndentStarChainTest(unittest.TestCase):
    """부연설명_들여쓰기_전체_적용의 '*' → '**' 문단 간 연쇄 규칙 검증."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(SOURCE), run_name="supplement_indent_star_chain_test")

    def _run(self, texts, 여분_기록용=None):
        fn = self.ns["부연설명_들여쓰기_전체_적용"]
        state = {"i": 0}

        class Doc:
            def GetPos(self):
                return (0, state["i"], 0)

            def SetPos(self, *pos):
                state["i"] = pos[1]

        def next_para():
            if state["i"] >= len(texts) - 1:
                return False
            state["i"] += 1
            return True

        호출들 = []

        def fake_apply(start, text, 목표, 여분_글자수=0):
            marker = "**" if text.strip().startswith("**") else text.strip()[:1]
            호출들.append((start[1], marker, 목표, 여분_글자수))
            return True

        changed = set()
        with patch.dict(fn.__globals__, {
            "hwp": Doc(), "hwp_run": lambda cmd: True, "중단_요청됨": lambda: False,
            "순회_시작": lambda: state.__setitem__("i", 0),
            "현재문단_텍스트": lambda: texts[state["i"]],
            "범위_다음_문단으로_진행": next_para, "부연설명_들여쓰기_사용": True,
            "부모_본문시작_실측": lambda start, text: 1000 + start[1],
            "_부연설명_들여쓰기_적용": fake_apply,
            "내어쓰기_변경문단": changed, "로그": Mock(), "진단로그": Mock(),
            "표준서식_설정": {},
        }):
            self.assertTrue(fn())
        return 호출들

    def test_double_star_targets_immediately_preceding_single_star_position(self):
        texts = ["ㅁ 제목", "ㅇ 본문", "* 주석1", "** 주석2"]
        호출들 = self._run(texts)
        # '* 주석1'은 일반 규칙대로 부모(ㅇ 본문, 문단 1) 본문 시작(1001)에 맞춘다.
        self.assertIn((2, "*", 1001, 0), 호출들)
        # '** 주석2'는 부모가 아니라 바로 앞줄 *의 확정 위치(1001)를, 별표 1글자를
        # 더 건너뛰는 방식(여분_글자수=1)으로 맞춘다.
        self.assertIn((3, "**", 1001, 1), 호출들)

    def test_double_star_falls_back_to_parent_when_not_immediately_after_single_star(self):
        # * 와 ** 사이에 ※가 끼면 '바로 앞줄'이 아니므로 일반 규칙(부모 기준)으로 되돌아간다.
        texts = ["ㅁ 제목", "ㅇ 본문", "* 주석1", "※ 참고", "** 주석2"]
        호출들 = self._run(texts)
        self.assertIn((2, "*", 1001, 0), 호출들)
        self.assertIn((3, "※", 1001, 0), 호출들)
        # **는 직전 *를 잇지 못하므로 여분_글자수=0(일반 규칙)으로 호출된다.
        self.assertIn((4, "**", 1001, 0), 호출들)

    def test_double_star_without_any_preceding_star_uses_general_rule(self):
        texts = ["ㅁ 제목", "ㅇ 본문", "** 주석2"]
        호출들 = self._run(texts)
        self.assertEqual(호출들, [(2, "**", 1001, 0)])

    def test_two_double_stars_in_a_row_only_first_gets_the_chain(self):
        # **는 그 자체로 다음 **의 '앞줄 *' 역할을 하지 못한다(단일 * 문단만 인정).
        texts = ["ㅁ 제목", "ㅇ 본문", "* 주석1", "** 주석2a", "** 주석2b"]
        호출들 = self._run(texts)
        self.assertIn((2, "*", 1001, 0), 호출들)
        self.assertIn((3, "**", 1001, 1), 호출들)   # 첫 **만 *를 잇는다
        self.assertIn((4, "**", 1001, 0), 호출들)   # 둘째 **는 일반 규칙


if __name__ == "__main__":
    unittest.main()
