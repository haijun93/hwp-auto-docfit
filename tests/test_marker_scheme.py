"""C6: 변형 기호 체계와 실제 formatter 연결(COM 호출 없음)."""

from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import Mock

from docfit_core.marker_scheme import MarkerScheme, detect_scheme, detect_hwpx_scheme
from docfit_core.marker_prefix import expected_prefix, normalize_prefix, audit_hwpx_prefixes
from docfit_core.style_hierarchy import leading_marker, DOT_MARKERS
from docfit_core.xml_hanging_indent import (
    DEFAULT_SYMBOL_RULES, marker_end_offset, hanging_indent_offset,
    consistent_reference_pair, prefix_width_hwpunit, reference_hanging_indent_pair,
)
from tests.test_batch_format import app_functions, fixture, paragraph, roots, shapes
from docfit_core.batch_format import plain_text, tag
from docfit_core.document_rules import marker_space_fix


DECIMAL_TEXTS = ['1. 추진 배경', '1.1. (삼체 행성 상황) 설명', '1.1.1. 항세기와 난세기',
                 '* 항세기: 설명', '** 난세기: 설명', '1.1.2. 탈수 대응',
                 '1.2. (지구 확인 경과) 설명', '1.2.1 항성계 안정', '1.3. 판단',
                 '붙임 : 1. 시행계획 1부.', '2. 스케줄표 1부.  끝.']


def formatter_namespace(scheme=None):
    ns = app_functions('표준서식_기호규칙_찾기', '_부모문단_유형',
                       '_문단_공백_건너뛰기', '_문단_기호뒤_오프셋',
                       '_문단_본문시작_오프셋', '문단_내어쓰기_기준_오프셋',
                       '_여는낫표_건너뛰기', '복사_내어쓰기_규칙', '표준서식_문단위간격_찾기')
    ns.update(활성_항목기호_체계=scheme,
              표준서식_설정={'기호_규칙': DEFAULT_SYMBOL_RULES},
              표준서식_기호_별칭={'ㅁ': '□', '○': 'ㅇ'}, leading_marker=leading_marker,
              DOT_MARKERS=DOT_MARKERS, _제목_기호=set('□ㅁ■'), _본문_기호=set('ㅇ○●◦'),
              _내용_기호=set('-–—‒−―'), 공문서_기호=set('□ㅇ-*※'),
              항목_패턴=[re.compile(r'^\d+\.')], _내어쓰기_건너뛸_여는낫표=set('「『'))
    return ns


class MarkerSchemeTests(unittest.TestCase):
    def test_decimal_depths_and_missing_final_dot(self):
        scheme = detect_scheme(DECIMAL_TEXTS)
        self.assertTrue(scheme.decimal)
        self.assertEqual(scheme.paragraph_count, 7)
        for text, canonical in [('1. 배경', '□'), ('1.1. 상황', 'ㅇ'), ('1.1.1. 내용', '-'),
                                ('1.2.1 내용', '-'), ('12.23.34.45. 상세', '-')]:
            with self.subTest(text=text):
                self.assertEqual(scheme.canonical(text), (canonical, text.index(' ')))
        self.assertIsNone(scheme.canonical('* 설명'))
        self.assertIsNone(scheme.canonical('** 설명'))

    def test_canonical_end_includes_leading_whitespace_excludes_following_whitespace(self):
        scheme = detect_scheme(DECIMAL_TEXTS)
        text = '\t 1.2.1.\u3000본문'
        self.assertEqual(scheme.canonical(text), ('-', 8))
        self.assertEqual(scheme.style_text(text), '\t -\u3000본문')
        self.assertEqual(detect_scheme(['◆ 제목']).canonical('  ◆ 본문'), ('□', 3))

    def test_attachments_are_excluded_from_detection_and_lookup(self):
        scheme = detect_scheme(DECIMAL_TEXTS)
        for text in DECIMAL_TEXTS[-2:]:
            self.assertIsNone(scheme.canonical(text))
            self.assertTrue(scheme.is_excluded('  ' + text))
        only_attachment = detect_scheme(['붙임 : 1. 계획 1부.', '1.1. 세부 계획 1부.', '◆ 별첨 1부. 끝.'])
        self.assertFalse(only_attachment)
        self.assertFalse(only_attachment.decimal)
        self.assertEqual(only_attachment.symbols, {})

    def test_simple_numbered_list_needs_serial_evidence(self):
        scheme = detect_scheme(['1. 목록', '2. 목록', '본문'])
        self.assertTrue(scheme)
        self.assertEqual(scheme.canonical('1. 목록'), ('□', 2))
        self.assertFalse(detect_scheme(['1. 단발 목록', '본문']))
        self.assertIsNone(MarkerScheme().canonical('◆ 제목'))
        self.assertFalse(detect_scheme(['1..100. 잘못된 번호', '2026.10.21. 날짜']))

    def test_nonstandard_symbols_are_assigned_in_first_seen_order_clamped_after_three(self):
        scheme = detect_scheme(['◆ 제목', '◆ 다음 제목', '◇ 본문', '▶ 내용', '▷ 추가'])
        self.assertEqual(scheme.symbols, {'◆': '□', '◇': 'ㅇ', '▶': '-', '▷': '-'})
        self.assertEqual(scheme.canonical('▷ 추가'), ('-', 1))
        for symbol in '▪▫●◎★☆➢✓':
            self.assertEqual(detect_scheme([symbol + ' 문단']).canonical(symbol + ' 문단'), ('□', 1))

    def test_mixed_official_symbols_reserve_their_levels_even_when_seen_later(self):
        scheme = detect_scheme(['◆ 본문', '◇ 내용', 'ㅁ 공식 제목', '* 부연'])
        self.assertEqual(scheme.symbols, {'◆': 'ㅇ', '◇': '-'})
        self.assertIsNone(scheme.canonical('ㅁ 공식 제목'))
        self.assertEqual(detect_scheme(['□ 제목', 'ㅇ 본문', '- 내용', '◆ 나머지']).canonical('◆ 나머지'), ('-', 1))
        for official in '□ㅁㅇ○-*※':
            self.assertIsNone(detect_scheme([official + ' 문장']).canonical(official + ' 문장'))

    def test_log_message(self):
        self.assertEqual(detect_scheme(DECIMAL_TEXTS).log_message(),
                         '[항목기호 체계] 계열→단계: 1.=□, 1.1.=ㅇ, 1.1.1.=- (문단 7개)')


class MarkerSchemeConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = formatter_namespace()

    def setUp(self):
        self.ns['활성_항목기호_체계'] = None
        self.ns['표준서식_설정'] = {'기호_규칙': DEFAULT_SYMBOL_RULES}

    def test_rule_lookup_with_and_without_scheme(self):
        find = self.ns['표준서식_기호규칙_찾기']
        self.assertIsNone(find('1.1. 상황'))
        self.assertIsNone(find('◆ 제목'))
        self.assertEqual(find('ㅇ 본문'), DEFAULT_SYMBOL_RULES[1])
        self.ns['활성_항목기호_체계'] = detect_scheme(DECIMAL_TEXTS)
        for text, rule in zip(DECIMAL_TEXTS[:3], DEFAULT_SYMBOL_RULES[:3]):
            self.assertEqual(find(text), rule)
        for text in DECIMAL_TEXTS[-2:]:
            self.assertIsNone(find(text))
        self.ns['활성_항목기호_체계'] = detect_scheme(['● 제목', '◆ 본문'])
        self.assertEqual(find('● 제목'), DEFAULT_SYMBOL_RULES[0])

    def test_parent_types_with_and_without_scheme(self):
        parent = self.ns['_부모문단_유형']
        self.assertIsNone(parent('1.1. 상황'))
        self.assertIsNone(parent('◆ 제목'))
        self.assertEqual(parent('ㅇ 본문'), '본문')
        self.ns['활성_항목기호_체계'] = detect_scheme(DECIMAL_TEXTS)
        self.assertEqual([parent(t) for t in DECIMAL_TEXTS[:3]], ['제목', '본문', '내용'])
        self.assertIsNone(parent(DECIMAL_TEXTS[-1]))

    def test_full_decimal_token_offsets_in_xml_and_com(self):
        for scheme in (None, detect_scheme(DECIMAL_TEXTS)):
            self.ns['활성_항목기호_체계'] = scheme
            for text in ['1.1. 상황', '   1.1.1. 내용', '\t1.2.1 항성계']:
                with self.subTest(scheme=bool(scheme), text=text):
                    end = text.index(' ', len(text) - len(text.lstrip()))
                    self.assertEqual(marker_end_offset(text), end)
                    self.assertEqual(hanging_indent_offset(text), end + 1)
                    self.assertEqual(self.ns['_문단_기호뒤_오프셋'](text), end + 1)
                    self.assertEqual(self.ns['문단_내어쓰기_기준_오프셋'](text), end + 1)
        self.ns['활성_항목기호_체계'] = detect_scheme(['✓ 제목'])
        self.assertEqual(self.ns['_문단_기호뒤_오프셋']('✓ 본문'), 2)
        self.assertEqual(self.ns['문단_내어쓰기_기준_오프셋']('✓ 본문'), 2)
        self.ns['활성_항목기호_체계'] = None
        self.assertIsNone(self.ns['_문단_기호뒤_오프셋']('✓ 본문'))

    def test_prefix_audit_and_repair_use_canonical_and_keep_original_token(self):
        scheme = detect_scheme(DECIMAL_TEXTS)
        text = '1.1. 상황'
        self.assertIsNone(expected_prefix(text, DEFAULT_SYMBOL_RULES))
        self.assertEqual(expected_prefix(text, DEFAULT_SYMBOL_RULES, scheme), ('ㅇ', 0, 1))
        self.assertEqual(normalize_prefix(text, DEFAULT_SYMBOL_RULES, scheme), ' ' + text)
        self.assertIsNone(expected_prefix(DECIMAL_TEXTS[-1], DEFAULT_SYMBOL_RULES, scheme))

    def test_later_punctuation_spacing_does_not_split_decimal_token(self):
        ns = app_functions('문장부호_마커_끝위치', '문장부호뒤공백_글변환')
        ns['marker_space_fix'] = marker_space_fix
        for scheme in (None, detect_scheme(DECIMAL_TEXTS)):
            ns['활성_항목기호_체계'] = scheme
            for text in ['1.1. (상황) 설명', '   1.1.1. 항세기', '   1.2.1 항성계']:
                self.assertEqual(ns['문장부호뒤공백_글변환'](text), text)

    def test_reference_keys_are_canonical_but_width_uses_original_decimal_token(self):
        scheme = detect_scheme(DECIMAL_TEXTS)
        text = '   1.1.1. 내용'
        width = prefix_width_hwpunit(text, text.index('내용'), size_pt=14)
        pair = (0, -width)
        self.assertEqual(reference_hanging_indent_pair(text, {'-': pair}, scheme=scheme), pair)
        self.assertEqual(consistent_reference_pair(text, {'-': pair}, size_pt=14, scheme=scheme), pair)
        self.assertIsNone(consistent_reference_pair(text, {'-': (0, -2800)}, size_pt=14, scheme=scheme))
        self.assertIsNone(consistent_reference_pair(text, {'-': pair}, size_pt=14))
        self.assertEqual(reference_hanging_indent_pair('1.1.1. 일시: 본문', {'-:label:일시': pair}, scheme=scheme), pair)

    def test_copy_indent_rule_uses_canonical(self):
        self.ns['활성_항목기호_체계'] = detect_scheme(DECIMAL_TEXTS)
        self.ns['표준서식_설정']['내어쓰기_규칙'] = {'ㅇ': 'fixed'}
        self.assertEqual(self.ns['복사_내어쓰기_규칙']('1.1. 상황'), 'fixed')
        self.assertIsNone(self.ns['문단_내어쓰기_기준_오프셋']('1.1. 상황'))

    def test_com_spacing_tracker_sees_canonical_hierarchy(self):
        tracker = Mock()
        self.ns.update(활성_항목기호_체계=detect_scheme(DECIMAL_TEXTS),
                       _표준서식_문단위간격_상태=tracker, _표준서식_문단위간격_표=lambda: {},
                       표준서식_문단위간격_복귀배율=150)
        self.ns['표준서식_문단위간격_찾기']('1.1. 상황')
        tracker.spacing_for.assert_called_with('ㅇ 상황', {}, 150)


class MarkerSchemeHwpxTests(unittest.TestCase):
    def _format(self, source, target, indent=False):
        from docfit_core.batch_format import apply_batch, ParagraphStyle, BatchUnsupported
        from docfit_core.fidelity.package import UnsupportedPackage
        from docfit_core.document_rules import ParagraphSpacingTracker
        from docfit_core.style_hierarchy import normalize_leading_dot
        from tests.test_supplement_lead import _app_defaults

        ns = app_functions('표준서식_hwpx_처리', '표준서식_기호규칙_찾기',
                           '_부모문단_유형', '_부연설명_문단인가', '부연설명_앞빈칸_수',
                           '_문단_본문글', '_알파_글꼴형식')
        ns['DOT_MARKERS'] = DOT_MARKERS
        _app_defaults(ns, {'표준서식_설정', '표준서식_기호_별칭', '표준서식_기호_굵게',
                           '_제목_기호', '_본문_기호', '_내용_기호', '부연설명_앞빈칸'})
        ns.update(apply_batch=apply_batch, ParagraphStyle=ParagraphStyle, BatchUnsupported=BatchUnsupported,
                  UnsupportedPackage=UnsupportedPackage, ParagraphSpacingTracker=ParagraphSpacingTracker,
                  normalize_leading_dot=normalize_leading_dot, leading_marker=leading_marker,
                  DOT_MARKERS=DOT_MARKERS, 알파_일괄서식_가능=lambda: True,
                  _알파_라벨_굵게범위=lambda t: (), _GDI_글꼴인가=lambda name: True, _글꼴형식={},
                  부연설명_들여쓰기_사용=True, 표준서식_기호_사용=True,
                  표준서식_문단위간격_사용=True, 표준서식_내어쓰기_사용=indent,
                  표준서식_문단위간격_복귀배율=150, 표준서식_장평_사용=True,
                  표준서식_줄간격_사용=True, 제목_xml이름=tag,
                  _표준서식_문단위간격_표=lambda: {'box': 15, 'circle': 8, 'dash': 4, 'note': 0},
                  로그=Mock(), shutil=__import__('shutil'))
        self.assertGreater(ns['표준서식_hwpx_처리'](source, target), 0,
                           str(ns['로그'].call_args_list))
        self.assertFalse(any('기존 COM 경로' in str(call) for call in ns['로그'].call_args_list))
        return ns

    def test_saved_character_and_paragraph_styles_match_standard_symbols(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            outputs = []
            variants = ['1. 배경', '1.1. 상황', '1.1.1. 내용', '* 항세기: 설명', '** 난세기: 설명']
            standards = ['□ 배경', 'ㅇ 상황', '- 내용', '* 항세기: 설명', '** 난세기: 설명']
            for index, texts in enumerate((variants, standards)):
                source, target = folder / f'in{index}.hwpx', folder / f'out{index}.hwpx'
                fixture(source, ''.join(paragraph(t) for t in texts))
                before = source.read_bytes()
                self._format(source, target)
                self.assertEqual(source.read_bytes(), before)
                outputs.append(roots(target))
            for index in range(len(variants)):
                char_styles, para_styles = [], []
                for header, section in outputs:
                    p = section[index]
                    char_map, para_map = shapes(header, 'charPr'), shapes(header, 'paraPr')
                    char_styles.append([(r[0].text, char_map[r.get('charPrIDRef')])
                                        for r in p if tag(r) == 'run'])
                    para_styles.append(para_map[p.get('paraPrIDRef')])
                # 원문 기호 길이가 달라도 글꼴·크기·굵게와 문단 위/줄 간격은 같은 규칙이다.
                for runs in char_styles:
                    self.assertTrue(all(s.get('height') == char_styles[0][0][1].get('height') for _, s in runs))
                self.assertTrue(plain_text(outputs[0][1][index]).lstrip().startswith(variants[index]))
                self.assertEqual([[x.attrib for _, s in runs for x in s if tag(x) == 'fontRef']
                                  for runs in char_styles][0],
                                 [[x.attrib for _, s in runs for x in s if tag(x) == 'fontRef']
                                  for runs in char_styles][1])
                self.assertEqual([tag(x) for _, s in char_styles[0] for x in s if tag(x) == 'bold'],
                                 [tag(x) for _, s in char_styles[1] for x in s if tag(x) == 'bold'])
                paragraph_values = [[(tag(x), x.attrib) for x in s.iter() if tag(x) in {'prev', 'lineSpacing'}]
                                    for s in para_styles]
                self.assertEqual(*paragraph_values)

    def test_xml_indent_uses_full_original_token_width(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = (Path(folder) / name for name in ('input.hwpx', 'output.hwpx'))
            fixture(source, paragraph('1. 제목') + paragraph('1.1. 상황') + paragraph('1.1.1. 내용'))
            self._format(source, target, indent=True)
            header, section = roots(target)
            para_map = shapes(header, 'paraPr')
            for p, size in zip(list(section)[1:], (15, 14)):
                text = plain_text(p)
                expected = prefix_width_hwpunit(text, hanging_indent_offset(text), size_pt=size)
                intents = [int(x.get('value')) for x in para_map[p.get('paraPrIDRef')].iter() if tag(x) == 'intent']
                self.assertEqual(intents, [-expected, -expected * 2])

    def test_xml_processing_resets_scheme_between_documents(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = (Path(folder) / name for name in ('input.hwpx', 'output.hwpx'))
            fixture(source, paragraph('1.1. 상황'))
            ns = self._format(source, target)
            self.assertTrue(ns['활성_항목기호_체계'])
            fixture(source, paragraph('1. 단순 목록'))
            ns['표준서식_hwpx_처리'](source, target)
            self.assertFalse(ns['활성_항목기호_체계'])
            self.assertIsNone(ns['표준서식_기호규칙_찾기']('1.1. 이전 문서 번호'))

    def test_hwpx_detection_and_prefix_audit_exclude_table_numbering_and_attachments(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'input.hwpx'
            table = '<hp:tbl>' + paragraph('1.1. 표 안 목록') + '</hp:tbl>'
            fixture(source, paragraph('1. 목록') + paragraph('표', extra=table))
            self.assertFalse(detect_hwpx_scheme(source))
            fixture(source, ''.join(paragraph(t) for t in DECIMAL_TEXTS))
            before = source.read_bytes()
            self.assertEqual(detect_hwpx_scheme(source).paragraph_count, 7)
            audit = audit_hwpx_prefixes(source, DEFAULT_SYMBOL_RULES)
            self.assertEqual(audit['measured']['ㅇ'], 3)
            self.assertEqual(audit['measured']['-'], 3)
            self.assertFalse(any(t['text'] == DECIMAL_TEXTS[-1] for t in audit['mismatches']))
            self.assertEqual(source.read_bytes(), before)

    def test_formatter_xml_matches_standard_hierarchy_and_preserves_symbols(self):
        from tests.test_supplement_lead import XmlPlanSupplementLeadTests
        run = XmlPlanSupplementLeadTests()._run
        texts = run('\n'.join(DECIMAL_TEXTS))
        joined = ''.join(texts)
        for token in ['1.', ' 1.1.', '   1.1.1.', '   1.2.1 ',
                      '      * 항세기:', '     ** 난세기:', '2. 스케줄표 1부.  끝.']:
            self.assertIn(token, joined)
        self.assertNotIn('□', joined)
        self.assertNotIn('ㅇ', joined)
        symbols = run('● 제목\n◆ 본문\n✓ 내용\n* 부연: 설명')
        self.assertIn('● 제목', ''.join(symbols))
        self.assertIn(' ◆ 본문', ''.join(symbols))
        self.assertIn('   ✓ 내용', ''.join(symbols))
        self.assertNotIn('•', ''.join(symbols))


if __name__ == '__main__':
    unittest.main()
