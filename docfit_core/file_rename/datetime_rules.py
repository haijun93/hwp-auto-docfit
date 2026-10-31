"""날짜·시각 삽입: 수정/생성/오늘/EXIF 촬영일과 공문서식 형식 문자열."""
from __future__ import annotations

import re
from datetime import datetime

EXIF_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".heic", ".webp", ".png"}
_TOKENS = re.compile(r"YYYY|YY|MM|DD|hh|mm|ss")
_EXIF_DATETIME_ORIGINAL = 0x9003
_EXIF_DATETIME = 0x0132
_EXIF_IFD = 0x8769


def format_datetime(moment, pattern):
    """YYYY·YY·MM·DD·hh·mm·ss 토큰만 바꾸고 나머지 글자(., _, -, 공백)는 그대로 둔다."""
    values = {"YYYY": f"{moment.year:04d}", "YY": f"{moment.year % 100:02d}", "MM": f"{moment.month:02d}",
              "DD": f"{moment.day:02d}", "hh": f"{moment.hour:02d}", "mm": f"{moment.minute:02d}",
              "ss": f"{moment.second:02d}"}
    return _TOKENS.sub(lambda match: values[match.group(0)], pattern)


def read_exif_datetime(path):
    """사진의 촬영 시각(DateTimeOriginal, 없으면 DateTime). 읽을 수 없으면 None."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            raw = exif.get_ifd(_EXIF_IFD).get(_EXIF_DATETIME_ORIGINAL) or exif.get(_EXIF_DATETIME)
    except Exception:
        return None
    if not isinstance(raw, str):
        return None
    try:
        return datetime.strptime(raw.strip("\x00 ")[:19], "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def entry_datetime(entry, source, *, today=None, exif_reader=read_exif_datetime):
    """(시각, 대체 여부). EXIF가 없으면 수정 시각으로 대체하고 대체 여부를 True로 알린다."""
    if source == "today":
        return today or datetime.now(), False
    if source == "ctime":
        return datetime.fromtimestamp(entry.ctime), False
    if source == "exif":
        moment = exif_reader(entry.path) if entry.ext.lower() in EXIF_EXTENSIONS else None
        if moment is not None:
            return moment, False
    return datetime.fromtimestamp(entry.mtime), source == "exif"
