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


    def _kinds(self, path):
        result = []
        for p in (x for x in self._read(path) if self.name(x) == 'p'):
            if any(self.name(x) == 'tbl' for x in p.iter()):
                result.append('tbl')
            else:
                text = ''.join(t.text or '' for t in p.iter() if self.name(t) == 't').strip()
                result.append(text or ('secPr' if any(self.name(x) == 'secPr' for x in p.iter()) else 'blank'))
        return result

    def test_no_blank_line_before_first_marker_sentence(self):
        # 제목·개요 표와 첫 문두기호 문장 사이는 문단 위 여백으로만 띄우고 빈 줄은 지운다.
        title, overview = self._tables()
        line = '<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{}</hp:t></hp:run></hp:p>'
        body = (self._table_p(title) + BLANK + self._table_p(overview) + BLANK + BLANK
                + line.format('□ 활용대상 : 전기버스 4대') + BLANK + line.format(' ㅇ (개요) 본문'))
        source = self._doc(body)
        fn = self.ns['제목_hwpx_처리']
        target = source.with_name('marker.hwpx')
        fn(source, target, fn(source))
        # 문두기호 문장 사이 빈 줄은 이 단계가 아니라 표준서식의 빈 줄 삭제가 맡는다.
        self.assertEqual(self._kinds(target), ['secPr', 'tbl', 'tbl', '□ 활용대상 : 전기버스 4대', 'blank',
                                               'ㅇ (개요) 본문'])

    def test_abbreviation_title_overview_and_marker_have_no_blank_line(self):
        from docfit_core.abbreviations import merge_with_defaults
        line = '<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{}</hp:t></hp:run></hp:p>'
        body = (line.format('제목: 마포순환열차버스 사업종료(2026.9.30.)에 따른, 전기버스 활용방안 검토자료')
                + line.format('개요 :  부구청장 주재 현안토의(2026.9.1.) 결과를 보고드림') + BLANK + BLANK
                + line.format('□ 활용대상 : 전기버스 4대'))
        source = self._doc(body)
        fn = self.ns['준말_hwpx_처리']
        with patch.dict(fn.__globals__, {'준말_등록표': merge_with_defaults({})}):
            target = source.with_name('abbr-marker.hwpx')
            self.assertEqual(fn(source, target, fn(source)), 2)
        self.assertEqual(self._kinds(target), ['secPr', 'tbl', 'tbl', '□ 활용대상 : 전기버스 4대'])

    def test_title_without_overview_and_plain_text_after(self):
        from docfit_core.abbreviations import merge_with_defaults
        line = '<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{}</hp:t></hp:run></hp:p>'
        fn = self.ns['준말_hwpx_처리']
        with patch.dict(fn.__globals__, {'준말_등록표': merge_with_defaults({})}):
            # 개요가 없으면 제목 표 뒤 빈 줄을 첫 문두기호 문장 앞까지 지운다.
            source = self._doc(line.format('제목1: 지구 침공계획(안) 보고') + BLANK + line.format('ㅇ (목적) 보고'))
            target = source.with_name('title-only.hwpx')
            fn(source, target, fn(source))
            self.assertEqual(self._kinds(target), ['secPr', 'tbl', 'ㅇ (목적) 보고'])
            # 빈 줄 다음이 문두기호 문장이 아니면(일반 글) 빈 줄을 그대로 둔다.
            source = self._doc(line.format('제목1: 지구 침공계획(안) 보고') + BLANK + line.format('일반 안내 글'))
            target = source.with_name('title-plain.hwpx')
            fn(source, target, fn(source))
            self.assertEqual(self._kinds(target), ['secPr', 'tbl', 'blank', '일반 안내 글'])

    def test_existing_title_subtitle_is_17pt(self):
        # 문서에 이미 있는 부제 있는 제목 표(2×2)에 제목 서식을 입혀도 부제는 15pt, 제목은 27pt다.
        header, section = self.ns['제목_원본자료']()
        title = copy.deepcopy([x for x in section.iter() if self.name(x) == 'tbl'][1])
        source = self._doc(self._table_p(title))
        fn = self.ns['제목_hwpx_처리']
        found = fn(source)
        self.assertEqual(found, {'Contents/section0.xml': [(0, 2)]})
        target = source.with_name('subtitle.hwpx')
        fn(source, target, found)
        with zipfile.ZipFile(target) as z:
            out_header = self.parse(z.read('Contents/header.xml'))
        chars = {c.get('id'): c for c in out_header.iter() if self.name(c) == 'charPr'}
        table = next(t for t in self._read(target).iter() if self.name(t) == 'tbl')
        paras = [p for p in self.ns['제목_문단들'](self.ns['제목_셀들'](table)[0]) if self.ns['제목_문자열'](p).strip()]
        heights = [{chars[r.get('charPrIDRef')].get('height') for r in p if self.name(r) == 'run'
                    and self.ns['제목_문자열'](r).strip()} for p in paras]
        self.assertEqual(heights, [{'1500'}, {'2700'}])

    def test_early_width_step_fits_existing_title_and_overview(self):
        # 작업 맨 앞 단계: 문서에 이미 있는 제목·개요 표를 쪽 좌우 여백 사이 최대 폭으로 맞춘다(서식은 그대로).
        title, overview = self._tables()
        for table in (title, overview):
            self.ns['_서식표_가로맞춤'](table, 30000)          # 좁은 표로 만든다
        source = self._doc(self._table_p(title) + self._table_p(overview))
        fn = self.ns['제목개요폭_hwpx_처리']
        found = fn(source)
        self.assertEqual(found, {'Contents/section0.xml': [0, 1]})
        target = source.with_name('early.hwpx')
        self.assertEqual(fn(source, target, found), 2)
        for table in (t for t in self._read(target).iter() if self.name(t) == 'tbl'):
            out = self.ns['제목_자식'](table, 'outMargin')
            self.assertEqual(self._widths(table)[0], 48190 - int(out.get('left')) - int(out.get('right')))
        self.assertEqual(fn(target), {'Contents/section0.xml': []})   # 이미 최대 폭이면 대상 없음

    def test_early_width_uses_margins_standard_format_will_apply(self):
        # 표준서식이 편집 여백(좌우 25mm = 7087)을 바꿀 예정이면 바뀐 뒤 여백으로 잰다.
        title, _ = self._tables()
        source = self._doc(self._table_p(title))
        fn = self.ns['제목개요폭_hwpx_처리']
        settings = {'left': 25, 'right': 25, 'top': 15, 'bottom': 15, 'header': 10, 'footer': 10}
        with patch.dict(fn.__globals__, {'작업_모드': 'all', '표준서식_선행_사용': True, '표준서식_여백_사용': True,
                                         '쪽범위_요청': None, '선택_세부작업': {},
                                         '표준서식_설정': {**fn.__globals__['표준서식_설정'], '여백_mm': settings}}):
            self.assertEqual(self.ns['_예정_좌우여백'](), (7087, 7087))
            target = source.with_name('early-margin.hwpx')
            fn(source, target, fn(source))
        table = next(t for t in self._read(target).iter() if self.name(t) == 'tbl')
        self.assertEqual(self._widths(table)[0], 59528 - 2 * 7087 - 566)
        # 여백을 바꿀 예정이 없으면(기본) 문서의 지금 여백으로 잰다.
        self.assertIsNone(self.ns['_예정_좌우여백']())

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
