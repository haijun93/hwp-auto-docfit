"""Plain 로1 / Ⅰ headings become reference-style midtitle tables."""
import hashlib
from pathlib import Path
import runpy
import unittest
import zipfile
from docfit_core.roman_heading import match_heading
from docfit_core.ai_answer import ai_answer_to_labeled_text
import tests.test_midtitle_format as reference


class RomanHeadingTests(unittest.TestCase):
    def test_alias_and_unicode_number_preserve_number_and_normalize_sample_title(self):
        for text in ('로1 추진근거', 'Ⅰ 추진근거', 'Ⅰ. 추진근거', '로1: 추진근거'):
            self.assertEqual(match_heading(text), ('Ⅰ', '추진 근거'))
        self.assertEqual(match_heading('로12 행정사항'), ('Ⅻ', '행정사항'))
        self.assertEqual(match_heading('Ⅰ. 추진개요'), ('Ⅰ', '추진개요'))
        self.assertEqual(match_heading('Ⅱ. 소요'), ('Ⅱ', '소요'))
        for text in ('I am writing', 'Ⅳ형 제품', '로13 잘못된 번호', 'Ⅰ 문장을 설명합니다.', 'Ⅱ', 'Ⅰ 제목\n본문'):
            self.assertIsNone(match_heading(text), text)

    def test_markdown_roman_chapters_keep_numbers_and_child_hierarchy(self):
        out = ai_answer_to_labeled_text('# 계획\n## Ⅰ. 추진근거\n### 1. 내용\n- 세부\n## Ⅱ. 일정\n- 계획', markdown_document=True)
        self.assertIn('기호: Ⅰ. 추진 근거', out)
        self.assertIn('네모: 내용', out)
        self.assertIn('원: 세부', out)
        self.assertIn('기호: Ⅱ. 일정', out)
        partial = ai_answer_to_labeled_text('# 계획\n## Ⅱ. 대상\n## Ⅳ. 일정', markdown_document=True)
        self.assertIn('기호: Ⅱ. 대상', partial)
        self.assertIn('기호: Ⅳ. 일정', partial)


class RomanHeadingEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def source(self, lines):
        helper = reference.MidTitleFormatTest()
        helper.ns = self.ns
        helper.parse, helper.name = self.ns['safe_xml_fromstring'], self.ns['제목_xml이름']
        self.addCleanup(helper.doCleanups)
        source = helper._hwpx([])
        with zipfile.ZipFile(source) as z:
            data = {n: z.read(n) for n in z.namelist()}
        root = self.ns['safe_xml_fromstring'](data['Contents/section0.xml'])
        hp = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
        ET = self.ns['ET']
        for text in lines:
            p = self.ns['XML_자식_추가'](root, root, tag='{%s}p' % hp, attrib={'id': '0', 'paraPrIDRef': '0', 'styleIDRef': '0'})
            run = self.ns['XML_자식_추가'](p, root, tag='{%s}run' % hp, attrib={'charPrIDRef': '0'})
            self.ns['XML_자식_추가'](run, root, tag='{%s}t' % hp).text = text
        data['Contents/section0.xml'] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        with zipfile.ZipFile(source, 'w') as z:
            for name, content in data.items():
                z.writestr(name, content)
        return source

    def test_before_examples_become_three_cells_with_reference_fonts_and_borders(self):
        source = self.source(['[서식적용 전]', '로1 추진근거', 'Ⅰ 추진근거', 'ㅇ 본문 보존'])
        original = hashlib.sha256(source.read_bytes()).hexdigest()
        fn = self.ns['중제목_hwpx_처리']
        selections = fn(source)
        self.assertEqual(sum(map(len, selections.values())), 2)
        target = source.with_name('after.hwpx')
        self.assertEqual(fn(source, target, selections), 2)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original)
        with zipfile.ZipFile(target) as z:
            root = self.ns['safe_xml_fromstring'](z.read('Contents/section0.xml'))
            header = self.ns['safe_xml_fromstring'](z.read('Contents/header.xml'))
        tables = [e for e in root.iter() if self.ns['제목_xml이름'](e) == 'tbl']
        self.assertEqual(len(tables), 2)
        for table in tables:
            cells = self.ns['제목_셀들'](table)
            self.assertEqual([self.ns['제목_문자열'](c) for c in cells], ['Ⅰ', '', '추진 근거'])
            self.assertEqual((table.get('rowCnt'), table.get('colCnt')), ('1', '3'))
            self.assertEqual(self.ns['제목_자식'](table, 'pos').get('treatAsChar'), '1')
            chars = {e.get('id'): e for e in header.iter() if self.ns['제목_xml이름'](e) == 'charPr'}
            for cell in (cells[0], cells[-1]):
                for run in cell.iter():
                    if self.ns['제목_xml이름'](run) == 'run':
                        self.assertEqual(chars[run.get('charPrIDRef')].get('height'), '2000')
            borders = {e.get('id'): e for e in header.iter() if self.ns['제목_xml이름'](e) == 'borderFill'}
            for side in ('leftBorder', 'rightBorder', 'topBorder', 'bottomBorder'):
                border = self.ns['제목_자식'](borders[cells[0].get('borderFillIDRef')], side)
                self.assertEqual(border.get('type'), 'SOLID')
                self.assertEqual(border.get('color'), '#000000')
        self.assertIn('ㅇ 본문 보존', ''.join(root.itertext()))
        again = target.with_name('again.hwpx')
        fn(target, again, fn(target))
        with zipfile.ZipFile(again) as z:
            parsed = self.ns['safe_xml_fromstring'](z.read('Contents/section0.xml'))
        self.assertEqual(len([e for e in parsed.iter() if self.ns['제목_xml이름'](e) == 'tbl']), 2)

    def test_changed_heading_after_analysis_is_rejected(self):
        source = self.source(['Ⅰ 추진근거'])
        fn = self.ns['중제목_hwpx_처리']
        selections = fn(source)
        selections['Contents/section0.xml'][0] = (0, ('text', 'Ⅱ', '다른 제목'))
        with self.assertRaisesRegex(RuntimeError, '중제목이 변경'):
            fn(source, source.with_name('reject.hwpx'), selections)
