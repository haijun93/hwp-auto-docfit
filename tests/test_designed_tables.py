"""사용자가 꾸민 표(장식 막대 표·캡션 달린 표)는 서식·너비·자간 작업에서 그대로 둔다(사용자 규칙, 2026-10-15)."""
import unittest
import runpy
import tempfile
import zipfile
from pathlib import Path

from defusedxml.ElementTree import fromstring

from docfit_core.spacing_reset import reset_spacing
from docfit_core.table_style import (has_unit_caption, is_design_table, is_grid_table, is_user_designed_table,
                                     protected_tables)

NS = ('xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
      'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"')


def cell(text, col, row, row_span=1):
    return (f'<hp:tc><hp:subList><hp:p paraPrIDRef="0"><hp:run charPrIDRef="1"><hp:t>{text}</hp:t></hp:run></hp:p>'
            f'</hp:subList><hp:cellAddr colAddr="{col}" rowAddr="{row}"/>'
            f'<hp:cellSpan colSpan="1" rowSpan="{row_span}"/><hp:cellSz width="1000" height="1000"/></hp:tc>')


def table(rows, cols, extra=''):
    body = ''.join('<hp:tr>' + ''.join(r) + '</hp:tr>' for r in rows)
    return f'<hp:tbl {NS} rowCnt="{len(rows)}" colCnt="{cols}">{extra}{body}</hp:tbl>'


# '2026 추진실적 ……… ( 8. 31. 현재 )': 글 칸 둘이 두 행을 덮고, 가운데는 빈 점선 칸.
BAR = table([[cell('2026 추진실적', 0, 0, 2), cell('', 1, 0), cell('', 2, 0), cell('( 8. 31. 현재 )', 3, 0, 2)],
             [cell('', 1, 1), cell('', 2, 1)]], 4)
DATA = table([[cell('구 분', 0, 0), cell('노래연습장', 1, 0)], [cell('332', 0, 1), cell('', 1, 1)]], 2)
UNIT = ('<hp:caption side="TOP"><hp:subList><hp:p><hp:run charPrIDRef="1"><hp:t>(단위: 개소)</hp:t></hp:run></hp:p>'
        '</hp:subList></hp:caption>')
PLAIN = ('<hp:caption side="TOP"><hp:subList><hp:p><hp:run charPrIDRef="1"><hp:t>&lt;표 1&gt; 추진 현황</hp:t>'
         '</hp:run></hp:p></hp:subList></hp:caption>')


class DesignedTableTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"), run_name="import_check")

    def _captioned_dates(self):
        return fromstring(table([[cell("시작일", 0, 0), cell("종료일", 1, 0)],
                                 [cell("2026. 10. 14.", 0, 1), cell("2026. 10. 15.", 1, 1)]],
                                2, UNIT))

    def _nested(self, inner, protect_outer=False):
        from docfit_core.table_style import _cells, _child
        outer = fromstring(DATA)
        if protect_outer:
            outer.insert(0, fromstring(UNIT.replace('<hp:caption ', f'<hp:caption {NS} ', 1)))
        sub = _child(_cells(outer)[0], "subList")
        sub[0][0].append(inner)
        return outer

    def _records(self, table_element):
        from defusedxml.ElementTree import tostring
        section = fromstring(f'<hp:sec {NS}><hp:p><hp:run/></hp:p></hp:sec>')
        section[0][0].append(table_element)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nested.hwpx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("Contents/header.xml", "<head/>")
                archive.writestr("Contents/section0.xml", tostring(section))
            return self.ns["서식표_영역_목록"](path, 장식만=True)

    def test_captioned_dates_are_not_squeezed(self):
        from defusedxml.ElementTree import tostring
        protected = self._captioned_dates()
        before = tostring(protected)
        self.assertEqual(self.ns["표_날짜칸_한줄"](protected), 0)
        self.assertEqual(tostring(protected), before)

    def test_dates_skip_nested_designs_but_process_ordinary_cells(self):
        from defusedxml.ElementTree import tostring
        protected = self._captioned_dates()
        before = tostring(protected)
        outer = self._nested(protected)
        from docfit_core.table_style import _cells, _child
        _child(_cells(outer)[-1], "subList")[0][0][0].text = "2026. 10. 14."
        self.assertEqual(self.ns["표_날짜칸_한줄"](outer), 1)
        self.assertEqual(tostring(protected), before)

    def test_nested_bar_protection_does_not_include_ordinary_parent_cells(self):
        records = self._records(self._nested(fromstring(BAR)))
        protected = {area for areas, _ in records for area in areas}
        self.assertEqual(protected, set(range(3, 9)))

    def test_nested_protection_is_consumed_by_the_spacing_engine(self):
        from docfit_engine.runtime import session_for
        protected = {area for areas, _ in self._records(self._nested(fromstring(BAR))) for area in areas}
        class Hwp:
            area = 3
            def GetPos(self):
                return (self.area, 0, 0)
        hwp = Hwp()
        context = session_for(self.ns).new_context(state={
            "hwp": hwp, "디자인표_보호영역": protected, "표_자간조정_사용": True})
        for area in protected:
            hwp.area = area
            self.assertTrue(self.ns["표셀_자간_제외인가"](context=context))
        hwp.area = 2
        self.assertFalse(self.ns["표셀_자간_제외인가"](context=context))

    def test_nested_caption_table_has_its_own_protection(self):
        records = self._records(self._nested(self._captioned_dates()))
        protected = {area for areas, _ in records for area in areas}
        self.assertEqual(protected, set(range(3, 8)))   # 안쪽 표의 캡션 목록(3) + 칸 4개

    def test_caption_text_list_is_protected_with_the_table(self):
        protected_table = self._captioned_dates()   # 캡션 '(단위: 개소)' 목록(2) + 칸 4개
        records = self._records(protected_table)
        protected = {area for areas, _ in records for area in areas}
        self.assertEqual(protected, set(range(2, 7)))

    def test_protected_parent_includes_ordinary_nested_cells(self):
        records = self._records(self._nested(fromstring(DATA), protect_outer=True))
        protected = {area for areas, _ in records for area in areas}
        self.assertEqual(protected, set(range(2, 11)))   # 바깥 캡션(2) + 바깥 칸 4개 + 안쪽 칸 4개

    def test_bar_table_is_design_and_not_styled(self):
        bar = fromstring(BAR)
        self.assertTrue(is_design_table(bar))
        self.assertFalse(is_grid_table(bar))

    def test_data_table_with_an_empty_cell_is_still_a_data_table(self):
        self.assertFalse(is_design_table(fromstring(DATA)))

    def test_one_row_table_with_blank_cell_is_not_design(self):
        # 1행 표는 '글 칸이 모든 행을 덮는다'가 늘 참이라 결재란·구분 표가 장식 표로 오판됐다.
        self.assertFalse(is_design_table(fromstring(table([[cell('구 분', 0, 0), cell('내 용', 1, 0), cell('', 2, 0)]], 3))))

    def test_only_unit_captions_mark_a_user_designed_table(self):
        unit = fromstring(DATA.replace('colCnt="2">', 'colCnt="2">' + UNIT, 1))
        plain = fromstring(DATA.replace('colCnt="2">', 'colCnt="2">' + PLAIN, 1))
        self.assertTrue(has_unit_caption(unit) and is_user_designed_table(unit))
        self.assertFalse(has_unit_caption(plain) or is_user_designed_table(plain))

    def test_tables_inside_a_designed_table_are_protected(self):
        inner = table([[cell('가', 0, 0), cell('나', 1, 0)], [cell('1', 0, 1), cell('2', 1, 1)]], 2)
        outer = DATA.replace('colCnt="2">', 'colCnt="2">' + UNIT, 1).replace('<hp:t>332</hp:t>', inner, 1)
        section = fromstring(f'<hp:sec {NS}><hp:p><hp:run>{outer}</hp:run></hp:p>'
                             f'<hp:p><hp:run>{DATA}</hp:run></hp:p></hp:sec>')
        tables = [t for t in section.iter() if t.tag.endswith('}tbl')]
        self.assertEqual(protected_tables(section), {id(tables[0]), id(tables[1])})

    def test_spacing_reset_keeps_designed_and_captioned_tables(self):
        header = fromstring(f'<hh:head {NS}><hh:charProperties>'
                            '<hh:charPr id="1" height="1100"><hh:spacing hangul="10"/></hh:charPr>'
                            '</hh:charProperties></hh:head>')
        captioned = DATA.replace('rowCnt="2" colCnt="2">', 'rowCnt="2" colCnt="2">' + UNIT, 1)
        section = fromstring(f'<hp:sec {NS}><hp:p><hp:run charPrIDRef="1">{BAR}</hp:run></hp:p>'
                             f'<hp:p><hp:run charPrIDRef="1">{captioned}</hp:run></hp:p>'
                             f'<hp:p><hp:run charPrIDRef="1"><hp:t>본문 글</hp:t></hp:run></hp:p></hp:sec>')
        reset_spacing(header, [section], lambda text: 0)
        inside = [r.get('charPrIDRef') for t in section.iter() if t.tag.endswith('}tbl')
                  for r in t.iter() if r.tag.endswith('}run')]
        self.assertEqual(set(inside), {'1'})                 # 표 안 글은 원래 자간(10%) 그대로
        body = [p for p in section if p.tag.endswith('}p')][2]
        self.assertNotEqual(body[0].get('charPrIDRef'), '1')  # 본문은 0%로 초기화


if __name__ == '__main__':
    unittest.main()
