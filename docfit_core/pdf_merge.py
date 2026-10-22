"""여러 PDF·그림 파일을 PDF 하나로 합치기.

파일포맷 변경의 'PDF로 일괄 변환(합치기)' 옵션에서 사용되는 핵심 모듈이다.
PDF는 pypdf로 읽어 쪽을 합치고, 그림(PNG, JPEG, GIF, TIFF 등)은 Pillow로
150dpi PDF로 변환해 붙인다. 각 원본의 첫 쪽에 원본 표시 이름을 책갈피(outline)로 달며,
암호·보안이 걸린 PDF는 합치지 않고 거부한다.
"""

from __future__ import annotations

import io
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
MAX_IMAGE_BYTES = 200 * 1024 * 1024   # 그림 1개 크기 상한 200MB
MAX_PIXELS = 200_000_000               # 그림 픽셀 수 상한 2억
MAX_TOTAL_PAGES = 3000                 # 전체 쪽 수 상한 3000쪽


class PdfMergeError(ValueError):
    """사용자에게 그대로 보일 수 있는 거부·실패."""


@dataclass(frozen=True)
class MergeResult:
    target: Path
    files: int
    pages: int

    def summary(self) -> str:
        return f"파일 {self.files}개 → {self.pages}쪽"


def merged_output_path(sources: list[Path]) -> Path:
    """합친 PDF가 저장될 경로를 결정한다.

    첫 파일과 같은 폴더에 저장하며, 파일이 1개면 '<이름>(합친 PDF).pdf',
    여러 개면 '<첫 파일 이름(확장자 제외)> 외 N개(합친 PDF).pdf' 형태로 이름을 짓는다.
    이미 같은 이름의 파일이 있으면 '... (2).pdf', '(3)' 처럼 겹치지 않게 번호를 붙이며,
    원본 파일은 절대 덮어쓰지 않는다.
    """
    if not sources:
        raise PdfMergeError("합칠 파일 목록이 비어 있습니다.")

    sources = [Path(p) for p in sources]
    first = sources[0]
    folder = first.parent
    first_stem = first.stem

    others = len(sources) - 1
    if others == 0:
        base_name = f"{first_stem}(합친 PDF)"
    else:
        base_name = f"{first_stem} 외 {others}개(합친 PDF)"

    candidate = folder / f"{base_name}.pdf"
    if not candidate.exists() and candidate not in sources:
        return candidate

    index = 2
    while True:
        candidate = folder / f"{base_name} ({index}).pdf"
        if not candidate.exists() and candidate not in sources:
            return candidate
        index += 1


def _to_rgb_white_bg(frame) -> "Image.Image":
    """임의의 모드(RGBA, P, LA 등)를 흰 바탕 위에 합성해 RGB 모드로 변환한다."""
    from PIL import Image

    if frame.mode == "RGB":
        return frame.copy()
    rgba = frame.convert("RGBA")
    background = Image.new("RGB", rgba.size, (255, 255, 255))
    background.paste(rgba, mask=rgba.split()[3])
    return background


def image_to_pdf_bytes(path: str | Path) -> bytes:
    """Pillow로 그림 한 장(또는 여러 프레임)을 PDF 바이트로 변환한다.

    여러 프레임(GIF, TIFF 등)은 모든 프레임을 각각 한 쪽으로 만들고,
    RGBA·P·LA 등 투명/특수 모드는 흰 바탕에 합성하여 RGB로 변환한다.
    쪽 크기는 그림 크기를 150dpi로 본 크기(resolution=150)로 설정한다.
    그림 크기 200MB, 픽셀 수 2억 초과 시 PdfMergeError를 일으킨다.
    """
    from PIL import Image

    # Pillow의 전역 픽셀 상한은 이 변환 동안에만 바꾸고 되돌린다(앱의 다른 그림 처리 방어값 유지).
    previous = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        return _image_to_pdf_bytes(Path(path))
    finally:
        Image.MAX_IMAGE_PIXELS = previous


def _image_to_pdf_bytes(path: Path) -> bytes:
    from PIL import Image, ImageSequence

    path = Path(path)
    if not path.is_file():
        raise PdfMergeError(f"{path.name}: 파일이 없거나 올바른 파일이 아닙니다.")

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise PdfMergeError(f"{path.name}: 파일 정보를 읽지 못했습니다: {exc}") from exc

    if size > MAX_IMAGE_BYTES:
        raise PdfMergeError(f"{path.name}: 그림 파일 크기가 200MB를 넘습니다({size / 1024 / 1024:.1f}MB).")

    try:
        with Image.open(path) as img:
            pages = []
            for frame in ImageSequence.Iterator(img):
                pixels = frame.width * frame.height
                if pixels > MAX_PIXELS:
                    raise PdfMergeError(f"{path.name}: 그림 픽셀 수가 2억을 넘습니다({pixels:,}px).")
                pages.append(_to_rgb_white_bg(frame))

            if not pages:
                raise PdfMergeError(f"{path.name}: 변환할 그림 프레임이 없습니다.")

            buffer = io.BytesIO()
            if len(pages) == 1:
                pages[0].save(buffer, format="PDF", resolution=150.0)
            else:
                pages[0].save(buffer, format="PDF", resolution=150.0, save_all=True, append_images=pages[1:])
            return buffer.getvalue()
    except PdfMergeError:
        raise
    except Exception as exc:
        raise PdfMergeError(f"{path.name}: 그림을 읽거나 PDF로 변환하지 못했습니다: {exc}") from exc


def merge_to_pdf(parts: list[tuple[str, Path]], target: Path) -> MergeResult:
    """여러 PDF·그림 파일을 하나의 PDF로 합쳐 target에 저장한다.

    parts: (원본 표시 이름, PDF 또는 그림 경로) 목록 (순서 = 결과 쪽 순서).
    target: 최종 저장 경로 (이미 존재하면 덮어쓰지 않고 PdfMergeError).
    """
    from pypdf import PdfReader, PdfWriter

    if not parts:
        raise PdfMergeError("합칠 파일 목록이 비어 있습니다.")

    target = Path(target)
    if target.exists():
        raise PdfMergeError(f"대상 파일이 이미 있습니다: {target.name}")

    target.parent.mkdir(parents=True, exist_ok=True)

    writer = PdfWriter()
    readers = []
    streams = []
    total_pages = 0

    temporary: Path | None = None

    try:
        for name, file_path in parts:
            p = Path(file_path)
            if not p.is_file():
                raise PdfMergeError(f"{name}: 파일이 없거나 읽을 수 없습니다({p.name}).")

            suffix = p.suffix.lower()
            if suffix in IMAGE_EXTENSIONS:
                pdf_bytes = image_to_pdf_bytes(p)
                stream = io.BytesIO(pdf_bytes)
                streams.append(stream)
                try:
                    reader = PdfReader(stream)
                except Exception as exc:
                    raise PdfMergeError(f"{name}: 변환한 그림 PDF를 읽지 못했습니다: {exc}") from exc
            elif suffix == ".pdf":
                try:
                    with p.open("rb") as f:
                        if f.read(5) != b"%PDF-":
                            raise PdfMergeError(f"{name}: 올바른 PDF가 아닙니다(문서보안 프로그램으로 보호된 파일일 수 있습니다).")
                    reader = PdfReader(str(p))
                except PdfMergeError:
                    raise
                except Exception as exc:
                    raise PdfMergeError(f"{name}: PDF를 읽지 못했습니다: {exc}") from exc
            else:
                raise PdfMergeError(f"{name}: 지원하지 않는 파일 형식입니다({p.suffix}).")

            readers.append(reader)

            if reader.is_encrypted:
                raise PdfMergeError(f"{name}: 암호·보안이 걸린 PDF는 합칠 수 없습니다(보호가 풀린 사본을 만들지 않기 위해).")

            page_count = len(reader.pages)
            if page_count == 0:
                raise PdfMergeError(f"{name}: 쪽 수가 0인 PDF입니다.")

            if total_pages + page_count > MAX_TOTAL_PAGES:
                raise PdfMergeError(f"합친 전체 쪽 수가 상한({MAX_TOTAL_PAGES}쪽)을 넘습니다.")

            first_page_index = len(writer.pages)
            for page in reader.pages:
                writer.add_page(page)

            writer.add_outline_item(title=name, page_number=first_page_index)
            total_pages += page_count

        with tempfile.NamedTemporaryFile(prefix="docfit_merge_", suffix=".tmp", dir=target.parent, delete=False) as temp_file:
            temporary = Path(temp_file.name)
            writer.write(temp_file)

        check = PdfReader(str(temporary))
        if len(check.pages) != total_pages:
            raise PdfMergeError("합친 PDF의 쪽 수가 일치하지 않아 저장하지 않았습니다.")

        if target.exists():
            raise PdfMergeError(f"대상 파일이 이미 있습니다: {target.name}")

        os.replace(temporary, target)
        temporary = None
    except PdfMergeError:
        raise
    except Exception as exc:
        raise PdfMergeError(f"PDF를 합치거나 저장하지 못했습니다: {exc}") from exc
    finally:
        for s in streams:
            try:
                s.close()
            except Exception:
                pass
        if temporary is not None and temporary.exists():
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    return MergeResult(target=target, files=len(parts), pages=total_pages)
