import unittest

from docfit_core.pasted_text import clean_pasted_text


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


if __name__ == "__main__":
    unittest.main()
