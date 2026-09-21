import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from defusedxml import ElementTree as ET

from docfit_core.korean_proofread import (
    apply_approved_hwpx, load_exclusions, save_exclusions, scan_hwpx,
)


SECTION = '''<hs:sec xmlns:hs="urn:section" xmlns:hp="urn:para">
  <hp:p><hp:run><hp:t>금</hp:t></hp:run><hp:run><hp:t>번 계획은 몇일 내에 확정합니다.</hp:t></hp:run></hp:p>
  <hp:p><hp:run><hp:t>금번 일정은 금일에 공지합니다.</hp:t></hp:run></hp:p>
  <hp:p><hp:run><hp:tbl><hp:tr><hp:tc><hp:subList>
    <hp:p><hp:run><hp:t>명일 회의</hp:t></hp:run></hp:p>
  </hp:subList></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>
</hs:sec>'''.encode("utf-8")


class KoreanProofreadTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / "source.hwpx"
        with ZipFile(self.source, "w") as archive:
            archive.writestr("Contents/header.xml", "<head/>")
            archive.writestr("Contents/section0.xml", SECTION)

    def test_scan_including_split_runs_and_table_cells(self):
        findings = {item["source"]: item for item in scan_hwpx(self.source)}
        self.assertEqual(findings["금번"]["count"], 2)
        self.assertEqual(findings["몇일"]["count"], 1)
        self.assertEqual(findings["명일"]["count"], 1)
        self.assertEqual(findings["금일"]["count"], 1)

    def test_only_approved_expression_changes_in_new_file(self):
        target = self.folder / "result.hwpx"
        count = apply_approved_hwpx(self.source, target, {"public.geumbeon"})
        self.assertEqual(count, 2)
        with ZipFile(target) as archive:
            root = ET.fromstring(archive.read("Contents/section0.xml"))
            text = "".join(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
        self.assertIn("이번 계획", text)
        self.assertIn("몇일", text)
        self.assertIn("명일", text)
        with ZipFile(self.source) as archive:
            self.assertEqual(archive.read("Contents/section0.xml"), SECTION)
        with self.assertRaises(FileExistsError):
            apply_approved_hwpx(self.source, target, {"public.geumbeon"})

    def test_excluded_expression_is_not_found_or_changed(self):
        exclusion_file = self.folder / "excluded.json"
        save_exclusions(exclusion_file, {"금번"})
        self.assertEqual(load_exclusions(exclusion_file), {"금번"})
        findings = scan_hwpx(self.source, load_exclusions(exclusion_file))
        self.assertNotIn("금번", {item["source"] for item in findings})
        target = self.folder / "excluded_result.hwpx"
        count = apply_approved_hwpx(self.source, target, {"public.geumbeon", "spelling.myeochil"},
                                    load_exclusions(exclusion_file))
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
