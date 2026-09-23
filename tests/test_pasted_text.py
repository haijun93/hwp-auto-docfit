import unittest

from docfit_core.pasted_text import clean_pasted_text, outline_pasted_text


class CleanPastedTextTest(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(clean_pasted_text(""), "")
        self.assertEqual(clean_pasted_text("   \n  \n "), "")

    def test_wrapped_sentences_are_rejoined_into_one_paragraph(self):
        text = "안녕하세요. 오늘은 날씨가\n좋습니다. 저는 산책을\n다녀왔습니다."
        self.assertEqual(clean_pasted_text(text),
                          "안녕하세요. 오늘은 날씨가 좋습니다. 저는 산책을 다녀왔습니다.")

    def test_blank_line_keeps_paragraphs_separate(self):
        text = "첫 번째 문단입니다.\n\n두 번째 문단입니다."
        self.assertEqual(clean_pasted_text(text),
                          "첫 번째 문단입니다.\n\n두 번째 문단입니다.")

    def test_excess_blank_lines_collapse_to_one(self):
        text = "문단 하나.\n\n\n\n\n문단 둘."
        self.assertEqual(clean_pasted_text(text), "문단 하나.\n\n문단 둘.")

    def test_heading_markers_are_stripped_and_isolated(self):
        text = "## 결론\n본문 내용입니다."
        self.assertEqual(clean_pasted_text(text), "결론\n\n본문 내용입니다.")

    def test_hash_without_space_is_not_a_heading(self):
        text = "이건 #해시태그 입니다."
        self.assertEqual(clean_pasted_text(text), "이건 #해시태그 입니다.")

    def test_bullet_markers_are_normalized(self):
        text = "다음과 같습니다.\n* 첫째 항목\n- 둘째 항목\n•셋째 항목"
        self.assertEqual(clean_pasted_text(text),
                          "다음과 같습니다.\n\n- 첫째 항목\n\n- 둘째 항목\n\n- 셋째 항목")

    def test_numbered_and_circled_markers_get_a_following_space(self):
        text = "1.첫 단계\n2) 둘째 단계\n①셋째 단계"
        self.assertEqual(clean_pasted_text(text),
                          "1. 첫 단계\n\n2) 둘째 단계\n\n① 셋째 단계")

    def test_numbered_marker_without_space_is_still_detected(self):
        text = "안내드립니다.\n1.문서를 연다\n2.서식을 적용한다"
        self.assertEqual(clean_pasted_text(text),
                          "안내드립니다.\n\n1. 문서를 연다\n\n2. 서식을 적용한다")

    def test_decimal_number_is_not_treated_as_a_list_marker(self):
        text = "원주율은 3.14 정도입니다."
        self.assertEqual(clean_pasted_text(text), "원주율은 3.14 정도입니다.")

    def test_bullet_glued_to_previous_sentence_is_split_out(self):
        text = "요약하면 다음과 같습니다. - 첫째 항목입니다. - 둘째 항목입니다."
        self.assertEqual(clean_pasted_text(text),
                          "요약하면 다음과 같습니다.\n\n- 첫째 항목입니다.\n\n- 둘째 항목입니다.")

    def test_bold_and_italic_markers_are_removed(self):
        text = "이것은 **매우 중요**하고 *조금* 강조된 내용입니다."
        self.assertEqual(clean_pasted_text(text),
                          "이것은 매우 중요하고 조금 강조된 내용입니다.")

    def test_italic_asterisk_is_not_confused_with_a_bullet(self):
        text = "*이것은 강조된 문장입니다.*"
        self.assertEqual(clean_pasted_text(text), "이것은 강조된 문장입니다.")

    def test_inline_and_fenced_code_are_stripped_of_markers(self):
        text = "명령어는 `pip install`을 사용하세요.\n\n```python\nprint('hi')\n```"
        self.assertEqual(clean_pasted_text(text),
                          "명령어는 pip install을 사용하세요.\n\nprint('hi')")

    def test_horizontal_rule_becomes_a_paragraph_break(self):
        text = "위 문단.\n---\n아래 문단."
        self.assertEqual(clean_pasted_text(text), "위 문단.\n\n아래 문단.")

    def test_blockquote_marker_is_stripped(self):
        text = "> 인용된 문장입니다."
        self.assertEqual(clean_pasted_text(text), "인용된 문장입니다.")

    def test_markdown_link_keeps_visible_text_only(self):
        text = "자세한 내용은 [공식 문서](https://example.com/docs)를 참고하세요."
        self.assertEqual(clean_pasted_text(text),
                          "자세한 내용은 공식 문서를 참고하세요.")

    def test_markdown_image_keeps_alt_text_only(self):
        text = "다음 그림을 보세요. ![설명 텍스트](https://example.com/a.png)"
        self.assertEqual(clean_pasted_text(text), "다음 그림을 보세요. 설명 텍스트")

    def test_table_separator_row_is_dropped_and_rows_flattened(self):
        text = "| 이름 | 나이 |\n|---|---|\n| 홍길동 | 20 |"
        self.assertEqual(clean_pasted_text(text), "이름 나이\n\n홍길동 20")

    def test_citation_tags_are_removed(self):
        text = "이 내용은 사실입니다【6:0†source】."
        self.assertEqual(clean_pasted_text(text), "이 내용은 사실입니다.")

    def test_invisible_characters_are_stripped(self):
        text = "안녕​하세요 반갑습니다﻿."
        self.assertEqual(clean_pasted_text(text), "안녕하세요 반갑습니다.")

    def test_repeated_internal_spaces_collapse(self):
        text = "이것은    여러    공백이   있는   문장입니다."
        self.assertEqual(clean_pasted_text(text), "이것은 여러 공백이 있는 문장입니다.")

    def test_numeric_citation_markers_are_removed(self):
        text = "매수자가 의무를 승계하게 됩니다[2][4]. 보조금을 반납해야 합니다[1]."
        self.assertEqual(clean_pasted_text(text),
                          "매수자가 의무를 승계하게 됩니다. 보조금을 반납해야 합니다.")

    def test_bracket_reference_with_text_is_kept(self):
        text = "「대기환경보전법 시행규칙」 제79조의4 및 [별표 21의2] (보조금 회수기준)"
        self.assertEqual(clean_pasted_text(text), text)

    def test_escaped_bold_and_tilde_are_unescaped_then_bold_stripped(self):
        text = r"보조금 회수요율은 \*\*70%\~20%\*\*입니다."
        self.assertEqual(clean_pasted_text(text), "보조금 회수요율은 70%~20%입니다.")

    def test_gemini_style_nested_bullets_with_citations_are_flattened(self):
        text = (
            "* **회수요율 적용 (일반 말소 기준)**:\n"
            "  * 3개월 미만 70% \\~ 21개월 이상 24개월 미만 20%\n"
            "  * **24개월(2년) 이상 경과 시 회수요율 0%** (보조금 반환 의무 완전히 소멸)[4]."
        )
        expected = (
            "- 회수요율 적용 (일반 말소 기준):\n\n"
            "- 3개월 미만 70% ~ 21개월 이상 24개월 미만 20%\n\n"
            "- 24개월(2년) 이상 경과 시 회수요율 0% (보조금 반환 의무 완전히 소멸)."
        )
        self.assertEqual(clean_pasted_text(text), expected)

    def test_realistic_llm_answer_end_to_end(self):
        text = (
            "## 요약\n"
            "아래는 핵심\n"
            "내용입니다.\n"
            "\n"
            "### 절차\n"
            "1.문서를 연다\n"
            "2. 서식을 적용한다\n"
            "- 자간을 조정한다\n"
            "- **결과**를 저장한다\n"
            "\n"
            "---\n"
            "\n"
            "자세한 내용은 [가이드](https://example.com)를 참고하세요."
        )
        expected = (
            "요약\n\n"
            "아래는 핵심 내용입니다.\n\n"
            "절차\n\n"
            "1. 문서를 연다\n\n"
            "2. 서식을 적용한다\n\n"
            "- 자간을 조정한다\n\n"
            "- 결과를 저장한다\n\n"
            "자세한 내용은 가이드를 참고하세요."
        )
        self.assertEqual(clean_pasted_text(text), expected)


class OutlinePastedTextTest(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(outline_pasted_text(""), "")
        self.assertEqual(outline_pasted_text("   \n  \n "), "")

    def test_heading_without_number_gets_box_marker(self):
        text = "## 요약\n본문 내용입니다."
        self.assertEqual(outline_pasted_text(text), "ㅁ 요약\n본문 내용입니다.")

    def test_heading_with_existing_number_keeps_it_as_is(self):
        text = "### 1. 법적 근거\n* 첫째 항목"
        self.assertEqual(outline_pasted_text(text), "1. 법적 근거\nㅇ 첫째 항목")

    def test_bullet_depth_maps_to_o_dash_dot_tiers(self):
        text = "* 최상위 항목\n  * 두 칸 들여쓰기\n    * 네 칸 들여쓰기\n      * 여섯 칸도 점으로 묶임"
        self.assertEqual(
            outline_pasted_text(text),
            "ㅇ 최상위 항목\n- 두 칸 들여쓰기\n• 네 칸 들여쓰기\n• 여섯 칸도 점으로 묶임",
        )

    def test_blank_line_before_each_new_level1_section_only(self):
        text = "# 하나\n* 항목 A\n# 둘\n* 항목 B"
        self.assertEqual(outline_pasted_text(text), "ㅁ 하나\nㅇ 항목 A\n\nㅁ 둘\nㅇ 항목 B")

    def test_bullet_is_self_contained_and_does_not_absorb_the_next_plain_line(self):
        # clean_pasted_text와 마찬가지로 글머리 기호 줄은 그 자체로 완결되며,
        # 기호 없는 다음 줄은 별도의 일반 문단으로 남는다(항목에 흡수되지 않음).
        text = "* 첫째 항목\n뒤이은 일반 문장입니다."
        self.assertEqual(outline_pasted_text(text), "ㅇ 첫째 항목\n뒤이은 일반 문장입니다.")

    def test_wrapped_plain_sentence_across_lines_is_rejoined(self):
        text = "기호 없는 문장이 줄바꿈으로\n끊겨 있습니다."
        self.assertEqual(outline_pasted_text(text), "기호 없는 문장이 줄바꿈으로 끊겨 있습니다.")

    def test_horizontal_rule_between_sections_is_dropped(self):
        text = "# 하나\n* 항목\n---\n# 둘\n* 항목2"
        self.assertEqual(outline_pasted_text(text), "ㅁ 하나\nㅇ 항목\n\nㅁ 둘\nㅇ 항목2")

    def test_gemini_legal_answer_end_to_end(self):
        text = (
            "### **1\\. 법정 의무운행기간(2년)의 법적 근거**\n"
            "\n"
            "* **「대기환경보전법 시행규칙」 제79조의4 제1항**: 보조금을 지원받은 전기자동차 "
            "구매자는 최초 등록일을 기준으로 **최소 2년(24개월)의 법정 의무운행기간**을 "
            "준수해야 합니다[1][2].\n"
            "* **환경부 「전기자동차 보급사업 보조금 업무처리지침」 (5-3\\. 의무운행기간)**: "
            "전기차를 구매하여 신규 등록한 날부터 **2년간의 의무운행기간**을 설정하고 이에 "
            "따른 사후관리를 규정하고 있습니다[1][2].\n"
            "\n---\n\n"
            "### **2\\. 매각 제한 및 보조금 회수·환수의 법적 근거**\n"
            "\n"
            "* **「대기환경보전법」 제58조 (저공해자동차의 운행 등)**: 국가 및 지방자치단체가 "
            "저공해자동차(전기차 등) 구매자에게 지급하는 보조금의 지원, 의무 이행 및 환수에 "
            "관한 근거를 제공합니다[3].\n"
            "* **「대기환경보전법 시행규칙」 제79조의4 및 [별표 21의2] (보조금 회수기준)**:\n"
            "  * **중고 매도 시 의무 승계**: 의무운행기간(2년) 내에 차량을 제3자에게 "
            "매도(매각)하는 것은 가능하나, **매수자가 잔여 의무운행기간 준수 의무를 그대로 "
            "승계**하게 됩니다[2][4].\n"
            "  * **등록말소(폐차·수출 등) 시 사전 승인 및 회수**: 의무운행기간 내에 폐차나 "
            "말소등록을 하려면 지자체 등 보조사업자의 사전 승인을 받아야 하며, 사용 기간에 "
            "미달한 경우 \\*\\*[별표 21의2]의 운행기간별 보조금 회수요율(70%\\~20%)\\*\\*에 "
            "따라 지급된 보조금(국비+지방비)을 회수 및 반납해야 합니다[1].\n"
            "  * **회수요율 적용 (일반 말소 기준)**:\n"
            "    * 3개월 미만 70% \\~ 21개월 이상 24개월 미만 20%\n"
            "    * **24개월(2년) 이상 경과 시 회수요율 0%** (보조금 반환 의무 완전히 "
            "소멸)[4].\n"
            "* **전기화물차의 특수 제한**: 보조금을 받아 구매한 전기화물차를 최초 "
            "등록일로부터 1년 이내에 1만 km 이상 운행하지 않고 판매하는 경우 지급된 "
            "보조금의 **30%를 회수**합니다"
        )
        expected = (
            "1. 법정 의무운행기간(2년)의 법적 근거\n"
            "ㅇ 「대기환경보전법 시행규칙」 제79조의4 제1항: 보조금을 지원받은 전기자동차 "
            "구매자는 최초 등록일을 기준으로 최소 2년(24개월)의 법정 의무운행기간을 준수해야 "
            "합니다.\n"
            "ㅇ 환경부 「전기자동차 보급사업 보조금 업무처리지침」 (5-3. 의무운행기간): 전기차를 "
            "구매하여 신규 등록한 날부터 2년간의 의무운행기간을 설정하고 이에 따른 사후관리를 "
            "규정하고 있습니다.\n"
            "\n"
            "2. 매각 제한 및 보조금 회수·환수의 법적 근거\n"
            "ㅇ 「대기환경보전법」 제58조 (저공해자동차의 운행 등): 국가 및 지방자치단체가 "
            "저공해자동차(전기차 등) 구매자에게 지급하는 보조금의 지원, 의무 이행 및 환수에 "
            "관한 근거를 제공합니다.\n"
            "ㅇ 「대기환경보전법 시행규칙」 제79조의4 및 [별표 21의2] (보조금 회수기준):\n"
            "- 중고 매도 시 의무 승계: 의무운행기간(2년) 내에 차량을 제3자에게 매도(매각)하는 "
            "것은 가능하나, 매수자가 잔여 의무운행기간 준수 의무를 그대로 승계하게 됩니다.\n"
            "- 등록말소(폐차·수출 등) 시 사전 승인 및 회수: 의무운행기간 내에 폐차나 "
            "말소등록을 하려면 지자체 등 보조사업자의 사전 승인을 받아야 하며, 사용 기간에 "
            "미달한 경우 [별표 21의2]의 운행기간별 보조금 회수요율(70%~20%)에 따라 지급된 "
            "보조금(국비+지방비)을 회수 및 반납해야 합니다.\n"
            "- 회수요율 적용 (일반 말소 기준):\n"
            "• 3개월 미만 70% ~ 21개월 이상 24개월 미만 20%\n"
            "• 24개월(2년) 이상 경과 시 회수요율 0% (보조금 반환 의무 완전히 소멸).\n"
            "ㅇ 전기화물차의 특수 제한: 보조금을 받아 구매한 전기화물차를 최초 등록일로부터 "
            "1년 이내에 1만 km 이상 운행하지 않고 판매하는 경우 지급된 보조금의 30%를 "
            "회수합니다"
        )
        self.assertEqual(outline_pasted_text(text), expected)


if __name__ == "__main__":
    unittest.main()
