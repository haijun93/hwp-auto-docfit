"""*(주석1) 바로 뒤에 오는 **(주석2) 정렬 및 앞 빈칸 삭제 독립 단계 단위 테스트."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from docfit_core.stage_selection import default_choice, enabled, stages_for_mode

SOURCE = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"


class StarAlignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(SOURCE), run_name="star_align_test")

    def _doc(self, left_margin=0, text=""):
        applied = []
        current_text = [text]

        class Action:
            def CreateSet(self):
                values = {}
                return type("Set", (), {
                    "SetItem": lambda self, k, v: values.__setitem__(k, v),
                    "values": values
                })()

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

            def SelectText(self, p1, c1, p2, c2):
                return True

        return Doc(), applied, current_text

    def test_stage_selection_defaults_and_modes(self):
        """별표 정렬(star_align) 단계는 기본으로 켜져 있고 format·all 모드에 포함된다."""
        self.assertTrue(default_choice("star_align"))
        self.assertTrue(enabled({}, "star_align"))
        format_stages = [s[0] for s in stages_for_mode("format")]
        all_stages = [s[0] for s in stages_for_mode("all")]
        self.assertIn("star_align", format_stages)
        self.assertIn("star_align", all_stages)
        self.assertLess(format_stages.index("star_align"), format_stages.index("hanging_indent"))
        self.assertLess(all_stages.index("star_align"), all_stages.index("hanging_indent"))

    def test_measure_star_position(self):
        """_별표_위치_실측은 왼쪽여백 + 선행공백 폭을 합산하여 반환한다."""
        fn = self.ns["_별표_위치_실측"]
        doc, _, _ = self._doc(left_margin=2000)
        with patch.dict(fn.__globals__, {
            "hwp": doc, "hwp_run": lambda cmd: True,
            "_캐럿위치_폭_실측": lambda start, n: 1500 if n == 2 else 0,
            "진단로그": Mock(),
        }):
            pos = fn((0, 5, 0), "  * 주석1")
            self.assertEqual(pos, 3500)

    def test_star_align_deletes_space_when_margin_would_be_negative(self):
        """*와 **의 앞 공백이 같고 여백이 0이면, 필요 여백이 음수가 되므로 앞 빈칸을 삭제해 정렬한다."""
        fn = self.ns["_별표_정렬_적용"]
        doc, applied, text_box = self._doc(left_margin=0, text="  ** 주석2")
        hwp_runs = []

        def fake_hwp_run(cmd):
            hwp_runs.append(cmd)
            if cmd == "Delete":
                # 앞 공백 1칸 삭제 시뮬레이션
                if text_box[0].startswith(" "):
                    text_box[0] = text_box[0][1:]
            return True

        def fake_measure(start, n):
            # 글자수 n에 비례한 가로폭 (글자당 500)
            return 500 * n

        with patch.dict(fn.__globals__, {
            "hwp": doc, "hwp_run": fake_hwp_run, "현재_한칸표인가": lambda: False,
            "현재문단_텍스트": lambda: text_box[0],
            "_캐럿위치_폭_실측": fake_measure,
            "문단_범위_선택": lambda start, s, e: True,
            "진단로그": Mock(), "로그": Mock(),
        }):
            # 목표 별표 위치 = 1000 (공백 2칸 폭)
            # ** 시작 상태: 공백 2칸 + 별표 1글자 = 3글자 (폭 1500)
            # 필요 여백 = 1000 - 1500 = -500 (음수)
            # 공백 1칸 삭제 후: 공백 1칸 + 별표 1글자 = 2글자 (폭 1000)
            # 필요 여백 = 1000 - 1000 = 0 (정렬 완료)
            res = fn((0, 5, 0), "  ** 주석2", 1000)
            self.assertTrue(res)
            self.assertIn("Delete", hwp_runs)
            self.assertEqual(text_box[0], " ** 주석2")
            self.assertEqual(applied, [])  # 기존 여백이 이미 0이면 불필요한 COM 호출을 하지 않음

    def test_star_align_deletes_space_and_sets_remaining_margin(self):
        """앞 공백 1칸을 지운 후 남은 미세 차이를 LeftMargin으로 정확히 맞춘다."""
        fn = self.ns["_별표_정렬_적용"]
        doc, applied, text_box = self._doc(left_margin=0, text="  ** 주석2")

        def fake_hwp_run(cmd):
            if cmd == "Delete" and text_box[0].startswith(" "):
                text_box[0] = text_box[0][1:]
            return True

        with patch.dict(fn.__globals__, {
            "hwp": doc, "hwp_run": fake_hwp_run, "현재_한칸표인가": lambda: False,
            "현재문단_텍스트": lambda: text_box[0],
            "_캐럿위치_폭_실측": lambda start, n: 500 * n,
            "문단_범위_선택": lambda start, s, e: True,
            "진단로그": Mock(), "로그": Mock(),
        }):
            # 목표 별표 위치 = 1200 (공백 2칸 폭 1000 + 여백 200)
            # ** 시작 상태: 공백 2칸 + 별표 1글자 = 3글자 (폭 1500)
            # 필요 여백 = 1200 - 1500 = -300 (음수)
            # 공백 1칸 삭제 후: 공백 1칸 + 별표 1글자 = 2글자 (폭 1000)
            # 필요 여백 = 1200 - 1000 = 200 (양수)
            # -> LeftMargin이 200으로 설정됨
            res = fn((0, 5, 0), "  ** 주석2", 1200)
            self.assertTrue(res)
            self.assertEqual(text_box[0], " ** 주석2")
            self.assertEqual(applied, [{"LeftMargin": 200}])

    def test_star_align_sets_margin_without_deleting_space_when_positive(self):
        """목표 위치가 충분히 커서 필요 여백이 양수이면 앞 빈칸을 삭제하지 않고 왼쪽여백만 설정한다."""
        fn = self.ns["_별표_정렬_적용"]
        doc, applied, text_box = self._doc(left_margin=0, text="* 주석2")
        hwp_runs = []

        def fake_measure(start, n):
            return 500 * n

        with patch.dict(fn.__globals__, {
            "hwp": doc, "hwp_run": lambda cmd: hwp_runs.append(cmd) or True,
            "현재_한칸표인가": lambda: False,
            "현재문단_텍스트": lambda: text_box[0],
            "_캐럿위치_폭_실측": fake_measure,
            "문단_범위_선택": Mock(), "진단로그": Mock(), "로그": Mock(),
        }):
            # 목표 별표 위치 = 3000, **의 폭 (선행공백 0 + 별표 1글자) = 500
            # 필요 여백 = 3000 - 500 = 2500
            res = fn((0, 5, 0), "** 주석2", 3000)
            self.assertTrue(res)
            self.assertNotIn("Delete", hwp_runs)
            self.assertEqual(applied, [{"LeftMargin": 2500}])

    def test_star_align_full_pass_chain(self):
        """별표_정렬_전체_적용은 * 바로 뒤에 오는 **를 찾아 정렬 함수를 호출한다."""
        fn = self.ns["별표_정렬_전체_적용"]
        texts = ["ㅁ 제목", "ㅇ 본문", "  * 주석1", "  ** 주석2"]
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

        applied_targets = []

        def fake_apply(start, text, target):
            applied_targets.append((start[1], text.strip()[:2], target))
            return True

        changed = set()
        with patch.dict(fn.__globals__, {
            "hwp": Doc(), "hwp_run": lambda cmd: True, "중단_요청됨": lambda: False,
            "순회_시작": lambda: state.__setitem__("i", 0),
            "현재문단_텍스트": lambda: texts[state["i"]],
            "범위_다음_문단으로_진행": next_para,
            "_별표_위치_실측": lambda start, text: 1200,
            "_별표_정렬_적용": fake_apply,
            "내어쓰기_변경문단": changed, "로그": Mock(), "진단로그": Mock(),
        }):
            self.assertTrue(fn())
        # 문단 3번(** 주석2)에 대해 목표 위치 1200으로 정렬 호출됨
        self.assertEqual(applied_targets, [(3, "**", 1200)])
        self.assertEqual(changed, {(0, 3)})

    def test_star_align_chain_broken_by_other_paragraph(self):
        """*와 ** 사이에 다른 문단(※)이 끼면 바로 뒤가 아니므로 정렬하지 않는다."""
        fn = self.ns["별표_정렬_전체_적용"]
        texts = ["  * 주석1", "  ※ 참고", "  ** 주석2"]
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

        applied_targets = []

        with patch.dict(fn.__globals__, {
            "hwp": Doc(), "hwp_run": lambda cmd: True, "중단_요청됨": lambda: False,
            "순회_시작": lambda: state.__setitem__("i", 0),
            "현재문단_텍스트": lambda: texts[state["i"]],
            "범위_다음_문단으로_진행": next_para,
            "_별표_위치_실측": lambda start, text: 1200,
            "_별표_정렬_적용": lambda start, text, target: applied_targets.append(start),
            "내어쓰기_변경문단": set(), "로그": Mock(), "진단로그": Mock(),
        }):
            self.assertTrue(fn())
        self.assertEqual(applied_targets, [])

    def test_star_align_empty_line_does_not_break_chain(self):
        """*와 ** 사이에 빈 줄(공백)이 있어도 끊기지 않고 정렬 대상에 포함된다."""
        fn = self.ns["별표_정렬_전체_적용"]
        texts = ["  * 주석1", "", "   ", "  ** 주석2"]
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

        applied_targets = []

        def fake_apply(start, text, target):
            applied_targets.append((start[1], text.strip()[:2], target))
            return True

        changed = set()
        with patch.dict(fn.__globals__, {
            "hwp": Doc(), "hwp_run": lambda cmd: True, "중단_요청됨": lambda: False,
            "순회_시작": lambda: state.__setitem__("i", 0),
            "현재문단_텍스트": lambda: texts[state["i"]],
            "범위_다음_문단으로_진행": next_para,
            "_별표_위치_실측": lambda start, text: 1200,
            "_별표_정렬_적용": fake_apply,
            "내어쓰기_변경문단": changed, "로그": Mock(), "진단로그": Mock(),
        }):
            self.assertTrue(fn())
        # 빈 줄을 건너뛰고 문단 3번(** 주석2)에 대해 정렬 호출됨
        self.assertEqual(applied_targets, [(3, "**", 1200)])
        self.assertEqual(changed, {(0, 3)})

    def test_star_align_refreshes_hanging_indent(self):
        """별표 정렬 중 앞 빈칸을 삭제하거나 여백을 변경하면 문단_내어쓰기_적용이 호출된다."""
        fn = self.ns["_별표_정렬_적용"]
        doc, applied, text_box = self._doc(left_margin=0, text="  ** 주석2")
        indent_called = []

        def fake_hwp_run(cmd):
            if cmd == "Delete" and text_box[0].startswith(" "):
                text_box[0] = text_box[0][1:]
            return True

        with patch.dict(fn.__globals__, {
            "hwp": doc, "hwp_run": fake_hwp_run, "현재_한칸표인가": lambda: False,
            "현재문단_텍스트": lambda: text_box[0],
            "_캐럿위치_폭_실측": lambda start, n: 500 * n,
            "문단_범위_선택": lambda start, s, e: True,
            "문단_내어쓰기_적용": lambda start, text: indent_called.append((start, text)),
            "진단로그": Mock(), "로그": Mock(),
        }):
            res = fn((0, 5, 0), "  ** 주석2", 1000)
            self.assertTrue(res)
            self.assertEqual(len(indent_called), 1)
            self.assertEqual(indent_called[0][1], " ** 주석2")


if __name__ == "__main__":
    unittest.main()
