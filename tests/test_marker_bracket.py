"""항목기호 뒤 여는 낫표 규칙(사용자 규칙, 2026-10-17): 빈칸 없이 붙이고, 내어쓰기는 '「' 바로 뒤 첫 글자 기준."""
from pathlib import Path
import runpy
import unittest


class MarkerBracketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_space_between_marker_and_bracket_is_removed(self):
        span = self.ns['항목기호_낫표_빈칸_구간']
        convert = self.ns['공백규칙_글변환']
        self.assertEqual(span(' ㅇ 「난세기 대비 탈수준비절차에 관한 법령」 개정'), (2, 3))
        self.assertEqual(convert(' ㅇ 「난세기 대비 탈수준비절차에 관한 법령」 개정'),
                         ' ㅇ「난세기 대비 탈수준비절차에 관한 법령」 개정')
        self.assertEqual(convert('   - 　「규칙」 준수'), '   -「규칙」 준수')

    def test_other_text_is_unchanged(self):
        span = self.ns['항목기호_낫표_빈칸_구간']
        for text in (' ㅇ「법령」 개정', '□ 정책 「법령」', ' ㅇ (라벨) 「법」', '「법령」 개정', ''):
            self.assertIsNone(span(text), text)

    def test_hanging_starts_after_the_bracket(self):
        offset = self.ns['문단_내어쓰기_기준_오프셋']
        globals_ = offset.__globals__
        saved = globals_.get('표준서식_설정')
        globals_['표준서식_설정'] = {}
        try:
            self.assertEqual(offset(' ㅇ「법령」 개정'), 3)          # '법' 위치
        finally:
            globals_['표준서식_설정'] = saved


if __name__ == '__main__':
    unittest.main()
