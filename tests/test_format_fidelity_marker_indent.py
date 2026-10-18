from pathlib import Path
import runpy
import unittest


MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "format_fidelity_pc.py"))


class MarkerIndentFidelityTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
