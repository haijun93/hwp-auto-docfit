"""Spacing changes re-run hanging indent, then re-check only changed paragraphs, at most 3 times."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class SpacingIndentLoopTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def _run(self, changes_per_pass, indent_changes=({(0, 5)},) * 3):
        fn = self.ns['문서_처리_1회']
        g = fn.__globals__
        calls = []
        seen = []
        passes = iter(changes_per_pass)
        indents = iter(indent_changes)

        def spacing():
            calls.append('spacing')
            seen.append((g['재검사_대상문단'], g['다음단어_당김_사용']))
            g['자간_변경_횟수'] += next(passes, 0)
            return True

        def indent():
            calls.append('indent')
            g['내어쓰기_변경문단'].clear()
            g['내어쓰기_변경문단'].update(next(indents, set()))
            return True

        noop = lambda: True
        with patch.dict(g, {
            '작업_모드': 'spacing', '표준서식_사용': False, '표준서식_내어쓰기_사용': True,
            '선택_세부작업': {}, '자간_변경_횟수': 0, '내어쓰기_변경문단': set(),
            '재검사_대상문단': None, '다음단어_당김_사용': True,
            '중단_요청됨': lambda: False, '단계표시': Mock(), '상태': Mock(), '로그': Mock(),
            'hwp_run': lambda cmd: True, '순회_시작': noop,
            '본문_기존자간조정': spacing, '문단_내어쓰기_전체_갱신': indent,
            '본문_문장부호_처리': noop, '컨트롤_내부_자간조정': noop,
            '컨트롤_내부_문장부호_처리': noop,
        }):
            self.assertTrue(fn('test.hwpx'))
            # 반복이 끝나면 전체 검사·당김 사용 상태로 되돌린다.
            self.assertIsNone(g['재검사_대상문단'])
            self.assertTrue(g['다음단어_당김_사용'])
        return calls, seen

    def test_no_spacing_change_skips_indent(self):
        calls, _ = self._run([0])
        self.assertEqual(calls, ['spacing'])

    def test_indent_after_change_then_recheck_stops_when_clean(self):
        calls, _ = self._run([2, 0])
        self.assertEqual(calls, ['spacing', 'indent', 'spacing'])

    def test_loop_is_capped_at_three_rounds(self):
        calls, _ = self._run([1, 1, 1, 1])
        self.assertEqual(calls, ['spacing', 'indent'] * 3)

    def test_later_passes_check_only_changed_paragraphs_without_pull(self):
        _, seen = self._run([3, 1, 0], indent_changes=[{(0, 5), (0, 9)}, {(0, 9)}])
        self.assertEqual(seen, [(None, True), ({(0, 5), (0, 9)}, False), ({(0, 9)}, False)])

    def test_recheck_skipped_when_indent_unchanged(self):
        calls, _ = self._run([4, 1], indent_changes=[set()])
        self.assertEqual(calls, ['spacing', 'indent'])

    def test_recheck_filters(self):
        g = self.ns['재검사_대상인가'].__globals__
        with patch.dict(g, {'재검사_대상문단': None}):
            self.assertTrue(self.ns['재검사_대상인가']((0, 3, 7)))
            self.assertTrue(self.ns['재검사_영역인가'](2))
        with patch.dict(g, {'재검사_대상문단': {(0, 3)}}):
            self.assertTrue(self.ns['재검사_대상인가']((0, 3, 7)))
            self.assertFalse(self.ns['재검사_대상인가']((0, 4, 0)))
            self.assertFalse(self.ns['재검사_영역인가'](2))


if __name__ == '__main__':
    unittest.main()
