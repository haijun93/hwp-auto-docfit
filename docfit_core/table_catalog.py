"""표 서식 모음 HWPX에서 이름별 표 템플릿을 안전하게 읽고 개별 문서로 내보낸다."""

from __future__ import annotations

import copy
import re
import sys
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from .batch_format import _serialize
from .table_builder import BORDER_TYPES, BORDER_WIDTHS, FONTS, _Header, _installed_fonts

_HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
_HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
_HC = "{http://www.hancom.co.kr/hwpml/2011/core}"
_DEFAULT_NAME = "표 서식모음.hwpx"
_MAX_ARCHIVE_BYTES = 80 * 1024 * 1024
_MAX_ENTRIES = 2000

_DEFAULT_BORDER_SIDE = {"type": "SOLID", "width": "0.12 mm", "color": "#000000"}
_DEFAULT_BORDERS = {side: dict(_DEFAULT_BORDER_SIDE) for side in ("top", "bottom", "left", "right")}
_DEFAULT_STYLE = {"font": "한컴돋움", "size": 11.0, "bold": False, "color": "#000000", "fill": ""}


def _tag(element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _child(element, name: str):
    return next((x for x in element if _tag(x) == name), None)


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


def _cell_text_nodes(cell):
    sub_tc = cell.find(".//" + _HP + "tbl//" + _HP + "tc")
    target = sub_tc if sub_tc is not None else cell
    found = []

    def walk(node):
        for child in list(node):
            if child.tag == _HP + "tbl":
                continue
            if child.tag == _HP + "t":
                found.append(child)
            else:
                walk(child)

    walk(target)
    return found


def _cell_runs(cell):
    sub_tc = cell.find(".//" + _HP + "tbl//" + _HP + "tc")
    target = sub_tc if sub_tc is not None else cell
    found = []

    def walk(node):
        for child in list(node):
            if child.tag == _HP + "tbl":
                continue
            if child.tag == _HP + "run":
                found.append(child)
            else:
                walk(child)

    walk(target)
    return found


def _cell_paragraphs(cell):
    sub_tc = cell.find(".//" + _HP + "tbl//" + _HP + "tc")
    target = sub_tc if sub_tc is not None else cell
    found = []

    def walk(node):
        for child in list(node):
            if child.tag == _HP + "tbl":
                continue
            if child.tag == _HP + "p":
                found.append(child)
            else:
                walk(child)

    walk(target)
    return found


def _normalize_hex(value: str | None, default: str = "#000000") -> str:
    if isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", value.strip()):
        return value.strip().upper()
    return default


def _header_lookup(header_root) -> dict:
    """HWPX header.xml에서 글꼴·글자모양·문단정렬·테두리/배경을 사전으로 읽는다."""
    fonts: dict[str, str] = {}
    if header_root is None:
        return {"fonts": fonts, "chars": {}, "paras": {}, "borders": {}}
    fontfaces = [el for el in header_root.iter() if _tag(el) == "fontface"]
    ordered = sorted(fontfaces, key=lambda ff: 0 if ff.get("lang") == "HANGUL" else 1)
    for ff in ordered:
        for font in ff:
            if _tag(font) == "font" and font.get("id") not in fonts and font.get("face"):
                fonts[font.get("id")] = font.get("face")

    chars: dict[str, dict] = {}
    for cp in (el for el in header_root.iter() if _tag(el) == "charPr"):
        cid = cp.get("id")
        if not cid:
            continue
        ref = _child(cp, "fontRef")
        font_id = ref.get("hangul", "0") if ref is not None else "0"
        face = fonts.get(font_id, "한컴돋움")
        try:
            raw_size = round(max(1.0, min(40.0, int(cp.get("height", "1000")) / 100.0)), 1)
        except ValueError:
            raw_size = 11.0
        bold = any(_tag(child) == "bold" for child in cp)
        color = _normalize_hex(cp.get("textColor"), "#000000")
        chars[cid] = {"font": face, "size": raw_size, "bold": bold, "color": color}

    paras: dict[str, str] = {}
    for pp in (el for el in header_root.iter() if _tag(el) == "paraPr"):
        pid = pp.get("id")
        align = _child(pp, "align")
        if pid:
            paras[pid] = (align.get("horizontal", "CENTER") if align is not None else "CENTER").upper()

    borders: dict[str, dict] = {}
    for bf in (el for el in header_root.iter() if _tag(el) == "borderFill"):
        bid = bf.get("id")
        if not bid:
            continue
        sides = {}
        for side in ("top", "bottom", "left", "right"):
            node = _child(bf, side + "Border")
            btype = node.get("type", "NONE") if node is not None else "NONE"
            bwidth = node.get("width", "0.12 mm") if node is not None else "0.12 mm"
            bcolor = _normalize_hex(node.get("color") if node is not None else "#000000", "#000000")
            if btype not in BORDER_TYPES:
                btype = "SOLID"
            if bwidth not in BORDER_WIDTHS:
                bwidth = "0.12 mm"
            sides[side] = {"type": btype, "width": bwidth, "color": bcolor}
        fill = ""
        for wb in (el for el in bf.iter() if _tag(el) == "winBrush"):
            face_color = wb.get("faceColor", "")
            if re.fullmatch(r"#[0-9A-Fa-f]{6}", face_color):
                fill = face_color.upper()
                break
        if not fill:
            grad_colors = [
                el.get("value", "").upper()
                for el in bf.iter()
                if _tag(el) == "color" and re.fullmatch(r"#[0-9A-Fa-f]{6}", el.get("value", ""))
            ]
            non_white = [c for c in grad_colors if c != "#FFFFFF"]
            if non_white:
                fill = non_white[-1]
            elif grad_colors:
                fill = grad_colors[-1]
        borders[bid] = {"fill": fill, "borders": sides}

    return {"fonts": fonts, "chars": chars, "paras": paras, "borders": borders}


def _cell_meta(cell, fallback_row: int, fallback_col: int, text: str, header_info: dict | None) -> dict:
    addr = cell.find(_HP + "cellAddr")
    span = cell.find(_HP + "cellSpan")
    sz = cell.find(_HP + "cellSz")
    row_addr = int(addr.get("rowAddr", fallback_row)) if addr is not None else fallback_row
    col_addr = int(addr.get("colAddr", fallback_col)) if addr is not None else fallback_col
    row_span = max(1, int(span.get("rowSpan", 1))) if span is not None else 1
    col_span = max(1, int(span.get("colSpan", 1))) if span is not None else 1
    width = max(1, int(sz.get("width", 4000))) if sz is not None else 4000
    height = max(1, int(sz.get("height", 1800))) if sz is not None else 1800

    chars = (header_info or {}).get("chars", {})
    paras = (header_info or {}).get("paras", {})
    borders_map = (header_info or {}).get("borders", {})

    target_cell = cell
    sub_tc = cell.find(".//" + _HP + "tbl//" + _HP + "tc")
    if sub_tc is not None:
        target_cell = sub_tc

    runs = _cell_runs(target_cell)
    char_id = runs[0].get("charPrIDRef", "0") if runs else "0"
    char_info = chars.get(char_id, _DEFAULT_STYLE)

    cell_paras = _cell_paragraphs(target_cell)
    para_id = cell_paras[0].get("paraPrIDRef", "0") if cell_paras else "0"
    align = paras.get(para_id, "CENTER")

    bf_id = target_cell.get("borderFillIDRef", "1")
    bf_info = borders_map.get(bf_id, {"fill": "", "borders": _DEFAULT_BORDERS})

    size = char_info.get("size", 11.0)
    display_size = size if size >= 6.0 else 10.0
    return {
        "row": row_addr,
        "col": col_addr,
        "rowSpan": row_span,
        "colSpan": col_span,
        "width": width,
        "height": height,
        "text": text,
        "align": align,
        "style": {
            "font": char_info.get("font", "한컴돋움"),
            "size": display_size,
            "bold": bool(char_info.get("bold", False)),
            "color": char_info.get("color", "#000000"),
            "fill": bf_info.get("fill", ""),
        },
        "borders": copy.deepcopy(bf_info.get("borders", _DEFAULT_BORDERS)),
    }


def _table_preview(table, header_info: dict | None = None) -> dict:
    rows = []
    meta_rows = []
    for r_idx, row in enumerate(table.findall(_HP + "tr")[:40]):
        cells = []
        meta_cells = []
        for c_idx, cell in enumerate(row.findall(_HP + "tc")[:30]):
            # Avoid text from a nested table leaking into the containing cell's label.
            parts = [node.text or "" for node in _cell_text_nodes(cell)]
            text = " ".join("".join(parts).split())[:80]
            cells.append(text)
            meta_cells.append(_cell_meta(cell, r_idx, c_idx, text, header_info))
        rows.append(cells)
        meta_rows.append(meta_cells)
    return {
        "rows": int(table.get("rowCnt", len(rows)) or len(rows)),
        "cols": int(table.get("colCnt", max((len(row) for row in rows), default=0)) or 0),
        "cells": rows,
        "cell_meta": meta_rows,
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
        header_root = (
            ET.fromstring(archive.read("Contents/header.xml"))
            if "Contents/header.xml" in archive.namelist()
            else None
        )
        header_info = _header_lookup(header_root)
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
                    preview = _table_preview(table, header_info)
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
                        "cell_meta": preview["cell_meta"],
                        "section": section_name,
                        "paragraph_index": paragraph_index,
                        "table_index": table_index,
                    })
    return records


def list_catalog(path: str | Path | None = None) -> dict:
    """이름 구획과 각 표 모양의 구조·텍스트·서식 미리보기를 반환한다."""
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
            key: record[key] for key in ("id", "name", "rows", "cols", "cells", "cell_meta")
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


def _apply_cell_edits(table, edits: dict) -> None:
    """Apply text-only edits to selected cells while retaining their HWPX formatting tree."""
    rows = table.findall(_HP + "tr")
    for key, value in edits.items():
        match = re.fullmatch(r"(\d{1,3}):(\d{1,3})", str(key))
        if (not match or not isinstance(value, str) or len(value) > 2000 or
                re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value)):
            raise ValueError("표 칸 수정 정보를 확인해 주세요.")
        row_index, cell_index = map(int, match.groups())
        if row_index >= len(rows):
            raise ValueError("수정할 표 행을 찾을 수 없습니다.")
        cells = rows[row_index].findall(_HP + "tc")
        if cell_index >= len(cells):
            raise ValueError("수정할 표 칸을 찾을 수 없습니다.")
        cell = cells[cell_index]
        text_nodes = _cell_text_nodes(cell)
        if not text_nodes:
            runs = _cell_runs(cell)
            run = runs[0] if runs else None
            if run is None:
                paragraph = next(cell.iter(_HP + "p"), None)
                if paragraph is None:
                    raise ValueError("선택한 칸에 입력 가능한 글자 영역이 없습니다.")
                run = type(paragraph)(_HP + "run", {"charPrIDRef": "0"})
                paragraph.append(run)
            text_node = type(run)(_HP + "t")
            run.append(text_node)
            text_nodes = [text_node]
        text_nodes[0].text = value
        for node in text_nodes[1:]:
            node.text = ""


def _resize_task_table(table, step_count: int) -> None:
    """분야별과제표(3행)의 정보단위 세트+연결단위 세트를 단계 수에 맞게 너비(46601 twip) 보존하여 재구성한다."""
    if not (2 <= step_count <= 10):
        raise ValueError("단계 수는 2~10 사이로 지정해 주세요.")
    rows = table.findall(_HP + "tr")
    if len(rows) < 3:
        raise ValueError("과제표 구조(3행)를 찾을 수 없습니다.")

    total_w = 46601
    conn_w = (step_count - 1) * 566 + 283
    rem_w = total_w - conn_w
    step_base = rem_w // step_count
    step_rem = rem_w % step_count
    step_widths = [step_base + (step_rem if i == step_count - 1 else 0) for i in range(step_count)]
    center_widths = [sw - 2830 for sw in step_widths]

    r0_cells = rows[0].findall(_HP + "tc")
    r1_cells = rows[1].findall(_HP + "tc")
    r2_cells = rows[2].findall(_HP + "tc")
    orig_n = max(1, len(r0_cells) // 4)

    new_r0, new_r1, new_r2 = [], [], []
    for i in range(step_count):
        src_i = min(i, orig_n - 1)
        is_last = (i == step_count - 1)

        # Row 0: 4 cells [left cap, center title with sub-table, right cap, connector]
        c0 = copy.deepcopy(r0_cells[src_i * 4])
        c1 = copy.deepcopy(r0_cells[src_i * 4 + 1])
        c2 = copy.deepcopy(r0_cells[src_i * 4 + 2])
        c3 = copy.deepcopy(r0_cells[src_i * 4 + 3])
        addr0 = c0.find(_HP + "cellAddr")
        if addr0 is not None:
            addr0.set("colAddr", str(i * 4))
        addr1 = c1.find(_HP + "cellAddr")
        if addr1 is not None:
            addr1.set("colAddr", str(i * 4 + 1))
        addr2 = c2.find(_HP + "cellAddr")
        if addr2 is not None:
            addr2.set("colAddr", str(i * 4 + 2))
        addr3 = c3.find(_HP + "cellAddr")
        if addr3 is not None:
            addr3.set("colAddr", str(i * 4 + 3))

        sz0 = c0.find(_HP + "cellSz")
        if sz0 is not None:
            sz0.set("width", "1415")
        sz1 = c1.find(_HP + "cellSz")
        if sz1 is not None:
            sz1.set("width", str(center_widths[i]))
        sub = c1.find(".//" + _HP + "tbl")
        if sub is not None:
            sub_sz = sub.find(_HP + "sz")
            if sub_sz is not None:
                sub_sz.set("width", str(center_widths[i] - 371))
            sub_tc = sub.find(".//" + _HP + "tc")
            if sub_tc is not None and sub_tc.find(_HP + "cellSz") is not None:
                sub_tc.find(_HP + "cellSz").set("width", str(center_widths[i] - 371))
        sz2 = c2.find(_HP + "cellSz")
        if sz2 is not None:
            sz2.set("width", "1415")
        sz3 = c3.find(_HP + "cellSz")
        if sz3 is not None:
            sz3.set("width", "283" if is_last else "566")
        c3.set("borderFillIDRef", "249" if is_last else "248")

        if i >= orig_n:
            if sub is not None:
                t_nodes = sub.findall(".//" + _HP + "t")
                if t_nodes:
                    t_nodes[0].text = f"과제 {i + 1}"
                    for t in t_nodes[1:]:
                        t.text = ""
        new_r0.extend([c0, c1, c2, c3])

        # Row 1: 3 cells [left cap bottom, right cap bottom, connector bottom]
        r1_c0 = copy.deepcopy(r1_cells[src_i * 3])
        r1_c1 = copy.deepcopy(r1_cells[src_i * 3 + 1])
        r1_c2 = copy.deepcopy(r1_cells[src_i * 3 + 2])
        r1_addr0 = r1_c0.find(_HP + "cellAddr")
        if r1_addr0 is not None:
            r1_addr0.set("colAddr", str(i * 4))
        r1_addr1 = r1_c1.find(_HP + "cellAddr")
        if r1_addr1 is not None:
            r1_addr1.set("colAddr", str(i * 4 + 2))
        r1_addr2 = r1_c2.find(_HP + "cellAddr")
        if r1_addr2 is not None:
            r1_addr2.set("colAddr", str(i * 4 + 3))

        r1_sz0 = r1_c0.find(_HP + "cellSz")
        if r1_sz0 is not None:
            r1_sz0.set("width", "1415")
        r1_sz1 = r1_c1.find(_HP + "cellSz")
        if r1_sz1 is not None:
            r1_sz1.set("width", "1415")
        r1_sz2 = r1_c2.find(_HP + "cellSz")
        if r1_sz2 is not None:
            r1_sz2.set("width", "283" if is_last else "566")
        r1_c2.set("borderFillIDRef", "252")
        new_r1.extend([r1_c0, r1_c1, r1_c2])

        # Row 2: 2 cells [content box (colSpan 3), connector bottom]
        r2_c0 = copy.deepcopy(r2_cells[src_i * 2])
        r2_c1 = copy.deepcopy(r2_cells[src_i * 2 + 1])
        r2_addr0 = r2_c0.find(_HP + "cellAddr")
        if r2_addr0 is not None:
            r2_addr0.set("colAddr", str(i * 4))
        r2_addr1 = r2_c1.find(_HP + "cellAddr")
        if r2_addr1 is not None:
            r2_addr1.set("colAddr", str(i * 4 + 3))

        r2_sz0 = r2_c0.find(_HP + "cellSz")
        if r2_sz0 is not None:
            r2_sz0.set("width", str(step_widths[i]))
        r2_sz1 = r2_c1.find(_HP + "cellSz")
        if r2_sz1 is not None:
            r2_sz1.set("width", "283" if is_last else "566")
        r2_c1.set("borderFillIDRef", "254")

        if i >= orig_n:
            t_nodes = r2_c0.findall(".//" + _HP + "t")
            if t_nodes:
                t_nodes[0].text = f"• 과제 {i + 1} 세부내용"
                for t in t_nodes[1:]:
                    t.text = ""
        new_r2.extend([r2_c0, r2_c1])

    for r, new_cells in zip(rows, [new_r0, new_r1, new_r2]):
        for old in r.findall(_HP + "tc"):
            r.remove(old)
        for c in new_cells:
            r.append(c)
    table.set("colCnt", str(step_count * 4))


def _parse_structure_op(operation, row_count: int, col_count: int) -> tuple[str, int]:
    if isinstance(operation, str):
        if operation == "add_row":
            return ("insert_row", row_count)
        if operation == "delete_row":
            return ("delete_row", row_count - 1)
        if operation == "add_column":
            return ("insert_column", col_count)
        if operation == "delete_column":
            return ("delete_column", col_count - 1)
        match = re.fullmatch(r"(insert_row|delete_row|insert_column|delete_column):(\d{1,3})", operation)
        if match:
            return (match.group(1), int(match.group(2)))
    elif isinstance(operation, dict):
        op_name = operation.get("op")
        if op_name == "resize_steps":
            steps = operation.get("steps")
            if isinstance(steps, int) and not isinstance(steps, bool):
                return ("resize_steps", steps)
            raise ValueError("단계 수를 확인해 주세요.")
        idx = operation.get("index")
        if op_name in ("insert_row", "delete_row", "insert_column", "delete_column") and isinstance(idx, int) and not isinstance(idx, bool):
            return (op_name, idx)
    raise ValueError("지원하지 않는 표 구조 수정입니다.")


def _apply_structure_edits(table, operations: list) -> None:
    """Append/insert/remove native HWPX rows and columns by cloning formatted cells."""
    if not isinstance(operations, list) or len(operations) > 100:
        raise ValueError("표 구조 수정 정보가 올바르지 않습니다.")
    for operation in operations:
        rows = table.findall(_HP + "tr")
        row_count = len(rows)
        col_count = int(table.get("colCnt", "0"))
        op_name, target_idx = _parse_structure_op(operation, row_count, col_count)

        if op_name == "resize_steps":
            _resize_task_table(table, target_idx)
            continue

        if op_name == "insert_row":
            if row_count >= 100:
                raise ValueError("표는 최대 100행까지 추가할 수 있습니다.")
            if not rows or not (0 <= target_idx <= row_count):
                raise ValueError("행 추가 위치를 확인해 주세요.")
            if target_idx == row_count:
                source = rows[-1]
                clone = copy.deepcopy(source)
                for cell in clone.findall(_HP + "tc"):
                    span = cell.find(_HP + "cellSpan")
                    if span is not None and int(span.get("rowSpan", "1")) != 1:
                        raise ValueError("마지막 행의 세로 병합 셀을 해제한 뒤 행을 추가해 주세요.")
                    address = cell.find(_HP + "cellAddr")
                    if address is not None:
                        address.set("rowAddr", str(row_count))
                    for node in cell.iter(_HP + "t"):
                        node.text = ""
                table.insert(list(table).index(rows[-1]) + 1, clone)
            else:
                for prev_row in rows[:target_idx]:
                    for cell in prev_row.findall(_HP + "tc"):
                        span = cell.find(_HP + "cellSpan")
                        address = cell.find(_HP + "cellAddr")
                        if span is not None and address is not None:
                            if int(address.get("rowAddr", "0")) + int(span.get("rowSpan", "1")) > target_idx:
                                raise ValueError("세로 병합된 셀 구간 사이에는 행을 끼울 수 없습니다.")
                source = rows[target_idx]
                clone = copy.deepcopy(source)
                for cell in clone.findall(_HP + "tc"):
                    span = cell.find(_HP + "cellSpan")
                    if span is not None:
                        span.set("rowSpan", "1")
                    address = cell.find(_HP + "cellAddr")
                    if address is not None:
                        address.set("rowAddr", str(target_idx))
                    for node in cell.iter(_HP + "t"):
                        node.text = ""
                for existing_row in rows[target_idx:]:
                    for cell in existing_row.findall(_HP + "tc"):
                        address = cell.find(_HP + "cellAddr")
                        if address is not None:
                            address.set("rowAddr", str(int(address.get("rowAddr", "0")) + 1))
                table.insert(list(table).index(rows[target_idx]), clone)
            table.set("rowCnt", str(row_count + 1))

        elif op_name == "delete_row":
            if row_count <= 1:
                raise ValueError("표에는 최소 한 행이 있어야 합니다.")
            if not (0 <= target_idx < row_count):
                raise ValueError("삭제할 표 행을 찾을 수 없습니다.")
            target_row = rows[target_idx]
            for cell in target_row.findall(_HP + "tc"):
                span = cell.find(_HP + "cellSpan")
                if span is not None and int(span.get("rowSpan", "1")) > 1:
                    raise ValueError("세로 병합된 셀이 포함된 행은 먼저 병합을 해제해 주세요.")
            for prev_row in rows[:target_idx]:
                for cell in prev_row.findall(_HP + "tc"):
                    span = cell.find(_HP + "cellSpan")
                    address = cell.find(_HP + "cellAddr")
                    if span is not None and address is not None:
                        if int(span.get("rowSpan", "1")) > 1 and int(address.get("rowAddr", "0")) + int(span.get("rowSpan", "1")) > target_idx:
                            msg = ("마지막 행과 세로 병합된 셀은 먼저 병합을 해제해 주세요."
                                   if target_idx == row_count - 1 else
                                   "세로 병합된 셀이 포함된 행은 먼저 병합을 해제해 주세요.")
                            raise ValueError(msg)
            table.remove(target_row)
            for existing_row in rows[target_idx + 1:]:
                for cell in existing_row.findall(_HP + "tc"):
                    address = cell.find(_HP + "cellAddr")
                    if address is not None:
                        address.set("rowAddr", str(max(0, int(address.get("rowAddr", "1")) - 1)))
            table.set("rowCnt", str(row_count - 1))

        elif op_name == "insert_column":
            if not rows or not col_count:
                raise ValueError("열이 없는 표입니다.")
            if col_count >= 50:
                raise ValueError("표는 최대 50열까지 추가할 수 있습니다.")
            if not (0 <= target_idx <= col_count):
                raise ValueError("열 추가 위치를 확인해 주세요.")
            if target_idx == col_count:
                for row in rows:
                    cells = row.findall(_HP + "tc")
                    if not cells:
                        raise ValueError("빈 행에는 열을 추가할 수 없습니다.")
                    last = cells[-1]
                    span = last.find(_HP + "cellSpan")
                    clone = copy.deepcopy(last)
                    if span is not None:
                        old_col_span = max(1, int(span.get("colSpan", "1")))
                        span.set("colSpan", "1")
                        span.set("rowSpan", "1")
                        size = clone.find(_HP + "cellSz")
                        if size is not None and old_col_span > 1:
                            size.set("width", str(max(1, int(size.get("width", "1")) // old_col_span)))
                    address = clone.find(_HP + "cellAddr")
                    if address is not None:
                        address.set("colAddr", str(col_count))
                    for node in clone.iter(_HP + "t"):
                        node.text = ""
                    row.append(clone)
            else:
                for row in rows:
                    cells = row.findall(_HP + "tc")
                    if not cells:
                        raise ValueError("빈 행에는 열을 추가할 수 없습니다.")
                    chosen_idx = len(cells) - 1
                    for idx, tc in enumerate(cells):
                        addr = tc.find(_HP + "cellAddr")
                        c_addr = int(addr.get("colAddr", str(idx))) if addr is not None else idx
                        if c_addr >= target_idx:
                            chosen_idx = idx
                            break
                    ref_cell = cells[chosen_idx]
                    clone = copy.deepcopy(ref_cell)
                    span = clone.find(_HP + "cellSpan")
                    if span is not None:
                        old_col_span = max(1, int(span.get("colSpan", "1")))
                        span.set("colSpan", "1")
                        span.set("rowSpan", "1")
                        size = clone.find(_HP + "cellSz")
                        if size is not None and old_col_span > 1:
                            size.set("width", str(max(1, int(size.get("width", "1")) // old_col_span)))
                    address = clone.find(_HP + "cellAddr")
                    if address is not None:
                        address.set("colAddr", str(target_idx))
                    for node in clone.iter(_HP + "t"):
                        node.text = ""
                    for tc in cells[chosen_idx:]:
                        addr = tc.find(_HP + "cellAddr")
                        if addr is not None and int(addr.get("colAddr", "0")) >= target_idx:
                            addr.set("colAddr", str(int(addr.get("colAddr", "0")) + 1))
                    row.insert(list(row).index(ref_cell), clone)
            table.set("colCnt", str(col_count + 1))

        else:  # delete_column
            if not rows or not col_count:
                raise ValueError("열이 없는 표입니다.")
            if col_count <= 1:
                raise ValueError("표에는 최소 한 열이 있어야 합니다.")
            if not (0 <= target_idx < col_count):
                raise ValueError("삭제할 표 열을 찾을 수 없습니다.")
            if target_idx == col_count - 1:
                for row in rows:
                    cells = row.findall(_HP + "tc")
                    if not cells:
                        raise ValueError("열이 없는 행은 삭제할 수 없습니다.")
                    last = cells[-1]
                    span = last.find(_HP + "cellSpan")
                    if span is not None and (int(span.get("colSpan", "1")) != 1 or int(span.get("rowSpan", "1")) != 1):
                        raise ValueError("마지막 열의 병합 셀은 먼저 병합을 해제해 주세요.")
                    row.remove(last)
            else:
                targets = []
                for row in rows:
                    cells = row.findall(_HP + "tc")
                    if not cells:
                        raise ValueError("열이 없는 행은 삭제할 수 없습니다.")
                    found_tc = None
                    for idx, tc in enumerate(cells):
                        addr = tc.find(_HP + "cellAddr")
                        c_addr = int(addr.get("colAddr", str(idx))) if addr is not None else idx
                        if c_addr == target_idx:
                            found_tc = tc
                            break
                    if found_tc is None and target_idx < len(cells):
                        found_tc = cells[target_idx]
                    if found_tc is None:
                        raise ValueError("병합된 열은 먼저 병합을 해제해 주세요.")
                    span = found_tc.find(_HP + "cellSpan")
                    if span is not None and (int(span.get("colSpan", "1")) != 1 or int(span.get("rowSpan", "1")) != 1):
                        raise ValueError("병합 셀이 포함된 열은 먼저 병합을 해제해 주세요.")
                    targets.append((row, found_tc, cells))
                for row, found_tc, cells in targets:
                    row.remove(found_tc)
                    for tc in cells:
                        if tc is found_tc:
                            continue
                        addr = tc.find(_HP + "cellAddr")
                        if addr is not None and int(addr.get("colAddr", "0")) > target_idx:
                            addr.set("colAddr", str(max(0, int(addr.get("colAddr", "1")) - 1)))
            table.set("colCnt", str(col_count - 1))


def _clone_char_with_patch(pool: _Header, base_char_id: str, patch: dict, fallback_info: dict) -> str:
    """기존 셀의 charPr(자간·장평 등)을 보존하면서 글꼴·크기·굵게·글자색만 바꾼 새 charPr ID를 만든다."""
    font = patch.get("font", fallback_info.get("font", "한컴돋움"))
    if not isinstance(font, str) or (font not in FONTS and font not in _installed_fonts() and not re.fullmatch(r"[^\"'<>;{}]{1,40}", font)):
        raise ValueError("고를 수 있는 글꼴이 아닙니다.")
    try:
        size = float(patch.get("size", fallback_info.get("size", 11.0)))
    except (TypeError, ValueError) as exc:
        raise ValueError("글꼴 크기를 확인해 주세요.") from exc
    if not 6 <= size <= 40:
        raise ValueError("글꼴 크기는 6~40pt로 지정해 주세요.")
    bold = bool(patch.get("bold", fallback_info.get("bold", False)))
    color = str(patch.get("color", fallback_info.get("color", "#000000")) or "#000000")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        raise ValueError("글자색은 #RRGGBB 형식이어야 합니다.")
    color = color.upper()

    char_group = pool.groups["charProperties"]
    source = next((x for x in char_group if x.get("id") == str(base_char_id)), None)
    if source is None:
        source = next(x for x in char_group if x.get("id") == "0")
    clone = copy.deepcopy(source)
    clone.set("height", str(int(round(size * 100))))
    clone.set("textColor", color)
    ref = _child(clone, "fontRef")
    for lang, font_id in pool.font(font).items():
        if ref is not None and lang in ref.attrib:
            ref.set(lang, font_id)
    for old in [x for x in clone if _tag(x) == "bold"]:
        clone.remove(old)
    if bold:
        index = next((i for i, x in enumerate(clone) if _tag(x) in (
            "underline", "strikeout", "outline", "shadow", "emboss", "engrave", "supscript", "subscript")), len(clone))
        clone.insert(index, type(clone)(_HH + "bold", {}))
    return pool._append("charProperties", clone)


def _apply_style_edits(table, header_root, style_edits: dict) -> bool:
    """기본 표(_Header)의 글자 서식·바탕색·테두리 편집 기술을 표 서식 모음 셀에 적용한다."""
    if not isinstance(style_edits, dict) or len(style_edits) > 1000:
        raise ValueError("표 서식 수정 정보가 올바르지 않습니다.")
    if not style_edits:
        return False
    if header_root is None:
        raise ValueError("표 서식 헤더 정보를 찾을 수 없습니다.")
    header_info = _header_lookup(header_root)
    pool = _Header(header_root)
    rows = table.findall(_HP + "tr")
    modified = False

    for key, patch in style_edits.items():
        match = re.fullmatch(r"(\d{1,3}):(\d{1,3})", str(key))
        if not match or not isinstance(patch, dict):
            raise ValueError("표 칸 서식 수정 정보를 확인해 주세요.")
        row_index, cell_index = map(int, match.groups())
        if row_index >= len(rows):
            raise ValueError("서식을 수정할 표 행을 찾을 수 없습니다.")
        cells = rows[row_index].findall(_HP + "tc")
        if cell_index >= len(cells):
            raise ValueError("서식을 수정할 표 칸을 찾을 수 없습니다.")
        cell = cells[cell_index]
        sub_tc = cell.find(".//" + _HP + "tbl//" + _HP + "tc")
        target_cell = sub_tc if sub_tc is not None else cell

        if any(k in patch for k in ("font", "size", "bold", "color")):
            runs = _cell_runs(target_cell)
            if not runs:
                paragraph = next(target_cell.iter(_HP + "p"), None)
                if paragraph is None:
                    raise ValueError("선택한 칸에 글자 서식을 적용할 영역이 없습니다.")
                run = type(paragraph)(_HP + "run", {"charPrIDRef": "0"})
                paragraph.append(run)
                runs = [run]
            base_char_id = runs[0].get("charPrIDRef", "0")
            fallback = header_info["chars"].get(base_char_id, _DEFAULT_STYLE)
            new_char_id = _clone_char_with_patch(pool, base_char_id, patch, fallback)
            for run in runs:
                run.set("charPrIDRef", new_char_id)
            modified = True

        if "fill" in patch:
            fill = str(patch.get("fill") or "")
            if fill and not re.fullmatch(r"#[0-9A-Fa-f]{6}", fill):
                raise ValueError("바탕색은 #RRGGBB 형식이어야 합니다.")
            border_id = target_cell.get("borderFillIDRef", "1")
            target_cell.set("borderFillIDRef", pool.refill(border_id, fill.upper()))
            modified = True

        if "borders" in patch:
            borders_patch = patch.get("borders")
            if not isinstance(borders_patch, dict) or not borders_patch:
                raise ValueError("테두리 수정 정보를 확인해 주세요.")
            sides = {}
            for side_name, side_val in borders_patch.items():
                if side_name not in ("top", "bottom", "left", "right") or not isinstance(side_val, dict):
                    raise ValueError("테두리 방향 정보를 확인해 주세요.")
                btype = str(side_val.get("type", "SOLID"))
                bwidth = str(side_val.get("width", "0.12 mm"))
                bcolor = str(side_val.get("color", "#000000"))
                if btype not in BORDER_TYPES or bwidth not in BORDER_WIDTHS or not re.fullmatch(r"#[0-9A-Fa-f]{6}", bcolor):
                    raise ValueError("테두리(종류·굵기·색)를 확인해 주세요.")
                sides[side_name] = (btype, bwidth, bcolor.upper())
            border_id = target_cell.get("borderFillIDRef", "1")
            target_cell.set("borderFillIDRef", pool.reborder(border_id, sides))
            modified = True

    return modified


def export_template(template_id: str, output_path: str | Path,
                    catalog_path: str | Path | None = None, *,
                    cell_edits: dict | None = None,
                    structure_edits: list | None = None,
                    style_edits: dict | None = None) -> Path:
    """원본 HWPX 표 구조·셀 서식·테두리·병합을 보존하고 요청한 칸 글·구조·서식을 반영해 저장한다."""
    if cell_edits is not None and (not isinstance(cell_edits, dict) or len(cell_edits) > 1000):
        raise ValueError("표 칸 수정 정보가 올바르지 않습니다.")
    if style_edits is not None and (not isinstance(style_edits, dict) or len(style_edits) > 1000):
        raise ValueError("표 서식 수정 정보가 올바르지 않습니다.")
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
        output_paragraph = _paragraph_with_table(source_paragraph, record["table_index"])
        if structure_edits:
            selected_tables = _top_tables(output_paragraph)
            if len(selected_tables) != 1:
                raise ValueError("선택한 표를 편집할 수 없습니다.")
            _apply_structure_edits(selected_tables[0], structure_edits)
        if cell_edits:
            selected_tables = _top_tables(output_paragraph)
            if len(selected_tables) != 1:
                raise ValueError("선택한 표를 편집할 수 없습니다.")
            _apply_cell_edits(selected_tables[0], cell_edits)

        header_data = None
        if style_edits:
            selected_tables = _top_tables(output_paragraph)
            if len(selected_tables) != 1:
                raise ValueError("선택한 표를 편집할 수 없습니다.")
            header_bytes = archive.read("Contents/header.xml") if "Contents/header.xml" in archive.namelist() else None
            header_root = ET.fromstring(header_bytes) if header_bytes is not None else None
            if _apply_style_edits(selected_tables[0], header_root, style_edits) and header_bytes is not None:
                header_data = _serialize(header_root, header_bytes)

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
                if info.filename == record["section"]:
                    data = chosen_data
                elif info.filename == "Contents/header.xml" and header_data is not None:
                    data = header_data
                else:
                    data = archive.read(info.filename)
                output.writestr(info, data)
    return target
