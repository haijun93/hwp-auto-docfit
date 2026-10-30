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
                    p = units._capped(item["name"], axis, expected[axis])
                    self.assertEqual(item["units"][axis],
                        {k: p[k] for k in ("count", "min", "max", "core", "sep", "kind") if k in p} if p else None)

    def test_task_columns_sequential(self):
        table, plan = self.load("분야별과제표 · 모양 1")
        total = table.find(HP + "sz").get("width")
        for count in (2, 1, 4):
            units.resize_table(table, plan, col_count=count)
            self.assertEqual(int(table.get("colCnt")), count * 4)
            self.assertEqual(table.find(HP + "sz").get("width"), total)
            self.grid(table, width=True)

    def test_increment_tokens(self):
        for text, previous, expected in (
                ("2030년", "2029년", "2031년"), ("12월", "11월", "1월"),
                ("1월", "12월", "2월"), ("2주", "1주", "3주"),
                ("2일차 제2회 2)", "1일차 제1회 1)", "3일차 제3회 3)"),
                ("② Ⅱ", "① Ⅰ", "③ Ⅲ"), ("⑳ Ⅻ", "⑲ Ⅺ", "① Ⅰ"),
                ("14:20~14:25", "14:15~14:20", "14:25~14:30"),
                ("23:55", "23:45", "24:05"), ("안내문", None, "안내문"),
                # 앞 단위와 같은 값은 반복 번호다(2026-10-23 사용자 지시: 분기 1·2·3·4 반복)
                ("2030", "2030", "2030"), ("제9회", None, "제10회")):
            with self.subTest(text=text):
                self.assertEqual(units._increment_text(text, previous), expected)

    def test_fill_modes_and_edit_coordinates(self):
        for fill, expected in (("increment", "2032"), ("blank", ""), ("copy", "2030")):
            table, plan = self.load("일정표(연간) · 모양 1")
            units.resize_table(table, plan, col_count=7, fill=fill)
            self.assertEqual(catalog._text(table.findall(HP + "tr")[0].findall(HP + "tc")[-1]), expected)
        table, plan = self.load("분야별과제표 · 모양 1")
        units.resize_table(table, plan, col_count=4, fill="blank", cell_texts={"0,13": "새 제목\n둘째 줄"})
        cell = next(c for _, c in units._cells(table) if c.find(HP + "cellAddr").get("colAddr") == "13")
        self.assertEqual([catalog._text(p) for p in catalog._cell_paragraphs(cell)][:2], ["새 제목", "둘째 줄"])
        self.grid(table, width=True)

    def test_fill_preserves_split_run_format_and_blank_clears_nested(self):
        cell = ET.fromstring(f'<hp:tc xmlns:hp="{HP[1:-1]}"><hp:subList><hp:p><hp:run charPrIDRef="1"><hp:t>20</hp:t></hp:run>'
            '<hp:run charPrIDRef="2"><hp:t>30년</hp:t></hp:run></hp:p></hp:subList></hp:tc>')
        previous = copy.deepcopy(cell)
        list(previous.iter(HP + "t"))[1].text = "29년"
        units._fill_clone(cell, previous, "increment", 1)
        self.assertEqual(catalog._text(cell), "2031년")
        self.assertEqual([n.get("charPrIDRef") for n in cell.iter(HP + "run")], ["1", "2"])
        units._fill_clone(cell, previous, "blank", 1)
        self.assertEqual(catalog._text(cell), "")

    def test_nested_preview_and_new_plans_export_grid(self):
        view = units.preview(self.records["분야별과제표 · 모양 1"]["id"], SOURCE, col_count=4)
        nested = view["cell_meta"][0][1]["nested"][0]
        self.assertIn("cell_meta", nested)
        self.assertGreater(nested["rows"], 0)
        for name, axis in (("표(가로) · 모양 2", "row"), ("표(가로) · 모양 3", "col"),
                           ("현황표(가로) · 모양 1", "col")):
            record = self.records[name]
            plan = units.plan_for(record)[axis]
            self.assertIsNotNone(plan)
            for target in (1, plan["count"] + 1):
                with self.subTest(name=name, target=target), tempfile.TemporaryDirectory() as folder:
                    out = Path(folder) / "export.hwpx"
                    units.export_resized(record["id"], out, SOURCE, **{axis + "_count": target})
                    with zipfile.ZipFile(out) as archive:
                        tables = [t for n in catalog._section_names(archive)
                                  for p in ET.fromstring(archive.read(n)).findall(HP + "p") for t in catalog._top_tables(p)]
                    self.assertEqual(len(tables), 1)
                    self.grid(tables[0], width=axis == "col")

    def test_cell_text_validation_atomic(self):
        table, plan = self.load("일정표(연간) · 모양 1")
        before = ET.tostring(table)
        for texts in ({"0,2": "covered"}, {"0,99": "missing"}, {"0,1": "x" * 1001}, {"0,1": "\x00"}):
            with self.assertRaises(ValueError):
                units.resize_table(table, plan, col_count=6, cell_texts=texts)
            self.assertEqual(ET.tostring(table), before)

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
        self.assertIn("3일차", catalog._text(table.findall(HP + "tr")[17]))
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
                if axis not in ("row", "col") or p is None:   # signature 같은 부가 정보는 축이 아니다
                    continue
                for target in (p.get("min", 1), p["count"] + 1, p["max"]):
                    with self.subTest(name=name, axis=axis, target=target):
                        table, plan = self.load(name)
                        units.resize_table(table, plan, **{axis + "_count": target})
                        self.grid(table, width=axis == "col")

    def test_invalid_requests_are_atomic(self):
        table, plan = self.load("행사시간표 · 모양 1")
        original = ET.tostring(table)
        for value in (0, 51, 1.5, True):
            with self.assertRaises(ValueError):
                units.resize_table(table, plan, row_count=value)
            self.assertEqual(ET.tostring(table), original)
        with self.assertRaises(ValueError):
            units.resize_table(table, plan, row_count=3, col_count=31)
        self.assertEqual(ET.tostring(table), original)
        # 조직도 모양 1은 2.0.6부터 2~9팀으로 조절한다(1.80.15에서 꺼졌던 조절 복구). 범위 밖은 표를 바꾸지 않는다.
        table, plan = self.load("조직도 · 모양 1")
        original = ET.tostring(table)
        with self.assertRaises(ValueError):
            units.resize_table(table, plan, col_count=1)
        self.assertEqual(ET.tostring(table), original)

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
                    actual = [[{k: v for k, v in cell.items() if k != "nested"} for cell in row]
                              for row in view["cell_meta"]]
                    self.assertEqual(actual, expected)
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
                    expected = dict(units.PLANS[name])
                    for axis in ("row", "col"):
                        expected[axis] = units._capped(name, axis, expected[axis])
                    self.assertEqual(units.plan_for(self.records[name]), expected)

    def test_detect_fixed_templates(self):
        fixed = [f"{category} · 모양 {number}"
                 for category, numbers in (("부연설명", range(1, 8)),
                                           ("라벨 서식", range(1, 7)))
                 for number in numbers]
        with patch.object(units, "detect_plan", side_effect=AssertionError("fixed template detection forbidden")):
            for name in fixed:
                with self.subTest(name=name):
                    self.assertEqual(units.PLANS[name]["row"], None)
                    self.assertEqual(units.PLANS[name]["col"], None)
                    record = self.records.get(name, {"name": name, "rows": 1, "cols": 1})
                    self.assertEqual(units.plan_for(record)["row"], None)
                    self.assertEqual(units.plan_for(record)["col"], None)

        # 열 단위가 보완된 템플릿의 단위 값 검증
        self.assertEqual(units.PLANS["표(가로) · 모양 3"]["col"], units._axis(2, 2, 1, axis="col"))
        self.assertEqual(units.PLANS["현황표(가로) · 모양 1"]["col"], units._axis(0, 2, 2, axis="col"))
        for name in ("표(가로) · 모양 3", "현황표(가로) · 모양 1"):
            if name in self.records:
                actual = {k: v for k, v in units.plan_for(self.records[name]).items() if k in ("row", "col")}
                self.assertEqual(actual,
                                 {"row": units._capped(name, "row", units.PLANS[name]["row"]),
                                  "col": units._capped(name, "col", units.PLANS[name]["col"])})

    def test_plan_for_matches_by_shape_signature_when_name_changed(self):
        # 이름이 바뀌었지만 모양 서명이 같은 경우 PLANS를 정상적으로 찾는지 시험
        rec = copy.deepcopy(self.records["표(가로) · 모양 1"])
        sig = units.shape_signature(rec["cell_meta"], rec["rows"], rec["cols"])

        fake_rec = copy.deepcopy(rec)
        fake_rec["name"] = "기본형(가로) · 모양 1"
        fake_rec["category"] = "기본형(가로)"

        orig_sig = units.PLANS["표(가로) · 모양 1"].get("signature")
        try:
            units.PLANS["표(가로) · 모양 1"]["signature"] = sig
            with patch.object(units, "detect_plan", side_effect=AssertionError("detect_plan should not be called")):
                plan = units.plan_for(fake_rec)
                self.assertEqual(plan["row"], units._capped(fake_rec["name"], "row", units.PLANS["표(가로) · 모양 1"]["row"]))
                self.assertEqual(plan["col"], units._capped(fake_rec["name"], "col", units.PLANS["표(가로) · 모양 1"]["col"]))
        finally:
            units.PLANS["표(가로) · 모양 1"]["signature"] = orig_sig

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

    def test_org_chart_generation(self):
        user_catalog = Path(r"C:\HWP_AUTODOCFIT\표서식모음\표 서식모음.hwpx")
        catalog_path = user_catalog if user_catalog.is_file() else SOURCE
        records_map = {r["name"]: r for r in catalog._scan(catalog_path)}

        if "조직도 · 모양 2" not in records_map:
            self.skipTest("조직도 기준 파일에 '조직도 · 모양 2'가 없어 시험을 건너뜁니다.")

        rec_m2 = records_map["조직도 · 모양 2"]
        _, template_table, _ = units._load(rec_m2["id"], catalog_path)
        orig_width = int(template_table.find(HP + "sz").get("width"))
        # 칸 테두리를 실제 문서 정의(header.xml)로 풀어 읽는다(없으면 기본값 SOLID로 잘못 읽힘).
        import zipfile
        from defusedxml import ElementTree as DET
        with zipfile.ZipFile(catalog_path) as archive:
            header_info = catalog._header_lookup(DET.fromstring(archive.read("Contents/header.xml")))

        # N=3, 4, 5, 6, 8 시험
        for N in (3, 4, 5, 6, 8):
            with self.subTest(team_count=N):
                table = units.generate_org_chart(template_table, N)

                # 1. 그리드 무결성 및 표 폭 유지
                self.grid(table, width=True)
                self.assertEqual(int(table.find(HP + "sz").get("width")), orig_width)

                # 2. 열 수 (3N-1, N이 짝수면 +1)
                expected_cols = 3 * N if N % 2 == 0 else 3 * N - 1
                self.assertEqual(int(table.get("rowCnt")), 6)
                self.assertEqual(int(table.get("colCnt")), expected_cols)

                rows = table.findall(HP + "tr")
                self.assertEqual(len(rows), 6)

                # 3. 위 상자가 가운데
                r1_cells = rows[1].findall(HP + "tc")
                top_box = next(c for c in r1_cells if int(c.find(HP + "cellSpan").get("colSpan")) > 1)
                box_col = int(top_box.find(HP + "cellAddr").get("colAddr"))
                box_span = int(top_box.find(HP + "cellSpan").get("colSpan"))
                left_cols = box_col
                right_cols = expected_cols - (box_col + box_span)
                self.assertEqual(left_cols, right_cols, f"위 상자가 가운데에 있지 않음 ({left_cols} != {right_cols})")

                # 4. 가로 연결선이 첫 팀 가운데~마지막 팀 가운데
                r2_meta = [catalog._cell_meta(tc, 2, 0, "", header_info) for tc in rows[2].findall(HP + "tc")]
                bottom_borders = {}
                for c in r2_meta:
                    for col in range(c["col"], c["col"] + c["colSpan"]):
                        bottom_borders[col] = c["borders"]["bottom"]["type"]

                self.assertEqual(bottom_borders[0], "NONE", "col 0은 가로선이 없어야 함")
                for col in range(1, expected_cols - 1):
                    self.assertEqual(bottom_borders[col], "SOLID", f"col {col} 가로 연결선 누락")
                self.assertEqual(bottom_borders[expected_cols - 1], "NONE", "마지막 열은 가로선이 없어야 함")

                # 5. 팀마다 세로선 (가운데 경계 테두리)
                r3_meta = [catalog._cell_meta(tc, 3, 0, "", header_info) for tc in rows[3].findall(HP + "tc")]
                is_even = (N % 2 == 0)
                t_cols = {}
                cur_c = 0
                for t in range(N):
                    t_cols[t] = (cur_c, cur_c + 1)
                    cur_c += 2
                    if t < N - 1:
                        cur_c += 2 if (is_even and t == (N // 2) - 1) else 1

                for t in range(N):
                    cL, cR = t_cols[t]
                    cL_cell = next(c for c in r3_meta if c["col"] <= cL < c["col"] + c["colSpan"])
                    cR_cell = next(c for c in r3_meta if c["col"] <= cR < c["col"] + c["colSpan"])
                    has_v = (cL_cell["borders"]["right"]["type"] == "SOLID" or
                             cR_cell["borders"]["left"]["type"] == "SOLID")
                    self.assertTrue(has_v, f"팀 {t} 세로선 누락 (cL={cL}, cR={cR})")

                # 6. 팀 상자 N개, 인원 칸 N개
                # 짝수 팀이면 가운데 간격 칸도 2칸 병합이다(예시 모양 1과 같음) — 위·아래 테두리가 있는 칸만 팀 상자로 센다.
                def boxed(tc, row):
                    meta = catalog._cell_meta(tc, row, 0, "", header_info)
                    return meta["borders"]["top"]["type"] != "NONE" and meta["borders"]["bottom"]["type"] != "NONE"
                r4_teams = [c for c in rows[4].findall(HP + "tc") if boxed(c, 4)]
                self.assertEqual(len(r4_teams), N, f"팀 상자 개수 불일치: {len(r4_teams)} != {N}")
                r5_counts = [c for c in rows[5].findall(HP + "tc")
                             if int(c.find(HP + "cellSpan").get("colSpan")) == 2 and "".join(c.itertext()).strip()]
                self.assertEqual(len(r5_counts), N, f"인원 칸 개수 불일치: {len(r5_counts)} != {N}")

        # N=5는 기준 모양 2와 칸 구조·테두리 역할이 같아야 함
        t5 = units.generate_org_chart(template_table, 5)
        t5_rows = t5.findall(HP + "tr")
        ref_rows = template_table.findall(HP + "tr")
        for r_idx in range(6):
            new_tcs = t5_rows[r_idx].findall(HP + "tc")
            ref_tcs = ref_rows[r_idx].findall(HP + "tc")
            self.assertEqual(len(new_tcs), len(ref_tcs), f"행 {r_idx} 칸 개수 불일치")
            for c_idx in range(len(new_tcs)):
                m_new = catalog._cell_meta(new_tcs[c_idx], r_idx, 0, "", header_info)
                m_ref = catalog._cell_meta(ref_tcs[c_idx], r_idx, 0, "", header_info)
                self.assertEqual(m_new["col"], m_ref["col"])
                self.assertEqual(m_new["colSpan"], m_ref["colSpan"])
                self.assertEqual(m_new["rowSpan"], m_ref["rowSpan"])
                for side in ("top", "bottom", "left", "right"):
                    self.assertEqual(m_new["borders"][side]["type"], m_ref["borders"][side]["type"],
                                     f"행 {r_idx} 칸 {c_idx} {side} 테두리 불일치")

        # N=4는 모양 1과 열 수(12열) 및 테두리 역할(가로선 범위·세로선 위치)이 같아야 함
        if "조직도 · 모양 1" in records_map:
            rec_m1 = records_map["조직도 · 모양 1"]
            _, table_m1, _ = units._load(rec_m1["id"], catalog_path)
            t4 = units.generate_org_chart(template_table, 4)
            self.assertEqual(int(t4.get("colCnt")), int(table_m1.get("colCnt")))
            r2_t4 = [catalog._cell_meta(tc, 2, 0, "", header_info) for tc in t4.findall(HP + "tr")[2].findall(HP + "tc")]
            r2_m1 = [catalog._cell_meta(tc, 2, 0, "", header_info) for tc in table_m1.findall(HP + "tr")[2].findall(HP + "tc")]
            b_t4 = {col: c["borders"]["bottom"]["type"] for c in r2_t4 for col in range(c["col"], c["col"] + c["colSpan"])}
            b_m1 = {col: c["borders"]["bottom"]["type"] for c in r2_m1 for col in range(c["col"], c["col"] + c["colSpan"])}
            self.assertEqual(b_t4, b_m1, "N=4 가로선 범위가 모양 1과 일치해야 함")

        # N=6은 모양 3과 열 수(18열)가 같아야 함
        if "조직도 · 모양 3" in records_map:
            rec_m3 = records_map["조직도 · 모양 3"]
            _, table_m3, _ = units._load(rec_m3["id"], catalog_path)
            t6 = units.generate_org_chart(template_table, 6)
            self.assertEqual(int(t6.get("colCnt")), int(table_m3.get("colCnt")))

        # 기존 정보단위 체계 연결(resize_table, describe_units) 시험
        plan = units.plan_for(rec_m2)
        self.assertIsNotNone(plan["col"])
        self.assertEqual(plan["col"]["kind"], "org_chart")
        self.assertEqual(plan["col"]["count"], 5)

        working = copy.deepcopy(template_table)
        units.resize_table(working, plan, col_count=3)
        self.assertEqual(plan["col"]["count"], 3)
        self.assertEqual(int(working.get("colCnt")), 8)
        self.grid(working, width=True)

        descriptions = units.describe_units(catalog_path)
        org_items = [d for d in descriptions if d.get("category") == "조직도"]
        self.assertEqual(len(org_items), 1, "목록에서 조직도는 1개만 노출되어야 함")
        self.assertEqual(org_items[0]["name"], "조직도")
        self.assertEqual(org_items[0]["units"]["col"]["kind"], "org_chart")

    def test_org_chart_top_box_width_and_centering(self):
        user_catalog = Path(r"C:\HWP_AUTODOCFIT\표서식모음\표 서식모음.hwpx")
        catalog_path = user_catalog if user_catalog.is_file() else SOURCE
        records_map = {r["name"]: r for r in catalog._scan(catalog_path)}
        if "조직도 · 모양 2" not in records_map:
            self.skipTest("조직도 · 모양 2가 없어 시험을 건너뜁니다.")

        rec_m2 = records_map["조직도 · 모양 2"]
        _, template_table, _ = units._load(rec_m2["id"], catalog_path)
        ref_top_box = next(c for c in template_table.findall(HP + "tr")[1].findall(HP + "tc")
                           if int(c.find(HP + "cellSpan").get("colSpan")) > 1)
        ref_width = int(ref_top_box.find(HP + "cellSz").get("width"))

        for N in range(2, 11):
            with self.subTest(team_count=N):
                table = units.generate_org_chart(template_table, N)

                # 1. 그리드 무결성
                self.grid(table, width=True)

                # 2. 가운데 정렬
                total_cols = int(table.get("colCnt"))
                r1_cells = table.findall(HP + "tr")[1].findall(HP + "tc")
                top_box = next(c for c in r1_cells if int(c.find(HP + "cellSpan").get("colSpan")) > 1)
                box_col = int(top_box.find(HP + "cellAddr").get("colAddr"))
                box_span = int(top_box.find(HP + "cellSpan").get("colSpan"))
                left_cols = box_col
                right_cols = total_cols - (box_col + box_span)
                self.assertEqual(left_cols, right_cols, f"N={N} 위 상자 가운데 정렬 불일치 ({left_cols} != {right_cols})")

                # 3. 위 상자 폭 >= 기준 폭 * 0.95
                box_width = int(top_box.find(HP + "cellSz").get("width"))
                self.assertGreaterEqual(box_width, ref_width * 0.95,
                                        f"N={N} 위 상자 폭 부족: {box_width} < {ref_width * 0.95}")



class C13TableUnitsTests(unittest.TestCase):
    grid = TableUnitsTests.grid

    @classmethod
    def setUpClass(cls):
        cls.sources = [SOURCE]
        user = Path(r"C:\HWP_AUTODOCFIT\표서식모음\표 서식모음.hwpx")
        if user.is_file():
            cls.sources.append(user)
        cls.records = {path: {r["name"]: r for r in catalog._scan(path)} for path in cls.sources}

    def check_axes(self, name, axes):
        for source in self.sources:
            rec = self.records[source][name]
            for axis in axes:
                with self.subTest(source=str(source), name=name, axis=axis):
                    p = units.plan_for(rec)[axis]
                    self.assertIsNotNone(p)
                    self.assertEqual(p["min"], 1)
                    # 최대값: 50, 깨지는 축은 실측값(AXIS_CAPS) — 2026-10-23 사용자 지시
                    self.assertEqual(p["max"], max(p["count"], units.AXIS_CAPS.get((name, axis), units.UNIT_MAX)))
                    for target in (p["min"], p["count"] + 1, p["max"]):
                        _, table, _ = units._load(rec["id"], source)
                        plan = units.plan_for(rec)
                        units.resize_table(table, plan, **{axis + "_count": target})
                        self.grid(table, width=axis == "col")
                        self.assertEqual(int(table.get(axis + "Cnt")),
                                         rec["rows" if axis == "row" else "cols"] +
                                         (target - p["count"]) * (p["core"] + p["sep"]))
                    _, table, _ = units._load(rec["id"], source)
                    before = ET.tostring(table)
                    plan = units.plan_for(rec)
                    for target in (0, p["max"] + 1):
                        with self.assertRaises(ValueError):
                            units.resize_table(table, plan, **{axis + "_count": target})
                        self.assertEqual(ET.tostring(table), before)

    def test_c13_01_status_rows(self):
        self.check_axes("현황표(가로) · 모양 1", ("row", "col"))

    def test_c13_02_horizontal_rows_keep_columns(self):
        for number in range(1, 6):
            self.check_axes(f"추진절차(가로) · 모양 {number}", ("row", "col"))

    def test_c13_03_both_process_axes(self):
        self.check_axes("추진절차(가로세로) · 모양 1", ("row", "col"))
        for source in self.sources:
            rec = self.records[source]["추진절차(가로세로) · 모양 1"]
            _, table, _ = units._load(rec["id"], source)
            plan = units.plan_for(rec)
            units.resize_table(table, plan, row_count=plan["row"]["count"] + 1,
                               col_count=plan["col"]["count"] + 1)
            self.grid(table, width=True)

    def test_c13_04_comparison_rows_and_merged_arrow(self):
        self.check_axes("신구대조표 · 모양 1", ("row",))
        for source in self.sources:
            rec = self.records[source]["신구대조표 · 모양 1"]
            target = units.plan_for(rec)["row"]["count"] + 1
            view = units.preview(rec["id"], source, row_count=target)
            center = next(c for row in view["cell_meta"] for c in row if c["col"] == 1)
            self.assertEqual(center["rowSpan"], view["rows"])

    def test_c13_05_blank_information_pair(self):
        self.check_axes("신구대조표 · 모양 3", ("row",))
        for source in self.sources:
            rec = self.records[source]["신구대조표 · 모양 3"]
            p = units.plan_for(rec)["row"]
            self.assertEqual((p["start"], p["core"], p["count"]), (1, 2, 3))
            view = units.preview(rec["id"], source, row_count=4)
            self.assertEqual(view["rows"], 9)
            # 늘린 한 쌍 = 빈 칸 행(낮은 행) + 정보 행(높은 행). 원본 정보 행도 비어 있어 글이 아니라 행 높이로 쌍을 확인한다.
            heights = [row[0]["height"] for row in view["cell_meta"]]
            self.assertTrue(all(not c["text"] for c in view["cell_meta"][7]))
            self.assertEqual(heights[7], heights[5])
            self.assertEqual(heights[8], heights[6])
            self.assertLess(heights[7], heights[8])
            self.assertEqual(units.preview(rec["id"], source, row_count=2)["rows"], 5)

    def test_photo_attachment_stacks_two_row_block_by_exact_name(self):
        """사진첨부용: 이름이 같은 판정표가 모양 서명이 겹치는 다른 표보다 우선하고, 행 단위는 사진+설명 두 행 묶음이다."""
        meta = [[{"row": r, "col": c, "rowSpan": 1, "colSpan": 1, "text": "", "fill": None} for c in range(4)] for r in range(2)]
        for number in (1, 2):
            plan = units.plan_for({"name": f"사진첨부용 · 모양 {number}", "rows": 2, "cols": 4, "cell_meta": meta})
            self.assertEqual((plan["row"]["start"], plan["row"]["core"], plan["row"]["count"]), (0, 2, 1))
            self.assertEqual((plan["col"]["core"], plan["col"]["count"]), (1, 4))

    def test_c13_06_daily_columns(self):
        self.check_axes("일정표(일간) · 모양 1", ("row", "col"))

    def test_c13_07_timetable_columns(self):
        self.check_axes("행사시간표 · 모양 1", ("row", "col"))

    def test_c13_08_event_columns(self):
        self.check_axes("행사표(1일) · 모양 1", ("row", "col"))

    def shape_views(self, name):
        for source in self.sources:
            rec = self.records[source][name]
            view = units.preview(rec["id"], source)
            for row in view["cell_meta"]:
                for cell in row:
                    self.assertIn("shapes", cell)
                    for shape in cell["shapes"]:
                        self.assertTrue({"kind", "x", "y", "w", "h", "direction", "fill", "line", "text"} <= shape.keys())
                        self.assertIn(shape["kind"], ("arrow", "triangle", "line", "rect", "ellipse", "pic", "other"))
                        self.assertGreater(shape["w"], 0)
                        self.assertGreater(shape["h"], 0)
            yield source, rec, view

    def test_c13_09_process_polygon_and_clone(self):
        for source, rec, view in self.shape_views("추진절차(가로세로) · 모양 1"):
            if rec["cols"] != 3:
                continue
            shapes = [s for row in view["cell_meta"] for c in row for s in c["shapes"]]
            self.assertEqual([(s["kind"], s["direction"]) for s in shapes], [("arrow", "right")])
            grown = units.preview(rec["id"], source, col_count=3, row_count=6)
            self.assertEqual(sum(len(c["shapes"]) for row in grown["cell_meta"] for c in row), 2)
            self.assertEqual(sum(c["text"] == "↓" for row in grown["cell_meta"] for c in row), 15)

    def test_c13_10_vertical_pictures_and_clone_ids(self):
        for source, rec, view in self.shape_views("추진절차(세로) · 모양 1"):
            shapes = [s for row in view["cell_meta"] for c in row for s in c["shapes"]]
            self.assertEqual(len(shapes), 5)
            self.assertTrue(all(s["kind"] == "pic" and s["src"].startswith("data:image/") for s in shapes))
            _, table, _ = units._load(rec["id"], source)
            plan = units.plan_for(rec)
            for target in (7, 1, 8):
                units.resize_table(table, plan, row_count=target)
                self.grid(table)
                pics = list(table.iter(HP + "pic"))
                self.assertEqual(len(pics), target - 1)
                for attr in ("id", "instid", "zOrder"):
                    values = [p.get(attr) for p in pics]
                    self.assertEqual(len(values), len(set(values)))
            # 이 표의 단계 표시는 칸 글이 아니라 그림 안에 있다(칸 글 없음) — 그림 수·번호 중복 없음으로 확인한다.

    def test_c13_11_comparison_background_picture(self):
        for source, rec, view in self.shape_views("신구대조표 · 모양 1"):
            if rec["cell_meta"][0][1]["rowSpan"] != 5:
                continue
            shape = view["cell_meta"][0][1]["shapes"][0]
            self.assertEqual(shape["kind"], "pic")
            self.assertTrue(shape["src"].startswith("data:image/png;base64,"))
            grown = units.preview(rec["id"], source, row_count=5)
            self.assertEqual(grown["cell_meta"][0][1]["shapes"], [shape])

    def test_snapshot_revision_and_outside_drawing_crop(self):
        from docfit_app.table_units_service import crop_to_content, _digest, SNAPSHOT_REVISION
        from PIL import Image, ImageDraw
        import hashlib
        self.assertNotEqual(_digest(SOURCE), hashlib.sha256(SOURCE.read_bytes()).hexdigest()[:16])
        self.assertTrue(SNAPSHOT_REVISION)
        image = Image.new("RGB", (200, 100), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((50, 20, 130, 70), outline="black")
        draw.polygon(((140, 40), (180, 50), (140, 60)), fill="gray")
        cropped = crop_to_content(image, margin=0)
        self.assertEqual(cropped.size, (131, 51))
        self.assertEqual(cropped.getpixel((130, 30)), (128, 128, 128))

    def test_drawing_geometry_and_text_symbols(self):
        cell = ET.fromstring(f'<hp:tc xmlns:hp="{HP[1:-1]}"><hp:subList><hp:p><hp:run><hp:t>→</hp:t>'
            '<hp:polygon><hp:curSz width="20" height="30"/><hp:rotationInfo angle="90"/>'
            '<hp:sz width="20" height="30"/><hp:pos treatAsChar="0" horzOffset="120" vertOffset="-10"/>'
            '<hp:shapeComment>오른쪽 화살표</hp:shapeComment></hp:polygon></hp:run></hp:p></hp:subList>'
            '<hp:cellSz width="100" height="50"/></hp:tc>')
        shapes = catalog._cell_meta(cell, 0, 0, "→", None)["shapes"]
        self.assertEqual(len(shapes), 1)
        self.assertEqual((shapes[0]["x"], shapes[0]["y"], shapes[0]["w"], shapes[0]["h"]), (1.2, -.2, .2, .6))
        self.assertEqual(shapes[0]["direction"], "down")


if __name__ == "__main__":
    unittest.main()


class IncrementAndScheduleTests(unittest.TestCase):
    """2026-10-23 사용자 실측: 반복 번호는 반복, 날짜는 달력대로, 주간표는 첫 날짜 기준 주 단위, 최대값 50·실측 상한."""

    def test_equal_tokens_repeat_and_dates_follow_calendar(self):
        self.assertEqual(units._increment_text("1", "1"), "1")            # 분기 1·2·3·4 반복
        self.assertEqual(units._increment_text("2027", "2026"), "2028")
        self.assertEqual(units._increment_text("2026.10.28.(수)", "2026.10.27.(화)"), "2026.10.29.(목)")
        self.assertEqual(units._increment_text("12.31.(목)", "12.30.(수)"), "1.1.(금)")
        self.assertEqual(units._increment_text("5.23.~5.25.", "5.16.~5.22."), "5.30.~6.5.")
        self.assertEqual(units._increment_text("2026.10.28.(수)"), "2026.10.29.(목)")

    def test_annual_quarters_repeat_when_years_grow(self):
        rid = next(r["id"] for r in units.describe_units(SOURCE) if r["name"] == "일정표(연간) · 모양 1")
        view = units.preview(rid, SOURCE, col_count=7)
        quarters = view["cells"][1]
        self.assertEqual(quarters, ["1", "2", "3", "4"] * (len(quarters) // 4))

    def test_weekly_first_date_drives_week_ranges(self):
        rid = next(r["id"] for r in units.describe_units(SOURCE) if r["name"] == "일정표(주간) · 모양 1")
        view = units.preview(rid, SOURCE, col_count=7)
        self.assertEqual(view["cells"][0][1:8], [f"{k}주" for k in range(1, 8)])
        self.assertEqual(view["cells"][1][:3], ["4.26.~5.1.", "5.2.~5.8.", "5.9.~5.15."])
        self.assertEqual(view["cells"][0][-1], "당일")                      # 끝 열은 단위가 아니다
        view = units.preview(rid, SOURCE, col_count=5, cell_texts={"1,1": "6.1."})
        self.assertEqual(view["cells"][1][:2], ["6.1.~6.5.", "6.6.~6.12."])

    def test_unit_maximum_is_fifty_unless_measured_cap(self):
        for item in units.describe_units(SOURCE):
            for axis, p in (item["units"] or {}).items():
                if p:
                    with self.subTest(name=item["name"], axis=axis):
                        cap = units.AXIS_CAPS.get((item["name"], axis), units.UNIT_MAX)
                        if p.get("kind") in ("org_chart", "org_chart_wide"):
                            cap = units.AXIS_CAPS[("조직도", "col")]
                        self.assertEqual(p["max"], max(p["count"], cap))
