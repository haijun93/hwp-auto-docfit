"""문두기호 문장 사이의 빈 줄만 지우고, 컨트롤 문단·머리 문단 주변 빈 줄은 둔다."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class BlankLineRemovalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def classify(self, text, units=None):
        units = len(text) if units is None else units
        return self.ns['빈문단_분류'](text, (0, 1, 0), (0, 1, units))

    def test_classification(self):
        self.assertEqual(self.classify(''), 'blank')
        self.assertEqual(self.classify('   '), 'blank')
        self.assertEqual(self.classify('', units=8), 'other')   # 표·그림 컨트롤 문단
        self.assertEqual(self.classify('  ㅇ (개요) 본문'), 'marker')
        self.assertEqual(self.classify('2026. 9. 24.(목)'), 'other')
        self.assertEqual(self.classify('일반 문장'), 'other')

    def test_form_template_writing_space_is_kept(self):
        # 기호만 있는 작성란('○', '*')은 template → 그 앞뒤 빈 줄(작성 여백)은 둔다.
        self.assertEqual(self.classify('○'), 'template')
        self.assertEqual(self.classify('  * '), 'template')
        self.assertEqual(self.classify('□ (자유작성)'), 'marker')
        find = self.ns['문두기호문장_사이_빈문단_찾기']
        kinds = ['marker', 'blank', 'template', 'blank', 'marker', 'blank', 'marker']
        self.assertEqual(find(kinds), [5])

    def test_table_only_paragraph_is_not_blank(self):
        # 표 하나만 있는 문단: MoveParaBegin이 표 뒤(pos 8)에 멈춰 시작·끝이 같다.
        fn = self.ns['빈문단_분류']
        self.assertEqual(fn('', (0, 27, 8), (0, 27, 8)), 'other')
        self.assertEqual(fn('', (0, 33, 0), (0, 33, 0)), 'blank')

    def test_only_blanks_between_marker_sentences(self):
        find = self.ns['문두기호문장_사이_빈문단_찾기']
        kinds = ['other', 'blank', 'marker', 'blank', 'blank', 'marker', 'blank',
                 'other', 'blank', 'marker', 'blank']
        # 3·4번: 문두기호 문장 사이, 10번: 문서 끝 빈 문단(빈 쪽 방지)
        self.assertEqual(find(kinds), [3, 4, 10])
        self.assertEqual(find(['marker', 'blank', 'blank']), [1, 2])
        self.assertEqual(find(['blank', 'marker']), [])

    def _delete(self, texts, control_paras=()):
        fn = self.ns['문두기호문장_사이_빈줄_삭제']
        state = {'i': 0}
        selections = []

        class Anchor:
            def __init__(self, para):
                self.para = para
            def Item(self, name):
                return {'List': 0, 'Para': self.para}[name]

        class Ctrl:
            def __init__(self, paras):
                self.paras = list(paras)
                self.CtrlID = 'tbl'
            def GetAnchorPos(self, _):
                return Anchor(self.paras[0])
            @property
            def Next(self):
                return Ctrl(self.paras[1:]) if len(self.paras) > 1 else None

        class Doc:
            HeadCtrl = Ctrl(control_paras) if control_paras else None
            def GetPos(self):
                return (0, state['i'], 0)
            def SetPos(self, *pos):
                pass
            def SelectText(self, *args):
                selections.append(args)
                return True

        def run(cmd):
            if cmd == 'MoveNextParaBegin' and state['i'] < len(texts) - 1:
                state['i'] += 1
            elif cmd == 'MoveDocBegin':
                state['i'] = 0

        with patch.dict(fn.__globals__, {
            'hwp': Doc(), 'hwp_run': run, '현재문단_텍스트': lambda: texts[state['i']],
            '중단_요청됨': lambda: False, '쪽범위_안인가': lambda pos=None: True,
            '로그': Mock(), '진단로그': Mock(), '문두기호문장_빈줄_삭제_사용': True,
        }):
            self.assertTrue(fn())
        return selections

    def test_never_deletes_paragraph_holding_a_table(self):
        # 2번 문단은 글자 없이 표만 있다 → 지우지 않고, 표 앞뒤 빈 줄도 문두기호
        # 문장 '사이'가 아니므로 둔다. 5번만 문두기호 문장 사이 빈 줄이다.
        texts = ['□ 공모일정', 'ㅇ 개요', '', '□ 신청절차', 'ㅇ 절차', '', '- 내용']
        selections = self._delete(texts, control_paras=[2])
        self.assertEqual([args[2] for args in selections], [5])

    def test_deletes_from_the_end_joining_into_previous_paragraph(self):
        fn = self.ns['문두기호문장_사이_빈줄_삭제']
        texts = ['□ 제목', '', 'ㅇ 본문', '', '', '- 내용']
        state = {'i': 0}
        selections = []

        class Doc:
            def GetPos(self):
                return (0, state['i'], 0)
            def SetPos(self, *pos):
                pass
            def SelectText(self, *args):
                selections.append(args)
                return True

        def run(cmd):
            if cmd == 'MoveNextParaBegin' and state['i'] < len(texts) - 1:
                state['i'] += 1
            elif cmd == 'MoveDocBegin':
                state['i'] = 0

        doc = Doc()
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': run, '현재문단_텍스트': lambda: texts[state['i']],
            '중단_요청됨': lambda: False, '쪽범위_안인가': lambda pos=None: True,
            '로그': Mock(), '문두기호문장_빈줄_삭제_사용': True,
        }):
            self.assertTrue(fn())
        # 뒤에서부터(4, 3, 1번 빈 문단) 바로 앞 문단 끝에서 선택해 지운다.
        self.assertEqual([args[0] for args in selections], [3, 2, 0])
        self.assertEqual([args[2] for args in selections], [4, 3, 1])

    def test_setting_defaults_on(self):
        self.assertIs(self.ns['기본_설정']['std_remove_blank_lines'], True)


if __name__ == '__main__':
    unittest.main()
