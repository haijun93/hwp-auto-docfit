"""C25: 사용자 설정·표 변환 경계의 회귀 시험."""
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from defusedxml import ElementTree as ET
from docfit_core import table_sketch, table_import
from docfit_core.app_state import RunOptions
from docfit_core.cell_image_bg import convert_section_cell_images

class C25IntegrationTest(unittest.TestCase):
    def test_cell_background_option_reaches_run_stages(self):
        for mode in ('spacing', 'all', 'format'):
            option = 'spacing_cell_image_to_bg' if mode == 'spacing' else 'all_cell_image_to_bg'
            self.assertTrue(RunOptions(mode=mode, **{option:True}).resolve_stages({})['cell_image_to_bg'])
            self.assertFalse(RunOptions(mode=mode).resolve_stages({})['cell_image_to_bg'])

    def test_real_border_width_color_round_trip(self):
        lines=[dict(x1=0,y1=0,x2=2,y2=0),dict(x1=0,y1=2,x2=2,y2=2),
               dict(x1=0,y1=0,x2=0,y2=2),dict(x1=2,y1=0,x2=2,y2=2)]
        for line in lines: line.update(width='thin',width_mm=1.5,color='#FF0022')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'table.hwpx'
            table_sketch.to_hwpx(dict(grid=dict(cols=2,rows=2),lines=lines),path)
            result=table_import.import_table_from_hwpx(path)
            self.assertTrue(result['lines'])
            self.assertTrue(all(line['width_mm']==1.5 and line['color']=='#FF0022' for line in result['lines']))

    def test_tail_text_prevents_image_removal(self):
        hp='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
        header=ET.fromstring('<head/>')
        section=ET.fromstring('<sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:tbl><hp:tr><hp:tc><hp:subList><hp:p><hp:run><hp:t><hp:fwSpace/>보존할 글</hp:t><hp:pic><img binaryItemIDRef="image1"/></hp:pic></hp:run></hp:p></hp:subList></hp:tc></hp:tr></hp:tbl></sec>')
        self.assertEqual(convert_section_cell_images(section,header),0)
        self.assertEqual(len(list(section.iter(hp+'pic'))),1)

    def test_import_xml_string_and_limits(self):
        result=table_import.import_table_from_xml('<hp:tbl xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" rowCnt="1" colCnt="1"><hp:tr><hp:tc><hp:cellAddr rowAddr="0" colAddr="0"/><hp:cellSpan rowSpan="1" colSpan="1"/></hp:tc></hp:tr></hp:tbl>')
        self.assertEqual(len(result['lines']),4)
        result=table_import.import_table_from_html('<table><tr><td colspan="200">a</td><td>b</td></tr></table>')
        self.assertEqual(result['grid']['cols'],200)
        self.assertEqual(len(result['texts']),1)
