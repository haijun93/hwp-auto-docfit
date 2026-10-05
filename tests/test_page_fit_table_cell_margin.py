"""페이지 수 맞춤 시 표 셀 세로 여백 연동 비례 조정 테스트."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class PageFitTableCellMarginTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_cell_vertical_margin_read_and_set(self):
        # 셀_세로여백_읽기 및 셀_세로여백_현재선택 동작 검증
        read_fn = self.ns['셀_세로여백_읽기']
        set_fn = self.ns['셀_세로여백_현재선택']

        class ShapeTableCellMock:
            def __init__(self):
                self.HasMargin = 0
                self.MarginTop = 150
                self.MarginBottom = 150

        class HShapeObjectMock:
            def __init__(self):
                self.HSet = Mock()
                self.ShapeTableCell = ShapeTableCellMock()

        pset = HShapeObjectMock()
        executed = []

        class HwpMock:
            HParameterSet = type('H', (), {'HShapeObject': pset})()
            HAction = type('A', (), {
                'GetDefault': lambda self, name, hset: True,
                'Execute': lambda self, name, hset: executed.append((pset.ShapeTableCell.HasMargin,
                                                                    pset.ShapeTableCell.MarginTop,
                                                                    pset.ShapeTableCell.MarginBottom)) or True,
            })()

        with patch.dict(read_fn.__globals__, {'hwp': HwpMock(), '로그': Mock()}):
            res = read_fn()
            self.assertEqual(res, (0, 150, 150))

            # 새 여백 적용
            success = set_fn(top_hwpunit=100, bottom_hwpunit=80)
            self.assertTrue(success)
            self.assertEqual(executed[-1], (1, 100, 80))

            # 원래값 복원
            success = set_fn(원래값=(0, 150, 150))
            self.assertTrue(success)
            self.assertEqual(executed[-1], (0, 150, 150))

    def test_table_cell_margin_bulk_adjust_proportional_and_restore(self):
        # 표_셀_세로여백_일괄조정이 원래 여백에 비례하여 축소하고, 복원 시 원래값으로 복구되는지 검증
        adjust_fn = self.ns['표_셀_세로여백_일괄조정']
        restore_fn = self.ns['표_셀_세로여백_복원']
        g = adjust_fn.__globals__

        # 표 구조 모의: 표 1(area 2, 3: 2쪽), 표 2(area 4, 5: 3쪽), 한칸표(area 6: 3쪽)
        table_groups = {
            'T1': [(2, 'A1', 1), (3, 'A2', 2)],
            'T2': [(4, 'A1', 1), (5, 'A2', 2)],
            'T3': [(6, 'A1', 1)],
        }
        page_by_area = {2: 2, 3: 2, 4: 3, 5: 3, 6: 3}
        current_margins = {
            2: [0, 200, 200],  # 2쪽 표: 최소쪽(3쪽) 이전이므로 손대지 않아야 함
            3: [0, 200, 200],
            4: [0, 200, 100],  # 3쪽 표: 원래 top 200, bottom 100
            5: [0, 300, 150],  # 3쪽 표: 원래 top 300, bottom 150
            6: [0, 200, 200],  # 한 칸 표: 건너뜀
        }
        curr_pos = [0, 0, 0]

        def get_pos():
            return tuple(curr_pos)

        def set_pos(*pos):
            curr_pos[0] = pos[0]
            curr_pos[1] = pos[1] if len(pos) > 1 else 0
            curr_pos[2] = pos[2] if len(pos) > 2 else 0

        def read_margin():
            area = curr_pos[0]
            if area in current_margins:
                return tuple(current_margins[area])
            return None

        def set_margin(top_hwpunit=None, bottom_hwpunit=None, 원래값=None):
            area = curr_pos[0]
            if area in current_margins:
                if 원래값 is not None:
                    current_margins[area] = list(원래값)
                else:
                    if top_hwpunit is not None:
                        current_margins[area][1] = top_hwpunit
                    if bottom_hwpunit is not None:
                        current_margins[area][2] = bottom_hwpunit
                return True
            return False

        hwp_mock = Mock()
        hwp_mock.HParameterSet = Mock()
        hwp_mock.GetPos = get_pos
        hwp_mock.SetPos = set_pos

        original_values = {}
        with patch.dict(g, {
            'hwp': hwp_mock,
            '중단_요청됨': lambda: False,
            '페이지맞춤_표셀세로여백_사용': True,
            '페이지맞춤_최대_pt': 10.0,
            '페이지맞춤_스텝_pt': 1.0,
            '페이지맞춤_표셀세로여백_최소_pt': 0.0,
            '한칸표_영역_목록': lambda: {6},
            '표칸_묶음_키별': lambda: table_groups,
            '현재_페이지번호': lambda: page_by_area.get(curr_pos[0], 1),
            '셀_세로여백_읽기': read_margin,
            '셀_세로여백_현재선택': set_margin,
            '로그': Mock(),
        }):
            # 스텝 1 축소 (10% 축소): 최소쪽 3쪽만 대상
            # area 4 (200, 100) -> 10% 축소 -> (180, 90)
            # area 5 (300, 150) -> 10% 축소 -> (270, 135)
            # area 2, 3 (2쪽) 및 area 6 (한칸표)은 변경 없음
            count = adjust_fn(스텝=1, 최소쪽=3, 원래값=original_values)
            self.assertEqual(count, 2)
            self.assertEqual(current_margins[4], [0, 180, 90])
            self.assertEqual(current_margins[5], [0, 270, 135])
            self.assertEqual(current_margins[2], [0, 200, 200])  # 2쪽 보존
            self.assertEqual(current_margins[6], [0, 200, 200])  # 한칸표 보존

            # 원래값 딕셔너리에 원본(변경 전) 값 보존 확인
            self.assertEqual(original_values[4], (0, 200, 100))
            self.assertEqual(original_values[5], (0, 300, 150))
            self.assertNotIn(2, original_values)

            # 스텝 2 축소 (20% 축소):
            # area 4 -> (160, 80), area 5 -> (240, 120)
            count2 = adjust_fn(스텝=2, 최소쪽=3, 원래값=original_values)
            self.assertEqual(count2, 2)
            self.assertEqual(current_margins[4], [0, 160, 80])
            self.assertEqual(current_margins[5], [0, 240, 120])

            # 복원 실행 검증
            restored_count = restore_fn(original_values)
            self.assertEqual(restored_count, 2)
            self.assertEqual(current_margins[4], [0, 200, 100])
            self.assertEqual(current_margins[5], [0, 300, 150])

    def test_page_fit_links_table_cell_margin_and_restores_on_failure(self):
        # 보고서_페이지수_맞춤_시도에서 표 셀 여백이 문단 간격과 연동되어 축소/복원되는지 검증
        fit_fn = self.ns['보고서_페이지수_맞춤_시도']
        g = fit_fn.__globals__

        para_calls, table_calls, restored = [], [], []

        def para_adjust(delta, 최소쪽=None, 위간격=False, 원래값=None):
            para_calls.append(('위' if 위간격 else '아래', delta))
            if 원래값 is not None:
                원래값[(0, len(para_calls))] = 10.0
            return 1

        def table_adjust(스텝, 최소쪽=None, 원래값=None):
            table_calls.append(스텝)
            if 원래값 is not None:
                원래값[10] = (0, 200, 200)
            return 1

        def para_restore(values, 위간격=False):
            restored.append(('문단', 위간격, len(values)))
            return len(values)

        def table_restore(values):
            restored.append(('표', len(values)))
            return len(values)

        # 실패 시나리오: 끝까지 목표 쪽수에 도달하지 못함 (마지막쪽 계속 4쪽)
        with patch.dict(g, {
            'hwp': object(),
            '중단_요청됨': lambda: False,
            '로그': Mock(),
            '구조문단_간격_일괄조정': para_adjust,
            '표_셀_세로여백_일괄조정': table_adjust,
            '마지막쪽_화면줄수': lambda: (4, 1),
            '쪽맞춤_묶음분리_있음': lambda 최소쪽=None: False,
            '구조문단_간격_복원': para_restore,
            '표_셀_세로여백_복원': table_restore,
            '페이지맞춤_최대_pt': 2.0,
            '페이지맞춤_스텝_pt': 1.0,
            '페이지맞춤_뒤쪽범위_쪽수': 1,
            '페이지맞춤_표셀세로여백_사용': True,
            '페이지맞춤_묶음확인_추가단계': 2,
            '쪽맞춤_묶음_확인됨': False,
            '쪽맞춤_묶음이동_결정': False,
        }):
            result = fit_fn(3)
            self.assertFalse(result)
            # 표 셀 여백도 각 단계마다 호출되었는지 확인
            self.assertEqual(table_calls, [1, 2, 3, 4])
            # 문단 복원 및 표 셀 복원이 모두 호출되었는지 확인
            self.assertIn(('표', 1), restored)
            self.assertTrue(any(r[0] == '문단' for r in restored))

    def test_page_fit_success_with_table_cell_margin(self):
        # 표 셀 여백 연동으로 2단계만에 목표 쪽수에 도달하여 성공하는 시나리오
        fit_fn = self.ns['보고서_페이지수_맞춤_시도']
        g = fit_fn.__globals__

        pages = iter([4, 3])  # 1단계 4쪽, 2단계 3쪽 도달
        table_calls = []

        with patch.dict(g, {
            'hwp': object(),
            '중단_요청됨': lambda: False,
            '로그': Mock(),
            '구조문단_간격_일괄조정': lambda delta, 최소쪽=None, 위간격=False, 원래값=None: 1,
            '표_셀_세로여백_일괄조정': lambda 스텝, 최소쪽=None, 원래값=None: table_calls.append(스텝) or 1,
            '마지막쪽_화면줄수': lambda: (next(pages, 3), 1),
            '쪽맞춤_묶음분리_있음': lambda 최소쪽=None: False,
            '구조문단_간격_복원': lambda values, 위간격=False: 0,
            '표_셀_세로여백_복원': lambda values: 0,
            '페이지맞춤_최대_pt': 5.0,
            '페이지맞춤_스텝_pt': 1.0,
            '페이지맞춤_뒤쪽범위_쪽수': 1,
            '페이지맞춤_표셀세로여백_사용': True,
            '페이지맞춤_묶음확인_추가단계': 2,
            '쪽맞춤_묶음_확인됨': False,
            '쪽맞춤_묶음이동_결정': False,
        }):
            result = fit_fn(3)
            self.assertTrue(result)
            self.assertEqual(table_calls, [1, 2])
            self.assertTrue(g['쪽맞춤_묶음_확인됨'])


if __name__ == '__main__':
    unittest.main()
