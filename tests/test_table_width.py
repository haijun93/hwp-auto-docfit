"""표 칸 너비: 칸 글자 수 비율(1행 제외, 2행부터 행별 비율의 평균)로 열 너비를 나누고 표 폭은 본문 폭."""
import unittest

from defusedxml.ElementTree import fromstring

from docfit_core.format_elements import HeaderIndex
from docfit_core.table_width import cap_floors, column_ratios, fit_table, is_target, longest_word, plan_widths

NS = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"'
# 글자 크기 10pt(1000), 장평 100, 자간 0
HEADER = fromstring(f'<hh:head {NS}><hh:charProperties><hh:charPr id="0" height="1000">'
                    '<hh:ratio hangul="100"/><hh:spacing hangul="0"/></hh:charPr></hh:charProperties></hh:head>')


def _cell(text, col, row, width=1000, col_span=1, row_span=1):
    return (f'<hp:tc><hp:subList><hp:p><hp:run charPrIDRef="0"><hp:t>{text}</hp:t></hp:run>'
            '<hp:linesegarray><hp:lineseg/></hp:linesegarray></hp:p></hp:subList>'
            f'<hp:cellAddr colAddr="{col}" rowAddr="{row}"/><hp:cellSpan colSpan="{col_span}" rowSpan="{row_span}"/>'
            f'<hp:cellSz width="{width}" height="1000"/><hp:cellMargin left="510" right="510" top="141" bottom="141"/>'
            '</hp:tc>')


def _table(rows, cols, extra=''):
    body = ''.join('<hp:tr>' + ''.join(row) + '</hp:tr>' for row in rows)
    return fromstring(f'<hp:tbl {NS} rowCnt="{len(rows)}" colCnt="{cols}"><hp:sz width="2000" widthRelTo="ABSOLUTE" '
                      f'height="1000"/><hp:outMargin left="283" right="283" top="283" bottom="283"/>'
                      f'<hp:inMargin left="510" right="510" top="141" bottom="141"/>{body}{extra}</hp:tbl>')


def _widths(table):
    result = []
    for tr in (x for x in table if x.tag.endswith('}tr')):
        result.append([int(next(x for x in tc if x.tag.endswith('}cellSz')).get('width'))
                       for tc in tr if tc.tag.endswith('}tc')])
    return result


class TableWidthTest(unittest.TestCase):
    def test_single_row_follows_character_count_including_inner_spaces(self):
        # '도  시' = 4자, '마 을 여  행' = 8자 → 1:2
        table = _table([[_cell('도  시', 0, 0), _cell(' 마 을 여  행 ', 1, 0)]], 2)
        self.assertEqual(column_ratios(table), [1 / 3, 2 / 3])
        self.assertTrue(fit_table(table, 42520, HeaderIndex(HEADER)))
        total = 42520 - 566
        self.assertEqual(table.find('{*}sz').get('width'), str(total))
        (a, b), = _widths(table)
        self.assertEqual(a + b, total)
        self.assertAlmostEqual(b / a, 2, places=2)
        self.assertIsNone(table.find('.//{*}linesegarray'))   # 한/글이 줄 배치를 다시 계산하도록

    def test_first_row_is_header_and_row_ratios_are_averaged(self):
        # 1행은 비율에서 뺀다. 2행 1:3(25%:75%), 3행 3:1(75%:25%)의 평균 50%:50%를 모든 행에 적용
        table = _table([[_cell('구분', 0, 0), _cell('아주 긴 머리글 제목입니다', 1, 0)],
                        [_cell('가', 0, 1), _cell('나다라', 1, 1)],
                        [_cell('가나다', 0, 2), _cell('라', 1, 2)]], 2)
        self.assertEqual(column_ratios(table), [0.5, 0.5])
        fit_table(table, 42520, HeaderIndex(HEADER))
        rows = _widths(table)
        self.assertEqual(rows[0], rows[1])
        self.assertEqual(rows[1], rows[2])                     # 행마다 따로 맞추지 않는다
        self.assertLessEqual(abs(rows[0][0] - rows[0][1]), 1)

    def test_empty_rows_are_left_out_of_average(self):
        table = _table([[_cell('항목', 0, 0), _cell('내용', 1, 0)],
                        [_cell('도  시', 0, 1), _cell('마 을 여  행', 1, 1)],
                        [_cell('', 0, 2), _cell('', 1, 2)]], 2)
        self.assertEqual(column_ratios(table), [1 / 3, 2 / 3])

    def test_rows_with_blank_cell_are_used_only_without_full_rows(self):
        # 비고 칸이 빈 행은 비고 열을 0으로 만들어 비율을 흐리므로, 모든 칸에 글이 있는 행으로만 정한다.
        table = _table([[_cell('시간', 0, 0), _cell('내용', 1, 0), _cell('비고', 2, 0)],
                        [_cell('가나', 0, 1), _cell('가나', 1, 1), _cell('가나다라', 2, 1)],
                        [_cell('가나다라', 0, 2), _cell('가나', 1, 2), _cell('', 2, 2)]], 3)
        self.assertEqual(column_ratios(table), [0.25, 0.25, 0.5])
        # 모든 칸에 글이 있는 행이 없으면 글이 있는 행 모두로(빈 칸은 0) 정한다.
        table = _table([[_cell('구분', 0, 0), _cell('비고', 1, 0)],
                        [_cell('가나다', 0, 1), _cell('', 1, 1)],
                        [_cell('가', 0, 2), _cell('', 1, 2)]], 2)
        self.assertEqual(column_ratios(table), [1.0, 0.0])

    def test_header_only_text_falls_back_to_first_row(self):
        table = _table([[_cell('도  시', 0, 0), _cell('마 을 여  행', 1, 0)],
                        [_cell('', 0, 1), _cell('', 1, 1)]], 2)
        self.assertEqual(column_ratios(table), [1 / 3, 2 / 3])

    def test_merged_cells_split_count_over_spanned_columns_and_rows(self):
        # 2행: A2 '가나'(2) + B2:C2 병합 '가나다라'(4 → 2, 2) → 2:2:2
        # 3행: A2:A3 세로 병합 '가나'(2) + B3 '가'(1) + C3 '가나다'(3) → 2:1:3
        table = _table([[_cell('머리', 0, 0), _cell('머리', 1, 0), _cell('머리', 2, 0)],
                        [_cell('가나', 0, 1, row_span=2), _cell('가나다라', 1, 1, col_span=2)],
                        [_cell('가', 1, 2), _cell('가나다', 2, 2)]], 3)
        ratios = column_ratios(table)
        for got, want in zip(ratios, [(1 / 3 + 2 / 6) / 2, (1 / 3 + 1 / 6) / 2, (1 / 3 + 3 / 6) / 2]):
            self.assertAlmostEqual(got, want)
        fit_table(table, 42520, HeaderIndex(HEADER))
        rows = _widths(table)
        self.assertEqual(rows[1][1], rows[2][0] + rows[2][1])  # 병합 칸 너비 = 걸친 열 너비 합
        self.assertEqual(sum(rows[0]), 42520 - 566)

    def test_short_word_column_keeps_minimum_width(self):
        # 비율로는 아주 좁아지는 열도 가장 긴 낱말이 한 줄에 들어갈 폭은 지킨다
        long_text = '가' * 200
        table = _table([[_cell('구분명칭', 0, 0), _cell(long_text, 1, 0)]], 2)
        fit_table(table, 42520, HeaderIndex(HEADER))
        (a, _), = _widths(table)
        self.assertGreaterEqual(a, 4 * 1000 + 1020)

    def test_floor_counts_half_width_characters_and_caps_largest_first(self):
        # 숫자·영문·문장부호는 한글 반 글자 폭으로 잰다
        table = _table([[_cell('14:00~14:50 (10’)', 0, 0), _cell('가나다', 1, 0)]], 2)
        cells = [tc for tr in table if tr.tag.endswith('}tr') for tc in tr]
        self.assertEqual(longest_word(cells[0]), 5.5)
        self.assertEqual(longest_word(cells[1]), 3)
        # 최소 폭 합이 넘치면 큰 값만 깎고 작은 값(짧은 낱말 열)은 그대로 지킨다
        self.assertEqual(cap_floors([1000, 1000, 9000], 10000), [1000, 1000, 7500])
        self.assertEqual(cap_floors([1000, 2000], 10000), [1000, 2000])

    def test_gantt_like_table_keeps_label_column(self):
        # 일정표: 1·2행 머리글(첫 칸 세로 병합), 3행부터 막대 칸은 비어 있다 → 2행(분기 숫자)으로 비율을 정한다
        head = [_cell('세부추진사항', 0, 0, row_span=2)] + [_cell(str(2026 + y), 1 + 4 * y, 0, col_span=4)
                                                        for y in range(2)]
        quarters = [_cell(str(q % 4 + 1), 1 + q, 1) for q in range(8)]
        body = [[_cell('문화관광벨트 종합 실행계획 수립', 0, r)] + [_cell('', 1 + q, r) for q in range(8)]
                for r in (2, 3)]
        table = _table([head, quarters] + body, 9)
        ratios = column_ratios(table)
        self.assertAlmostEqual(ratios[0], 6 / 14)
        fit_table(table, 42520, HeaderIndex(HEADER))
        rows = _widths(table)
        self.assertGreater(rows[2][0], rows[2][1] * 4)        # 항목 열이 분기 칸보다 넉넉하다
        self.assertEqual(len(set(rows[2][1:])), 1)

    def test_column_without_text_gets_floor_only(self):
        self.assertEqual(plan_widths([0.0, 1.0], [600, 600], 10000), [600, 9400])
        self.assertEqual(plan_widths([0.0, 0.0], [600, 600], 10000), [5000, 5000])

    def test_tables_with_objects_or_single_column_are_skipped(self):
        single = _table([[_cell('가', 0, 0)]], 1)
        self.assertFalse(is_target(single))
        nested = _table([[_cell('가', 0, 0), _cell('나', 1, 0).replace('<hp:t>나</hp:t>', '<hp:t>나</hp:t><hp:pic/>')]], 2)
        self.assertFalse(is_target(nested))
        self.assertFalse(fit_table(nested, 42520, HeaderIndex(HEADER)))


if __name__ == '__main__':
    unittest.main()
