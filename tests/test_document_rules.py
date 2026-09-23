import unittest

from docfit_core.document_rules import (
    ParagraphSpacingTracker,
    marker_space_fix,
    normalize_straight_double_quotes,
    normalize_year_quotes,
    straight_double_quote_replacements,
)


class YearQuoteTest(unittest.TestCase):
    def test_year_variants_only(self):
        variants = "'‘ʼ′`´"
        for quote in variants:
            with self.subTest(quote=quote):
                self.assertEqual(normalize_year_quotes(f"{quote}21년"), "’21년")
                self.assertEqual(normalize_year_quotes(f"{quote}21.4월"), "’21.4월")
                self.assertEqual(normalize_year_quotes(f"{quote}21.4.4일"), "’21.4.4일")

    def test_quotes_without_year_are_unchanged(self):
        samples = ("6' 신발", "‘안녕’이라고", "'2021년", "'21일", "'21x4", "'21-4", "'21.456")
        for text in samples:
            with self.subTest(text=text):
                self.assertEqual(normalize_year_quotes(text), text)
        self.assertEqual(normalize_year_quotes("’21년"), "’21년")
        self.assertEqual(normalize_year_quotes("'21년과 `22.12월"), "’21년과 ’22.12월")


class StraightDoubleQuoteTest(unittest.TestCase):
    def test_simple_pair_at_sentence_boundaries(self):
        self.assertEqual(normalize_straight_double_quotes('그는 "좋다"라고 말했다'),
                          "그는 “좋다”라고 말했다")

    def test_quote_at_very_start_of_text_is_opening(self):
        self.assertEqual(normalize_straight_double_quotes('"안녕"'), "“안녕”")

    def test_quote_after_opening_bracket_is_opening(self):
        self.assertEqual(normalize_straight_double_quotes('(예: "확인")'), "(예: “확인”)")

    def test_multiple_pairs_in_one_paragraph(self):
        self.assertEqual(normalize_straight_double_quotes('"가"와 "나" 항목'),
                          "“가”와 “나” 항목")

    def test_text_without_quotes_is_unchanged(self):
        text = "따옴표가 없는 평범한 문장입니다."
        self.assertEqual(normalize_straight_double_quotes(text), text)

    def test_already_curly_quotes_are_left_alone(self):
        text = "그는 “좋다”라고 말했다"
        self.assertEqual(normalize_straight_double_quotes(text), text)

    def test_single_quotes_are_never_touched(self):
        # 발·분 표기나 영어 축약형과 구분할 수 없어 작은따옴표는 다루지 않는다.
        text = "6' 2\" 신발과 don't"
        result = normalize_straight_double_quotes(text)
        self.assertIn("'", result)
        self.assertNotIn('"', result)

    def test_replacements_report_index_and_char(self):
        self.assertEqual(straight_double_quote_replacements('"가"'),
                          [(0, "“"), (2, "”")])
        self.assertEqual(straight_double_quote_replacements("본문"), [])


class MarkerSpaceFixTest(unittest.TestCase):
    def test_already_one_space_needs_nothing(self):
        self.assertIsNone(marker_space_fix("ㅇ 본문", 1))

    def test_missing_space_is_an_insert(self):
        self.assertEqual(marker_space_fix("ㅇ본문", 1), "insert")

    def test_tab_after_marker_is_a_replace(self):
        self.assertEqual(marker_space_fix("ㅇ\t본문", 1), "replace")

    def test_full_width_space_after_marker_is_a_replace(self):
        self.assertEqual(marker_space_fix("ㅇ　본문", 1), "replace")

    def test_no_room_after_marker_needs_nothing(self):
        self.assertIsNone(marker_space_fix("ㅇ", 1))
        self.assertIsNone(marker_space_fix("ㅇ", None))


class ParagraphSpacingTest(unittest.TestCase):
    def test_return_from_deeper_level(self):
        tracker = ParagraphSpacingTracker()
        base = {"box": 15, "circle": 10, "note": 3}
        texts = ("□ 제목", "ㅇ 본문", "ㅇ 본문", "- 내용", "* 참고",
                 "ㅇ 새 본문", "* 참고", "- 내용", "ㅇ 복귀", "□ 복귀")
        self.assertEqual([tracker.spacing_for(text, base) for text in texts],
                         [15, 10, 10, None, 3, 15, 3, None, 15, 22])

    def test_100_percent_is_old_behavior_and_reset(self):
        tracker = ParagraphSpacingTracker()
        base = {"box": 15, "circle": 10, "note": 3}
        for text in ("□ 제목", "ㅇ 본문", "- 내용", "※ 참고", "ㅇ 복귀", "□ 복귀"):
            self.assertEqual(tracker.spacing_for(text, base, 100),
                             base.get({"□": "box", "ㅇ": "circle", "-": "dash", "※": "note"}[text[0]]))
        tracker.reset()
        self.assertEqual(tracker.spacing_for("ㅇ 새 문서", base), 10)
        self.assertIsNone(tracker.spacing_for("일반 문장", base))

    def test_user_base_values_and_percent_bounds(self):
        tracker = ParagraphSpacingTracker()
        base = {"box": 8, "circle": 6, "note": 4}
        tracker.spacing_for("* 참고", base)
        self.assertEqual(tracker.spacing_for("ㅇ 본문", base, 200), 12)
        with self.assertRaises(ValueError):
            tracker.spacing_for("□ 제목", base, 99)


if __name__ == "__main__":
    unittest.main()
