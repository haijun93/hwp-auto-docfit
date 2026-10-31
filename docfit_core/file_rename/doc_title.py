"""HWPX 안의 첫 제목 문단을 안전하게 읽는다. 문서는 읽기만 한다."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

_HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
_MAX_ARCHIVE_BYTES = 80 * 1024 * 1024
_MAX_ENTRIES = 2000
_MAX_ENTRY_BYTES = 20 * 1024 * 1024
_FORBIDDEN = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def _safe_archive(path):
    archive = zipfile.ZipFile(path)
    infos = archive.infolist()
    if (len(infos) > _MAX_ENTRIES or sum(i.file_size for i in infos) > _MAX_ARCHIVE_BYTES
            or any(i.file_size > _MAX_ENTRY_BYTES for i in infos)):
        archive.close()
        raise ValueError("HWPX 압축 파일 크기가 허용 범위를 넘습니다.")
    return archive


def _section_names(archive):
    return sorted((name for name in archive.namelist() if re.fullmatch(r"Contents/section\d+\.xml", name)),
                  key=lambda name: int(re.search(r"section(\d+)", name).group(1)))


def _tag(element):
    return element.tag.rsplit("}", 1)[-1]


def _text(element):
    return "".join(node.text or "" for node in element.iter(_HP + "t")).strip()


def _cell_a1_text(table):
    rows = [node for node in table.iter() if _tag(node) == "tr"]
    if not rows:
        return ""
    cells = [node for node in rows[0] if _tag(node) == "tc"]
    return _text(cells[0]) if cells else ""


def _paragraph_text(paragraph):
    tables = [node for node in paragraph.iter() if _tag(node) == "tbl"]
    for table in tables:
        title = _cell_a1_text(table)
        if title:
            return title
    return _text(paragraph)


def read_document_title(path):
    """섹션 0의 첫 제목 표 A1 또는 첫 비어 있지 않은 문단을 돌려준다."""
    with _safe_archive(Path(path)) as archive:
        sections = _section_names(archive)
        if not sections:
            raise ValueError("HWPX 섹션을 찾지 못했습니다.")
        root = ET.fromstring(archive.read(sections[0]))
        for paragraph in (node for node in root.iter() if _tag(node) == "p"):
            title = _paragraph_text(paragraph)
            if title:
                return title
    return ""


def sanitize_title(title, max_length=60):
    """파일 이름에 쓸 수 없는 문자를 밑줄로 바꾸고 길이를 제한한다."""
    title = _FORBIDDEN.sub("_", title or "")
    title = re.sub(r"[. ]+$", "", title).strip()
    return title[:max_length].rstrip(". ")
