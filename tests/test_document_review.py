import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from docfit_core.document_review import _structure_issues, _visual_issues, review_document
from docfit_core.style_hierarchy import display_role, stored_role
from tests.test_style_profile import HEADER, SECTION


class DocumentReviewTest(unittest.TestCase):
    def test_stage_labels_keep_profile_roles_compatible(self):
        for internal, label in (("제목", "1단계"), ("중제목", "2단계"),
                                ("소제목", "3단계"), ("본문", "4단계"),
                                ("내용", "5단계"), ("부연설명", "부연설명")):
            self.assertEqual(display_role(internal), label)
            self.assertEqual(stored_role(label), internal)

    def _source(self, folder, section):
        path = Path(folder) / "review.hwpx"
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("Contents/header.xml", HEADER)
            archive.writestr("Contents/section0.xml", section)
        return path

    def test_read_only_outline_and_purpose(self):
        section = SECTION.replace("문서 제목".encode(), "□ 계획".encode()).replace(
            "기호 없이 작성된 일반 본문입니다.".encode(), "ㅇ 실행 방안".encode())
        with tempfile.TemporaryDirectory() as folder:
            source = self._source(folder, section)
            before = source.read_bytes()
            result = review_document(source, purpose="빠른 의사결정용", document_kind="계획서")
            self.assertEqual(source.read_bytes(), before)
        self.assertEqual(result["document_kind"], "계획서")
        self.assertEqual(result["body_count"], 2)
        self.assertEqual(result["outline"][0]["role"], "3단계")
        self.assertTrue(any(issue["category"] == "첫머리 검토" for issue in result["issues"]))
        self.assertTrue(any("목표·핵심 실행 방안·일정" in issue["message"] for issue in result["issues"]))

    def test_review_flags_are_suggestions_with_locations(self):
        section = SECTION.replace("문서 제목".encode(), "- 내용 추진 검토".encode()).replace(
            "기호 없이 작성된 일반 본문입니다.".encode(), "ㅇ 실행 방안".encode())
        with tempfile.TemporaryDirectory() as folder:
            result = review_document(self._source(folder, section))
        self.assertTrue(any(issue["category"] == "상위 항목 확인" for issue in result["issues"]))
        self.assertTrue(any(issue["category"] == "표현 명료성" and issue["severity"] == "선호 제안"
                            for issue in result["issues"]))
        self.assertTrue(all(issue["location"] and issue["context"] for issue in result["issues"]))

    def test_profile_style_is_review_reference(self):
        section = SECTION.replace("문서 제목".encode(), "□ 계획".encode())
        profile = {"style_hierarchy": {"styles": [{"role": "소제목", "marker": "□",
                   "font": "다른 글꼴", "size_pt": 16, "left_hwpunit": 0,
                   "first_line_hwpunit": 0, "prev_spacing_typical": 0}]}}
        with tempfile.TemporaryDirectory() as folder:
            result = review_document(self._source(folder, section), profile)
        self.assertTrue(any(issue["category"] == "서식 편차" and "글꼴" in issue["message"]
                            for issue in result["issues"]))

    def test_mixed_markers_and_missing_body_are_review_candidates(self):
        rows = [
            {"section": 1, "location": "1구역 본문 1번", "text": "□ 첫 소제목", "role": "소제목", "marker": "□"},
            {"section": 1, "location": "1구역 본문 2번", "text": "ㅇ 본문", "role": "본문", "marker": "ㅇ"},
            {"section": 1, "location": "1구역 본문 3번", "text": "1. 둘째 소제목", "role": "소제목", "marker": "1."},
        ]
        issues = _structure_issues(rows)
        self.assertTrue(any(item["category"] == "계층 기호 혼용" for item in issues))
        self.assertTrue(any(item["category"] == "하위 내용 확인" for item in issues))

    def test_excessive_bold_is_preference_not_error(self):
        rows = [{"section": 1, "location": f"1구역 본문 {index}번", "text": "ㅇ 본문",
                 "role": "본문", "marker": "ㅇ", "font": "명조", "size_pt": 12,
                 "bold": True, "color": None, "left": 0, "indent": 0,
                 "prev_spacing": 0, "align": None} for index in range(1, 5)]
        issues = _visual_issues(rows, [], None)
        self.assertTrue(any(item["category"] == "강조 밀도 확인" and item["severity"] == "선호 제안"
                            for item in issues))


if __name__ == "__main__":
    unittest.main()
