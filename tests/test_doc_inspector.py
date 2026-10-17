from pathlib import Path
import tempfile
import unittest
import zipfile
import struct
from unittest.mock import patch

from docfit_core.doc_inspector import inspect_documents


def hwpx(path, paragraphs, table=False):
    header = '<hh:head xmlns:hh="urn:hh"><hh:charPr id="0" height="1500"><hh:fontRef hangul="0"/></hh:charPr><hh:charPr id="1" height="1300"><hh:fontRef hangul="1"/></hh:charPr></hh:head>'
    section = '<hp:sec xmlns:hp="urn:hp">' + ''.join(
        f'<hp:p><hp:run charPrIDRef="{style}"><hp:t>{text}</hp:t></hp:run></hp:p>' for text, style in paragraphs)
    section += '<hp:tbl/>' if table else ''
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('Contents/header.xml', header)
        archive.writestr('Contents/section0.xml', section + '</hp:sec>')
    return path


class InspectorTests(unittest.TestCase):
    def test_external_formats_recommend_all_without_claiming_full_scan(self):
        for ext in ('.pdf', '.docx', '.xlsx', '.xls', '.pptx', '.hml', '.png', '.tiff'):
            with self.subTest(ext=ext):
                with tempfile.TemporaryDirectory() as folder:
                    path = Path(folder) / ('외부 문서' + ext)
                    path.write_bytes(b'format routing fixture')
                    hints = inspect_documents([str(path)])
                    self.assertEqual(hints['recommended_mode'], 'all')
                    self.assertIn(ext[1:].upper(), hints['reason'])
                    self.assertTrue(hints['show_table_option'])
                    self.assertFalse(hints['scan_complete'])

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def test_txt_md_are_drafts_and_hide_page_range(self):
        for ext in ('.txt', '.md'):
            path = self.root / ('초안' + ext)
            path.write_text('# 업무 계획\n추진할 사항입니다.', encoding='utf-8')
            hints = inspect_documents([str(path)])
            self.assertEqual(hints['recommended_mode'], 'all')
            self.assertFalse(hints['show_page_range'])
            self.assertFalse(hints['show_table_option'])

    def test_plain_hwpx_draft_but_marked_report_keeps_format(self):
        plain = hwpx(self.root/'plain.hwpx', [('안녕하십니까.', 0)])
        report = hwpx(self.root/'report.hwpx', [('□ 추진 계획', 0), ('ㅇ 내용', 0), ('ㅇ 일정', 0)])
        self.assertEqual(inspect_documents([str(plain)])['recommended_mode'], 'all')
        hints = inspect_documents([str(report)])
        self.assertEqual(hints['recommended_mode'], 'spacing')
        self.assertFalse(hints['has_tables'])
        self.assertFalse(hints['show_table_option'])

    def test_same_role_font_or_size_variants_recommend_unify(self):
        path = hwpx(self.root/'mixed.hwpx', [('□ 계획', 0), ('ㅇ 내용', 0), ('ㅇ 일정', 1)])
        self.assertEqual(inspect_documents([str(path)])['recommended_mode'], 'unify')
        path = hwpx(path, [('□ 계획', 1), ('ㅇ 내용', 0), ('ㅇ 일정', 0)])
        self.assertEqual(inspect_documents([str(path)])['recommended_mode'], 'spacing')

    def test_tables_and_long_single_document_context(self):
        path = hwpx(self.root/'long.hwpx', [('ㅇ 내용', 0)] * 200, table=True)
        hints = inspect_documents([str(path)])
        self.assertTrue(hints['has_tables'])
        self.assertTrue(hints['show_page_range'])
        self.assertFalse(inspect_documents([str(path), str(path)])['show_page_range'])

    def test_table_cell_font_difference_is_not_body_style_mixture(self):
        path = hwpx(self.root/'table.hwpx', [('ㅇ 본문', 0), ('ㅇ 내용', 0)])
        with zipfile.ZipFile(path) as archive:
            header = archive.read('Contents/header.xml')
            section = archive.read('Contents/section0.xml').decode().replace('</hp:sec>',
                '<hp:tbl><hp:p><hp:run charPrIDRef="1"><hp:t>ㅇ 표 셀의 별도 글꼴</hp:t></hp:run></hp:p></hp:tbl></hp:sec>')
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('Contents/header.xml', header)
            archive.writestr('Contents/section0.xml', section)
        self.assertEqual(inspect_documents([str(path)])['recommended_mode'], 'spacing')

    def test_markdown_and_box_tables_detected(self):
        for text in ('| 구분 | 내용 |\n| --- | --- |\n| 가 | 나 |', '┌──┬──┐\n│ 가 │ 나 │\n└──┴──┘'):
            path = self.root/'table.md'
            path.write_text(text, encoding='utf-8')
            self.assertTrue(inspect_documents([str(path)])['has_tables'])

    def test_mixed_files_prioritize_draft_otherwise_majority(self):
        report = hwpx(self.root/'report.hwpx', [('ㅇ 내용', 0)])
        mixed = hwpx(self.root/'mixed.hwpx', [('ㅇ 내용', 0), ('ㅇ 일정', 1)])
        draft = self.root/'draft.txt'
        draft.write_text('초안', encoding='utf-8')
        self.assertEqual(inspect_documents([str(report), str(report), str(mixed)])['recommended_mode'], 'spacing')
        self.assertEqual(inspect_documents([str(report), str(draft)])['recommended_mode'], 'all')

    def test_unknown_missing_unsafe_or_over_budget_does_not_hide_options(self):
        for name in ('binary.hwp', 'broken.hwpx'):
            path = self.root/name
            path.write_bytes(b'unknown')
            hints = inspect_documents([str(path)])
            self.assertTrue(hints['show_table_option'])
            self.assertTrue(hints['show_page_range'])
            self.assertFalse(hints['scan_complete'])
        path = hwpx(self.root/'limited.hwpx', [('ㅇ 내용', 0)])
        with patch('docfit_core.doc_inspector.MAX_XML_BYTES', 16):
            self.assertFalse(inspect_documents([str(path)])['scan_complete'])
        data = bytearray(path.read_bytes())
        end = data.rfind(b'PK\x05\x06')
        struct.pack_into('<H', data, end + 10, 4096)
        path.write_bytes(data)
        with patch('docfit_core.doc_inspector.zipfile.ZipFile', side_effect=AssertionError('사전 검사 전 ZIP 로드')):
            self.assertFalse(inspect_documents([str(path)])['scan_complete'])
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('Contents/section0.xml', '<!DOCTYPE x [<!ENTITY a "bad">]><x>&a;</x>')
        self.assertFalse(inspect_documents([str(path)])['scan_complete'])
