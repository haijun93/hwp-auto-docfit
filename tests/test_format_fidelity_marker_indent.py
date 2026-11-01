from pathlib import Path
import runpy
import unittest


MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "format_fidelity_pc.py"))


class MarkerIndentFidelityTest(unittest.TestCase):
    def test_leading_indentation_is_not_normalized_away(self):
        original = ("P", "      2. 끝.", (), (((), "      2. 끝."),), 1)
        result = ("P", "2. 끝.", (), (((), "2. 끝."),), 1)
        self.assertNotEqual(MODULE["_normalized"](original, 1), MODULE["_normalized"](result, 1))
        self.assertEqual(MODULE["_paragraph_key_text"](original[1]),
                         MODULE["_paragraph_key_text"](result[1]))

    def test_single_space_after_item_marker_is_separately_counted(self):
        self.assertEqual(MODULE["_marker_space_rule_pair"]("ㅇ「제목」", "ㅇ 「제목」"), ("ㅇ", 1))
        self.assertIsNone(MODULE["_marker_space_rule_pair"]("ㅇ  「제목」", "ㅇ 「제목」"))

    def test_marker_space_rule_is_shown_without_hiding_mismatch(self):
        import tempfile

        original = ("P", "ㅇ「제목」", (), (((), "ㅇ「제목」"),), 2)
        result = ("P", "ㅇ 「제목」", (), (((), "ㅇ 「제목」"),), 2)
        compare = MODULE["compare"]
        MODULE["compare"] = lambda *_: _compare_rule_fixture(original, result)
        try:
            count, lines = MODULE["compare"]("source", "target")
        finally:
            MODULE["compare"] = compare
        self.assertEqual(count, 1)
        self.assertTrue(any("공백 1개 1건" in line and "불일치 수 포함" in line for line in lines))

    def test_one_line_marker_indent_is_part_of_format_comparison(self):
        paragraph = ("P", "□ 추진 배경", (("intent", -2400), ("left", 2400)), (((), "□ 추진 배경"),), 1)
        actual = dict(MODULE["_normalized"](paragraph, 1)[2])
        self.assertEqual(actual["intent"], -2400)
        self.assertEqual(actual["left"], 2400)

    def test_one_line_marker_indent_difference_is_not_reported_as_hand_tweak(self):
        original = ("P", "ㅇ 항목", (("intent", -2400),), (((), "ㅇ 항목"),), 1)
        result = ("P", "ㅇ 항목", (("intent", 0),), (((), "ㅇ 항목"),), 1)
        excluded = MODULE["_excluded"](original, result)
        self.assertNotIn("한 줄 문단 내어쓰기", excluded)

    def test_regular_one_line_paragraph_keeps_existing_exception(self):
        regular = ("P", "일반 문장", (("intent", -2400),), (((), "일반 문장"),), 1)
        self.assertNotIn("intent", dict(MODULE["_normalized"](regular, 1)[2]))
        self.assertIn("한 줄 문단 내어쓰기", MODULE["_excluded"](
            regular, ("P", "일반 문장", (("intent", 0),), (((), "일반 문장"),), 1)))


def _compare_rule_fixture(original, result):
    pair = MODULE["_marker_space_rule_pair"](original[1], result[1])
    return 1, ["항목 수 원본 1 / 결과 1",
               f"항목기호 뒤 공백 규칙 적용(별도 계측, 불일치 수 포함): {pair[0]!r} 뒤 공백 {pair[1]}개 1건",
               "불일치 1"]


if __name__ == "__main__":
    unittest.main()
