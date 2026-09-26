"""표 서식 표 단위 일괄 적용 — 칸마다 적용하던 결과와 같아야 한다(머리글은 1행 칸만)."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class TableBulkFormatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def _run(self, cells):
        fn = self.ns['표_헤더서식_표단위_처리']
        log = []

        class Doc:
            pos = (0, 0, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos)
                log.append(('pos', pos[0]))
        doc = Doc()
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': lambda cmd: log.append(cmd),
            '문자모양_적용_현재선택': lambda **kw: log.append(('apply', kw['폰트'])),
            '표_헤더서식_헤더_폰트': '헤더체', '표_헤더서식_헤더_크기': 12, '표_헤더서식_헤더_굵게': True,
            '표_헤더서식_본문_폰트': '본문체', '표_헤더서식_본문_크기': 13, '표_헤더서식_본문_굵게': False,
            '로그': Mock(),
        }):
            return fn(cells), log

    def test_body_for_whole_table_then_header_only_on_row_one_cells(self):
        # A1이 두 행에 걸친 표: 1행 칸(A1,B1)만 머리글, B2·C2는 본문 그대로.
        cells = [(10, 'A1', 1), (11, 'B1', 1), (12, 'B2', 2), (13, 'C2', 2), (14, 'A3', 3)]
        count, log = self._run(cells)
        self.assertEqual(count, 5)
        body = log.index(('apply', '본문체'))
        self.assertEqual(log[:body], [('pos', 10), 'Cancel', 'TableCellBlock',
                                     'TableCellBlockExtend', 'TableCellBlockExtend'])
        headers = [log[i - 3][1] for i, item in enumerate(log) if item == ('apply', '헤더체')]
        self.assertEqual(headers, [10, 11])
        self.assertNotIn('TableCellBlockRow', log)

    def test_no_a1_cell_falls_back(self):
        count, log = self._run([(20, 'B1', 1), (21, 'B2', 2)])
        self.assertIsNone(count)
        self.assertEqual(log, [])

    def test_whole_pass_skips_cells_already_done_by_table(self):
        fn = self.ns['표_헤더서식_전체_적용']
        per_cell = []
        areas = {2: 'A1', 3: 'B1', 4: 'A2'}

        class Doc:
            pos = (0, 0, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos) if pos[0] in areas or pos[0] == 5 else (0, 0, 0)
        doc = Doc()
        with patch.dict(fn.__globals__, {
            'hwp': doc, '중단_요청됨': lambda: False, '한칸표_영역_목록': lambda: set(),
            '쪽범위_사용중': lambda: False, '표_서식_표단위_사용': True,
            '표칸_묶음_키별': lambda: {(0, 1, 0): [(2, 'A1', 1), (3, 'B1', 1), (4, 'A2', 2)]},
            '표_헤더서식_표단위_처리': lambda cells: len(cells),
            '표_헤더서식_현재셀_처리': lambda: per_cell.append(doc.GetPos()[0]) or False,
            '로그': Mock(), '진단로그': Mock(),
        }):
            self.assertTrue(fn())
        self.assertEqual(per_cell, [5])      # 표가 아닌 영역(글상자 등)만 예전 경로로

    def test_table_holding_a_nested_table_keeps_per_cell_path(self):
        # 칸(area 3) 안에 다른 표(앵커 리스트 3)가 든 표는 표 단위 선택이 안쪽 표까지
        # 바꾸므로 칸마다 적용한다. 안쪽 표 자체는 표 단위로 처리한다.
        fn = self.ns['표_헤더서식_전체_적용']
        bulk, per_cell = [], []
        areas = {2, 3, 4, 5}

        class Doc:
            pos = (0, 0, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos) if pos[0] in areas else (0, 0, 0)
        doc = Doc()
        with patch.dict(fn.__globals__, {
            'hwp': doc, '중단_요청됨': lambda: False, '한칸표_영역_목록': lambda: set(),
            '쪽범위_사용중': lambda: False, '표_서식_표단위_사용': True,
            '표칸_묶음_키별': lambda: {(0, 1, 0): [(2, 'A1', 1), (3, 'B1', 1)],
                                     (3, 0, 0): [(4, 'A1', 1), (5, 'A2', 2)]},
            '표_헤더서식_표단위_처리': lambda cells: bulk.append([a for a, _, _ in cells]) or len(cells),
            '표_헤더서식_현재셀_처리': lambda: per_cell.append(doc.GetPos()[0]) or True,
            '로그': Mock(), '진단로그': Mock(),
        }):
            self.assertTrue(fn())
        self.assertEqual(bulk, [[4, 5]])
        self.assertEqual(per_cell, [2, 3])


if __name__ == '__main__':
    unittest.main()
