import unittest

from docfit_core.text_table import classify_line, find_box_tables, parse_box_table

SAMPLE = [
    "┌──────────┬──────────────────────────────────────┐",
    "│ 구  분   │ 내  용                               │",
    "├──────────┼──────────────────────────────────────┤",
    "│ 추진 방향│ 기술 발전 차단 후 함대 도착 시 일괄 점령*│",
    "│ 소요 기간│ 함대 이동에 약 450년 소요 예상        │",
    "│ 투입 규모│ 함선 2,000여 척                       │",
    "│ 핵심 수단│ 지자, 함대, 지구 내 협력 세력         │",
    "└──────────┴──────────────────────────────────────┘",
]


class ClassifyLineTest(unittest.TestCase):
    def test_border_lines(self):
        self.assertEqual(classify_line("┌──────────┬──────┐"), "border")
        self.assertEqual(classify_line("├──────────┼──────┤"), "border")
        self.assertEqual(classify_line("└──────────┴──────┘"), "border")

    def test_content_line(self):
        self.assertEqual(classify_line("│ 구  분   │ 내  용 │"), "content")

    def test_ordinary_text_is_other(self):
        self.assertEqual(classify_line("ㅇ 이것은 그냥 본문 문장입니다."), "other")
        self.assertEqual(classify_line(""), "other")
        self.assertEqual(classify_line("   "), "other")

    def test_single_pipe_is_not_content(self):
        # 세로 막대가 한 번만 나오면(예: 수식이나 절댓값 표기) 표 칸으로 보지 않는다.
        self.assertEqual(classify_line("|x| 는 절댓값입니다"), "other")


class ParseBoxTableTest(unittest.TestCase):
    def test_parses_sample_table_into_rows(self):
        rows = parse_box_table(SAMPLE)
        self.assertEqual(rows, [
            ["구  분", "내  용"],
            ["추진 방향", "기술 발전 차단 후 함대 도착 시 일괄 점령*"],
            ["소요 기간", "함대 이동에 약 450년 소요 예상"],
            ["투입 규모", "함선 2,000여 척"],
            ["핵심 수단", "지자, 함대, 지구 내 협력 세력"],
        ])

    def test_rejects_block_without_top_border(self):
        self.assertIsNone(parse_box_table(SAMPLE[1:]))

    def test_rejects_block_without_bottom_border(self):
        self.assertIsNone(parse_box_table(SAMPLE[:-1]))

    def test_rejects_block_with_foreign_line_in_middle(self):
        broken = SAMPLE[:2] + ["이 줄은 표가 아닙니다"] + SAMPLE[2:]
        self.assertIsNone(parse_box_table(broken))

    def test_rejects_border_only_table_with_no_content(self):
        self.assertIsNone(parse_box_table([SAMPLE[0], SAMPLE[-1]]))

    def test_too_short_block_is_rejected(self):
        self.assertIsNone(parse_box_table(SAMPLE[:2]))

    def test_ragged_rows_are_padded_with_empty_cells(self):
        ragged = [
            "┌───┬───┬───┐",
            "│ a │ b │ c │",
            "│ d │",
            "└───┴───┴───┘",
        ]
        rows = parse_box_table(ragged)
        self.assertEqual(rows, [["a", "b", "c"], ["d", "", ""]])


class FindBoxTablesTest(unittest.TestCase):
    def test_finds_single_table_within_surrounding_paragraphs(self):
        paragraphs = ["ㅁ 추진 개요", ""] + SAMPLE + ["", "ㅇ 이하 생략"]
        matches = find_box_tables(paragraphs)
        self.assertEqual(len(matches), 1)
        start, end, rows = matches[0]
        self.assertEqual(start, 2)
        self.assertEqual(end, 2 + len(SAMPLE) - 1)
        self.assertEqual(rows[0], ["구  분", "내  용"])

    def test_finds_two_separate_tables(self):
        small_table = [
            "┌───┬───┐",
            "│ a │ b │",
            "└───┴───┘",
        ]
        paragraphs = SAMPLE + ["본문 문단"] + small_table
        matches = find_box_tables(paragraphs)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0][2][0], ["구  분", "내  용"])
        self.assertEqual(matches[1][2], [["a", "b"]])

    def test_no_table_in_plain_document(self):
        paragraphs = ["ㅁ 제목", "ㅇ 본문 내용", "- 세부 항목"]
        self.assertEqual(find_box_tables(paragraphs), [])

    def test_unclosed_block_is_ignored(self):
        paragraphs = [SAMPLE[0], SAMPLE[1], "본문으로 이어지는 문장"]
        self.assertEqual(find_box_tables(paragraphs), [])


if __name__ == "__main__":
    unittest.main()
