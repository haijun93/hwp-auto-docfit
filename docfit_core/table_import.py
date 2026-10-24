"""한/글 HWPX 문서의 표 또는 클립보드 표 데이터를 표그림판 모델로 역변환한다.

순수 파이썬으로 동작하며, 한/글 COM이나 GUI 라이브러리가 필요하지 않습니다.
XML 파싱에는 보안을 위해 defusedxml만 사용합니다.
"""

from __future__ import annotations

import copy
import html
from html.parser import HTMLParser
import io
import math
import re
import zipfile
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as ET

from . import table_catalog as catalog
from .table_builder import BORDER_TYPES, BORDER_WIDTHS

HP = catalog._HP
HH = catalog._HH
HC = catalog._HC
UNIT_MM = 283.465


def _parse_color(value: str | None, default: str = "#000000") -> str:
    if not value or not isinstance(value, str):
        return default
    v = value.strip().upper()
    if re.fullmatch(r"#[0-9A-F]{6}", v):
        return v
    # RGB(r, g, b) 형식 파싱
    rgb_match = re.fullmatch(r"RGB\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", v, re.IGNORECASE)
    if rgb_match:
        r, g, b = (int(x) for x in rgb_match.groups())
        return f"#{r:02X}{g:02X}{b:02X}"
    return default


def _parse_width(width_str: str | None) -> tuple[str, float]:
    """한/글 너비 문자열('0.12 mm' 등)을 (width_kind, width_mm)으로 변환."""
    if not width_str or not isinstance(width_str, str):
        return "thin", 0.12
    m = re.search(r"([0-9.]+)\s*mm", width_str.strip().lower())
    if m:
        try:
            mm = float(m.group(1))
            if mm >= 0.5:
                return "thick", mm
            elif mm >= 0.3:
                return "thick", mm
            else:
                return "thin", mm
        except ValueError:
            pass
    return "thin", 0.12


def _parse_style(btype: str | None) -> str:
    """한/글 테두리 종류(SOLID, DASH, DOT, DOUBLE_SLIM 등)를 solid, dash, dot으로 변환."""
    if not btype:
        return "solid"
    bt = btype.upper()
    if "DOUBLE" in bt:
        return "double"
    if "DASH" in bt:
        return "dash"
    if "DOT" in bt or "CIRCLE" in bt:
        return "dot"
    return "solid"


def import_table_from_xml(table_elem: Any, header_info: dict | None = None) -> dict[str, Any]:
    """HWPX hp:tbl 요소를 표그림판 스케치 모델로 변환한다."""
    if isinstance(table_elem, (str, bytes)):
        table_elem = ET.fromstring(table_elem)
    warnings: list[str] = []
    if table_elem is None or not table_elem.tag.endswith("tbl"):
        return {
            "grid": {"cols": 1, "rows": 1, "cell_mm": 5.0},
            "lines": [],
            "texts": [],
            "cell_colors": [],
            "warnings": ["유효한 HWPX 표 요소를 찾을 수 없습니다."],
        }

    try:
        row_cnt = int(table_elem.get("rowCnt", 0))
        col_cnt = int(table_elem.get("colCnt", 0))
    except (TypeError, ValueError):
        row_cnt = col_cnt = 0

    rows_els = table_elem.findall(HP + "tr")
    if not row_cnt:
        row_cnt = len(rows_els)

    # 행/열 한도 검사
    if row_cnt > 200 or col_cnt > 200:
        warnings.append(f"표 크기({row_cnt}x{col_cnt})가 최대 한도(200x200)를 초과하여 조정되었습니다.")
        row_cnt = min(row_cnt, 200)
        col_cnt = min(col_cnt, 200)

    # 실제 셀들의 최대 열/행 탐색
    grid_cells: list[dict[str, Any]] = []
    max_c = col_cnt
    max_r = row_cnt

    borders_map = (header_info or {}).get("borders", {})
    chars_map = (header_info or {}).get("chars", {})
    paras_map = (header_info or {}).get("paras", {})

    for r_idx, tr in enumerate(rows_els[:row_cnt]):
        c_idx = 0
        for tc in tr.findall(HP + "tc"):
            addr = tc.find(HP + "cellAddr")
            span = tc.find(HP + "cellSpan")
            r = int(addr.get("rowAddr", r_idx)) if addr is not None else r_idx
            c = int(addr.get("colAddr", c_idx)) if addr is not None else c_idx
            rs = max(1, int(span.get("rowSpan", 1))) if span is not None else 1
            cs = max(1, int(span.get("colSpan", 1))) if span is not None else 1

            if c + cs > max_c:
                max_c = c + cs
            if r + rs > max_r:
                max_r = r + rs

            # 텍스트 추출
            runs = catalog._cell_runs(tc)
            bold = False
            if runs:
                char_id = runs[0].get("charPrIDRef", "0")
                bold = bool(chars_map.get(char_id, {}).get("bold", False))

            paras = catalog._cell_paragraphs(tc)
            align = "center"
            if paras:
                para_id = paras[0].get("paraPrIDRef", "0")
                h_align = paras_map.get(para_id, "CENTER").lower()
                if h_align in ("left", "center", "right"):
                    align = h_align

            text = '\n'.join(''.join(t.itertext()) for p in paras for t in p.iter(HP + 't')).strip()
            if any(n.tag in (HP + 'pic', HP + 'tbl') for n in tc.iter()):
                warnings.append('셀 안 그림·중첩 표는 가져오기에서 제외했습니다.')

            # 테두리 및 배경색 추출
            bf_id = tc.get("borderFillIDRef", "1")
            bf_info = borders_map.get(bf_id, {})
            fill_color = bf_info.get("fill", "")

            # sides borders
            sides_borders = bf_info.get("borders", {})

            grid_cells.append({
                "row": r,
                "col": c,
                "rowspan": rs,
                "colspan": cs,
                "text": text,
                "bold": bold,
                "align": align,
                "fill": fill_color,
                "borders": sides_borders,
            })
            c_idx = c + cs

    cols = max(1, min(max_c, 200))
    rows = max(1, min(max_r, 200))

    # 선(lines) 추출: 셀 테두리 선분 수집
    # 변 세그먼트 집합 (x1, y1, x2, y2) -> (width, style, width_mm, color)
    edge_map: dict[tuple[int, int, int, int], dict[str, Any]] = {}

    for cell in grid_cells:
        r, c, rs, cs = cell["row"], cell["col"], cell["rowspan"], cell["colspan"]
        if r >= rows or c >= cols:
            continue
        row_end = min(r + rs, rows)
        ce = min(c + cs, cols)

        borders = cell.get("borders", {})

        def apply_edge(x1, y1, x2, y2, side_name):
            side = borders.get(side_name, {})
            btype = side.get("type", "SOLID")
            if btype == "NONE":
                return
            width_str = side.get("width", "0.12 mm")
            color = side.get("color", "#000000")
            w_kind, w_mm = _parse_width(width_str)
            style = _parse_style(btype)
            if style == "double":
                w_kind = "double"
                style = "solid"

            key = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            # 우선순위: thick/double > thin
            if key not in edge_map or (w_kind in ("thick", "double") and edge_map[key]["width"] == "thin"):
                edge_map[key] = {
                    "width": w_kind,
                    "style": style,
                    "width_mm": w_mm,
                    "color": color,
                }

        # top
        apply_edge(c, r, ce, r, "top")
        # bottom
        apply_edge(c, row_end, ce, row_end, "bottom")
        # left
        apply_edge(c, r, c, row_end, "left")
        # right
        apply_edge(ce, r, ce, row_end, "right")

    lines: list[dict[str, Any]] = []
    for (x1, y1, x2, y2), info in sorted(edge_map.items()):
        lines.append({
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "width": info["width"],
            "style": info["style"],
            "width_mm": info["width_mm"],
            "color": info["color"],
        })

    # 글자(texts) 및 배경색(cell_colors) 수집
    texts: list[dict[str, Any]] = []
    cell_colors: list[dict[str, Any]] = []

    for cell in grid_cells:
        c, r = cell["col"], cell["row"]
        if c < cols and r < rows:
            if cell["text"]:
                texts.append({
                    "x": c,
                    "y": r,
                    "text": cell["text"],
                    "bold": cell["bold"],
                    "align": cell["align"],
                })
            if cell["fill"] and re.fullmatch(r"#[0-9A-Fa-f]{6}", cell["fill"]):
                cell_colors.append({
                    "x": c,
                    "y": r,
                    "color": cell["fill"].upper(),
                })

    warnings.append('행·열 크기를 균일한 5mm 격자로 변환했습니다. 원본 칸 크기와 다를 수 있습니다.')
    return {
        "grid": {"cols": cols, "rows": rows, "cell_mm": 5.0},
        "lines": lines,
        "texts": texts,
        "cell_colors": cell_colors,
        "warnings": warnings,
    }


def import_table_from_hwpx(path_or_bytes: str | Path | bytes, table_index: int = 0) -> dict[str, Any]:
    """HWPX 문서에서 N번째 표를 찾아 표그림판 모델로 추출한다."""
    try:
        archive = catalog._safe_archive(Path(path_or_bytes) if isinstance(path_or_bytes, (str, Path)) else io.BytesIO(path_or_bytes))
    except Exception as e:
        return {
            "grid": {"cols": 1, "rows": 1, "cell_mm": 5.0},
            "lines": [],
            "texts": [],
            "cell_colors": [],
            "warnings": [f"HWPX 파일을 열 수 없습니다: {e}"],
        }

    with archive:
        try:
            header_root = None
            if "Contents/header.xml" in archive.namelist():
                header_root = ET.fromstring(archive.read("Contents/header.xml"))
            header_info = catalog._header_lookup(header_root)
        except Exception as e:
            header_info = {}

        # 구역 XML들 순회하며 표 탐색
        current_idx = 0
        target_tbl = None
        for name in catalog._section_names(archive):
            try:
                root = ET.fromstring(archive.read(name))
                for tbl in root.iter(HP + "tbl"):
                    if current_idx == table_index:
                        target_tbl = tbl
                        break
                    current_idx += 1
                if target_tbl is not None:
                    break
            except Exception:
                continue

        if target_tbl is None:
            return {
                "grid": {"cols": 1, "rows": 1, "cell_mm": 5.0},
                "lines": [],
                "texts": [],
                "cell_colors": [],
                "warnings": [f"HWPX 문서에서 {table_index + 1}번째 표를 찾을 수 없습니다."],
            }

        return import_table_from_xml(target_tbl, header_info)


class _HTMLTableExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.rows: list[list[dict[str, Any]]] = []
        self.current_row: list[dict[str, Any]] = []
        self.current_cell: dict[str, Any] | None = None
        self.cell_text_chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        attr_dict = dict(attrs)
        if t == "table":
            self.in_table = True
        elif self.in_table and t == "tr":
            self.current_row = []
        elif self.in_table and t in ("td", "th"):
            rs = 1
            cs = 1
            try:
                rs = int(attr_dict.get("rowspan", 1))
            except ValueError:
                pass
            try:
                cs = int(attr_dict.get("colspan", 1))
            except ValueError:
                pass

            style = attr_dict.get("style", "")
            # 배경색 추출
            bg = ""
            bg_match = re.search(r"background(-color)?\s*:\s*([^;]+)", style, re.IGNORECASE)
            if bg_match:
                bg = _parse_color(bg_match.group(2).strip(), "")
            elif "bgcolor" in attr_dict:
                bg = _parse_color(attr_dict["bgcolor"], "")

            bold = (t == "th") or ("bold" in style.lower())
            align = "center"
            if "text-align" in style.lower():
                m_align = re.search(r"text-align\s*:\s*(left|center|right)", style, re.IGNORECASE)
                if m_align:
                    align = m_align.group(1).lower()
            elif "align" in attr_dict:
                align = attr_dict["align"].lower()

            self.current_cell = {
                "rowspan": max(1, rs),
                "colspan": max(1, cs),
                "fill": bg,
                "bold": bold,
                "align": align if align in ("left", "center", "right") else "center",
            }
            self.cell_text_chunks = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if self.in_table and t in ("td", "th") and self.current_cell is not None:
            self.current_cell["text"] = "".join(self.cell_text_chunks).strip()
            self.current_row.append(self.current_cell)
            self.current_cell = None
        elif self.in_table and t == "tr":
            if self.current_row:
                self.rows.append(self.current_row)
        elif t == "table":
            self.in_table = False

    def handle_data(self, data):
        if self.in_table and self.current_cell is not None:
            self.cell_text_chunks.append(data)


def import_table_from_html(html_str: str) -> dict[str, Any]:
    """클립보드 HTML(<table>)을 표그림판 모델로 변환한다."""
    warnings: list[str] = []
    if not html_str or not isinstance(html_str, str):
        return {
            "grid": {"cols": 1, "rows": 1, "cell_mm": 5.0},
            "lines": [],
            "texts": [],
            "cell_colors": [],
            "warnings": ["HTML 내용이 비어 있습니다."],
        }

    parser = _HTMLTableExtractor()
    try:
        parser.feed(html_str)
    except Exception as e:
        warnings.append(f"HTML 파싱 중 오류 발생: {e}")

    if not parser.rows:
        return {
            "grid": {"cols": 1, "rows": 1, "cell_mm": 5.0},
            "lines": [],
            "texts": [],
            "cell_colors": [],
            "warnings": ["HTML에서 <table> 요소를 찾을 수 없습니다."] + warnings,
        }

    # 2차원 매트릭스에 배치하여 rowspan/colspan 해석
    occupied: dict[tuple[int, int], bool] = {}
    cell_placements: list[dict[str, Any]] = []

    max_c = 0
    max_r = 0

    for r_idx, row in enumerate(parser.rows[:200]):
        c_idx = 0
        for cell in row[:200]:
            while (r_idx, c_idx) in occupied:
                c_idx += 1
            if c_idx >= 200:
                warnings.append('200열을 넘는 칸은 제외했습니다.')
                break
            rs = min(cell["rowspan"], 200 - r_idx)
            cs = min(cell["colspan"], 200 - c_idx)

            for dr in range(rs):
                for dc in range(cs):
                    occupied[(r_idx + dr, c_idx + dc)] = True

            cell_placements.append({
                "row": r_idx,
                "col": c_idx,
                "rowspan": rs,
                "colspan": cs,
                "text": cell["text"],
                "bold": cell["bold"],
                "align": cell["align"],
                "fill": cell["fill"],
            })

            if c_idx + cs > max_c:
                max_c = c_idx + cs
            if r_idx + rs > max_r:
                max_r = r_idx + rs
            c_idx += cs

    cols = max(1, min(max_c, 200))
    rows = max(1, min(max_r, 200))

    # lines 생성 (모든 셀 둘레를 기본 실선으로 생성)
    edge_set: set[tuple[int, int, int, int]] = set()
    for cp in cell_placements:
        r, c, rs, cs = cp["row"], cp["col"], cp["rowspan"], cp["colspan"]
        re_pos = min(r + rs, rows)
        ce_pos = min(c + cs, cols)
        edge_set.add((min(c, ce_pos), r, max(c, ce_pos), r))
        edge_set.add((min(c, ce_pos), re_pos, max(c, ce_pos), re_pos))
        edge_set.add((c, min(r, re_pos), c, max(r, re_pos)))
        edge_set.add((ce_pos, min(r, re_pos), ce_pos, max(r, re_pos)))

    lines: list[dict[str, Any]] = []
    for x1, y1, x2, y2 in sorted(edge_set):
        lines.append({
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "width": "thin",
            "style": "solid",
            "width_mm": 0.12,
            "color": "#000000",
        })

    texts: list[dict[str, Any]] = []
    cell_colors: list[dict[str, Any]] = []

    for cp in cell_placements:
        c, r = cp["col"], cp["row"]
        if c < cols and r < rows:
            if cp["text"]:
                texts.append({
                    "x": c,
                    "y": r,
                    "text": cp["text"],
                    "bold": cp["bold"],
                    "align": cp["align"],
                })
            if cp["fill"] and re.fullmatch(r"#[0-9A-Fa-f]{6}", cp["fill"]):
                cell_colors.append({
                    "x": c,
                    "y": r,
                    "color": cp["fill"].upper(),
                })

    warnings.append('HTML 표의 칸 크기·테두리는 균일한 5mm 격자·기본 실선으로 변환했습니다.')
    return {
        "grid": {"cols": cols, "rows": rows, "cell_mm": 5.0},
        "lines": lines,
        "texts": texts,
        "cell_colors": cell_colors,
        "warnings": warnings,
    }
