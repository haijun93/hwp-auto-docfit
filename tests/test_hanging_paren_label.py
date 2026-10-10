"""내어쓰기 기준 개정(2026-10-10): 괄호 라벨 '( )'은 라벨 뒤가 아니라 기호 뒤 첫 글자, 콜론 ':' 라벨은 현행 유지."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


class HangingParenLabelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        func = cls.ns['문단_내어쓰기_기준_오프셋']
        cls.fn = staticmethod(func)
        cls.g = func.__globals__

    def offset(self, text, rules=None):
        settings = dict(self.g['표준서식_설정'], 내어쓰기_규칙=rules or {})
        with patch.dict(self.g, {'표준서식_설정': settings}):
            return self.fn(text)

    def protect(self, text, rules=None):
        settings = dict(self.g['표준서식_설정'], 내어쓰기_규칙=rules or {})
        with patch.dict(self.g, {'표준서식_설정': settings}):
            return self.ns['문단_자간보호_선행부_오프셋'](text)

    def test_parenthesis_label_uses_the_first_character_after_the_marker(self):
        self.assertEqual(self.offset('ㅇ (개요) 본문 문장'), 2)            # '('. 예전에는 7('본')
        self.assertEqual(self.offset('□ （목적） 체험학습 전 과정'), 2)       # 전각 괄호
        self.assertEqual(self.offset('- (운영방식) 현장 지원'), 2)
        self.assertEqual(self.offset('ㅇ (개요)「공유재산법 시행령」 개정'), 2)  # 라벨 뒤 낫표와 무관
        self.assertEqual(self.offset(' ㅇ (개요) 「공유재산법」에 따라'), 3)

    def test_square_bracket_label_uses_the_first_character_after_the_marker(self):
        self.assertEqual(self.offset('ㅇ [대상] 초·중·고등학교'), 2)         # '['

    def test_colon_label_is_unchanged(self):
        self.assertEqual(self.offset('- 추진부서 : 문화경제과'), 9)           # 콜론 뒤 '문'
        self.assertEqual(self.offset(' ㅇ 교육내용: 성희롱 예방교육'), 9)      # 콜론 뒤 본문
        self.assertEqual(self.offset(' - 근거 : 『지방재정법』 제17조'), 9)

    def test_parenthesis_label_followed_by_colon_is_a_colon_label(self):
        self.assertEqual(self.offset('- (운영방식) : 현장 지원'), 11)          # 콜론 라벨: 콜론 뒤(현행)
        self.assertEqual(self.offset('(6~16번) : 본문 문장'), 10)             # 기호 없는 세트 후속 라벨(현행)

    def test_year_parenthesis_and_plain_text_are_unchanged(self):
        self.assertEqual(self.offset(' ㅇ (2026)서울'), 3)
        self.assertEqual(self.offset('ㅇ 본문 문장입니다'), 2)
        self.assertEqual(self.offset(' ㅇ 「공유재산법」에 따라'), 4)           # 문두기호 바로 뒤 낫표 다음 글자(현행)

    def test_saved_rules_are_unchanged(self):
        text = 'ㅇ (개요) 본문 문장'
        self.assertEqual(self.offset(text, {'ㅇ': 'after_marker'}), 2)
        self.assertEqual(self.offset(text, {'ㅇ': 'after_label'}), 2)        # 라벨 규칙: 괄호는 기호 뒤
        self.assertIsNone(self.offset(text, {'ㅇ': 'fixed'}))
        self.assertIsNone(self.offset(text, {'ㅇ': 'none'}))

    def test_spacing_protection_still_covers_the_parenthesis_label(self):
        self.assertEqual(self.protect('ㅇ (개요) 본문 문장'), 7)             # 자간 보정은 라벨을 건드리지 않는다
        self.assertEqual(self.protect(' ※ (참고) 본문'), 8)
        self.assertEqual(self.protect('- 추진부서 : 문화경제과'), 9)
        self.assertEqual(self.protect('ㅇ (개요) 본문', {'ㅇ': 'after_marker'}), 2)
        self.assertIsNone(self.protect('ㅇ (개요) 본문', {'ㅇ': 'fixed'}))


if __name__ == '__main__':
    unittest.main()
