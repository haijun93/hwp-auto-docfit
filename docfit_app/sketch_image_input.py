"""표그림판 칸 배경 그림 입력: 끌어 놓은 사진 파일·클립보드 사진을 알맞은 크기의 PNG/JPG로 바꾼다.

큰 사진은 긴 변 1600px로 줄이고, 투명한 부분이 있으면 PNG, 아니면 JPG(품질 88)로 저장한다.
결과는 base64 문자열이라 화면(Flutter)과 표 문서(HWPX BinData)가 그대로 쓴다.
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
MAX_SOURCE_BYTES = 40 * 1024 * 1024
MAX_SIDE = 1600
MAX_OUTPUT_BYTES = 8 * 1024 * 1024


def _encode(image):
    from PIL import Image

    image.load()
    if max(image.size) > MAX_SIDE:
        image.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    has_alpha = image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)
    out = io.BytesIO()
    if has_alpha:
        image.convert("RGBA").save(out, "PNG", optimize=True)
        kind = "png"
    else:
        image.convert("RGB").save(out, "JPEG", quality=88, optimize=True)
        kind = "jpg"
    data = out.getvalue()
    if len(data) > MAX_OUTPUT_BYTES:
        raise ValueError("그림이 너무 큽니다. 더 작은 그림을 써 주세요.")
    return dict(ok=True, data=base64.b64encode(data).decode("ascii"), kind=kind,
                width=image.size[0], height=image.size[1])


def from_path(path):
    from PIL import Image

    source = Path(str(path))
    if source.suffix.lower() not in IMAGE_SUFFIXES:
        raise ValueError("그림 파일(PNG·JPG·GIF·BMP·WEBP·TIFF)을 놓아 주세요.")
    if not source.is_file() or source.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("그림 파일을 읽지 못했거나 40MB보다 큽니다.")
    Image.MAX_IMAGE_PIXELS = 80_000_000  # 압축 폭탄 막기
    with Image.open(source) as image:
        image.seek(0)
        return _encode(image.copy())


def from_clipboard(grab=None):
    """클립보드의 사진(또는 복사한 그림 파일)을 읽는다."""
    if grab is None:
        from PIL import ImageGrab
        grab = ImageGrab.grabclipboard
    content = grab()
    if content is None:
        raise ValueError("클립보드에 사진이 없습니다. 사진을 복사한 뒤 다시 눌러 주세요.")
    if isinstance(content, list):
        for item in content:
            if Path(str(item)).suffix.lower() in IMAGE_SUFFIXES:
                return from_path(item)
        raise ValueError("클립보드에 그림 파일이 없습니다.")
    return _encode(content)
