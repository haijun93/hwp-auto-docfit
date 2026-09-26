"""숫자 데이터 일치 검사(TODO 4순위): 본문 수치가 같은 문서의 표에 있는지 대조."""
import unittest
from types import SimpleNamespace

from docfit_core.number_check import 본문_수치, 숫자_대조, 숫자_정규화


def doc(*blocks):
    return SimpleNamespace(blocks=[SimpleNamespace(type=t, text=x if t == "paragraph" else "",
                                                   rows=x if t == "table" else None) for t, x in blocks])


TABLE = [["구분", "예산(억원)", "비율"], ["상품권", "218", "45.5%"], ["주차", "1,234", "12.30"],
         ["합계", "1,452", "57.8"]]


class NumberCheckTest(unittest.TestCase):
    def test_extracts_only_data_like_quantities(self):
        text = "2026. 9. 24. 예산 218억원(45.5%), 참여 1,234명, 3차 회의, 9월 개최"
        self.assertEqual(본문_수치(text), [("218", "억원"), ("45.5", "%"), ("1,234", "명")])
        self.assertEqual(숫자_정규화("1,234.50"), "1234.5")

    def test_body_numbers_missing_from_tables_need_review(self):
        result = 숫자_대조(doc(("paragraph", "ㅇ 상품권 218억원, 주차 1,234건, 합계 1,500억원"),
                           ("table", TABLE)))
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["checked"], 2)      # 표에 '건'이 없어 1,234건은 대조 안 함
        self.assertEqual([item["text"] for item in result["review"]], ["'1,500억원'"])
        self.assertEqual(result["issues"], [])       # 실패가 아니라 확인 필요만

    def test_small_numbers_are_matched_by_unit_not_anywhere(self):
        # 표에 11(행 번호)이 있어도 '11대'라는 칸이 없으면 본문 '11대'는 확인 필요.
        table = [["번호", "차종/대수", "비고"], ["11", "카운티 4대", "대부분 채택"],
                 ["12", "버스 3대", "2026. 9. 1."]]
        result = 숫자_대조(doc(("paragraph", "※ (11대 중 1대) 교체 예정"), ("table", table)))
        self.assertEqual([item["text"] for item in result["review"]], ["'11대'", "'1대'"])
        result = 숫자_대조(doc(("paragraph", "※ (4대 중 3대) 교체 예정"), ("table", table)))
        self.assertEqual(result["review"], [])

    def test_documents_without_numeric_tables_are_skipped(self):
        result = 숫자_대조(doc(("paragraph", "예산 218억원"), ("table", [["구분", "내용"]])))
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["review"], [])


if __name__ == "__main__":
    unittest.main()
