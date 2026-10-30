"""표 템플릿 화살표 바꾸기(2.0.6)."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from docfit_core import table_arrows, table_catalog, table_units

CATALOG = table_catalog.default_catalog_path()
HP = table_arrows.HP


def _records():
    return {r["name"]: r for r in table_catalog._scan(CATALOG)}


class TableArrowsTest(unittest.TestCase):
    def test_arrow_cells_and_directions_are_found(self):
        records = _records()
        flow = [r for n, r in records.items() if n.startswith("추진절차(가로) ")]
        self.assertTrue(flow)
        for record in flow:
            found = table_arrows.detect(record)
            self.assertTrue(found, record["name"])
            self.assertEqual(set(found.values()), {"right"}, record["name"])
        # 화살표가 없는 표는 화살표 고르기를 보이지 않는다.
        plain = next(r for n, r in records.items() if n.startswith("일정표(연간)"))
        self.assertEqual(table_arrows.detect(plain), {})

    def test_validate(self):
        self.assertIsNone(table_arrows.validate(None))
        self.assertEqual(table_arrows.validate({"kind": "symbol", "value": "⇨"}), {"kind": "symbol", "value": "⇨"})
        self.assertEqual(table_arrows.validate({"kind": "image", "value": "basic"})["direction"], "auto")
        for bad in ({"kind": "symbol", "value": "X"}, {"kind": "image", "value": "basic", "size": "huge"},
                    {"kind": "image", "value": "nope"}, "⇨"):
            with self.assertRaises(ValueError):
                table_arrows.validate(bad)

    def test_symbol_follows_each_cell_direction_and_grown_units(self):
        record = next(r for n, r in _records().items() if n.startswith("추진절차(가로) "))
        plan = table_units.plan_for(record)
        count = (plan["col"] or {}).get("count")
        view = table_units.preview(record["id"], CATALOG, col_count=count + 1 if count else None,
                                   arrow={"kind": "symbol", "value": "⇨"})
        arrows = [t for row in view["cells"] for t in row if t == "⇨"]
        self.assertEqual(len(arrows), len(table_arrows.detect(record)) + (1 if count else 0))
        self.assertEqual(table_arrows._turned("⇨", "down"), "⇩")
        self.assertEqual(table_arrows._turned("⇦", "down"), "⇦")   # 오른쪽이 아닌 기호는 그대로

    def test_image_arrow_is_embedded_as_hangul_picture(self):
        record = next(r for n, r in _records().items() if n.startswith("추진절차(가로) "))
        with tempfile.TemporaryDirectory() as folder:
            out = table_units.export_resized(record["id"], Path(folder) / "a.hwpx", CATALOG,
                                             arrow={"kind": "image", "value": "chevron", "size": "large"})
            with zipfile.ZipFile(out) as archive:
                names = archive.namelist()
                self.assertIn("BinData/docfitArrowRight.png", names)
                self.assertIn('id="docfitArrowRight"', archive.read("Contents/content.hpf").decode("utf-8"))
                section = ET.fromstring(archive.read(next(n for n in names if n.startswith("Contents/section"))))
            pics = [p for p in section.iter(HP + "pic")]
            self.assertEqual(len(pics), len(table_arrows.detect(record)))
            self.assertEqual(len({p.get("id") for p in pics}), len(pics))   # 그림마다 다른 id
        view = table_units.preview(record["id"], CATALOG, arrow={"kind": "image", "value": "basic"})
        shapes = [s for row in view["cell_meta"] for c in row for s in c.get("shapes") or []]
        self.assertTrue(shapes and all(s.get("src", "").startswith("data:image/png") for s in shapes))

    def test_manifest_prefix_is_kept(self):
        plain = b'<manifest xmlns="x"><item id="a"/></manifest>'
        self.assertIn(b'<item id="docfitArrowDown"', table_arrows.add_to_manifest(plain, ["BinData/docfitArrowDown.png"]))
        opf = b'<opf:package><opf:manifest></opf:manifest></opf:package>'
        self.assertIn(b"<opf:item id=", table_arrows.add_to_manifest(opf, ["BinData/docfitArrowRight.png"]))

    def test_catalog_offers_symbols_and_five_images(self):
        catalog = table_arrows.catalog()
        self.assertEqual(len(catalog["symbols"]), 12)
        self.assertEqual([i["value"] for i in catalog["images"]], list(table_arrows.IMAGE_STYLES))
        self.assertTrue(all(i["src"].startswith("data:image/png;base64,") for i in catalog["images"]))


if __name__ == "__main__":
    unittest.main()
