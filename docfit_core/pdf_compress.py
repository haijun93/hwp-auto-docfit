"""PDF 용량 줄이기(파일 변환 'PDF 압축').

재조판 없이 PDF 안의 내용 스트림과 그림만 다시 저장한다. 글자층·쪽 수·쪽 크기는 그대로 두고,
보안(권한 제한) PDF는 원본과 같은 권한값으로 다시 잠가 보호가 풀린 사본을 만들지 않는다.
설계: docs/PDF_COMPRESSION_DESIGN.md
"""

from __future__ import annotations

import io
import os
import secrets
import tempfile
from dataclasses import dataclass
from pathlib import Path

# 강도: (목표 dpi, JPEG 품질). 기본은 '보통'.
LEVELS = {"lossless": None, "normal": (150, 75), "strong": (100, 60)}
DEFAULT_LEVEL = "normal"
MAX_BYTES = 1024 ** 3
MAX_PAGES = 3000
MIN_IMAGE_SIDE = 200
MIN_SAVING = 0.05          # 5% 미만으로 줄면 결과를 만들지 않는다.
_SKIP_MODES = {"1", "P", "PA", "LA", "RGBA", "CMYK", "I", "I;16", "F"}


class PdfCompressError(ValueError):
    """사용자에게 그대로 보여 줄 수 있는 처리 거부·실패."""


class NothingToCompress(PdfCompressError):
    """이미 충분히 작아 결과 파일을 만들지 않음."""


@dataclass(frozen=True)
class CompressResult:
    target: Path
    before: int
    after: int
    secured: bool
    images: int

    @property
    def saving(self) -> float:
        return 1 - self.after / self.before if self.before else 0.0

    def summary(self) -> str:
        text = f"{_size(self.before)} → {_size(self.after)} (−{self.saving * 100:.0f}%)"
        return text + (" · 보안 유지" if self.secured else "")


def _size(value: int) -> str:
    return f"{value / 1024 / 1024:.1f}MB" if value >= 1024 * 1024 else f"{max(1, round(value / 1024))}KB"


def _has_signature(reader) -> bool:
    try:
        fields = reader.get_fields() or {}
    except Exception:
        return False
    return any(str((field or {}).get("/FT")) == "/Sig" for field in fields.values())


def _page_signature(reader):
    return [(round(float(p.mediabox.width), 1), round(float(p.mediabox.height), 1), int(p.get("/Rotate", 0) or 0))
            for p in reader.pages]


def _page_texts(path: Path) -> list[str]:
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(str(path))
    try:
        texts = []
        for index in range(len(document)):
            page = document[index]
            try:
                textpage = page.get_textpage()
                try:
                    texts.append(textpage.get_text_range())
                finally:
                    textpage.close()
            finally:
                page.close()
        return texts
    finally:
        document.close()


def _recompress_images(page, dpi: int, quality: int) -> int:
    from PIL import Image

    limit = (max(1, int(float(page.mediabox.width) / 72 * dpi)),
             max(1, int(float(page.mediabox.height) / 72 * dpi)))
    changed = 0
    for image in page.images:
        try:
            stream = image.indirect_reference.get_object() if image.indirect_reference else None
            if stream is None or "/SMask" in stream or "/Mask" in stream:
                continue        # 투명 마스크가 있는 그림은 그대로 둔다.
            pil = image.image
            if pil is None or pil.mode in _SKIP_MODES or min(pil.size) < MIN_IMAGE_SIDE:
                continue        # 흑백 1비트·색인·CMYK·투명·작은 그림은 그대로 둔다.
            if pil.width > limit[0] or pil.height > limit[1]:
                pil = pil.copy()
                pil.thumbnail(limit, Image.LANCZOS)
            if pil.mode != "RGB" and pil.mode != "L":
                pil = pil.convert("RGB")
            buffer = io.BytesIO()
            pil.save(buffer, "JPEG", quality=quality, optimize=True)
            if buffer.tell() >= len(stream._data or b"") * 0.9:
                continue        # 10% 이상 작아지지 않으면 원래 그림을 둔다.
            image.replace(pil, quality=quality)
            changed += 1
        except Exception:
            continue            # 읽지 못하는 그림 형식은 건드리지 않는다.
    return changed


def compress_pdf(source: str | Path, target: str | Path, *, level: str = DEFAULT_LEVEL) -> CompressResult:
    """PDF를 줄여 target에 새로 저장한다. 원본은 읽기만 하고 target은 덮어쓰지 않는다."""
    from pypdf import PdfReader, PdfWriter

    source, target = Path(source), Path(target)
    if level not in LEVELS:
        raise PdfCompressError("지원하지 않는 압축 강도입니다.")
    if source.is_symlink() or not source.is_file() or source.suffix.lower() != ".pdf":
        raise PdfCompressError("PDF 압축은 일반 PDF 파일에만 쓸 수 있습니다.")
    if target.suffix.lower() != ".pdf" or target.exists():
        raise PdfCompressError("PDF 압축 결과 경로가 잘못되었거나 이미 있습니다.")
    before = source.stat().st_size
    if before > MAX_BYTES:
        raise PdfCompressError("1GB보다 큰 PDF는 줄이지 않습니다.")
    with source.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise PdfCompressError("올바른 PDF가 아닙니다(문서보안 프로그램으로 보호된 파일일 수 있습니다).")

    try:
        reader = PdfReader(str(source))
        secured = bool(reader.is_encrypted)
        if secured and not reader.decrypt(""):
            raise PdfCompressError("열기 암호가 걸린 PDF는 아직 줄일 수 없습니다.")
        if len(reader.pages) > MAX_PAGES:
            raise PdfCompressError(f"{MAX_PAGES}쪽보다 많은 PDF는 줄이지 않습니다.")
        if _has_signature(reader):
            raise PdfCompressError("전자서명이 있는 PDF는 다시 저장하면 서명이 무효가 되어 줄이지 않습니다.")
        permissions = int(reader.trailer["/Encrypt"]["/P"]) if secured else None
        pages_before = _page_signature(reader)
        writer = PdfWriter(clone_from=reader)
        images = 0
        setting = LEVELS[level]
        for page in writer.pages:
            page.compress_content_streams(level=9)
            if setting:
                images += _recompress_images(page, *setting)
        writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
        if secured:
            # 원본과 같은 권한값으로 다시 잠근다. 원래 소유자 암호는 알 수 없으므로 새 무작위 값을 쓴다.
            writer.encrypt(user_password="", owner_password=secrets.token_urlsafe(24),
                           permissions_flag=permissions, algorithm="AES-256")
        buffer = io.BytesIO()
        writer.write(buffer)
    except PdfCompressError:
        raise
    except Exception as exc:
        raise PdfCompressError(f"PDF를 읽거나 다시 저장하지 못했습니다: {exc}") from exc

    after = buffer.tell()
    if after > before * (1 - MIN_SAVING):
        raise NothingToCompress(f"이미 충분히 작아 줄이지 않았습니다({_size(before)}).")

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="docfit_pdfz_", suffix=".pdf", dir=target.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(buffer.getvalue())
    try:
        check = PdfReader(str(temporary))
        if bool(check.is_encrypted) != secured:
            raise PdfCompressError("결과 PDF의 보안 설정이 원본과 달라 저장하지 않았습니다.")
        if secured:
            if not check.decrypt("") or int(check.trailer["/Encrypt"]["/P"]) != permissions:
                raise PdfCompressError("결과 PDF의 권한 설정이 원본과 달라 저장하지 않았습니다.")
        if _page_signature(check) != pages_before:
            raise PdfCompressError("결과 PDF의 쪽 수나 쪽 크기가 원본과 달라 저장하지 않았습니다.")
        if _page_texts(temporary) != _page_texts(source):
            raise PdfCompressError("결과 PDF의 글자가 원본과 달라 저장하지 않았습니다.")
        # hard link는 대상 이름이 작업 중 먼저 생긴 경우에도 덮어쓰지 않는다.
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return CompressResult(target, before, after, secured, images)
