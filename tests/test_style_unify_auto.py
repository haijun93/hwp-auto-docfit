"""Automatic exception correction and unresolved-style red marking."""
from contextlib import contextmanager
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class AutomaticUnifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    @contextmanager
    def document(self, sizes=(1500, 1500, 1500, 1700), *, red=False, scope=None, review=None):
        fn = self.ns['서식통일_전체_적용']
        index = [0]
        texts = [f'ㅇ 본문 {i}' for i in range(len(sizes))]
        def shape(pos, text):
            i = pos[1]
            end = (0, i, len(text))
            return ('한컴돋움', sizes[i], [(pos, end, ('한컴돋움', sizes[i]), len(text), False)], {
                'marker_bold': False, 'label_bold': None, 'hanging_indent': False,
                'marker_bold_runs': [(pos, (0, i, 1), False, 1)],
                'label_bold_runs': [], 'parenthetical_size_runs': [], 'red_marked': red,
            }), pos, end
        def advance():
            index[0] += 1
            return index[0] < len(sizes)
        com = Mock()
        com.GetPos.side_effect = lambda: (0, index[0], 0)
        def command(name):
            if name == 'MoveDocBegin':
                index[0] = 0
        callback = Mock(side_effect=review or (lambda kind, payload: {'approved': True}))
        writes, marks, selection, indent = Mock(), Mock(), Mock(), Mock()
        with patch.dict(fn.__globals__, {
            'hwp': com, 'hwp_run': command, '중단_요청됨': lambda: False,
            '쪽범위_실제': None, '쪽범위_안인가': scope or (lambda pos: True),
            '현재문단_텍스트': lambda: texts[index[0]], '다음_문단으로_진행': advance,
            '서식통일_표본': shape, '_서식통일_문서대표프로필': {},
            '_서식통일_대표값_검토콜백': callback,
            '_서식통일_내어쓰기_상태': lambda pos, text: False,
            '문자모양_적용_현재선택': writes, '_서식통일_미확정_빨간표시': marks,
            '_서식통일_문단자간_조정': Mock(return_value=True),
            '단어모드_범위선택': selection, '문단_내어쓰기_적용': indent,
            '로그': Mock(), '진단로그': Mock(),
        }):
            yield fn, callback, writes, marks, selection, indent

    def test_automatically_corrects_only_outlier_without_regions_dialog(self):
        with self.document() as (fn, callback, writes, marks, selection, indent):
            self.assertTrue(fn())
            self.assertEqual([call.args[0] for call in callback.call_args_list], [])
            writes.assert_called_once_with(크기_pt=15.0, 자간_유지=True)
            self.assertEqual(selection.call_args.args[0], (0, 3, 0))
            marks.assert_not_called()
            indent.assert_not_called()

    def test_standard_paragraphs_receive_no_writes(self):
        with self.document((1500,) * 4) as (fn, _, writes, marks, selection, indent):
            self.assertTrue(fn())
            for operation in (writes, marks, selection, indent):
                operation.assert_not_called()

    def test_tied_size_marks_all_unresolved_paragraphs_not_arbitrary_winner(self):
        with self.document((1500, 1700)) as (fn, _, writes, marks, _, _):
            self.assertTrue(fn())
            writes.assert_not_called()
            self.assertEqual(marks.call_count, 2)

    def test_single_sentence_group_is_left_alone(self):
        # 같은 계층 문장이 하나뿐이면 '다른 문장'을 가릴 기준이 없으므로 고치거나 표시하지 않는다.
        with self.document((1500,)) as (fn, _, writes, marks, _, _):
            self.assertTrue(fn())
            writes.assert_not_called()
            marks.assert_not_called()

    def test_marking_respects_selected_page_range(self):
        with self.document((1500, 1700), scope=lambda pos: pos[1] == 1) as (fn, _, _, marks, _, _):
            fn()
            marks.assert_called_once()
            self.assertEqual(marks.call_args.args[0], (0, 1, 0))

    def test_profile_is_auto_approved_without_user_review(self):
        with self.document(review=lambda *_: {'approved': False}) as (fn, callback, writes, *_):
            self.assertTrue(fn())
            callback.assert_not_called()
            writes.assert_called_once_with(크기_pt=15.0, 자간_유지=True)

    def test_standard_format_follow_up_skips_red_marking(self):
        with self.document((1500, 1700)) as (fn, _, writes, marks, _, _):
            with patch.dict(fn.__globals__, {'서식통일_빨간표시_사용': False}):
                self.assertTrue(fn())
            marks.assert_not_called()

    def test_standard_format_follow_up_verification_does_not_require_red(self):
        with self.document((1500, 1700), red=False) as (fn, *_):
            with patch.dict(fn.__globals__, {'서식통일_빨간표시_사용': False}):
                result = fn(검증만=True)
            self.assertEqual(result['status'], 'passed')

    def test_saved_verification_is_read_only_and_reports_red_unknowns(self):
        with self.document((1500, 1700), red=True) as (fn, callback, writes, marks, selection, indent):
            result = fn(검증만=True)
            self.assertEqual(result['status'], 'incomplete')
            self.assertEqual(len(result['unresolved']), 2)
            self.assertEqual(result['unresolved'][0]['fields'], ['size'])
            for operation in (callback, writes, marks, selection, indent):
                operation.assert_not_called()

    def test_verification_detects_failed_red_marking(self):
        with self.document((1500, 1700)) as (fn, _, _, marks, _, _):
            result = fn(검증만=True)
            self.assertEqual(result['status'], 'failed')
            self.assertIn('unresolved_red_marking', result['issues'][0]['fields'])
            marks.assert_not_called()

    def test_absent_label_is_not_treated_as_unknown_style(self):
        profile = {key: (value, 3) for key, value in {
            'font': '한컴돋움', 'size': 1500, 'marker_bold': False,
            'label_bold': None, 'hanging_indent': False,
        }.items()}
        fn = self.ns['_서식통일_미확정_항목']
        self.assertEqual(fn(profile, 'ㅇ 본문'), [])
        self.assertEqual(fn(profile, 'ㅇ (개요) 본문'), ['label_bold'])

    def test_red_marking_writes_only_color_and_propagates_failure(self):
        fn = self.ns['_서식통일_미확정_빨간표시']
        com = Mock()
        com.RGBColor.return_value = 255
        action = com.CreateAction.return_value
        with patch.dict(fn.__globals__, {'hwp': com, '단어모드_범위선택': Mock(), 'hwp_run': Mock()}):
            fn((0, 0, 0), (0, 0, 10))
            action.CreateSet.return_value.SetItem.assert_called_once_with('TextColor', 255)
            com.HAction.GetDefault.assert_not_called()
            action.Execute.return_value = False
            with self.assertRaises(RuntimeError):
                fn((0, 0, 0), (0, 0, 10))

    def test_indent_is_fixed_before_spacing_pass_on_corrected_sentences(self):
        # 자간 뒤에 내어쓰기를 적용하면 둘째 줄 폭이 바뀌어 새 단어 분리가 생긴다.
        events = []
        with self.document((1700, 1500, 1500, 1500, 1700, 1500, 1500)) as (fn, *_):
            pending = fn.__globals__['_서식통일_자간보류문단']
            pending.clear()
            def spacing_pass():
                events.append(('spacing_pass', sorted(pending)))
                return True
            with patch.dict(fn.__globals__, {
                '_서식통일_문단서식_적용': lambda item: events.append(('format', item['start'][1])),
                '_서식통일_문단내어쓰기_적용': lambda item: events.append(('indent', item['start'][1])),
                '서식통일_보류자간_재조정': spacing_pass,
            }):
                self.assertTrue(fn())
            pending.clear()
        # 서식은 문장별로 먼저 맞추고, 마무리 묶음은 고친 문장에만 한 번 적용한다.
        self.assertEqual(events, [('format', 0), ('format', 4),
                                  ('spacing_pass', ['ㅇ 본문 0', 'ㅇ 본문 4'])])

    def test_sentence_finish_runs_indent_then_spacing_then_short_line_merge(self):
        fn = self.ns['서식통일_문장_마무리']
        events = []
        com = Mock()
        positions = iter([(0, 3, 30), (0, 3, 0), (0, 4, 0)])
        com.GetPos.side_effect = lambda: next(positions)
        with patch.dict(fn.__globals__, {
            'hwp': com, 'hwp_run': lambda name: None, '중단_요청됨': lambda: False,
            '서식통일_줄병합_사용': True,
            '문단_내어쓰기_기준_오프셋': lambda text: 2,
            '문단_내어쓰기_적용': lambda start, text: events.append('indent'),
            '_서식통일_문단자간_조정': lambda start, end: events.append('spacing'),
            '문장부호_줄병합_시도': lambda: events.append('merge'),
        }):
            self.assertTrue(fn((0, 3, 0), 'ㅇ 본문', True))
        self.assertEqual(events, ['indent', 'spacing', 'merge'])

    def test_unknown_style_does_not_trigger_spacing_or_indent(self):
        with self.document((1500, 1700)) as (fn, *_):
            spacing, indent = Mock(), Mock()
            with patch.dict(fn.__globals__, {
                '_서식통일_문단자간_조정': spacing, '_서식통일_문단내어쓰기_적용': indent,
            }):
                fn()
            spacing.assert_not_called()
            indent.assert_not_called()

    def test_scoped_spacing_restores_failed_attempts_and_caps_existing_compression(self):
        fn = self.ns['_서식통일_문단자간_조정']
        com = Mock()
        com.GetPos.return_value = (0, 3, 20)
        start, end = (0, 3, 0), (0, 3, 20)
        info = (start, (0, 3, 10), start, (0, 3, 14), 10, 4)
        apply = Mock()
        runs = [(start, (0, 3, 14), (-8,) * 7)]
        with patch.dict(fn.__globals__, {
            'hwp': com, 'hwp_run': Mock(), '중단_요청됨': lambda: False,
            '자간_최대시도_본문': 30, '단어모드_분리정보': lambda pos: info,
            '단어모드_마지막줄_짧은잔여인가': lambda pos: True,
            '단어모드_자간보관': lambda a, b: runs, '단어모드_자간적용': apply,
            '단어모드_줄범위': lambda pos: (start, (0, 3, 10)),
            '검수_문제_기록': Mock(), '진단로그': Mock(),
        }):
            self.assertTrue(fn(start, end))
        self.assertEqual([call.args[1] for call in apply.call_args_list], [-1, -2, 0])

    def test_scoped_spacing_rejects_cross_paragraph_ranges_before_write(self):
        fn = self.ns['_서식통일_문단자간_조정']
        apply = Mock()
        with patch.dict(fn.__globals__, {
            'hwp': Mock(), '중단_요청됨': lambda: False,
            '단어모드_분리정보': lambda pos: ((0, 3, 0), (0, 3, 10), (0, 3, 6), (0, 4, 5), 4, 5),
            '단어모드_자간적용': apply,
        }):
            with self.assertRaisesRegex(RuntimeError, '벗어났습니다'):
                fn((0, 3, 0), (0, 3, 20))
        apply.assert_not_called()


if __name__ == '__main__':
    unittest.main()
