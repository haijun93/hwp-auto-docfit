"""콜론 공백 규칙(2026-10-10): 글자와 ':' 사이 0칸, ':' 뒤 다음 글자와 정확히 1칸."""
from pathlib import Path
import runpy
import unittest


def apply(edits, text):
    for 시작, 끝, 교체 in reversed(edits):
        text = text[:시작] + 교체 + text[끝:]
    return text


class ColonSpacingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.target = staticmethod(ns['콜론_공백_보정_대상'])

    def fix(self, text):
        return apply(self.target(text), text)

    def test_space_before_colon_removed_and_one_space_after(self):
        self.assertEqual(self.fix('- 추진부서 : 문화경제과'), '- 추진부서: 문화경제과')
        self.assertEqual(self.fix('- (운영방식) : 현장 지원'), '- (운영방식): 현장 지원')
        self.assertEqual(self.fix('근거 :  지방재정법'), '근거: 지방재정법')
        self.assertEqual(self.fix('근거:\t지방재정법'), '근거: 지방재정법')
        self.assertEqual(self.fix('근거 ：지방재정법'), '근거： 지방재정법')   # 전각 콜론 문자는 그대로

    def test_missing_space_after_colon_inserted_next_to_hangul(self):
        self.assertEqual(self.fix('비고:내용'), '비고: 내용')
        self.assertEqual(self.fix('2025:행사'), '2025: 행사')

    def test_already_correct_is_untouched(self):
        for t in ('비고: 내용', '교육내용: 성희롱 예방교육', '일    시: 10. 19.'):
            self.assertEqual(self.target(t), [], t)

    def test_exclusions(self):
        for t in ('회의 10:30 시작', '비율 3 : 1', 'http://a.kr', 'mailto:abc@x.kr',
                  'C:\\data', 'a::b', ':시작', '비고:'):
            self.assertEqual(self.fix(t), t, t)

    def test_trailing_colon_only_tightens_left(self):
        self.assertEqual(self.fix('아래와 같음 :'), '아래와 같음:')

    def test_colon_before_closing_bracket_not_spaced(self):
        self.assertEqual(self.fix('(예 :)'), '(예:)')

    def test_multiple_colons(self):
        self.assertEqual(self.fix('가 : 나 , 다 : 라'), '가: 나 , 다: 라')


if __name__ == '__main__':
    unittest.main()
