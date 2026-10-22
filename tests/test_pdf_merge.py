"""PDF 합치기 모듈 시험: 쪽 수·순서 보존, 책갈피, 암호 PDF 거부, 안전한 경로 작명."""

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image
from pypdf import PdfReader, PdfWriter

from docfit_core.pdf_merge import (
    IMAGE_EXTENSIONS,
    MergeResult,
    PdfMergeError,
    image_to_pdf_bytes,
    merge_to_pdf,
    merged_output_path,
)


class PdfMergeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def test_merge_mixed_pdf_and_images(self):
        """빈 PDF 2개와 그림(RGBA PNG, JPEG) 2개를 합칠 때 쪽 수·순서·책갈피가 올바른지 확인한다."""
        # 1. 1쪽 빈 PDF (100 x 200 pt)
        pdf1 = self.root / "doc1.pdf"
        w1 = PdfWriter()
        w1.add_blank_page(width=100, height=200)
        with open(pdf1, "wb") as f:
            w1.write(f)

        # 2. 2쪽 빈 PDF (200 x 300 pt 각각)
        pdf2 = self.root / "doc2.pdf"
        w2 = PdfWriter()
        w2.add_blank_page(width=200, height=300)
        w2.add_blank_page(width=200, height=300)
        with open(pdf2, "wb") as f:
            w2.write(f)

        # 3. RGBA PNG 1장 (150 x 300 px -> 150dpi 시 72 x 144 pt)
        png = self.root / "img1.png"
        img_png = Image.new("RGBA", (150, 300), (255, 0, 0, 128))
        img_png.save(png)

        # 4. JPEG 1장 (300 x 150 px -> 150dpi 시 144 x 72 pt)
        jpg = self.root / "img2.jpg"
        img_jpg = Image.new("RGB", (300, 150), (0, 255, 0))
        img_jpg.save(jpg)

        target = self.root / "merged_out.pdf"
        parts = [
            ("첫째 문서", pdf1),
            ("둘째 문서", pdf2),
            ("투명 그림", png),
            ("풍경 사진", jpg),
        ]

        result = merge_to_pdf(parts, target)

        # 반환값 검증
        self.assertEqual(result.files, 4)
        self.assertEqual(result.pages, 5)  # 1 + 2 + 1 + 1 = 5쪽
        self.assertEqual(result.summary(), "파일 4개 → 5쪽")
        self.assertTrue(target.exists())

        # 결과 PDF 검증
        reader = PdfReader(str(target))
        self.assertEqual(len(reader.pages), 5)

        # 순서 및 쪽 크기(mediabox) 검증
        sizes = [
            (round(float(p.mediabox.width)), round(float(p.mediabox.height)))
            for p in reader.pages
        ]
        expected_sizes = [
            (100, 200),  # 첫째 문서 (1쪽)
            (200, 300),  # 둘째 문서 (1쪽)
            (200, 300),  # 둘째 문서 (2쪽)
            (72, 144),   # 투명 그림 (150x300 px @ 150dpi)
            (144, 72),   # 풍경 사진 (300x150 px @ 150dpi)
        ]
        self.assertEqual(sizes, expected_sizes)

        # 책갈피(outline) 수 및 제목 검증
        self.assertEqual(len(reader.outline), 4)
        outline_titles = [item.title for item in reader.outline]
        self.assertEqual(outline_titles, ["첫째 문서", "둘째 문서", "투명 그림", "풍경 사진"])

    def test_encrypted_pdf_is_rejected_and_no_leftover(self):
        """암호가 걸린 PDF는 거부되고 대상 파일 및 임시 파일이 남지 않는다."""
        secret_pdf = self.root / "encrypted.pdf"
        w = PdfWriter()
        w.add_blank_page(width=100, height=100)
        w.encrypt("secret_pw")
        with open(secret_pdf, "wb") as f:
            w.write(f)

        target = self.root / "should_not_exist.pdf"
        parts = [("보안문서", secret_pdf)]

        with self.assertRaises(PdfMergeError) as ctx:
            merge_to_pdf(parts, target)

        msg = str(ctx.exception)
        self.assertIn("보안문서", msg)
        self.assertIn("암호·보안이 걸린 PDF는 합칠 수 없습니다", msg)

        # 파일이 생성되거나 남지 않아야 함
        self.assertFalse(target.exists())
        leftover_tmps = list(self.root.glob("*.tmp"))
        self.assertEqual(leftover_tmps, [])

    def test_merged_output_path(self):
        """출력 경로 명명 규칙: 1개, 여러 개, 중복 번호 증가, 원본 폴더 위치 유지 확인."""
        doc1 = self.root / "기획안.hwp"
        doc2 = self.root / "붙임1.pdf"
        doc3 = self.root / "붙임2.png"

        # 1개일 때
        path_single = merged_output_path([doc1])
        self.assertEqual(path_single, self.root / "기획안(합친 PDF).pdf")
        self.assertEqual(path_single.parent, self.root)

        # 여러 개(3개)일 때: '기획안 외 2개(합친 PDF).pdf'
        path_multi = merged_output_path([doc1, doc2, doc3])
        self.assertEqual(path_multi, self.root / "기획안 외 2개(합친 PDF).pdf")
        self.assertEqual(path_multi.parent, self.root)

        # 대상 파일이 이미 존재할 때 중복 번호 (2), (3) 부여
        path_multi.touch()
        path_multi_2 = merged_output_path([doc1, doc2, doc3])
        self.assertEqual(path_multi_2, self.root / "기획안 외 2개(합친 PDF) (2).pdf")

        path_multi_2.touch()
        path_multi_3 = merged_output_path([doc1, doc2, doc3])
        self.assertEqual(path_multi_3, self.root / "기획안 외 2개(합친 PDF) (3).pdf")

        # 빈 목록 거부
        with self.assertRaises(PdfMergeError):
            merged_output_path([])

    def test_target_already_exists_rejects_and_preserves_target(self):
        """target 파일이 이미 존재하면 덮어쓰지 않고 거부하며 원본 내용이 보존된다."""
        target = self.root / "already_exists.pdf"
        original_bytes = b"%PDF-1.7-important-existing-file"
        target.write_bytes(original_bytes)

        pdf = self.root / "source.pdf"
        w = PdfWriter()
        w.add_blank_page(width=100, height=100)
        with open(pdf, "wb") as f:
            w.write(f)

        with self.assertRaises(PdfMergeError) as ctx:
            merge_to_pdf([("자료", pdf)], target)

        self.assertIn("이미 있습니다", str(ctx.exception))
        # 원본 바이트 그대로 보존
        self.assertEqual(target.read_bytes(), original_bytes)

    def test_multiframe_gif_becomes_multiple_pages(self):
        """다중 프레임 GIF는 프레임 수만큼의 쪽으로 변환되어 합쳐진다."""
        gif_path = self.root / "animation.gif"
        frames = [
            Image.new("RGB", (100, 100), (255, 0, 0)),
            Image.new("RGB", (100, 100), (0, 255, 0)),
            Image.new("RGB", (100, 100), (0, 0, 255)),
        ]
        frames[0].save(gif_path, save_all=True, append_images=frames[1:])

        # 1. image_to_pdf_bytes 직접 시험
        pdf_bytes = image_to_pdf_bytes(gif_path)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        self.assertEqual(len(reader.pages), 3)

        # 2. merge_to_pdf 시험
        target = self.root / "gif_merged.pdf"
        result = merge_to_pdf([("움직이는 그림", gif_path)], target)
        self.assertEqual(result.pages, 3)

        merged_reader = PdfReader(str(target))
        self.assertEqual(len(merged_reader.pages), 3)

    def test_zero_page_pdf_rejected(self):
        """0쪽 PDF는 거부되고 에러 메시지에 원본 표시 이름이 포함된다."""
        zero_pdf = self.root / "zero.pdf"
        zero_pdf.write_bytes(b"%PDF-1.4\n%%EOF")

        target = self.root / "out.pdf"
        with self.assertRaises(PdfMergeError) as ctx:
            merge_to_pdf([("빈 PDF", zero_pdf)], target)

        self.assertIn("빈 PDF", str(ctx.exception))

    def test_image_size_limit_rejected(self):
        """200MB 초과 그림 파일은 변환을 거부한다."""
        big_image = self.root / "huge.png"
        with open(big_image, "wb") as f:
            f.seek(200 * 1024 * 1024 + 10)
            f.write(b"\x00")

        with self.assertRaises(PdfMergeError) as ctx:
            image_to_pdf_bytes(big_image)

        self.assertIn("200MB", str(ctx.exception))

    def test_image_pixel_limit_rejected(self):
        """2억 픽셀 초과 그림은 거부한다."""
        dummy = self.root / "pixel_test.png"
        dummy.write_bytes(b"fake-image-data")

        mock_frame = MagicMock()
        mock_frame.width = 20000
        mock_frame.height = 10001  # 200,020,000 픽셀 > 200,000,000

        with patch("PIL.Image.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_frame
            with patch("PIL.ImageSequence.Iterator", return_value=[mock_frame]):
                with self.assertRaises(PdfMergeError) as ctx:
                    image_to_pdf_bytes(dummy)

        self.assertIn("2억", str(ctx.exception))

    def test_total_pages_limit_rejected(self):
        """전체 쪽 수 상한(3000쪽)을 초과하면 거부한다."""
        pdf = self.root / "doc.pdf"
        w = PdfWriter()
        w.add_blank_page(width=100, height=100)
        with open(pdf, "wb") as f:
            w.write(f)

        target = self.root / "out.pdf"
        with patch("pypdf.PdfReader.pages", new_callable=lambda: [MagicMock()] * 3001):
            with self.assertRaises(PdfMergeError) as ctx:
                merge_to_pdf([("초대형 문서", pdf)], target)

        self.assertIn("3000쪽", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
