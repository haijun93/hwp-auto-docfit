"""1.80.10: 항목기호 뒤 인라인 탭/Run 경계와 본문 보존."""
import copy
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
from defusedxml import ElementTree as ET
from docfit_core.marker_spacing import normalize_paragraph, normalize_hwpx, xml_text
from docfit_core.batch_format import plain_text

NS = "http://www.hancom.co.kr/hwpml/2011/paragraph"

def paragraph(inner):
    return ET.fromstring(f'<p xmlns="{NS}">{inner}</p>')

class MarkerSpacingTests(unittest.TestCase):
    def test_inline_tab_makes_marker_paragraph_plain_and_keeps_runs(self):
        p=paragraph('<run charPrIDRef="10"><t>□<tab width="850"/></t></run><run charPrIDRef="20"><t>(사업내용) 내용</t></run>')
        self.assertIsNone(plain_text(p))
        self.assertTrue(normalize_paragraph(p))
        self.assertEqual(xml_text(p),'□ (사업내용) 내용')
        self.assertEqual(plain_text(p),'□ (사업내용) 내용')
        self.assertEqual([r.get('charPrIDRef') for r in p],['10','20'])
        self.assertFalse(normalize_paragraph(p))

    def test_tail_after_tab_is_not_lost(self):
        p=paragraph('<run><t>ㅇ<tab/>탭 뒤 본문</t></run>')
        self.assertEqual(xml_text(p),'ㅇ\t탭 뒤 본문')
        normalize_paragraph(p)
        self.assertEqual(xml_text(p),'ㅇ 탭 뒤 본문')

    def test_mixed_separators_across_runs(self):
        p=paragraph('<run><t>  - <tab/> </t></run><run><t><tab/>본문</t></run>')
        normalize_paragraph(p)
        self.assertEqual(xml_text(p),'  - 본문')

    def test_body_tab_and_plain_prose_are_preserved(self):
        p=paragraph('<run><t>ㅇ<tab/>본문<tab width="1200"/>수치</t></run>')
        normalize_paragraph(p)
        self.assertEqual(xml_text(p),'ㅇ 본문\t수치')
        self.assertEqual(len(p.findall('.//{*}tab')),1)
        p=paragraph('<run><t>설명<tab/>수치</t></run>')
        before=ET.tostring(p)
        self.assertFalse(normalize_paragraph(p))
        self.assertEqual(ET.tostring(p),before)

    def test_fixed_space_is_also_replaced_and_numbered_markers_supported(self):
        for inner, expected in [('<t>ㅇ<fwSpace/>본문</t>','ㅇ 본문'),
            ('<t>①<tab/>본문</t>','① 본문'),
            ('<t>Ⅰ.<tab/>장 제목</t>','Ⅰ. 장 제목'),
            ('<t>1.<tab/>절 제목</t>','1. 절 제목'),
            ('<t>ㅇ「법령」 적용</t>','ㅇ 「법령」 적용')]:
            p=paragraph('<run>'+inner+'</run>')
            self.assertTrue(normalize_paragraph(p))
            self.assertEqual(xml_text(p),expected)

    def test_table_and_field_objects_are_not_flattened(self):
        for inner in ['<run><t>□<tab/>본문</t><tbl/></run>','<run><fieldBegin/><t>ㅇ<tab/>본문</t></run>']:
            p=paragraph(inner); before=ET.tostring(p)
            self.assertFalse(normalize_paragraph(p))
            self.assertEqual(ET.tostring(p),before)

    def test_archive_preserves_original_header_and_table_cells(self):
        from tests.test_format_elements import HEADER,NS as DECLS,OVERVIEW
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source.hwpx'
            target=Path(directory)/'result.hwpx'
            section=f'<sec {DECLS}><hp:p><hp:run charPrIDRef="0"><hp:t>□<hp:tab/>본문</hp:t></hp:run></hp:p><hp:p><hp:run>{OVERVIEW}</hp:run></hp:p></sec>'
            with ZipFile(source,'w') as z:
                z.writestr('mimetype','application/hwp+zip')
                z.writestr('Contents/header.xml',HEADER)
                z.writestr('Contents/section0.xml',section)
            before=source.read_bytes()
            self.assertEqual(normalize_hwpx(source,target),1)
            self.assertEqual(source.read_bytes(),before)
            with ZipFile(target) as z:
                self.assertEqual(z.read('Contents/header.xml').decode(),HEADER)
                root=ET.fromstring(z.read('Contents/section0.xml'))
                self.assertEqual(xml_text(root[0]),'□ 본문')
                self.assertEqual(xml_text(root[1]),xml_text(ET.fromstring(section)[1]))
            with self.assertRaises(ValueError):normalize_hwpx(source,source)
            with self.assertRaises(ValueError):normalize_hwpx(source,target)

    def test_normative_leading_spaces_are_not_learned_from_bad_kordoc_input(self):
        from docfit_core.marker_spacing import invariant_rule
        for marker,count in [('□',0),('ㅁ',0),('ㅇ',1),('-',3)]:
            original=(marker,9,'글꼴',15,False,False)
            self.assertEqual(invariant_rule(original)[1],count)
            self.assertEqual(original[1],9)
        self.assertEqual(invariant_rule(('*',4,'글꼴',12)),('*',4,'글꼴',12))
