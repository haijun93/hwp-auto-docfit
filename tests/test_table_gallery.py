"""2.0.5 표 템플릿 추가 서식(공공기관 표 종류 × 디자인 유형)."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from docfit_app.table_units_service import GALLERY_PATH, TableUnitsService
from docfit_core import table_catalog, table_units
from docfit_core.table_gallery import DEFINITIONS, THEMES, build_gallery, gallery_templates


class TableGalleryTest(unittest.TestCase):
    def test_bundled_gallery_matches_the_generator(self):
        # 정의를 고쳤으면 scripts/render_table_gallery.py로 파일과 그림을 다시 만들어야 한다.
        with tempfile.TemporaryDirectory() as folder:
            fresh = build_gallery(table_catalog.default_catalog_path(), Path(folder) / "g.hwpx")
            with zipfile.ZipFile(fresh) as a, zipfile.ZipFile(GALLERY_PATH) as b:
                for name in ("Contents/header.xml", "Contents/section0.xml"):
                    self.assertEqual(a.read(name), b.read(name), name)

    def test_many_public_table_kinds_in_several_designs(self):
        listing = table_catalog.list_catalog(GALLERY_PATH)
        self.assertEqual(listing["category_count"], len(DEFINITIONS))
        self.assertGreaterEqual(listing["category_count"], 18)
        self.assertEqual(listing["template_count"], len(gallery_templates()))
        self.assertEqual({theme for *_, theme in gallery_templates()}, set(THEMES))

    def test_every_template_grows_and_shrinks_by_information_unit(self):
        tails = {d[0]: bool(d[3]) for d in DEFINITIONS}
        for item in table_units.describe_units(GALLERY_PATH):
            row, col = item["units"]["row"], item["units"]["col"]
            self.assertIsNotNone(row, item["name"])
            base = table_units.preview(item["id"], GALLERY_PATH)
            grown = table_units.preview(item["id"], GALLERY_PATH, row_count=row["count"] + 2)
            self.assertEqual(grown["rows"], base["rows"] + 2, item["name"])
            # 합계 행은 단위 밖이라 늘어난 뒤에도 맨 끝에 남는다.
            if tails[item["category"]]:
                self.assertEqual(grown["cells"][-1][0], base["cells"][-1][0], item["name"])
            shrunk = table_units.preview(item["id"], GALLERY_PATH, row_count=1)
            self.assertEqual(shrunk["rows"], base["rows"] - row["count"] + 1, item["name"])
            if col:
                wider = table_units.preview(item["id"], GALLERY_PATH, col_count=col["count"] + 1)
                self.assertEqual(wider["cols"], base["cols"] + 1, item["name"])
                ends_inside = any(d[0] == item["category"] and d[4][0] + d[4][1] < len(d[1]) for d in DEFINITIONS)
                if ends_inside:  # 계·비고 같은 끝 열은 늘어난 열 뒤에 그대로 남는다.
                    self.assertEqual(wider["cells"][0][-1], base["cells"][0][-1], item["name"])

    def test_service_shows_gallery_beside_the_user_catalog_with_pictures(self):
        service = TableUnitsService(source=table_catalog.default_catalog_path())
        listing = service.list()
        gallery = [t for t in listing["templates"] if t.get("gallery")]
        self.assertEqual(len(gallery), len(gallery_templates()))
        self.assertTrue(all(t["id"].startswith("g") and t["thumbnail"] for t in gallery))
        self.assertTrue(listing["thumbnails_ready"])
        first = gallery[0]["id"]
        self.assertEqual(service.preview(first, row_count=3)["id"], first)
        with tempfile.TemporaryDirectory() as folder:
            exported = service._export(Path(folder), first, row_count=3)
            self.assertTrue(exported.is_file())


if __name__ == "__main__":
    unittest.main()
