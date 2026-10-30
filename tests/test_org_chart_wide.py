"""내장 '조직도 · 모양 1'(5행) 정보단위(팀 수) 조절 복구와 표 템플릿 목록 순서(2.0.6)."""
import unittest

from docfit_app.table_units_service import TableUnitsService, _is_last_category
from docfit_core import table_catalog, table_units

CATALOG = table_catalog.default_catalog_path()


def _record(name):
    return next(r for r in table_catalog._scan(CATALOG) if r["name"] == name)


class OrgChartWideTest(unittest.TestCase):
    def test_every_builtin_org_chart_is_adjustable(self):
        # 카탈로그에 조직도가 새로 들어와도 조절이 조용히 꺼지지 않게 한다.
        org = [r for r in table_catalog._scan(CATALOG) if r["category"] == "조직도"]
        self.assertTrue(org)
        for record in org:
            plan = table_units.plan_for(record)["col"]
            self.assertIsNotNone(plan, record["name"])
            self.assertEqual(plan["count"], 6)

    def test_team_count_changes_and_round_trip(self):
        record = _record("조직도 · 모양 1")
        base = table_units.preview(record["id"], CATALOG)
        same = table_units.preview(record["id"], CATALOG, col_count=6)
        self.assertEqual(same["cell_meta"], base["cell_meta"])
        for teams, cols in ((2, 6), (3, 8), (4, 12), (5, 14), (7, 20), (9, 26)):
            result = table_units.preview(record["id"], CATALOG, col_count=teams)
            self.assertEqual((result["rows"], result["cols"]), (5, cols), teams)
            boxes = [t for t in result["cells"][3] if t]
            self.assertEqual(len(boxes), teams)
            self.assertEqual(boxes[:2], ["관광정책과", "지역경제과"])
            self.assertEqual([t for t in result["cells"][0] if t], ["문화경제국"])
            # 행마다 칸이 표 전체 열을 빈틈없이 덮는다.
            for row in result["cell_meta"]:
                self.assertEqual(sum(cell["colSpan"] for cell in row), cols)

    def test_limits_keep_the_table(self):
        record = _record("조직도 · 모양 1")
        for bad in (1, 10):
            with self.assertRaises(ValueError):
                table_units.preview(record["id"], CATALOG, col_count=bad)
        with self.assertRaises(ValueError):
            table_units.preview(record["id"], CATALOG, row_count=2)


class TemplateOrderTest(unittest.TestCase):
    def test_label_templates_come_last_and_others_keep_order(self):
        listing = TableUnitsService(source=CATALOG).list()["templates"]
        categories = [t["category"] for t in listing]
        labels = [i for i, c in enumerate(categories) if _is_last_category(c)]
        self.assertTrue(labels)
        self.assertEqual(labels, list(range(len(categories) - len(labels), len(categories))))
        others = [t["id"] for t in listing if not _is_last_category(t["category"])]
        builtin = [t["id"] for t in table_units.describe_units(CATALOG) if not _is_last_category(t["category"])]
        self.assertEqual(others[:len(builtin)], builtin)
        self.assertTrue(_is_last_category("라벨서식"))


if __name__ == "__main__":
    unittest.main()
