"""항목기호 뒤 빈칸 1개(2026-10-25), 내어쓰기는 '「' 바로 뒤 첫 글자 기준."""
from pathlib import Path
import runpy
import unittest


class MarkerBracketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_space_before_bracket_is_preserved_by_latest_invariant(self):
        span = self.ns['항목기호_낫표_빈칸_구간']
        convert = self.ns['공백규칙_글변환']
        self.assertIsNone(span(' ㅇ 「법령」 개정'))
        self.assertEqual(convert(' ㅇ 「법령」 개정'), ' ㅇ 「법령」 개정')
        punct = self.ns['문장부호뒤공백_글변환']
        self.assertEqual(punct(' ㅇ「법령」 개정'), ' ㅇ 「법령」 개정')

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


class MarkerFixedSpaceTest(unittest.TestCase):
    """항목기호 뒤 고정폭 빈칸(교육부 업무계획 'ㅇ[고정폭][고정폭]본문'): 지우고 일반 빈칸 1칸으로 맞춘다(2026-10-17)."""

    def paragraph(self, inner):
        from defusedxml import ElementTree as ET
        return ET.fromstring('<p xmlns="http://www.hancom.co.kr/hwpml/2011/paragraph">' + inner + '</p>')

    def test_fixed_spaces_after_marker_are_removed_only_there(self):
        from docfit_core import text_edit as T
        p = self.paragraph('<run><t> ㅇ<fwSpace/><fwSpace/>국가 담당관<fwSpace/>:<fwSpace/>홍</t></run>')
        self.assertEqual(T.drop_spaces_at(p, 2, 2), 2)
        self.assertEqual(T.paragraph_text(p), ' ㅇ국가 담당관:홍')
        self.assertEqual(sum(1 for c in p.iter() if c.tag.endswith('fwSpace')), 2)   # 담당관 칸 정렬용은 그대로

    def test_fixed_spaces_after_a_normal_space_and_across_runs(self):
        from docfit_core import text_edit as T
        p = self.paragraph('<run><t> ㅇ <fwSpace/>국가</t></run>')
        self.assertEqual(T.drop_spaces_at(p, 2, 3), 1)
        self.assertEqual(T.paragraph_text(p), ' ㅇ 국가')
        p = self.paragraph('<run><t> ㅇ</t></run><run><t><fwSpace/>국가</t></run>')
        self.assertEqual(T.drop_spaces_at(p, 2, 2), 1)
        self.assertEqual(T.paragraph_text(p), ' ㅇ국가')


if __name__ == '__main__':
    unittest.main()
