"""표 스케치 이미지 인식(순수 Pillow) 시험: 합성 이미지로 기대 격자와 비교한다."""
import base64
import random
import tempfile
import time
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from docfit_app.table_sketch_service import TableSketchService
from docfit_core import table_sketch as ts
from docfit_core import table_sketch_recognize as rec

XS = [100, 300, 500, 700, 900]   # 열 경계 x (4열)
YS = [100, 300, 500, 700, 900]   # 행 경계 y (4행)


def full_grid(xs=XS, ys=YS):
    """(방향, 고정 인덱스, 시작 인덱스, 끝 인덱스) 선 목록: 모든 칸이 나뉜 격자."""
    out = [("h", r, 0, len(xs) - 1) for r in range(len(ys))]
    out += [("v", c, 0, len(ys) - 1) for c in range(len(xs))]
    return out


def paint(spec, xs=XS, ys=YS, size=(1000, 1000), width=3, gaps=(), noise=0, angle=0.0,
          bg=255, ink=0, seed=1, widths=None):
    """spec 선을 그린 이미지. gaps: 선마다 지울 (방향, 인덱스, 비율 중심, 지우는 픽셀 길이)."""
    img = Image.new("L", size, bg)
    d = ImageDraw.Draw(img)
    for n, (kind, fixed, a, b) in enumerate(spec):
        w = (widths or {}).get(n, width)
        if kind == "h":
            y = ys[fixed]
            d.line([(xs[a], y), (xs[b], y)], fill=ink, width=w)
        else:
            x = xs[fixed]
            d.line([(x, ys[a]), (x, ys[b])], fill=ink, width=w)
    for kind, fixed, center, length in gaps:
        if kind == "h":
            y = ys[fixed]
            d.rectangle([center - length // 2, y - 8, center + length // 2, y + 8], fill=bg)
        else:
            x = xs[fixed]
            d.rectangle([x - 8, center - length // 2, x + 8, center + length // 2], fill=bg)
    if noise:
        rnd = random.Random(seed)
        for _ in range(noise):
            x, y = rnd.randrange(size[0]), rnd.randrange(size[1])
            d.ellipse([x, y, x + rnd.choice((0, 1, 2)), y + rnd.choice((0, 1, 2))], fill=ink)
    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC, fillcolor=bg)
    return img


def expected_lines(spec):
    lines = [dict(x1=a, y1=f, x2=b, y2=f) if k == "h" else dict(x1=f, y1=a, x2=f, y2=b) for k, f, a, b in spec]
    drawing, _ = ts.normalize(dict(grid=dict(cols=4, rows=4, cell_mm=5.0), lines=lines))
    return {(l["x1"], l["y1"], l["x2"], l["y2"]) for l in drawing["lines"]}


def got_lines(result):
    drawing, _ = ts.normalize(result["sketch"])
    return {(l["x1"], l["y1"], l["x2"], l["y2"]) for l in drawing["lines"]}


class RecognizeTests(unittest.TestCase):
    def check(self, img, spec, cols=4, rows=4, **kw):
        result = rec.recognize_image(img)
        self.assertEqual((result["cols"], result["rows"]), (cols, rows))
        self.assertEqual(got_lines(result), expected_lines(spec))
        return result

    def test_01_plain_grid(self):
        self.check(paint(full_grid()), full_grid())

    def test_02_thin_one_pixel_lines(self):
        self.check(paint(full_grid(), width=1), full_grid())

    def test_03_thick_lines_not_split(self):
        result = self.check(paint(full_grid(), width=11), full_grid())
        self.assertTrue(all(l["width"] == "thin" for l in result["sketch"]["lines"]))

    def test_04_tilt_positive_2_degrees(self):
        r = self.check(paint(full_grid(), angle=2.0), full_grid())
        self.assertAlmostEqual(abs(r["angle"]), 2.0, delta=0.4)

    def test_05_tilt_negative_3_degrees(self):
        self.check(paint(full_grid(), angle=-3.0), full_grid())

    def test_06_tilt_small_half_degree(self):
        self.check(paint(full_grid(), angle=0.5, width=2), full_grid())

    def test_07_broken_lines_within_20_percent(self):
        gaps = [("h", 2, 400, 36), ("h", 1, 700, 30), ("v", 2, 600, 36), ("v", 3, 400, 30)]
        self.check(paint(full_grid(), gaps=gaps), full_grid())

    def test_08_broken_and_tilted(self):
        gaps = [("h", 2, 400, 30), ("v", 1, 600, 30)]
        self.check(paint(full_grid(), gaps=gaps, angle=-1.5), full_grid())

    def test_09_speckle_noise(self):
        self.check(paint(full_grid(), noise=1500), full_grid())

    def test_10_noise_and_tilt_and_gray_background(self):
        self.check(paint(full_grid(), noise=800, angle=1.0, bg=235, ink=40), full_grid())

    def test_11_merged_cells(self):
        spec = [("h", 0, 0, 4), ("h", 1, 0, 4), ("h", 2, 0, 2), ("h", 3, 0, 4), ("h", 4, 0, 4),
                ("v", 0, 0, 4), ("v", 1, 0, 4), ("v", 2, 0, 1), ("v", 2, 2, 4), ("v", 3, 0, 4), ("v", 4, 0, 4)]
        r = self.check(paint(spec), spec)
        layout = ts.preview(r["sketch"])
        self.assertTrue(any(c.get("rowspan", 1) > 1 or c.get("colspan", 1) > 1 for c in layout["cells"]))

    def test_12_merged_cells_with_tilt(self):
        spec = [("h", 0, 0, 4), ("h", 1, 0, 4), ("h", 2, 1, 4), ("h", 3, 0, 4), ("h", 4, 0, 4),
                ("v", 0, 0, 4), ("v", 1, 0, 4), ("v", 2, 0, 1), ("v", 2, 2, 4), ("v", 3, 0, 4), ("v", 4, 0, 4)]
        self.check(paint(spec, angle=1.5), spec)

    def test_13_thick_outer_frame_thin_inside(self):
        spec = full_grid()
        widths = {i: 9 for i, (k, f, a, b) in enumerate(spec) if f in (0, 4)}
        r = self.check(paint(spec, widths=widths, width=2), spec)
        thick = [l for l in r["sketch"]["lines"] if l["width"] == "thick"]
        self.assertEqual(len(thick), 4)

    def test_14_uneven_columns_and_non_square_image(self):
        xs, ys = [40, 130, 400, 520, 760], [30, 90, 330, 380]
        spec = full_grid(xs, ys)
        self.check(paint(spec, xs=xs, ys=ys, size=(820, 420)), spec, cols=4, rows=3)

    def test_15_text_inside_cells_ignored(self):
        img = paint(full_grid())
        d = ImageDraw.Draw(img)
        for r in range(4):
            for c in range(4):
                d.text((XS[c] + 60, YS[r] + 90), "ab12 Xy", fill=0)
                d.line([(XS[c] + 40, YS[r] + 150), (XS[c] + 70, YS[r] + 150)], fill=0, width=2)
        self.check(img, full_grid())

    def test_16_png_bytes_rgba_and_jpeg(self):
        img = paint(full_grid(), angle=1.0).convert("RGBA")
        buf = BytesIO(); img.save(buf, "PNG")
        self.check(buf.getvalue(), full_grid())
        buf = BytesIO(); paint(full_grid(), angle=1.0).convert("RGB").save(buf, "JPEG", quality=60)
        self.check(buf.getvalue(), full_grid())

    def test_17_rejects_blank_and_garbage(self):
        with self.assertRaises(ValueError):
            rec.recognize_image(Image.new("L", (400, 400), 255))
        with self.assertRaises(ValueError):
            rec.recognize_image(b"not an image")
        with self.assertRaises(ValueError):
            rec.recognize_image(Image.new("L", (10, 10), 255))

    def test_18_large_image_downscaled(self):
        img = paint(full_grid(), size=(1000, 1000)).resize((3000, 3000), Image.NEAREST)
        self.check(img, full_grid())

    def test_19_speed_1000px(self):
        img = paint(full_grid(), noise=1500, angle=1.0)
        start = time.perf_counter()
        rec.recognize_image(img)
        elapsed = time.perf_counter() - start
        print(f"\n[1000x1000 인식 시간] {elapsed:.3f}s")
        self.assertLess(elapsed, 5.0)


class ServiceRecognizeTests(unittest.TestCase):
    def test_service_command(self):
        buf = BytesIO(); paint(full_grid(), angle=1.0).save(buf, "PNG")
        payload = base64.b64encode(buf.getvalue()).decode("ascii")
        with tempfile.TemporaryDirectory() as folder:
            service = TableSketchService(Path(folder))
            result = service.command("recognize", payload)
            self.assertTrue(result["ok"], result)
            self.assertEqual((result["cols"], result["rows"]), (4, 4))
            self.assertTrue(service.command("preview", result["sketch"])["ok"])
            self.assertFalse(service.command("recognize", "###")["ok"])
            self.assertFalse(service.command("recognize", None)["ok"])


if __name__ == "__main__":
    unittest.main()
