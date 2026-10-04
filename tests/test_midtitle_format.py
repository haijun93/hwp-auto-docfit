"""중제목 표(로마자 번호 + 글) 판별과 HY견고딕 20pt 서식 적용을 확인한다."""
import base64
import copy
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest
import zipfile
import zlib
from unittest.mock import patch


class MidTitleFormatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.parse = staticmethod(cls.ns['safe_xml_fromstring'])
        cls.name = staticmethod(cls.ns['제목_xml이름'])

    def _sample(self):
        header, section = self.ns['중제목_원본자료']()
        table = next(x for x in section.iter() if self.name(x) == 'tbl')
        return header, table

    def _plain_table(self, cols, numeral='Ⅰ', text='추진배경', middle=''):
        """서식이 없는(10pt 바탕체) 중제목 표를 기준 표에서 만들어 낸다."""
        _, sample = self._sample()
        table = copy.deepcopy(sample)
        cells = self.ns['제목_셀들'](table)
        if cols == 2:
            row = next(x for x in table if self.name(x) == 'tr')
            row.remove(cells[1])
            cells = [cells[0], cells[2]]
        table.set('colCnt', str(cols))
        values = [numeral, text] if cols == 2 else [numeral, middle, text]
        for cell, value in zip(cells, values):
            cell.set('borderFillIDRef', '1')
            for p in self.ns['제목_문단들'](cell):
                p.set('paraPrIDRef', '0')
                for run in p:
                    if self.name(run) == 'run':
                        run.set('charPrIDRef', '0')
                        for t in list(run):
                            run.remove(t)
                        if value:
                            t = copy.deepcopy(next(x for x in sample.iter() if self.name(x) == 't'))
                            t.text = value
                            run.append(t)
        return table

    def _hwpx(self, tables):
        header, _ = self._sample()
        ns = self.ns
        chars = next(x for x in header.iter() if self.name(x) == 'charProperties')
        base = copy.deepcopy(next(iter(chars)))
        base.set('id', '0'); base.set('height', '1000')
        chars.insert(0, base)
        paras = next(x for x in header.iter() if self.name(x) == 'paraProperties')
        para = copy.deepcopy(next(iter(paras))); para.set('id', '0')
        paras.insert(0, para)
        section = self.parse(
            b'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
            b'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"/>')
        for table in tables:
            p = ns['XML_자식_추가'](section, section, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}p',
                                attrib={'id': '0', 'paraPrIDRef': '0', 'styleIDRef': '0'})
            run = ns['XML_자식_추가'](p, section, tag='{http://www.hancom.co.kr/hwpml/2011/paragraph}run',
                                  attrib={'charPrIDRef': '0'})
            run.append(table)
        out = Path(tempfile.mkdtemp(prefix='docfit-mid-')) / 'in.hwpx'
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', ns['ET'].tostring(header, encoding='utf-8', xml_declaration=True))
            z.writestr('Contents/section0.xml', ns['ET'].tostring(section, encoding='utf-8', xml_declaration=True))
        return out

    def test_kind_detection(self):
        judge = self.ns['중제목_유형판별']
        self.assertEqual(judge(self._plain_table(3)), 1)
        self.assertEqual(judge(self._plain_table(2)), 2)
        self.assertEqual(judge(self._plain_table(3, numeral='Ⅳ', text='행 정 사 항')), 1)
        self.assertEqual(judge(self._plain_table(3, numeral='II')), 1)
        # 서식(HY견고딕 20pt)은 로마자 번호 표에만 입히고, 아라비아 숫자 번호(1·01·2.) 표는 글 칸 폭만 맞춘다(2026-10-04).
        self.assertIsNone(judge(self._plain_table(3, numeral='1')))
        cells = self.ns['중제목_글칸들']
        self.assertEqual(cells(self._plain_table(3, numeral='1')), [2])
        self.assertEqual(cells(self._plain_table(2, numeral='01')), [1])
        self.assertEqual(cells(self._plain_table(2, numeral='2.')), [1])
        self.assertEqual(cells(self._plain_table(3, numeral='Ⅱ', text='', middle='글')), [1])   # 2열에 글
        self.assertEqual(cells(self._plain_table(2, numeral='123')), [])
        self.assertEqual(cells(self._plain_table(3, numeral='가')), [])
        self.assertIsNone(judge(self._plain_table(3, numeral='가')))
        self.assertIsNone(judge(self._plain_table(3, text='')))
        self.assertIsNone(judge(self._plain_table(3, middle='끼임')))
        self.assertIsNone(judge(self._plain_table(3, text='붙임 자료')))
        self.assertIsNone(judge(self._plain_table(2, text='□ 추진')))

    def test_apply_sets_hy_gyeongothic_20pt_everywhere(self):
        ns = self.ns
        tables = [self._plain_table(3), self._plain_table(2, numeral='Ⅱ', text='추진방향 및 추진계획'),
                  self._plain_table(3, numeral='Ⅲ', text='아주 아주 긴 중제목 문구를 넣어서 칸 폭을 넘겨 봅니다')]
        source = self._hwpx(tables)
        found = ns['중제목_hwpx_처리'](source)
        self.assertEqual(found, {'Contents/section0.xml': [(0, 1), (1, 2), (2, 1)]})
        target = source.with_name('out.hwpx')
        self.assertEqual(ns['중제목_hwpx_처리'](source, target, found), 3)
        with zipfile.ZipFile(target) as z:
            header = self.parse(z.read('Contents/header.xml'))
            section = self.parse(z.read('Contents/section0.xml'))
        faces = {}
        for ff in next(x for x in header.iter() if self.name(x) == 'fontfaces'):
            faces[ff.get('lang').lower()] = {f.get('id'): f.get('face') for f in ff}
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        out_tables = [t for t in section.iter() if self.name(t) == 'tbl']
        self.assertEqual(len(out_tables), 3)
        for table, original in zip(out_tables, tables):
            self.assertEqual(ns['제목_문자열'](table), ns['제목_문자열'](original))
            for run in (r for r in table.iter() if self.name(r) == 'run'):
                cp = chars[run.get('charPrIDRef')]
                self.assertEqual(cp.get('height'), '2000')
                fonts = next(x for x in cp if self.name(x) == 'fontRef')
                for lang, fid in fonts.attrib.items():
                    self.assertEqual(faces[lang][fid], 'HY견고딕', lang)
        # 긴 글은 글 칸과 표 폭이 늘어난다.
        long_table = out_tables[2]
        text_cell = ns['제목_셀들'](long_table)[-1]
        self.assertGreater(int(ns['제목_자식'](text_cell, 'cellSz').get('width')), 15109)
        self.assertGreater(int(ns['제목_자식'](long_table, 'sz').get('width')), 19746)
        # 결과를 다시 판별해도 같은 유형이다.
        again = ns['중제목_hwpx_처리'](target)
        self.assertEqual(again, found)

    def _numeral_and_text_bold(self, bold_option):
        ns = self.ns
        source = self._hwpx([self._plain_table(3)])
        found = ns['중제목_hwpx_처리'](source)
        target = source.with_name('bold.hwpx')
        with patch.dict(ns['중제목_hwpx_처리'].__globals__, {'중제목_번호굵게': bold_option}):
            ns['중제목_hwpx_처리'](source, target, found)
        with zipfile.ZipFile(target) as z:
            header = self.parse(z.read('Contents/header.xml'))
            section = self.parse(z.read('Contents/section0.xml'))
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        cells = ns['제목_셀들'](next(t for t in section.iter() if self.name(t) == 'tbl'))
        def bold(cell):
            run = next(r for r in cell.iter() if self.name(r) == 'run')
            return any(self.name(x) == 'bold' for x in chars[run.get('charPrIDRef')])
        return bold(cells[0]), bold(cells[2])

    def test_text_cell_width_follows_text_length(self):
        # 중제목 글 칸 폭은 글자 수에 비례해 자동으로 맞춘다: 짧은 글은 줄이고 긴 글은 넓히며, 표 폭은 칸 폭의 합이다.
        ns = self.ns
        texts = ['추진배경', '추진방향 및 세부 추진계획', '추진배경 및 필요성 검토']
        tables = [self._plain_table(3, numeral=n, text=t) for n, t in zip(('Ⅰ', 'Ⅱ', '3'), texts)]
        # 번호·글·빈칸처럼 서식 기준 표가 없는 모양도 글 칸 폭만 맞춘다.
        odd = self._plain_table(3, numeral='4', text='', middle='향후 계획')
        source = self._hwpx(tables + [odd])
        found = ns['중제목_hwpx_처리'](source)
        self.assertEqual(found, {'Contents/section0.xml': [(0, 1), (1, 1), (2, 'fit'), (3, 'fit')]})   # 숫자 번호는 폭만
        target = source.with_name('fit.hwpx')
        ns['중제목_hwpx_처리'](source, target, found)
        with zipfile.ZipFile(target) as z:
            section = self.parse(z.read('Contents/section0.xml'))
        out = [t for t in section.iter() if self.name(t) == 'tbl']
        def widths(table):
            return [int(ns['제목_자식'](c, 'cellSz').get('width')) for c in ns['제목_셀들'](table)]
        글칸 = [widths(t)[2] for t in out[:3]]
        self.assertLess(글칸[0], 15109)                       # 4글자: 기준 표 글 칸보다 좁아짐
        self.assertTrue(글칸[0] < 글칸[2] < 글칸[1], 글칸)          # 글자 수(4·13·14자) 순서대로 넓어짐
        # 20pt 한글 4글자 폭(8000) + 여백·여유가 들어가고 너무 넓지 않다.
        self.assertTrue(8000 < 글칸[0] < 8000 + 3000, 글칸[0])
        for table in out:
            self.assertEqual(int(ns['제목_자식'](table, 'sz').get('width')), sum(widths(table)))
        self.assertEqual(widths(out[3])[0], widths(tables[0])[0])          # 번호 칸은 그대로
        # 'fit' 표: 좁은 2열에 든 10pt 글 '향후 계획'(한글 4자+빈칸) 폭만큼 넓힌다(4500 + 여백·여유).
        self.assertTrue(4500 < widths(out[3])[1] < 4500 + 2500, widths(out[3]))
        # 쪽 본문 폭을 넘으면 글 칸을 줄여 표가 본문 폭 안에 들어가게 한다.
        long_table = self._plain_table(2, numeral='Ⅴ', text='아주 아주 긴 중제목 문구를 넣어서 쪽 본문 폭을 넘겨 봅니다 정말로')
        ns['_중제목_칸폭_맞춤'](long_table, 30000, None)
        self.assertLessEqual(int(ns['제목_자식'](long_table, 'sz').get('width')), 30000)

    def test_numeral_bold_is_default_and_can_be_turned_off(self):
        self.assertTrue(self.ns['중제목_번호굵게'])
        self.assertEqual(self._numeral_and_text_bold(True), (True, False))
        self.assertEqual(self._numeral_and_text_bold(False), (False, False))

    def test_numeral_bold_setting_defaults_on(self):
        self.assertTrue(self.ns['기본_설정']['std_midtitle_bold'])

    def test_reference_borders_are_black_of_first_two_tables(self):
        """기준 모양은 Ⅰ·Ⅱ 표의 검은 0.5mm 테두리이며 Ⅲ 표의 남색 변형이 아니다."""
        ns = self.ns
        source = self._hwpx([self._plain_table(3), self._plain_table(2, numeral='Ⅱ')])
        found = ns['중제목_hwpx_처리'](source)
        target = source.with_name('border.hwpx')
        ns['중제목_hwpx_처리'](source, target, found)
        with zipfile.ZipFile(target) as z:
            header = self.parse(z.read('Contents/header.xml'))
            section = self.parse(z.read('Contents/section0.xml'))
        fills = {b.get('id'): b for b in header.iter() if self.name(b) == 'borderFill'}
        def side(fill, name):
            e = next(x for x in fills[fill] if self.name(x) == name)
            return e.get('type'), e.get('width'), e.get('color')
        solid = ('SOLID', '0.5 mm', '#000000')
        for table in (t for t in section.iter() if self.name(t) == 'tbl'):
            cells = ns['제목_셀들'](table)
            number = cells[0].get('borderFillIDRef')
            for name in ('leftBorder', 'rightBorder', 'topBorder', 'bottomBorder'):
                self.assertEqual(side(number, name), solid, name)
            text = cells[-1].get('borderFillIDRef')
            for name in ('topBorder', 'bottomBorder'):
                self.assertEqual(side(text, name), solid, name)
        for fill in fills.values():
            self.assertNotIn('#1D1E42', [x.get('color') for x in fill.iter() if x.get('color')])

    def test_pre_format_runs_midtitle_processor_when_enabled(self):
        from unittest.mock import Mock, patch
        fn = self.ns['제목붙임_선행적용']
        seen = []

        def processor(source, target=None, selections=None):
            seen.append(Path(source).name)
            return {}

        with patch.dict(fn.__globals__, {
            '제목4종_사용': False, '붙임2종_사용': False, '중제목_사용': True,
            '중제목_hwpx_처리': processor, '로그': Mock(), '중단_요청됨': lambda: False,
        }):
            self.assertTrue(fn('C:/원본/문서.hwpx'))
        self.assertEqual(seen, ['문서.hwpx'])


if __name__ == '__main__':
    unittest.main()
