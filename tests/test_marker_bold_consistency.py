"""Markers whose label was bolded get their other paragraphs' headings bolded too."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class MarkerBoldConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def head(self, text):
        r = self.ns['일관성_굵게_머리말_범위'](text)
        return r and text[r[0]:r[1]]

    def test_heading_before_explanation_paren(self):
        self.assertEqual(self.head('  - 조례제정 (무료 셔틀버스 운행에 관한 조례 제정)'), '조례제정')
        self.assertEqual(self.head('  - 조례 제정 (70개 자치구 사례를 참고)'), '조례 제정')

    def test_not_a_heading(self):
        for text in ('  - 추진부서 : 운영방식에 따른 사업부서',       # 콜론 라벨: 기존 규칙
                     '  - (운영방식) 조례를 제정하여 운영',            # 괄호 라벨: 기존 규칙
                     '  - 이동형 행정서비스 유형에 따라 차량 내부 특장개조 필요',
                     '  - 서울 노원구 이동건강버스는 의료인력이 탑승해 경로당(15곳)',
                     '  - 경기도(1)',
                     '일반 문장 (설명)'):
            self.assertIsNone(self.head(text), text)

    def _apply(self, paragraphs, triggered, enabled=True):
        fn = self.ns['괄호_텍스트_크기_축소_전체_적용']
        g = fn.__globals__
        state = {'i': 0}
        bolded = []

        def process(세트후속문단=False):
            text = paragraphs[state['i']]
            if text.strip()[:1] in triggered and ':' in text:
                g['_일관성_굵게_적용기호'].add(text.strip()[:1])
            return 0

        def advance():
            state['i'] += 1
            return state['i'] < len(paragraphs)

        class Doc:
            def GetPos(self):
                return (0, state['i'], 0)

        def select(pos, start, end):
            bolded.append(paragraphs[pos[1]][start:end])

        with patch.dict(g, {
            'hwp': Doc(), '중단_요청됨': lambda: False, '순회_시작': lambda: None,
            '현재문단_텍스트': lambda: paragraphs[state['i']],
            '괄호_및_라벨_텍스트_문단_처리': process, '범위_다음_문단으로_진행': advance,
            '문단_범위_선택': select, '문자모양_적용_현재선택': lambda **kw: None,
            'hwp_run': lambda cmd: True, '로그': Mock(), '진단로그': Mock(),
            '괄호_라벨_볼드_사용': True, '_일관성_굵게_적용기호': set(),
            '문두기호_굵게_일관성_사용': enabled,
            '세트문장_시작인가': lambda t: False, '세트문장_후속문단인가': lambda *a: False,
        }):
            self.assertTrue(fn())
        return bolded

    def test_same_marker_headings_follow_bold_label(self):
        paragraphs = ['  - 추진부서 : 운영방식에 따른 사업부서',
                      '  - 조례제정 (무료 셔틀버스 운행에 관한 조례 제정)',
                      '  - 예산편성 (차량 운영비 및 운전원 인건비 편성)',
                      '  * 비고 (참고 자료 별도 첨부)']
        self.assertEqual(self._apply(paragraphs, {'-'}), ['조례제정', '예산편성'])

    def test_setting_off_disables_rule(self):
        paragraphs = ['  - 추진부서 : 운영방식에 따른 사업부서',
                      '  - 조례제정 (무료 셔틀버스 운행에 관한 조례 제정)']
        self.assertEqual(self._apply(paragraphs, {'-'}, enabled=False), [])

    def test_setting_defaults_on(self):
        self.assertIs(self.ns['기본_설정']['std_marker_bold_consistency'], True)
        self.assertTrue(self.ns['문두기호_굵게_일관성_사용'])

    def test_no_bold_label_for_marker_means_no_change(self):
        paragraphs = ['  - 조례제정 (무료 셔틀버스 운행에 관한 조례 제정)',
                      '  - 예산편성 (차량 운영비 및 운전원 인건비 편성)']
        self.assertEqual(self._apply(paragraphs, set()), [])


if __name__ == '__main__':
    unittest.main()
