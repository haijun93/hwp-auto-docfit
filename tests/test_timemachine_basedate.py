import unittest
from unittest.mock import Mock

from docfit_core.timemachine.basedate import extract_base_date
from docfit_core.timemachine.content_search import ContentSearchIndex
from docfit_core.timemachine.related import related_documents

CASES = [
    # (본문, 날짜, 정밀도)
    ("작성기준일: 2026. 9. 30.", "2026-09-30", "day"),
    ("작성 기준일 2026-09-30", "2026-09-30", "day"),
    ("기준일：2026년 9월 30일", "2026-09-30", "day"),
    ("기준일 2026/9/30", "2026-09-30", "day"),
    ("작 성 기 준 일 : 2026.9.30.", "2026-09-30", "day"),
    ("작성기준일 2026. 9. 30.(수)", "2026-09-30", "day"),
    ("작성기준일: ’26. 9. 30.", "2026-09-30", "day"),
    ("기준일자: 2026. 3. 31.", "2026-03-31", "day"),
    ("주요업무추진실적 (2026. 9. 30. 기준)", "2026-09-30", "day"),
    ("(2026.9.30.기준)", "2026-09-30", "day"),
    ("[2026. 6. 30. 현재]", "2026-06-30", "day"),
    ("2026. 9. 30. 기준 현황", "2026-09-30", "day"),
    ("2026년 9월 30일 현재", "2026-09-30", "day"),
    ("2026.9.30. 현재", "2026-09-30", "day"),
    ("기준일: 2024. 2. 29.", "2024-02-29", "day"),
    ("기준일: 2026. 9.", "2026-09-30", "month"),
    ("2026년 9월 기준", "2026-09-30", "month"),
    ("작성기준일 2026년 2월", "2026-02-28", "month"),
    ("2026년 3분기 주요업무추진실적", "2026-09-30", "quarter"),
    ("2026년도 3분기", "2026-09-30", "quarter"),
    ("2026년도 제3분기", "2026-09-30", "quarter"),
    ("2026년 3/4분기", "2026-09-30", "quarter"),
    ("2026년도 1/4분기 실적", "2026-03-31", "quarter"),
    ("2026 3Q 보고", "2026-09-30", "quarter"),
    ("2026년 제2사분기", "2026-06-30", "quarter"),
    ("2026년 4분기", "2026-12-31", "quarter"),
    ("2026년 2분기\n본문\n3/4분기 계획", "2026-06-30", "quarter"),
    ("2026년 업무 현황\n제3/4분기 실적", "2026-09-30", "quarter"),
    ("2026년 상반기 실적", "2026-06-30", "half"),
    ("2026년도 하반기", "2026-12-31", "half"),
    ("2026년도 결산 보고", "2026-12-31", "year"),
    ("2025년 연간 통계", "2025-12-31", "year"),
    # 명시 기준일이 기간 표기보다 우선
    ("2026년 3분기 실적\n작성기준일: 2026. 9. 15.", "2026-09-15", "day"),
    ("2026년 3분기 실적\n(2026. 9. 30. 기준)", "2026-09-30", "day"),
    ("2026년 상반기\n2026년 9월 기준", "2026-09-30", "month"),
    ("2026년 3분기 실적, 2026년도 결산", "2026-09-30", "quarter"),
    # 잘못된 날짜는 건너뛰고 다음 후보를 쓴다
    ("작성기준일: 2026. 2. 30.\n2026년 1분기", "2026-03-31", "quarter"),
]

NONE_CASES = [
    "", "기준일 없음", "기준일: 미정", "2026. 2. 30. 기준", "3/4분기 실적", "작성 일자 2026. 9. 30.",
    "2026년 2월 1일 회의", "기준일: 2026. 13. 1.", "분기별 실적",
]


class BaseDateExtractTests(unittest.TestCase):
    def test_cases(self):
        for text, expected, precision in CASES:
            with self.subTest(text=text):
                found = extract_base_date(text)
                self.assertIsNotNone(found)
                self.assertEqual((found["date"], found["precision"]), (expected, precision))
                self.assertTrue(found["evidence"])
                self.assertIn(found["basis"], ("explicit", "period"))

    def test_not_found(self):
        for text in NONE_CASES:
            with self.subTest(text=text):
                self.assertIsNone(extract_base_date(text))

    def test_non_string(self):
        self.assertIsNone(extract_base_date(None))

    def test_evidence_is_matched_text(self):
        found = extract_base_date("표지\n(2026. 9. 30. 기준)\n본문")
        self.assertEqual(found["evidence"], "(2026. 9. 30. 기준)")
        self.assertEqual(found["basis"], "explicit")
        self.assertEqual(extract_base_date("2026년 3분기")["basis"], "period")

    def test_case_count(self):
        self.assertGreaterEqual(len(CASES) + len(NONE_CASES), 30)


class RelatedBaseDateFieldsTests(unittest.TestCase):
    def test_fields_sorting_and_missing_flag(self):
        index = Mock(spec=ContentSearchIndex)
        sel = {"body": "주요업무추진실적 디지털전환 2026년 3분기", "reference_date": None}
        cands = [
            {"path": "/r/q1.txt", "name": "q1.txt", "reference_date": None,
             "body": "주요업무추진실적 디지털전환 2026년 1분기"},
            {"path": "/r/q2.txt", "name": "q2.txt", "reference_date": None,
             "body": "주요업무추진실적 디지털전환\n(2026. 6. 30. 기준)"},
            {"path": "/r/nodate.txt", "name": "nodate.txt", "reference_date": "2026-12-01",
             "body": "주요업무추진실적 디지털전환 자료"},
        ]
        index.related_candidates.return_value = (sel, cands)
        res = related_documents(index, "/r/sel.txt", roots=["/r"])
        self.assertEqual([i["name"] for i in res["items"]], ["q2.txt", "q1.txt", "nodate.txt"])
        q2, q1, nd = res["items"]
        self.assertEqual((q2["reference_date"], q2["reference_date_precision"], q2["reference_date_basis"]),
                         ("2026-06-30", "day", "explicit"))
        self.assertEqual(q2["reference_date_evidence"], "(2026. 6. 30. 기준)")
        self.assertEqual((q1["reference_date"], q1["reference_date_precision"]), ("2026-03-31", "quarter"))
        # 저장된 reference_date가 있어도 본문에 근거가 없으면 '못 찾음'으로 표시
        self.assertIsNone(nd["reference_date"])
        self.assertFalse(nd["reference_date_found"])
        self.assertIsNone(nd["reference_date_evidence"])
        self.assertTrue(nd["reference_date_note"])
        self.assertEqual(res["reference_date"], "2026-09-30")
        self.assertEqual(res["reference_date_evidence"], "2026년 3분기")

    def test_selected_missing(self):
        index = Mock(spec=ContentSearchIndex)
        index.related_candidates.return_value = (None, [])
        res = related_documents(index, "/r/x.txt")
        self.assertFalse(res["reference_date_found"])
        self.assertTrue(res["reference_date_note"])


if __name__ == "__main__":
    unittest.main()
