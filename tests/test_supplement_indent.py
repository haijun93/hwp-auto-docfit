"""부연설명 앞 빈칸은 위 문단 유형별 칸 수를 따른다(기준 문서 '1) 보고서(계획서) 서식.hwpx')."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class SupplementIndentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_blank_counts_follow_the_reference_document(self):
        fn = self.ns['부연설명_앞빈칸_수']
        self.assertEqual([fn('제목', m) for m in ('※', '*', '**')], [4, 5, 4])
        self.assertEqual([fn('본문', m) for m in ('※', '*', '**')], [5, 6, 5])
        self.assertEqual([fn('내용', m) for m in ('※', '*', '**')], [5, 6, 5])
        self.assertEqual([fn(None, m) for m in ('※', '*', '**')], [3, 4, 3])
        self.assertIsNone(fn('본문', 'ㅇ'))

    def _run(self, texts, margins=None, 부모대상=None):
        fn = self.ns['부연설명_들여쓰기_전체_적용']
        state = {'i': 0}
        done = []
        margins = margins or {}

        class Doc:
            ParaShape = type('P', (), {'Item': lambda self, key: margins.get(state['i'], 0)})()
            def GetPos(self):
                return (0, state['i'], 0)
            def SetPos(self, *pos):
                state['i'] = pos[1]

        def next_para():
            if state['i'] >= len(texts) - 1:
                return False
            state['i'] += 1
            return True

        changed = set()
        with patch.dict(fn.__globals__, {
            'hwp': Doc(), 'hwp_run': lambda cmd: True, '중단_요청됨': lambda: False,
            '순회_시작': lambda: state.__setitem__('i', 0),
            '현재문단_텍스트': lambda: texts[state['i']],
            '범위_다음_문단으로_진행': next_para, '부연설명_들여쓰기_사용': True,
            '_부연설명_앞빈칸_적용': lambda start, text, n, left: done.append((start[1], n, left)) or True,
            '내어쓰기_변경문단': changed, '로그': Mock(), '진단로그': Mock(),
            '표준서식_설정': {},
        }):
            self.assertTrue(fn(부모대상=부모대상))
        return done, changed

    def test_counts_by_parent_type(self):
        texts = ['□ 제목', '※ 참고', '* 주', '** 주', ' ㅇ 본문', '※ 참고', '* 주',
                 '   - 내용', '** 주', '  1. 번호 항목', '※ 참고']
        done, changed = self._run(texts, margins={0: 0, 4: 300, 7: 600})
        self.assertEqual(done, [(1, 4, 0), (2, 5, 0), (3, 4, 0), (5, 5, 300), (6, 6, 300),
                                (8, 5, 600), (10, 3, None)])
        self.assertIn((0, 10), changed)

    def test_only_supplements_of_changed_parents_are_refreshed(self):
        done, changed = self._run(['ㅇ (개요) 본문', '※ 참고 1', '- 내용', '※ 참고 2'], 부모대상={(0, 2)})
        self.assertEqual(done, [(3, 5, 0)])
        self.assertEqual(changed, {(0, 3)})

    def test_apply_replaces_leading_blanks(self):
        fn = self.ns['_부연설명_앞빈칸_적용']
        calls = []
        doc = Mock()
        doc.ParaShape.Item.return_value = 0
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': lambda cmd: calls.append(cmd) or True, '현재_한칸표인가': lambda: False,
            '문단_범위_선택': lambda start, a, b: calls.append(('select', a, b)) or True,
            '텍스트_삽입': lambda t: calls.append(('insert', t)), '현재문단_텍스트': lambda: '     * 주',
            '표준서식_내어쓰기_사용': False, '진단로그': Mock(), '로그': Mock(),
        }):
            self.assertFalse(fn((0, 5, 0), '     * 주', 5, 0))       # 이미 5칸이면 그대로
            self.assertTrue(fn((0, 5, 0), '  * 주', 5, 0))
        self.assertIn(('select', 0, 2), calls)
        self.assertIn(('insert', '     '), calls)


if __name__ == '__main__':
    unittest.main()
