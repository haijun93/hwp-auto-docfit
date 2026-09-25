"""부연설명 들여쓰기는 위 문단의 '실측' 본문 시작 위치에 마커를 맞춘다(TODO 1순위)."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class SupplementIndentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def _doc(self, left_margin=0):
        applied = []

        class Action:
            def CreateSet(self):
                values = {}
                return type('Set', (), {'SetItem': lambda self, k, v: values.__setitem__(k, v),
                                        'values': values})()
            def Execute(self, pset):
                applied.append(dict(pset.values))
                return True

        class Doc:
            pos = (0, 5, 0)
            ParaShape = type('P', (), {'Item': lambda self, key: {'LeftMargin': left_margin}[key]})()
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos)
            def CreateAction(self, name):
                return Action()
        return Doc(), applied

    def test_marker_lands_on_parent_text_start(self):
        fn = self.ns['_부연설명_들여쓰기_적용']
        doc, applied = self._doc()
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': lambda cmd: True, '현재_한칸표인가': lambda: False,
            '_캐럿위치_폭_실측': lambda start, n: 5000, '진단로그': Mock(), '로그': Mock(),
        }):
            # 선행 공백(실측 5000) 뒤 마커가 부모 본문 시작(15160)에 오도록 왼쪽여백 10160
            self.assertTrue(fn((0, 5, 0), '    ※ (차량규격) 전기버스', 15160))
        self.assertEqual(applied, [{'LeftMargin': 10160}])

    def test_no_leading_space_and_unchanged_margin(self):
        fn = self.ns['_부연설명_들여쓰기_적용']
        measure = Mock(side_effect=AssertionError('선행 공백이 없으면 재지 않음'))
        doc, applied = self._doc(left_margin=1104)
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': lambda cmd: True, '현재_한칸표인가': lambda: False,
            '_캐럿위치_폭_실측': measure, '진단로그': Mock(), '로그': Mock(),
        }):
            self.assertFalse(fn((0, 5, 0), '※주의사항안내', 1104))   # 이미 같으면 바꾸지 않음
        self.assertEqual(applied, [])

    def test_only_supplements_of_changed_parents_are_refreshed(self):
        fn = self.ns['부연설명_들여쓰기_전체_적용']
        texts = ['ㅇ (개요) 본문', '※ 참고 1', '- 내용', '※ 참고 2']
        state = {'i': 0}
        done = []

        class Doc:
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
            '부모_본문시작_실측': lambda start, text: 1000 + start[1],
            '_부연설명_들여쓰기_적용': lambda start, text, w: done.append((start[1], w)) or True,
            '내어쓰기_변경문단': changed, '로그': Mock(), '진단로그': Mock(),
            '표준서식_설정': {},
        }):
            self.assertTrue(fn(부모대상={(0, 2)}))
        self.assertEqual(done, [(3, 1002)])      # '- 내용' 아래 부연설명만
        self.assertEqual(changed, {(0, 3)})      # 다음 단어 분리 재검사 대상


if __name__ == '__main__':
    unittest.main()
