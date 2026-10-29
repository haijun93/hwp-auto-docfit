"""표그림판 칸 배경 그림: 검증·칸 배정·HWPX(BinData·목록·칸 채우기 그림) 회귀 시험."""
import base64
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET
from PIL import Image

from docfit_core import table_sketch as ts

HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
HC = "{http://www.hancom.co.kr/hwpml/2011/core}"
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def png(color=(200, 30, 30), size=(8, 6), kind="PNG"):
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, kind)
    return base64.b64encode(out.getvalue()).decode()


def line(x1, y1, x2, y2):
    return dict(x1=x1, y1=y1, x2=x2, y2=y2)


def two_by_two(images):
    lines = [line(0, 0, 8, 0), line(0, 4, 8, 4), line(0, 8, 8, 8),
             line(0, 0, 0, 8), line(4, 0, 4, 8), line(8, 0, 8, 8)]
    return dict(grid=dict(cols=20, rows=20, cell_mm=5.0), lines=lines, texts=[], images=images)


class CellImageTests(unittest.TestCase):
    def test_normalize_keeps_png_and_jpeg_and_drops_bad_items(self):
        sketch = two_by_two([
            dict(x=1, y=1, data=png()),
            dict(x=5, y=1, data="data:image/jpeg;base64," + png(kind="JPEG")),
            dict(x=1, y=5, data=base64.b64encode(b"GIF89a....").decode()),  # 형식 아님
            dict(x=99, y=1, data=png()),  # 격자 밖
            dict(x=1, y=1, data=png()),  # 같은 자리 두 번
        ])
        drawing, warnings = ts.normalize(sketch)
        self.assertEqual([(i["x"], i["y"], i["kind"]) for i in drawing["images"]], [(1, 1, "png"), (5, 1, "jpg")])
        self.assertEqual(len([w for w in warnings if "칸 그림" in w]), 3)

    def test_too_many_images_is_rejected(self):
        with self.assertRaises(ValueError):
            ts.normalize(two_by_two([dict(x=0, y=0, data=png())] * (ts.MAX_IMAGES + 1)))

    def test_layout_assigns_image_to_the_cell_that_contains_it(self):
        result = ts.preview(two_by_two([dict(x=6, y=7, data=png())]))
        by_pos = {(c["row"], c["col"]): c for c in result["cells"]}
        self.assertEqual(by_pos[(1, 1)].get("image"), 0)
        self.assertNotIn("image", by_pos[(0, 0)])
        # 미리보기 응답에는 그림 자료(무거운 base64)를 싣지 않는다.
        self.assertNotIn("data", repr(result["cells"]))

    def test_old_sketch_without_images_still_works(self):
        sketch = two_by_two(None)
        del sketch["images"]
        self.assertEqual(len(ts.preview(sketch)["cells"]), 4)

    def test_hwpx_embeds_image_and_fills_the_cell(self):
        sketch = two_by_two([dict(x=1, y=1, data=png()), dict(x=5, y=5, data=png(kind="JPEG"))])
        with tempfile.TemporaryDirectory() as folder:
            path = ts.to_hwpx(sketch, Path(folder) / "t.hwpx")
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
                self.assertIn("BinData/sketchimg1.png", names)
                self.assertIn("BinData/sketchimg2.jpg", names)
                self.assertEqual(z.read("BinData/sketchimg1.png")[:8], b"\x89PNG\r\n\x1a\n")
                manifest = z.read("Contents/content.hpf").decode()
                self.assertIn('id="sketchimg1" href="BinData/sketchimg1.png" media-type="image/png" isEmbeded="1"', manifest)
                self.assertIn('id="sketchimg2" href="BinData/sketchimg2.jpg" media-type="image/jpg"', manifest)
                ET.fromstring(manifest.encode())  # 목록이 여전히 올바른 XML
                header = ET.fromstring(z.read("Contents/header.xml"))
                section_name = next(n for n in names if n.startswith("Contents/section"))
                section = ET.fromstring(z.read(section_name))
            fills = {bf.get("id"): bf for bf in header.iter(HH + "borderFill")}
            image_refs = {}
            for ident, bf in fills.items():
                img = bf.find(HC + "fillBrush/" + HC + "imgBrush/" + HC + "img")
                if img is not None:
                    self.assertEqual(bf.find(HC + "fillBrush/" + HC + "imgBrush").get("mode"), "TOTAL")
                    image_refs[ident] = img.get("binaryItemIDRef")
            self.assertEqual(sorted(image_refs.values()), ["sketchimg1", "sketchimg2"])
            cells = {(tc.find(HP + "cellAddr").get("rowAddr"), tc.find(HP + "cellAddr").get("colAddr")): tc.get("borderFillIDRef")
                     for tc in section.iter(HP + "tc")}
            self.assertEqual(image_refs.get(cells[("0", "0")]), "sketchimg1")
            self.assertEqual(image_refs.get(cells[("1", "1")]), "sketchimg2")
            self.assertNotIn(cells[("0", "1")], image_refs)

    def test_hwpx_without_images_keeps_manifest_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            path = ts.to_hwpx(two_by_two([]), Path(folder) / "t.hwpx")
            with zipfile.ZipFile(path) as z:
                self.assertNotIn("sketchimg", z.read("Contents/content.hpf").decode())
                self.assertFalse(any("sketchimg" in n for n in z.namelist()))


if __name__ == "__main__":
    unittest.main()


class SketchImageInputTests(unittest.TestCase):
    def test_large_photo_is_resized_to_jpeg_and_transparent_stays_png(self):
        from docfit_app import sketch_image_input as sii
        with tempfile.TemporaryDirectory() as folder:
            photo = Path(folder) / "사진 1.bmp"
            Image.new("RGB", (3200, 1600), (10, 120, 200)).save(photo)
            out = sii.from_path(photo)
            self.assertEqual((out["kind"], out["width"], out["height"]), ("jpg", 1600, 800))
            self.assertEqual(base64.b64decode(out["data"])[:3], b"\xff\xd8\xff")
            logo = Path(folder) / "logo.png"
            Image.new("RGBA", (40, 20), (0, 0, 0, 0)).save(logo)
            self.assertEqual(sii.from_path(logo)["kind"], "png")
            text = Path(folder) / "memo.txt"
            text.write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                sii.from_path(text)

    def test_clipboard_image_and_copied_files_and_empty(self):
        from docfit_app import sketch_image_input as sii
        self.assertEqual(sii.from_clipboard(lambda: Image.new("RGB", (5, 5)))["kind"], "jpg")
        with tempfile.TemporaryDirectory() as folder:
            pic = Path(folder) / "a.png"
            Image.new("RGB", (5, 5)).save(pic)
            self.assertEqual(sii.from_clipboard(lambda: [str(Path(folder) / "x.txt"), str(pic)])["width"], 5)
        with self.assertRaises(ValueError):
            sii.from_clipboard(lambda: None)

    def test_drop_on_sketch_tab_is_held_for_the_canvas_with_its_position(self):
        from unittest.mock import Mock
        from desktop_web_ui import DesktopWebBridge
        with tempfile.TemporaryDirectory() as folder:
            pic = Path(folder) / "사진.png"
            Image.new("RGB", (30, 20), (1, 2, 3)).save(pic)
            gui = Mock(running=False, files=[])
            bridge = DesktopWebBridge(gui)
            bridge._tk = lambda callback: callback()
            bridge.get_state = Mock(return_value={})
            bridge.window = Mock()
            bridge.set_drop_target("sketch_image")
            bridge.receive_drop([str(pic)], client_x=120, client_y=80)
            gui.파일추가.assert_not_called()  # 문서 목록에 들어가지 않는다
            bridge.window.run_js.assert_any_call("window.dispatchEvent(new Event('docfit-sketch-image-dropped'));")
            bridge._tk = lambda callback: Path(folder)  # 설정 폴더
            taken = bridge.table_sketch("take_drop")
            self.assertEqual((taken["client_x"], taken["client_y"], taken["width"]), (120, 80, 30))
            self.assertFalse(bridge.table_sketch("take_drop")["ok"])  # 한 번만 가져간다
            bridge._tk = lambda callback: callback()
            bridge.receive_drop([str(Path(folder) / "memo.txt")])
            self.assertIsNone(getattr(bridge, "_sketch_drop", None))
