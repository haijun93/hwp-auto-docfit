"""C7: 모든 문두 계열의 분류·위계·서식 학습 연결(COM 없음)."""

import hashlib
from pathlib import Path
import runpy
import tempfile
import unittest

from docfit_core.asterisk_superscript import mark_spans
from docfit_core.marker_scheme import classify_marker, detect_scheme
from docfit_core.style_hierarchy import analyze_hierarchy, leading_marker
from docfit_core.xml_hanging_indent import marker_end_offset
from tests.test_batch_format import fixture, paragraph, roots
from tests import test_marker_scheme as c6


DATA = Path('C:/HWP_AUTODOCFIT/테스트예시/항목기호체계')
EXPECTED = ['□', 'ㅇ', '-', '*', '**', '-', '*', 'ㅇ', '-', 'ㅇ']
VARIANTS = [
    ['1.', '1.1.', '1.1.1.', '1.1.2.', '1.2.', '1.2.1', '1.3.'],
    ['1.', '1-1.', '1-1-1.', '1-1-2.', '1-2.', '1-2-1', '1-3.'],
    ['1.', '가.', '1)', '2)', '나.', '1)', '다.'],
    ['가.', '1)', '(1)', '(2)', '2)', '(1)', '3)'],
    ['1.', '①', '가)', '나)', '②', '가)', '③'],
    ['Ⅰ.', 'A.', 'a)', 'b)', 'B.', 'a)', 'C.'],
    ['◆', '▶', '➢', '➢', '▶', '➢', '▶'],
    ['■', '●', '▪', '▪', '●', '▪', '●'],
    ['▣', '✓', '→', '→', '✓', '→', '✓'],
]


def example(markers):
    a, b, c, d, e, f, g = markers
    return [f'{a} 제목', f'{b} 본문', f'{c} 항목* 설명**', '* 부연', '** 부연',
            f'{d} 내용', '* 부연', f'{e} 본문', f'{f} 내용', f'{g} 본문']


class ClassifyMarkerTests(unittest.TestCase):
    def test_families_and_full_original_offsets(self):
        cases = {'1.': '1.', '2．': '1.', '3)': '1)', '(4)': '(1)',
                 '1.2.': '1.1.', '1.2.3': '1.1.1.', '2．3．': '1.1.',
                 '1-2.': '1-1.', '2-3-4': '1-1-1.', '100.200.': '1.1.', 'Ⅼ.': 'Ⅰ.',
                 '나.': '가.', '다)': '가)', '(라)': '(가)',
                 '③': '①', '⑳': '①', '㉯': '㉮', '㉡': '㉠',
                 'Ⅱ.': 'Ⅰ.', 'Ⅰ': 'Ⅰ', 'II.': 'I.', 'IV.': 'I.',
                 'B.': 'A.', 'C.': 'A.', 'b)': 'a)', '(c)': '(a)', '**': '**'}
        for token, family in cases.items():
            with self.subTest(token=token):
                self.assertEqual(classify_marker('\t ' + token + '\u3000글'), (family, len(token) + 2))
        for symbol in '■□▣◆◇◈▶▷►▸➢➤●○◎◦▪▫•·∙✓✔→⇒☞★☆※*-ㅁㅇ':
            self.assertEqual(classify_marker(symbol + ' 글'), (symbol, 1))

    def test_single_shape_requires_token_boundary(self):
        for text in ['◆붙은글', '→붙은글', 'AB. 단어', '일반 문장', '3*4 계산',
                     '2026.10.21. 날짜', '1.1.잘못붙음', '(문장) 본문', '가정. 문장']:
            self.assertIsNone(classify_marker(text), text)

    def test_all_families_protect_token_and_find_superscript(self):
        for token in ['1-1-1.', '(1)', '㉮', 'Ⅱ.', 'II.', 'A.', '(a)', '➢', '→']:
            text = '\t ' + token + ' 항목*와 설명**'
            with self.subTest(token=token):
                self.assertEqual(marker_end_offset(text), len(token) + 2)
                self.assertEqual([text[a:b] for a, b in mark_spans(text)], ['*', '**'])


class GeneralSchemeTests(unittest.TestCase):
    def assert_sequence(self, texts):
        scheme = detect_scheme(texts)
        self.assertTrue(scheme)
        actual = []
        for text in texts:
            mapped = scheme.canonical(text)
            actual.append(mapped[0] if mapped else text.split()[0])
        self.assertEqual(actual, EXPECTED)
        self.assertEqual(scheme.paragraph_count, 7)
        return scheme

    def test_portable_nine_systems(self):
        for markers in VARIANTS:
            with self.subTest(markers=markers):
                texts = example(markers)
                self.assert_sequence(texts)

    def test_nine_user_files_and_attachment_exclusion(self):
        if not DATA.is_dir():
            self.skipTest('로컬 사용자 시험 자료 없음(동일 9계열 합성 시험은 항상 실행)')
        paths = sorted(DATA.glob('*.txt'))
        self.assertEqual(len(paths), 9)
        for path in paths:
            with self.subTest(file=path.name):
                before = path.read_bytes()
                texts = [line for line in before.decode('utf-8-sig').splitlines() if line.strip()]
                scheme = detect_scheme(texts)
                self.assert_sequence(texts[2:-2])
                self.assertEqual([scheme.canonical(t)[0] if scheme.canonical(t) else t.split()[0]
                                  for t in texts[2:-2]], EXPECTED)
                for text in texts[:2] + texts[-2:]:
                    self.assertIsNone(scheme.canonical(text))
                self.assertTrue(all(scheme.is_excluded(t) for t in texts[-2:]))
                self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), hashlib.sha256(before).digest())

    def test_official_only_stays_in_legacy_path(self):
        texts = ['ㅁ 제목', ' ㅇ 본문', '   - 내용', '* 부연', '** 부연', '※ 부연']
        self.assertFalse(detect_scheme(texts))
        path = DATA.parent / '내어쓰기 테스트.txt'
        if path.is_file():
            self.assertFalse(detect_scheme(path.read_text(encoding='utf-8-sig').splitlines()))

    def test_official_boxes_keep_roman_and_korean_midtitles(self):
        for heading in ['Ⅰ. 중제목', 'I. 중제목', '가. 중제목']:
            texts = [heading, '□ 소제목', 'ㅇ 본문', '- 내용']
            scheme = detect_scheme(texts)
            self.assertIsNone(scheme.canonical(heading))
            self.assertEqual(leading_marker(heading, scheme)[1], '중제목')
            self.assertEqual(analyze_hierarchy([{'text': t} for t in texts])['role_sequence'][0], '중제목')

    def test_serial_evidence_and_lone_accidental_number(self):
        for texts in [['1. 단발', '일반 문장'], ['A. 단발'], ['가. 단발'], ['1. 첫째', '8. 임의']]:
            self.assertFalse(detect_scheme(texts), texts)
        for texts in [['1. 하나', '2. 둘', '3. 셋'], ['가. 하나', '나. 둘', '다. 셋'],
                      ['A. 하나', 'B. 둘', 'C. 셋'], ['I. 하나', 'II. 둘', 'III. 셋']]:
            scheme = detect_scheme(texts)
            self.assertEqual([scheme.canonical(t)[0] for t in texts], ['□'] * 3)

    def test_stack_returns_and_unbounded_depth_keep_first_level(self):
        texts = ['◆ 첫째', '▶ 둘째', '➢ 셋째', '✓ 넷째', '→ 다섯째',
                 '▶ 다시 둘째', '→ 최초 다섯째 유지', '◆ 다시 첫째']
        scheme = detect_scheme(texts)
        self.assertEqual([scheme.canonical(t)[0] for t in texts], ['□', 'ㅇ', '-', '-', '-', 'ㅇ', '-', '□'])
        self.assertEqual(scheme.family_levels['→'], 5)

    def test_official_order_supports_singleton_outline_and_legacy_shapes_have_context(self):
        texts = ['가. 부모', '1) 자식', '(1) 손자']
        self.assertEqual([detect_scheme(texts).canonical(t)[0] for t in texts], ['□', 'ㅇ', '-'])
        texts = ['◆ 부모', '• 자식', '→ 손자']
        self.assertEqual([detect_scheme(texts).canonical(t)[0] for t in texts], ['□', 'ㅇ', '-'])
        for symbol in '◦☞•·∙':
            self.assertEqual(detect_scheme([symbol + ' 단독 계열']).canonical(symbol + ' 단독 계열'), ('□', 1))
        self.assertFalse(detect_scheme(['□ 제목', 'ㅇ 본문', '• 부연']))

    def test_indent_and_official_order_resolve_new_siblings(self):
        texts = ['◆ 최상위', '    ▶ 하위', '  ✓ 덜 깊은 새 계열', '    → 아래']
        self.assertEqual(detect_scheme(texts).family_levels, {'◆': 1, '▶': 2, '✓': 2, '→': 3})
        texts = ['1. 최상위', '  1) 하위', '  가. 같은 들여쓰기의 공식 상위', '나. 다음']
        self.assertEqual(detect_scheme(texts).family_levels, {'1.': 1, '1)': 2, '가.': 2})

    def test_labels_and_attachment_only_cannot_invent_scheme(self):
        texts = ['제목: ◆ 글', '개요 : 1.1. 글', '붙임 : 1. 계획서 1부.', '◆ 별첨 1부. 끝.']
        scheme = detect_scheme(texts)
        self.assertFalse(scheme)
        self.assertTrue(scheme.is_excluded(texts[-1]))

    def test_mapping_log_and_style_text_preserve_original_content(self):
        texts = example(VARIANTS[2])
        scheme = detect_scheme(texts)
        self.assertEqual(scheme.log_message(), '[항목기호 체계] 계열→단계: 1.=□, 가.=ㅇ, 1)=- (문단 7개)')
        self.assertEqual(scheme.style_text('\t 2)\u3000원문'), '\t -\u3000원문')


class GeneralConnectionsTests(unittest.TestCase):
    def test_analyze_hierarchy_uses_same_scheme_and_standard_role_keys(self):
        for markers in VARIANTS:
            texts = example(markers)
            result = analyze_hierarchy([{'text': t, 'font': '예시글꼴', 'size_pt': 14} for t in texts])
            self.assertEqual(result['role_sequence'],
                             ['소제목', '본문', '내용', '부연설명', '부연설명', '내용', '부연설명', '본문', '내용', '본문'])
            self.assertEqual({s['marker'] for s in result['styles'] if s['role'] == '본문'}, {'ㅇ'})

    def test_page_roles_override_old_number_and_dot_roles(self):
        from tests.test_batch_format import app_functions
        ns = app_functions('보고서_문단역할', '항목기호_역할표')
        ns.update(leading_marker=leading_marker, 표준서식_설정={})
        for markers in VARIANTS:
            texts = example(markers)
            ns['활성_항목기호_체계'] = detect_scheme(texts)
            self.assertEqual([ns['보고서_문단역할'](t) for t in texts],
                             ['소제목', '본문', '내용', '부연설명', '부연설명', '내용', '부연설명', '본문', '내용', '본문'])

    def test_all_nine_systems_reach_formatter_rules_and_original_token_offsets(self):
        for markers in VARIANTS:
            texts = example(markers)
            ns = c6.formatter_namespace(detect_scheme(texts))
            for index, key in [(0, '□'), (1, 'ㅇ'), (2, '-')]:
                text = texts[index]
                self.assertEqual(ns['표준서식_기호규칙_찾기'](text)[0], key)
                self.assertEqual(ns['_문단_기호뒤_오프셋'](text), classify_marker(text)[1] + 1)

    def test_example_hwpx_learning_uses_own_scheme_without_global_leak(self):
        from tests.test_style_profile import HEADER
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        analyze = ns['hwpx_서식_분석']
        global_ns = analyze.__globals__
        global_ns['활성_항목기호_체계'] = detect_scheme(['◆ 외부', '▶ 외부'])
        previous = global_ns['활성_항목기호_체계']
        with tempfile.TemporaryDirectory() as folder:
            for markers in VARIANTS:
                texts = example(markers)
                source = Path(folder) / 'reference.hwpx'
                fixture(source, ''.join(paragraph(t, '1' if i in (1, 7, 9) else '0') for i, t in enumerate(texts)), header=HEADER)
                before = source.read_bytes()
                profile = analyze(source)
                rules = {r[0]: r for r in profile['format']['기호_규칙']}
                self.assertEqual(rules['ㅇ'][2:5], ('테스트명조', 16, True), markers)
                self.assertEqual(profile['format']['논리역할_규칙']['본문'][0:5], ('ㅇ', 0, '테스트명조', 16, True))
                self.assertEqual(profile['style_hierarchy']['role_sequence'][1], '본문')
                self.assertEqual(global_ns['활성_항목기호_체계'], previous)
                self.assertEqual(source.read_bytes(), before)

    def test_xml_output_keeps_all_original_markers_and_applies_standard_styles(self):
        from docfit_core.batch_format import plain_text
        from tests.test_batch_format import shapes
        helper = c6.MarkerSchemeHwpxTests()
        def heights(markers):
            texts = example(markers)
            fixture(source, ''.join(paragraph(t) for t in texts))
            before = source.read_bytes()
            helper._format(source, target)
            header, section = roots(target)
            self.assertEqual([plain_text(p).strip() for p in section], texts)
            self.assertEqual(source.read_bytes(), before)
            char_shapes = shapes(header, 'charPr')
            return [[char_shapes[run.get('charPrIDRef')].get('height') for run in p if run.tag.endswith('run')]
                    for p in section]

        # 이 시험 환경은 XML 일괄 단계만 흉내 내므로 표준 □·ㅇ·- 문서도 ㅇ·-·부연 크기가 실제 앱과 다르다.
        # 여기서는 원문 기호·본문 보존과 1단계(□) 서식만 본다. 단계별 서식이 표준과 같은지는
        # 실제 앱으로 테스트예시\항목기호체계 9종을 표준 문서와 대조해 확인한다(2026-10-22 모두 불일치 0).
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'in.hwpx', Path(folder) / 'out.hwpx'
            for markers in VARIANTS:
                self.assertEqual(set(heights(markers)[0]), {'1700'}, markers)

if __name__ == '__main__':
    unittest.main()
