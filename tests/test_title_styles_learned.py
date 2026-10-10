"""첨부 문서로 학습한 제목 서식2(2행1열, 유형3)와 요지 서식 기준값을 확인한다."""
import copy
from pathlib import Path
import runpy
import tempfile
import unittest
import zipfile


class LearnedTitleStyleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.parse = staticmethod(cls.ns['safe_xml_fromstring'])
        cls.name = staticmethod(cls.ns['제목_xml이름'])

    def _title2_sample(self):
        header, section = self.ns['제목2행1열_원본자료']()
        return header, next(x for x in section.iter() if self.name(x) == 'tbl')

    def _plain_title2(self, paragraphs=2, owner='○○과장 : 홍길동 ☎1234'):
        """서식이 없는(10pt) 2행1열 제목 표를 기준 표에서 만들어 낸다."""
        _, sample = self._title2_sample()
        table = copy.deepcopy(sample)
        cells = self.ns['제목_셀들'](table)
        top = self.ns['제목_자식'](cells[0], 'subList')
        plist = [p for p in top if self.name(p) == 'p']
        if paragraphs == 1:
            top.remove(plist[0])
        texts = (['『부제』', '제목 본문'] if paragraphs == 2 else ['제목 본문'])
        for p, text in zip([p for p in top if self.name(p) == 'p'], texts):
            runs = [r for r in p if self.name(r) == 'run']
            for extra in runs[1:]:
                p.remove(extra)
            for t in list(runs[0]):
                runs[0].remove(t)
            t = copy.deepcopy(next(x for x in sample.iter() if self.name(x) == 't'))
            t.text = text
            runs[0].append(t)
        for cell in cells:
            cell.set('borderFillIDRef', '1')
            for p in self.ns['제목_문단들'](cell):
                p.set('paraPrIDRef', '0')
                for r in p:
                    if self.name(r) == 'run':
                        r.set('charPrIDRef', '0')
        owner_p = self.ns['제목_문단들'](cells[1])[0]
        run = next(r for r in owner_p if self.name(r) == 'run')
        for t in list(run):
            run.remove(t)
        t = copy.deepcopy(next(x for x in sample.iter() if self.name(x) == 't'))
        t.text = owner
        run.append(t)
        return table

    def _hwpx(self, table):
        header, _ = self._title2_sample()
        chars = next(x for x in header.iter() if self.name(x) == 'charProperties')
        base = copy.deepcopy(next(iter(chars)))
        base.set('id', '0'); base.set('height', '1000')
        chars.insert(0, base)
        paras = next(x for x in header.iter() if self.name(x) == 'paraProperties')
        para = copy.deepcopy(next(iter(paras))); para.set('id', '0')
        paras.insert(0, para)
        borders = next(x for x in header.iter() if self.name(x) == 'borderFills')
        fill = copy.deepcopy(next(iter(borders))); fill.set('id', '1')
        borders.insert(0, fill)
        ns = self.ns
        section = self.parse(
            b'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
            b'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"/>')
        pt = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
        p = ns['XML_자식_추가'](section, section, tag=pt + 'p', attrib={'id': '0', 'paraPrIDRef': '0', 'styleIDRef': '0'})
        run = ns['XML_자식_추가'](p, section, tag=pt + 'run', attrib={'charPrIDRef': '0'})
        run.append(table)
        out = Path(tempfile.mkdtemp(prefix='docfit-title-')) / 'in.hwpx'
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', ns['ET'].tostring(header, encoding='utf-8', xml_declaration=True))
            z.writestr('Contents/section0.xml', ns['ET'].tostring(section, encoding='utf-8', xml_declaration=True))
        return out

    def test_title2_kind_detection(self):
        judge = self.ns['제목_유형판별']
        self.assertEqual(judge(self._title2_sample()[1]), 3)
        self.assertEqual(judge(self._plain_title2()), 3)
        self.assertEqual(judge(self._plain_title2(paragraphs=1)), 3)
        self.assertIsNone(judge(self._plain_title2(owner='특이사항 없음')))

    def test_title2_is_found_and_styled(self):
        ns = self.ns
        table = self._plain_title2()
        source = self._hwpx(table)
        found = ns['제목_hwpx_처리'](source)
        self.assertEqual(found, {'Contents/section0.xml': [(0, 3)]})
        target = source.with_name('out.hwpx')
        self.assertEqual(ns['제목_hwpx_처리'](source, target, found), 1)
        with zipfile.ZipFile(target) as z:
            header = self.parse(z.read('Contents/header.xml'))
            section = self.parse(z.read('Contents/section0.xml'))
        out = next(t for t in section.iter() if self.name(t) == 'tbl')
        self.assertEqual(ns['제목_문자열'](out), ns['제목_문자열'](table))
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        faces = {}
        for ff in next(x for x in header.iter() if self.name(x) == 'fontfaces'):
            faces[ff.get('lang').lower()] = {f.get('id'): f.get('face') for f in ff}
        def look(paragraph):
            run = next(r for r in paragraph if self.name(r) == 'run')
            cp = chars[run.get('charPrIDRef')]
            font = next(x for x in cp if self.name(x) == 'fontRef')
            return int(cp.get('height')), faces['hangul'][font.get('hangul')]
        cells = ns['제목_셀들'](out)
        sub, title = [p for p in ns['제목_문단들'](cells[0]) if ns['제목_문자열'](p).strip()]
        self.assertEqual(look(sub), (1500, 'HY헤드라인M'))   # 부제(쉼표 앞 글) 15pt
        self.assertEqual(look(title), (2700, 'HY헤드라인M'))
        self.assertEqual(look(ns['제목_문단들'](cells[1])[0]), (1200, '휴먼명조'))
        self.assertEqual(ns['제목_자식'](out, 'sz').get('width'), '48758')
        self.assertEqual(ns['제목_유형판별'](out), 3)

    def test_title2_without_subtitle_uses_title_paragraph_style(self):
        ns = self.ns
        source = self._hwpx(self._plain_title2(paragraphs=1))
        found = ns['제목_hwpx_처리'](source)
        target = source.with_name('one.hwpx')
        ns['제목_hwpx_처리'](source, target, found)
        with zipfile.ZipFile(target) as z:
            header = self.parse(z.read('Contents/header.xml'))
            section = self.parse(z.read('Contents/section0.xml'))
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        out = next(t for t in section.iter() if self.name(t) == 'tbl')
        title = [p for p in ns['제목_문단들'](ns['제목_셀들'](out)[0]) if ns['제목_문자열'](p).strip()][0]
        run = next(r for r in title if self.name(r) == 'run')
        self.assertEqual(chars[run.get('charPrIDRef')].get('height'), '2700')

    def test_one_by_one_title_box_at_page_start_is_type4(self):
        """1×1 제목 상자는 2×2 유형 판별(1~3) 대상은 아니지만, 쪽 첫머리의 제목다운 1×1 표는 유형 4로 인정한다
        (사용자 요청, 2026-10-10: 중앙부처 보고서의 제목 상자)."""
        ns = self.ns
        _, sample = self._title2_sample()
        one = copy.deepcopy(sample)
        row2 = [r for r in one if self.name(r) == 'tr'][1]
        one.remove(row2)
        one.set('rowCnt', '1')
        one.set('colCnt', '1')
        self.assertEqual(len(ns['제목_셀들'](one)), 1)
        self.assertIsNone(ns['제목_유형판별'](one))
        self.assertTrue(ns['_한칸_제목표인가'](one))
        found = ns['제목_hwpx_처리'](self._hwpx(one))
        self.assertEqual(found, {'Contents/section0.xml': [(0, 4)]})

    def test_title_reference_has_two_by_two_samples_only(self):
        header, section = self.ns['제목_원본자료']()
        tables = [x for x in section.iter() if self.name(x) == 'tbl']
        self.assertEqual([(t.get('rowCnt'), t.get('colCnt')) for t in tables], [('2', '2'), ('2', '2')])
        self.assertEqual([self.ns['제목_유형판별'](t) for t in tables], [1, 2])

    def test_overview_reference_matches_learned_values(self):
        """요지: 문단 좌우 여백 5, 줄간격 140%, 한컴돋움 15 진하게, 자간 0."""
        header, section = self.ns['개요붙임_원본자료']()
        overview = next(x for x in section.iter() if self.name(x) == 'tbl')
        para = self.ns['제목_문단들'](self.ns['제목_셀들'](overview)[0])[0]
        paras = {p.get('id'): p for p in header.iter() if self.name(p) == 'paraPr'}
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        pp = paras[para.get('paraPrIDRef')]
        case = next(x for x in pp.iter() if self.name(x) == 'case')
        margin = next(x for x in case.iter() if self.name(x) == 'margin')
        self.assertEqual([x.get('value') for x in margin if self.name(x) in ('left', 'right')], ['500', '500'])
        self.assertEqual(next(x for x in case.iter() if self.name(x) == 'lineSpacing').get('value'), '140')
        for run in (r for r in para if self.name(r) == 'run'):
            cp = chars[run.get('charPrIDRef')]
            self.assertEqual(cp.get('height'), '1500')
            self.assertTrue(any(self.name(x) == 'bold' for x in cp))
            spacing = next(x for x in cp if self.name(x) == 'spacing')
            self.assertEqual(set(spacing.attrib.values()), {'0'})


if __name__ == '__main__':
    unittest.main()
