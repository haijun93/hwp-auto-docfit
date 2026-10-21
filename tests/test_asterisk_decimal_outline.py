"""십진 개요 번호(1.1.·1.1.1.) 문장도 단어 뒤 별표를 위첨자 대상으로 본다(2026-10-21 변형 항목기호 체계)."""
import unittest

from docfit_core.asterisk_superscript import applies_to, mark_spans


class DecimalOutlineAsteriskTest(unittest.TestCase):
    def test_decimal_outline_sentences_mark_word_stars(self):
        self.assertEqual(mark_spans("1.1.1. 항세기*와 난세기**가"), [(10, 11), (16, 18)])
        self.assertEqual(mark_spans("1.2.1 항성계 안정*"), [(12, 13)])
        self.assertTrue(applies_to("1.1. (현황) 문장"))

    def test_standard_and_non_targets_unchanged(self):
        self.assertEqual(mark_spans("   - 항세기*와"), [(8, 9)])
        self.assertEqual(mark_spans("* 항세기: 기후"), [])
        self.assertEqual(mark_spans("3*4 계산"), [])
        self.assertFalse(applies_to("일반 문장*"))


if __name__ == "__main__":
    unittest.main()
