"""표 템플릿 서비스: 스냅샷 캐시·미리보기·한/글 복사 흐름(가짜 한/글·가짜 클립보드)."""
import tempfile
import unittest
from pathlib import Path

from docfit_app.api_contract import ServiceError
from docfit_app.table_units_service import TableUnitsService, crop_to_content
from docfit_core.table_catalog import default_catalog_path


class FakeHwp:
    def __init__(self, log):
        self.log = log

    def Open(self, path, kind, option):
        self.log.append(("Open", Path(path).suffix, kind))
        self.opened = Path(path)
        return self.opened.is_file()

    def Run(self, action):
        self.log.append(("Run", action))

    def SaveAs(self, path, kind, option):
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(200, 100)
        with open(path, "wb") as stream:
            writer.write(stream)
        self.log.append(("SaveAs", kind))
        return True

    def Clear(self, _):
        self.log.append(("Clear",))

    def Quit(self):
        self.log.append(("Quit",))


class TableUnitsServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.log = []
        self.formats = ["Hwp Native", "HTML Format"]
        self.service = TableUnitsService(lambda: FakeHwp(self.log), source=default_catalog_path(),
                                         snapshot_root=Path(self.temp.name), clipboard_formats=lambda: self.formats)

    def test_list_reports_units_and_missing_snapshots(self):
        data = self.service.command("list", {})
        self.assertFalse(data["thumbnails_ready"])
        self.assertTrue(data["templates"])
        first = data["templates"][0]
        self.assertIn("units", first)
        self.assertIsNone(first["thumbnail"])

    def test_thumbnails_are_made_once_and_cached(self):
        data = self.service.command("thumbnails", {})
        self.assertTrue(data["thumbnails_ready"])
        self.assertTrue(data["templates"][0]["thumbnail"].startswith("data:image/png;base64,"))
        saves = sum(1 for item in self.log if item[0] == "SaveAs")
        self.assertEqual(saves, len(data["templates"]))
        self.log.clear()
        self.service.command("thumbnails", {})
        self.assertFalse(any(item[0] == "SaveAs" for item in self.log))   # 캐시 사용

    def test_old_snapshot_folders_are_removed_and_failed_hwp_leaves_no_cache(self):
        old = Path(self.temp.name) / ("0" * 16)
        old.mkdir()
        (old / "0_1.png").write_bytes(b"old")
        self.service.command("thumbnails", {})
        self.assertFalse(old.exists())

        def broken():
            raise RuntimeError("한/글 없음")
        service = TableUnitsService(broken, source=default_catalog_path(),
                                    snapshot_root=Path(self.temp.name) / "other")
        with self.assertRaises(RuntimeError):
            service.command("thumbnails", {})

    def test_copy_uses_hidden_hwp_and_checks_clipboard(self):
        template = next(item for item in self.service.list()["templates"] if item["units"]["col"] or item["units"]["row"])
        result = self.service.command("copy", {"id": template["id"]})
        self.assertTrue(result["copied"])
        self.assertIn(("Run", "Copy"), self.log)
        self.assertEqual(self.log[-1], ("Quit",))
        self.formats = ["HTML Format"]
        with self.assertRaises(ServiceError):
            self.service.command("copy", {"id": template["id"]})

    def test_copy_without_hwp_is_refused(self):
        service = TableUnitsService(None, source=default_catalog_path(), snapshot_root=Path(self.temp.name))
        template = service.list()["templates"][0]
        with self.assertRaises(ServiceError):
            service.command("copy", {"id": template["id"]})

    def test_invalid_requests(self):
        for action, payload in (("preview", {}), ("preview", {"id": "0:1", "row_count": "3"}),
                                ("preview", {"id": "0:1", "col_count": True}), ("delete", {})):
            with self.assertRaises(ServiceError):
                self.service.command(action, payload)

    def test_crop_removes_white_margin(self):
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (200, 100), "white")
        ImageDraw.Draw(image).rectangle((50, 20, 80, 40), fill="black")
        cropped = crop_to_content(image, margin=2)
        self.assertEqual(cropped.size, (35, 25))


if __name__ == "__main__":
    unittest.main()
