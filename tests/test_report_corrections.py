import hashlib
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from docfit_core.batch_format import plain_text, tag
from docfit_core.marker_scheme import classify_marker
from docfit_core.style_hierarchy import leading_marker
from docfit_core.report_corrections import join_title_overview
from defusedxml import ElementTree as ET
from tests.test_batch_format import roots, shapes


class ReportCorrectionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_black_numbers_use_dash_rules_without_changing_glyph(self):
        fn = self.ns['표준서식_기호규칙_찾기']
        for marker in '❶❷❸❹❺❻❼❽❾❿':
            text = '   ' + marker + ' (라벨) 본문'
            self.assertEqual(classify_marker(text), ('-', 4))
            self.assertEqual(leading_marker(text)[1], '내용')
            with patch.dict(fn.__globals__, {'활성_항목기호_체계': None}):
                self.assertEqual(fn(text), fn('   - (라벨) 본문'))

    def test_title_variants_and_overview_boundaries(self):
        for title in ('title1', 'title2'):
            root = ET.fromstring('<sec><p id="title"><run><tbl id="1"/><t/></run></p>'
                                 '<p><run><tbl id="2"/><t/></run></p></sec>')
            converted = [(root[0], title), (root[1], 'overview')]
            self.assertEqual(join_title_overview(root, converted), 1)
            self.assertEqual(len(root), 1)
            self.assertEqual([x.get('id') for x in root[0].iter() if tag(x) == 'tbl'], ['1', '2'])
            self.assertEqual(join_title_overview(root, converted), 0)
        for kind in ('reference', 'overview'):
            root = ET.fromstring('<sec><p><run><tbl/></run></p><p><run><tbl/></run></p></sec>')
            self.assertEqual(join_title_overview(root, [(root[0], kind), (root[1], 'overview')]), 0)
        root = ET.fromstring('<sec><p><run><tbl/></run></p><p pageBreak="1"><run><tbl/></run></p></sec>')
        self.assertEqual(join_title_overview(root, [(root[0], 'title1'), (root[1], 'overview')]), 0)

    def test_six_case_fixture_uses_actual_abbreviation_and_formatter_paths(self):
        source = Path(__file__).parent / 'fixtures/c23_report_rules.hwpx'
        before = hashlib.sha256(source.read_bytes()).digest()
        ns = self.ns
        convert, standard = ns['준말_hwpx_처리'], ns['표준서식_hwpx_처리']
        from docfit_core.abbreviations import merge_with_defaults
        registry = merge_with_defaults({})
        with tempfile.TemporaryDirectory() as folder, patch.dict(standard.__globals__, {
                '준말_등록표': registry, '로그': lambda message: None,
                '알파_일괄서식_가능': lambda: True, '표준서식_내어쓰기_사용': True,
                '_알파_글꼴형식': lambda font: 'TTF', '활성_서식예시_파일': None}):
            expanded, result = Path(folder) / 'expanded.hwpx', Path(folder) / 'result.hwpx'
            selection = convert(source)
            self.assertEqual(convert(source, expanded, selection), 2)
            header, section = roots(expanded)
            self.assertEqual(sum(tag(x) == 'tbl' for x in section[0].iter()), 2)
            self.assertEqual(len(section), len(roots(source)[1]) - 1)
            self.assertGreater(standard(expanded, result), 0)
            header, section = roots(result)
            chars, paras = shapes(header, 'charPr'), shapes(header, 'paraPr')
            def char_at(p, offset):
                for run in p:
                    if tag(run) != 'run':
                        continue
                    text = run[0].text or ''
                    if offset < len(text):
                        return chars[run.get('charPrIDRef')]
                    offset -= len(text)
                self.fail('missing character')
            texts = {plain_text(p): p for p in section if plain_text(p)}
            for text, p in texts.items():
                if text.lstrip().startswith('ㅇ ('):
                    shape = paras[p.get('paraPrIDRef')]
                    intent = int(next(x for x in shape.iter() if tag(x) == 'intent').get('value'))
                    self.assertLessEqual(abs(intent + 3000), 200)
                if text.lstrip()[:1] in '❶❷❸❹❺❻❼❽❾❿':
                    offset = text.index(')') + 2 if ')' in text else text.index(':') + 2
                    shape = char_at(p, offset)
                    self.assertEqual(shape.get('height'), '1400')
                    self.assertFalse(any(tag(x) == 'bold' for x in shape))
                    para_shape = paras[p.get('paraPrIDRef')]
                    self.assertEqual(next(x for x in para_shape.iter() if tag(x) == 'prev').get('value'), '0')
                if '운행형태:' in text:
                    label = char_at(p, text.index('운'))
                    body = char_at(p, text.index('비'))
                    self.assertEqual(label.get('height'), body.get('height'))
                    self.assertEqual(label.get('height'), '1400')
                    self.assertTrue(any(tag(x) == 'bold' for x in label))
            for prefix in ('(나머지 3대)', '(이동건강버스)'):
                p = next(p for text, p in texts.items() if text.startswith(prefix))
                idx = list(section).index(p)
                parent = section[idx - 1]
                parent_text = plain_text(parent)
                self.assertEqual(char_at(p, 0).get('height'), char_at(parent, parent_text.index('(')).get('height'))
                shape = paras[p.get('paraPrIDRef')]
                self.assertGreater(int(next(x for x in shape.iter() if tag(x) == 'left').get('value')), 0)
        self.assertEqual(before, hashlib.sha256(source.read_bytes()).digest())
