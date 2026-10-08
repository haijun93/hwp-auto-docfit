import unittest

from docfit_core.page_fit_search import classify_reports, level_amounts, search_level


class ClassifyReportsTest(unittest.TestCase):
    def report(self, start, end, overflow=None):
        return {'start': start, 'end': end, 'overflow': overflow}

    def test_single_page_report(self):
        self.assertEqual(classify_reports([self.report(1, 1)]), ('1쪽 보고서', []))

    def test_one_page_report_spilling_few_lines(self):
        self.assertEqual(classify_reports([self.report(1, 2, 3)]), ('1쪽 보고서', [0]))

    def test_long_single_report_is_deep_report(self):
        self.assertEqual(classify_reports([self.report(1, 2, 20)])[0], '심화보고서')
        self.assertEqual(classify_reports([self.report(1, 5, 2)])[0], '심화보고서')

    def test_bundle_fits_only_spilled_one_page_reports(self):
        reports = [self.report(1, 1), self.report(2, 3, 2), self.report(4, 7, 1), self.report(8, 9, None)]
        self.assertEqual(classify_reports(reports), ('취합보고서', [1]))


class LevelAmountsTest(unittest.TestCase):
    def test_bottom_then_top(self):
        self.assertEqual(level_amounts(0), (0.0, 0.0, 0.0))
        self.assertEqual(level_amounts(3), (3.0, 0.0, 0.3))
        self.assertEqual(level_amounts(10), (10.0, 0.0, 1.0))
        self.assertEqual(level_amounts(16), (10.0, 6.0, 1.0))
        self.assertEqual(level_amounts(20), (10.0, 10.0, 1.0))


class SearchLevelTest(unittest.TestCase):
    def pages_from(self, reach_level, before=23, after=22):
        calls = []

        def measure(level):
            calls.append(level)
            return after if level >= reach_level else before
        return measure, calls

    def test_finds_minimum_level_with_few_measurements(self):
        measure, calls = self.pages_from(16)
        result = search_level(measure, 22, 20)
        self.assertEqual((result['status'], result['level']), ('ok', 16))
        self.assertLessEqual(len(calls), 6)        # 선형 방식은 16번 측정

    def test_gives_up_after_one_measurement_when_max_level_fails(self):
        measure, calls = self.pages_from(99)
        result = search_level(measure, 22, 20)
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(calls, [20])

    def test_bundle_split_tries_extra_levels_then_keeps_first(self):
        measure, _ = self.pages_from(5)
        seen = []
        result = search_level(measure, 22, 20, bundle_split=lambda lv: seen.append(lv) or True)
        self.assertEqual((result['status'], result['level']), ('bundle_moved', 5))
        self.assertEqual(seen, [5, 6, 7, 8, 9])

    def test_bundle_split_resolved_at_higher_level(self):
        measure, _ = self.pages_from(5)
        result = search_level(measure, 22, 20, bundle_split=lambda lv: lv < 7)
        self.assertEqual((result['status'], result['level']), ('ok', 7))

    def test_measure_failure_is_error(self):
        result = search_level(lambda lv: None, 22, 20)
        self.assertEqual(result['status'], 'error')


if __name__ == '__main__':
    unittest.main()
