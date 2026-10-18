from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from docfit_core.release_format_audit import inspect_hanging_indent


HEADER = '''<?xml version="1.0"?><hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"><hh:refList><hh:paraPr id="0"><hp:switch><hp:case><hh:margin><hc:intent value="{indent}"/><hc:left value="{left}"/></hh:margin></hp:case></hp:switch></hh:paraPr></hh:refList></hh:head>'''
SECTION = '''<?xml version="1.0"?><hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p paraPrIDRef="0"><hp:run><hp:t>□ 추진 배경</hp:t></hp:run></hp:p><hp:p paraPrIDRef="0"><hp:run><hp:t>일반 본문</hp:t></hp:run></hp:p></hs:sec>'''


class ReleaseFormatAuditTest(unittest.TestCase):
    def _document(self, left, indent):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / 'sample.hwpx'
        with ZipFile(path, 'w') as archive:
            archive.writestr('Contents/header.xml', HEADER.format(left=left, indent=indent))
            archive.writestr('Contents/section0.xml', SECTION)
        return path

    def test_rejects_negative_indent_without_compensating_margin(self):
        result = inspect_hanging_indent(self._document(0, -2400))
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['failed_count'], 1)
        self.assertIn('compensating left margin', result['findings'][0]['reason'])

    def test_accepts_hanging_indent_pair_with_nonnegative_first_line(self):
        result = inspect_hanging_indent(self._document(2400, -2400))
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['marker_paragraph_count'], 1)

    def test_no_marker_paragraphs_is_not_a_pass(self):
        path = self._document(0, 0)
        with ZipFile(path, 'w') as archive:
            archive.writestr('Contents/header.xml', HEADER.format(left=0, indent=0))
            archive.writestr('Contents/section0.xml', SECTION.replace('□ 추진 배경', '일반 제목'))
        self.assertEqual(inspect_hanging_indent(path)['status'], 'fail')

    def test_hanging_indent_is_applied_after_all_copy_style_operations(self):
        source = (Path(__file__).resolve().parents[1] / 'docfit_engine' / 'formatter.py').read_text(encoding='utf-8')
        start = source.index("if _docfit_symbol == '표준서식_문단_처리':")
        end = source.index('return bind_function(표준서식_문단_처리', start)
        body = source[start:end]
        self.assertLess(body.rfind('복사_문단모양_적용('), body.rfind('문단_내어쓰기_적용('))
        self.assertLess(body.rfind('복사_간격_규칙_적용('), body.rfind('문단_내어쓰기_적용('))


if __name__ == '__main__':
    unittest.main()
