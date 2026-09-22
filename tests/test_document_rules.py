import unittest

from docfit_core.document_rules import ParagraphSpacingTracker, normalize_year_quotes


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
