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


if __name__ == '__main__':
    unittest.main()
