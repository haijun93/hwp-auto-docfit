"""타임머신 썸네일: 형식별로 160px JPEG(품질 70)를 만들고 디스크에 캐시한다.

신뢰할 수 없는 파일을 읽으므로 크기 한도를 두고, 실패하면 예외 대신 None을 돌려준다(화면은 종류 아이콘).
클라우드 전용 파일은 읽는 순간 내려받기가 시작되므로 내용을 열지 않는다.
"""
from __future__ import annotations

import hashlib
import io
import logging
import math
import os
import stat
import tempfile
import threading
import time
import zipfile

from .. import pdfium_guard
from .rules import cloud_only
from .store import path_key

SIZE = 160
QUALITY = 70
MAX_CACHE_BYTES = 200 * 1024 * 1024
MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_PIXELS = 64_000_000
MAX_ARCHIVE_BYTES = 80 * 1024 * 1024  # table_catalog._safe_archive와 같은 한도
MAX_ARCHIVE_ENTRIES = 2000
MAX_MEMBER_BYTES = 16 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
PDF_LOCK_WAIT = 1.0
STALE_TEMP_SECONDS = 3600

_IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".gif": "GIF", ".bmp": "BMP",
                  ".tif": "TIFF", ".tiff": "TIFF", ".webp": "WEBP"}
_OFFICE = frozenset((".docx", ".xlsx", ".xlsm", ".pptx"))
_EMBEDDED_FORMATS = ["PNG", "JPEG", "BMP", "GIF"]


class ThumbnailBusy(Exception):
    """PDFium을 다른 기능이 쓰는 중. 파일 문제가 아니므로 나중에 다시 시도할 수 있다."""


def _encode(image):
    from PIL import Image

    image.thumbnail((SIZE, SIZE), Image.Resampling.BILINEAR, reducing_gap=2.0)
    if image.mode in ("RGBA", "LA", "PA") or (image.mode == "P" and "transparency" in image.info):
        image = image.convert("RGBA")
        flat = Image.new("RGB", image.size, "white")
        flat.paste(image, mask=image.getchannel("A"))
        image = flat
    elif image.mode != "RGB":
        image = image.convert("RGB")
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=QUALITY)
    return output.getvalue()


def _decode(source, formats):
    from PIL import Image, ImageOps

    with Image.open(source, formats=formats) as image:
        image.draft("RGB", (SIZE * 2, SIZE * 2))  # JPEG는 축소 디코딩, 다른 형식은 아무 일도 하지 않는다
        width, height = image.size
        if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
            return None
        return _encode(ImageOps.exif_transpose(image))


def _from_image(path):
    return _decode(path, [_IMAGE_FORMATS[os.path.splitext(path)[1].lower()]])


def _from_archive(path, member, *, check_manifest=False):
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if (len(infos) > MAX_ARCHIVE_ENTRIES or
                sum(item.file_size for item in infos) > MAX_ARCHIVE_BYTES):
            return None
        by_name = {item.filename: item for item in infos}
        info = by_name.get(member)
        if info is None or info.flag_bits & 1 or info.file_size > MAX_MEMBER_BYTES:
            return None
        if check_manifest:
            # 암호 건 HWPX는 매니페스트에 암호화 정보가 있다. 첫 쪽 그림이 비밀번호 없이 보이면 안 된다.
            manifest = by_name.get("META-INF/manifest.xml")
            if manifest is not None:
                if manifest.flag_bits & 1 or manifest.file_size > MAX_MANIFEST_BYTES:
                    return None
                with archive.open(manifest) as stream:
                    if b"encryption-data" in stream.read(MAX_MANIFEST_BYTES + 1):
                        return None
        with archive.open(info) as stream:
            data = stream.read(MAX_MEMBER_BYTES + 1)
    if len(data) > MAX_MEMBER_BYTES:
        return None
    return _decode(io.BytesIO(data), _EMBEDDED_FORMATS)


def _from_pdf(path):
    import pypdfium2 as pdfium

    with pdfium_guard.try_exclusive(PDF_LOCK_WAIT) as acquired:
        if not acquired:
            raise ThumbnailBusy()
        document = pdfium.PdfDocument(path)
        try:
            if len(document) < 1:
                return None
            page = document[0]
            try:
                width, height = page.get_size()
                if not (math.isfinite(width) and math.isfinite(height)) or min(width, height) <= 0:
                    return None
                bitmap = page.render(scale=SIZE / max(width, height), may_draw_forms=False)
                try:
                    image = bitmap.to_pil().copy()
                finally:
                    bitmap.close()
            finally:
                page.close()
        finally:
            document.close()
    return _encode(image)


def render(path):
    """파일 내용에서 썸네일 JPEG를 만든다. 지원하지 않거나 읽지 못하면 None."""
    extension = os.path.splitext(path)[1].lower()
    try:
        if extension == ".hwpx":
            return _from_archive(path, "Preview/PrvImage.png", check_manifest=True)
        if extension in _OFFICE:
            return _from_archive(path, "docProps/thumbnail.jpeg")
        if extension == ".pdf":
            return _from_pdf(path)
        if extension in _IMAGE_FORMATS:
            return _from_image(path)
    except ThumbnailBusy:
        raise
    except Exception as exc:  # 손상·암호·악성 파일: 원인과 상관없이 아이콘으로 대체한다
        logging.getLogger(__name__).debug("썸네일 생성 실패: %s", type(exc).__name__)
    return None


class ThumbnailCache:
    """`sha256(경로|수정시각|크기).jpg` 캐시. 총량이 한도를 넘으면 오래 안 쓴 것부터 지운다."""

    def __init__(self, folder, max_bytes=MAX_CACHE_BYTES):
        self.folder = os.fspath(folder)
        self.max_bytes = max_bytes
        self._lock = threading.Lock()
        self._total = None

    @staticmethod
    def key(path, mtime_ns, size):
        return hashlib.sha256(f"{path_key(path)}|{mtime_ns}|{size}".encode("utf-8")).hexdigest()

    def _file(self, key):
        return os.path.join(self.folder, key + ".jpg")

    def get(self, key):
        target = self._file(key)
        try:
            with open(target, "rb") as stream:
                data = stream.read(MAX_MEMBER_BYTES + 1)
            if not data.startswith(b"\xff\xd8\xff") or len(data) > MAX_MEMBER_BYTES:
                return None
            os.utime(target)  # 정리할 때 오래 안 본 것부터 지우도록 사용 시각을 남긴다
            return data
        except OSError:
            return None

    def put(self, key, data):
        os.makedirs(self.folder, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix="thumb-", suffix=".tmp", dir=self.folder)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
            os.replace(temporary, self._file(key))
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        with self._lock:
            if self._total is None or self._total + len(data) > self.max_bytes:
                self._prune()
            else:
                self._total += len(data)

    def _prune(self):
        entries, total = [], 0
        now = time.time()
        with os.scandir(self.folder) as iterator:
            for item in iterator:
                try:
                    info = item.stat(follow_symlinks=False)
                    if not item.is_file(follow_symlinks=False):
                        continue
                    if not item.name.endswith(".jpg"):
                        if item.name.endswith(".tmp") and now - info.st_mtime > STALE_TEMP_SECONDS:
                            os.unlink(item.path)
                        continue
                except OSError:
                    continue
                entries.append((info.st_mtime_ns, item.path, info.st_size))
                total += info.st_size
        entries.sort()
        for _, target, size in entries:
            if total <= self.max_bytes:
                break
            try:
                os.unlink(target)
                total -= size
            except OSError:
                continue
        self._total = total


def lookup(path, cache, *, cloud=False):
    """(캐시된 JPEG, 캐시 키). 만들 수 없는 파일이면 키가 None이다. 내용은 읽지 않는다."""
    if cloud:
        return None, None
    try:
        info = os.lstat(path)
    except OSError:
        return None, None
    if (not stat.S_ISREG(info.st_mode) or cloud_only(getattr(info, "st_file_attributes", 0)) or
            not 0 < info.st_size <= MAX_FILE_BYTES):
        return None, None
    key = cache.key(path, info.st_mtime_ns, info.st_size)
    return cache.get(key), key


def generate(path, key, cache):
    """만들어 캐시에 넣는다. 캐시 쓰기 실패는 화면 표시를 막지 않는다."""
    data = render(path)
    if data is not None:
        try:
            cache.put(key, data)
        except OSError as exc:
            logging.getLogger(__name__).debug("썸네일 캐시 저장 실패: %s", type(exc).__name__)
    return data
