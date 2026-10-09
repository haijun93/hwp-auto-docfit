"""알파 XML 서식의 원본·강조·컨트롤 보존과 COM 선택 경로 회귀 검사."""

import ast
import copy
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import Mock
from zipfile import ZipFile, ZIP_DEFLATED

from defusedxml import ElementTree as ET

from docfit_core.batch_format import apply_batch, ParagraphStyle, BatchUnsupported, plain_text, tag
from docfit_core.document_rules import ParagraphSpacingTracker
from docfit_core.fidelity.package import PackageSnapshot, UnsupportedPackage
from docfit_core.stage_selection import enabled as stage_enabled
from docfit_core.style_hierarchy import normalize_leading_dot, leading_marker, DOT_MARKERS


LANGS = 'hangul latin hanja japanese other symbol user'.split()
ATTRS = ' '.join(f'{lang}="0"' for lang in LANGS)
RATIOS = ' '.join(f'{lang}="95"' for lang in LANGS)
HEADER = (f'''<hh:head xmlns:hh="urn:head" xmlns:hc="urn:core" xmlns:hp="urn:para"
 xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:extra="urn:extra" mc:Ignorable="extra">
 <hh:fontfaces>{''.join(f'<hh:fontface lang="{lang.upper()}" fontCnt="1"><hh:font id="0" face="원본" type="TTF" isEmbedded="0"/></hh:fontface>' for lang in LANGS)}</hh:fontfaces>
 <hh:refList><hh:charProperties itemCnt="2">
 <hh:charPr id="0" height="1200" textColor="#112233"><hh:fontRef {ATTRS}/><hh:ratio {RATIOS}/><hh:spacing {ATTRS}/><hh:offset {ATTRS}/><hh:underline type="BOTTOM"/></hh:charPr>
 <hh:charPr id="1" height="1000" textColor="#AA0000"><hh:fontRef {ATTRS}/><hh:ratio {RATIOS}/><hh:spacing {ATTRS}/><hh:offset {ATTRS}/><hh:bold/><hh:supscript/></hh:charPr>
 </hh:charProperties><hh:paraProperties itemCnt="1"><hh:paraPr id="0">
 <hp:switch><hp:case required-namespace="urn:core"><hh:margin><hc:left value="321" unit="HWPUNIT"/><hc:intent value="-400" unit="HWPUNIT"/><hc:prev value="250" unit="HWPUNIT"/></hh:margin><hh:lineSpacing type="FIXED" value="2000"/></hp:case>
 <hp:default><hh:margin><hc:left value="642" unit="HWPUNIT"/><hc:intent value="-800" unit="HWPUNIT"/><hc:prev value="500" unit="HWPUNIT"/></hh:margin><hh:lineSpacing type="FIXED" value="4000"/></hp:default></hp:switch>
 </hh:paraPr></hh:paraProperties></hh:refList></hh:head>''').encode()


def paragraph(text, shape='0', extra=''):
    return f'<hp:p paraPrIDRef="0"><hp:run charPrIDRef="{shape}"><hp:t>{text}</hp:t></hp:run>{extra}<hp:linesegarray><hp:lineseg textpos="0"/></hp:linesegarray></hp:p>'


def section(contents):
    return ('<hs:sec xmlns:hs="urn:section" xmlns:hp="urn:para">' + contents + '</hs:sec>').encode()


def fixture(path, contents, header=HEADER, extra_section=None):
    with ZipFile(path, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('mimetype', b'application/hwp+zip')
        archive.writestr('Contents/header.xml', header)
        archive.writestr('Contents/section0.xml', section(contents))
        if extra_section is not None:
            archive.writestr('Contents/section1.xml', section(extra_section))
        archive.writestr('BinData/image.bin', b'unchanged-image')
        archive.writestr('META-INF/container.xml', b'<container/>')


def roots(path):
    with ZipFile(path) as archive:
        return (ET.fromstring(archive.read('Contents/header.xml')),
                ET.fromstring(archive.read('Contents/section0.xml')))


def shapes(header, name):
    return {x.get('id'): x for x in header.iter() if tag(x) == name}


def basic_plan(text, element):
    if text is None or not text.lstrip().startswith('□'):
        return None
    return ParagraphStyle(text=text.lstrip(), font='서식글꼴', size_pt=17, ratio=100,
                          line_percent=160, prev_pt=15, bold_spans=((0, 1),))


class BatchFormatTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'source.hwpx'
        self.target = Path(self.folder.name) / 'target.hwpx'

    def test_applies_styles_preserves_source_emphasis_and_unrelated_zip_records(self):
        fixture(self.source, paragraph('   □ 보고서') + paragraph('일반 본문'))
        before = self.source.read_bytes()
        result = apply_batch(self.source, self.target, basic_plan)
        self.assertEqual((result.applied, result.fallback), (1, 1))
        self.assertEqual(self.source.read_bytes(), before)
        header, root = roots(self.target)
        self.assertEqual(plain_text(root[0]), '□ 보고서')
        self.assertEqual(ET.tostring(root[1]), ET.tostring(ET.fromstring(section(paragraph('일반 본문')))[0]))
        character = shapes(header, 'charPr')
        original = shapes(ET.fromstring(HEADER), 'charPr')['0']
        self.assertEqual(ET.tostring(character['0']), ET.tostring(original))
        for run in root[0]:
            if tag(run) != 'run':
                continue
            shape = character[run.get('charPrIDRef')]
            self.assertEqual(shape.get('height'), '1700')
            self.assertEqual(shape.get('textColor'), '#112233')
            self.assertTrue(any(tag(x) == 'underline' for x in shape))
            self.assertEqual(any(tag(x) == 'bold' for x in shape), run[0].text == '□')
        self.assertFalse(any(tag(x) == 'linesegarray' for x in root[0]))
        old, new = PackageSnapshot.load(self.source), PackageSnapshot.load(self.target)
        for name in ('mimetype', 'BinData/image.bin', 'META-INF/container.xml'):
            self.assertEqual(old.entries[name].local, new.entries[name].local)

    def test_paragraph_units_and_original_indentation_are_preserved(self):
        fixture(self.source, paragraph('□ 내용'))
        apply_batch(self.source, self.target, basic_plan)
        header, root = roots(self.target)
        shape = shapes(header, 'paraPr')[root[0].get('paraPrIDRef')]
        self.assertEqual([x.get('value') for x in shape.iter() if tag(x) == 'prev'], ['1500', '3000'])
        self.assertEqual([x.get('value') for x in shape.iter() if tag(x) == 'intent'], ['-400', '-800'])
        self.assertEqual([x.get('value') for x in shape.iter() if tag(x) == 'left'], ['321', '642'])
        self.assertEqual([(x.get('type'), x.get('value')) for x in shape.iter() if tag(x) == 'lineSpacing'], [('PERCENT', '160')] * 2)

    def test_label_across_runs_preserves_superscript_and_existing_bold(self):
        body = '<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>□ (목</hp:t></hp:run><hp:run charPrIDRef="1"><hp:t>적) 내용*</hp:t></hp:run></hp:p>'
        fixture(self.source, body)
        def plan(text, element):
            return ParagraphStyle(text=text, size_pt=17, bold_spans=((2, 6),))
        apply_batch(self.source, self.target, plan)
        header, root = roots(self.target)
        cs = shapes(header, 'charPr')
        self.assertEqual(plain_text(root[0]), '□ (목적) 내용*')
        for run in root[0]:
            shape = cs[run.get('charPrIDRef')]
            if '(' in run[0].text or ')' in run[0].text:
                self.assertTrue(any(tag(x) == 'bold' for x in shape))
            if '내용*' in run[0].text:
                self.assertTrue(any(tag(x) == 'bold' for x in shape))
                self.assertTrue(any(tag(x) == 'supscript' for x in shape))
                self.assertEqual(shape.get('textColor'), '#AA0000')

    def test_shared_style_ids_are_cached_and_second_application_adds_no_styles(self):
        fixture(self.source, ''.join(paragraph(f'□ 항목 {i}') for i in range(100)))
        result = apply_batch(self.source, self.target, basic_plan)
        self.assertEqual(result.applied, 100)
        self.assertEqual(result.char_styles, 2)
        self.assertEqual(result.paragraph_styles, 1)
        second = Path(self.folder.name) / 'again.hwpx'
        result = apply_batch(self.target, second, basic_plan)
        self.assertEqual((result.char_styles, result.paragraph_styles), (0, 0))
        self.assertEqual(second.read_bytes(), self.target.read_bytes())

    def test_duplicate_text_in_body_or_control_stays_on_com_path(self):
        complex_paragraph = '<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>□ 중복</hp:t><hp:ctrl/></hp:run></hp:p>'
        fixture(self.source, paragraph('□ 중복') + complex_paragraph + paragraph('□ 중복'))
        result = apply_batch(self.source, self.target, basic_plan)
        self.assertEqual(result.applied, 0)
        self.assertEqual(result.formatted_texts, set())
        self.assertEqual(self.target.read_bytes(), self.source.read_bytes())

    def test_nested_table_text_also_blocks_ambiguous_body_match(self):
        table = '<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:tbl><hp:tr><hp:tc><hp:subList>' + paragraph('□ 중복') + '</hp:subList></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>'
        fixture(self.source, paragraph('□ 중복') + table + paragraph('□ 독립'))
        result = apply_batch(self.source, self.target, basic_plan)
        self.assertEqual(result.formatted_texts, {'□ 독립'})
        _, root = roots(self.target)
        self.assertEqual(ET.tostring(root[1]), ET.tostring(ET.fromstring(section(table))[0]))

    def test_normalization_collisions_are_not_skipped_by_com(self):
        fixture(self.source, paragraph('□ 같은 내용') + paragraph('  □ 같은 내용'))
        result = apply_batch(self.source, self.target, basic_plan)
        self.assertEqual(result.applied, 2)
        self.assertEqual(result.formatted_texts, set())

    def test_disabled_font_size_ratio_and_line_options_keep_original_values(self):
        fixture(self.source, paragraph('□ 항목', shape='1'))
        apply_batch(self.source, self.target, lambda text, p: ParagraphStyle(text=text))
        header, root = roots(self.target)
        self.assertEqual(root[0][0].get('charPrIDRef'), '1')
        self.assertEqual(root[0].get('paraPrIDRef'), '0')
        self.assertEqual(ET.tostring(header), ET.tostring(ET.fromstring(HEADER)))

    def test_missing_shape_is_not_silently_replaced_with_another_shape(self):
        fixture(self.source, paragraph('□ 항목', shape='999'))
        result = apply_batch(self.source, self.target, basic_plan)
        self.assertEqual(result.applied, 0)
        self.assertEqual(self.target.read_bytes(), self.source.read_bytes())

    def test_hft_font_already_in_document_is_reused(self):
        fixture(self.source, paragraph('□ 항목'), header=HEADER.replace(b'face="\xec\x9b\x90\xeb\xb3\xb8" type="TTF"', 'face="서식글꼴" type="HFT"'.encode()))
        apply_batch(self.source, self.target, basic_plan)
        header, _ = roots(self.target)
        self.assertTrue(all(x.get('fontCnt') == '1' for x in header.iter() if tag(x) == 'fontface'))
        self.assertTrue(all(x.get('type') == 'HFT' for x in header.iter() if tag(x) == 'font'))

    def test_ignorable_namespace_declarations_survive_serialization(self):
        fixture(self.source, paragraph('□ 항목'))
        apply_batch(self.source, self.target, basic_plan)
        with ZipFile(self.target) as archive:
            header = archive.read('Contents/header.xml')
        self.assertIn(b'xmlns:extra="urn:extra"', header)
        self.assertIn(b'mc:Ignorable="extra"', header)

    def test_all_sections_are_processed_and_duplicate_ids_do_not_alias(self):
        fixture(self.source, paragraph('□ 첫 구역'), extra_section=paragraph('□ 둘째 구역'))
        result = apply_batch(self.source, self.target, basic_plan)
        self.assertEqual(result.applied, 2)
        self.assertEqual(result.formatted_texts, {'□ 첫 구역', '□ 둘째 구역'})

    def test_analysis_does_not_create_files_or_change_input(self):
        fixture(self.source, paragraph('□ 항목'))
        before = self.source.read_bytes()
        result = apply_batch(self.source, None, basic_plan)
        self.assertEqual(result.applied, 1)
        self.assertFalse(self.target.exists())
        self.assertEqual(self.source.read_bytes(), before)

    def test_refuses_overwriting_original_or_body_content(self):
        fixture(self.source, paragraph('□ 항목'))
        with self.assertRaisesRegex(ValueError, '출력 경로'):
            apply_batch(self.source, self.source, basic_plan)
        with self.assertRaises(ValueError):
            apply_batch(self.source, self.target, lambda t, p: ParagraphStyle(text='□ 다른'))
        self.assertFalse(self.target.exists())

    def test_rejects_xml_entities_without_creating_output(self):
        bad = b'<!DOCTYPE h [<!ENTITY x SYSTEM "file:///etc/passwd">]><h>&x;</h>'
        fixture(self.source, paragraph('□ 항목'), header=bad)
        with self.assertRaises(Exception) as error:
            apply_batch(self.source, self.target, basic_plan)
        self.assertIn(type(error.exception).__name__, ('EntitiesForbidden', 'ExternalReferenceForbidden'))
        self.assertFalse(self.target.exists())


def app_functions(*names):
    """Windows 앱을 임포트하지 않고 실제 함수 본문을 검사한다(COM 자체 검증 아님)."""
    path = Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    nodes = [x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name in names]
    namespace = {'re': re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


class BatchComSelectionTests(unittest.TestCase):
    def test_body_passes_skip_measured_single_lines_and_process_every_multiline_boundary(self):
        class Cursor:
            def __init__(self):
                self.pos = (0, 0, 0)
                self.starts = ([0], [0, 5], [0])
                self.ends = (9, 9, 7)

            def GetPos(self):
                return self.pos

            def SetPos(self, *pos):
                self.pos = tuple(pos)

            def move(self, action):
                area, para, offset = self.pos
                if action == 'MoveDocBegin':
                    self.pos = (0, 0, 0)
                    return
                if action == 'MoveParaBegin':
                    offset = 0
                elif action == 'MoveParaEnd':
                    offset = self.ends[para]
                elif action == 'MoveLineBegin':
                    offset = max(s for s in self.starts[para] if s <= offset)
                elif action == 'MoveLineEnd':
                    offset = next((s - 1 for s in self.starts[para] if s > offset), self.ends[para])
                elif action == 'MoveNextChar':
                    if offset < self.ends[para]:
                        offset += 1
                    elif para < 2:
                        para, offset = para + 1, 0
                else:
                    raise AssertionError(action)
                self.pos = (area, para, offset)

        for function in ('본문_기존자간조정', '본문_문장부호_처리'):
            ns = app_functions(function, '_알파_한줄문단인가')
            cursor, visited = Cursor(), []
            def correct():
                visited.append(cursor.GetPos())
                return True
            ns.update(hwp=cursor, hwp_run=cursor.move, _알파_일괄서식_문서=True,
                      순회_시작=lambda: cursor.SetPos(0, 0, 0), 중단_요청됨=lambda: False,
                      끝위치추출=lambda: (0, 2, 7), 쪽범위_끝지남=lambda p: False,
                      쪽범위_안인가=lambda p: True, 재검사_대상인가=lambda p: True,
                      표셀_자간_제외인가=lambda: False, 자간자동조정=correct,
                      문장부호_줄병합_시도=correct)
            self.assertTrue(ns[function]())
            self.assertEqual(visited, [(0, 1, 0), (0, 1, 5)])

    def test_app_processor_uses_actual_rules_and_preserves_heading_and_label_options(self):
        ns = app_functions('알파_일괄서식_가능', '_알파_라벨_굵게범위', '표준서식_hwpx_처리',
                           '표준서식_기호규칙_찾기', '문장부호_마커_끝위치',
                           '문두_라벨_굵게_제외_문단인가', '괄호_문두_라벨인가', '_문단_본문글', '_알파_글꼴형식')
        ns['DOT_MARKERS'] = DOT_MARKERS
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py').read_text(encoding='utf-8'))
        wanted = {'표준서식_설정', '표준서식_기호_별칭', '문두라벨_기호설정', '표준서식_기호_굵게'}
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in wanted for t in node.targets):
                exec(compile(ast.Module(body=[node], type_ignores=[]), '<app defaults>', 'exec'), ns)
        ns.update(apply_batch=apply_batch, ParagraphStyle=ParagraphStyle, BatchUnsupported=BatchUnsupported,
                  UnsupportedPackage=UnsupportedPackage, ParagraphSpacingTracker=ParagraphSpacingTracker,
                  stage_enabled=stage_enabled, normalize_leading_dot=normalize_leading_dot,
                  leading_marker=leading_marker, DOT_MARKERS=DOT_MARKERS,
                  알파_HWPX_일괄서식_사용=True, 작업_모드='all', 표준서식_선행_사용=True,
                  쪽범위_요청=None, 선택_세부작업={}, 괄호_라벨_볼드_사용=True,
                  표준서식_기호_사용=True, 표준서식_문단위간격_사용=True,
                  표준서식_장평_사용=True, 표준서식_줄간격_사용=True,
                  표준서식_문단위간격_복귀배율=150, _글꼴형식={}, 항목_패턴=[], 공문서_기호={'□', 'ㅇ', '-', '*', '※'},
                  _문두_무시문자_정규식=re.compile(r'[\s\u200b\u2060\ufeff]+'),
                  괄호_정규식=re.compile(r'\(([^()]+)\)|\[([^\[\]]+)\]'), 제목_xml이름=tag,
                  _표준서식_문단위간격_표=lambda: dict(chapter=15, midtitle=15, box=15, circle=8, dash=4, note=0),
                  _GDI_글꼴인가=lambda name: True, 로그=Mock())
        ns['표준서식_설정']['스타일_속성선택'] = {'-': {'font': False, 'size': False}}
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'in.hwpx', Path(folder) / 'out.hwpx'
            fixture(source, paragraph('일반 제목') + paragraph('   □ 소제목') + paragraph('ㅇ (목적) 내용') + paragraph('- 세부 내용') + paragraph('□ 복귀'))
            selections = ns['표준서식_hwpx_처리'](source)
            self.assertEqual(len(selections['본문']), 4)
            self.assertFalse(target.exists())
            self.assertEqual(ns['표준서식_hwpx_처리'](source, target, selections), 4)
            header, root = roots(target)
            self.assertEqual(plain_text(root[0]), '일반 제목')
            self.assertEqual(root[0][0].get('charPrIDRef'), '0')
            self.assertEqual([plain_text(p) for p in root], ['일반 제목', '□ 소제목', ' ㅇ (목적) 내용', '   - 세부 내용', '□ 복귀'])
            self.assertTrue(ns['_알파_일괄서식_문서'])
            self.assertEqual(ns['_표준서식_XML텍스트'], {'□ 소제목', ' ㅇ (목적) 내용', '   - 세부 내용', '□ 복귀'})
            cs, ps = shapes(header, 'charPr'), shapes(header, 'paraPr')
            self.assertTrue(all(cs[r.get('charPrIDRef')].get('height') == '1200' for r in root[3]))
            returning = ps[root[4].get('paraPrIDRef')]
            self.assertEqual([p.get('value') for p in returning.iter() if tag(p) == 'prev'], ['2200', '4400'])

    def test_actual_single_line_measurement_restores_cursor(self):
        ns = app_functions('_알파_한줄문단인가')
        original = (0, 7, 4)
        hwp = Mock()
        hwp.GetPos.side_effect = [(0, 7, 0), (0, 7, 20), (0, 7, 0)]
        ns.update(hwp=hwp, hwp_run=Mock(), _알파_일괄서식_문서=True)
        self.assertTrue(ns['_알파_한줄문단인가'](original))
        hwp.SetPos.assert_called_once_with(*original)
        self.assertEqual([call.args[0] for call in ns['hwp_run'].call_args_list], ['MoveParaBegin', 'MoveParaEnd', 'MoveLineBegin'])

    def test_multiline_missing_measurement_or_control_is_never_excluded(self):
        for positions in ([(0, 7, 0), (0, 7, 20), (0, 7, 10)], [RuntimeError('실측 실패')]):
            ns = app_functions('_알파_한줄문단인가')
            hwp = Mock()
            hwp.GetPos.side_effect = positions
            ns.update(hwp=hwp, hwp_run=Mock(), _알파_일괄서식_문서=True)
            self.assertFalse(ns['_알파_한줄문단인가']((0, 7, 4)))
            hwp.SetPos.assert_called_once_with(0, 7, 4)
            self.assertFalse(ns['_알파_한줄문단인가']((3, 7, 4)))

    def test_complex_profile_page_range_or_disabled_standard_format_uses_old_path(self):
        ns = app_functions('알파_일괄서식_가능')
        ns.update(알파_HWPX_일괄서식_사용=True, 작업_모드='all', 표준서식_선행_사용=True,
                  쪽범위_요청=None, 선택_세부작업={}, 표준서식_설정={}, stage_enabled=stage_enabled)
        self.assertTrue(ns['알파_일괄서식_가능']())
        for key, value in [('쪽범위_요청', (1, 2)), ('선택_세부작업', {'standard_format': False}),
                           ('표준서식_설정', {'계층_추가서식': {'□': {'italic': True}}}), ('작업_모드', 'unify')]:
            before = ns[key]
            ns[key] = value
            self.assertFalse(ns['알파_일괄서식_가능']())
            ns[key] = before

    def test_xml_formatted_paragraph_does_not_repeat_com_typography(self):
        ns = app_functions('표준서식_문단_처리')
        hwp = Mock()
        hwp.GetPos.return_value = (0, 2, 0)
        change = Mock(side_effect=AssertionError('XML 적용 문단에 COM 서식 중복 적용'))
        ns.update(hwp=hwp, 현재_한칸표인가=lambda: False, 현재문단_텍스트=lambda: '□ 항목',
                  normalize_leading_dot=normalize_leading_dot, 표준서식_기호규칙_찾기=lambda t: ('□', 0, '서식', 17, False, True),
                  표준서식_기호_사용=True, 표준서식_문단위간격_사용=True, 표준서식_설정={},
                  표준서식_문단위간격_찾기=lambda t: 15, _표준서식_XML텍스트={'□ 항목'},
                  _표준서식_XML간격={'□ 항목': 15},
                  표준서식_내어쓰기_사용=True, 최종_내어쓰기_예정=True,
                  문자모양_적용_현재선택=change, 문단_위간격_적용_현재선택=change, hwp_run=change)
        ns['표준서식_문단_처리'](1)
        change.assert_not_called()

    def test_actual_hierarchy_spacing_overrides_ambiguous_xml_prediction(self):
        ns = app_functions('표준서식_문단_처리')
        hwp, character, spacing = Mock(), Mock(), Mock()
        hwp.GetPos.return_value = (0, 2, 0)
        ns.update(hwp=hwp, 현재_한칸표인가=lambda: False, 현재문단_텍스트=lambda: '□ 항목',
                  normalize_leading_dot=normalize_leading_dot,
                  표준서식_기호규칙_찾기=lambda t: ('□', 0, '서식', 17, False, True),
                  표준서식_기호_사용=True, 표준서식_문단위간격_사용=True, 표준서식_설정={},
                  표준서식_문단위간격_찾기=lambda t: 15,
                  _표준서식_XML텍스트={'□ 항목'}, _표준서식_XML간격={'□ 항목': 22},
                  표준서식_내어쓰기_사용=True, 최종_내어쓰기_예정=True,
                  문자모양_적용_현재선택=character, 문단_위간격_적용_현재선택=spacing, hwp_run=Mock())
        ns['표준서식_문단_처리'](1)
        spacing.assert_called_once_with(15)
        character.assert_not_called()


class AlphaFontTypeTests(unittest.TestCase):
    """XML 일괄 서식의 글꼴 형식: 알려진 형식 우선, Windows 글꼴 목록에 있으면 TTF, 없으면 HFT(2026-10-09 검토)."""

    def test_font_type_rule(self):
        ns = app_functions('_알파_글꼴형식')
        ns.update(_글꼴형식={'알려진글꼴': 'HFT'}, _GDI_글꼴인가=lambda name: name == '맑은 고딕')
        f = ns['_알파_글꼴형식']
        self.assertEqual(f('알려진글꼴'), 'HFT')
        self.assertEqual(f('맑은 고딕'), 'TTF')
        self.assertEqual(f('휴먼명조'), 'HFT')   # 한/글 전용 글꼴은 Windows 글꼴 목록에 없다
        self.assertIsNone(f(None))

if __name__ == '__main__':
    unittest.main()
