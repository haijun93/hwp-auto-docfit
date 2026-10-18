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
        state = {'pos': (0, 3, 0), 'indent': -5992, 'left': 0}

        class Doc:
            ParaShape = type('P', (), {'Item': lambda self, key: state['left' if key == 'LeftMargin' else 'indent']})()

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

        def set_pair(left, indent):
            state['left'] = left
            state['indent'] = indent

        return Doc(), run, set_indent, set_pair

    def _assert_layout_refreshed(self, calls, target):
        line_end = calls.index('MoveLineEnd')
        jump = calls.index(('SetPos', target), line_end)
        self.assertIn('MoveParaBegin', calls[line_end + 1:jump])

    def test_body_indent_refreshes_layout_before_caret_jump(self):
        fn = self.ns['문단_내어쓰기_적용']
        calls = []
        doc, run, set_indent, set_pair = self._doc(calls)
        log = Mock()
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': run, '_내어쓰기_값_설정': set_indent,
            '_내어쓰기_여백쌍_설정': set_pair,
            '문단_내어쓰기_기준_오프셋': lambda text: 3,
            '현재_한칸표인가': lambda: False,
            '내어쓰기_변경문단': set(), '로그': log, '진단로그': Mock(),
        }):
            self.assertTrue(fn((0, 3, 0), ' ㅇ 난세기 예보 시 전 주민을'), repr(log.call_args_list))
        self._assert_layout_refreshed(calls, (0, 3, 3))

    def test_width_probe_refreshes_layout_before_caret_jump(self):
        fn = self.ns['_캐럿위치_폭_실측']
        calls = []
        doc, run, set_indent, _ = self._doc(calls)
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': run, '_내어쓰기_값_설정': set_indent,
            '현재문단_텍스트': lambda: ' ㅇ 난세기 예보 시 전 주민을', '진단로그': Mock(),
        }):
            self.assertEqual(fn((0, 3, 0), 3), 6480)
        self._assert_layout_refreshed(calls, (0, 3, 3))

    def test_hanging_indent_sets_compensating_left_margin(self):
        fn = self.ns['문단_내어쓰기_적용']
        calls = []
        doc, run, set_indent, set_pair = self._doc(calls)
        log = Mock()
        with patch.dict(fn.__globals__, {
            'hwp': doc,
            'hwp_run': run,
            '_내어쓰기_값_설정': set_indent,
            '_내어쓰기_여백쌍_설정': set_pair,
            '문단_내어쓰기_기준_오프셋': lambda text: 3,
            '_캐럿위치_폭_실측': lambda begin, count: 6480,
            '현재_한칸표인가': lambda: False,
            '로그': log,
            '진단로그': Mock(),
            '내어쓰기_변경문단': set(),
        }):
            self.assertTrue(fn((0, 3, 0), ' ㅇ 항목 내용'), repr(log.call_args_list))
        self.assertEqual(doc.ParaShape.Item('LeftMargin'), 6480)
        self.assertEqual(doc.ParaShape.Item('Indentation'), -6480)
        self.assertGreaterEqual(doc.ParaShape.Item('LeftMargin') + doc.ParaShape.Item('Indentation'), 0)


if __name__ == '__main__':
    unittest.main()
