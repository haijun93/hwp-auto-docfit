"""표 스케치 인식: 사진·스캔에 가까운 열화(그림자·원근·JPEG·흔들림·줄무늬·글자) 합성 시험."""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import bench_sketch_degraded as bench  # noqa: E402

from docfit_core import table_sketch as ts  # noqa: E402
from docfit_core import table_sketch_recognize as rec  # noqa: E402


class DegradedRecognizeTests(unittest.TestCase):
    def check(self, name, seeds=3):
        exp = bench.expected()
        for seed in range(seeds):
            result = rec.recognize_image(bench.SCENARIOS[name](random.Random(seed)))
            self.assertEqual((result["cols"], result["rows"]), (4, 4), f"{name} seed={seed}")
            drawing, _ = ts.normalize(result["sketch"])
            got = {(l["x1"], l["y1"], l["x2"], l["y2"]) for l in drawing["lines"]}
            self.assertEqual(got, exp, f"{name} seed={seed}")

    def test_clean_asymmetric_table_keeps_vertical_partial_lines(self):
        self.check("깨끗(기준)", 1)

    def test_shadow_and_uneven_light(self):
        self.check("그림자·조명")

    def test_trapezoid_perspective_is_rectified(self):
        self.check("원근 왜곡")

    def test_jpeg_noise(self):
        self.check("JPEG 잡음")

    def test_hand_drawn_wobbly_lines(self):
        self.check("손그림 흔들림")

    def test_ruled_paper_background(self):
        self.check("종이 줄무늬")

    def test_text_inside_cells(self):
        self.check("칸 안 글자")

    def test_combined(self):
        self.check("복합(그림자+JPEG+흔들림)")


if __name__ == "__main__":
    unittest.main()
