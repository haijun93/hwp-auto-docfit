"""표 서식 모음 HWPX에서 이름별 표 템플릿을 안전하게 읽고 개별 문서로 내보낸다."""

from __future__ import annotations

import copy
import re
import sys
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

_HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
_DEFAULT_NAME = "표 서식모음.hwpx"
_MAX_ARCHIVE_BYTES = 80 * 1024 * 1024
_MAX_ENTRIES = 2000


def default_catalog_path() -> Path:
    """개발·PyInstaller 양쪽에서 같은 내장 표 서식 모음을 찾는다."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return root / "resources" / "서식예시" / _DEFAULT_NAME


def _safe_archive(path: Path) -> zipfile.ZipFile:
    archive = zipfile.ZipFile(path)
    infos = archive.infolist()
    if len(infos) > _MAX_ENTRIES or sum(item.file_size for item in infos) > _MAX_ARCHIVE_BYTES:
        archive.close()
        raise ValueError("표 서식 파일 크기 또는 항목 수가 허용 범위를 넘습니다.")
    if any(item.file_size > _MAX_ARCHIVE_BYTES for item in infos):
        archive.close()
        raise ValueError("표 서식 파일 안의 개별 항목이 너무 큽니다.")
    return archive


def _section_names(archive: zipfile.ZipFile) -> list[str]:
    return sorted(
        (name for name in archive.namelist()
         if re.fullmatch(r"Contents/section\d+\.xml", name)),
        key=lambda name: int(re.search(r"section(\d+)", name).group(1)),
    )


def _text(element) -> str:
    return "".join(node.text or "" for node in element.iter(_HP + "t")).strip()


def _top_tables(paragraph):
    found = []

    def walk(element, inside_table=False):
        for child in list(element):
            is_table = child.tag == _HP + "tbl"
            if is_table and not inside_table:
                found.append(child)
            walk(child, inside_table or is_table)

    walk(paragraph)
    return found


def _table_preview(table) -> dict:
    rows = []
    for row in table.findall(_HP + "tr")[:12]:
        cells = []
        for cell in row.findall(_HP + "tc")[:12]:
            # Avoid text from a nested table leaking into the containing cell's label.
            parts = []
            for node in cell.iter(_HP + "t"):
                parent_text = node.text or ""
                if parent_text:
                    parts.append(parent_text)
            cells.append(" ".join("".join(parts).split())[:80])
        rows.append(cells)
    return {
        "rows": int(table.get("rowCnt", len(rows)) or len(rows)),
        "cols": int(table.get("colCnt", max((len(row) for row in rows), default=0)) or 0),
        "cells": rows,
    }


def _scan(path: str | Path) -> list[dict]:
    source = Path(path)
    if not source.is_file() or source.suffix.lower() != ".hwpx":
        raise ValueError("표 서식 모음 HWPX 파일을 찾을 수 없습니다.")
    records = []
    category_index = -1
    current_category = None
    with _safe_archive(source) as archive:
        sections = _section_names(archive)
        if not sections:
            raise ValueError("HWPX에 본문 구역이 없습니다.")
        for section_name in sections:
            root = ET.fromstring(archive.read(section_name))
            for paragraph_index, paragraph in enumerate(root.findall(_HP + "p")):
                label = _text(paragraph)
                if label.startswith("#"):
                    current_category = label[1:].strip()
                    if not current_category:
                        current_category = "이름 없는 서식"
                    category_index += 1
                if current_category is None:
                    continue
                for table_index, table in enumerate(_top_tables(paragraph)):
                    preview = _table_preview(table)
                    template_number = sum(1 for item in records if item["category_index"] == category_index) + 1
                    records.append({
                        "id": f"{category_index}:{template_number}",
                        "category": current_category,
                        "category_index": category_index,
                        "number": template_number,
                        "name": f"{current_category} · 모양 {template_number}",
                        "rows": preview["rows"],
                        "cols": preview["cols"],
                        "cells": preview["cells"],
                        "section": section_name,
                        "paragraph_index": paragraph_index,
                        "table_index": table_index,
                    })
    return records


def list_catalog(path: str | Path | None = None) -> dict:
    """이름 구획과 각 표 모양의 구조·텍스트 미리보기를 반환한다."""
    records = _scan(path or default_catalog_path())
    categories = []
    for record in records:
        if not categories or categories[-1]["id"] != str(record["category_index"]):
            categories.append({
                "id": str(record["category_index"]),
                "name": record["category"],
                "templates": [],
            })
        categories[-1]["templates"].append({
            key: record[key] for key in ("id", "name", "rows", "cols", "cells")
        })
    return {
        "source": Path(path or default_catalog_path()).name,
        "category_count": len(categories),
        "template_count": len(records),
        "categories": categories,
    }


def _find_template(records: list[dict], template_id: str) -> dict:
    for record in records:
        if record["id"] == template_id:
            return record
    raise ValueError("선택한 표 서식 항목을 찾을 수 없습니다. 목록을 새로고침해 주세요.")


def _paragraph_with_table(source_paragraph, table_index):
    paragraph = copy.deepcopy(source_paragraph)
    tables = _top_tables(paragraph)
    chosen = tables[table_index]
    parents = {child: parent for parent in paragraph.iter() for child in list(parent)}
    run = parents.get(chosen)
    while run is not None and run.tag != _HP + "run":
        run = parents.get(run)
    if run is None:
        raise ValueError("선택한 표의 HWPX 구조를 해석하지 못했습니다.")
    for child in list(paragraph):
        if child.tag == _HP + "linesegarray":
            paragraph.remove(child)
            continue
        if child is not run:
            paragraph.remove(child)
            continue
    # The table is a direct child of this run in valid HWPX; preserve only it.
    for item in list(run):
        if item is not chosen:
            run.remove(item)
    return paragraph


def _section_properties_paragraph(root):
    for paragraph in root.findall(_HP + "p"):
        if any(node.tag == _HP + "secPr" for node in paragraph.iter()):
            preserved = copy.deepcopy(paragraph)
            for run in list(preserved.iter(_HP + "run")):
                for child in list(run):
                    if child.tag not in (_HP + "secPr", _HP + "ctrl"):
                        run.remove(child)
            for child in list(preserved):
                if child.tag not in (_HP + "run",):
                    preserved.remove(child)
            return preserved
    return None


def export_template(template_id: str, output_path: str | Path,
                    catalog_path: str | Path | None = None) -> Path:
    """원본 HWPX의 셀 서식·테두리·병합을 보존해 선택한 표만 든 HWPX를 만든다."""
    source = Path(catalog_path or default_catalog_path())
    record = _find_template(_scan(source), str(template_id))
    target = Path(output_path)
    if target.suffix.lower() != ".hwpx":
        raise ValueError("저장 파일은 .hwpx 확장자를 사용해 주세요.")
    if target.resolve() == source.resolve():
        raise ValueError("원본 표 서식 모음은 덮어쓸 수 없습니다.")
    with _safe_archive(source) as archive:
        section_bytes = archive.read(record["section"])
        root = ET.fromstring(section_bytes)
        paragraphs = root.findall(_HP + "p")
        source_paragraph = paragraphs[record["paragraph_index"]]
        tables = _top_tables(source_paragraph)
        output_paragraph = _paragraph_with_table(source_paragraph, record["table_index"])
        properties = _section_properties_paragraph(root)

        for section_name in _section_names(archive):
            if section_name == record["section"]:
                section_root = root
                keep = [node for node in (properties, output_paragraph) if node is not None]
                for child in list(section_root):
                    section_root.remove(child)
                section_root.extend(keep)
                section_data = ET.tostring(section_root, encoding="utf-8", xml_declaration=True)
            else:
                other_root = ET.fromstring(archive.read(section_name))
                other_properties = _section_properties_paragraph(other_root)
                for child in list(other_root):
                    other_root.remove(child)
                if other_properties is not None:
                    other_root.append(other_properties)
                section_data = ET.tostring(other_root, encoding="utf-8", xml_declaration=True)
            if section_name == record["section"]:
                chosen_data = section_data
                break

        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for info in archive.infolist():
                data = chosen_data if info.filename == record["section"] else archive.read(info.filename)
                output.writestr(info, data)
    return target
