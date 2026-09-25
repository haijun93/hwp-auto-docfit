"""열거 뒤 의존명사 '등'은 바로 앞 어절과 한 어절로 묶여 줄 경계 분리를 검사한다."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

TEXT = '과일은 사과, 바나나 등으로 구성된다.'


class DeungWordUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def split_at(self, marker, text=TEXT):
        """marker의 '|' 위치에서 화면줄이 바뀐 문단에서 분리된 어절을 돌려준다."""
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

    def test_break_around_space_before_deung(self):
        self.assertEqual(self.split_at('과일은 사과, 바나나 |등으로 구성된다.'), '바나나 등으로')
        self.assertEqual(self.split_at('과일은 사과, 바나나| 등으로 구성된다.'), '바나나 등으로')

    def test_break_inside_either_word(self):
        self.assertEqual(self.split_at('과일은 사과, 바나|나 등으로 구성된다.'), '바나나 등으로')
        self.assertEqual(self.split_at('과일은 사과, 바나나 등|으로 구성된다.'), '바나나 등으로')

    def test_ordinary_breaks_unchanged(self):
        self.assertIsNone(self.split_at('과일은 사과, 바나나 등으로 |구성된다.'))
        self.assertIsNone(self.split_at('과일은 |사과, 바나나 등으로 구성된다.'))
        self.assertEqual(self.split_at('과일은 사과, 바나나 등으로 구|성된다.'), '구성된다')

    def test_words_starting_with_deung_are_not_merged(self):
        text = '주민 등록 절차'
        self.assertIsNone(self.split_at('주민 |등록 절차', text))
        self.assertEqual(self.split_at('주민 등|록 절차', text), '등록')


NUM_TEXT = '수원 2, 서울 4, 용인 1등으로 구성'


class NumberCommaWordUnitTest(DeungWordUnitTest):
    """'단어 + 빈칸 + 숫자 + 쉼표'(예: '수원 2,')는 한 어절로 묶는다."""

    def test_unit_ranges(self):
        ranges = self.ns['어절_의미단위_범위'](NUM_TEXT)
        # 쉼표 없이 끝나는 마지막 항목 '용인 1등으로'도 한 어절이다.
        self.assertEqual([NUM_TEXT[a:b] for a, b in ranges],
                         ['수원 2,', '서울 4,', '용인 1등으로', '구성'])
        # 열거가 아닌 '1등'(첫째)은 묶지 않는다.
        text = '대회에서 1등으로 입상'
        self.assertEqual([text[a:b] for a, b in self.ns['어절_의미단위_범위'](text)],
                         ['대회에서', '1등으로', '입상'])

    def test_last_item_without_comma(self):
        self.assertEqual(self.split_at('수원 2, 서울 4, 용인 |1등으로 구성', NUM_TEXT), '용인 1등으로')
        self.assertEqual(self.split_at('수원 2, 서울 4, 용인| 1등으로 구성', NUM_TEXT), '용인 1등으로')
        self.assertEqual(self.split_at('수원 2, 서울 4, 용|인 1등으로 구성', NUM_TEXT), '용인 1등으로')
        self.assertEqual(self.split_at('수원 2, 서울 4, 용인 1등|으로 구성', NUM_TEXT), '용인 1등으로')
        text = '대회에서 1등으로 입상'
        self.assertIsNone(self.split_at('대회에서 |1등으로 입상', text))
        # 숫자끼리의 열거는 묶지 않는다.
        text = '순번 1, 2, 3'
        self.assertEqual([text[a:b] for a, b in self.ns['어절_의미단위_범위'](text)],
                         ['순번 1,', '2,', '3'])

    def test_break_between_word_and_number(self):
        self.assertEqual(self.split_at('수원 |2, 서울 4, 용인 1등으로 구성', NUM_TEXT), '수원 2,')
        self.assertEqual(self.split_at('수원| 2, 서울 4, 용인 1등으로 구성', NUM_TEXT), '수원 2,')
        self.assertEqual(self.split_at('수원 2, 서울 |4, 용인 1등으로 구성', NUM_TEXT), '서울 4,')

    def test_break_inside_word(self):
        self.assertEqual(self.split_at('수|원 2, 서울 4, 용인 1등으로 구성', NUM_TEXT), '수원 2,')

    def test_ordinary_breaks_unchanged(self):
        self.assertIsNone(self.split_at('수원 2, |서울 4, 용인 1등으로 구성', NUM_TEXT))
        self.assertIsNone(self.split_at('순번 1, |2, 3', '순번 1, 2, 3'))


if __name__ == '__main__':
    unittest.main()
