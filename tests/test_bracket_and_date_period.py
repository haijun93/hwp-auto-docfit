"""대괄호 부연설명 축소와 띄어 쓴 날짜 기간('10. 19.~11. 18.')의 한 어절 판정."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

TEXT = 'ㅇ 계량기 정기검사 실시[세부일정 붙임1] ····· 10. 19.~11. 18.'


class BracketAndDatePeriodTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_square_bracket_matches_like_parenthesis(self):
        matches = list(self.ns['괄호_정규식'].finditer(TEXT))
        self.assertEqual([m.group(0) for m in matches], ['[세부일정 붙임1]'])
        self.assertEqual(self.ns['괄호_안쪽'](matches[0]), '세부일정 붙임1')
        self.assertFalse(self.ns['괄호_문두_라벨인가'](TEXT, matches[0]))

    def test_date_period_is_one_unit(self):
        ranges = self.ns['어절_의미단위_범위'](TEXT)
        self.assertIn('10. 19.~11. 18.', [TEXT[a:b] for a, b in ranges])
        text = '기간 10. 19. ~ 11. 18. 운영'
        self.assertIn('10. 19. ~ 11. 18.', [text[a:b] for a, b in self.ns['어절_의미단위_범위'](text)])

    def split_at(self, marker, text=TEXT):
        k = marker.index('|')
        assert marker.replace('|', '') == text
        fn = self.ns['단어모드_분리정보']

        def line_range(pos):
            return ((0, 0, 0), (0, 0, k)) if pos[2] < k else ((0, 0, k), (0, 0, len(text)))

        def one_char(pos, back=False):
            i = pos[2]
            if back:
                return ((0, 0, i - 1), pos, text[i - 1]) if i > 0 else None
            return (pos, (0, 0, i + 1), text[i]) if i < len(text) else None

        with patch.dict(fn.__globals__, {
            '단어모드_줄범위': line_range, '단어모드_한글자': one_char,
            '중단_요청됨': lambda: False,
        }):
            info = fn((0, 0, 0))
        return info and text[info[2][2]:info[3][2]]

    def test_break_inside_period_is_word_split(self):
        period = '10. 19.~11. 18.'
        for i in (2, 3, 4, 8, 11, 12):
            marker = TEXT[:TEXT.index(period) + i] + '|' + TEXT[TEXT.index(period) + i:]
            self.assertEqual(self.split_at(marker), period, marker)

    def test_break_before_period_is_fine(self):
        marker = TEXT.replace('····· ', '····· |')
        self.assertIsNone(self.split_at(marker))


if __name__ == '__main__':
    unittest.main()
