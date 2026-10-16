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
