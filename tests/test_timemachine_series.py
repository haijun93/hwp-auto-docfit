"""정기 문서 계열 키 추출과 연관검색 series 필드 시험."""
import tempfile
import unittest
from pathlib import Path

from docfit_core.timemachine.content_search import ContentSearchIndex
from docfit_core.timemachine.related import related_documents
from docfit_core.timemachine.series import series_key


class SeriesKeyTests(unittest.TestCase):
    CASES = [
        ("2026년도 3분기 주요업무추진실적.hwpx", "주요업무추진실적", "quarter", 2026, 3, "2026Q3"),
        ("2026년 2분기 주요업무추진실적.hwp", "주요업무추진실적", "quarter", 2026, 2, "2026Q2"),
        ("2026년도 제1분기 주요업무추진실적", "주요업무추진실적", "quarter", 2026, 1, "2026Q1"),
        ("2025년도 4/4분기 주요업무추진실적", "주요업무추진실적", "quarter", 2025, 4, "2025Q4"),
        ("주요업무추진실적_2026Q3.docx", "주요업무추진실적", "quarter", 2026, 3, "2026Q3"),
        ("2026 Q1 부서 현황", "부서현황", "quarter", 2026, 1, "2026Q1"),
        ("2026년도 상반기 통계자료.xlsx", "통계자료", "half", 2026, 1, "2026H1"),
        ("2026년 하반기 통계자료", "통계자료", "half", 2026, 2, "2026H2"),
        ("2025년도 하반기 사업 현황", "사업현황", "half", 2025, 2, "2025H2"),
        ("2026년 7월 월간 업무보고.hwpx", "월간업무보고", "month", 2026, 7, "2026-07"),
        ("2026년 10월 월간 업무보고", "월간업무보고", "month", 2026, 10, "2026-10"),
        ("월간업무보고_2026.07.hwp", "월간업무보고", "month", 2026, 7, "2026-07"),
        ("월간업무보고_202611.hwp", "월간업무보고", "month", 2026, 11, "2026-11"),
        ("2026-03 월간 통계", "월간통계", "month", 2026, 3, "2026-03"),
        ("2026년도 사업 현황", "사업현황", "year", 2026, 2026, "2026"),
        ("2025년 연간 통계자료.xlsx", "연간통계자료", "year", 2025, 2025, "2025"),
        ("2024학년도 학사 현황", "학사현황", "year", 2024, 2024, "2024"),
        ("2026년 제3차 운영위원회 회의자료.hwpx", "운영위원회회의자료", "round", 2026, 3, "2026-3차"),
        ("제12차 정례 회의자료", "정례회의자료", "round", None, 12, "12차"),
        ("제2회 정례 회의자료.pdf", "정례회의자료", "round", None, 2, "2차"),
        ("제3차 주요업무추진실적", "주요업무추진실적", "round", None, 3, "3차"),
        ("2026년도 3분기 주요업무추진실적 (최종).hwpx", "주요업무추진실적", "quarter", 2026, 3, "2026Q3"),
        ("2026년도 3분기 주요업무추진실적_최종_v2.hwpx", "주요업무추진실적", "quarter", 2026, 3, "2026Q3"),
        ("2026년도 3분기 주요업무추진실적 - 사본.hwpx", "주요업무추진실적", "quarter", 2026, 3, "2026Q3"),
        ("2026년도 3분기 주요업무추진실적(1).hwpx", "주요업무추진실적", "quarter", 2026, 3, "2026Q3"),
        ("[마포구] 2026년도 3분기 주요업무추진실적", "마포구주요업무추진실적", "quarter", 2026, 3, "2026Q3"),
        ("C:\\Users\\a\\Desktop\\2026년 1분기 부서 현황.hwpx", "부서현황", "quarter", 2026, 1, "2026Q1"),
        ("/tmp/docs/2026년 1분기 부서 현황.hwpx", "부서현황", "quarter", 2026, 1, "2026Q1"),
        ("2026년도 3분기 주요업무추진실적 20261005.hwpx", "주요업무추진실적", "quarter", 2026, 3, "2026Q3"),
        ("2026년 제3분기 디지털전환 사업 추진실적", "디지털전환사업추진실적", "quarter", 2026, 3, "2026Q3"),
        ("3분기 업무보고", "업무보고", "quarter", None, 3, "Q3"),
        ("상반기 업무보고", "업무보고", "half", None, 1, "H1"),
        ("7월 업무보고", "업무보고", "month", None, 7, "07월"),
        ("주민센터 2026.3분기 현황", "주민센터현황", "quarter", 2026, 3, "2026Q3"),
    ]

    def test_extracts_series_and_period(self):
        for title, series, kind, year, value, label in self.CASES:
            with self.subTest(title=title):
                found = series_key(title)
                self.assertIsNotNone(found)
                self.assertEqual(found["series"], series)
                period = found["period"]
                self.assertEqual((period["kind"], period["year"], period["value"], period["label"]),
                                 (kind, year, value, label))

    def test_same_series_across_periods(self):
        keys = {series_key(f"2026년도 {q}분기 주요업무추진실적.hwpx")["series"] for q in (1, 2, 3, 4)}
        self.assertEqual(keys, {"주요업무추진실적"})
        a = series_key("2025년도 4분기 주요업무추진실적")["period"]["ordinal"]
        b = series_key("2026년도 1분기 주요업무추진실적")["period"]["ordinal"]
        self.assertLess(a, b)

    def test_no_period_or_empty_returns_none(self):
        for title in ("", None, "회의록.hwp", "2026년도 3분기", "제3차", "여행 기록"):
            with self.subTest(title=title):
                self.assertIsNone(series_key(title))

    def test_ordinal_orders_mixed_kinds(self):
        half = series_key("2026년 상반기 통계자료")["period"]["ordinal"]
        quarter = series_key("2026년 3분기 통계자료")["period"]["ordinal"]
        self.assertLess(half, quarter)


class SeriesRelatedTests(unittest.TestCase):
    def test_related_series_groups_by_base_date(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = ContentSearchIndex(root / "content.sqlite")
            try:
                docs = {
                    "2026년도 3분기 주요업무추진실적.txt": "작성 기준일: 2026. 9. 30.\n디지털전환",
                    "2026년도 2분기 주요업무추진실적.txt": "작성 기준일: 2026. 6. 30.\n디지털전환",
                    "2026년도 1분기 주요업무추진실적.txt": "디지털전환",
                    "2026년도 4분기 주요업무추진실적.txt": "작성 기준일: 2026. 12. 31.\n디지털전환",
                    "2026년도 3분기 통계자료.txt": "작성 기준일: 2026. 9. 30.\n통계",
                }
                for name, body in docs.items():
                    (root / name).write_text(body, encoding="utf-8")
                    self.assertTrue(index.index_file(root / name)["indexed"])
                result = related_documents(index, str(root / "2026년도 3분기 주요업무추진실적.txt"), roots=[str(root)])
                series = result["series"]
                self.assertEqual(series["key"], "주요업무추진실적")
                self.assertEqual(series["period"]["label"], "2026Q3")
                self.assertEqual([i["period_label"] for i in series["previous"]], ["2026Q2", "2026Q1"][:1])
                self.assertEqual([i["period_label"] for i in series["next"]], ["2026Q4"])
                self.assertEqual([i["period_label"] for i in series["undated"]], ["2026Q1"])
                self.assertEqual(series["total"], 3)
                self.assertNotIn("통계", " ".join(i["name"] for g in ("previous", "next", "undated") for i in series[g]))
            finally:
                index.close()

    def test_series_none_without_period_and_respects_exclusion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = ContentSearchIndex(root / "content.sqlite")
            try:
                for name, body in (("메모.txt", "여행"), ("2026년 1분기 보고서.txt", "a"), ("2026년 2분기 보고서.txt", "b")):
                    (root / name).write_text(body, encoding="utf-8")
                    index.index_file(root / name)
                self.assertIsNone(related_documents(index, str(root / "메모.txt"), roots=[str(root)])["series"])
                a, b = str(root / "2026년 1분기 보고서.txt"), str(root / "2026년 2분기 보고서.txt")
                self.assertEqual(related_documents(index, a, roots=[str(root)])["series"]["total"], 1)
                gone = related_documents(index, a, roots=[str(root)], excluded_pairs=[(a, b)])["series"]
                self.assertEqual(gone["total"], 0)
            finally:
                index.close()


if __name__ == "__main__":
    unittest.main()
