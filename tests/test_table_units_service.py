"""표 템플릿 서비스: 스냅샷 캐시·미리보기·한/글 복사 흐름(가짜 한/글·가짜 클립보드)."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from docfit_app.api_contract import ServiceError
from docfit_app.table_units_service import TableUnitsService, crop_to_content
from docfit_core.table_catalog import default_catalog_path
from docfit_app.settings_service import SettingsService


class FakeHwp:
    def __init__(self, log):
        self.log = log
        table = SimpleNamespace(CtrlID="tbl", Next=None, GetAnchorPos=lambda n: self.anchor(n))
        self.HeadCtrl = SimpleNamespace(CtrlID="secd", Next=table)

    def anchor(self, index):
        self.log.append(("GetAnchorPos", index))
        return "anchor"

    def SetPosBySet(self, pos):
        self.log.append(("SetPosBySet", pos))
        return True

    def FindCtrl(self):
        self.log.append(("FindCtrl",))
        return True

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
                                         snapshot_root=Path(self.temp.name), clipboard_formats=lambda: self.formats,
                                         settings=SettingsService(Path(self.temp.name) / "settings.json"), activator=lambda: False)

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
        self.assertEqual(self.log[1:5], [("GetAnchorPos", 0), ("SetPosBySet", "anchor"), ("FindCtrl",), ("Run", "Copy")])
        self.assertNotIn(("Run", "SelectAll"), self.log)
        self.assertFalse(result["activated"])
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

    def test_preferences_persist_recent_deduplicates_and_caps_at_eight(self):
        templates = self.service.list()["templates"][:9]
        first = templates[0]["id"]
        result = self.service.command("favorite", {"id": first, "on": True})
        self.assertTrue(result["templates"][0]["favorite"])
        fresh = TableUnitsService(source=default_catalog_path(), snapshot_root=Path(self.temp.name),
                                  settings=self.service._settings)
        self.assertTrue(fresh.list()["templates"][0]["favorite"])
        for item in templates:
            self.service.copy(item["id"])
        self.service.copy(templates[-2]["id"])
        recent = fresh.list()["recent"]
        self.assertEqual(len(recent), 8)
        self.assertEqual(recent[:2], [templates[-2]["id"], templates[-1]["id"]])
        self.assertFalse(self.service.favorite(first, False)["templates"][0]["favorite"])
        with self.assertRaises(ServiceError):
            self.service.command("favorite", {"id": first, "on": 1})
        with self.assertRaises(ServiceError):
            self.service.favorite("missing", True)

    def test_payload_validation_and_post_fill_text(self):
        item = next(t for t in self.service.list()["templates"] if "연간" in t["name"])
        result = self.service.command("preview", {"id": item["id"], "col_count": 6,
            "fill": "blank", "cell_texts": {"0,21": "입력 제목"}})
        self.assertEqual(result["cell_meta"][0][-1]["text"], "입력 제목")
        invalid = [{"fill": []}, {"fill": "unknown"}, {"cell_texts": []},
                   {"cell_texts": {"0:1": "x"}}, {"cell_texts": {"0,1": 1}},
                   {"cell_texts": {"0,1": "x" * 1001}}, {"cell_texts": {"0,2": "covered"}},
                   {"cell_texts": {f"{i},0": "x" for i in range(201)}}]
        for extra in invalid:
            for action in ("preview", "copy"):
                with self.subTest(extra=extra, action=action), self.assertRaises(ServiceError):
                    self.service.command(action, {"id": item["id"], **extra})

    def test_activation_failure_still_copies_and_failed_copy_does_not_update_recent(self):
        item = self.service.list()["templates"][0]
        self.service._activator = lambda: (_ for _ in ()).throw(OSError("focus"))
        self.assertTrue(self.service.copy(item["id"])["copied"])
        self.assertEqual(self.service.list()["recent"], [item["id"]])
        self.service._hwp_factory = lambda: SimpleNamespace(Open=lambda *a: True, HeadCtrl=None, Clear=lambda *a: None, Quit=lambda: None)
        with self.assertRaises(ServiceError):
            self.service.copy(self.service.list()["templates"][1]["id"])
        self.assertEqual(self.service.list()["recent"], [item["id"]])

    def test_crop_removes_white_margin(self):
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (200, 100), "white")
        ImageDraw.Draw(image).rectangle((50, 20, 80, 40), fill="black")
        cropped = crop_to_content(image, margin=2)
        self.assertEqual(cropped.size, (35, 25))


if __name__ == "__main__":
    unittest.main()
