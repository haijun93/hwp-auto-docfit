from pathlib import Path
import re
import unittest

from docfit_core.ai_answer import ai_answer_to_outline_text, looks_like_ai_answer
from docfit_core.pasted_text import clean_pasted_text, outline_pasted_text


SOURCE = Path(__file__).parent / "fixtures" / "gemini_bench_reply.txt"
EXPECTED = [
    "안녕하십니까.",
    "귀하께서 제기하신 민원을 확인한 결과, 야외 벤치 내 주취객 방지를 위한 벤치 철거 요청으로 이해됩니다.",
    "벤치 이용에 따른 불편을 드린 점에 대해 유감스럽게 생각하며, 요청하신 사항과 관련하여 우리 구에서는 벤치를 전면 철거하는 대신 구민과 방문객의 휴식 공간 기능을 유지하면서 주취객이 눕지 못하도록 '야외 의자 눕기방지용 장치(팔걸이/분리대 등)' 부착을 추진하고 있습니다.",
    "현재 관련 작업 진행을 위해 업체 선정 및 세부 작업 일정을 조정하고 있으며, 신속히 정비가 완료될 수 있도록 최선을 다하겠습니다.",
    "마포구에 애정을 갖고 의견을 보내주신 귀하께 감사드리며, 이와 관련하여 더 궁금하신 사항은 아래 담당자에게 문의하시면 성심껏 답변드리도록 하겠습니다. 항상 건강하고 행복이 함께 하시기를 진심으로 기원합니다.",
    "감사합니다.",
]


class GeminiPasteCleanupTests(unittest.TestCase):
    def test_actual_reply_preserves_all_six_paragraphs_in_each_route(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertTrue(looks_like_ai_answer(source))
        for convert in (clean_pasted_text, outline_pasted_text, ai_answer_to_outline_text):
            with self.subTest(route=convert.__name__):
                result = convert(source)
                paragraphs = [re.sub(r"^※ ", "", line) for line in result.splitlines() if line]
                self.assertEqual(paragraphs, EXPECTED)
                for residue in ("&gt;", ">", "*", "[2]", "\u200b"):
                    self.assertNotIn(residue, result)

    def test_decoded_numeric_and_nested_quote_markers_are_removed(self):
        for marker in (">", "&gt;", "&#62;", "&gt; &gt;"):
            for convert in (clean_pasted_text, outline_pasted_text, ai_answer_to_outline_text):
                with self.subTest(marker=marker, route=convert.__name__):
                    result = convert(f"{marker} **감사합니다**[2]**.**")
                    self.assertEqual(result.removeprefix("※ "), "감사합니다.")

    def test_adjacent_cited_emphasis_does_not_leave_stars_or_add_spaces(self):
        for source in ("**문의하겠습니다**[2]**. 항상 건강하시기를 기원합니다**[2]**.**",
                       "***첫 문장***[2]***. 다음 문장***[4]***.***",
                       "__감사합니다__[2]__.__"):
            for convert in (clean_pasted_text, ai_answer_to_outline_text):
                with self.subTest(source=source, route=convert.__name__):
                    result = convert(source)
                    self.assertNotRegex(result, r"[*_]|\[\d+\]|\u200b")
                    self.assertNotIn(" .", result)
        self.assertEqual(clean_pasted_text("***첫 문장***[2]***. 다음 문장***[4]***.***"),
                         "첫 문장. 다음 문장.")

    def test_beta1_escaped_spaced_bold_and_hex_entities(self):
        source = r"\*\* 안녕하십니까.\*\*" + "\n\n&#x20;  " + r"\*\* 2026년 10월 13&#xC77C;**"
        expected = "안녕하십니까.\n\n2026년 10월 13일"
        self.assertEqual(clean_pasted_text(source), expected)
        for convert in (outline_pasted_text, ai_answer_to_outline_text):
            result = convert(source)
            for residue in ("*", "\\", "&#", "&gt;"):
                self.assertNotIn(residue, result)
            self.assertIn("안녕하십니까.", result)
            self.assertIn("2026년 10월 13일", result)

    def test_meaningful_comparisons_numbers_brackets_and_punctuation_are_preserved(self):
        source = "검토: 3 &gt; 2, 2 * 3 = 6. [별표 21의2] '팔걸이/분리대 등'(2026. 10. 13.)"
        expected = "검토: 3 > 2, 2 * 3 = 6. [별표 21의2] '팔걸이/분리대 등'(2026. 10. 13.)"
        self.assertEqual(clean_pasted_text(source), expected)


if __name__ == "__main__":
    unittest.main()
