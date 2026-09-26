"""서식통일(TODO 3순위): 문서 안 대표 스타일 판정과 옵트인 기본값, 프리셋."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from docfit_core.stage_selection import default_choice, enabled, stages_for_mode


class StyleUnifyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_representative_style_needs_clear_majority(self):
        fn = self.ns['서식통일_대표']
        a, b = ('휴먼명조', 1500, 100), ('굴림', 1200, 100)
        self.assertEqual(fn([a] * 18 + [b] * 2), (a, 18))
        self.assertEqual(fn([a, a, b, b])[0], None)        # 50% — 뚜렷하지 않음
        self.assertEqual(fn([a, b])[0], None)              # 문단이 너무 적음

    def test_stage_is_opt_in_in_every_mode(self):
        for mode in ('spacing', 'format', 'all'):
            keys = [k for k, _ in stages_for_mode(mode)]
            self.assertIn('style_unify', keys)
            if mode != 'spacing':
                self.assertLess(keys.index('style_unify'), keys.index('standard_format'))
        self.assertFalse(default_choice('style_unify'))
        self.assertFalse(enabled(None, 'style_unify'))
        self.assertFalse(enabled({}, 'style_unify'))
        self.assertTrue(enabled({'style_unify': True}, 'style_unify'))
        self.assertTrue(enabled({}, 'body_spacing'))

    def test_only_deviating_paragraphs_are_corrected(self):
        fn = self.ns['서식통일_전체_적용']
        texts = ['ㅇ 가', 'ㅇ 나', 'ㅇ 다', 'ㅇ 라', '제목 문단']
        styles = [('한컴돋움', 1500, 100)] * 3 + [('굴림', 1200, 100)]
        state = {'i': 0}
        applied = []

        class Doc:
            def GetPos(self):
                return (0, state['i'], 0)
            def SetPos(self, *pos):
                state['i'] = pos[1]

        def next_para():
            if state['i'] >= len(texts) - 1:
                return False
            state['i'] += 1
            return True
        with patch.dict(fn.__globals__, {
            'hwp': Doc(), 'hwp_run': lambda cmd: True, '중단_요청됨': lambda: False,
            '순회_시작': lambda: state.__setitem__('i', 0), '쪽범위_안인가': lambda pos=None: True,
            '현재문단_텍스트': lambda: texts[state['i']],
            '보고서_문단역할': lambda text: '본문' if text.startswith('ㅇ') else None,
            '서식통일_표본': lambda pos, text: (styles[pos[1]], (0, pos[1], 2), (0, pos[1], 3)),
            '범위_다음_문단으로_진행': next_para, '단어모드_범위선택': lambda *a: None,
            '문자모양_적용_현재선택': lambda **kw: applied.append(kw),
            '로그': Mock(), '진단로그': Mock(),
        }):
            self.assertTrue(fn())
        # 굴림 12pt 문단 하나만, 다른 항목(글꼴·크기)만 바꾼다.
        self.assertEqual(applied, [{'폰트': '한컴돋움', '크기_pt': 15.0, '장평': None}])


class UnifyModeTest(unittest.TestCase):
    """'서식 통일'을 자간 정리·서식 적용·한 번에 적용과 따로 실행하는 작업 유형."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_unify_mode_has_only_unify_stage_and_is_on(self):
        self.assertEqual([k for k, _ in stages_for_mode('unify')], ['style_unify'])
        self.assertTrue(default_choice('style_unify', 'unify'))
        self.assertFalse(default_choice('style_unify', 'spacing'))

    def test_pipeline_runs_only_style_unify(self):
        fn = self.ns['_문서_처리_1회']
        calls = []

        def track(name):
            return lambda *a, **k: calls.append(name) or True
        g = fn.__globals__
        names = ['서식통일_전체_적용', '표준서식_전체_적용', '본문_기존자간조정', '문단_내어쓰기_전체_갱신',
                 '문장내_공백_정규화_전체_적용', '컨트롤_내부_자간조정', '표_헤더서식_전체_적용']
        with patch.dict(g, {**{n: track(n) for n in names},
                            '작업_모드': 'unify', '표준서식_사용': False, '선택_세부작업': {'style_unify': True},
                            '중단_요청됨': lambda: False, '단계표시': Mock(), '상태': Mock(), '로그': Mock(),
                            'hwp_run': lambda *a: True, '순회_시작': lambda: None}):
            self.assertTrue(fn('문서.hwpx', 회차=1))
        self.assertEqual(calls, ['서식통일_전체_적용'])

    def test_output_name_and_run_mode(self):
        fn = self.ns['저장파일명']
        with patch.dict(fn.__globals__, {'작업_모드': 'unify', '쪽범위_실제': None}):
            self.assertTrue(fn(r'C:\\문서\\보고.hwp').endswith('보고(서식통일).hwpx'))
        from docfit_core.final_evaluation import build_work_goal
        self.assertEqual(build_work_goal('unify', 1)['mode'], 'unify')


if __name__ == '__main__':
    unittest.main()
