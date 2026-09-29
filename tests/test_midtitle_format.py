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
        self.assertIsNone(judge(self._plain_table(3, numeral='1')))
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
