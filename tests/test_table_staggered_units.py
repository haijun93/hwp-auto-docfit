"""불규칙 표 정보단위(TMPL231): 신구대조표 모양 1의 엇갈린 병합(왼쪽·오른쪽 칸이 한 줄씩 어긋난 2행 묶음)."""
import copy
import unittest
import xml.etree.ElementTree as StdET

from docfit_core import table_catalog, table_units

CATALOG = table_catalog.default_catalog_path()
NAME = "신구대조표 · 모양 1"


def _record():
    return next(r for r in table_catalog._scan(CATALOG) if r["name"] == NAME)


def _columns(table):
    """열마다 (시작 행, 행 수) 목록. 전체를 덮는 가운데 칸은 따로."""
    result = {}
    for c in table_units._meta(table):
        result.setdefault(c["col"], []).append((c["row"], c["rowSpan"]))
    return {col: sorted(v) for col, v in result.items()}


class StaggeredComparisonTest(unittest.TestCase):
    def setUp(self):
        self.record = _record()
        _, self.table, _ = table_units._load(self.record["id"], CATALOG)

    def test_plan_is_two_row_staggered_unit(self):
        plan = table_units.plan_for(self.record)
        self.assertIsNone(plan["col"])
        row = plan["row"]
        self.assertEqual((row["kind"], row["start"], row["core"], row["count"], row["min"]),
                         ("staggered", 1, 2, 4, 1))
        units = next(d for d in table_units.describe_units(CATALOG) if d["name"] == NAME)["units"]
        self.assertEqual(units["row"]["count"], 4)
        self.assertEqual(units["row"]["kind"], "staggered")

    def test_resize_keeps_staggered_merge_shape(self):
        for target in (1, 2, 3, 5, 8):
            with self.subTest(target=target):
                table = copy.deepcopy(self.table)
                plan = table_units.plan_for(self.record)
                table_units.resize_table(table, plan, row_count=target)
                rows = 1 + 2 * target
                self.assertEqual(int(table.get("rowCnt")), rows)
                self.assertEqual(len(table.findall(table_units.HP + "tr")), rows)
                cols = _columns(table)
                # 왼쪽(현행): 머리말, 반 칸, 2행 칸(target-1개), 반 칸.
                self.assertEqual([s for _, s in cols[0]], [1, 1] + [2] * (target - 1) + [1])
                # 오른쪽(개선): 머리말 + 2행 칸 target개(왼쪽보다 한 줄 어긋남).
                self.assertEqual([s for _, s in cols[2]], [1] + [2] * target)
                # 가운데 화살표 칸은 표 전체 높이를 덮는다.
                self.assertEqual(cols[1], [(0, rows)])
                # 칸이 행을 빈틈없이 이어 덮고, 칸 높이는 덮는 행 높이 합과 같다.
                for col, spans in cols.items():
                    self.assertEqual([r for r, _ in spans],
                                     [sum(s for _, s in spans[:i]) for i in range(len(spans))], col)
                sizes = table_units._sizes(table, "row")
                for c in table_units._meta(table):
                    self.assertEqual(c["height"], sum(sizes[c["row"]:c["row"] + c["rowSpan"]]))
                self.assertEqual(int(table.find(table_units.HP + "sz").get("height")), sum(sizes))
                # tr 안의 칸은 그 행 좌표를 가진다.
                for index, tr in enumerate(table.findall(table_units.HP + "tr")):
                    for tc in tr.findall(table_units.HP + "tc"):
                        self.assertEqual(int(tc.find(table_units.HP + "cellAddr").get("rowAddr")), index)

    def test_round_trip_restores_original(self):
        original = StdET.tostring(self.table)
        for sequence in ((7, 4), (2, 4), (4,), (7, 1, 4), (1, 9, 2, 4)):
            with self.subTest(sequence=sequence):
                table = copy.deepcopy(self.table)
                plan = table_units.plan_for(self.record)
                for target in sequence:
                    table_units.resize_table(table, plan, row_count=target)
                self.assertEqual(StdET.tostring(table), original)
        # 1개까지 줄였다 다시 늘려도 모양(병합 배치)은 같다.
        table = copy.deepcopy(self.table)
        plan = table_units.plan_for(self.record)
        for target in (1, 6, 4):
            table_units.resize_table(table, plan, row_count=target)
        self.assertEqual(_columns(table), _columns(self.table))

    def test_limits_reject_and_keep_table(self):
        plan = table_units.plan_for(self.record)
        before = StdET.tostring(self.table)
        for target in (0, plan["row"]["max"] + 1):
            with self.assertRaises(ValueError):
                table_units.resize_table(self.table, plan, row_count=target)
            self.assertEqual(StdET.tostring(self.table), before)
        with self.assertRaises(ValueError):
            table_units.resize_table(self.table, plan, col_count=2)

    def test_preview_and_export_use_staggered_unit(self):
        view = table_units.preview(self.record["id"], CATALOG, row_count=6, fill="blank")
        self.assertEqual(view["rows"], 13)
        center = next(c for row in view["cell_meta"] for c in row if c["col"] == 1)
        self.assertEqual(center["rowSpan"], 13)

    def test_other_names_or_shapes_do_not_use_staggered_engine(self):
        # 이름만 같고 칸이 엇갈리지 않은 표(사용자 서식모음형)는 일반 행 단위로 판정한다.
        fake = copy.deepcopy(self.record)
        meta = [[{**c, "rowSpan": 1} if c["col"] != 1 else c for c in row] for row in fake["cell_meta"]]
        fake["cell_meta"] = meta
        plan = table_units.plan_for(fake)
        self.assertTrue(plan["row"] is None or plan["row"].get("kind") != "staggered")


class IrregularUnitsCheckTest(unittest.TestCase):
    """불규칙 표 정보단위 정의 확인: 현황표(행·열), 조직도(팀 수)."""

    def test_status_table_has_row_and_col_units(self):
        record = next(r for r in table_catalog._scan(CATALOG) if r["name"] == "현황표(가로) · 모양 1")
        plan = table_units.plan_for(record)
        self.assertEqual((plan["row"]["start"], plan["row"]["core"], plan["row"]["count"]), (3, 1, 2))
        self.assertEqual((plan["col"]["start"], plan["col"]["core"], plan["col"]["count"]), (0, 2, 2))
        grown = table_units.preview(record["id"], CATALOG, row_count=4, col_count=3)
        self.assertEqual((grown["rows"], grown["cols"]), (7, 6))

    def test_org_charts_adjust_by_team(self):
        for record in table_catalog._scan(CATALOG):
            if record["category"] == "조직도":
                self.assertIn(table_units.plan_for(record)["col"]["kind"], ("org_chart", "org_chart_wide"))


if __name__ == "__main__":
    unittest.main()
