"""날짜 끝 온점 채우기가 시각을 날짜로 오인하지 않는다(test6 시험 P1: '15:00' → '15.:00', 2026-10-10)."""
import unittest

from docfit_core.document_rules import normalize_date_range_marks as f


class DateTimeDotTest(unittest.TestCase):
    def test_time_after_date_is_kept(self):
        self.assertEqual(f("2026. 10. 4. 15:00"), "2026. 10. 4. 15:00")
        self.assertEqual(f("기간: 2026. 10. 4.~10. 25. 15:00 [매주 일요일]"), "기간: 2026. 10. 4.~10. 25. 15:00 [매주 일요일]")
        self.assertEqual(f("10. 25. 15:00"), "10. 25. 15:00")

    def test_existing_normalization_still_works(self):
        self.assertEqual(f("2026. 3. 1"), "2026. 3. 1.")
        self.assertEqual(f("2026. 10. 5(월)"), "2026. 10. 5.(월)")
        self.assertEqual(f("2026. 3. 1 - 2026. 6. 30"), "2026. 3. 1. ~ 2026. 6. 30.")


if __name__ == '__main__':
    unittest.main()
