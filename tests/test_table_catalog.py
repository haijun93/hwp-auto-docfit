import tempfile
import unittest
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from docfit_core.table_catalog import (
    _scan,
    _top_tables,
    default_catalog_path,
    export_template,
    list_catalog,
)


HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


class TableCatalogTests(unittest.TestCase):
    def test_embedded_catalog_has_named_groups_and_all_table_shapes(self):
        catalog = list_catalog()
        self.assertEqual(catalog["category_count"], 15)
        self.assertEqual(catalog["template_count"], 32)
        categories = {item["name"]: item for item in catalog["categories"]}
        self.assertEqual(len(categories["부연설명"]["templates"]), 6)
        self.assertEqual(len(categories["추진절차(가로)"]["templates"]), 5)
        ids = [template["id"] for item in catalog["categories"] for template in item["templates"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_export_preserves_exact_table_xml_and_contains_only_selected_table(self):
        catalog_path = default_catalog_path()
        catalog = list_catalog(catalog_path)
        selected = catalog["categories"][2]["templates"][3]
        record = next(item for item in _scan(catalog_path) if item["id"] == selected["id"])
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "selected.hwpx"
            export_template(selected["id"], target, catalog_path)
            with zipfile.ZipFile(catalog_path) as source, zipfile.ZipFile(target) as output:
                source_root = ET.fromstring(source.read(record["section"]))
                output_root = ET.fromstring(output.read("Contents/section0.xml"))
                source_paragraph = source_root.findall(HP + "p")[record["paragraph_index"]]
                expected_table = _top_tables(source_paragraph)[record["table_index"]]
                output_tables = list(output_root.iter(HP + "tbl"))
                self.assertEqual(len(output_tables), 1)
                self.assertEqual(ET.tostring(output_tables[0]), ET.tostring(expected_table))
                self.assertFalse(any((node.text or "").strip().startswith("#") for node in output_root.iter(HP + "t")))
                self.assertTrue(any(node.tag == HP + "secPr" for node in output_root.iter()))

    def test_every_catalog_entry_exports_as_one_standalone_table(self):
        catalog = list_catalog()
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "selected.hwpx"
            for category in catalog["categories"]:
                for template in category["templates"]:
                    export_template(template["id"], target)
                    with zipfile.ZipFile(target) as archive:
                        root = ET.fromstring(archive.read("Contents/section0.xml"))
                    top_level_tables = [
                        table for paragraph in root.findall(HP + "p")
                        for table in _top_tables(paragraph)
                    ]
                    self.assertEqual(len(top_level_tables), 1, template["id"])
                    self.assertEqual(int(top_level_tables[0].get("rowCnt")), template["rows"])
                    self.assertEqual(int(top_level_tables[0].get("colCnt")), template["cols"])

    def test_invalid_ids_extensions_and_source_overwrite_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "bad.txt"
            with self.assertRaises(ValueError):
                export_template("999:1", target)
            with self.assertRaises(ValueError):
                export_template("0:1", target)
            with self.assertRaises(ValueError):
                export_template("0:1", default_catalog_path(), default_catalog_path())


if __name__ == "__main__":
    unittest.main()
