"""준말(약어) → 본말 등록표와 문서 줄 변환을 확인한다."""
import copy
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from docfit_core.abbreviations import (DEFAULT_ENTRIES, clean_key, match_line, normalize, split_title2, upsert)

HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
HS = 'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
REGISTRY = {
    '제목1': {'type': 'format', 'value': 'title1'},
    '제목2': {'type': 'format', 'value': 'title2'},
    '개요': {'type': 'format', 'value': 'overview'},
    '요약': {'type': 'text', 'value': '본 문서는 다음과 같이 보고함'},
    '로1': {'type': 'format', 'value': 'midtitle'},
    '로3': {'type': 'format', 'value': 'midtitle'},
    '붙임': {'type': 'format', 'value': 'attach1'},
    '붙임2': {'type': 'format', 'value': 'attach2'},
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

    def test_title_word_is_treated_as_title1(self):
        """준말 "제목:"은 "제목1:"로 취급한다(등록표에 '제목'이 따로 있으면 그 등록이 우선)."""
        self.assertEqual(match_line('제목: 지구 침공계획(안) 보고', REGISTRY), ('제목1', '지구 침공계획(안) 보고', 4))
        self.assertEqual(match_line('제목 :지구', REGISTRY)[:2], ('제목1', '지구'))
        own = dict(REGISTRY, 제목={'type': 'text', 'value': '자체 제목'})
        self.assertEqual(match_line('제목: 가', own)[0], '제목')
        no_title1 = {k: v for k, v in REGISTRY.items() if k != '제목1'}
        self.assertIsNone(match_line('제목: 가', no_title1))   # 제목1이 없으면 별칭도 없다

    def test_split_title2_at_first_comma(self):
        self.assertEqual(split_title2('희망2023 나눔캠페인, ‘사랑의 온도탑’ 제막행사 검토보고'),
                         ('희망2023 나눔캠페인', '‘사랑의 온도탑’ 제막행사 검토보고'))
        self.assertEqual(split_title2('‘사랑의 온도탑’ 제막행사 검토보고'), ('', '‘사랑의 온도탑’ 제막행사 검토보고'))
        self.assertEqual(split_title2('가, 나, 다'), ('가', '나, 다'))
        self.assertEqual(split_title2('가，나'), ('가', '나'))
        self.assertEqual(split_title2('가,'), ('', '가'))


class DefaultsTest(unittest.TestCase):
    def test_defaults_work_without_any_registration(self):
        """"제목1 :"·"개요 :" 같은 기본 준말은 사용자가 등록하지 않아도 쓸 수 있다."""
        from docfit_core.abbreviations import merge_with_defaults
        merged = merge_with_defaults({})
        self.assertEqual(match_line('제목1 : 지구 침공계획(안) 보고', merged)[:2], ('제목1', '지구 침공계획(안) 보고'))
        self.assertEqual(match_line('개요 : 삼채인의 명랑', merged)[:2], ('개요', '삼채인의 명랑'))
        self.assertEqual(match_line('제목: 가', merged)[0], '제목1')
        self.assertEqual(match_line('로1 : 추진배경', merged)[0], '로1')
        self.assertEqual(match_line('붙임: 자료', merged)[0], '붙임')
        self.assertEqual(merge_with_defaults({}, False), {})
        own = merge_with_defaults({'개요': {'type': 'text', 'value': '내 개요'}})
        self.assertEqual(own['개요'], {'type': 'text', 'value': '내 개요'})   # 사용자 등록 우선
        self.assertIn('제목1', own)

    def test_run_builds_registry_from_settings_with_defaults(self):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        build = ns['준말_사용표_만들기']
        self.assertIn('제목1', build({}))
        self.assertIn('제목1', build({'abbreviations': {}}))
        self.assertEqual(build({'abbreviation_defaults': False}), {})
        self.assertEqual(set(build({'abbreviation_defaults': False, 'abbreviations': {'요약': {'type': 'text', 'value': 'x'}}})), {'요약'})
        self.assertTrue(ns['기본_설정']['abbreviation_defaults'])


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

    def test_title_line_becomes_title1_table_in_document(self):
        ns = self.ns
        found, count, _, section = self._convert(self._p('제목: 지구 침공계획(안) 보고'))
        self.assertEqual(found, {'Contents/section0.xml': [(0, '제목1', '지구 침공계획(안) 보고')]})
        table = next(t for t in section.iter() if self.name(t) == 'tbl')
        self.assertEqual((table.get('rowCnt'), table.get('colCnt')), ('2', '2'))
        self.assertEqual(ns['제목_문자열'](ns['제목_셀들'](table)[0]), '지구 침공계획(안) 보고')

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

    def _faces_and_chars(self, header):
        faces = {f.get('id'): f.get('face') for ff in header.iter()
                 if self.name(ff) == 'fontface' and ff.get('lang') == 'HANGUL' for f in ff}
        return faces, {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}

    def test_midtitle_abbreviation_numeral_from_key_and_text_in_text_cell(self):
        ns = self.ns
        body = self._p('로1 : 추진배경') + self._p('로3: 행 정 사 항')
        found, count, header, section = self._convert(body)
        self.assertEqual(count, 2)
        tables = [t for t in section.iter() if self.name(t) == 'tbl']
        self.assertEqual([[ns['제목_문자열'](c) for c in ns['제목_셀들'](t)] for t in tables],
                         [['Ⅰ', '', '추진배경'], ['Ⅲ', '', '행 정 사 항']])
        faces, chars = self._faces_and_chars(header)
        for table in tables:
            self.assertEqual(ns['중제목_유형판별'](table), 1)      # 다시 판별해도 중제목
            for run in (r for r in table.iter() if self.name(r) == 'run' and ns['제목_문자열'](r).strip()):
                cp = chars[run.get('charPrIDRef')]
                self.assertEqual(cp.get('height'), '2000')
                font = next(x for x in cp if self.name(x) == 'fontRef')
                self.assertEqual(faces[font.get('hangul')], 'HY견고딕')
        numeral_run = next(r for r in ns['제목_셀들'](tables[0])[0].iter() if self.name(r) == 'run')
        self.assertTrue(any(self.name(x) == 'bold' for x in chars[numeral_run.get('charPrIDRef')]))
        self.assertNotIn('로1', ''.join(self._texts(section)))

    def test_midtitle_bold_switch_and_page_width_cap(self):
        ns = self.ns
        long_text = '아주 긴 중제목 문구 ' * 20
        fn = ns['준말_hwpx_처리']
        source = self._doc(self._p('로1: ' + long_text))
        with patch.dict(fn.__globals__, {'준말_등록표': REGISTRY, '중제목_번호굵게': False}):
            target = source.with_name('nb.hwpx')
            fn(source, target, fn(source))
        with zipfile.ZipFile(target) as z:
            header = self.parse(z.read('Contents/header.xml'))
            section = self.parse(z.read('Contents/section0.xml'))
        _, chars = self._faces_and_chars(header)
        table = next(t for t in section.iter() if self.name(t) == 'tbl')
        numeral_run = next(r for r in ns['제목_셀들'](table)[0].iter() if self.name(r) == 'run')
        self.assertFalse(any(self.name(x) == 'bold' for x in chars[numeral_run.get('charPrIDRef')]))
        self.assertLessEqual(int(ns['제목_자식'](table, 'sz').get('width')), 42520)   # 쪽 본문 폭을 넘지 않는다

    def test_attachment_abbreviations_use_attachment_formats(self):
        ns = self.ns
        body = self._p('붙임: 우수시책 요약서 작성서식') + self._p('붙임2 : 참고자료')
        found, count, header, section = self._convert(body)
        self.assertEqual(count, 2)
        tables = [t for t in section.iter() if self.name(t) == 'tbl']
        self.assertEqual([[ns['제목_문자열'](c) for c in ns['제목_셀들'](t)] for t in tables],
                         [['붙임', '', '우수시책 요약서 작성서식'], ['붙임', '참고자료']])
        self.assertEqual([ns['붙임_유형판별'](t) for t in tables], [1, 2])
        faces, chars = self._faces_and_chars(header)
        for table in tables:
            for run in (r for r in table.iter() if self.name(r) == 'run' and ns['제목_문자열'](r).strip()):
                font = next(x for x in chars[run.get('charPrIDRef')] if self.name(x) == 'fontRef')
                self.assertEqual(faces[font.get('hangul')], 'HY헤드라인M')

    def test_every_format_kind_leaves_only_valid_style_references(self):
        """모든 서식 표 종류를 변환한 뒤에도 문단·글자·테두리 참조가 헤더에 실제로 있어야 한다."""
        body = ''.join(self._p(line) for line in (
            '제목1: 가', '제목2: 부제, 제목', '개요: 나', '로1: 다', '붙임: 라', '붙임2: 마', '제목1:', '로3:', '붙임:'))
        _, count, header, section = self._convert(body)
        self.assertEqual(count, 9)
        ids = {tag: {x.get('id') for x in header.iter() if self.name(x) == tag}
               for tag in ('paraPr', 'charPr', 'borderFill', 'tabPr')}
        used = {'paraPr': set(), 'charPr': set(), 'borderFill': set()}
        for x in section.iter():
            if x.get('paraPrIDRef') is not None: used['paraPr'].add(x.get('paraPrIDRef'))
            if x.get('charPrIDRef') is not None: used['charPr'].add(x.get('charPrIDRef'))
            if x.get('borderFillIDRef') is not None: used['borderFill'].add(x.get('borderFillIDRef'))
        for x in header.iter():   # 헤더 안 서로 간 참조
            if self.name(x) == 'charPr': used['borderFill'].add(x.get('borderFillIDRef'))
            if self.name(x) == 'paraPr':
                used['tabPr'] = used.get('tabPr', set()) | {x.get('tabPrIDRef')}
        for tag, refs in used.items():
            self.assertLessEqual({r for r in refs if r is not None}, ids[tag], tag)
        empty_titles = [t for t in section.iter() if self.name(t) == 'tbl']
        self.assertEqual(len(empty_titles), 9)

    def test_midtitle_key_needs_a_roman_number(self):
        from docfit_core.abbreviations import roman_of_key
        self.assertEqual([roman_of_key(k) for k in ('로1', '로3', '로12', '로', '로13', '로0')], ['Ⅰ', 'Ⅲ', 'Ⅻ', '', '', ''])
        self.assertEqual(normalize({'로': {'type': 'format', 'value': 'midtitle'}}), {})
        entries, error = upsert({}, '로', 'format', 'midtitle')
        self.assertTrue(error)
        self.assertEqual(entries, {})
        self.assertEqual(upsert({}, '로2', 'format', 'midtitle')[0]['로2']['value'], 'midtitle')
        self.assertEqual(normalize(DEFAULT_ENTRIES), DEFAULT_ENTRIES)
        self.assertEqual(DEFAULT_ENTRIES['붙임'], {'type': 'format', 'value': 'attach1'})

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

    def test_stage_reads_original_hwpx_and_reopens_only_when_something_changed(self):
        """기본 준말 사용표로 "제목1 :"·"개요 :" 줄이 있는 HWPX를 처리하면 결과를 한 번만 다시 연다."""
        from docfit_core.abbreviations import merge_with_defaults
        ns = self.ns
        stage = ns['준말_선행적용']
        registry = merge_with_defaults({})
        opened = Mock(return_value=True)
        env = {'준말_등록표': registry, '한글_문서_열기': opened, 'hwp': object(), '로그': Mock(),
               '중단_요청됨': lambda: False, '진단로그': Mock()}
        source = self._doc(self._p('제목1 : 지구 침공계획(안) 보고') + self._p('개요 : 삼채인의 명랑 지구침략계획을 수립하고 보고드림')
                           + self._p('□ 보고 개요'))
        with patch.dict(stage.__globals__, env):
            notice = {}
            self.assertTrue(stage(str(source), 현재문서_기준=False, 변경알림=notice))
        self.assertTrue(notice['changed'])
        self.assertEqual(opened.call_count, 1)
        self.assertEqual(Path(opened.call_args.args[1]).name, 'abbrev.hwpx')
        # 바꿀 줄이 없는 문서는 다시 열지 않는다.
        plain = self._doc(self._p('□ 보고 개요') + self._p('일시: 오늘'))
        opened.reset_mock()
        with patch.dict(stage.__globals__, dict(env, 한글_문서_열기=opened)):
            notice = {}
            self.assertTrue(stage(str(plain), 현재문서_기준=False, 변경알림=notice))
        self.assertFalse(notice['changed'])
        opened.assert_not_called()


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
