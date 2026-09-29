"""표 서식통일 판정: 표 종류별로 같은 모양 칸끼리만 비교한다."""
import unittest

from docfit_core.table_unify import plan_table_fixes


def cell(area, text, font='한컴돋움', size=1300, color='#000000', bold=False, header=False, fill='5'):
    return {"area": area, "header": header, "fill": fill,
            "paras": [{"index": 0, "text": text,
                       "runs": [(0, len(text), font, size, color, bold)] if text else []}]}


def grid(index, cells):
    return {"index": index, "box": False, "marker": "", "cells": cells}


def box(index, area, text, marker='', fill='7', **style):
    return {"index": index, "box": True, "marker": marker, "cells": [cell(area, text, fill=fill, **style)]}


class TableUnifyTests(unittest.TestCase):
    def test_outlier_cell_in_table_is_fixed(self):
        cells = [cell(10 + i, f'값{i}') for i in range(5)]
        cells.append(cell(20, '다른 글꼴', font='굴림'))
        fixes, summary = plan_table_fixes([grid(0, cells)])
        self.assertEqual([(f['area'], f['field'], f['value']) for f in fixes], [(20, 'font', '한컴돋움')])
        self.assertEqual(summary, {'표 안': 1})

    def test_label_column_with_its_own_design_is_not_forced_to_body_style(self):
        # 항목 열(배경 있는 칸, 굵게)은 모양이 달라 본문 칸과 비교하지 않는다.
        cells = [cell(10 + i, f'항목{i}', bold=True, fill='9') for i in range(5)]
        cells += [cell(30 + i, f'내용{i}') for i in range(20)]
        fixes, _ = plan_table_fixes([grid(0, cells)])
        self.assertEqual(fixes, [])

    def test_smaller_cell_size_is_left_but_larger_is_reduced(self):
        cells = [cell(10 + i, f'값{i}') for i in range(8)]
        cells += [cell(20, '칸에 맞춘 긴 글', size=1100), cell(21, '큰 글', size=1500)]
        fixes, _ = plan_table_fixes([grid(0, cells)])
        self.assertEqual([(f['area'], f['field'], f['value']) for f in fixes], [(21, 'size', 1300)])

    def test_header_row_is_compared_separately(self):
        header = [cell(i, f'구분{i}', bold=True, header=True, fill='3') for i in range(5)]
        header.append(cell(9, '안굵음', bold=False, header=True, fill='3'))
        body = [cell(20 + i, f'값{i}') for i in range(10)]
        fixes, _ = plan_table_fixes([grid(0, header + body)])
        self.assertEqual([(f['area'], f['field'], f['value']) for f in fixes], [(9, 'bold', True)])

    def test_table_colors_are_not_changed(self):
        cells = [cell(10 + i, f'값{i}') for i in range(5)]
        cells.append(cell(20, '▲ 증가', color='#FF0000'))
        self.assertEqual(plan_table_fixes([grid(0, cells)])[0], [])

    def test_font_is_unified_across_tables_of_same_design_but_not_size(self):
        tables = [grid(i, [cell(100 * i + j, f'값{j}') for j in range(3)]) for i in range(3)]
        tables.append(grid(3, [cell(400 + j, f'값{j}', font='휴먼명조', size=1100) for j in range(3)]))
        fixes, summary = plan_table_fixes(tables)
        self.assertEqual({(f['field'], f['value']) for f in fixes}, {('font', '한컴돋움')})
        self.assertEqual(len(fixes), 3)
        self.assertEqual(summary, {'표 사이': 1})

    def test_tables_of_different_design_keep_their_own_fonts(self):
        tables = [grid(i, [cell(100 * i + j, f'값{j}') for j in range(3)]) for i in range(3)]
        tables.append(grid(3, [cell(400 + j, f'값{j}', font='휴먼명조', fill='8') for j in range(3)]))
        self.assertEqual(plan_table_fixes(tables)[0], [])

    def test_heading_boxes_of_same_marker_are_unified_including_color(self):
        tables = [box(i, 10 + i, f'\U000F02B1 절 제목 {i}', marker='\U000F02B1',
                      font='HY헤드라인M', size=1500) for i in range(3)]
        tables.append(box(3, 20, '\U000F02B5 붙여넣은 제목', marker='\U000F02B1',
                          font='한컴돋움', size=1000, color='#0000FF'))
        fixes, summary = plan_table_fixes(tables)
        self.assertEqual({(f['area'], f['field'], f['value']) for f in fixes},
                         {(20, 'font', 'HY헤드라인M'), (20, 'size', 1500), (20, 'color', '#000000')})
        self.assertEqual(summary, {'제목 상자': 3})

    def test_boxes_without_marker_are_grouped_by_design(self):
        dividers = [box(i, 10 + i, f'국 이름 {i}', fill='12', font='HY헤드라인M', size=2400,
                        color='#00007D') for i in range(4)]
        dividers.append(box(4, 20, '보건소', fill='12', font='HY헤드라인M', size=2000, color='#00007D'))
        summary_box = box(5, 30, '요약 상자 내용', fill='11', font='한컴돋움', size=1500)
        fixes, _ = plan_table_fixes(dividers + [summary_box])
        self.assertEqual([(f['area'], f['field'], f['value']) for f in fixes], [(20, 'size', 2400)])

    def test_two_different_boxes_have_no_representative(self):
        tables = [box(0, 10, '가', font='굴림'), box(1, 11, '나', font='돋움')]
        self.assertEqual(plan_table_fixes(tables)[0], [])


if __name__ == '__main__':
    unittest.main()
