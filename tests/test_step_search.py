"""자간·장평 단계 탐색이 한 단계씩 늘리는 방식과 같은 답을 더 적은 측정으로 찾는다."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

# 11:39 실행 로그의 실제 어절 분리 성공 단계(당김·밈).
LOG_STEPS = [4, 2, 2, 4, 1, 2, 4, 6, 1, 8, 5, 2, 2, 4, 7, 3, 6]


class StepSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.search = staticmethod(cls.ns['최소_성공단계_탐색'])

    def run_search(self, maximum, threshold, **options):
        applied = []
        with patch.dict(self.search.__globals__, {'중단_요청됨': lambda: False,
                                                  '단계탐색_통계': {'탐색': 0, '측정': 0}}):
            found = self.search(maximum, lambda s: applied.append(s) or s >= threshold, **options)
        return found, applied

    def check_same_answer(self, **options):
        for maximum in (4, 10, 30):
            for threshold in range(1, maximum + 2):
                found, applied = self.run_search(maximum, threshold, **options)
                self.assertEqual(found, threshold if threshold <= maximum else None,
                                 (options, maximum, threshold))
                if found is not None:
                    self.assertEqual(applied[-1], found)   # 찾은 단계가 적용된 상태

    def test_same_answer_as_linear(self):
        self.check_same_answer()
        self.check_same_answer(상한먼저=True)

    def test_default_matches_linear_cost_up_to_eight_steps(self):
        for threshold in range(1, 9):
            self.assertEqual(len(self.run_search(30, threshold)[1]), threshold)
        linear = sum(LOG_STEPS)
        search = sum(len(self.run_search(30, t)[1]) for t in LOG_STEPS)
        self.assertEqual(search, linear)   # 실제 로그 분포에서 손해가 없다

    def test_failures_need_far_fewer_measurements(self):
        found, applied = self.run_search(30, 99)
        self.assertIsNone(found)
        self.assertEqual(len(applied), 9)          # 예전 30번
        found, applied = self.run_search(10, 99, 상한먼저=True)
        self.assertIsNone(found)
        self.assertEqual(applied, [10])            # 예전 10번

    def test_zero_maximum_does_nothing(self):
        self.assertEqual(self.run_search(0, 1), (None, []))

    def test_abort_raises(self):
        with patch.dict(self.search.__globals__, {'중단_요청됨': lambda: True,
                                                  '단계탐색_통계': {'탐색': 0, '측정': 0}}):
            with self.assertRaises(self.ns['_단계탐색_중단']):
                self.search(10, lambda step: True)

    def test_non_monotonic_layout_still_returns_verified_step(self):
        results = {s: s in (10, 12, 13, 14, 15, 16) for s in range(1, 17)}
        applied = []
        with patch.dict(self.search.__globals__, {'중단_요청됨': lambda: False,
                                                  '단계탐색_통계': {'탐색': 0, '측정': 0}}):
            found = self.search(16, lambda s: applied.append(s) or results[s])
        self.assertTrue(results[found])
        self.assertEqual(applied[-1], found)


if __name__ == '__main__':
    unittest.main()
