"""HWPX 문서 추출기."""
from __future__ import annotations

import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from defusedxml import ElementTree as ET

from ..hwpx import HwpxSecurityError, open_hwpx_safely
from .extractors import ExtractionError, ExtractionRecord
from .extractors_ooxml import MAX_COMPRESSION_RATIO, MAX_ENTRIES, MAX_FILE_SIZE, MAX_TOTAL_SIZE


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _extract_paragraph_text(p_elem: ET.Element) -> str:
    """HWPX 문단 요소 내의 텍스트를 추출한다."""
    parts: list[str] = []

    def visit(node: ET.Element, root: bool = False) -> None:
        name = _local_name(node.tag)
        if not root and name in {"p", "tbl"}:
            return
        if name == "t" and node.text:
            parts.append(node.text)
        elif name in {"lineBreak", "br"}:
            parts.append("\n")
        elif name == "tab":
            parts.append("\t")
        elif name in {"fwSpace", "nbSpace"}:
            parts.append(" ")
        for child in node:
            visit(child)
            if name == "t" and child.tail:
                parts.append(child.tail)

    visit(p_elem, True)
    text = "".join(parts).strip()
    if not text:
        # hp:t 외에 일반 <p>text</p> 구조 대응
        text = "".join(p_elem.itertext()).strip()
    return text


def extract_hwpx(path: Path | str, hierarchy_records: list | None = None) -> list[ExtractionRecord]:
    """HWPX 문서에서 섹션 및 문단 위치를 포함한 추출 레코드를 생성한다."""
    file_path = Path(path)
    try:
        archive = open_hwpx_safely(file_path)
    except HwpxSecurityError as exc:
        msg = str(exc)
        if "암호" in msg or "password" in msg.lower() or "encrypted" in msg.lower():
            raise ExtractionError("encrypted", f"암호화된 HWPX 문서: {exc}") from exc
        raise ExtractionError("corrupt", f"손상되었거나 안전하지 않은 HWPX: {exc}") from exc
    except (BadZipFile, OSError) as exc:
        raise ExtractionError("corrupt", f"HWPX 압축 파일 열기 실패: {exc}") from exc

    with archive:
        namelist = archive.namelist()
        infos = archive.infolist()
        if len(infos) > MAX_ENTRIES:
            raise ExtractionError("corrupt", "HWPX 압축 항목 수 초과")
        total_size = 0
        normalized_names = set()
        for info in infos:
            name = info.filename.replace("\\", "/")
            from pathlib import PurePosixPath
            member = PurePosixPath(name)
            if member.is_absolute() or ".." in member.parts or re.match(r"^[A-Za-z]:", name):
                raise ExtractionError("corrupt", f"안전하지 않은 HWPX 압축 경로: {info.filename}")
            if name in normalized_names:
                raise ExtractionError("corrupt", f"중복된 HWPX 압축 항목: {name}")
            normalized_names.add(name)
            if info.file_size > MAX_FILE_SIZE:
                raise ExtractionError("corrupt", f"HWPX 단일 항목 크기 초과: {name}")
            total_size += info.file_size
            if total_size > MAX_TOTAL_SIZE or (info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO):
                raise ExtractionError("corrupt", f"HWPX 압축 크기 제한 초과: {name}")
        for info in archive.infolist():
            if info.flag_bits & 0x1:
                raise ExtractionError("encrypted", "암호화된 HWPX 항목이 포함되어 있음")

        if any("encrypt" in name.lower() for name in namelist):
            raise ExtractionError("encrypted", "암호화된 HWPX 메타데이터가 발견됨")

        section_names = [
            n for n in namelist
            if re.match(r"^Contents/section\d+\.xml$", n, re.IGNORECASE)
            or (n.startswith("Contents/section") and n.endswith(".xml"))
        ]
        if not section_names:
            raise ExtractionError("corrupt", "HWPX 본문 섹션(Contents/section*.xml)을 찾지 못함")

        def _sort_key(name: str) -> int:
            m = re.search(r"\d+", name)
            return int(m.group()) if m else 0

        section_names.sort(key=_sort_key)

        records: list[ExtractionRecord] = []
        seq = 1

        hierarchy_index = 0
        for s_name in section_names:
            section_stem = Path(s_name).stem
            try:
                root = ET.fromstring(archive.read(s_name))
            except Exception as exc:
                raise ExtractionError("corrupt", f"HWPX 섹션 XML 파싱 실패 ({s_name}): {exc}") from exc

            p_idx = 1
            def walk(node, in_table=False):
                nonlocal p_idx, seq, hierarchy_index
                tag = _local_name(node.tag)
                if tag in {"tc", "cell"}:
                    for child in node:
                        walk(child, True)
                    return
                if tag == "p":
                    in_cell = in_table
                    if in_cell:
                        return
                    hierarchy = hierarchy_records[hierarchy_index] if hierarchy_records and hierarchy_index < len(hierarchy_records) else None
                    if hierarchy is not None:
                        p_text = hierarchy.text.strip()
                    else:
                        p_text = _extract_paragraph_text(node)
                    if p_text:
                        records.append(ExtractionRecord(
                            text=p_text, location_kind="paragraph",
                            location_label=f"{section_stem} 문단 {p_idx}", sequence=seq,
                            section=section_stem,
                            hierarchy_level=hierarchy.level if hierarchy else None,
                            is_table_cell=bool(hierarchy and hierarchy.is_table_cell),
                            style_name=hierarchy.style_name if hierarchy else None,
                            outline_level=hierarchy.outline_level if hierarchy else None,
                        ))
                        p_idx += 1
                        seq += 1
                    if p_text:
                        hierarchy_index += 1
                    for child in node:
                        walk(child, in_table)
                    return
                for child in node:
                    walk(child, in_table)

            walk(root)

    if not records:
        raise ExtractionError("empty", "본문 문단 텍스트가 없음")

    return records

