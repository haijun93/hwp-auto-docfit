"""'붙임 …'~'끝.' 묶음의 글꼴·크기를 문두기호 ㅇ와 같게 하는 규칙을 확인한다."""
import copy
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from docfit_core.attachment_block import (
    find_blocks, find_trailing_numbered_blocks, is_numbered_header, is_numbered_item, numbered_item_offset,
)
from docfit_core.document_rules import normalize_attachment_list_header

HP = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
HS = 'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'


class BlockRuleTest(unittest.TestCase):
    def test_single_line_block(self):
        self.assertEqual(find_blocks(['가', '붙임  지구 침공 세부 시행계획 1부.  끝.', '나']), [(1, 1)])

    def test_multi_line_block_ends_at_end_marker(self):
        texts = ['ㅇ 본문', '붙임: 1. 지구 침공 세부 시행계획 1부.', '2. 지자 개발 현황 1부.', '끝.', '나머지']
        self.assertEqual(find_blocks(texts), [(1, 3)])
        self.assertEqual(find_blocks(['붙임 : 가.', '나.', '다.', '끝. ']), [(0, 3)])

    def test_numbered_attachment_list_with_indent_and_trailing_space(self):
        """붙임 1. 고구마 1부. / 2. 만두 1부. (끝 공백) / 3. 자장면 1부. 끝."은 한 묶음이다."""
        texts = ['ㅇ 본문', '붙임 1. 고구마 1부.', '       2. 만두 1부. ', '       3. 자장면 1부. 끝.', '뒤 문장']
        self.assertEqual(find_blocks(texts), [(1, 3)])

    def test_invalid_blocks_are_ignored(self):
        self.assertEqual(find_blocks(['붙임: 가.', '마침표 없는 문장', '끝.']), [])       # 중간 문장이 마침표로 끝나지 않음
        self.assertEqual(find_blocks(['붙임: 가.', '', '끝.']), [])                      # 빈 줄
        self.assertEqual(find_blocks(['붙임: 가.', None, '끝.']), [])                    # 표·그림 문단
        self.assertEqual(find_blocks(['붙임: 가.', '나.']), [])                          # 끝. 없음
        self.assertEqual(find_blocks(['붙임: 가']), [])                                  # 붙임 줄이 마침표로 끝나지 않음
        self.assertEqual(find_blocks(['참고 붙임 자료 끝.']), [])                         # 첫 어절이 붙임이 아님
        self.assertEqual(find_blocks(['붙임: 가.'] + ['나.'] * 40 + ['끝.']), [])         # 너무 긴 목록

    def test_several_blocks_and_nested_start(self):
        texts = ['붙임: 가.', '끝.', '중간', '붙임 나. 끝.']
        self.assertEqual(find_blocks(texts), [(0, 1), (3, 3)])

    def test_attachment_number_header_and_items(self):
        header = '붙임 : 1. 지구 침공 세부 시행계획 1부.'
        self.assertTrue(is_numbered_header(header))
        self.assertTrue(is_numbered_item(header))
        self.assertEqual(numbered_item_offset(header), header.index('1.'))
        self.assertTrue(is_numbered_item('   2. 스케줄표 1부.'))
        self.assertEqual(numbered_item_offset('   2. 스케줄표 1부.'), 3)
        self.assertFalse(is_numbered_item('별첨 2. 스케줄표'))

    def test_attachment_list_header_uses_official_two_spaces(self):
        self.assertEqual(normalize_attachment_list_header('붙임     1. 계획서 1부.'), '붙임  1. 계획서 1부.')
        # 쌍점을 쓴 꼴은 사용자 기재 스타일 그대로 둔다.
        for text in ('붙임 : 1. 계획서 1부.', '붙임: 1. 계획서 1부.', '붙임:1. 계획서 1부.'):
            self.assertEqual(normalize_attachment_list_header(text), text)

    def test_numbered_indent_only_targets_a_complete_attachment_list_at_document_end(self):
        items = ['붙임: 1. 계획서 1부.', '   2. 스케줄표 1부.', '끝.']
        self.assertEqual(find_trailing_numbered_blocks(items), [(0, 1)])
        official_example = ['붙임  1. 서식승인 목록 1부.', '    2. 승인서식 2부.  끝.']
        self.assertEqual(find_trailing_numbered_blocks(official_example), [(0, 1)])
        self.assertEqual(find_trailing_numbered_blocks(items + ['본문']), [])
        self.assertEqual(find_trailing_numbered_blocks(['붙임: 자료 1부.', '끝.']), [])
        self.assertEqual(find_trailing_numbered_blocks(['붙임: 1. 계획서 1부.', '비번호 문장.', '끝.']), [])


class DocumentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.parse = staticmethod(cls.ns['safe_xml_fromstring'])
        cls.name = staticmethod(cls.ns['제목_xml이름'])

    def _doc(self, body, marker_face='휴먼명조'):
        """글자모양 0 = 바탕 10pt, 1 = ㅇ 문장(marker_face 15pt)."""
        ns = self.ns
        header, _ = ns['제목_원본자료']()
        faces = ns['_한글_글꼴표'](header)
        chars = next(x for x in header.iter() if self.name(x) == 'charProperties')
        base = copy.deepcopy(next(iter(chars))); base.set('id', '0'); base.set('height', '1000')
        chars.insert(0, base)
        marker = copy.deepcopy(base); marker.set('id', '1'); marker.set('height', '1500')
        ref = next(x for x in marker if self.name(x) == 'fontRef')
        for lang in list(ref.attrib):
            by_name = {name: fid for fid, name in faces[lang.lower()].items()}
            ref.set(lang, by_name.get(marker_face, next(iter(by_name.values()))))
        chars.insert(1, marker)
        section = f'<hs:sec {HS} {HP}>{body}</hs:sec>'.encode('utf-8')
        out = Path(tempfile.mkdtemp(prefix='docfit-att-')) / 'in.hwpx'
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr('mimetype', 'application/hwp+zip')
            z.writestr('Contents/header.xml', ns['ET'].tostring(header, encoding='utf-8', xml_declaration=True))
            z.writestr('Contents/section0.xml', section)
        return out

    @staticmethod
    def _p(text, char='0'):
        return (f'<hp:p id="1" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="{char}">'
                f'<hp:t>{text}</hp:t></hp:run></hp:p>')

    BODY = (_p.__func__('ㅇ 본문 문장', '1') + _p.__func__('일반 문장')
            + _p.__func__('붙임: 1. 지구 침공 세부 시행계획 1부.') + _p.__func__('2. 지자 개발 현황 1부.')
            + _p.__func__('끝.') + _p.__func__('뒤 문장'))

    def _convert(self, body=None, symbol_rule=True, marker_face='휴먼명조'):
        ns = self.ns
        fn = ns['붙임글꼴_hwpx_처리']
        source = self._doc(body or self.BODY, marker_face)
        with patch.dict(fn.__globals__, {'표준서식_기호_사용': symbol_rule}):
            found = fn(source)
            target = source.with_name('out.hwpx')
            count = fn(source, target, found)
        with zipfile.ZipFile(target) as z:
            header = self.parse(z.read('Contents/header.xml'))
            section = self.parse(z.read('Contents/section0.xml'))
        return source, target, found, count, header, section

    def _look(self, header, section, index):
        ns = self.ns
        faces = ns['_한글_글꼴표'](header)
        chars = {c.get('id'): c for c in header.iter() if self.name(c) == 'charPr'}
        p = [x for x in section if self.name(x) == 'p'][index]
        out = []
        for run in (r for r in p if self.name(r) == 'run'):
            names, size = ns['_글자모양_글꼴크기'](chars[run.get('charPrIDRef')], faces)
            out.append((names, size))
        return out

    def test_block_takes_standard_marker_font_and_size(self):
        source, _, found, count, header, section = self._convert(symbol_rule=True)
        self.assertEqual(found, {'Contents/section0.xml': [(2, 4)]})
        self.assertEqual(count, 3)
        for index in (2, 3, 4):     # 붙임~끝. 문장 전부: 표준서식 ㅇ 규칙(한컴돋움 15pt)
            self.assertEqual(self._look(header, section, index), [({'한컴돋움'}, 15.0)], index)
        # 묶음 밖 문장은 그대로다.
        self.assertIn('휴먼명조', self._look(header, section, 0)[0][0])
        self.assertEqual(self._look(header, section, 0)[0][1], 15.0)
        self.assertEqual(self._look(header, section, 1)[0][1], 10.0)
        self.assertEqual(self._look(header, section, 5)[0][1], 10.0)
        texts = [self.ns['제목_문자열'](p) for p in section if self.name(p) == 'p']
        self.assertEqual(texts[2:5], ['붙임: 1. 지구 침공 세부 시행계획 1부.', '2. 지자 개발 현황 1부.', '끝.'])
        # 헤더 개수 표기가 실제와 맞고, 없던 글꼴은 모든 언어 그룹에 추가됐다.
        self.assertEqual(int(next(x for x in header.iter() if self.name(x) == 'charProperties').get('itemCnt')),
                         len([x for x in header.iter() if self.name(x) == 'charPr']))
        for ff in (x for x in header.iter() if self.name(x) == 'fontface'):
            self.assertEqual(int(ff.get('fontCnt')), len(ff))
            self.assertIn('한컴돋움', {f.get('face') for f in ff})

    def test_without_symbol_rule_uses_the_documents_marker_sentences(self):
        _, _, found, _, header, section = self._convert(symbol_rule=False, marker_face='휴먼명조')
        self.assertEqual(found, {'Contents/section0.xml': [(2, 4)]})
        for index in (2, 3, 4):
            self.assertEqual(self._look(header, section, index), [({'휴먼명조'}, 15.0)], index)

    def test_second_run_finds_nothing_and_already_matching_block_is_skipped(self):
        ns = self.ns
        _, target, _, _, _, _ = self._convert()
        fn = ns['붙임글꼴_hwpx_처리']
        with patch.dict(fn.__globals__, {'표준서식_기호_사용': True}):
            self.assertEqual(fn(target), {'Contents/section0.xml': []})

    def test_no_marker_sentences_and_no_symbol_rule_means_no_change(self):
        ns = self.ns
        source = self._doc(self._p('붙임: 가.') + self._p('끝.'))
        fn = ns['붙임글꼴_hwpx_처리']
        with patch.dict(fn.__globals__, {'표준서식_기호_사용': False}):
            self.assertEqual(fn(source), {'Contents/section0.xml': []})

    def test_combined_stage_reopens_once_for_both_char_level_processors(self):
        ns = self.ns
        stage = ns['글자서식_선행적용']
        opened = Mock(return_value=True)
        body = self.BODY + self._p('ㅇ 지자* 선행', '1')
        source = self._doc(body)
        env = {'한글_문서_열기': opened, 'hwp': object(), '로그': Mock(), '중단_요청됨': lambda: False,
               '진단로그': Mock(), '표준서식_기호_사용': True}
        with patch.dict(stage.__globals__, env):
            notice = {}
            self.assertTrue(stage(str(source), True, True, False, notice))
        self.assertTrue(notice['changed'])
        self.assertEqual(opened.call_count, 1)
        # 위첨자만 켠 경우에도 동작하고, 둘 다 끄면 아무것도 하지 않는다.
        opened.reset_mock()
        with patch.dict(stage.__globals__, dict(env, 한글_문서_열기=opened)):
            self.assertTrue(stage(str(source), False, False, False, {}))
        opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()
