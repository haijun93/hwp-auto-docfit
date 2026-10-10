"""화면이 위치 인자로 넘기는 작업_실행 호출이 매개변수 순서와 맞는지 확인한다.

작업_실행 중간에 새 매개변수를 끼워 넣으면 뒤의 인자가 한 칸씩 밀려 '잘못된 실행 모드' 같은
오류가 난다. 새 매개변수는 맨 끝에만 추가해야 한다.
"""
import ast
import inspect
from pathlib import Path
import runpy
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'


class RunSignatureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        cls.namespace = runpy.run_path(str(SOURCE))
        cls.params = list(inspect.signature(cls.namespace['작업_실행']).parameters)

    def _thread_args(self):
        for node in ast.walk(self.tree):
            if (isinstance(node, ast.Call) and getattr(node.func, 'attr', '') == 'Thread'
                    and any(k.arg == 'target' and getattr(k.value, 'id', '') == '작업_실행' for k in node.keywords)):
                args = next(k.value for k in node.keywords if k.arg == 'args')
                return args.elts
        self.fail('작업_실행을 실행하는 Thread 호출을 찾지 못했습니다.')

    def test_positional_call_lines_up_with_parameters(self):
        args = self._thread_args()
        self.assertLessEqual(len(args), len(self.params))
        by_name = dict(zip(self.params, args))
        self.assertEqual(ast.unparse(by_name['실행모드']), 'mode')
        # 세부 작업은 '표 제외'를 반영해 미리 만든 값이다(켜면 표 관련 작업을 모두 끈 사본).
        self.assertEqual(ast.unparse(by_name['세부작업_선택']), '세부작업')
        self.assertEqual(ast.unparse(by_name['표자간조정']), 'self.table_spacing_var.get() and (not 표제외)')
        self.assertEqual(ast.unparse(by_name['시작_인덱스']), '시작_인덱스')
        self.assertEqual(ast.unparse(by_name['쪽범위']), '작업범위')
        self.assertEqual(ast.unparse(by_name['표준서식_세부']), '표준서식_세부_전달')
        self.assertEqual(ast.unparse(by_name['표준서식_문단위간격_pt']), '문단위간격_값')
        self.assertEqual(ast.unparse(by_name['무결성보고서파일']), 'self.integrity_report_file_var.get()')
        self.assertEqual(ast.unparse(by_name['최종검수파일']), 'self.final_review_file_var.get()')

    def test_new_parameters_are_only_appended_at_the_end(self):
        self.assertEqual(self.params[-3:], ['준말_등록', '무결성보고서파일', '최종검수파일'])
        self.assertEqual(self.params.index('시작_인덱스') + 1, self.params.index('준말_등록'))

    def test_report_files_are_off_by_default(self):
        defaults = self.namespace['기본_설정']
        self.assertFalse(defaults['log_file'])
        self.assertFalse(defaults['integrity_report_file'])
        self.assertFalse(defaults['final_review_file'])


if __name__ == '__main__':
    unittest.main()
