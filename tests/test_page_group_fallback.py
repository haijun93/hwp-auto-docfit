"""A paragraph group that cannot be pulled back is pushed to the next page instead."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class PageGroupFallbackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def _run(self, can_shrink, can_expand):
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


if __name__ == '__main__':
    unittest.main()
