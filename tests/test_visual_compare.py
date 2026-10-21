"""COM 없이 화면 차이·쪽 판정·선택 PDF 렌더링을 검증한다."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

from scripts.visual_compare_pc import image_difference, summary_passes, compare_pdfs, parse_pair


@unittest.skipUnless(importlib.util.find_spec("PIL"), "선택 의존성 Pillow 없음")
class ImageDifferenceTests(unittest.TestCase):
    def setUp(self):
        from PIL import Image
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.original = Path(self.work.name) / "original.png"
        self.result = Path(self.work.name) / "result.png"
        self.image = Image.new("RGB", (10, 10), "white")
        self.addCleanup(self.image.close)
        self.image.save(self.original)

    def test_identical(self):
        self.image.save(self.result)
        self.assertEqual(image_difference(self.original, self.result), (0, None))

    def test_ratio_and_bbox(self):
        for point in ((2, 3), (3, 3), (2, 4), (3, 4)):
            self.image.putpixel(point, (0, 0, 0))
        self.image.save(self.result)
        self.assertEqual(image_difference(self.original, self.result), (0.04, [2, 3, 4, 5]))

    def test_threshold_is_strict(self):
        self.image.putpixel((0, 0), (215, 215, 215))  # 차이 40: 제외
        self.image.putpixel((9, 9), (214, 214, 214))  # 차이 41: 포함
        self.image.save(self.result)
        self.assertEqual(image_difference(self.original, self.result), (0.01, [9, 9, 10, 10]))

    def test_white_size_difference(self):
        self.image.crop((0, 0, 9, 10)).save(self.result)
        self.assertEqual(image_difference(self.original, self.result), (0.1, [9, 0, 10, 10]))


class SummaryTests(unittest.TestCase):
    def summary(self, ratio=0.005):
        return {"기본서식": {"pages_original": 1, "pages_result": 1,
                            "pages": [{"page": 1, "diff_ratio": ratio, "bbox": None}]}}

    def test_default_boundary(self):
        self.assertTrue(summary_passes(self.summary()))
        self.assertFalse(summary_passes(self.summary(0.00501)))
        self.assertTrue(summary_passes(self.summary(0.01), 0.01))

    def test_page_count_mismatch(self):
        summary = self.summary(0)
        summary["기본서식"]["pages_result"] = 2
        self.assertFalse(summary_passes(summary))

    def test_incomplete_and_empty(self):
        self.assertFalse(summary_passes({}))
        summary = self.summary(0)
        summary["기본서식"]["pages"] = []
        self.assertFalse(summary_passes(summary))
        summary["기본서식"]["pages_original"] = 0
        summary["기본서식"]["pages_result"] = 0
        self.assertFalse(summary_passes(summary))

    def test_invalid_ratio_and_page(self):
        for ratio in (float("nan"), float("inf"), -1):
            self.assertFalse(summary_passes(self.summary(ratio)))
        summary = self.summary(0)
        summary["기본서식"]["pages"][0]["page"] = 2
        self.assertFalse(summary_passes(summary))

    def test_all_pairs_must_pass(self):
        summary = self.summary(0)
        summary["다른서식"] = self.summary(0.1)["기본서식"]
        self.assertFalse(summary_passes(summary))

    def test_pair_with_spaces(self):
        name, original, result = parse_pair("기본서식=기본 서식.hwpx,기본 서식.all.hwpx")
        self.assertEqual(name, "기본서식")
        self.assertEqual(original.name, "기본 서식.hwpx")
        self.assertEqual(result.name, "기본 서식.all.hwpx")


@unittest.skipUnless(importlib.util.find_spec("pypdfium2") and importlib.util.find_spec("PIL"),
                     "선택 의존성 pypdfium2/Pillow 없음")
class PdfRenderingTests(unittest.TestCase):
    def test_render_and_missing_page(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as work:
            original, result = Path(work) / "original.pdf", Path(work) / "result.pdf"
            with Image.new("RGB", (10, 10), "white") as image:
                image.save(original, save_all=True, append_images=[image])
                image.save(result)
            summary = compare_pdfs(original, result)
            self.assertEqual((summary["pages_original"], summary["pages_result"]), (2, 1))
            self.assertEqual(summary["pages"][0]["diff_ratio"], 0)
            self.assertFalse(summary_passes({"합성": summary}))
            self.assertTrue((Path(work) / "side_by_side_002.png").is_file())


if __name__ == "__main__":
    unittest.main()
