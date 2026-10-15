"""표 칸 너비: 칸 글자 수 비율(1행 제외, 2행부터 행별 비율의 평균)로 열 너비를 나누고 표 폭은 본문 폭."""
import unittest

from defusedxml.ElementTree import fromstring

from docfit_core.format_elements import HeaderIndex
from docfit_core.table_width import (cap_floors, column_ratios, fit_table, host_reserve, is_target, longest_word,
                                     plan_widths)

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
    def test_captioned_table_keeps_its_design_and_only_shrinks_to_fit(self):
        # '(단위: 개소)' 캡션이 달린 표: 열을 다시 나누지 않고, 넘칠 때만 같은 비율로 줄인다.
        rows = [[_cell('총 계', 0, 0, width=6000), _cell('노래연습장', 1, 0, width=4000)],
                [_cell('332', 0, 1, width=6000), _cell('175', 1, 1, width=4000)]]
        wide = _table(rows, 2, '<hp:caption side="TOP" lastWidth="10000"><hp:subList><hp:p><hp:run>'
                               '<hp:t>(단위: 개소)</hp:t></hp:run></hp:p></hp:subList></hp:caption>')
        next(x for x in wide if x.tag.endswith('}sz')).set('width', '10000')
        index = HeaderIndex(HEADER)
        self.assertFalse(fit_table(wide, 40000, index))          # 들어가면 그대로
        self.assertTrue(fit_table(wide, 8566, index))            # 넘치면 비율 그대로 축소
        self.assertEqual(_widths(wide)[0], [4800, 3200])

    def test_design_bar_table_is_left_untouched(self):
        # test6 문화경제국 '2026 추진실적 ……(8. 31. 현재)' 막대 표: 빈 점선 칸이 최소 폭으로 줄어 모양이 깨졌다.
        # 실제 문서처럼 글 칸이 두 행을 덮고 가운데 점선 칸이 위아래 두 행이다.
        rows = [[_cell('2026 추진실적', 0, 0, width=13425, row_span=2), _cell('', 1, 0, width=22339),
                 _cell('(8. 31. 현재)', 2, 0, width=11676, row_span=2)], [_cell('', 1, 1, width=22339)]]
        table = _table(rows, 3)
        # 사용자가 꾸민 장식 표는 너비를 전혀 바꾸지 않는다(사용자 규칙).
        self.assertFalse(fit_table(table, 48000, HeaderIndex(HEADER)))
        self.assertEqual(_widths(table)[0], [13425, 22339, 11676])

    def test_one_row_table_with_blank_cell_is_not_a_design_table(self):
        # 1행 표는 빈칸이 있어도 장식 표가 아니다(결재란·구분 표가 너비 맞춤에서 빠지던 오판).
        table = _table([[_cell('구 분', 0, 0), _cell('내 용', 1, 0), _cell('', 2, 0)]], 3)
        self.assertTrue(is_target(table))

    def test_plain_caption_table_is_fitted_like_any_data_table(self):
        # '<표 1> 추진 현황' 같은 일반 캡션 표는 베타처럼 열을 글자 수 비율로 다시 나눈다.
        rows = [[_cell('구 분', 0, 0, width=6000), _cell('노래연습장 현황', 1, 0, width=4000)],
                [_cell('총계', 0, 1, width=6000), _cell('노래연습장 현황', 1, 1, width=4000)]]
        table = _table(rows, 2, '<hp:caption side="TOP"><hp:subList><hp:p><hp:run><hp:t>&lt;표 1&gt; 추진 현황'
                                '</hp:t></hp:run></hp:p></hp:subList></hp:caption>')
        self.assertTrue(fit_table(table, 20000, HeaderIndex(HEADER)))
        first, second = _widths(table)[1]
        self.assertGreater(second, first)

    def test_unit_caption_shrink_keeps_merged_borders_aligned(self):
        # 칸마다 따로 버리면 병합 칸(10000)과 나뉜 칸(6001+3999)의 오른쪽 선이 1단위 어긋났다.
        rows = [[_cell('제목', 0, 0, width=10000, col_span=2)],
                [_cell('332', 0, 1, width=6001), _cell('175', 1, 1, width=3999)]]
        table = _table(rows, 2, '<hp:caption side="TOP"><hp:subList><hp:p><hp:run><hp:t>(단위: 개소)'
                                '</hp:t></hp:run></hp:p></hp:subList></hp:caption>')
        next(x for x in table if x.tag.endswith('}sz')).set('width', '10000')
        self.assertTrue(fit_table(table, 8566 + 566, HeaderIndex(HEADER)))
        merged, split = _widths(table)
        self.assertEqual(merged[0], sum(split))
        self.assertEqual(merged[0], 8566)

    def test_inline_table_after_spaces_leaves_room_for_them(self):
        # test6 문화경제국 문서: '   '(빈칸 셋) 뒤 글자처럼 놓인 표를 본문 폭 그대로 넓히면 줄을 넘쳐 용지 밖으로 밀렸다.
        rows = [[_cell('총 계', 0, 0), _cell('노래연습장', 1, 0)], [_cell('332', 0, 1), _cell('175', 1, 1)]]
        table = _table(rows, 2, '<hp:pos treatAsChar="1" horzRelTo="PARA"/>')
        para = fromstring(f'<hp:p {NS} paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>   </hp:t></hp:run>'
                          '<hp:run charPrIDRef="0"></hp:run></hp:p>')
        para[1].append(table)
        index = HeaderIndex(HEADER)
        reserve = host_reserve(para, table, index)
        self.assertEqual(reserve, 4800)          # 빈칸 셋 × 전각 × 16pt(나중에 커질 본문 크기)
        self.assertTrue(fit_table(table, 40000, index, reserve=reserve))
        width = int(next(x for x in table if x.tag.endswith('}sz')).get('width'))
        self.assertEqual(width, 40000 - 566 - 4800)   # 본문 폭 − 바깥 여백 − 표 앞 빈칸
        # 글과 따로 놓인 표는 앞 글을 세지 않는다.
        floating = _table(rows, 2, '<hp:pos treatAsChar="0"/>')
        self.assertEqual(host_reserve(para, floating, index), 0)

    def test_row_spanning_labels_are_not_a_multi_row_header(self):
        # test6 '(서식)' 양식 표: 첫 행 칸 셋이 두 행에 걸쳐 있을 뿐 아래 열을 묶는 머리글이 없다.
        # 둘째 행까지 머리글로 빼면 근거 법규 칸(글이 가장 많음)이 너비 계산에서 빠져 좁아지고 글자가 겹쳤다.
        bullets = '● 최상위 근거법규(~ 법 제00조) ● 최하위 근거법규(~ 조례 제00조)'
        rows = [
            [_cell('설치근거', 0, 0, row_span=2), _cell(bullets, 1, 0, row_span=2),
             _cell('유형', 2, 0, row_span=2), _cell('상설/비상설', 3, 0)],
            [_cell('법령상 강행/임의', 3, 1)],
            [_cell('설치일자', 0, 2), _cell('2000. 00. 00.', 1, 2), _cell('위원장', 2, 2), _cell('위원 중 호선', 3, 2)],
            [_cell('설치목적/기능', 0, 3, row_span=2), _cell('•', 1, 3, row_span=2), _cell('위원수', 2, 3),
             _cell('(정원) 16명~20명 (현원) 18명', 3, 3)],
            [_cell('임기', 2, 4), _cell('2년(1회 연임)', 3, 4)],
        ]
        ratios = column_ratios(_table(rows, 4))
        self.assertGreater(ratios[1], ratios[0])   # 근거 법규 열이 이름 열보다 좁아지지 않는다

    def test_grouped_two_row_header_still_skips_both_header_rows(self):
        # 진짜 다단 머리글: 첫 행 '2026년' 칸이 아래 두 열(월)을 묶는다. 본문 행으로만 비율을 정한다.
        rows = [
            [_cell('구분', 0, 0, row_span=2), _cell('2026년', 1, 0, col_span=2)],
            [_cell('1월', 1, 1), _cell('2월', 2, 1)],
            [_cell('아주 긴 사업 이름을 적은 칸', 0, 2), _cell('●', 1, 2), _cell('●', 2, 2)],
        ]
        ratios = column_ratios(_table(rows, 3))
        self.assertGreater(ratios[0], ratios[1] * 3)

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


class MultiRowHeaderRatiosTest(unittest.TestCase):
    def test_second_header_row_does_not_distort_body_ratios(self):
        from docfit_core.table_style import header_row_count
        table = _table([
            [_cell('구분', 0, 0, row_span=2), _cell('묶음', 1, 0, col_span=2)],
            [_cell('아주긴머리글입니다', 1, 1), _cell('짧음', 2, 1)],
            [_cell('가나', 0, 2), _cell('다라', 1, 2), _cell('마바', 2, 2)],
        ], 3)
        self.assertEqual(header_row_count(table), 2)
        for value in column_ratios(table):
            self.assertAlmostEqual(value, 1/3)
