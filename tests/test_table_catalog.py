import tempfile
import unittest
import zipfile
import hashlib
from pathlib import Path

from defusedxml import ElementTree as ET

from docfit_core.table_catalog import (
    _scan,
    _text,
    _top_tables,
    _cell_text_nodes,
    default_catalog_path,
    export_template,
    list_catalog,
)


HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


class TableCatalogTests(unittest.TestCase):
    def test_embedded_catalog_has_named_groups_and_all_table_shapes(self):
        catalog = list_catalog()
        self.assertEqual(catalog["category_count"], 16)
        self.assertEqual(catalog["template_count"], 34)
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

    def test_editing_cell_text_preserves_every_non_text_hwp_structure_and_source(self):
        catalog_path = default_catalog_path()
        source_hash = hashlib.sha256(catalog_path.read_bytes()).hexdigest()
        record = _scan(catalog_path)[0]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "edited.hwpx"
            with zipfile.ZipFile(catalog_path) as source:
                source_root = ET.fromstring(source.read(record["section"]))
            source_table = _top_tables(source_root.findall(HP + "p")[record["paragraph_index"]])[record["table_index"]]
            cell_position = next((r, c) for r, row in enumerate(source_table.findall(HP + "tr"))
                                 for c, cell in enumerate(row.findall(HP + "tc")) if _cell_text_nodes(cell))
            row_index, cell_index = cell_position
            export_template(record["id"], target, cell_edits={f"{row_index}:{cell_index}": "편집 검증"})
            with zipfile.ZipFile(catalog_path) as source, zipfile.ZipFile(target) as output:
                original_root = ET.fromstring(source.read(record["section"]))
                edited_root = ET.fromstring(output.read("Contents/section0.xml"))
            original_table = _top_tables(original_root.findall(HP + "p")[record["paragraph_index"]])[record["table_index"]]
            edited_table = next(table for paragraph in edited_root.findall(HP + "p") for table in _top_tables(paragraph))
            edited_cell = edited_table.findall(HP + "tr")[row_index].findall(HP + "tc")[cell_index]
            self.assertEqual("".join(node.text or "" for node in _cell_text_nodes(edited_cell)), "편집 검증")
            for table in (original_table, edited_table):
                for text_node in table.iter(HP + "t"):
                    text_node.text = ""
            self.assertEqual(ET.tostring(edited_table), ET.tostring(original_table))
        self.assertEqual(hashlib.sha256(catalog_path.read_bytes()).hexdigest(), source_hash)

    def test_empty_catalog_cell_can_be_filled_without_rebuilding_its_cell_format(self):
        record = _scan(default_catalog_path())[0]
        with zipfile.ZipFile(default_catalog_path()) as source:
            root = ET.fromstring(source.read(record["section"]))
        table = _top_tables(root.findall(HP + "p")[record["paragraph_index"]])[record["table_index"]]
        empty = next((r, c, cell) for r, row in enumerate(table.findall(HP + "tr"))
                     for c, cell in enumerate(row.findall(HP + "tc")) if not _cell_text_nodes(cell))
        row_index, cell_index, original_cell = empty
        original_char_shape = next((run.get("charPrIDRef") for run in original_cell.iter(HP + "run")), None)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "filled.hwpx"
            export_template(record["id"], target, cell_edits={f"{row_index}:{cell_index}": "새 내용"})
            with zipfile.ZipFile(target) as output:
                edited = ET.fromstring(output.read("Contents/section0.xml"))
        edited_table = next(tab for paragraph in edited.findall(HP + "p") for tab in _top_tables(paragraph))
        cell = edited_table.findall(HP + "tr")[row_index].findall(HP + "tc")[cell_index]
        self.assertEqual(_text(cell), "새 내용")
        self.assertEqual(next(run.get("charPrIDRef") for run in cell.iter(HP + "run")), original_char_shape)

    def test_invalid_cell_edit_is_rejected_without_touching_source(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                export_template("0:1", Path(folder) / "bad.hwpx", cell_edits={"999:0": "bad"})
            with self.assertRaises(ValueError):
                export_template("0:1", Path(folder) / "bad.hwpx", cell_edits={"0:0": "x" * 2001})

    def test_native_row_and_column_edits_update_hwp_table_geometry(self):
        record = next(item for item in _scan(default_catalog_path()) if item["id"] == "1:1")
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "resized.hwpx"
            export_template(record["id"], target, structure_edits=["add_row", "add_column"])
            with zipfile.ZipFile(target) as output:
                root = ET.fromstring(output.read("Contents/section0.xml"))
            table = next(tab for paragraph in root.findall(HP + "p") for tab in _top_tables(paragraph))
            rows = table.findall(HP + "tr")
            self.assertEqual(table.get("rowCnt"), str(record["rows"] + 1))
            self.assertEqual(table.get("colCnt"), str(record["cols"] + 1))
            self.assertEqual(len(rows), record["rows"] + 1)
            self.assertEqual(len(rows[-1].findall(HP + "tc")), len(rows[-2].findall(HP + "tc")))
            self.assertEqual(rows[-1].findall(HP + "tc")[-1].find(HP + "cellAddr").get("rowAddr"), str(record["rows"]))
            self.assertEqual(rows[0].findall(HP + "tc")[-1].find(HP + "cellAddr").get("colAddr"), str(record["cols"]))

    def test_each_catalog_template_accepts_a_native_row_and_column(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "resized.hwpx"
            for record in _scan(default_catalog_path()):
                for operation, field in (("add_row", "rowCnt"), ("add_column", "colCnt")):
                    with self.subTest(template=record["id"], operation=operation):
                        export_template(record["id"], target, structure_edits=[operation])
                        with zipfile.ZipFile(target) as output:
                            root = ET.fromstring(output.read("Contents/section0.xml"))
                        table = next(tab for paragraph in root.findall(HP + "p") for tab in _top_tables(paragraph))
                        self.assertEqual(int(table.get(field)), record["rows"] + (operation == "add_row")
                                         if field == "rowCnt" else record["cols"] + (operation == "add_column"))

    def test_native_row_and_column_deletes_keep_minimum_table_dimensions(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "resized.hwpx"
            export_template("1:1", target, structure_edits=["add_row", "add_column", "delete_column", "delete_row"])
            with zipfile.ZipFile(target) as output:
                root = ET.fromstring(output.read("Contents/section0.xml"))
            table = next(tab for paragraph in root.findall(HP + "p") for tab in _top_tables(paragraph))
            self.assertEqual(table.get("rowCnt"), "6")
            self.assertEqual(table.get("colCnt"), "5")
            with self.assertRaises(ValueError):
                export_template("1:1", target, structure_edits=["delete_row"] * 6)
            with self.assertRaises(ValueError):
                export_template("1:1", target, structure_edits=["delete_column"] * 5)

    def test_invalid_structure_edit_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                export_template("1:1", Path(folder) / "bad.hwpx", structure_edits=["delete_table"])


if __name__ == "__main__":
    unittest.main()
