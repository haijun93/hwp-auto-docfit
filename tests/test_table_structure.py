"""표 구조 정밀 조정(C1/C2/C3)과 표 칸 묶음 — 실제 한/글 검증(2026-09-25)에서 고친 동작."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class TableStructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_cells_are_grouped_by_parent_table_not_by_a1(self):
        # 가운데 열이 세로 병합된 표: A1,B1,C1,A2,C2,A3 — 예전 A1 규칙이면 첫 칸이
        # 한 칸 표로 오인되거나 표가 쪼개졌다. 표 컨트롤 앵커로 묶는다.
        fn = self.ns['표칸_묶음_수집']
        cells = {2: ('T1', 'A1', 1), 3: ('T1', 'B1', 1), 4: ('T1', 'C1', 1),
                 5: ('T1', 'A2', 2), 6: ('T1', 'C2', 2), 7: (None, None, None),
                 8: ('T2', 'A1', 1)}

        class Doc:
            pos = (0, 0, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos) if pos[0] in cells else (0, 0, 0)
        doc = Doc()
        with patch.dict(fn.__globals__, {
            'hwp': doc, '중단_요청됨': lambda: False,
            '현재_표_키': lambda: cells[doc.pos[0]][0],
            '현재_셀_주소_행번호': lambda: cells[doc.pos[0]][1:],
        }):
            groups = fn()
        self.assertEqual([[a for a, _, _ in g] for g in groups], [[2, 3, 4, 5, 6], [8]])
        with patch.dict(fn.__globals__, {'표칸_묶음_수집': lambda: groups}):
            self.assertEqual(self.ns['한칸표_영역_목록'](), {8})

    def test_column_fit_skips_tables_with_merged_cells(self):
        fn = self.ns['표_열너비_본문맞춤_시도']
        setter = Mock()
        merged = [(2, 'A', 1), (3, 'B', 1), (4, 'C', 1), (5, 'A', 2), (6, 'C', 2)]
        with patch.dict(fn.__globals__, {'표_열너비_순서대로_설정': setter, '진단로그': Mock()}):
            self.assertFalse(fn(merged, 174.0))
        setter.assert_not_called()

    def test_border_uses_cell_block_and_border_only_action(self):
        fn = self.ns['표_셀_테두리_적용']
        runs = []
        executed = []

        class PSet:
            HSet = object()
        pset = PSet()

        class Doc:
            HParameterSet = type('H', (), {'HCellBorderFill': pset})()
            HAction = type('A', (), {
                'GetDefault': lambda self, name, hset: executed.append(('default', name)),
                'Execute': lambda self, name, hset: executed.append(('execute', name)) or True})()
            def HwpLineType(self, name):
                return 'type:' + name
            def HwpLineWidth(self, name):
                return 'width:' + name
        with patch.dict(fn.__globals__, {'hwp': Doc(), 'hwp_run': runs.append, '로그': Mock()}):
            self.assertTrue(fn(아래=('DoubleSlim', '0.5mm')))
        self.assertEqual(runs, ['TableCellBlock', 'Cancel'])
        self.assertEqual(executed, [('default', 'CellBorder'), ('execute', 'CellBorder')])
        self.assertEqual((pset.BorderTypeBottom, pset.BorderWidthBottom), ('type:DoubleSlim', 'width:0.5mm'))

    def test_cell_margin_restored_when_it_cannot_reach_one_line(self):
        fn = self.ns['셀_안쪽여백_축소_시도']
        calls = []
        with patch.dict(fn.__globals__, {
            '셀_화면줄수': lambda: 2, '셀_안쪽여백_읽기': lambda: (0, 510, 510),
            '_셀_안쪽여백_단계축소': lambda: False,
            '셀_안쪽여백_현재선택': lambda mm=None, 원래값=None: calls.append(원래값) or True,
        }):
            self.assertFalse(fn())
        self.assertEqual(calls, [(0, 510, 510)])


if __name__ == '__main__':
    unittest.main()
