"""알파 1-c: 공백 정규화·문장부호 뒤 공백을 XML에서. 글 반영은 차이만, 숨은 글자는 그대로."""
from pathlib import Path
import runpy
import unittest

from defusedxml import ElementTree as ET

from docfit_core import text_edit as te

HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'


def tag(e):
    return e.tag.rsplit('}', 1)[-1]


def para(inner):
    return ET.fromstring(f'<hp:p {HP}>{inner}</hp:p>')


class ApplyTextTest(unittest.TestCase):
    def test_only_differences_change_and_style_follows_previous_char(self):
        p = para('<hp:run charPrIDRef="1"><hp:t>사업,추진</hp:t></hp:run><hp:run charPrIDRef="2"><hp:t>(예산)</hp:t></hp:run>')
        self.assertTrue(te.apply_text(p, '사업, 추진(예산)'))
        runs = [r for r in p if tag(r) == 'run']
        self.assertEqual([r[0].text for r in runs], ['사업, 추진', '(예산)'])   # 넣은 빈칸은 앞 글자(쉼표)의 run에

    def test_hidden_child_elements_are_kept(self):
        p = para('<hp:run charPrIDRef="1"><hp:t>주민과의<hp:fwSpace/>대화  시간</hp:t></hp:run>')
        self.assertEqual(te.paragraph_text(p), '주민과의대화  시간')
        self.assertTrue(te.apply_text(p, '주민과의대화 시간'))
        t = p[0][0]
        self.assertEqual(len(t), 1)                     # 고정폭 빈칸 요소 그대로
        self.assertEqual((t.text, t[0].tail), ('주민과의', '대화 시간'))

    def test_no_change_returns_false(self):
        p = para('<hp:run charPrIDRef="1"><hp:t>그대로</hp:t></hp:run>')
        self.assertFalse(te.apply_text(p, '그대로'))


class TextRuleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.space = staticmethod(ns['공백규칙_글변환'])
        cls.punct = staticmethod(ns['문장부호뒤공백_글변환'])

    def test_space_rules(self):
        self.assertEqual(self.space('ㅁ 사업 개요'), '□ 사업 개요')
        self.assertEqual(self.space('예산( 1억 원 )'), '예산(1억 원)')
        self.assertEqual(self.space('교육 ,홍보'), '교육, 홍보')
        self.assertEqual(self.space('일시  :  10월'), '일시: 10월')
        self.assertEqual(self.space('주민   참여'), '주민 참여')
        self.assertEqual(self.space('1,000원'), '1,000원')        # 천 단위 쉼표는 그대로

    def test_one_cell_table_paragraph_skips_space_rules(self):
        self.assertEqual(self.space('ㅁ 교육 ,홍보( 예시 )', 한칸표=True), 'ㅁ 교육 ,홍보( 예시 )')

    def test_marker_space(self):
        self.assertEqual(self.punct('ㅇ사업 추진'), 'ㅇ 사업 추진')
        self.assertEqual(self.punct('ㅇ\t사업'), 'ㅇ 사업')
        self.assertEqual(self.punct('ㅇ 사업'), 'ㅇ 사업')


if __name__ == '__main__':
    unittest.main()
