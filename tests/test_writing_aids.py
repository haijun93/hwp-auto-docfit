"""벤치마킹 A·B: 라벨 입력, AI 프롬프트, 작성 보조 함수."""
from datetime import date
from decimal import Decimal
import unittest

from docfit_core import ai_prompts
from docfit_core import writing_aids as wa
from docfit_core.labeled_text import label_outline_text, looks_labeled, parse_labeled_text


class LabeledTextTest(unittest.TestCase):
    SAMPLE = ("제목: 직원 워크숍 계획\n상자: 협업 문화 조성을 위해 워크숍을 개최하고자 함\n"
              "네모: 행사 개요\n일시: 2025. 9. 26.(금) 14:00~17:00\n장소: 대회의실\n"
              "원: 전 직원 대상\n바: 부서별 신청\n당구: 일정은 추후 확정\n주석: 예산 포함\n"
              "표: 구분 | 금액\n표: 강사료 | 500,000원\n참고: 문의 총무과")

    def test_detects_label_format_only_with_hierarchy_labels(self):
        self.assertTrue(looks_labeled(self.SAMPLE))
        self.assertFalse(looks_labeled("일시: 오늘\n장소: 회의실"))  # 키-값만 있는 일반 글
        self.assertFalse(looks_labeled("# 제목\n- 항목"))

    def test_parses_blocks_and_key_values(self):
        blocks = parse_labeled_text(self.SAMPLE)
        kinds = [b["kind"] for b in blocks]
        self.assertEqual(kinds[:2], ["title", "box"])
        self.assertIn({"kind": "table", "rows": [["구분", "금액"], ["강사료", "500,000원"]]}, blocks)
        self.assertEqual(blocks[-1], {"kind": "ref", "text": "문의 총무과"})
        text = label_outline_text(self.SAMPLE)
        self.assertIn("□ 행사 개요", text)
        self.assertIn("ㅇ (일시) 2025. 9. 26.(금) 14:00~17:00", text)  # 시각의 콜론은 키로 보지 않음
        self.assertIn("- 부서별 신청", text)
        self.assertIn("※ 일정은 추후 확정", text)
        self.assertIn("* 예산 포함", text)

    def test_numbered_headings_and_continuation(self):
        text = label_outline_text("숫자소제목: 추진 배경\n원: 현황\n이어지는 문장\n숫자소제목: 추진 계획\n로마소제목: 총괄")
        self.assertIn("1. 추진 배경", text)
        self.assertIn("ㅇ 현황 이어지는 문장", text)
        self.assertIn("2. 추진 계획", text)
        self.assertIn("Ⅰ. 총괄", text)

    def test_ai_example_round_trips(self):
        self.assertTrue(looks_labeled(ai_prompts.LABEL_EXAMPLE))
        prompt = ai_prompts.build_prompt("행사 계획", "10월 체육대회")
        self.assertIn("10월 체육대회", prompt)
        self.assertIn("네모:", prompt)
        plain = ai_prompts.build_prompt("공문 어투로 바꾸기", "내일 회의함")
        self.assertNotIn("네모:", plain)


class AmountAndNumberTest(unittest.TestCase):
    def test_number_to_hangul(self):
        self.assertEqual(wa.number_to_hangul(1500000), "일백오십만")
        self.assertEqual(wa.number_to_hangul(1500000, full=False), "백오십만")
        self.assertEqual(wa.number_to_hangul(100010001), "일억일만일")
        self.assertEqual(wa.number_to_hangul(0), "영")

    def test_hangulize_amounts_skips_existing(self):
        self.assertEqual(wa.hangulize_amounts("예산 1,500,000원"), "예산 금1,500,000원(금일백오십만원)")
        already = "금1,000원(금일천원)"
        self.assertEqual(wa.hangulize_amounts(already), already)

    def test_commas_and_scaling(self):
        self.assertEqual(wa.add_commas("1234567원, 2025년"), "1,234,567원, 2025년")
        self.assertEqual(wa.remove_commas("1,234,567원"), "1234567원")
        self.assertEqual(wa.scale_numbers("1,500,000원", Decimal("0.001")), "1,500원")
        self.assertEqual(wa.scale_numbers("12", 1000), "12,000")


class DateTest(unittest.TestCase):
    def test_add_and_fix_weekdays(self):
        self.assertEqual(wa.add_weekdays("2025. 7. 25. 회의"), "2025. 7. 25.(금) 회의")
        self.assertEqual(wa.add_weekdays("’25. 7. 26.(월)"), "’25. 7. 26.(토)")
        self.assertEqual(wa.add_weekdays("2025-12-31"), "2025-12-31(수)")

    def test_generators(self):
        d = date(2025, 7, 25)
        self.assertEqual(wa.weekdays_in_month(d, 4), [date(2025, 7, x) for x in (4, 11, 18, 25)])
        self.assertEqual(wa.month_bounds(d, 6), (date(2026, 1, 1), date(2026, 1, 31)))
        self.assertEqual(wa.week_of(d, 1), (date(2025, 7, 28), date(2025, 8, 1)))
        self.assertEqual(wa.format_date(d, "short"), "’25. 7. 25.(금)")
        self.assertEqual(wa.days_between(date(2025, 7, 1), d, inclusive=True), 25)


class TableCalcTest(unittest.TestCase):
    ROWS = wa.parse_table("구분\t1월\t2월\n인건비\t1,000\t2,000\n운영비\t500\t700")

    def test_column_sum_average_row_sum(self):
        self.assertEqual(wa.calc_table(self.ROWS, "col_sum")[-1], ["합계", "1,500", "2,700"])
        self.assertEqual(wa.calc_table(self.ROWS, "col_avg")[-1], ["평균", "750", "1,350"])
        self.assertEqual([r[-1] for r in wa.calc_table(self.ROWS, "row_sum")], ["합계", "3,000", "1,200"])

    def test_ratio_and_pipe_tables(self):
        ratio = wa.calc_table(self.ROWS, "col_ratio")
        self.assertEqual(ratio[1][1], "1,000 (66.7%)")
        rows = wa.parse_table("| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertEqual(rows, [["a", "b"], ["1", "2"]])


class PersonalInfoAndNumberingTest(unittest.TestCase):
    def test_age_and_rrn(self):
        self.assertEqual(wa.international_age(date(1990, 12, 31), date(2025, 12, 30)), 34)
        self.assertEqual(wa.rrn_birth("030101-3123456"), (date(2003, 1, 1), "남"))
        self.assertEqual(wa.mask_rrn("900101-2123456"), "900101-2******")
        out = wa.ages_for_lines("홍길동 900101-2123456", date(2025, 7, 25))
        self.assertEqual(out, "홍길동 900101-2****** (만 35세)")
        self.assertNotIn("2123456", out)

    def test_renumber_and_roman(self):
        self.assertEqual(wa.renumber_lines("1. 가\n② 나\n\n다", "가."), "가. 가\n나. 나\n\n다. 다")
        self.assertEqual(wa.renumber_lines("a\nb", "Ⅰ."), "Ⅰ. a\nⅡ. b")
        self.assertEqual(wa.roman(14), "XIV")
        self.assertEqual(wa.circled(21), "㉑")


class ReplyDocumentTest(unittest.TestCase):
    def test_reply_title_and_body(self):
        self.assertEqual(wa.reply_title("(긴급) 민원 처리 현황 협조 요청"), "민원 처리 현황 자료 제출")
        self.assertEqual(wa.reply_title("교육 실적 자료 제출 요청"), "교육 실적 자료 제출")
        body = wa.reply_document("교육 실적 자료 제출 요청", "인재개발과", "인재개발과-12", "2025.7.1.",
                                 contact="홍길동, 02-123-4567")
        self.assertIn("1. 관련: 인재개발과 인재개발과-12(2025. 7. 1.) 「교육 실적 자료 제출 요청」", body)
        self.assertIn("교육 실적 자료를 붙임과 같이 제출합니다(문의: 홍길동, 02-123-4567).", body)
        self.assertTrue(body.endswith("붙임  교육 실적 자료 1부.  끝."))

    def test_josa(self):
        self.assertEqual(wa.josa("현황", "을", "를"), "현황을")
        self.assertEqual(wa.josa("자료", "을", "를"), "자료를")


if __name__ == "__main__":
    unittest.main()
