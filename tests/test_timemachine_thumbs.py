"""타임머신 썸네일 시험. 합성 파일만 임시 폴더에서 다룬다."""
import io
import os
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from docfit_core import pdfium_guard
from docfit_core.timemachine import thumbs


def picture_bytes(fmt="PNG", size=(320, 200), color="blue"):
    output = io.BytesIO()
    Image.new("RGB", size, color).save(output, format=fmt)
    return output.getvalue()


def minimal_pdf():
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 600] >>"]
    output = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(len(output))
        output += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    start = len(output)
    output += b"xref\n0 4\n0000000000 65535 f \n"
    for offset in offsets:
        output += b"%010d 00000 n \n" % offset
    output += b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % start
    return bytes(output)


class ThumbsTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def archive(self, name, members):
        target = self.folder / name
        with zipfile.ZipFile(target, "w") as archive:
            for member, data in members.items():
                archive.writestr(member, data)
        return str(target)

    def assertThumbnail(self, data):
        self.assertIsNotNone(data)
        with Image.open(io.BytesIO(data)) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(max(image.size), thumbs.SIZE)
        return data


class RenderTests(ThumbsTestCase):
    def test_hwpx_preview(self):
        self.assertThumbnail(thumbs.render(self.archive("a.hwpx", {"Preview/PrvImage.png": picture_bytes()})))

    def test_hwpx_without_preview_is_none(self):
        self.assertIsNone(thumbs.render(self.archive("a.hwpx", {"Contents/section0.xml": b"<a/>"})))

    def test_hwpx_corrupt_is_none(self):
        broken = self.folder / "broken.hwpx"
        broken.write_bytes(b"PK\x03\x04 not a zip")
        self.assertIsNone(thumbs.render(str(broken)))
        self.assertIsNone(thumbs.render(self.archive("bad.hwpx", {"Preview/PrvImage.png": b"not a picture"})))

    def test_hwpx_with_encryption_manifest_is_none(self):
        manifest = b'<manifest><file-entry><encryption-data/></file-entry></manifest>'
        path = self.archive("secret.hwpx", {"Preview/PrvImage.png": picture_bytes(), "META-INF/manifest.xml": manifest})
        self.assertIsNone(thumbs.render(path))

    def test_archive_limits_block_zip_bomb(self):
        target = self.folder / "bomb.hwpx"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("Preview/PrvImage.png", picture_bytes())
            archive.writestr("huge.bin", b"\0" * (thumbs.MAX_ARCHIVE_BYTES + 1))
        self.assertLess(target.stat().st_size, 1024 * 1024)
        self.assertIsNone(thumbs.render(str(target)))
        path = self.archive("many.hwpx", {"Preview/PrvImage.png": picture_bytes(),
                                          **{f"f{i}": b"" for i in range(thumbs.MAX_ARCHIVE_ENTRIES)}})
        self.assertIsNone(thumbs.render(path))
        with patch.object(thumbs, "MAX_MEMBER_BYTES", 10):
            self.assertIsNone(thumbs.render(self.archive("big.hwpx", {"Preview/PrvImage.png": picture_bytes()})))

    def test_office_thumbnail(self):
        for name in ("a.docx", "a.xlsx", "a.xlsm", "a.pptx"):
            path = self.archive(name, {"docProps/thumbnail.jpeg": picture_bytes("JPEG")})
            self.assertThumbnail(thumbs.render(path))

    def test_docx_without_thumbnail_is_none(self):
        self.assertIsNone(thumbs.render(self.archive("a.docx", {"word/document.xml": b"<a/>"})))

    def test_encrypted_office_is_none(self):
        # 암호 건 Office 문서는 ZIP이 아니라 OLE 복합 문서다.
        path = self.folder / "secret.docx"
        path.write_bytes(bytes.fromhex("D0CF11E0A1B11AE1") + b"\0" * 512)
        self.assertIsNone(thumbs.render(str(path)))

    def test_pdf_first_page(self):
        path = self.folder / "a.pdf"
        path.write_bytes(minimal_pdf())
        data = self.assertThumbnail(thumbs.render(str(path)))
        with Image.open(io.BytesIO(data)) as image:
            self.assertEqual(image.size[1], thumbs.SIZE)
            self.assertLess(image.size[0], image.size[1])

    def test_pdf_corrupt_is_none(self):
        path = self.folder / "bad.pdf"
        path.write_bytes(b"%PDF-1.4 broken")
        self.assertIsNone(thumbs.render(str(path)))

    def test_pdf_busy_when_other_feature_holds_pdfium(self):
        path = self.folder / "a.pdf"
        path.write_bytes(minimal_pdf())
        held, release = threading.Event(), threading.Event()
        def holder():
            with pdfium_guard.exclusive():
                held.set()
                release.wait(5)
        worker = threading.Thread(target=holder)
        worker.start()
        self.assertTrue(held.wait(2))
        try:
            with patch.object(thumbs, "PDF_LOCK_WAIT", 0.01), self.assertRaises(thumbs.ThumbnailBusy):
                thumbs.render(str(path))
        finally:
            release.set()
            worker.join()

    def test_images(self):
        for name, fmt in (("a.png", "PNG"), ("a.jpg", "JPEG"), ("a.gif", "GIF"), ("a.bmp", "BMP"),
                          ("a.tiff", "TIFF"), ("a.webp", "WEBP")):
            path = self.folder / name
            path.write_bytes(picture_bytes(fmt))
            self.assertThumbnail(thumbs.render(str(path)))

    def test_transparent_png_flattens_on_white(self):
        path = self.folder / "alpha.png"
        Image.new("RGBA", (200, 200), (255, 0, 0, 0)).save(path)
        with Image.open(io.BytesIO(thumbs.render(str(path)))) as image:
            self.assertGreater(min(image.convert("RGB").getpixel((5, 5))), 240)

    def test_jpeg_uses_draft_decoding(self):
        path = self.folder / "big.jpg"
        path.write_bytes(picture_bytes("JPEG", (4000, 3000)))
        original = Image.Image.thumbnail
        seen = []
        def spy(image, *args, **kwargs):
            seen.append(image.size)
            return original(image, *args, **kwargs)
        with patch.object(Image.Image, "thumbnail", spy):
            self.assertThumbnail(thumbs.render(str(path)))
        self.assertLess(max(seen[0]), 4000)

    def test_too_many_pixels_is_none(self):
        path = self.folder / "wide.png"
        path.write_bytes(picture_bytes("PNG", (400, 400)))
        with patch.object(thumbs, "MAX_PIXELS", 1000):
            self.assertIsNone(thumbs.render(str(path)))

    def test_image_with_wrong_content_is_none(self):
        path = self.folder / "fake.png"
        path.write_bytes(picture_bytes("JPEG"))  # 확장자와 다른 형식은 해당 해석기만 시도하므로 실패
        self.assertIsNone(thumbs.render(str(path)))

    def test_unsupported_formats_are_none(self):
        for name in ("a.hwp", "a.txt", "a.csv", "a.doc"):
            path = self.folder / name
            path.write_bytes(b"x")
            self.assertIsNone(thumbs.render(str(path)))


class LookupTests(ThumbsTestCase):
    def setUp(self):
        super().setUp()
        self.cache = thumbs.ThumbnailCache(self.folder / "cache")
        self.file = self.folder / "a.png"
        self.file.write_bytes(picture_bytes())

    def test_cloud_flag_skips_without_touching_file(self):
        with patch.object(thumbs.os, "lstat", side_effect=AssertionError("파일을 보면 안 됨")):
            self.assertEqual(thumbs.lookup(str(self.file), self.cache, cloud=True), (None, None))

    def test_recall_attribute_detected_even_if_index_is_stale(self):
        real = os.lstat(self.file)
        class Info:
            st_mode, st_size, st_mtime_ns = real.st_mode, real.st_size, real.st_mtime_ns
            st_file_attributes = 0x00400000
        with patch.object(thumbs.os, "lstat", return_value=Info()):
            self.assertEqual(thumbs.lookup(str(self.file), self.cache), (None, None))

    def test_missing_empty_and_oversized_files(self):
        self.assertEqual(thumbs.lookup(str(self.folder / "none.png"), self.cache), (None, None))
        empty = self.folder / "empty.png"
        empty.write_bytes(b"")
        self.assertEqual(thumbs.lookup(str(empty), self.cache), (None, None))
        with patch.object(thumbs, "MAX_FILE_BYTES", 5):
            self.assertEqual(thumbs.lookup(str(self.file), self.cache), (None, None))

    def test_cache_hit_then_miss_after_change(self):
        cached, key = thumbs.lookup(str(self.file), self.cache)
        self.assertIsNone(cached)
        data = thumbs.generate(str(self.file), key, self.cache)
        self.assertThumbnail(data)
        with patch.object(thumbs, "render", side_effect=AssertionError("캐시 적중이면 다시 만들지 않음")):
            self.assertEqual(thumbs.lookup(str(self.file), self.cache), (data, key))
        self.assertTrue((self.folder / "cache" / f"{key}.jpg").is_file())
        os.utime(self.file, (time.time() + 100, time.time() + 100))
        cached, changed = thumbs.lookup(str(self.file), self.cache)
        self.assertIsNone(cached)
        self.assertNotEqual(changed, key)

    def test_key_is_sha256_of_path_mtime_size(self):
        key = self.cache.key("C:\\문서\\A.PNG", 1, 2)
        self.assertEqual(len(key), 64)
        self.assertNotEqual(key, self.cache.key("C:\\문서\\A.PNG", 1, 3))
        self.assertNotEqual(key, self.cache.key("C:\\문서\\A.PNG", 2, 2))
        self.assertNotEqual(key, self.cache.key("C:\\문서\\B.PNG", 1, 2))

    def test_corrupt_cache_file_is_regenerated(self):
        _, key = thumbs.lookup(str(self.file), self.cache)
        target = self.folder / "cache" / f"{key}.jpg"
        target.parent.mkdir()
        target.write_bytes(b"garbage")
        self.assertEqual(thumbs.lookup(str(self.file), self.cache), (None, key))

    def test_generate_returns_data_when_cache_write_fails(self):
        _, key = thumbs.lookup(str(self.file), self.cache)
        with patch.object(self.cache, "put", side_effect=OSError("디스크 가득")):
            self.assertThumbnail(thumbs.generate(str(self.file), key, self.cache))


class PruneTests(ThumbsTestCase):
    def test_removes_oldest_first_over_limit(self):
        cache = thumbs.ThumbnailCache(self.folder / "c", max_bytes=2500)
        now = time.time()
        for index in range(3):
            key = f"{index:064d}"
            cache.put(key, b"\xff\xd8\xff" + b"x" * 997)
            os.utime(self.folder / "c" / f"{key}.jpg", (now - 100 + index, now - 100 + index))
        cache.put("3" * 64, b"\xff\xd8\xff" + b"x" * 997)
        names = {item.name for item in (self.folder / "c").iterdir()}
        self.assertNotIn(f"{0:064d}.jpg", names)
        self.assertIn("3" * 64 + ".jpg", names)
        self.assertEqual(len(names), 2)
        self.assertLessEqual(sum(item.stat().st_size for item in (self.folder / "c").iterdir()), 2500)

    def test_recently_viewed_survives_prune(self):
        cache = thumbs.ThumbnailCache(self.folder / "c", max_bytes=2500)
        now = time.time()
        for index in range(2):
            key = f"{index:064d}"
            cache.put(key, b"\xff\xd8\xff" + b"x" * 997)
            os.utime(self.folder / "c" / f"{key}.jpg", (now - 100 + index, now - 100 + index))
        self.assertIsNotNone(cache.get(f"{0:064d}"))  # 오래된 항목을 다시 본다
        cache.put("2" * 64, b"\xff\xd8\xff" + b"x" * 997)
        names = {item.name for item in (self.folder / "c").iterdir()}
        self.assertIn(f"{0:064d}.jpg", names)
        self.assertNotIn(f"{1:064d}.jpg", names)

    def test_existing_cache_counted_on_first_write(self):
        folder = self.folder / "c"
        folder.mkdir()
        for index in range(3):
            (folder / f"{index:064d}.jpg").write_bytes(b"x" * 1000)
        cache = thumbs.ThumbnailCache(folder, max_bytes=2500)
        cache.put("9" * 64, b"x" * 1000)
        self.assertLessEqual(sum(item.stat().st_size for item in folder.iterdir()), 2500)

    def test_stale_temp_removed_recent_temp_kept(self):
        folder = self.folder / "c"
        folder.mkdir()
        stale, recent = folder / "thumb-old.tmp", folder / "thumb-new.tmp"
        stale.write_bytes(b"x")
        recent.write_bytes(b"x")
        old = time.time() - thumbs.STALE_TEMP_SECONDS - 10
        os.utime(stale, (old, old))
        thumbs.ThumbnailCache(folder).put("1" * 64, b"x")
        self.assertFalse(stale.exists())
        self.assertTrue(recent.exists())


class GuardTests(unittest.TestCase):
    def test_exclusive_proceeds_after_timeout_and_releases(self):
        held, release, ran = threading.Event(), threading.Event(), []
        def holder():
            with pdfium_guard.exclusive():
                held.set()
                release.wait(5)
        worker = threading.Thread(target=holder)
        worker.start()
        held.wait(2)
        with pdfium_guard.exclusive(timeout=0.01):
            ran.append(True)
        release.set()
        worker.join()
        self.assertEqual(ran, [True])
        with pdfium_guard.try_exclusive(0.01) as acquired:
            self.assertTrue(acquired)

    def test_exclusive_as_decorator_can_be_called_repeatedly(self):
        @pdfium_guard.exclusive()
        def work():
            return 1
        self.assertEqual(work() + work(), 2)


if __name__ == "__main__":
    unittest.main()
