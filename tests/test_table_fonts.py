"""설정창의 표 머리글·본문 글꼴·크기가 표 서식 값에 반영된다."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


class TableFontsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def apply(self, fonts):
        fn = self.ns['표글꼴_적용']
        g = fn.__globals__
        with patch.dict(g, {'표_헤더서식_헤더_폰트': '한컴돋움', '표_헤더서식_헤더_크기': 13,
                            '표_헤더서식_본문_폰트': '휴먼명조', '표_헤더서식_본문_크기': 12}):
            fn(fonts)
            return (g['표_헤더서식_헤더_폰트'], g['표_헤더서식_헤더_크기'],
                    g['표_헤더서식_본문_폰트'], g['표_헤더서식_본문_크기'])

    def test_user_values_applied(self):
        self.assertEqual(self.apply({'header': {'font': '맑은 고딕', 'size': '11'},
                                     'body': {'font': '바탕', 'size': '10.5'}}),
                         ('맑은 고딕', 11, '바탕', 10.5))

    def test_blank_or_invalid_values_keep_current(self):
        self.assertEqual(self.apply({'header': {'font': ' ', 'size': 'abc'},
                                     'body': {'size': '0'}}),
                         ('한컴돋움', 13, '휴먼명조', 12))
        self.assertEqual(self.apply(None), ('한컴돋움', 13, '휴먼명조', 12))

    def test_defaults_match_built_in_table_format(self):
        self.assertEqual(self.ns['기본_설정']['table_fonts'],
                         {'header': {'font': '한컴돋움', 'size': '13'},
                          'body': {'font': '휴먼명조', 'size': '12'}})


if __name__ == '__main__':
    unittest.main()
