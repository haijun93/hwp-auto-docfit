"""HWPX 표 → 표그림판 그림(docfit_core.table_import, 서비스 import_hwpx_table). 합성 시료는 scripts/make_timport_fixtures.py."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from docfit_app.table_sketch_service import TableSketchService
from docfit_core import table_sketch
from docfit_core.table_import import import_hwpx_table, list_hwpx_tables

FIX = Path(__file__).parent / "fixtures"


def load(name, **kw):
    return import_hwpx_table(FIX / f"timport_{name}.hwpx", **kw)


def segs(sketch):
    return {(l["x1"], l["y1"], l["x2"], l["y2"]): (l["width"], l["style"], l.get("color", "#000000")) for l in sketch["lines"]}


class TableImportTest(unittest.TestCase):
    def test_basic_grid_text_bold_align(self):
        sketch, info = load("basic")
        self.assertEqual((info["rows"], info["cols"], info["warnings"]), (2, 2, []))
        self.assertEqual(sorted(segs(sketch)), sorted([(1, 1, 9, 1), (1, 3, 9, 3), (1, 5, 9, 5), (1, 1, 1, 5), (5, 1, 5, 5), (9, 1, 9, 5)]))
        texts = {t["text"]: t for t in sketch["texts"]}
        self.assertEqual((texts["가"]["x"], texts["가"]["y"], texts["가"]["bold"], texts["가"]["align"]), (1, 1, False, "center"))
        self.assertTrue(texts["나"]["bold"])
        self.assertEqual(texts["다"]["align"], "left")
        self.assertEqual(texts["라"]["align"], "right")
        self.assertEqual((texts["라"]["x"], texts["라"]["y"]), (5, 3))

    def test_center_merge_has_no_inner_lines(self):
        sketch, _ = load("merge_center")
        preview = table_sketch.preview(sketch)
        self.assertTrue(preview["ok"], preview["warnings"])
        spans = {(c["row"], c["col"]): (c["rowspan"], c["colspan"]) for c in preview["cells"]}
        self.assertEqual(spans[(0, 1)], (2, 2))
        self.assertEqual((preview["rows"], preview["cols"]), (3, 4))
        lines = segs(sketch)
        self.assertNotIn((5, 3, 13, 3), lines)  # 병합 칸 안쪽 가로선 없음
        self.assertIn((9, 5, 9, 7), lines)     # 병합 아래 칸 사이 세로선은 있음
        self.assertNotIn((9, 1, 9, 5), lines)

    def test_uneven_cells_round_to_grid(self):
        sketch, _ = load("uneven")
        xs = sorted({k[0] for k in segs(sketch) if k[0] == k[2]})
        ys = sorted({k[1] for k in segs(sketch) if k[1] == k[3]})
        self.assertEqual(xs, [1, 3, 9, 13])  # 10·30·20mm = 2·6·4칸
        self.assertEqual(ys, [1, 3, 7])      # 10·20mm = 2·4칸
        by = {t["text"]: t["x"] for t in sketch["texts"]}
        self.assertEqual((by["x"], by["y"], by["z"]), (1, 3, 9))
        self.assertEqual(load("uneven", cell_mm=10.0)[0]["grid"]["cell_mm"], 10.0)

    def test_border_weights_and_styles(self):
        lines = segs(load("borders")[0])
        self.assertEqual(lines[(1, 1, 5, 1)], ("thick", "solid", "#000000"))
        self.assertEqual(lines[(5, 1, 9, 1)], ("double", "solid", "#000000"))
        self.assertEqual(lines[(1, 5, 5, 5)], ("thin", "dot", "#000000"))
        self.assertEqual(lines[(1, 3, 1, 5)], ("thin", "dash", "#000000"))
        # 이웃 칸이 다르면 굵은 쪽: 굵은 칸(0,0)과 이중선 칸(0,1) 사이 세로선은 이중선
        self.assertEqual(lines[(5, 1, 5, 3)][0], "double")
        self.assertEqual(lines[(5, 3, 5, 5)][0], "thick")  # 이중 아닌 칸 사이: 굵은 칸 쪽
        self.assertTrue(table_sketch.preview(load("borders")[0])["ok"])

    def test_fill_color_and_white_ignored(self):
        sketch, _ = load("fill")
        self.assertEqual(sketch["fills"], [dict(x1=1, y1=1, x2=5, y2=3, color="#FCE4D6")])

    def test_empty_cells_and_no_border_cells(self):
        sketch, _ = load("empty")
        self.assertEqual([t["text"] for t in sketch["texts"]], ["끝"])
        lines = segs(sketch)
        self.assertNotIn((1, 5, 5, 5), lines)  # 선 없는 칸(1,0)의 아래·왼쪽은 선 없음
        self.assertNotIn((1, 3, 1, 5), lines)
        self.assertIn((5, 5, 9, 5), lines)

    def test_table_index_selects_table(self):
        first, info = load("two_tables")
        second, _ = load("two_tables", index=1)
        self.assertEqual(info["tables"], 2)
        self.assertEqual(first["texts"][0]["text"], "첫째")
        self.assertEqual(second["texts"][0]["text"], "둘째")
        self.assertEqual(segs(second)[(1, 1, 9, 1)][0], "thick")
        with self.assertRaises(ValueError):
            load("two_tables", index=2)

    def test_unsupported_properties_are_reported(self):
        _, info = load("unsupported")
        text = " ".join(info["warnings"])
        self.assertIn("대각선", text)
        self.assertIn("칸 그림 배경", text)

    def test_rejects_bad_input(self):
        for name in ("no_table", "too_wide"):
            with self.assertRaises(ValueError, msg=name):
                load(name)
        with self.assertRaises(ValueError):
            load("basic", index=-1)
        with self.assertRaises(ValueError):
            load("basic", index=True)
        with self.assertRaises(ValueError):
            load("basic", cell_mm=0)

    def test_untrusted_archive_and_xml(self):
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "bad.hwpx"
            bad.write_bytes(b"not a zip")
            with self.assertRaises(ValueError):
                import_hwpx_table(bad)
            evil = Path(folder) / "evil.hwpx"
            xml = ('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;&a;">]>'
                   '<sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">&b;</sec>')
            with zipfile.ZipFile(evil, "w") as z:
                z.writestr("Contents/header.xml", "<head/>")
                z.writestr("Contents/section0.xml", xml)
            with self.assertRaises(ValueError):
                import_hwpx_table(evil)

    def test_service_command(self):
        with tempfile.TemporaryDirectory() as folder:
            service = TableSketchService(folder)
            result = service.command("import_hwpx_table", dict(path=str(FIX / "timport_fill.hwpx")))
            self.assertTrue(result["ok"], result)
            self.assertEqual((result["rows"], result["cols"], result["tables"]), (1, 2, 1))
            self.assertTrue(table_sketch.preview(result["sketch"])["ok"])
            two = service.command("import_hwpx_table", dict(path=str(FIX / "timport_two_tables.hwpx"), index=1))
            self.assertEqual(two["sketch"]["texts"][0]["text"], "둘째")
            for bad in (None, dict(), dict(path=str(FIX / "nope.hwpx")), dict(path=str(FIX / "timport_fill.hwpx"), index=9),
                        dict(path=str(FIX / "timport_no_table.hwpx"))):
                self.assertFalse(service.command("import_hwpx_table", bad)["ok"], bad)

    def test_list_tables_summary(self):
        found = list_hwpx_tables(FIX / "timport_two_tables.hwpx")
        self.assertEqual(found["total"], 2)
        self.assertEqual([(t["index"], t["first_text"], t["ok"]) for t in found["tables"]], [(0, "첫째", True), (1, "둘째", True)])
        basic = list_hwpx_tables(FIX / "timport_basic.hwpx")["tables"]
        self.assertEqual((basic[0]["rows"], basic[0]["cols"], basic[0]["first_text"], basic[0]["reason"]), (2, 2, "가", ""))
        self.assertEqual(list_hwpx_tables(FIX / "timport_no_table.hwpx"), dict(tables=[], total=0))
        wide = list_hwpx_tables(FIX / "timport_too_wide.hwpx")["tables"][0]
        self.assertEqual((wide["ok"], wide["cols"]), (False, 201))
        self.assertIn("너무 커서", wide["reason"])
        # 칸 간격을 좁혀도(60mm 폭 → 0.5mm 120칸) 200칸 안이면 가져올 수 있다.
        self.assertTrue(list_hwpx_tables(FIX / "timport_uneven.hwpx", cell_mm=0.5)["tables"][0]["ok"])
        with self.assertRaises(ValueError):
            list_hwpx_tables(FIX / "timport_basic.hwpx", cell_mm=0)

    def test_service_list_command(self):
        with tempfile.TemporaryDirectory() as folder:
            service = TableSketchService(folder)
            result = service.command("list_hwpx_tables", dict(path=str(FIX / "timport_two_tables.hwpx")))
            self.assertTrue(result["ok"], result)
            self.assertEqual([t["first_text"] for t in result["tables"]], ["첫째", "둘째"])
            empty = service.command("list_hwpx_tables", dict(path=str(FIX / "timport_no_table.hwpx")))
            self.assertEqual((empty["ok"], empty["tables"], empty["message"]), (True, [], "이 문서에는 표가 없습니다."))
            for bad in (None, dict(), dict(path=str(FIX / "nope.hwpx")), dict(path=str(FIX / "timport_basic.hwpx") + ".txt")):
                self.assertFalse(service.command("list_hwpx_tables", bad)["ok"], bad)
            with tempfile.NamedTemporaryFile(suffix=".hwpx", dir=folder, delete=False) as bad:
                bad.write(b"not a zip")
            self.assertFalse(service.command("list_hwpx_tables", dict(path=bad.name))["ok"])


if __name__ == "__main__":
    unittest.main()
