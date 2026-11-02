"""쉬운 파일명 일괄변경 화면이 보내는 규칙을 실제 코어로 적용한 결과."""
import unittest
from datetime import datetime

from docfit_core.file_rename import Entry, apply_rules

TODAY = datetime(2026, 11, 3)


def rename(name, *rules):
    entry = Entry("1", "C:/t/" + name, 1, 0.0, 0.0)
    return apply_rules([entry], list(rules), today=TODAY)[0][0]


def add(text, position):
    return {"kind": "add", "text": text, "position": position, "sep": ""}


def date(fmt, position):
    return {"kind": "date", "source": "today", "format": fmt, "position": position, "sep": ""}


class SimpleRenameTests(unittest.TestCase):
    def test_prefix_goes_first(self):
        self.assertEqual(rename("보고서.hwpx", add("사진", "prefix")), "사진보고서.hwpx")

    def test_suffix_goes_before_extension(self):
        self.assertEqual(rename("보고서.hwpx", add("끝", "suffix")), "보고서끝.hwpx")

    def test_replace_changes_every_occurrence(self):
        rule = {"kind": "replace", "find": "만두", "to": "자장면"}
        self.assertEqual(rename("만두와 군만두.hwpx", rule), "자장면와 군자장면.hwpx")

    def test_all_options_together(self):
        rules = ({"kind": "replace", "find": "만두", "to": "자장면"}, add("사진", "prefix"), add("끝", "suffix"),
                 date("YYMMDD", "prefix"))
        self.assertEqual(rename("만두.jpg", *rules), "261103사진자장면끝.jpg")

    def test_date_formats(self):
        self.assertEqual(rename("보고서.hwpx", date("YYYY.MM.DD.", "prefix")), "2026.11.03.보고서.hwpx")
        self.assertEqual(rename("보고서.hwpx", date("YYYY.MM.DD", "suffix")), "보고서2026.11.03.hwpx")
        self.assertEqual(rename("보고서.hwpx", date("YYMMDD", "suffix")), "보고서261103.hwpx")


if __name__ == "__main__":
    unittest.main()
