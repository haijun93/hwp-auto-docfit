"""라벨 입력 모드의 제목1·개요 표식 표가 서식 표로 바뀌는지 확인한다."""
import copy
from pathlib import Path
import runpy
import tempfile
import unittest
import zipfile


class LabelTableTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.parse = staticmethod(cls.ns['safe_xml_fromstring'])
        cls.name = staticmethod(cls.ns['제목_xml이름'])

    def _plain_one_by_one(self, text):
        """한/글이 만드는 서식 없는 1×1 표(10pt)를 개요 기준 표에서 만들어 낸다."""
        _, section = self.ns['개요붙임_원본자료']()
        table = copy.deepcopy(next(x for x in section.iter() if self.name(x) == 'tbl'))
        cell = self.ns['제목_셀들'](table)[0]
        paras = self.ns['제목_문단들'](cell)
        for p in paras[1:]:
            self.ns['제목_자식'](cell, 'subList').remove(p)
        runs = [r for r in paras[0] if self.name(r) == 'run']
        for extra in runs[1:]:
            paras[0].remove(extra)
        for child in list(runs[0]):
            runs[0].remove(child)
        t = copy.deepcopy(next(x for x in section.iter() if self.name(x) == 't'))
        t.text = text
        runs[0].append(t)
        cell.set('borderFillIDRef', '1')
        paras[0].set('paraPrIDRef', '0')
        runs[0].set('charPrIDRef', '0')
        table.set('borderFillIDRef', '1')
        return table

    def _hwpx(self, tables):
        ns = self.ns
        header, _ = ns['제목_원본자료']()
        chars = next(x for x in header.iter() if self.name(x) == 'charProperties')
        base = copy.deepcopy(next(iter(chars))); base.set('id', '0'); base.set('height', '1000')
        chars.insert(0, base)
        paras = next(x for x in header.iter() if self.name(x) == 'paraProperties')
        para = copy.deepcopy(next(iter(paras))); para.set('id', '0')
        paras.insert(0, para)
        borders = next(x for x in header.iter() if self.name(x) == 'borderFills')
        fill = copy.deepcopy(next(iter(borders))); fill.set('id', '1')
        borders.insert(0, fill)
        section = self.parse(
            b'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
            b'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"/>')
        pt = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
        for table in tables:
            p = ns['XML_자식_추가'](section, section, tag=pt + 'p', attrib={'id': '0', 'paraPrIDRef': '0', 'styleIDRef': '0'})
            run = ns['XML_자식_추가'](p, section, tag=pt + 'run', attrib={'charPrIDRef': '0'})
            run.append(table)
        out = Path(tempfile.mkdtemp(prefix='docfit-label-')) / 'label.hwpx'
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', ns['ET'].tostring(header, encoding='utf-8', xml_declaration=True))
            z.writestr('Contents/section0.xml', ns['ET'].tostring(section, encoding='utf-8', xml_declaration=True))
        return out

    def _read(self, path):
        with zipfile.ZipFile(path) as z:
            return self.parse(z.read('Contents/header.xml')), self.parse(z.read('Contents/section0.xml'))

    def test_title1_and_overview_marker_tables_become_styled_tables(self):
        ns = self.ns
        title, overview = '지구 침공계획(안) 보고', '삼채인의 명랑 지구침략계획을 수립하고 보고드림'
        marks = ns['_라벨_표식']
        source = self._hwpx([self._plain_one_by_one(marks['title1'] + title),
                             self._plain_one_by_one(marks['overview'] + overview)])
        self.assertEqual(ns['라벨_서식표_적용'](source), 2)
        header, section = self._read(source)
        tables = [t for t in section.iter() if self.name(t) == 'tbl']
        self.assertEqual(len(tables), 2)
        # 제목1: 2×2 표, 글은 A1, 날짜·담당자 칸은 비어 있다.
        first = tables[0]
        self.assertEqual((first.get('rowCnt'), first.get('colCnt')), ('2', '2'))
        cells = ns['제목_셀들'](first)
        self.assertEqual(ns['제목_문자열'](cells[0]), title)
        self.assertEqual([ns['제목_문자열'](c) for c in cells[1:]], ['', ''])
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        faces = {f.get('id'): f.get('face') for ff in header.iter()
                 if self.name(ff) == 'fontface' and ff.get('lang') == 'HANGUL' for f in ff}
        heights = set()
        for run in (r for r in cells[0].iter() if self.name(r) == 'run' and ns['제목_문자열'](r).strip()):
            cp = chars[run.get('charPrIDRef')]
            heights.add(cp.get('height'))
        self.assertIn('2700', heights)
        # 개요: 요지 서식(한컴돋움 15pt 굵게), 글은 A1.
        second = tables[1]
        self.assertEqual((second.get('rowCnt'), second.get('colCnt')), ('1', '1'))
        self.assertEqual(ns['제목_문자열'](second), overview)
        run = next(r for r in second.iter() if self.name(r) == 'run' and ns['제목_문자열'](r).strip())
        cp = chars[run.get('charPrIDRef')]
        self.assertEqual(cp.get('height'), '1500')
        self.assertEqual(faces[next(x for x in cp if self.name(x) == 'fontRef').get('hangul')], '한컴돋움')
        # 표식은 남지 않고, 표 id가 겹치지 않는다.
        raw = zipfile.ZipFile(source).read('Contents/section0.xml').decode('utf-8')
        self.assertNotIn('@@DOCFIT', raw)
        ids = [t.get('id') for t in tables]
        self.assertEqual(len(set(ids)), len(ids))

    def test_title2_marker_table_splits_subtitle_at_comma(self):
        ns = self.ns
        text = '희망2023 나눔캠페인, ‘사랑의 온도탑’ 제막행사 검토보고'
        source = self._hwpx([self._plain_one_by_one(ns['_라벨_표식']['title2'] + text)])
        self.assertEqual(ns['라벨_서식표_적용'](source), 1)
        header, section = self._read(source)
        table = next(t for t in section.iter() if self.name(t) == 'tbl')
        self.assertEqual((table.get('rowCnt'), table.get('colCnt')), ('2', '1'))
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        paras = ns['제목_문단들'](ns['제목_셀들'](table)[0])
        self.assertEqual([ns['제목_문자열'](p) for p in paras], ['희망2023 나눔캠페인', '‘사랑의 온도탑’ 제막행사 검토보고'])
        heights = [{chars[r.get('charPrIDRef')].get('height') for r in p if self.name(r) == 'run'
                    and ns['제목_문자열'](r).strip()} for p in paras]
        self.assertEqual(heights, [{'1500'}, {'2700'}])

    def test_document_without_markers_is_left_untouched(self):
        source = self._hwpx([self._plain_one_by_one('일반 1×1 표')])
        before = source.read_bytes()
        self.assertEqual(self.ns['라벨_서식표_적용'](source), 0)
        self.assertEqual(source.read_bytes(), before)

    def test_only_marked_tables_change(self):
        ns = self.ns
        plain = self._plain_one_by_one('표식 없는 표')
        source = self._hwpx([plain, self._plain_one_by_one(ns['_라벨_표식']['overview'] + '개요 문장')])
        self.assertEqual(ns['라벨_서식표_적용'](source), 1)
        _, section = self._read(source)
        tables = [t for t in section.iter() if self.name(t) == 'tbl']
        self.assertEqual(ns['제목_문자열'](tables[0]), '표식 없는 표')
        self.assertEqual(tables[0].get('borderFillIDRef'), '1')  # 손대지 않음

    def test_labeled_blocks_insert_marker_text(self):
        """한/글 삽입 함수는 제목1·개요 블록의 표 첫 칸에 표식 + 글을 넣는다."""
        from unittest.mock import MagicMock
        ns = self.ns
        hwp = MagicMock()
        typed = []
        pset = hwp.HParameterSet.HInsertText
        type(pset).Text = property(lambda self: None, lambda self, v: typed.append(v))
        ns['라벨블록_한글삽입'](hwp, [{'kind': 'title1', 'text': '지구 침공계획(안) 보고'},
                                    {'kind': 'box', 'text': '개요 문장'}])
        self.assertIn(ns['_라벨_표식']['title1'] + '지구 침공계획(안) 보고', typed)
        self.assertIn(ns['_라벨_표식']['overview'] + '개요 문장', typed)

    def test_standalone_conversion_post_processes_after_hangul_quits(self):
        """저장 → 한/글 종료 → 표식 표 서식 적용 순서로 실행된다."""
        import shutil
        from unittest.mock import MagicMock, patch
        ns = self.ns
        fn = ns['텍스트_hwpx_단독변환']
        prepared = self._hwpx([self._plain_one_by_one(ns['_라벨_표식']['title1'] + '제목 글'),
                               self._plain_one_by_one(ns['_라벨_표식']['overview'] + '개요 글')])
        target = prepared.with_name('result.hwpx')
        events = []
        fake = MagicMock()
        fake.Run.return_value = True
        fake.SaveAs.side_effect = lambda path, *a: (events.append('save'), shutil.copyfile(prepared, path))[1] or True
        fake.Quit.side_effect = lambda: events.append('quit')
        real_apply = ns['라벨_서식표_적용']
        def apply(path):
            events.append('apply')
            return real_apply(path)
        with patch.dict(fn.__globals__, {'pythoncom': MagicMock(), '한글_COM_인스턴스_생성': lambda **k: fake,
                                         '라벨블록_한글삽입': lambda *a: None, '라벨_서식표_적용': apply}):
            fn('제목1: 제목 글\n개요: 개요 글', target)
        self.assertEqual(events, ['save', 'quit', 'apply'])
        _, section = self._read(target)
        tables = [t for t in section.iter() if self.name(t) == 'tbl']
        self.assertEqual([(t.get('rowCnt'), t.get('colCnt')) for t in tables], [('2', '2'), ('1', '1')])
        self.assertNotIn('@@DOCFIT', zipfile.ZipFile(target).read('Contents/section0.xml').decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
