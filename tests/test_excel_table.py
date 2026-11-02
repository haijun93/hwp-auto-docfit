import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from docfit_core.excel_table import parse_clipboard

SAMPLE='''Version:1.0\r\nStartHTML:0000000105\r\nEndHTML:0000000600\r\nStartFragment:0000000137\r\nEndFragment:0000000570\r\n<html><body><!--StartFragment--><table><tr><th style="background-color:#eeeeee;font-weight:bold">제목</th><th>값</th></tr><tr><td rowspan="2" style="width:40pt"><span style="mso-highlight:yellow;background-color:yellow"> A&nbsp; B </span></td><td style="text-align:right">1,234</td></tr><tr><td>'12%_x000D_</td></tr></table><!--EndFragment--></body></html>'''

class ExcelTableTests(unittest.TestCase):
    def test_cf_html_parse_cleanup_and_tsv(self):
        result=parse_clipboard(SAMPLE)
        self.assertEqual((result['row_count'],result['col_count']),(3,2))
        self.assertEqual(result['rows'][1][0]['text'],'A B')
        self.assertEqual(result['rows'][1][0]['rowspan'],2)
        self.assertEqual(result['rows'][1][1]['text'],'1,234')
        self.assertEqual(result['rows'][1][1]['align'],'right')
        self.assertEqual(parse_clipboard(None,'a\tb\n1\t2')['col_count'],2)

    def test_hwpx_structure(self):
        from docfit_core.excel_table_hwpx import to_hwpx
        from defusedxml import ElementTree as ET
        import zipfile
        model=parse_clipboard('<table><tr><td>A</td><td>B</td></tr></table>')
        with TemporaryDirectory() as d:
            path=to_hwpx(model,Path(d)/'table.hwpx')
            with zipfile.ZipFile(path) as z:
                doc=ET.fromstring(z.read('Contents/section0.xml'))
            self.assertTrue(any(e.tag.endswith('}tbl') for e in doc.iter()))

if __name__=='__main__': unittest.main()
