import os
import tempfile
import unittest
from pathlib import Path

from docfit_app.library_service import LibraryService


class LibraryServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "자료"
        self.root.mkdir()
        self.service = LibraryService(Path(self.temp.name) / "library.db")
        self.library = self.service.create("검토 자료함", "테스트")

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def test_explicit_root_on_demand_index_and_filename_search(self):
        (self.root / "회의 결과.hwpx").write_bytes(b"source")
        (self.root / "메모.txt").write_text("본문은 아직 읽지 않음", encoding="utf-8")
        (self.root / "무시.exe").write_bytes(b"ignored")
        self.service.add_folder(self.library["id"], self.root)

        result = self.service.index(self.library["id"])

        self.assertTrue(result["ok"])
        self.assertEqual(result["indexed"], 2)
        found = self.service.search(self.library["id"], "회의")
        self.assertEqual([item["name"] for item in found], ["회의 결과.hwpx"])
        self.assertEqual(self.service.search(self.library["id"], extensions=["txt"])[0]["name"], "메모.txt")
        self.assertEqual(self.service.store.list_libraries()[0]["files"], 2)
        unchanged = self.service.index(self.library["id"])
        self.assertEqual(unchanged["indexed"], 0)
        (self.root / "회의 결과.hwpx").unlink()
        rescanned = self.service.index(self.library["id"])
        self.assertEqual(rescanned["removed"], 1)
        self.assertEqual(self.service.search(self.library["id"], "회의"), [])

    def test_rejects_missing_or_linked_root(self):
        with self.assertRaises(ValueError):
            self.service.add_folder(self.library["id"], self.root / "missing")
        link = Path(self.temp.name) / "link"
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(ValueError):
            self.service.add_folder(self.library["id"], link)

    def test_cancelled_scan_does_not_open_source_for_write(self):
        (self.root / "original.md").write_text("keep", encoding="utf-8")
        self.service.add_folder(self.library["id"], self.root)
        class Cancel:
            def is_set(self): return True
        result = self.service.index(self.library["id"], cancel=Cancel())
        self.assertTrue(result["cancelled"])
        self.assertEqual((self.root / "original.md").read_text(encoding="utf-8"), "keep")
        self.assertEqual(self.service.search(self.library["id"]), [])


if __name__ == "__main__":
    unittest.main()
