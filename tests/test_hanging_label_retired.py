"""내어쓰기 기준에서 '괄호 라벨 뒤 첫 글자' 규칙 폐지(2026-10-10 긴급 수정).

둘째 줄은 항상 문두기호 뒤 첫 글자에 맞춘다. 'ㅇ (개요) 본문'이면 '본'이 아니라 '('에 맞춘다.
"""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


class HangingLabelRetiredTest(unittest.TestCase):
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

    def test_parenthesis_label_is_not_the_basis_any_more(self):
        self.assertEqual(self.offset('ㅇ (개요) 본문 문장'), 2)            # '('. 예전에는 7('본')
        self.assertEqual(self.offset('□ (목적) 체험학습 전 과정'), 2)
        self.assertEqual(self.offset('- (운영방식) 현장 지원'), 2)

    def test_colon_label_is_not_the_basis_any_more(self):
        self.assertEqual(self.offset('- 추진부서 : 문화경제과'), 2)        # '추'. 예전에는 라벨 뒤
        self.assertEqual(self.offset('ㅇ 일시: 2026. 10. 10.'), 2)

    def test_label_followed_by_quotation_mark_uses_the_label_start(self):
        self.assertEqual(self.offset('ㅇ (개요)「공유재산법 시행령」 개정'), 2)

    def test_opening_quotation_right_after_the_marker_is_still_skipped(self):
        self.assertEqual(self.offset('ㅇ 「공유재산법」 개정 계획'), 3)      # 라벨이 없을 때만: '「' 다음 '공'

    def test_plain_sentence_uses_the_text_start(self):
        self.assertEqual(self.offset('ㅇ 본문 문장입니다'), 2)

    def test_paragraph_without_a_marker_has_no_basis(self):
        self.assertIsNone(self.offset('(6~16번) : 본문 문장'))              # 세트 후속 라벨은 기호가 없어 건드리지 않는다
        self.assertIsNone(self.offset('일반 문장입니다'))

    def test_saved_rules(self):
        text = 'ㅇ (개요) 본문 문장'
        self.assertEqual(self.offset(text, {'ㅇ': 'after_marker'}), 2)
        self.assertEqual(self.offset(text, {'ㅇ': 'after_label'}), 2)      # 예전에 저장한 서식은 기호 뒤로 읽는다
        self.assertIsNone(self.offset(text, {'ㅇ': 'fixed'}))
        self.assertIsNone(self.offset(text, {'ㅇ': 'none'}))

    def test_spacing_protection_still_covers_marker_and_label(self):
        # 내어쓰기 기준과 별개로, 자간·장평 조정은 문두기호+라벨까지 건드리지 않는다.
        prot = self.ns['문단_자간보호_선행부_오프셋']
        self.assertEqual(prot('ㅇ (개요) 본문 문장'), 7)
        self.assertEqual(prot('- 추진부서 : 문화경제과'), 9)
        self.assertEqual(prot('ㅇ 본문 문장'), 2)
        settings = dict(self.g['표준서식_설정'], 내어쓰기_규칙={'ㅇ': 'fixed'})
        with patch.dict(self.g, {'표준서식_설정': settings}):
            self.assertIsNone(prot('ㅇ (개요) 본문 문장'))

    def test_old_helper_is_gone(self):
        self.assertNotIn('_문단_본문시작_오프셋', self.g)
        self.assertIn('문단_자간보호_선행부_오프셋', self.g)


if __name__ == '__main__':
    unittest.main()
