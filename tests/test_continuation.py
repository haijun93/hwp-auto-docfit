import copy
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from defusedxml import ElementTree as ET

from docfit_core.continuation import align_sections, inline_item, geometry
from docfit_core.xml_hanging_indent import hanging_indent_offset
from docfit_core.batch_format import plain_text, tag
from tests.test_batch_format import HEADER, paragraph, section, shapes


class ContinuationTest(unittest.TestCase):
    def test_inline_families_and_multiple_item_exception(self):
        for a, b in [('①', '②'), ('1)', '2)'), ('(1)', '(2)'), ('가.', '나.'), ('가)', '나)'), ('㉮', '㉯'), ('-', '-'), ('•', '•'), ('※', '※')]:
            with self.subTest(a=a):
                text = '   • 위치: ' + a + ' 본문(참고)'
                found = inline_item(text)
                self.assertIsNotNone(found)
                self.assertEqual(hanging_indent_offset(text), text.index('본문'))
        self.assertIsNone(inline_item('   • 위치: ① 첫째 ② 둘째'))
        self.assertIsNone(inline_item('   • 위치 ① 첫째'))

    def test_final_user_geometry_with_spaces_replaced_by_margins(self):
        p, q = geometry(6880, 9044)
        self.assertEqual(p, (9044, -9044))
        self.assertEqual(q[0] + q[1], 6880)
        self.assertEqual(q[0], p[0])
        self.assertLessEqual(abs(q[0] - 8857), 200)

    def make(self, lines):
        return ET.fromstring(HEADER), {'section': ET.fromstring(section(''.join(paragraph(t) for t in lines)))}

    def measure(self, text, shape, fonts):
        return sum(1300 if ch in '①②③' else 650 for ch in text)

    def pair(self, header, p):
        shape = shapes(header, 'paraPr')[p.get('paraPrIDRef')]
        return tuple(int(next(x for x in shape.iter() if tag(x) == k).get('value')) for k in ('left', 'intent'))

    def test_alignment_roles_preservation_and_idempotence(self):
        for spaces in (3, 10, 13):
            header, sections = self.make(['   • 위치: ① 첫째(주석)', ' ' * spaces + '② 둘째(설명)', '③ 셋째'])
            # Parent body 13pt, parentheses 11pt, continuation initially uses another font/shape.
            root = sections['section']
            first = root[0][0]
            first[0].text = '   • 위치: ① 첫째'
            extra = copy.deepcopy(first)
            extra.set('charPrIDRef', '1')
            extra[0].text = '(주석)'
            root[0].insert(1, extra)
            changed = align_sections(header, sections, measure=self.measure)
            self.assertEqual(len(changed), 3)
            p, q, third = root
            self.assertEqual(plain_text(q), '② 둘째(설명)')
            self.assertEqual(self.pair(header, p)[0], self.pair(header, q)[0])
            self.assertEqual(self.pair(header, q), self.pair(header, third))
            self.assertEqual(q[-1].get('charPrIDRef'), '1')
            self.assertEqual(q[0].get('charPrIDRef'), '0')
            before = (ET.tostring(header), ET.tostring(root))
            align_sections(header, sections, measure=self.measure)
            self.assertEqual(before, (ET.tostring(header), ET.tostring(root)))

    def test_boundaries_and_profile_priority(self):
        for following in ('가. 다른 유형', '일반 문장', '□ 새 항목'):
            header, sections = self.make(['• 위치: ① 첫째', following])
            q = sections['section'][1]
            before = ET.tostring(q)
            align_sections(header, sections, measure=self.measure)
            self.assertEqual(before, ET.tostring(q))
        for override in ('none', 'fixed', 'after_marker'):
            header, sections = self.make(['• 위치: ① 첫째', '   ② 둘째'])
            before = ET.tostring(sections['section'])
            align_sections(header, sections, rules={'•': override}, measure=self.measure)
            self.assertEqual(before, ET.tostring(sections['section']))
        header, sections = self.make(['• 위치: ① 첫째', '   ② 둘째'])
        q = sections['section'][1]
        q.set('pageBreak', '1')
        before = ET.tostring(q)
        align_sections(header, sections, measure=self.measure)
        self.assertEqual(before, ET.tostring(q))

    def test_manual_line_break_gets_independent_continuation_geometry(self):
        header = ET.fromstring(HEADER)
        root = ET.fromstring(section(paragraph('• 위치: ① 첫째<hp:lineBreak/>   ② 둘째')))
        align_sections(header, {'section': root}, measure=self.measure)
        self.assertEqual([plain_text(p) for p in root], ['• 위치: ① 첫째', '② 둘째'])
        self.assertEqual(self.pair(header, root[0])[0], self.pair(header, root[1])[0])

    def test_xml_and_com_share_offset(self):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        fn = ns['문단_내어쓰기_기준_오프셋']
        with patch.dict(fn.__globals__, {'복사_내어쓰기_규칙': lambda text: None}):
            for text in ('• 위치: ① 본문', '• 위치: ① 첫째 ② 둘째', 'ㅇ (개요) 본문'):
                self.assertEqual(fn(text), hanging_indent_offset(text))

    def test_synthetic_hwpx_through_real_standard_formatter(self):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        fn = ns['표준서식_hwpx_처리']
        source = Path(__file__).parent / 'fixtures/c23_continuation.hwpx'
        from tests.test_batch_format import roots
        with tempfile.TemporaryDirectory() as folder, patch.dict(fn.__globals__, {
                '알파_일괄서식_가능': lambda: True, '표준서식_내어쓰기_사용': True,
                '_알파_글꼴형식': lambda face: 'TTF', '로그': lambda message: None,
                '활성_서식예시_파일': None}):
            output = Path(folder) / 'out.hwpx'
            self.assertGreater(fn(source, output), 0)
            header, root = roots(output)
            p, q = root[0], root[1]
            self.assertEqual(plain_text(q), '② 가상로 200 인근(가상 복지관 앞)')
            self.assertEqual(self.pair(header, p)[0], self.pair(header, q)[0])
