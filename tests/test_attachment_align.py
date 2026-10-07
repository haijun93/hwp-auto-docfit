"""붙임 번호의 세로 정렬을 확인한다(내어쓰기는 종전 Shift+Tab 기준)."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class AttachmentAlignTest(unittest.TestCase):
    def test_baseline_measure_sets_pos_with_three_values(self):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))
        fn = ns["_붙임번호_기준위치_실측"]
        hwp = Mock()
        hwp.GetPos.return_value = (0, 3, 0)
        hwp.ParaShape.Item.return_value = 0
        with patch.dict(fn.__globals__, {"hwp": hwp, "hwp_run": Mock(), "_내어쓰기_값_설정": Mock()}):
            fn((0, 3), "붙임  1. 항목 1부.")  # 수집 단계의 (리스트, 문단) 두 값 위치
        for call in hwp.SetPos.call_args_list:
            self.assertEqual(len(call.args), 3)

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
