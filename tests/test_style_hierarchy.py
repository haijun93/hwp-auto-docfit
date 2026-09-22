import unittest

from docfit_core.style_hierarchy import analyze_hierarchy, leading_marker, normalize_leading_dot


class StyleHierarchyTest(unittest.TestCase):
    def test_dot_markers_share_bullet_identity(self):
        for marker in ("•", "·", "‧", "∙", "⋅", "ㆍ", "●"):
            with self.subTest(marker=marker):
                self.assertEqual(leading_marker(f"{marker} 설명"), ("•", "부연설명"))
                self.assertEqual(normalize_leading_dot(f"  {marker} 설명"), "  • 설명")
        self.assertEqual(normalize_leading_dot("서울·경기"), "서울·경기")
        self.assertEqual(normalize_leading_dot("·붙은 문장"), "·붙은 문장")

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

    def test_explanations_after_subheading_are_optional(self):
        for explanations in ([], ["* 참고"], ["* 참고", "** 추가 설명"]):
            with self.subTest(explanations=explanations):
                texts = ["□ 소제목", *explanations, "ㅇ 본문"]
                records = [{"text": value, "left": 100, "indent": 0,
                            "font": "명조", "size_pt": 12} for value in texts]
                result = analyze_hierarchy(records)
                self.assertEqual(result["warnings"], [])
                self.assertTrue(result["page_policy"]["optional_explanations_after_subheading"])

    def test_subheading_still_requires_body_after_explanations(self):
        records = [{"text": value, "left": 100, "indent": 0,
                    "font": "명조", "size_pt": 12}
                   for value in ("□ 소제목", "* 참고", "□ 다음 소제목", "ㅇ 본문")]
        result = analyze_hierarchy(records)
        self.assertIn("1번째 3단계 아래에 4단계가 없습니다.", result["warnings"])

    def test_circled_marker_can_replace_three_roles(self):
        for anchor, expected, indent, size in (
                ("ㅇ 기준 본문", "본문", 100, 14),
                ("- 기준 내용", "내용", 200, 12),
                ("※ 기준 부연설명", "부연설명", 300, 10)):
            with self.subTest(expected=expected):
                records = [
                    {"text": "□ 소제목", "left": 0, "font": "명조", "size_pt": 16},
                    {"text": "ㅇ 본문", "left": 100, "font": "명조", "size_pt": 14},
                    {"text": anchor, "left": indent, "font": "명조", "size_pt": size},
                    {"text": "① 원문자", "left": indent, "font": "명조", "size_pt": size},
                ]
                result = analyze_hierarchy(records)
                self.assertEqual(result["role_sequence"][-1], expected)
                self.assertEqual(leading_marker("① 원문자"), ("①", ""))

    def test_circled_marker_without_style_anchor_requests_confirmation(self):
        records = [{"text": "① 항목", "left": 100, "font": "명조", "size_pt": 12}]
        result = analyze_hierarchy(records)
        self.assertEqual(result["role_sequence"], ["미분류"])
        self.assertTrue(any("원문자의 역할" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
