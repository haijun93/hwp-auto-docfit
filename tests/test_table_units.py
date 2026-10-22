"""내장 표 서식의 정보단위 XML 엔진 회귀 시험. 사용자 문서는 열지 않는다."""

import copy
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from docfit_core import table_catalog as catalog
from docfit_core import table_units as units
from docfit_core.hwpx import validate_and_inspect_hwpx

SOURCE = Path(__file__).resolve().parents[1] / "resources/서식예시/표 서식모음.hwpx"
HP = catalog._HP


class TableUnitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = SOURCE.read_bytes()
        cls.records = {r["name"]: r for r in catalog._scan(SOURCE)}

    @classmethod
    def tearDownClass(cls):
        if SOURCE.read_bytes() != cls.original:
            raise AssertionError("원본 템플릿 파일이 변경되었습니다.")

    def load(self, name):
        record = self.records[name]
        _, table, _ = units._load(record["id"], SOURCE)
        return table, units.plan_for(record)

    def grid(self, table, width=False):
        rows, cols = int(table.get("rowCnt")), int(table.get("colCnt"))
        coverage = [[0] * cols for _ in range(rows)]
        row_widths = [0] * rows
        self.assertEqual(len(table.findall(HP + "tr")), rows)
        for i, tr in enumerate(table.findall(HP + "tr")):
            addresses = []
            for tc in tr.findall(HP + "tc"):
                c = catalog._cell_meta(tc, 0, 0, "", None)
                self.assertEqual(c["row"], i)
                addresses.append(c["col"])
                self.assertLessEqual(c["row"] + c["rowSpan"], rows)
                self.assertLessEqual(c["col"] + c["colSpan"], cols)
                for r in range(c["row"], c["row"] + c["rowSpan"]):
                    row_widths[r] += c["width"]
                    for col in range(c["col"], c["col"] + c["colSpan"]):
                        coverage[r][col] += 1
            self.assertEqual(addresses, sorted(addresses))
        self.assertTrue(all(v == 1 for row in coverage for v in row), coverage)
        if width:
            total = int(table.find(HP + "sz").get("width"))
            self.assertEqual(row_widths, [total] * rows)

    def test_describe_units_matches_all_builtin_plans(self):
        descriptions = units.describe_units(SOURCE)
        self.assertEqual(len(descriptions), len(self.records))
        for item in descriptions:
            with self.subTest(name=item["name"]):
                expected = units.PLANS[item["name"]]
                for axis in ("row", "col"):
                    p = expected[axis]
                    self.assertEqual(item["units"][axis],
                        {k: p[k] for k in ("count", "min", "max", "core", "sep")} if p else None)

    def test_task_columns_sequential(self):
        table, plan = self.load("분야별과제표 · 모양 1")
        total = table.find(HP + "sz").get("width")
        for count in (2, 1, 4):
            units.resize_table(table, plan, col_count=count)
            self.assertEqual(int(table.get("colCnt")), count * 4)
            self.assertEqual(table.find(HP + "sz").get("width"), total)
            self.grid(table, width=True)

    def test_event_timetable_height_and_header(self):
        table, plan = self.load("행사시간표 · 모양 1")
        head = ET.tostring(table.find(HP + "tr"))
        for count in (3, 10):
            units.resize_table(table, plan, row_count=count)
            self.assertEqual(int(table.get("rowCnt")), count + 1)
            self.assertEqual(ET.tostring(table.find(HP + "tr")), head)
            self.assertEqual(int(table.find(HP + "sz").get("height")), sum(units._sizes(table, "row")))
            self.grid(table)

    def assert_object_ids_unique(self, roots):
        values = []
        for root in roots:
            for node in root.iter():
                if node.tag.startswith(HP) and node.tag not in (HP + "p", HP + "subList"):
                    for attr in ("id", "instId"):
                        value = units._integer(node.get(attr))
                        if value is not None:
                            values.append(value)
        self.assertEqual(len(values), len(set(values)), values)

    def test_export_clone_object_ids_and_nested_widths(self):
        for name, kwargs in (("분야별과제표 · 모양 1", dict(col_count=5)),
                             ("행사표(1일) · 모양 1", dict(row_count=3))):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                out = Path(folder) / "resized.hwpx"
                units.export_resized(self.records[name]["id"], out, SOURCE, **kwargs)
                validation, inspection = validate_and_inspect_hwpx(out)
                self.assertTrue(validation)
                self.assertGreater(inspection.table_count, 0)
                with zipfile.ZipFile(out) as archive:
                    roots = [ET.fromstring(archive.read(n)) for n in catalog._section_names(archive)]
                self.assert_object_ids_unique(roots)
                table = next(t for root in roots for p in root.findall(HP + "p")
                             for t in catalog._top_tables(p))
                self.grid(table, width="col_count" in kwargs)
                for parent in table.iter(HP + "tbl"):
                    for _, cell in units._cells(parent):
                        width = int(cell.find(HP + "cellSz").get("width"))
                        for nested in catalog._top_tables(cell):
                            self.assertLessEqual(int(nested.find(HP + "sz").get("width")), width)
                            self.grid(nested, width=True)

    def test_clone_drawing_ids_zorder_and_document_reservations(self):
        for axis, name, cell_index in (("row", "행사표(1일) · 모양 1", -1),
                                       ("col", "분야별과제표 · 모양 1", -2)):
            with self.subTest(axis=axis):
                table, plan = self.load(name)
                cell = table.findall(HP + "tr")[-1].findall(HP + "tc")[cell_index]
                drawing = ET.fromstring(f'<hp:container xmlns:hp="{HP[1:-1]}" id="101" instId="102" zOrder="80">'
                    '<hp:rect id="103" instId="104" zOrder="81"/><hp:pic id="logo" instId="105" zOrder="82"/>'
                    '<hp:ellipse id="106"/><hp:line id="107"/><hp:textart id="108"/></hp:container>')
                cell.append(drawing)
                original = ET.tostring(drawing)
                reserved = ET.fromstring(f'<hp:rect xmlns:hp="{HP[1:-1]}" id="1" instId="2" zOrder="100"/>')
                count = plan[axis]["count"] + 1
                units.resize_table(table, plan, **{axis + "_count": count}, id_roots=(reserved,))
                self.assert_object_ids_unique([table, reserved])
                drawings = list(table.iter(HP + "container"))
                self.assertEqual(len(drawings), 2)
                self.assertEqual(ET.tostring(drawings[0]), original)
                clone = drawings[1]
                clone_orders = [int(n.get("zOrder")) for n in clone.iter() if n.get("zOrder")]
                self.assertEqual(clone_orders, list(range(clone_orders[0], clone_orders[0] + 3)))
                added_orders = sorted(int(n.get("zOrder")) for n in table.iter()
                                      if units._integer(n.get("zOrder")) is not None and int(n.get("zOrder")) > 100)
                self.assertEqual(added_orders, list(range(101, 101 + len(added_orders))))
                self.assertEqual(clone.find(HP + "pic").get("id"), "logo")
                units.resize_table(table, plan, **{axis + "_count": count + 1}, id_roots=(reserved,))
                self.assert_object_ids_unique([table, reserved])

    def test_nested_width_rounding_merges_and_deeper_tables(self):
        table, plan = self.load("분야별과제표 · 모양 1")
        cell = table.findall(HP + "tr")[0].findall(HP + "tc")[1]
        nested = catalog._top_tables(cell)[0]
        # Give the nested table an uneven three-column grid with a merged row.
        fragment = f'''<hp:tbl xmlns:hp="{HP[1:-1]}" rowCnt="2" colCnt="3">
          <hp:sz width="101" height="20"/><hp:tr>
          <hp:tc><hp:cellAddr rowAddr="0" colAddr="0"/><hp:cellSpan rowSpan="1" colSpan="2"/><hp:cellSz width="68" height="10"/></hp:tc>
          <hp:tc><hp:cellAddr rowAddr="0" colAddr="2"/><hp:cellSpan rowSpan="1" colSpan="1"/><hp:cellSz width="33" height="10"/></hp:tc></hp:tr><hp:tr>'''
        for col, width in enumerate((31, 37, 33)):
            fragment += (f'<hp:tc><hp:cellAddr rowAddr="1" colAddr="{col}"/>'
                f'<hp:cellSpan rowSpan="1" colSpan="1"/><hp:cellSz width="{width}" height="10"/></hp:tc>')
        uneven = ET.fromstring(fragment + '</hp:tr></hp:tbl>')
        deep = copy.deepcopy(uneven)
        uneven.find(HP + "tr").find(HP + "tc").append(deep)
        cell.append(uneven)
        heights = [n.get("height") for n in cell.iter() if n.get("height") is not None]
        old_width = int(cell.find(HP + "cellSz").get("width"))
        old_nested = int(nested.find(HP + "sz").get("width"))
        units._scale_nested_tables(cell, old_width, old_width * 3 // 5)
        self.assertEqual(int(nested.find(HP + "sz").get("width")), old_nested * (old_width * 3 // 5) // old_width)
        self.assertEqual(heights, [n.get("height") for n in cell.iter() if n.get("height") is not None])
        self.grid(uneven, width=True)
        self.grid(deep, width=True)
        self.assertEqual(int(uneven.find(HP + "sz").get("width")), 101 * (old_width * 3 // 5) // old_width)

    def test_event_eight_row_bundle(self):
        table, plan = self.load("행사표(1일) · 모양 1")
        units.resize_table(table, plan, row_count=3)
        self.assertEqual(int(table.get("rowCnt")), 25)
        days = [c for c in units._meta(table) if c["col"] == 0 and c["row"] > 0]
        self.assertEqual([(c["row"], c["rowSpan"]) for c in days], [(1, 8), (9, 8), (17, 8)])
        self.assertIn("2일차", catalog._text(table.findall(HP + "tr")[17]))
        self.grid(table)

    def test_merged_headers_arrows_and_plain_comparison(self):
        for name, row, col in (("신구대조표 · 모양 3", 3, None),
                               ("일정표(연간) · 모양 1", 8, 3),
                               ("추진절차(가로) · 모양 2", None, 7)):
            with self.subTest(name=name):
                table, plan = self.load(name)
                units.resize_table(table, plan, row_count=row, col_count=col)
                self.grid(table, width=col is not None)
                if "연간" in name:
                    first = units._meta(table)[0]
                    self.assertEqual((first["rowSpan"], first["colSpan"]), (2, 1))
                if "추진절차" in name:
                    self.assertEqual(sum(c["rowSpan"] == 3 for c in units._meta(table)), 6)

    def test_all_adjustable_templates_min_max_and_grid(self):
        for name, record in self.records.items():
            for axis, p in units.plan_for(record).items():
                if p is None:
                    continue
                for target in (1, p["count"] + 1, p["max"]):
                    with self.subTest(name=name, axis=axis, target=target):
                        table, plan = self.load(name)
                        units.resize_table(table, plan, **{axis + "_count": target})
                        self.grid(table, width=axis == "col")

    def test_invalid_requests_are_atomic(self):
        table, plan = self.load("행사시간표 · 모양 1")
        original = ET.tostring(table)
        for value in (0, 41, 1.5, True):
            with self.assertRaises(ValueError):
                units.resize_table(table, plan, row_count=value)
            self.assertEqual(ET.tostring(table), original)
        with self.assertRaises(ValueError):
            units.resize_table(table, plan, row_count=3, col_count=3)
        self.assertEqual(ET.tostring(table), original)
        table, plan = self.load("조직도 · 모양 1")
        with self.assertRaises(ValueError):
            units.resize_table(table, plan, col_count=2)

    def test_plan_validation_rejects_cross_unit_merge(self):
        record = copy.deepcopy(self.records["행사시간표 · 모양 1"])
        record["cell_meta"][1][0]["rowSpan"] = 2
        self.assertIsNone(units.plan_for(record)["row"])
        table, plan = self.load("행사시간표 · 모양 1")
        table.findall(HP + "tr")[1].find(HP + "tc").find(HP + "cellSpan").set("rowSpan", "2")
        with self.assertRaises(ValueError):
            units.resize_table(table, plan, row_count=3)

    def test_covering_merge_grows_shrinks_and_survives_one_unit(self):
        # A left label spans the whole repeated body; every grid point still has one owner.
        table = ET.fromstring(f'''<hp:tbl xmlns:hp="{HP[1:-1]}" rowCnt="3" colCnt="2">
          <hp:sz width="200" height="30"/>
          <hp:tr><hp:tc><hp:cellAddr rowAddr="0" colAddr="0"/><hp:cellSpan rowSpan="3" colSpan="1"/><hp:cellSz width="100" height="30"/></hp:tc>
          <hp:tc><hp:cellAddr rowAddr="0" colAddr="1"/><hp:cellSpan rowSpan="1" colSpan="1"/><hp:cellSz width="100" height="10"/></hp:tc></hp:tr>
          <hp:tr><hp:tc><hp:cellAddr rowAddr="1" colAddr="1"/><hp:cellSpan rowSpan="1" colSpan="1"/><hp:cellSz width="100" height="10"/></hp:tc></hp:tr>
          <hp:tr><hp:tc><hp:cellAddr rowAddr="2" colAddr="1"/><hp:cellSpan rowSpan="1" colSpan="1"/><hp:cellSz width="100" height="10"/></hp:tc></hp:tr></hp:tbl>''')
        plan = {"row": units._axis(0, 1, 3), "col": None}
        for target in (5, 1, 4):
            units.resize_table(table, plan, row_count=target)
            self.assertEqual(units._meta(table)[0]["rowSpan"], target)
            self.grid(table)

    def test_export_preview_and_original_unchanged(self):
        for name, kwargs in (("일정표(연간) · 모양 1", dict(row_count=9, col_count=7)),
                             ("행사표(1일) · 모양 1", dict(row_count=5)),
                             ("분야별과제표 · 모양 1", dict(col_count=4))):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                template_id = self.records[name]["id"]
                out = Path(folder) / "resized.hwpx"
                self.assertEqual(units.export_resized(template_id, out, SOURCE, **kwargs), out)
                with zipfile.ZipFile(out) as archive:
                    tables = []
                    for section in catalog._section_names(archive):
                        root = ET.fromstring(archive.read(section))
                        for p in root.findall(HP + "p"):
                            tables.extend(catalog._top_tables(p))
                    self.assertEqual(len(tables), 1)
                    self.grid(tables[0], width="col_count" in kwargs)
                    view = units.preview(template_id, SOURCE, **kwargs)
                    self.assertEqual(view["rows"], int(tables[0].get("rowCnt")))
                    self.assertEqual(view["cols"], int(tables[0].get("colCnt")))
                    self.assertEqual(len(view["cell_meta"]), view["rows"])
                    header = units._load(template_id, SOURCE)[2]
                    expected = [[catalog._cell_meta(cell, i, j,
                        " ".join("".join(n.text or "" for n in catalog._cell_text_nodes(cell)).split())[:80], header)
                        for j, cell in enumerate(row.findall(HP + "tc"))]
                        for i, row in enumerate(tables[0].findall(HP + "tr"))]
                    self.assertEqual(view["cell_meta"], expected)
        self.assertEqual(SOURCE.read_bytes(), self.original)
        with self.assertRaises(ValueError):
            units.export_resized(self.records["행사시간표 · 모양 1"]["id"], SOURCE, SOURCE, row_count=3)

    def test_detect_plan_without_constants(self):
        expected = {
            "행사시간표 · 모양 1": {"row": units._axis(1, 1, 6), "col": None},
            "추진절차(가로) · 모양 1": {"row": None, "col": units._axis(0, 1, 5, 1, axis="col")},
        }
        for name, plan in expected.items():
            with self.subTest(name=name):
                r = self.records[name]
                axis = "col" if name.startswith("추진절차") else "row"
                self.assertEqual(units.detect_plan(r["cell_meta"], r["rows"], r["cols"])[axis], plan[axis])

    def test_detect_plan_catalog_comparison(self):
        for name, expected in units.PLANS.items():
            r = self.records.get(name)
            if r is None:
                print(f"DETECT {name}: catalog record missing")
                continue
            actual = units.detect_plan(r["cell_meta"], r["rows"], r["cols"])
            print(f"DETECT {name}: {actual} expected={expected} match={actual == expected}")

    def test_plan_for_uses_builtin_plans_without_detection(self):
        with patch.object(units, "detect_plan", side_effect=AssertionError("fixed template detection forbidden")):
            for name in ("일정표(일간) · 모양 1", "신구대조표 · 모양 3"):
                with self.subTest(name=name):
                    self.assertEqual(units.plan_for(self.records[name]), units.PLANS[name])

    def test_detect_fixed_templates(self):
        fixed = [f"{category} · 모양 {number}"
                 for category, numbers in (("부연설명", range(1, 8)),
                                           ("라벨 서식", range(1, 7)),
                                           ("표(가로)", (3,)), ("현황표(가로)", (1,)),
                                           ("신구대조표", (1,)), ("조직도", (1,)))
                 for number in numbers]
        with patch.object(units, "detect_plan", side_effect=AssertionError("fixed template detection forbidden")):
            for name in fixed:
                with self.subTest(name=name):
                    self.assertEqual(units.PLANS[name], {"row": None, "col": None})
                    record = self.records.get(name, {"name": name, "rows": 1, "cols": 1})
                    self.assertEqual(units.plan_for(record), {"row": None, "col": None})

    def test_signature_preserves_internal_and_lateral_edges(self):
        for axis in ("row", "col"):
            p = units._axis(0, 1, 4, axis=axis)
            cells = [{"row": i if axis == "row" else 0,
                      "col": i if axis == "col" else 0, "rowSpan": 1, "colSpan": 1,
                      "borders": {side: {"type": "SOLID"} for side in ("top", "bottom", "left", "right")}}
                     for i in range(4)]
            leading, trailing, lateral = ("top", "bottom", "left") if axis == "row" else ("left", "right", "top")
            cells[0]["borders"][leading]["type"] = "DOUBLE"
            cells[-1]["borders"][trailing]["type"] = "DOUBLE"
            def matches():
                return units._matching_signatures([units._unit_signature(cells, axis, p, i) for i in range(4)])
            self.assertTrue(matches())
            for index, side in ((0, trailing), (3, leading), (1, leading), (0, lateral)):
                with self.subTest(axis=axis, index=index, side=side):
                    cells[index]["borders"][side]["type"] = "DASH"
                    self.assertFalse(matches())
                    cells[index]["borders"][side]["type"] = "SOLID"

    def test_column_region_cover_separator_and_fixed_tail(self):
        def cell(row, col, span=1, width=10):
            return (f'<hp:tc><hp:cellAddr rowAddr="{row}" colAddr="{col}"/>'
                    f'<hp:cellSpan rowSpan="1" colSpan="{span}"/>'
                    f'<hp:cellSz width="{width}" height="10"/></hp:tc>')
        table = ET.fromstring(f'<hp:tbl xmlns:hp="{HP[1:-1]}" rowCnt="2" colCnt="7">'
            '<hp:sz width="70" height="20"/><hp:tr>' + cell(0, 0, 7, 70) + '</hp:tr><hp:tr>'
            + ''.join(cell(1, col) for col in range(7)) + '</hp:tr></hp:tbl>')
        plan = {"row": None, "col": units._axis(1, 1, 3, 1, axis="col")}
        for target in (1, 4, 2):
            units.resize_table(table, plan, col_count=target)
            self.grid(table, width=True)
            self.assertEqual(int(table.get("colCnt")), target * 2 + 1)
            self.assertEqual(units._meta(table)[0]["colSpan"], target * 2 + 1)
            cells = table.findall(HP + "tr")[1].findall(HP + "tc")
            self.assertEqual(cells[0].find(HP + "cellSz").get("width"), "10")
            self.assertEqual(cells[-1].find(HP + "cellSz").get("width"), "10")


if __name__ == "__main__":
    unittest.main()
