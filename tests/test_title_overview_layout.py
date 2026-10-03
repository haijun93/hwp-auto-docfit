"""제목·개요 서식 표: 가로 크기는 쪽 좌우 여백 사이 최대 폭, 제목 표와 개요 표 사이에는 빈 줄 없음."""
import copy
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
import zipfile

HS = 'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
PT = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
# A4(59528) 좌우 여백 20mm(5669): 본문 폭 48190
SEC = ('<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:secPr id="">'
       '<hp:pagePr landscape="{land}" width="59528" height="84188"><hp:margin header="4252" footer="4252" '
       'gutter="0" left="5669" right="5669" top="5669" bottom="4252"/></hp:pagePr></hp:secPr></hp:run></hp:p>')
BLANK = '<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>'


class TitleOverviewLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.name = staticmethod(cls.ns['제목_xml이름'])
        cls.parse = staticmethod(cls.ns['safe_xml_fromstring'])

    def _tables(self):
        _, section = self.ns['제목_원본자료']()
        title = copy.deepcopy(next(x for x in section.iter() if self.name(x) == 'tbl'))
        _, extra = self.ns['개요붙임_원본자료']()
        overview = copy.deepcopy(next(x for x in extra.iter() if self.name(x) == 'tbl'))
        return title, overview

    def _doc(self, body, land='WIDELY'):
        header, _ = self.ns['제목_원본자료']()
        chars = next(x for x in header.iter() if self.name(x) == 'charProperties')
        base = copy.deepcopy(next(iter(chars))); base.set('id', '0')
        chars.insert(0, base)
        paras = next(x for x in header.iter() if self.name(x) == 'paraProperties')
        para = copy.deepcopy(next(iter(paras))); para.set('id', '0')
        paras.insert(0, para)
        section = f'<hs:sec {HS} {HP}>{SEC.format(land=land)}{body}</hs:sec>'
        path = Path(tempfile.mkdtemp(prefix='docfit-title-layout-')) / 'in.hwpx'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', self.ns['ET'].tostring(header, encoding='utf-8', xml_declaration=True))
            z.writestr('Contents/section0.xml', section)
        return path

    def _table_p(self, table):
        return ('<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">'
                + self.ns['ET'].tostring(table, encoding='unicode') + '<hp:t/></hp:run></hp:p>')

    def _read(self, path):
        with zipfile.ZipFile(path) as z:
            return self.parse(z.read('Contents/section0.xml'))

    def _widths(self, table):
        rows = [[int(self.ns['제목_자식'](c, 'cellSz').get('width')) for c in row if self.name(c) == 'tc']
                for row in table if self.name(row) == 'tr']
        return int(self.ns['제목_자식'](table, 'sz').get('width')), rows

    def test_body_width_follows_page_orientation(self):
        portrait = self.parse(f'<hs:sec {HS} {HP}>{SEC.format(land="WIDELY")}</hs:sec>'.encode())
        landscape = self.parse(f'<hs:sec {HS} {HP}>{SEC.format(land="NARROWLY")}</hs:sec>'.encode())
        self.assertEqual(self.ns['_구역_본문폭'](portrait), 48190)
        self.assertEqual(self.ns['_구역_본문폭'](landscape), 72850)
        empty = self.parse(f'<hs:sec {HS} {HP}/>'.encode())
        self.assertEqual(self.ns['_구역_본문폭'](empty), 42520)
        self.assertIsNone(self.ns['_구역_본문폭'](empty, None))

    def test_width_fit_keeps_narrow_cells(self):
        title, _ = self._tables()
        self.ns['_서식표_가로맞춤'](title, 48190)
        width, rows = self._widths(title)
        # 바깥 여백(283 + 283)을 뺀 최대 폭. 날짜 칸(8531)은 그대로 두고 담당자 칸이 차이를 받는다.
        self.assertEqual(width, 48190 - 566)
        self.assertEqual(rows, [[width], [8531, width - 8531]])

    def test_title_formatting_fits_width_and_removes_blank_lines(self):
        title, overview = self._tables()
        body = self._table_p(title) + BLANK + BLANK + self._table_p(overview) + BLANK
        source = self._doc(body)
        fn = self.ns['제목_hwpx_처리']
        found = fn(source)
        self.assertEqual(found, {'Contents/section0.xml': [(0, 1)]})
        target = source.with_name('out.hwpx')
        self.assertEqual(fn(source, target, found), 1)
        section = self._read(target)
        paragraphs = [p for p in section if self.name(p) == 'p']
        # 구역 설정 문단, 제목 표, 개요 표, (개요 뒤 빈 줄은 그대로)
        kinds = ['tbl' if any(self.name(x) == 'tbl' for x in p.iter()) else 'text' for p in paragraphs]
        self.assertEqual(kinds, ['text', 'tbl', 'tbl', 'text'])
        tables = [t for t in section.iter() if self.name(t) == 'tbl']
        self.assertEqual(self._widths(tables[0])[0], 48190 - 566)
        overview_out = self.ns['제목_자식'](tables[1], 'outMargin')
        margin = int(overview_out.get('left')) + int(overview_out.get('right'))
        self.assertEqual(self._widths(tables[1]), (48190 - margin, [[48190 - margin]]))

    def test_text_between_title_and_overview_is_kept(self):
        title, overview = self._tables()
        body = (self._table_p(title) + BLANK
                + '<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>사이 글</hp:t></hp:run></hp:p>'
                + self._table_p(overview))
        source = self._doc(body)
        fn = self.ns['제목_hwpx_처리']
        target = source.with_name('out2.hwpx')
        fn(source, target, fn(source))
        self.assertEqual(len([p for p in self._read(target) if self.name(p) == 'p']), 5)

    def test_abbreviation_title_and_overview_have_no_blank_line(self):
        from docfit_core.abbreviations import merge_with_defaults
        line = '<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{}</hp:t></hp:run></hp:p>'
        body = (line.format('제목1: 지구 침공계획(안) 보고') + BLANK + BLANK
                + line.format('개요: 삼채인의 명랑 지구침략계획을 수립하고 보고드림') + BLANK)
        source = self._doc(body)
        fn = self.ns['준말_hwpx_처리']
        with patch.dict(fn.__globals__, {'준말_등록표': merge_with_defaults({})}):
            found = fn(source)
            target = source.with_name('abbr.hwpx')
            self.assertEqual(fn(source, target, found), 2)
        section = self._read(target)
        paragraphs = [p for p in section if self.name(p) == 'p']
        self.assertEqual(len(paragraphs), 4)   # 구역 설정, 제목 표, 개요 표, 개요 뒤 빈 줄
        tables = [t for t in section.iter() if self.name(t) == 'tbl']
        for table in tables:
            out = self.ns['제목_자식'](table, 'outMargin')
            self.assertEqual(self._widths(table)[0], 48190 - int(out.get('left')) - int(out.get('right')))


    def test_title_date_cell_uses_short_year(self):
        # 예시 서식 표처럼 날짜가 '2022. 4. 19.(화)'(네 자리 연도)여도 제목 서식 날짜는 ’26 약어로 쓴다.
        cell = self.parse(f'<hp:tc {HP}><hp:subList><hp:p><hp:run charPrIDRef="0"><hp:t>2022. 4. 19.(화)</hp:t>'
                          '</hp:run></hp:p></hp:subList></hp:tc>')
        import datetime
        self.assertEqual(self.ns['_칸_날짜_현행화'](cell, datetime.date(2026, 10, 3)), 1)
        self.assertEqual(self.ns['제목_문자열'](cell), '’26. 10. 3.(토)')
        # 기본 제목 표처럼 따옴표가 앞 글 조각에 있으면 그대로 두고 숫자만 바꾼다.
        cell = self.parse(f'<hp:tc {HP}><hp:subList><hp:p><hp:run charPrIDRef="10"><hp:t>’</hp:t></hp:run>'
                          '<hp:run charPrIDRef="11"><hp:t>22. 4. 19.(화)</hp:t></hp:run></hp:p></hp:subList></hp:tc>')
        self.ns['_칸_날짜_현행화'](cell, datetime.date(2026, 10, 3))
        self.assertEqual([t.text for t in cell.iter() if self.name(t) == 't'], ['’', '26. 10. 3.(토)'])


if __name__ == '__main__':
    unittest.main()
