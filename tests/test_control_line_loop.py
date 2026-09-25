"""표 셀의 마지막 줄을 두 번 처리하지 않는다(다음 단어 당김·단어 분리 중복 방지)."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class ControlLineLoopTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def _doc(self, cell_len=10):
        """리스트 2는 한 줄짜리 셀. 셀 끝에서 MoveNextChar는 제자리에 머문다."""
        class Doc:
            pos = (0, 0, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                # 리스트 3 이상은 없는 영역: 본문으로 돌아간다.
                self.pos = tuple(pos) if pos[0] <= 2 else (0, 0, 0)
            def run(self, action):
                lst, para, i = self.pos
                if action == 'MoveLineEnd':
                    self.pos = (lst, para, cell_len)
                elif action == 'MoveNextChar':
                    self.pos = (lst, para, min(cell_len, i + 1))
        return Doc()

    def test_single_line_cell_processed_once(self):
        fn = self.ns['컨트롤_내부_자간조정']
        doc = self._doc()
        calls = []
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': doc.run, '중단_요청됨': lambda: False,
            '한칸표_영역_목록': lambda: set(), '쪽범위_사용중': lambda: False,
            '재검사_영역인가': lambda area: True, '표셀_자간_제외인가': lambda: False,
            '괄호_안쪽_공백_정리_문단_처리': lambda: None, '쉼표_공백_정리_문단_처리': lambda: None,
            '자간자동조정': lambda 최대시도=None: calls.append(doc.GetPos()) or True,
            '작업_모드': 'all', '진단로그': Mock(),
        }):
            self.assertTrue(fn())
        self.assertEqual(calls, [(2, 0, 0)])

    def test_punctuation_pass_processes_last_line_once(self):
        fn = self.ns['컨트롤_내부_문장부호_처리']
        doc = self._doc()
        calls = []
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': doc.run, '중단_요청됨': lambda: False,
            '한칸표_영역_목록': lambda: set(), '재검사_영역인가': lambda area: True,
            '컨트롤_줄병합_대상인가': lambda: True,
            '문장부호_줄병합_시도': lambda: calls.append(doc.GetPos()),
            '진단로그': Mock(),
        }):
            self.assertTrue(fn())
        self.assertEqual(calls, [(2, 0, 0)])


if __name__ == '__main__':
    unittest.main()
