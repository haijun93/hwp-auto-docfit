"""A paragraph group that cannot be pulled back is pushed to the next page instead."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class PageGroupFallbackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def _run(self, can_shrink, can_expand, too_long=False, page_break=False):
        fn = self.ns['세트문장_같은쪽_시도']
        stats = {'대상': 0, '성공': 0, '실패': 0, '축소횟수': 0}
        applied = []
        state = {'counts': {3: 4, 4: 1}}

        class Doc:
            pos = (0, 5, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos)

        def apply(backup, step, 확대=False):
            applied.append(('확대' if 확대 else '축소', step))
            if step == 0:
                state['counts'] = {3: 4, 4: 1}
                return True
            if 확대 and can_expand:
                state['counts'] = {4: 5}
                return True
            if not 확대 and can_shrink:
                state['counts'] = {3: 5}
                return True
            return False

        record = Mock()
        breaks = []
        self.breaks = breaks
        with patch.dict(fn.__globals__, {
            'hwp': Doc(), 'hwp_run': lambda cmd: True, '중단_요청됨': lambda: False,
            '보고서_문단역할': lambda text: '소제목',
            '보고서_본문묶음_수집': lambda pos: [((0, 5, 0), (0, 5, 10), '소제목')],
            '쪽범위_사용중': lambda: False,
            '보고서_묶음_쪽별줄수': lambda paragraphs: dict(state['counts']),
            '보고서_줄간격_보관': lambda a, b: [((0, 3, 0), 0, 160), ((0, 5, 0), 0, 160)],
            '보고서_줄간격_적용': apply,
            '세트문장_통계': stats, '검수_문제_기록': record,
            '로그': Mock(), '진단로그': Mock(), '현재_처리파일': 'x.hwpx',
            '쪽보다_긴_묶음인가': lambda paragraphs, counts: too_long,
            '_묶음_쪽나눔_이동': lambda *args: breaks.append(args) or page_break,
        }):
            self.assertTrue(fn((0, 5, 0), 'ㅇ (기대효과 및 한계)'))
        return stats, applied, record

    def test_minimum_spacing_falls_back_to_pushing_group(self):
        stats, applied, record = self._run(can_shrink=False, can_expand=True)
        self.assertEqual(applied, [('축소', 1), ('확대', 1)])
        self.assertEqual((stats['성공'], stats['실패']), (1, 0))
        record.assert_not_called()

    def test_preferred_direction_still_wins_when_possible(self):
        stats, applied, _ = self._run(can_shrink=True, can_expand=True)
        self.assertEqual(applied, [('축소', 1)])
        self.assertEqual(stats['성공'], 1)

    def test_both_directions_blocked_is_recorded_once(self):
        stats, _, record = self._run(can_shrink=False, can_expand=False)
        self.assertEqual((stats['대상'], stats['성공'], stats['실패']), (1, 0, 1))
        record.assert_called_once()

    def test_group_longer_than_a_page_is_left_alone(self):
        stats, applied, record = self._run(can_shrink=False, can_expand=False, too_long=True)
        self.assertEqual(applied, [])
        self.assertEqual(stats['대상'], 0)
        record.assert_not_called()

    def test_page_break_when_spacing_cannot_move_group(self):
        stats, _, record = self._run(can_shrink=False, can_expand=False, page_break=True)
        self.assertEqual((stats['대상'], stats['성공'], stats['실패']), (1, 1, 0))
        self.assertEqual(len(self.breaks), 1)
        record.assert_not_called()


class PageBreakHelperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def _move(self, front, capacity, after_counts):
        fn = self.ns['_묶음_쪽나눔_이동']
        calls = []

        class Doc:
            pos = (0, 5, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos)
        with patch.dict(fn.__globals__, {
            'hwp': Doc(), 'hwp_run': lambda cmd: True, '로그': Mock(),
            '쪽_본문줄수': lambda pos: capacity,
            '쪽나눔_설정': lambda pos, on: calls.append(on),
            '보고서_묶음_쪽별줄수': lambda paragraphs: after_counts,
        }):
            ok = fn((0, 5, 0), [((0, 5, 0), (0, 6, 9), '본문')], {2: front, 3: 12}, 'ㅇ (만들기)')
        return ok, calls

    def test_breaks_when_front_part_is_small(self):
        self.assertEqual(self._move(8, 34, {3: 20}), (True, [True]))

    def test_no_break_when_it_would_leave_a_large_blank(self):
        self.assertEqual(self._move(22, 34, {3: 34}), (False, []))

    def test_reverts_break_when_group_still_splits(self):
        self.assertEqual(self._move(8, 34, {3: 30, 4: 4}), (False, [True, False]))

    def test_longer_than_page_detection(self):
        fn = self.ns['쪽보다_긴_묶음인가']
        paragraphs = [((0, 5, 0), (0, 9, 9), '본문')]
        with patch.dict(fn.__globals__, {'쪽첫줄_시작인가': lambda pos: False,
                                         '쪽_본문줄수': lambda pos: 30}):
            self.assertTrue(fn(paragraphs, {2: 22, 3: 12}))    # 34줄 > 30줄
            self.assertFalse(fn(paragraphs, {2: 8, 3: 12}))    # 20줄
            self.assertFalse(fn(paragraphs, {3: 20}))          # 이미 한 쪽
        with patch.dict(fn.__globals__, {'쪽첫줄_시작인가': lambda pos: True,
                                         '쪽_본문줄수': lambda pos: 30}):
            self.assertTrue(fn(paragraphs, {2: 25, 3: 3}))     # 쪽 첫 줄에서 시작해도 넘침


if __name__ == '__main__':
    unittest.main()
