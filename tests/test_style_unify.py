"""서식통일(TODO 3순위): 문서 안 대표 스타일 판정과 옵트인 기본값, 프리셋."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

from docfit_core.stage_selection import default_choice, enabled, stages_for_mode
from docfit_core.style_unify import parenthetical_spans


class StyleUnifyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_font_and_size_modes_are_independent(self):
        fn = self.ns['서식통일_대표']
        samples = [('함초롬바탕', 1500), ('함초롬바탕', 1200), ('함초롬바탕', 1500),
                   ('굴림', 1500), ('굴림', 1200)]
        result = fn(samples)
        self.assertEqual((result['font'], result['size']), (('함초롬바탕', 3), (1500, 3)))
        self.assertEqual(result['marker_bold'], (None, 0))
        # 표본 두 개가 같으면 대표값으로 인정하고, 다르면(크기 1500 vs 1200) 판정을 보류한다.
        tied = fn(samples[:2])
        self.assertEqual((tied['font'], tied['size']), (('함초롬바탕', 2), (None, 0)))

    def test_stage_is_opt_in_in_every_mode(self):
        for mode in ('spacing', 'format', 'all'):
            keys = [k for k, _ in stages_for_mode(mode)]
            self.assertIn('style_unify', keys)
            if mode != 'spacing':
                # 보고서 표준서식은 준말 변환 다음 다른 모든 단계보다 먼저 실행한다(서식통일보다도 먼저).
                self.assertLess(keys.index('standard_format'), keys.index('style_unify'))
        self.assertFalse(default_choice('style_unify'))
        self.assertFalse(enabled(None, 'style_unify'))
        self.assertFalse(enabled({}, 'style_unify'))
        self.assertTrue(enabled({'style_unify': True}, 'style_unify'))
        self.assertTrue(enabled({}, 'body_spacing'))
        self.assertFalse(default_choice('reset_spacing', 'unify'))
        self.assertFalse(enabled({'style_unify': True}, 'reset_spacing', 'unify'))
        self.assertTrue(enabled({}, 'reset_spacing', 'spacing'))

    # 예외 문장만 고치기·표준 문장 무변경·마무리 묶음 순서는 현재 설계 기준으로
    # tests/test_style_unify_auto.py에서 검사한다.

    def test_saved_result_audit_is_read_only_and_detects_remaining_mismatch(self):
        fn = self.ns['서식통일_전체_적용']
        texts = ['ㅇ 하나', 'ㅇ 둘', 'ㅇ 셋']
        styles = [('한컴돋움', 1500, 500), ('한컴돋움', 1500, 500), ('한컴돋움', 1200, 500)]
        state = {'i': 0}
        writes = []
        profile = {('ㅇ', '본문', '문서 공통'): {
            'font': ('한컴돋움', 3), 'size': (1500, 3), 'prev_spacing': (500, 3),
            'marker_bold': (False, 3), 'label_bold': (None, 0),
        }}

        class Doc:
            def GetPos(self):
                return (0, state['i'], 0)
            def SetPos(self, *pos):
                state['i'] = pos[1]

        def advance():
            if state['i'] >= len(texts) - 1:
                return False
            state['i'] += 1
            return True

        def sample(pos, text):
            idx = pos[1]
            style = styles[idx]
            run = ((0, idx, 0), (0, idx, len(text)), style[:2], len(text), False)
            return (style[0], style[1], (run,), {'prev_spacing': style[2]}), pos, (0, idx, len(text))

        with patch.dict(fn.__globals__, {
            '서식통일_보류자간_재조정': lambda: True,
            '문단_내어쓰기_기준_오프셋': lambda text: None,
            'hwp': Doc(), 'hwp_run': lambda *args: True,
            '중단_요청됨': lambda: False, '순회_시작': lambda: state.__setitem__('i', 0),
            '쪽범위_안인가': lambda pos=None: True,
            '현재문단_텍스트': lambda: texts[state['i']],
            '보고서_문단역할': lambda text: '본문',
            '서식통일_표본': sample,
            '_서식통일_그룹키': lambda marker, text, pos: ('ㅇ', '본문', '문서 공통'),
            '다음_문단으로_진행': advance,
            '_문단_내어쓰기_기준_오프셋': lambda text: None,
            '문단_내어쓰기_기준_오프셋': lambda text: None,
            '_서식통일_문서대표프로필': profile,
            '단어모드_범위선택': lambda *args: writes.append(('select', args)),
            '문자모양_적용_현재선택': lambda **kwargs: writes.append(('char', kwargs)),
            '로그': Mock(), '진단로그': Mock(),
        }):
            result = fn(고정_프로필_재적용=True, 검증만=True)

        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['checked'], 3)
        self.assertEqual(result['issues'], [{
            'text': 'ㅇ 셋', 'fields': ['size'],
            'expected_actual': {'size': {'expected': 1500, 'actual': [1200]}},
        }])
        self.assertEqual(writes, [])

    def test_only_inconsistent_runs_are_selected_and_highlights_are_preserved(self):
        fn = self.ns['_서식통일_불일치_구간']
        baseline = ('함초롬바탕', 1500)
        wrong = ('굴림', 1200)
        runs = (
            ((0, 0, 2), (0, 0, 5), baseline, 3),
            ((0, 0, 5), (0, 0, 8), wrong, 3),
            ((0, 0, 8), (0, 0, 10), baseline, 2),
            ((0, 0, 10), (0, 0, 13), wrong, 3),
        )
        self.assertEqual(fn((baseline[0], baseline[1], runs), None, None,
                            baseline[0], baseline[1]),
                         [((0, 0, 5), (0, 0, 8)), ((0, 0, 10), (0, 0, 13))])

    def test_inline_parentheses_are_not_part_of_base_font_size_correction(self):
        mismatch = self.ns['_서식통일_불일치_구간']
        aside_mismatch = self.ns['_서식통일_부연괄호_불일치_구간']
        base = ('한컴돋움', 1500)
        base_run = (((0, 0, 0), (0, 0, 8), base, 8),)
        source_size = 1300
        inline = {
            'parenthetical_size_runs': (
                ((0, 0, 8), (0, 0, 14), source_size, 6),
            ),
        }
        sample = (base[0], base[1], base_run, inline)

        self.assertEqual(mismatch(sample, (0, 0, 0), (0, 0, 14), base[0], base[1]), [])
        self.assertEqual(aside_mismatch(sample, 1500), ([], 1300))

        # 이미 본문보다 2pt 작은 괄호는 건드리지 않고, 잘못 본문과 같은
        # 크기인 경우에만 해당 괄호 범위를 13pt로 교정한다.
        inline['parenthetical_size_runs'] = (
            ((0, 0, 8), (0, 0, 14), 1500, 6),
        )
        self.assertEqual(aside_mismatch(sample, 1500),
                         ([((0, 0, 8), (0, 0, 14))], 1300))

    def test_inline_parenthetical_font_is_standardized_without_resetting_minus_two_size(self):
        mismatch = self.ns['_서식통일_불일치_구간']
        base = ('한컴돋움', 1500)
        wrong_aside_font = ('굴림', 1300)
        runs = (
            ((0, 0, 0), (0, 0, 4), base, 4, False),
            ((0, 0, 4), (0, 0, 10), wrong_aside_font, 6, True),
        )
        self.assertEqual(
            mismatch((base[0], base[1], runs), None, None, base[0], None),
            [((0, 0, 4), (0, 0, 10))],
        )
        self.assertEqual(
            mismatch((base[0], base[1], runs), None, None, None, base[1]), []
        )

    def test_inline_parenthetical_scanner_protects_leading_label_and_nesting(self):
        text = 'ㅇ (개요) 본문 (참고(세부)) 마침'
        marker, label = self.ns['_서식통일_문두요소_범위'](text)
        spans = parenthetical_spans(text, tuple(s for s in (marker, label) if s))
        self.assertEqual([text[start:end] for start, end in spans], ['(참고(세부))'])

    def test_terminal_reference_parenthesis_is_not_an_inline_aside(self):
        text = '추진일정 계획표를 참조 바람(붙임1).'
        self.assertEqual(parenthetical_spans(text), ())
        text = '설명(참고자료), 이후 본문'
        spans = parenthetical_spans(text)
        self.assertEqual([text[start:end] for start, end in spans], ['(참고자료)'])

    def test_unify_sample_uses_run_frequency_and_preserves_mixed_runs(self):
        from tempfile import TemporaryDirectory
        from zipfile import ZipFile
        from defusedxml import ElementTree as ET
        from docfit_core.style_inventory import _parse_fonts, _parse_char, _tag
        source = Path(__file__).resolve().parents[1] / 'tests' / 'fixtures' / 'style_unify_mixed.hwpx'
        with TemporaryDirectory() as temp:
            doc = Path(temp) / 'sample.hwpx'
            source = Path(temp) / 'source.hwpx'
            with ZipFile(doc, 'w') as archive:
                header = '''<?xml version="1.0" encoding="UTF-8"?><hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"><hh:fontface lang="HANGUL"><hh:font id="0" face="함초롬바탕"/><hh:font id="1" face="굴림"/></hh:fontface><hh:charProperties><hh:charPr id="0" height="1500"><hh:fontRef hangul="0"/></hh:charPr><hh:charPr id="1" height="1200"><hh:fontRef hangul="1"/></hh:charPr><hh:charPr id="2" height="1300"><hh:fontRef hangul="0"/></hh:charPr></hh:charProperties></hh:head>'''
                section = '''<?xml version="1.0" encoding="UTF-8"?><hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p><hp:run charPrIDRef="0"><hp:t>ㅇ 기준서식 문장이 충분히 깁니다 기준서식 문장이 충분히 깁니다< hp:fwSpace/></hp:t></hp:run><hp:run charPrIDRef="1"><hp:t>이 짧은 부분만 다른 서식입니다 </hp:t></hp:run><hp:run charPrIDRef="2"><hp:t>(부연 괄호) 뒤</hp:t></hp:run></hp:p></hp:sec>'''
                archive.writestr('Contents/header.xml', header)
                archive.writestr('Contents/section0.xml', section.replace('< hp:', '<hp:'))
            with ZipFile(source, 'w') as archive:
                archive.writestr('Contents/header.xml', header)
                archive.writestr('Contents/section0.xml', section.replace('< hp:', '<hp:'))
            fn = self.ns['서식통일_표본']
            fake_hwp = Mock()
            fake_hwp.Path = str(source)
            diagnostics = []
            with patch.dict(fn.__globals__, {'hwp': fake_hwp, '진단로그': diagnostics.append}):
                sample = fn((0, 0, 0), 'ㅇ 기준서식 문장이 충분히 깁니다 기준서식 문장이 충분히 깁니다 이 짧은 부분만 다른 서식입니다 (부연 괄호) 뒤')
            self.assertIsNotNone(sample, diagnostics)
            shape = sample[0]
            self.assertEqual(shape[0], '함초롬바탕')
            self.assertEqual(shape[1], 1500)
            # Inline aside split keeps the after-parenthesis body segment separate.
            self.assertEqual(len(shape[2]), 4)
            aside_ranges = [run for run in shape[2] if run[4]]
            self.assertEqual(len(aside_ranges), 1)
            aside = aside_ranges[0]
            self.assertTrue(any(not run[4] and run[0][2] >= aside[1][2]
                                for run in shape[2]))
            self.assertEqual(shape[3]['parenthetical_size_runs'][0][2], 1300)
            # 대표 서식 범위에는 문두기호와 괄호 라벨도 포함한다.
            self.assertEqual(sample[1], (0, 0, 0))
            self.assertEqual(shape[2][0][0], (0, 0, 0))

    def sample_for(self, runs):
        """(charPr 번호, 글자) 목록으로 문단 하나짜리 HWPX를 만들어 표본을 뽑는다."""
        from tempfile import TemporaryDirectory
        from zipfile import ZipFile
        header = ('<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"><hh:fontface lang="HANGUL">'
                  '<hh:font id="0" face="함초롬바탕"/><hh:font id="1" face="굴림"/></hh:fontface><hh:charProperties>'
                  '<hh:charPr id="0" height="1500"><hh:fontRef hangul="0"/></hh:charPr>'
                  '<hh:charPr id="1" height="1100"><hh:fontRef hangul="1"/></hh:charPr></hh:charProperties></hh:head>')
        body = "".join(f'<hp:run charPrIDRef="{char}"><hp:t>{text}</hp:t></hp:run>' for char, text in runs)
        section = f'<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p>{body}</hp:p></hp:sec>'
        with TemporaryDirectory() as temp:
            source = Path(temp) / 'source.hwpx'
            with ZipFile(source, 'w') as archive:
                archive.writestr('Contents/header.xml', header)
                archive.writestr('Contents/section0.xml', section)
            fn = self.ns['서식통일_표본']
            fake_hwp = Mock()
            fake_hwp.Path = str(source)
            with patch.dict(fn.__globals__, {'hwp': fake_hwp, '진단로그': Mock(),
                                             '_서식통일_HWPX_캐시': {}}):
                return fn((0, 0, 0), "".join(text for _, text in runs))

    def test_inline_reference_note_keeps_its_own_style(self):
        # 실측(정책회의): 'ㅇ 모집기간: … 마감시  ※ 일부 프로그램 상이'의 11pt ※ 참고가 15pt로 커졌다.
        lead = 'ㅇ 모집기간: 2026. 9. 10.(목) ~ 선착순 마감시  '
        sample = self.sample_for([(0, lead), (1, '※ 일부 프로그램 상이')])
        self.assertIsNotNone(sample)
        shape, start, end = sample
        self.assertEqual((shape[0], shape[1]), ('함초롬바탕', 1500))
        body_end = len(lead.rstrip())
        self.assertEqual(end, (0, 0, body_end))
        self.assertTrue(all(run[1][2] <= body_end for run in shape[2]))
        self.assertTrue(all(run[1][2] <= body_end for run in shape[3]['color_runs']))

    def test_note_marker_inside_parentheses_follows_parenthesis_rule(self):
        text = '□ 활용대상: 전기버스 4대(※차량원복시 23인승)'
        sample = self.sample_for([(0, text)])
        self.assertEqual(sample[2], (0, 0, len(text)))
        self.assertEqual(len(sample[0][3]['parenthetical_size_runs']), 1)

    def test_leading_note_marker_is_not_an_inline_note(self):
        text = '※ 기존 28개소 → 설치 후 총 39개소'
        self.assertEqual(self.sample_for([(1, text)])[2], (0, 0, len(text)))

class UnifyModeTest(unittest.TestCase):
    """'서식 통일'을 자간 정리·서식 적용·한 번에 적용과 따로 실행하는 작업 유형."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_unify_mode_has_only_unify_stage_and_is_on(self):
        # 기본 표 서식(준말 '표')을 먼저 입히고, 쪽 맞춤은 서식통일 뒤 사용자가 켤 때만 실행한다.
        # 준말 변환·보고서 표준서식은 서식 통일에서 하지 않는다.
        self.assertEqual([k for k, _ in stages_for_mode('unify')], ['table_style', 'style_unify', 'unify_spacing', 'table_unify', 'page_fit', 'page_layout_keep'])
        self.assertTrue(default_choice('table_style', 'unify'))
        for key in ('abbreviation', 'standard_format'):
            self.assertFalse(default_choice(key, 'unify'), key)
        self.assertFalse(default_choice('page_fit', 'unify'))
        self.assertTrue(default_choice('table_unify', 'unify'))
        self.assertTrue(default_choice('style_unify', 'unify'))
        self.assertTrue(default_choice('unify_spacing', 'unify'))   # 서식통일 문장 자간 정리(카드 '자간 정리 제외'와 연동)
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

    def test_standard_format_is_not_repeated_inside_the_pass(self):
        """보고서 표준서식은 선행 단계(표준서식_선행_적용)에서 이미 입혔으므로 회차 안에서 다시 하지 않는다."""
        fn = self.ns['_문서_처리_1회']
        g = fn.__globals__
        calls = []
        names = ['표준서식_전체_적용', '문장내_공백_정규화_전체_적용', '문장부호_뒤_공백_보정_전체_적용']
        with patch.dict(g, {**{n: (lambda n: lambda *a, **k: calls.append(n) or True)(n) for n in names},
                            '작업_모드': 'format', '표준서식_사용': True, '선택_세부작업': {},
                            'stage_enabled': lambda selection, key, mode=None: key in ('normalize_space', 'standard_format'),
                            '중단_요청됨': lambda: False, '단계표시': Mock(), '상태': Mock(), '로그': Mock(),
                            '진단로그': Mock(), 'hwp_run': lambda *a: True, '순회_시작': lambda: None,
                            '표_셀_안쪽여백_전체_적용': lambda: True, '표_열너비_본문맞춤_전체_적용': lambda: True,
                            '표_테두리_전체_적용': lambda: True}):
            self.assertTrue(fn('문서.hwpx', 회차=1))
        self.assertEqual(calls, ['문장내_공백_정규화_전체_적용'])

    def test_leading_standard_format_defers_hanging_indent(self):
        fn = self.ns['표준서식_선행_적용']
        g = fn.__globals__
        seen = []

        def standard():
            seen.append((g['작업_모드'], g['최종_내어쓰기_예정']))
            return True
        for mode in ('format', 'all'):
            with patch.dict(g, {'표준서식_전체_적용': standard, '작업_모드': mode, '표준서식_선행_사용': True,
                                '표준서식_내어쓰기_사용': True, '선택_세부작업': {},
                                '단계표시': Mock(), '상태': Mock(), 'hwp_run': lambda *a: True,
                                '순회_시작': lambda: None}):
                self.assertTrue(fn('문서.hwpx'))
                self.assertFalse(g['최종_내어쓰기_예정'])          # 끝나면 되돌린다
        # 최종 내어쓰기 단계가 뒤에 있으므로 표준서식 안의 문단별 내어쓰기는 미룬다.
        self.assertEqual(seen, [('format', True), ('all', True)])
        for off in ({'표준서식_선행_사용': False}, {'선택_세부작업': {'standard_format': False}}):
            with patch.dict(g, {'표준서식_전체_적용': standard, '작업_모드': 'format', '표준서식_선행_사용': True,
                                '선택_세부작업': {}, **off}):
                self.assertIsNone(fn('문서.hwpx'))
        self.assertEqual(len(seen), 2)

    def test_all_mode_rechecks_using_frozen_document_profile_after_other_stages(self):
        fn = self.ns['_문서_처리_1회']
        g = fn.__globals__
        calls = []

        def unify(**kwargs):
            calls.append(kwargs)
            if not kwargs:
                g['_서식통일_문서대표프로필'] = {('ㅇ', '본문', '문서 공통'): {'font': ('한컴돋움', 3)}}
            return True

        with patch.dict(g, {
            '서식통일_전체_적용': unify,
            '작업_모드': 'all', '표준서식_사용': False,
            '선택_세부작업': {'style_unify': True},
            'stage_enabled': lambda selection, key, mode=None: key == 'style_unify',
            '중단_요청됨': lambda: False, '단계표시': Mock(), '상태': Mock(), '로그': Mock(),
            '진단로그': Mock(), 'hwp_run': lambda *a: True, '순회_시작': lambda: None,
        }):
            self.assertTrue(fn('문서.hwpx', 회차=1))

        self.assertEqual(calls, [{}, {'고정_프로필_재적용': True}])

    def test_output_name_and_run_mode(self):
        fn = self.ns['저장파일명']
        with patch.dict(fn.__globals__, {'작업_모드': 'unify', '쪽범위_실제': None}):
            self.assertTrue(fn(r'C:\\문서\\보고.hwp').endswith('보고(서식통일).hwpx'))
        from docfit_core.final_evaluation import build_work_goal
        self.assertEqual(build_work_goal('unify', 1)['mode'], 'unify')


if __name__ == '__main__':
    unittest.main()
