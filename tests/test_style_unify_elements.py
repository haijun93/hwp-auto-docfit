"""서식통일 고도화: 기울임·밑줄·취소선·정렬·좌우 여백도 대표값과 다른 문장만 고친다."""
from contextlib import contextmanager
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class UnifyElementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    @contextmanager
    def document(self, extras, **paragraph_values):
        """문장 4개. extras[i]는 i번째 문장의 부가 정보(정렬·여백·기울임 등)를 덮어쓴다."""
        fn = self.ns['서식통일_전체_적용']
        count = len(extras)
        index = [0]
        texts = [f'ㅇ 본문 {i}' for i in range(count)]

        def shape(pos, text):
            i = pos[1]
            end = (0, i, len(text))
            extra = {'marker_bold': False, 'label_bold': None, 'hanging_indent': False,
                     'marker_bold_runs': [(pos, (0, i, 1), False, 1)], 'label_bold_runs': [],
                     'parenthetical_size_runs': [], 'red_marked': False,
                     'align': 'JUSTIFY', 'left_margin': 0, 'right_margin': 0, 'lead_spaces': 0,
                     'italic': False, 'italic_runs': [(pos, end, False, len(text))],
                     'underline': 'NONE', 'underline_runs': [(pos, end, 'NONE', len(text))],
                     'strike': False, 'strike_runs': [(pos, end, False, len(text))]}
            extra.update(extras[i])
            return ('한컴돋움', 1500, [(pos, end, ('한컴돋움', 1500), len(text), False)], extra), pos, end

        def advance():
            index[0] += 1
            return index[0] < count

        def command(name):
            if name == 'MoveDocBegin':
                index[0] = 0

        com = Mock()
        com.GetPos.side_effect = lambda: (0, index[0], 0)
        para_shape = SimpleNamespace(HSet=None, AlignType=0, LeftMargin=0, RightMargin=0,
                                     Indentation=0, PrevSpacing=0)
        com.HParameterSet.HParaShape = para_shape
        action = Mock()
        com.CreateAction.return_value = action
        char_fix = Mock()
        with patch.dict(fn.__globals__, {
            'hwp': com, 'hwp_run': command, '중단_요청됨': lambda: False,
            '쪽범위_실제': None, '쪽범위_안인가': lambda pos: True,
            '현재문단_텍스트': lambda: texts[index[0]], '다음_문단으로_진행': advance,
            '서식통일_표본': shape, '_서식통일_문서대표프로필': {},
            '_서식통일_대표값_검토콜백': None, '_서식통일_내어쓰기_상태': lambda pos, text: False,
            '문자모양_적용_현재선택': Mock(), '_서식통일_미확정_빨간표시': Mock(),
            '_서식통일_문단자간_조정': Mock(return_value=True), '단어모드_범위선택': Mock(),
            '문단_내어쓰기_적용': Mock(), '_서식통일_글자요소_적용': char_fix,
            '로그': Mock(), '진단로그': Mock(), '검수_사용': False, **paragraph_values,
        }):
            yield fn, com, action, char_fix

    def para_items(self, action):
        params = action.CreateSet.return_value
        return [call.args for call in params.SetItem.call_args_list]

    def test_alignment_outlier_copies_representative_paragraph_value(self):
        extras = [{}, {}, {}, {'align': 'LEFT'}]
        with self.document(extras) as (fn, com, action, char_fix):
            self.assertTrue(fn())
            self.assertEqual(self.para_items(action), [('AlignType', 0)])
            # 예시(첫 문장)에서 값을 읽은 뒤 대상 문장으로 옮겨 적용한다.
            self.assertEqual(com.SetPos.call_args_list[-1].args, ((0, 3, 0)))
            char_fix.assert_not_called()

    def test_italic_outlier_fixes_only_italic_runs(self):
        extras = [{}, {}, {}, {'italic': True, 'italic_runs': [((0, 3, 0), (0, 3, 5), True, 5)]}]
        with self.document(extras) as (fn, com, action, char_fix):
            self.assertTrue(fn())
            char_fix.assert_called_once_with('italic', False, None, [((0, 3, 0), (0, 3, 5))])
            self.assertEqual(self.para_items(action), [])

    def test_left_margin_is_compared_only_with_same_leading_spaces(self):
        indented_by_spaces = [{}, {}, {}, {'left_margin': 1000, 'lead_spaces': 2}]
        with self.document(indented_by_spaces) as (fn, com, action, char_fix):
            self.assertTrue(fn())
            self.assertEqual(self.para_items(action), [])
        margin_only = [{}, {}, {}, {'left_margin': 1000}]
        with self.document(margin_only) as (fn, com, action, char_fix):
            self.assertTrue(fn())
            self.assertEqual(self.para_items(action), [('LeftMargin', 0)])

    def test_verification_reports_new_fields(self):
        extras = [{}, {}, {}, {'align': 'CENTER', 'underline': 'BOTTOM',
                               'underline_runs': [((0, 3, 0), (0, 3, 5), 'BOTTOM', 5)]}]
        with self.document(extras) as (fn, com, action, char_fix):
            result = fn(검증만=True)
            self.assertEqual(result['status'], 'failed')
            fields = result['issues'][0]['fields']
            self.assertIn('align', fields)
            self.assertIn('underline', fields)
            char_fix.assert_not_called()

    def test_representative_includes_new_fields(self):
        shapes = [('글꼴', 1500, (), {'align': 'JUSTIFY', 'left_margin': 0, 'italic': False,
                                       'underline': 'NONE', 'strike': False, 'right_margin': 0,
                                       'lead_spaces': 1})] * 3
        result = self.ns['서식통일_대표'](shapes)
        self.assertEqual(result['align'][0], 'JUSTIFY')
        self.assertEqual(result['left'][0], 0)
        self.assertIs(result['italic'][0], False)
        self.assertEqual(result['underline'][0], 'NONE')
        self.assertEqual(result['lead'][0], 1)


if __name__ == '__main__':
    unittest.main()
