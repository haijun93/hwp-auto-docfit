"""파일변환: JPG·PNG 추가 허용과 그림 → PDF 직접 변환(2026-11-07)."""
import tempfile
import unittest
from pathlib import Path

from docfit_app.native_file_dialog_service import ADDABLE, IMAGES, PURPOSES
from docfit_core.file_conversion import convert_image_to_pdf, convert_to_pdf, output_path_for


class ImageAddPolicyTests(unittest.TestCase):
    def test_add_files_and_folder_accept_images(self):
        for purpose in ("add_files", "add_folder"):
            allowed = PURPOSES[purpose][1]
            for suffix in (".jpg", ".jpeg", ".png"):
                self.assertIn(suffix, allowed)
        self.assertTrue(IMAGES <= ADDABLE)

    def test_other_purposes_unchanged(self):
        self.assertNotIn(".jpg", PURPOSES["add_format_file"][1])
        self.assertNotIn(".png", PURPOSES["table_template"][1])


class ImageToPdfTests(unittest.TestCase):
    def setUp(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow 없음")
        self.Image = Image
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _make(self, name, mode="RGB"):
        path = self.dir / name
        self.Image.new(mode, (40, 30), (200, 50, 50) if mode == "RGB" else (200, 50, 50, 120)).save(path)
        return path

    def test_jpg_and_png_become_pdf_without_app(self):
        for name, mode in (("a.jpg", "RGB"), ("b.png", "RGBA")):
            source = self._make(name, mode)
            target = output_path_for(source, "pdf")
            self.assertEqual(convert_to_pdf(None, source, target), target)
            self.assertTrue(target.read_bytes().startswith(b"%PDF"))

    def test_existing_target_is_not_overwritten(self):
        source = self._make("c.jpg")
        target = self.dir / "c(PDF변경).pdf"
        target.write_bytes(b"keep")
        with self.assertRaises(ValueError):
            convert_image_to_pdf(source, target)
        self.assertEqual(target.read_bytes(), b"keep")

    def test_broken_image_reports_error(self):
        source = self.dir / "bad.jpg"
        source.write_bytes(b"not an image")
        with self.assertRaises(ValueError):
            convert_image_to_pdf(source, self.dir / "bad.pdf")


if __name__ == "__main__":
    unittest.main()
