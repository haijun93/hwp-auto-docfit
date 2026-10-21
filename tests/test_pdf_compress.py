"""PDF 압축: 원본 보존, 글자·쪽 보존, 보안 PDF 권한 유지, 거부 사유."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


def _scan_pdf(path, pages=2):
    """사진처럼 무늬가 있는 큰 그림을 품질 95 JPEG로 담은 A4 300dpi PDF."""
    images = []
    for index in range(pages):
        image = Image.new("RGB", (2480, 3508), "white")
        draw = ImageDraw.Draw(image)
        for y in range(0, 3508, 6):
            draw.line([(0, y), (2480, (y * 7 + index * 131) % 3508)], fill=((y * 3) % 255, (y * 5) % 255, 120), width=3)
        images.append(image)
    images[0].save(path, save_all=True, append_images=images[1:], resolution=300, quality=95)


def _encrypt(source, target, user_password=""):
    from pypdf import PdfWriter
    from pypdf.constants import UserAccessPermissions as UAP

    writer = PdfWriter(clone_from=str(source))
    writer.encrypt(user_password=user_password, owner_password="owner",
                   permissions_flag=UAP.PRINT | UAP.PRINT_TO_REPRESENTATION, algorithm="AES-256")
    with open(target, "wb") as stream:
        writer.write(stream)


class PdfCompressTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.scan = self.root / "scan.pdf"
        _scan_pdf(self.scan)

    def tearDown(self):
        self.folder.cleanup()

    def test_scan_pdf_shrinks_keeps_pages_and_source(self):
        from docfit_core.pdf_compress import compress_pdf

        digest = hashlib.sha256(self.scan.read_bytes()).hexdigest()
        result = compress_pdf(self.scan, self.root / "out.pdf")
        self.assertGreater(result.saving, 0.3)
        self.assertFalse(result.secured)
        self.assertEqual(hashlib.sha256(self.scan.read_bytes()).hexdigest(), digest)
        from pypdf import PdfReader
        self.assertEqual(len(PdfReader(str(result.target)).pages), 2)

    def test_secured_pdf_keeps_encryption_and_permissions(self):
        from pypdf import PdfReader
        from docfit_core.pdf_compress import compress_pdf

        secured = self.root / "secured.pdf"
        _encrypt(self.scan, secured)
        result = compress_pdf(secured, self.root / "out.pdf")
        self.assertTrue(result.secured)
        before, after = PdfReader(str(secured)), PdfReader(str(result.target))
        self.assertTrue(after.is_encrypted)
        before.decrypt("")
        after.decrypt("")
        self.assertEqual(int(after.trailer["/Encrypt"]["/P"]), int(before.trailer["/Encrypt"]["/P"]))
        self.assertIn("보안 유지", result.summary())

    def test_refusals(self):
        from docfit_core.pdf_compress import NothingToCompress, PdfCompressError, compress_pdf

        opened = self.root / "open.pdf"
        _encrypt(self.scan, opened, user_password="1234")
        with self.assertRaisesRegex(PdfCompressError, "열기 암호"):
            compress_pdf(opened, self.root / "a.pdf")
        fake = self.root / "drm.pdf"
        fake.write_bytes(b"DRM-PROTECTED")
        with self.assertRaisesRegex(PdfCompressError, "올바른 PDF"):
            compress_pdf(fake, self.root / "b.pdf")
        existing = self.root / "exists.pdf"
        existing.write_bytes(b"x")
        with self.assertRaises(PdfCompressError):
            compress_pdf(self.scan, existing)
        self.assertEqual(existing.read_bytes(), b"x")
        small = self.root / "small.pdf"
        once = compress_pdf(self.scan, small)
        with self.assertRaises(NothingToCompress):
            compress_pdf(once.target, self.root / "again.pdf")
        self.assertFalse((self.root / "again.pdf").exists())

    def test_output_name_and_target_menu(self):
        from docfit_core.file_conversion import output_path_for

        self.assertEqual(output_path_for(self.scan, "pdfz").name, "scan(PDF압축).pdf")
        text = self.root / "memo.txt"
        text.write_text("가", encoding="utf-8")
        with self.assertRaises(ValueError):
            output_path_for(text, "pdfz")


if __name__ == "__main__":
    unittest.main()
