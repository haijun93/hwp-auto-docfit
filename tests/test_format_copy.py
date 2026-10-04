"""서식 복사 전면 복제(FORMAT_COPY_DESIGN.md) 1단계: 계층 추가 서식 적용 값, 예시 열 비율 유지, 한 칸 상자, 용지 알림."""
import copy
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from docfit_core import format_elements as fe

HS = 'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
SEC = ('<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:secPr id="">'
       '<hp:pagePr landscape="WIDELY" width="59528" height="84188"><hp:margin header="4252" footer="4252" '
       'gutter="0" left="5669" right="5669" top="5669" bottom="4252"/></hp:pagePr></hp:secPr></hp:run></hp:p>')


class FormatCopyStage1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.name = staticmethod(cls.ns['제목_xml이름'])

    def test_extra_values_convert_to_com_items_without_removing_emphasis(self):
        convert = self.ns['계층_추가서식_값']
        글자, 문단 = convert({"font_latin": "Arial", "ratio": 95, "spacing": -5, "italic": True, "underline": "BOTTOM",
                          "strikeout": False, "color": "#ff0000", "shade": "없음", "align": "LEFT",
                          "break_word": "BREAK_WORD"})
        self.assertEqual(글자["FaceNameLatin"], "Arial")
        self.assertEqual((글자["RatioHangul"], 글자["SpacingLatin"]), (95, -5))
        self.assertEqual((글자["Italic"], 글자["UnderlineType"], 글자["TextColor"]), (1, 1, "#FF0000"))
        self.assertNotIn("StrikeOutType", 글자)          # 예시에 없는 강조는 지우지 않는다(넣지도 않음)
        self.assertNotIn("ShadeColor", 글자)
        self.assertEqual(문단, {"AlignType": 1, "BreakNonLatinWord": 0})
        글자, 문단 = convert({"color": "#000000", "italic": False, "underline": "NONE", "ratio": 100,
                          "align": "JUSTIFY", "break_word": "KEEP_WORD"}, 장평_사용=False)
        self.assertEqual(글자, {})                         # 검은 글자·장평 끔
        self.assertEqual(문단, {"AlignType": 0, "BreakNonLatinWord": 1})

    def test_example_table_keeps_column_ratio_at_full_width(self):
        _, section = self.ns['제목_원본자료']()
        title = copy.deepcopy(next(x for x in section.iter() if self.name(x) == 'tbl'))
        cells = self.ns['제목_셀들'](title)
        before = [int(self.ns['제목_자식'](c, 'cellSz').get('width')) for c in cells[1:]]
        self.ns['_서식표_가로맞춤'](title, 48190, 비례=True)
        after = [int(self.ns['제목_자식'](c, 'cellSz').get('width')) for c in cells[1:]]
        out = self.ns['제목_자식'](title, 'outMargin')
        target = 48190 - int(out.get('left')) - int(out.get('right'))
        self.assertEqual(sum(after), target)
        self.assertAlmostEqual(after[0] / after[1], before[0] / before[1], places=2)   # 예시 열 비율 유지

    def test_body_box_takes_example_box_format(self):
        ns = self.ns
        header, extra = ns['개요붙임_원본자료']()
        sample_table = next(x for x in extra.iter() if self.name(x) == 'tbl')
        sample = fe.extract_sample(header, sample_table)
        box = copy.deepcopy(sample_table)
        for t in (x for x in box.iter() if self.name(x) == 't'):
            t.text = ''
        first = next(x for x in box.iter() if self.name(x) == 't')
        first.text = '< 핵심 추진과제 > 본문 상자 글은 열다섯 글자를 넘습니다'
        body = ('<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>ㅇ 앞 문장</hp:t></hp:run></hp:p>'
                '<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">'
                + ns['ET'].tostring(box, encoding='unicode') + '<hp:t/></hp:run></hp:p>')
        folder = Path(tempfile.mkdtemp(prefix='docfit-box-'))
        source = folder / 'in.hwpx'
        with zipfile.ZipFile(source, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', ns['ET'].tostring(header, encoding='utf-8', xml_declaration=True))
            z.writestr('Contents/section0.xml', f'<hs:sec {HS} {HP}>{SEC}{body}</hs:sec>')
        fn = ns['상자서식_hwpx_처리']
        with patch.dict(fn.__globals__, {'활성_서식표_프로필': {'box': sample}, '로그': Mock()}):
            found = fn(source)
            self.assertEqual(found, {'Contents/section0.xml': [0]})
            self.assertEqual(fn(source, folder / 'out.hwpx', found), 1)
        with patch.dict(fn.__globals__, {'활성_서식표_프로필': None}):
            self.assertEqual(fn(source), {'Contents/section0.xml': []})   # 예시 상자가 없으면 대상 없음

    def test_profile_table_style_comes_before_abbreviation_style(self):
        # 결정 5: 서식 프로필이 예시 보고서의 일반 표에서 배운 표 서식이 준말 '표' 서식보다 먼저다.
        from docfit_core.table_style import default_style
        fn = self.ns['기본표서식']
        learned = dict(default_style(), source='예시.hwpx')
        with patch.dict(fn.__globals__, {'활성_표서식_프로필': learned, '준말_등록표': {}}):
            self.assertIs(fn(), learned)
        with patch.dict(fn.__globals__, {'활성_표서식_프로필': None, '준말_등록표': {}}):
            self.assertIsNone(fn())

    def test_example_analysis_learns_general_table_but_not_title_table(self):
        from tests import test_format_elements as fx
        folder = Path(tempfile.mkdtemp(prefix='docfit-table-profile-'))
        analyze = self.ns['hwpx_서식_분석']
        # 제목 표(2×2)와 개요 표만 있는 예시: 제목 표를 일반 표 서식으로 배우지 않는다.
        only_title = folder / 'title.hwpx'
        with zipfile.ZipFile(only_title, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', fx.HEADER)
            z.writestr('Contents/section0.xml', fx.SECTION)
        self.assertNotIn('table_style', analyze(only_title))
        # 일반 표(3행 3열)가 있으면 그 표에서 배운다.
        grid = ('<hp:tbl rowCnt="3" colCnt="3" borderFillIDRef="1"><hp:sz width="30000" height="3000"/>'
                '<hp:outMargin left="283" right="283" top="283" bottom="283"/>'
                '<hp:inMargin left="141" right="141" top="141" bottom="141"/>'
                + ''.join('<hp:tr>' + ''.join(fx._cell(c, r, 2 if r == 0 else 1, 10000, [(1 if r == 0 else 0, f'칸{r}{c}')])
                                              for c in range(3)) + '</hp:tr>' for r in range(3))
                + '</hp:tbl>')
        section = fx.SECTION.replace('</hs:sec>', f'<hp:p paraPrIDRef="1" styleIDRef="0"><hp:run charPrIDRef="0">'
                                                  f'{grid}</hp:run></hp:p></hs:sec>')
        with_grid = folder / 'grid.hwpx'
        with zipfile.ZipFile(with_grid, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', fx.HEADER)
            z.writestr('Contents/section0.xml', section)
        profile = analyze(with_grid)
        self.assertEqual((profile['table_style']['rows'], profile['table_style']['cols']), (3, 3))
        self.assertIn('일반 표 서식', profile['summary'])
        # 일반 표가 여럿이면 칸이 가장 많은 표가 아니라 일반 표 대표값과 가장 많이 같은 표에서 배운다
        # (결재란처럼 모양이 다른 4×4 표 하나의 굵게·테두리가 모든 표에 퍼지지 않게, 2026-10-04).
        def table(size, border, char):
            return (f'<hp:tbl rowCnt="{size}" colCnt="{size}" borderFillIDRef="1"><hp:sz width="30000" height="3000"/>'
                    '<hp:outMargin left="283" right="283" top="283" bottom="283"/>'
                    '<hp:inMargin left="141" right="141" top="141" bottom="141"/>'
                    + ''.join('<hp:tr>' + ''.join(fx._cell(c, r, border, 10000, [(char, f'칸{r}{c}')])
                                                  for c in range(size)) + '</hp:tr>' for r in range(size))
                    + '</hp:tbl>')
        tables = ''.join(f'<hp:p paraPrIDRef="1" styleIDRef="0"><hp:run charPrIDRef="0">{t}</hp:run></hp:p>'
                         for t in (table(4, 2, 1), table(3, 1, 0), table(3, 1, 0), table(3, 1, 0)))
        mixed = folder / 'mixed.hwpx'
        with zipfile.ZipFile(mixed, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', fx.HEADER)
            z.writestr('Contents/section0.xml', fx.SECTION.replace('</hs:sec>', tables + '</hs:sec>'))
        profile = analyze(mixed)
        self.assertEqual((profile['table_style']['rows'], profile['table_style']['cols']), (3, 3))

    def test_hanging_rule_from_example_chooses_engine_offset(self):
        fn = self.ns['문단_내어쓰기_기준_오프셋']
        text = 'ㅇ (개요) 본문 문장'
        settings = dict(self.ns['표준서식_설정'])
        with patch.dict(fn.__globals__, {'표준서식_설정': dict(settings, 내어쓰기_규칙={})}):
            self.assertEqual(fn(text), 7)            # 규칙 없음: 지금처럼 라벨 뒤
        with patch.dict(fn.__globals__, {'표준서식_설정': dict(settings, 내어쓰기_규칙={'ㅇ': 'after_marker'})}):
            self.assertEqual(fn(text), 2)            # 예시가 기호 뒤 맞춤
        with patch.dict(fn.__globals__, {'표준서식_설정': dict(settings, 내어쓰기_규칙={'ㅇ': 'fixed'})}):
            self.assertIsNone(fn(text))              # 고정 값: 규칙이 손대지 않고 복사한 값을 씀

    def test_spacing_rules_set_prev_spacing_for_first_sentence_and_level_return(self):
        fn = self.ns['복사_간격_규칙_적용']
        doc = Mock()
        params = Mock()
        doc.CreateAction.return_value.CreateSet.return_value = params
        settings = dict(self.ns['표준서식_설정'], 제목뒤_간격=1400, 복귀_간격={'ㅇ': 2400})
        state = {'첫문장': False, '직전깊이': None}
        with patch.dict(fn.__globals__, {'hwp': doc, '표준서식_설정': settings, '_문서_제목표_있음': True,
                                         '_간격규칙_상태': state, '표준서식_문단위간격_사용': True}):
            self.assertEqual(fn('□', '□ 첫 문장'), 1400)          # 제목·개요 뒤 첫 문장
            params.SetItem.assert_called_with('PrevSpacing', 2800)
            self.assertIsNone(fn('ㅇ', 'ㅇ 본문'))                  # 더 깊어지는 것은 그대로
            self.assertIsNone(fn('-', '- 내용'))
            self.assertEqual(fn('ㅇ', 'ㅇ 다음 본문'), 2400)        # '-' 다음 'ㅇ' = 계층 복귀
        state.update(첫문장=False, 직전깊이=None)
        with patch.dict(fn.__globals__, {'hwp': doc, '표준서식_설정': settings, '_문서_제목표_있음': False,
                                         '_간격규칙_상태': state, '표준서식_문단위간격_사용': True}):
            self.assertIsNone(fn('□', '□ 첫 문장'))                # 제목 표가 없는 문서

    def test_element_modes_and_coverage(self):
        from tests import test_format_elements as fx
        folder = Path(tempfile.mkdtemp(prefix='docfit-coverage-'))
        path = folder / 'example.hwpx'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', fx.HEADER)
            z.writestr('Contents/section0.xml', fx.SECTION)
        analysis = fe.analyze_format_elements(path, fx.classify)
        self.assertEqual(fe.element_mode('font', ('group', 0)), fe.MODE_VALUE)
        self.assertEqual(fe.element_mode('hanging_rule', ('group', 0)), fe.MODE_RULE)
        self.assertEqual(fe.element_mode('after_spaces', ('group', 0)), fe.MODE_SHOW)
        self.assertEqual(fe.element_mode('page_width', ('page',)), fe.MODE_SHOW)
        self.assertEqual(fe.element_mode('page_left', ('page',)), fe.MODE_VALUE)
        found = fe.coverage(analysis)
        self.assertEqual(found['total'], found['applied'] + found['shown'])
        self.assertGreater(found['applied'] / found['total'], 0.8)

    def test_old_profile_is_upgraded_when_loaded(self):
        import json
        import os
        from tests import test_format_elements as fx
        folder = Path(tempfile.mkdtemp(prefix='docfit-profile-load-'))
        example = folder / 'example.hwpx'
        with zipfile.ZipFile(example, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', fx.HEADER)
            z.writestr('Contents/section0.xml', fx.SECTION)
        profile = self.ns['기본_서식프로파일']()
        profile.update(name='예전 서식', profile_version=4,
                       element_analysis=fe.analyze_format_elements(example, fx.classify))
        profile['element_analysis'].pop('samples')
        with patch.dict(os.environ, {'APPDATA': str(folder)}):
            formats = self.ns['서식프로파일_폴더']()
            formats.mkdir(parents=True, exist_ok=True)
            (formats / 'old.json').write_text(json.dumps(profile, ensure_ascii=False), encoding='utf-8')
            loaded = self.ns['서식프로파일_목록']()['old']
        self.assertIn('ㅇ', loaded['format']['계층_추가서식'])       # 새 복사 범위로 다시 만든 적용 값
        self.assertIn('내어쓰기_규칙', loaded['format'])

    def test_page_number_shape_is_copied_only_where_page_numbers_exist(self):
        ns = self.ns
        fn = ns['쪽번호_hwpx_처리']
        folder = Path(tempfile.mkdtemp(prefix='docfit-pagenum-'))
        header, _ = ns['제목_원본자료']()
        number = '<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>' \
                 '<hp:pageNum pos="TOP_RIGHT" formatType="ROMAN_SMALL" sideChar=""/></hp:ctrl></hp:run></hp:p>'
        sources = {}
        for name, body in (('with', number), ('without', '')):
            path = folder / f'{name}.hwpx'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('mimetype', 'application/hwp+zip')
                z.writestr('Contents/header.xml', ns['ET'].tostring(header, encoding='utf-8', xml_declaration=True))
                z.writestr('Contents/section0.xml', f'<hs:sec {HS} {HP}>{SEC}{body}</hs:sec>')
            sources[name] = path
        shape = {'pos': 'BOTTOM_CENTER', 'formatType': 'DIGIT', 'sideChar': '-'}
        settings = dict(ns['표준서식_설정'], 쪽번호=shape)
        with patch.dict(fn.__globals__, {'표준서식_설정': settings, '로그': Mock()}):
            found = fn(sources['with'])
            self.assertEqual(found, {'Contents/section0.xml': [0]})
            target = folder / 'out.hwpx'
            self.assertEqual(fn(sources['with'], target, found), 1)
            self.assertEqual(fn(sources['without']), {'Contents/section0.xml': []})   # 없으면 넣지 않음
        with zipfile.ZipFile(target) as z:
            xml = z.read('Contents/section0.xml').decode('utf-8')
        self.assertIn('pos="BOTTOM_CENTER"', xml)
        self.assertIn('formatType="DIGIT"', xml)

    def test_paper_difference_is_reported_not_changed(self):
        fn = self.ns['용지_다르면_알림']
        page = Mock(PaperWidth=84188, PaperHeight=59528, Landscape=1)
        doc = Mock()
        doc.HParameterSet.HSecDef.PageDef = page
        log = Mock()
        settings = dict(self.ns['표준서식_설정'], 용지_mm={"width": 210.0, "height": 297.0, "landscape": False})
        with patch.dict(fn.__globals__, {'hwp': doc, '로그': log, '표준서식_설정': settings}):
            self.assertTrue(fn())
            self.assertIn('용지 크기·방향은 바꾸지 않았습니다', log.call_args.args[0])
            page.PaperWidth, page.PaperHeight, page.Landscape = 59528, 84188, 0
            self.assertFalse(fn())


class FormatCopyFidelityTest(unittest.TestCase):
    """2026-10-04 범정부오피스 서식 27종 왕복 시험(예시 서식을 예시 자신과 다른 보고서에 입혀 요소 비교)에서 나온 결함."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_parenthesis_shrink_follows_each_level(self):
        # 예시가 ○만 괄호를 2pt 줄이고 □·*는 그대로 쓰면 그대로 따른다(예전에는 모든 계층을 2pt 줄였다).
        profile = {"format": {"기호_규칙": [], "복사_문단모양": {}, "여백_mm": {}}, "options": {},
                   "element_analysis": {"paragraph_groups": [
                       {"marker": m, "role": "", "count": 2, "elements": {"paren_delta": {"value": d}}}
                       for m, d in (("□", 0), ("○", 200), ("*", 0))]}}
        fe.apply_to_profile(profile)
        shrink = profile["format"]["괄호_축소_기호별"]
        self.assertEqual((shrink["□"], shrink["○"], shrink["*"], shrink["ㅇ"]), (0.0, 2.0, 0.0, 2.0))
        fn = self.ns['괄호_축소량_pt']
        with patch.dict(fn.__globals__, {'표준서식_설정': profile["format"], '괄호_축소_pt': 2}):
            self.assertEqual(fn('□ 사업개요 (헤드라인M, 16p)'), 0.0)
            self.assertEqual(fn('ㅇ 본문 (참고)'), 2.0)            # ○와 같은 계층
            self.assertEqual(fn('- 내용 (참고)'), 2.0)             # 예시에 없는 계층은 대표 줄임 폭
        with patch.dict(fn.__globals__, {'표준서식_설정': {}, '괄호_축소_pt': 2}):
            self.assertEqual(fn('□ 기본 서식'), 2.0)

    def test_marker_only_bold_keeps_symbol_bold_gate_open(self):
        # 예시가 □ 기호만 굵게 쓰면(문단은 보통) '□ 굵게' 허용을 닫지 않는다(닫으면 기호 굵게까지 빠졌다).
        elements = {"font": {"value": "고딕"}, "size": {"value": 1600}, "bold": {"value": False},
                    "marker_bold": {"value": True}}
        profile = {"format": {"기호_규칙": [("□", 0, "고딕", 16, False, False)], "복사_문단모양": {}, "여백_mm": {}},
                   "options": {}, "element_analysis": {"paragraph_groups": [
                       {"marker": "□", "role": "소제목", "count": 3, "elements": elements}]}}
        fe.apply_to_profile(profile)
        self.assertEqual(profile["format"]["기호_규칙"][0][4:], (False, True))   # 문단 보통, 기호만 굵게
        self.assertTrue(profile["options"]["std_symbol_box_bold"])

    def test_precise_copy_skips_form_tables_handled_by_form_stages(self):
        # 제목·중제목·붙임 표와(예시 상자가 있으면) 한 칸 상자는 서식 표 단계가 문단별로 입히므로 정밀 복제하지 않는다.
        fn = self.ns['_정밀표_서식표인가']
        for kind, has_box, expected in (('title1', False, True), ('midtitle1', False, True), ('attach2', False, True),
                                        ('box', True, True), ('box', False, False), (None, True, False)):
            with patch.dict(fn.__globals__, {'서식표_종류판별': lambda table, k=kind: k,
                                             '활성_서식표_프로필': {'box': object()} if has_box else None}):
                self.assertEqual(fn(object()), expected, (kind, has_box))

    def test_font_type_mismatch_retries_other_type_then_without_latin(self):
        # 같은 이름의 글꼴이 TTF·HFT로 둘 다 든 문서에서 고른 형식이 이 PC와 맞지 않으면 글자 모양 실행이 실패한다.
        # 다른 형식으로 다시 해 보고(되면 기억), 그래도 안 되면 영문 글꼴만 빼고 장평·자간·글자색 등을 입힌다.
        ns = self.ns
        fn = ns['계층_추가서식_적용']
        doc = Mock()
        doc.FontType.side_effect = lambda kind: {"TTF": 1, "HFT": 2}[kind]
        action = Mock()
        doc.CreateAction.return_value = action
        sets = []
        action.CreateSet.side_effect = lambda: sets.append(Mock()) or sets[-1]
        action.Execute.side_effect = [False, True]          # TTF 실패 → HFT 성공
        settings = {"계층_추가서식": {"ㅇ": {"font_latin": "HCI Poppy", "ratio": 95}}}
        table = {"HCI Poppy": "TTF"}
        with patch.dict(fn.__globals__, {'hwp': doc, 'hwp_run': Mock(), '표준서식_설정': settings, '_글꼴형식': table,
                                         '표준서식_장평_사용': True, '로그': Mock()}):
            fn("ㅇ")
            self.assertEqual(table["HCI Poppy"], "HFT")
            sets[0].SetItem.assert_any_call("FontTypeLatin", 2)
            # 두 형식 모두 안 되면 영문 글꼴 없이 나머지를 입힌다.
            sets.clear()
            action.Execute.side_effect = [False, False, True]
            fn("ㅇ")
            last = sets[-1]
            keys = [c.args[0] for c in last.SetItem.call_args_list]
            self.assertNotIn("FaceNameLatin", keys)
            self.assertIn("RatioHangul", keys)

    def test_page_margins_round_trip_exactly(self):
        # 예시 여백 4252(15.0mm 저장)가 한/글 MiliToHwpUnit(소수 버림)으로 4251이 되던 문제: 반올림해 그대로 넣는다.
        fn = self.ns['페이지_여백_설정']
        doc = Mock()
        page = doc.HParameterSet.HSecDef.PageDef
        margins = {k: round(v / (7200 / 25.4), 3) for k, v in
                   (("left", 4252), ("right", 5385), ("top", 1700), ("bottom", 2267), ("header", 2835), ("footer", 2835))}
        with patch.dict(fn.__globals__, {'hwp': doc, '로그': Mock()}):
            fn(margins)
        self.assertEqual((page.LeftMargin, page.RightMargin, page.TopMargin, page.BottomMargin,
                          page.HeaderLen, page.FooterLen), (4252, 5385, 1700, 2267, 2835, 2835))

    def test_example_font_types_are_registered(self):
        # 예시의 HFT 글꼴(한양중고딕·HCI Poppy 등)을 TTF로 지정하면 한/글이 무시하므로 형식을 남기고 등록한다.
        ns = self.ns
        header = ns['safe_xml_fromstring'](
            '<hh:head xmlns:hh="urn:h"><hh:fontface lang="HANGUL"><hh:font id="0" face="한양중고딕" type="HFT"/>'
            '<hh:font id="1" face="휴먼명조" type="TTF"/></hh:fontface><hh:fontface lang="LATIN">'
            '<hh:font id="0" face="HCI Poppy" type="HFT"/><hh:font id="1" face="휴먼명조" type="HFT"/>'
            '</hh:fontface></hh:head>')
        found = ns['글꼴형식_모으기'](header)
        self.assertEqual(found, {"한양중고딕": "HFT", "휴먼명조": "TTF", "HCI Poppy": "HFT"})   # 같은 이름은 TTF 우선
        table = {"휴먼명조": "TTF"}
        with patch.dict(ns['글꼴형식_등록'].__globals__, {'_글꼴형식': table}):
            ns['글꼴형식_등록']({"한양중고딕": "HFT", "휴먼명조": "HFT"})
        self.assertEqual(table, {"휴먼명조": "TTF", "한양중고딕": "HFT"})

    def test_plain_sentences_take_example_body_format_only_for_body_sentences(self):
        # 기호 없는 문단은 본문 문장(빈칸 뺀 12자 이상·18pt 미만·가운데/오른쪽 정렬 아님·붙임 줄 아님)만 '일반 문장' 표본이자 적용 대상이다.
        self.assertTrue(fe.is_body_sentence("기호 없이 작성한 본문 문장이 이어집니다", 1500, "JUSTIFY"))
        self.assertFalse(fe.is_body_sentence("문서 제목입니다만 가운데에 놓인 줄입니다", 1500, "CENTER"))
        self.assertFalse(fe.is_body_sentence("2026. 10. 4.(일)", 1500, "RIGHT"))
        self.assertFalse(fe.is_body_sentence("아주 큰 제목 글자로 쓴 열다섯 글자 넘는 줄", 2400, "JUSTIFY"))
        self.assertFalse(fe.is_body_sentence("붙임  ○○○○ 1부.  끝.", 1300, "JUSTIFY"))   # 붙임 줄은 붙임 규칙
        self.assertFalse(fe.is_body_sentence("가 나 다 라 마 바 사 아 자 차 카", 1500, "JUSTIFY"))  # 빈칸 빼고 11자
        elements = {k: {"value": v} for k, v in (("font", "명조"), ("size", 1300), ("bold", False), ("prev", 1000),
                                                 ("line_type", "PERCENT"), ("line", 150), ("align", "LEFT"),
                                                 ("font_latin", "HCI Poppy"))}
        profile = {"format": {"기호_규칙": [], "복사_문단모양": {}, "여백_mm": {}}, "options": {},
                   "element_analysis": {"paragraph_groups": [
                       {"marker": "", "role": "일반 문장", "count": 4, "elements": elements}]}}
        fe.apply_to_profile(profile)
        fmt = profile["format"]
        self.assertEqual(fmt["본문_문단"], {"font": "명조", "size_pt": 13.0, "bold": False})
        self.assertEqual(fmt["복사_문단모양"][fe.PLAIN_KEY],
                         {"PrevSpacing": 1000, "LineSpacingType": 0, "LineSpacing": 150})
        self.assertEqual(fmt["계층_추가서식"][fe.PLAIN_KEY], {"font_latin": "HCI Poppy", "align": "LEFT"})
        # 정리할 문서에서도 지금 문단이 본문 문장인지 한/글에서 정렬·크기를 읽어 판정한다.
        fn = self.ns['본문형_일반문장인가']
        doc = Mock()
        doc.ParaShape.Item.return_value = 3          # 가운데 정렬
        doc.CharShape.Item.return_value = 1500
        with patch.dict(fn.__globals__, {'hwp': doc, 'hwp_run': Mock()}):
            self.assertFalse(fn("가운데에 놓인 열다섯 글자가 넘는 제목 줄입니다"))
            doc.ParaShape.Item.return_value = 0      # 양쪽 정렬
            self.assertTrue(fn("양쪽 정렬로 쓴 열다섯 글자가 넘는 본문 문장입니다"))


if __name__ == '__main__':
    unittest.main()
