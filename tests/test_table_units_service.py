"""표 템플릿 서비스: 스냅샷 캐시·미리보기·한/글 복사 흐름(가짜 한/글·가짜 클립보드)."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from docfit_app.api_contract import ServiceError
from docfit_app.settings_service import SettingsService
from docfit_app.table_units_service import TableUnitsService, crop_to_content
from docfit_core import public_table_presets, table_units
from docfit_core import table_catalog as catalog
from docfit_core.table_catalog import default_catalog_path


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
        bundled = patch("docfit_app.table_units_service.BUNDLED_SNAPSHOTS", Path(self.temp.name) / "no-bundled")
        bundled.start()
        self.addCleanup(bundled.stop)
        self.log = []
        self.formats = ["Hwp Native", "HTML Format"]
        self.service = TableUnitsService(
            lambda: FakeHwp(self.log),
            source=default_catalog_path(),
            snapshot_root=Path(self.temp.name),
            clipboard_formats=lambda: self.formats,
            settings=SettingsService(Path(self.temp.name) / "settings.json"),
            activator=lambda: False
        )

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
        self.assertFalse(any(item[0] == "SaveAs" for item in self.log))

    def test_old_snapshot_folders_are_removed_and_failed_hwp_leaves_no_cache(self):
        old = Path(self.temp.name) / ("0" * 16)
        old.mkdir()
        (old / "0_1.png").write_bytes(b"old")
        self.service.command("thumbnails", {})
        self.assertFalse(old.exists())

        def broken():
            raise RuntimeError("한/글 없음")
        service = TableUnitsService(
            broken,
            source=default_catalog_path(),
            snapshot_root=Path(self.temp.name) / "other"
        )
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
        for action, payload in (
            ("preview", {}),
            ("preview", {"id": "0:1", "row_count": "3"}),
            ("preview", {"id": "0:1", "col_count": True}),
            ("delete", {}),
        ):
            with self.assertRaises(ServiceError):
                self.service.command(action, payload)

    def test_preferences_persist_recent_deduplicates_and_caps_at_eight(self):
        templates = self.service.list()["templates"][:9]
        first = templates[0]["id"]
        result = self.service.command("favorite", {"id": first, "on": True})
        self.assertTrue(result["templates"][0]["favorite"])
        fresh = TableUnitsService(
            source=default_catalog_path(),
            snapshot_root=Path(self.temp.name),
            settings=self.service._settings
        )
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
        result = self.service.command("preview", {
            "id": item["id"],
            "col_count": 6,
            "fill": "blank",
            "cell_texts": {"0,21": "입력 제목"}
        })
        self.assertEqual(result["cell_meta"][0][-1]["text"], "입력 제목")
        invalid = [
            {"fill": []},
            {"fill": "unknown"},
            {"cell_texts": []},
            {"cell_texts": {"0:1": "x"}},
            {"cell_texts": {"0,1": 1}},
            {"cell_texts": {"0,1": "x" * 1001}},
            {"cell_texts": {"0,2": "covered"}},
            {"cell_texts": {f"{i},0": "x" for i in range(201)}},
        ]
        for extra in invalid:
            for action in ("preview", "copy"):
                with self.subTest(extra=extra, action=action), self.assertRaises(ServiceError):
                    self.service.command(action, {"id": item["id"], **extra})

    def test_activation_failure_still_copies_and_failed_copy_does_not_update_recent(self):
        item = self.service.list()["templates"][0]
        self.service._activator = lambda: (_ for _ in ()).throw(OSError("focus"))
        self.assertTrue(self.service.copy(item["id"])["copied"])
        self.assertEqual(self.service.list()["recent"], [item["id"]])
        self.service._hwp_factory = lambda: SimpleNamespace(
            Open=lambda *a: True,
            HeadCtrl=None,
            Clear=lambda *a: None,
            Quit=lambda: None
        )
        with self.assertRaises(ServiceError):
            self.service.copy(self.service.list()["templates"][1]["id"])
        self.assertEqual(self.service.list()["recent"], [item["id"]])

    def test_crop_removes_white_margin(self):
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (200, 100), "white")
        ImageDraw.Draw(image).rectangle((50, 20, 80, 40), fill="black")
        cropped = crop_to_content(image, margin=2)
        self.assertEqual(cropped.size, (35, 25))

    # --- P7 공공 프리셋 통합 서비스 시험 (설계서 9장 명세) ---

    def test_public_presets_append_without_changing_legacy_descriptors(self):
        legacy = table_units.describe_units(self.service.source)
        all_templates = self.service._units()
        self.assertEqual(len(all_templates), len(legacy) + 6)

        # 앞부분 legacy 검증: id, name, category, rows, cols, units 일치
        for idx, leg in enumerate(legacy):
            cur = all_templates[idx]
            for key in ("id", "name", "category", "rows", "cols", "units"):
                self.assertEqual(cur[key], leg[key])

        # 뒷부분 6개 공공 프리셋 검증
        public_items = all_templates[len(legacy):]
        self.assertEqual(len(public_items), 6)
        exp_ids = [
            "pub_summary_headline",
            "pub_two_col_definition",
            "pub_multi_col_comparison",
            "pub_gantt_timeline",
            "pub_budget_breakdown",
            "pub_qa_checklist",
        ]
        for idx, item in enumerate(public_items):
            self.assertEqual(item["id"], exp_ids[idx])
            self.assertEqual(item["category"], "공공 표준")
            self.assertIn("badge", item)
            self.assertIn("description", item)
            self.assertIn("guideline", item)

    def test_public_preview_and_export_route_by_exact_id(self):
        for pid in public_table_presets.PUBLIC_TABLE_PRESETS:
            res = self.service.command("preview", {"id": pid})
            self.assertEqual(res["id"], pid)
            self.assertIn("cell_meta", res)

            # export 재파싱 검사
            with tempfile.TemporaryDirectory() as td:
                out_path = self.service._export(Path(td), pid)
                rec = catalog._scan(out_path)[0]
                prev = catalog.preview(rec["id"], out_path)
                self.assertEqual(prev["rows"], public_table_presets.PUBLIC_TABLE_PRESETS[pid]["default_rows"])

        # 알 수 없는 pub_ ID는 INVALID_INPUT
        with self.assertRaises(ServiceError) as ctx:
            self.service.command("preview", {"id": "pub_unknown"})
        self.assertEqual(ctx.exception.code, "INVALID_INPUT")

    def test_public_copy_uses_existing_hwp_native_sequence(self):
        pub_id = "pub_two_col_definition"
        res = self.service.command("copy", {"id": pub_id, "row_count": 5})
        self.assertTrue(res["copied"])
        self.assertIn(("Run", "Copy"), self.log)
        self.assertEqual(self.log[-1], ("Quit",))
        self.assertEqual(self.log[1:5], [("GetAnchorPos", 0), ("SetPosBySet", "anchor"), ("FindCtrl",), ("Run", "Copy")])
        self.assertNotIn(("Run", "SelectAll"), self.log)

        # 실패 시 최근 목록 불변 검사
        initial_recent = list(self.service.list()["recent"])
        self.service._hwp_factory = lambda: SimpleNamespace(
            Open=lambda *a: False,
            Clear=lambda *a: None,
            Quit=lambda: None
        )
        with self.assertRaises(ServiceError):
            self.service.copy("pub_summary_headline")
        self.assertEqual(self.service.list()["recent"], initial_recent)

    def test_public_favorite_recent_persist_with_legacy_ids(self):
        all_tmpl = self.service.list()["templates"]
        legacy_id = all_tmpl[0]["id"]
        public_id = "pub_two_col_definition"

        # 즐겨찾기 설정
        self.service.command("favorite", {"id": public_id, "on": True})
        self.service.command("favorite", {"id": legacy_id, "on": True})

        # 복사 수행
        self.service.copy(legacy_id)
        self.service.copy(public_id)

        recent = self.service.list()["recent"]
        self.assertEqual(recent[0], public_id)
        self.assertEqual(recent[1], legacy_id)

        # 영속화 확인
        fresh = TableUnitsService(
            source=default_catalog_path(),
            snapshot_root=Path(self.temp.name),
            settings=self.service._settings
        )
        fresh_list = fresh.list()
        fav_ids = {t["id"] for t in fresh_list["templates"] if t["favorite"]}
        self.assertIn(public_id, fav_ids)
        self.assertIn(legacy_id, fav_ids)

    def test_public_snapshots_use_separate_content_cache(self):
        pub_path = self.service._snapshot_path("pub_summary_headline")
        self.assertIn("public", pub_path.parts)

        leg_id = self.service.list()["templates"][0]["id"]
        leg_path = self.service._snapshot_path(leg_id)
        self.assertNotIn("public", leg_path.parts)

        # 공공 스냅샷 키 캐시 확인
        k1 = self.service._public_snapshot_key("pub_summary_headline")
        k2 = self.service._public_snapshot_key("pub_summary_headline")
        self.assertEqual(k1, k2)

    def test_public_thumbnails_generate_once_and_preserve_bundled_legacy(self):
        fake_pdf = Path(self.temp.name) / "fake.pdf"
        from pypdf import PdfWriter
        w = PdfWriter()
        w.add_blank_page(200, 100)
        with open(fake_pdf, "wb") as f:
            w.write(f)

        def fake_convert(app, doc, pdf):
            pdf.write_bytes(fake_pdf.read_bytes())

        # pypdfium2 및 PIL을 가짜 렌더링으로 patch
        from PIL import Image
        fake_img = Image.new("RGB", (100, 50), "white")

        with patch("docfit_core.file_conversion.convert_hwpx_to_pdf", side_effect=fake_convert), \
             patch("pypdfium2.PdfDocument") as mock_pdf:
            mock_doc = mock_pdf.return_value
            mock_doc.__getitem__.return_value.render.return_value.to_pil.return_value = fake_img

            data = self.service.command("thumbnails", {})
            self.assertTrue(data["thumbnails_ready"])
            # 공공 스냅샷이 생성되었는지 확인
            pub_thumb = next(t["thumbnail"] for t in data["templates"] if t["id"] == "pub_summary_headline")
            self.assertIsNotNone(pub_thumb)

            # 2회차 호출 시 추가 SaveAs 없음
            self.log.clear()
            self.service.command("thumbnails", {})
            saves = sum(1 for item in self.log if item[0] == "SaveAs")
            self.assertEqual(saves, 0)

    def test_failed_public_thumbnail_does_not_leave_png_or_lose_legacy_cache(self):
        target = self.service._snapshot_path("pub_summary_headline")
        tmp_target = target.with_name(target.name + ".tmp")

        with patch("PIL.Image.Image.save", side_effect=IOError("save error")):
            with self.assertRaises(IOError):
                self.service.command("thumbnails", {})

        self.assertFalse(target.exists())
        self.assertFalse(tmp_target.exists())

    def test_public_errors_are_api_errors_before_hwp_launch(self):
        invalids = [
            {"id": "pub_two_col_definition", "row_count": 0},
            {"id": "pub_two_col_definition", "row_count": True},
            {"id": "pub_two_col_definition", "col_count": 2},
            {"id": "pub_two_col_definition", "fill": "unknown"},
            {"id": "pub_two_col_definition", "cell_texts": {"0:0": "x"}},
            {"id": "pub_unknown"},
        ]
        for payload in invalids:
            with self.subTest(payload=payload):
                self.log.clear()
                with self.assertRaises(ServiceError) as ctx:
                    self.service.command("preview", payload)
                self.assertEqual(ctx.exception.code, "INVALID_INPUT")
                self.assertEqual(len(self.log), 0)


class BundledSnapshotTests(unittest.TestCase):
    def test_builtin_templates_show_bundled_pictures_without_hangul(self):
        """앱에 넣어 둔 내장 표 그림은 한/글 없이 바로 보인다(처음 쓰는 사용자, 2026-10-23 사용자 요청)."""
        def no_hwp():
            raise AssertionError("내장 그림이 있으면 한/글을 띄우지 않는다")
        with patch.object(TableUnitsService, "_units", lambda s: table_units.describe_units(s.source)), \
             tempfile.TemporaryDirectory() as folder:
            service = TableUnitsService(no_hwp, source=default_catalog_path(), snapshot_root=Path(folder))
            data = service.list()
            missing = [t["name"] for t in data["templates"] if not t["thumbnail"]]
            self.assertTrue(data["thumbnails_ready"], f"그림 없는 템플릿: {missing[:5]} / {len(missing)}개, 출처 {service.source}")
            self.assertTrue(all(t["thumbnail"].startswith("data:image/png;base64,") for t in data["templates"]))
            self.assertTrue(service.command("thumbnails", {})["thumbnails_ready"])

    def test_bundled_pictures_do_not_depend_on_registered_xml_prefixes(self):
        """다른 기능이 이름공간 접두어를 등록해도 같은 표는 같은 그림을 찾는다(전체 시험 순서 실패 재현)."""
        import xml.etree.ElementTree as StdET
        with patch.object(TableUnitsService, "_units", lambda s: table_units.describe_units(s.source)), \
             patch.dict(StdET._namespace_map), tempfile.TemporaryDirectory() as folder:
            StdET.register_namespace("zz", table_units.HP[1:-1])
            service = TableUnitsService(lambda: None, source=default_catalog_path(), snapshot_root=Path(folder))
            self.assertTrue(service.list()["thumbnails_ready"])


if __name__ == "__main__":
    unittest.main()
