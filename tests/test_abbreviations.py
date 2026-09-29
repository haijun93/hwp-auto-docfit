"""준말(약어) → 본말 등록표와 문서 줄 변환을 확인한다."""
import copy
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from docfit_core.abbreviations import (DEFAULT_ENTRIES, clean_key, match_line, normalize, split_title2)

HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
HS = 'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
REGISTRY = {
    '제목1': {'type': 'format', 'value': 'title1'},
    '제목2': {'type': 'format', 'value': 'title2'},
    '개요': {'type': 'format', 'value': 'overview'},
    '요약': {'type': 'text', 'value': '본 문서는 다음과 같이 보고함'},
}


class RegistryTest(unittest.TestCase):
    def test_normalize_keeps_only_valid_entries(self):
        raw = {'제목1': {'type': 'format', 'value': 'title1'}, '요약': {'type': 'text', 'value': ' 문구 '},
               '잘못 된': {'type': 'text', 'value': 'x'}, '콜론:': {'type': 'text', 'value': 'x'},
               '표': {'type': 'format', 'value': '없는종류'}, '빈문구': {'type': 'text', 'value': '  '},
               '깨짐': 'text'}
        self.assertEqual(normalize(raw), {'제목1': {'type': 'format', 'value': 'title1'},
                                          '요약': {'type': 'text', 'value': '문구'}})
        self.assertEqual(normalize(None), {})
        self.assertEqual(normalize(DEFAULT_ENTRIES), DEFAULT_ENTRIES)
        self.assertEqual(clean_key(' 제목1 '), '제목1')
        self.assertEqual(clean_key('두 어절'), '')

    def test_match_requires_registered_first_word_followed_by_colon(self):
        self.assertEqual(match_line('제목1: 지구 침공계획(안) 보고', REGISTRY), ('제목1', '지구 침공계획(안) 보고', 5))
        self.assertEqual(match_line('  제목1 :지구', REGISTRY)[:2], ('제목1', '지구'))
        self.assertEqual(match_line('제목1：지구', REGISTRY)[:2], ('제목1', '지구'))
        self.assertEqual(match_line('제목1:', REGISTRY)[:2], ('제목1', ''))
        for text in ('제목1', '제목1 지구: 가', '일시: 오늘', '제목11: 가', ''):
            self.assertIsNone(match_line(text, REGISTRY), text)
        self.assertIsNone(match_line('제목1: 가', {}))

    def test_split_title2_at_first_comma(self):
        self.assertEqual(split_title2('희망2023 나눔캠페인, ‘사랑의 온도탑’ 제막행사 검토보고'),
                         ('희망2023 나눔캠페인', '‘사랑의 온도탑’ 제막행사 검토보고'))
        self.assertEqual(split_title2('‘사랑의 온도탑’ 제막행사 검토보고'), ('', '‘사랑의 온도탑’ 제막행사 검토보고'))
        self.assertEqual(split_title2('가, 나, 다'), ('가', '나, 다'))
        self.assertEqual(split_title2('가，나'), ('가', '나'))
        self.assertEqual(split_title2('가,'), ('', '가'))


class DocumentConversionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.parse = staticmethod(cls.ns['safe_xml_fromstring'])
        cls.name = staticmethod(cls.ns['제목_xml이름'])

    def _doc(self, body):
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
        section = f'<hs:sec {HS} {HP}>{body}</hs:sec>'.encode('utf-8')
        out = Path(tempfile.mkdtemp(prefix='docfit-abbr-')) / 'in.hwpx'
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', ns['ET'].tostring(header, encoding='utf-8', xml_declaration=True))
            z.writestr('Contents/section0.xml', section)
        return out

    @staticmethod
    def _p(*runs, attrs=''):
        inner = ''.join(f'<hp:run charPrIDRef="0"><hp:t>{r}</hp:t></hp:run>' if not r.startswith('<') else r
                        for r in runs)
        return f'<hp:p id="1" paraPrIDRef="0" styleIDRef="0" {attrs}>{inner}</hp:p>'

    BODY_SEC = ('<hp:run charPrIDRef="0"><hp:secPr id="" textDirection="HORIZONTAL"/>'
                '<hp:ctrl><hp:colPr id="" type="NEWSPAPER"/></hp:ctrl></hp:run>')

    def _convert(self, body, registry=REGISTRY):
        ns = self.ns
        source = self._doc(body)
        fn = ns['준말_hwpx_처리']
        with patch.dict(fn.__globals__, {'준말_등록표': registry}):
            found = fn(source)
            target = source.with_name('out.hwpx')
            count = fn(source, target, found)
        with zipfile.ZipFile(target) as z:
            header = self.parse(z.read('Contents/header.xml'))
            section = self.parse(z.read('Contents/section0.xml'))
        return found, count, header, section

    def _texts(self, section):
        ns = self.ns
        return [ns['제목_문자열'](p) for p in section if self.name(p) == 'p']

    def test_format_lines_become_tables_and_label_lines_disappear(self):
        ns = self.ns
        body = (self._p(self.BODY_SEC, '제목1: 지구 침공계획(안) 보고')
                + self._p('본문 첫 줄')
                + self._p('개요 : 삼채인의 명랑 지구침략계획을 수립하고 보고드림')
                + self._p('일시: 오늘'))
        found, count, header, section = self._convert(body)
        self.assertEqual(found, {'Contents/section0.xml': [(0, '제목1', '지구 침공계획(안) 보고'),
                                                           (2, '개요', '삼채인의 명랑 지구침략계획을 수립하고 보고드림')]})
        self.assertEqual(count, 2)
        paragraphs = [p for p in section if self.name(p) == 'p']
        # 첫 문단: 구역 설정(secPr)이 그대로 있고 표가 들어갔다.
        self.assertTrue(any(self.name(x) == 'secPr' for x in paragraphs[0].iter()))
        first = next(t for t in paragraphs[0].iter() if self.name(t) == 'tbl')
        self.assertEqual((first.get('rowCnt'), first.get('colCnt')), ('2', '2'))
        cells = ns['제목_셀들'](first)
        self.assertEqual(ns['제목_문자열'](cells[0]), '지구 침공계획(안) 보고')
        self.assertEqual([ns['제목_문자열'](c) for c in cells[1:]], ['', ''])
        third = next(t for t in paragraphs[2].iter() if self.name(t) == 'tbl')
        self.assertEqual((third.get('rowCnt'), third.get('colCnt')), ('1', '1'))
        self.assertEqual(ns['제목_문자열'](third), '삼채인의 명랑 지구침략계획을 수립하고 보고드림')
        # 준말 줄 글은 남지 않고, 다른 줄은 그대로다.
        raw = ''.join(self._texts(section))
        self.assertNotIn('제목1', raw)
        self.assertNotIn('개요 :', raw)
        self.assertEqual(ns['제목_문자열'](paragraphs[1]), '본문 첫 줄')
        self.assertEqual(ns['제목_문자열'](paragraphs[3]), '일시: 오늘')
        ids = [t.get('id') for t in section.iter() if self.name(t) == 'tbl']
        self.assertEqual(len(set(ids)), len(ids))

    def test_title2_splits_subtitle_at_comma_and_centers_all_title_text(self):
        ns = self.ns
        body = (self._p('제목2: 희망2023 나눔캠페인, ‘사랑의 온도탑’ 제막행사 검토보고')
                + self._p('제목2: ‘사랑의 온도탑’ 제막행사 검토보고'))
        _, count, header, section = self._convert(body)
        self.assertEqual(count, 2)
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        paras = {p.get('id'): p for p in header.iter() if self.name(p) == 'paraPr'}
        def align(paragraph):
            pp = paras[paragraph.get('paraPrIDRef')]
            return next(x for x in pp if self.name(x) == 'align').get('horizontal')
        def sizes(paragraph):
            return {chars[r.get('charPrIDRef')].get('height') for r in paragraph if self.name(r) == 'run'
                    and ns['제목_문자열'](r).strip()}
        tables = [t for t in section.iter() if self.name(t) == 'tbl']
        with_sub = [p for p in ns['제목_문단들'](ns['제목_셀들'](tables[0])[0])]
        self.assertEqual([ns['제목_문자열'](p) for p in with_sub],
                         ['희망2023 나눔캠페인', '‘사랑의 온도탑’ 제막행사 검토보고'])
        self.assertEqual(sizes(with_sub[0]), {'1500'})   # 쉼표 앞 = 부제 15pt
        self.assertEqual(sizes(with_sub[1]), {'2700'})   # 쉼표 뒤 = 제목 27pt
        self.assertEqual([align(p) for p in with_sub], ['CENTER', 'CENTER'])
        self.assertEqual((tables[0].get('rowCnt'), tables[0].get('colCnt')), ('2', '1'))
        only_title = ns['제목_문단들'](ns['제목_셀들'](tables[1])[0])
        self.assertEqual(len(only_title), 1)             # 쉼표 없음 = 27pt 제목 한 줄
        self.assertEqual(sizes(only_title[0]), {'2700'})
        self.assertEqual(align(only_title[0]), 'CENTER')

    def test_title1_text_is_centered_27pt(self):
        ns = self.ns
        _, _, header, section = self._convert(self._p('제목1: 지구 침공계획(안) 보고'))
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        paras = {p.get('id'): p for p in header.iter() if self.name(p) == 'paraPr'}
        table = next(t for t in section.iter() if self.name(t) == 'tbl')
        p = ns['제목_문단들'](ns['제목_셀들'](table)[0])[0]
        self.assertEqual(next(x for x in paras[p.get('paraPrIDRef')] if self.name(x) == 'align').get('horizontal'), 'CENTER')
        run = next(r for r in p if self.name(r) == 'run')
        self.assertEqual(chars[run.get('charPrIDRef')].get('height'), '2700')

    def test_text_type_replaces_abbreviation_and_keeps_rest_formatting(self):
        body = ('<hp:p id="1" paraPrIDRef="0" styleIDRef="0">'
                '<hp:run charPrIDRef="0"><hp:t>요약</hp:t></hp:run>'
                '<hp:run charPrIDRef="0"><hp:t> : 뒤 </hp:t></hp:run>'
                '<hp:run charPrIDRef="1"><hp:t>글</hp:t></hp:run></hp:p>')
        _, count, _, section = self._convert(body)
        self.assertEqual(count, 1)
        self.assertEqual(self._texts(section), ['본 문서는 다음과 같이 보고함 뒤 글'])
        runs = [r for r in next(p for p in section if self.name(p) == 'p') if self.name(r) == 'run']
        self.assertEqual(runs[-1].get('charPrIDRef'), '1')   # 나머지 글의 글자 모양 유지

    def test_lines_with_objects_or_inside_tables_are_ignored(self):
        body = (self._p('제목1: 표 안', attrs='') .replace('<hp:t>제목1: 표 안</hp:t>', '<hp:t>제목1: 표 안</hp:t><hp:tbl/>'))
        found, count, _, _ = self._convert(body)
        self.assertEqual(found, {'Contents/section0.xml': []})
        self.assertEqual(count, 0)

    def test_empty_registry_finds_nothing_and_stage_is_a_noop(self):
        ns = self.ns
        source = self._doc(self._p('제목1: 가'))
        fn = ns['준말_hwpx_처리']
        with patch.dict(fn.__globals__, {'준말_등록표': {}}):
            self.assertEqual(fn(source), {'Contents/section0.xml': []})
        stage = ns['준말_선행적용']
        runner = Mock(return_value=True)
        with patch.dict(stage.__globals__, {'준말_등록표': {}, '제목붙임_선행적용': runner}):
            self.assertTrue(stage('C:/원본/문서.hwpx'))
        runner.assert_not_called()
        with patch.dict(stage.__globals__, {'준말_등록표': REGISTRY, '제목붙임_선행적용': runner}):
            self.assertTrue(stage('C:/원본/문서.hwpx'))
        args, kwargs = runner.call_args
        self.assertTrue(kwargs['현재문서_기준'])
        self.assertEqual([item[1] for item in kwargs['처리목록']], ['준말 변환'])


class PreFormatProcessorListTest(unittest.TestCase):
    def test_custom_processor_list_runs_only_those_processors(self):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        fn = ns['제목붙임_선행적용']
        seen = []
        def processor(source, target=None, selections=None):
            seen.append(Path(source).name)
            return {}
        with patch.dict(fn.__globals__, {'제목4종_사용': True, '붙임2종_사용': True, '중제목_사용': True,
                                         '로그': Mock(), '중단_요청됨': lambda: False}):
            self.assertTrue(fn('C:/원본/문서.hwpx', 처리목록=((True, '준말 변환', processor, 'a.hwpx'),)))
        self.assertEqual(seen, ['문서.hwpx'])


if __name__ == '__main__':
    unittest.main()
