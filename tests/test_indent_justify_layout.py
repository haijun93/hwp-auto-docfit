"""양쪽 정렬 첫 줄의 늘어난 빈칸을 반영해 Shift+Tab 기준 글자를 잡는다.

줄 끝(MoveLineEnd)에서 곧바로 SetPos로 기준 글자에 가면 한/글이 늘기 전 글자 위치로 내어쓰기를
계산한다(실측: 'ㅇ 난세기…' 5992 대 6480, 둘째 줄이 기준 글자보다 약 1mm 왼쪽). 이동 명령
(MoveParaBegin)을 한 번 거쳐 줄 배치를 반영한 뒤 기준 글자로 가야 한다.
"""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class JustifiedIndentLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def _doc(self, calls):
        state = {'pos': (0, 3, 0), 'indent': -5992}

        class Doc:
            ParaShape = type('P', (), {'Item': lambda self, key: state['indent']})()

            def GetPos(self):
                return state['pos']

            def SetPos(self, *pos):
                calls.append(('SetPos', tuple(pos)))
                state['pos'] = tuple(pos)
                return True

        def run(cmd):
            calls.append(cmd)
            if cmd == 'MoveLineEnd':
                state['pos'] = (0, 3, 30)
            elif cmd == 'MoveParaBegin':
                state['pos'] = (0, 3, 0)
            elif cmd == 'ParagraphShapeIndentAtCaret':
                state['indent'] = -6480
            return True

        def set_indent(value):
            state['indent'] = value

        return Doc(), run, set_indent

    def _assert_layout_refreshed(self, calls, target):
        line_end = calls.index('MoveLineEnd')
        jump = calls.index(('SetPos', target), line_end)
        self.assertIn('MoveParaBegin', calls[line_end + 1:jump])

    def test_body_indent_refreshes_layout_before_caret_jump(self):
        fn = self.ns['문단_내어쓰기_적용']
        calls = []
        doc, run, set_indent = self._doc(calls)
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': run, '_내어쓰기_값_설정': set_indent, '현재_한칸표인가': lambda: False,
            '내어쓰기_변경문단': set(), '로그': Mock(), '진단로그': Mock(),
        }):
            self.assertTrue(fn((0, 3, 0), ' ㅇ 난세기 예보 시 전 주민을'))
        self._assert_layout_refreshed(calls, (0, 3, 3))

    def test_width_probe_refreshes_layout_before_caret_jump(self):
        fn = self.ns['_캐럿위치_폭_실측']
        calls = []
        doc, run, set_indent = self._doc(calls)
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': run, '_내어쓰기_값_설정': set_indent,
            '현재문단_텍스트': lambda: ' ㅇ 난세기 예보 시 전 주민을', '진단로그': Mock(),
        }):
            self.assertEqual(fn((0, 3, 0), 3), 6480)
        self._assert_layout_refreshed(calls, (0, 3, 3))


if __name__ == '__main__':
    unittest.main()
