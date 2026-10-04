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
        self.assertIn("1번째 4단계 아래에 5단계가 없습니다.", result["warnings"])

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


class SixLevelHierarchyTest(unittest.TestCase):
    """계층 6단계(제목·장·중제목·소제목·ㅇ·-)와 문서 유형 A·B·C형(2026-10-04)."""

    def test_chapter_marker_is_level_two(self):
        from docfit_core.style_hierarchy import display_role
        for text in ("제1장 총칙", "2장 추진 계획", "제2편 개요", "Chapter 3 결론"):
            self.assertEqual(leading_marker(text)[1], "장", text)
        self.assertEqual(leading_marker("Ⅰ 추진 배경")[1], "중제목")
        self.assertEqual(leading_marker("1. 항목")[1], "소제목")
        self.assertEqual([display_role(r) for r in ("장", "중제목", "소제목", "본문", "내용")],
                         ["2단계", "3단계", "4단계", "5단계", "6단계"])

    def test_document_types(self):
        from docfit_core.style_hierarchy import document_type
        self.assertEqual(document_type(["제목", "장", "중제목", "소제목", "본문", "내용"]), "A형")
        self.assertEqual(document_type(["제목", "중제목", "소제목", "본문"]), "B형")
        self.assertEqual(document_type(["제목", "소제목", "본문"], has_midtitle_table=True), "B형")
        self.assertEqual(document_type(["제목", "소제목", "본문", "내용"]), "C형")
        self.assertEqual(document_type(["제목", "본문", "본문"]), "기타")       # 보도자료·답변자료 등

    def test_analysis_reports_document_type(self):
        records = [{"text": t, "left": 0, "indent": 0, "font": "f", "size_pt": 15}
                   for t in ("제1장 총칙", "Ⅰ 배경", "□ 소제목", "ㅇ 본문", "- 내용")]
        self.assertEqual(analyze_hierarchy(records)["document_type"], "A형")

    def test_chapter_paragraph_gets_chapter_rule(self):
        import runpy
        from pathlib import Path
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        find = ns['표준서식_기호규칙_찾기']
        g = find.__globals__
        self.assertEqual(find('제1장 총칙')[:4], ('(장)', 0, 'HY헤드라인M', 20))      # 기본 장 서식
        self.assertEqual(find('  2장 추진 계획')[0], '(장)')
        saved = g['표준서식_설정'].get('논리역할_규칙')
        try:
            g['표준서식_설정']['논리역할_규칙'] = {'장': ('(장)', 0, '맑은 고딕', 22, True, False)}
            self.assertEqual(find('제3장 결론')[2:4], ('맑은 고딕', 22))            # 예시에서 배운 장 서식
        finally:
            g['표준서식_설정']['논리역할_규칙'] = saved
        self.assertEqual(find('□ 소제목')[0], '□')
