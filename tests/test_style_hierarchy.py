import unittest

from docfit_core.style_hierarchy import analyze_hierarchy, leading_marker


class StyleHierarchyTest(unittest.TestCase):
    def test_two_marker_systems(self):
        cases = {"Ⅰ 총괄": "중제목", "□ 사업": "소제목", "ㅇ 목적": "본문",
                 "- 실행": "내용", "** 참고": "부연설명", "가. 총괄": "중제목",
                 "1. 사업": "소제목", "1 사업": "소제목", "가) 목적": "본문", "1) 실행": "내용",
                 "(가) 참고": "부연설명", "• 추가": "부연설명"}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(leading_marker(text)[1], expected)

    def test_spacing_is_auxiliary_not_role_key(self):
        records = [
            {"text": "□ 첫째", "left": 100, "indent": 0, "font": "명조", "size_pt": 16, "prev_spacing": 100},
            {"text": "□ 둘째", "left": 100, "indent": 0, "font": "명조", "size_pt": 16, "prev_spacing": 1500},
            {"text": "ㅇ 본문", "left": 200, "indent": -20, "font": "고딕", "size_pt": 14, "prev_spacing": 0},
        ]
        result = analyze_hierarchy(records)
        subheading = next(s for s in result["styles"] if s["role"] == "소제목")
        self.assertEqual(subheading["count"], 2)
        self.assertEqual(subheading["prev_spacing_values"], [100, 1500])
        self.assertEqual(subheading["left_hwpunit"], 100)
        self.assertEqual(result["role_sequence"], ["소제목", "소제목", "본문"])


if __name__ == "__main__":
    unittest.main()
