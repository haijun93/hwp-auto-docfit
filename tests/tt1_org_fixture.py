"""TT1 조직도 템플릿 시험용 합성 카탈로그 생성기 (HWPX fixture helper)."""

from __future__ import annotations

import copy
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from docfit_core import table_catalog as catalog

HP = catalog._HP
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"

SOURCE = Path(__file__).resolve().parents[1] / "resources/서식예시/표 서식모음.hwpx"

# 각 프로필별 독립 표 모델 데이터: 행별 (col, colSpan, rowSpan, text, role, has_fill)
_FIXTURE_MODELS = {
    "six_even_4": {
        "rows": 6,
        "cols": 12,
        "count": 4,
        "cells": [
            # Row 0
            [(0, 1, 1, "", "none", False), (1, 1, 1, "", "none", False), (2, 1, 1, "", "none", False),
             (3, 1, 1, "", "none", False), (4, 1, 1, "", "cap_left", False), (5, 2, 1, "", "cap_mid", False),
             (7, 1, 1, "", "cap_right", False), (8, 1, 1, "", "none", False), (9, 1, 1, "", "none", False),
             (10, 1, 1, "", "none", False), (11, 1, 1, "", "none", False)],
            # Row 1
            [(0, 1, 1, "", "none", False), (1, 1, 1, "", "none", False), (2, 1, 1, "", "none", False),
             (3, 1, 1, "", "top_edge_left", False), (4, 4, 1, "총괄부서", "top_box", True),
             (8, 1, 1, "", "top_edge_right", False), (9, 1, 1, "", "none", False), (10, 1, 1, "", "none", False),
             (11, 1, 1, "", "none", False)],
            # Row 2
            [(0, 1, 1, "", "conn_edge_left", False), (1, 1, 1, "", "conn_normal", False),
             (2, 1, 1, "", "conn_normal", False), (3, 1, 1, "", "conn_normal", False),
             (4, 1, 1, "", "conn_box_left", False), (5, 1, 1, "", "conn_mid_left", False),
             (6, 1, 1, "", "conn_mid_right", False), (7, 1, 1, "", "conn_box_right", False),
             (8, 1, 1, "", "conn_normal", False), (9, 1, 1, "", "conn_normal", False),
             (10, 1, 1, "", "conn_normal", False), (11, 1, 1, "", "conn_edge_right", False)],
            # Row 3
            [(0, 1, 1, "", "stem_first_left", False), (1, 1, 1, "", "stem_first_right", False),
             (2, 1, 1, "", "stem_gap", False), (3, 1, 1, "", "stem_inner_left", False),
             (4, 1, 1, "", "stem_inner_right", False), (5, 2, 1, "", "stem_gap", False),
             (7, 1, 1, "", "stem_inner_left", False), (8, 1, 1, "", "stem_inner_right", False),
             (9, 1, 1, "", "stem_gap", False), (10, 1, 1, "", "stem_last_left", False),
             (11, 1, 1, "", "stem_last_right", False)],
            # Row 4
            [(0, 2, 1, "팀1", "team", True), (2, 1, 1, "", "team_gap", False),
             (3, 2, 1, "팀2", "team", True), (5, 2, 1, "", "team_gap", False),
             (7, 2, 1, "팀3", "team", True), (9, 1, 1, "", "team_gap", False),
             (10, 2, 1, "팀4", "team", True)],
            # Row 5
            [(0, 2, 1, "(11명)", "count", False), (2, 1, 1, "", "count_gap", False),
             (3, 2, 1, "(22명)", "count", False), (5, 2, 1, "", "count_gap", False),
             (7, 2, 1, "(33명)", "count", False), (9, 1, 1, "", "count_gap", False),
             (10, 2, 1, "(44명)", "count", False)],
        ],
    },
    "six_odd_5": {
        "rows": 6,
        "cols": 14,
        "count": 5,
        "cells": [
            # Row 0
            [(0, 1, 1, "", "none", False), (1, 1, 1, "", "none", False), (2, 1, 1, "", "none", False),
             (3, 1, 1, "", "none", False), (4, 1, 1, "", "cap_left", False), (5, 4, 1, "", "cap_mid", False),
             (9, 1, 1, "", "cap_right", False), (10, 1, 1, "", "none", False), (11, 1, 1, "", "none", False),
             (12, 1, 1, "", "none", False), (13, 1, 1, "", "none", False)],
            # Row 1
            [(0, 1, 1, "", "none", False), (1, 1, 1, "", "none", False), (2, 1, 1, "", "none", False),
             (3, 1, 1, "", "top_edge_left", False), (4, 6, 1, "총괄부서", "top_box", True),
             (10, 1, 1, "", "top_edge_right", False), (11, 1, 1, "", "none", False), (12, 1, 1, "", "none", False),
             (13, 1, 1, "", "none", False)],
            # Row 2
            [(0, 1, 1, "", "conn_edge_left", False), (1, 1, 1, "", "conn_normal", False),
             (2, 1, 1, "", "conn_normal", False), (3, 1, 1, "", "conn_normal", False),
             (4, 1, 1, "", "conn_box_left", False), (5, 2, 1, "", "conn_mid_left", False),
             (7, 2, 1, "", "conn_mid_right", False), (9, 1, 1, "", "conn_box_right", False),
             (10, 1, 1, "", "conn_normal", False), (11, 1, 1, "", "conn_normal", False),
             (12, 1, 1, "", "conn_normal", False), (13, 1, 1, "", "conn_edge_right", False)],
            # Row 3
            [(0, 1, 1, "", "stem_first_left", False), (1, 1, 1, "", "stem_first_right", False),
             (2, 1, 1, "", "stem_gap", False), (3, 1, 1, "", "stem_inner_left", False),
             (4, 1, 1, "", "stem_inner_right", False), (5, 2, 1, "", "stem_mid_left", False),
             (7, 2, 1, "", "stem_mid_right", False), (9, 1, 1, "", "stem_inner_left", False),
             (10, 1, 1, "", "stem_inner_right", False), (11, 1, 1, "", "stem_gap", False),
             (12, 1, 1, "", "stem_last_left", False), (13, 1, 1, "", "stem_last_right", False)],
            # Row 4
            [(0, 2, 1, "팀1", "team", True), (2, 1, 1, "", "team_gap", False),
             (3, 2, 1, "팀2", "team", True), (5, 1, 1, "", "team_gap", False),
             (6, 2, 1, "팀3", "team", True), (8, 1, 1, "", "team_gap", False),
             (9, 2, 1, "팀4", "team", True), (11, 1, 1, "", "team_gap", False),
             (12, 2, 1, "팀5", "team", True)],
            # Row 5
            [(0, 2, 1, "(11명)", "count", False), (2, 1, 1, "", "count_gap", False),
             (3, 2, 1, "(22명)", "count", False), (5, 1, 1, "", "count_gap", False),
             (6, 2, 1, "(33명)", "count", False), (8, 1, 1, "", "count_gap", False),
             (9, 2, 1, "(44명)", "count", False), (11, 1, 1, "", "count_gap", False),
             (12, 2, 1, "(55명)", "count", False)],
        ],
    },
    "five_even_6": {
        "rows": 5,
        "cols": 18,
        "count": 6,
        "cells": [
            # Row 0 (top_row)
            [(0, 1, 1, "", "none", False), (1, 1, 1, "", "none", False), (2, 1, 1, "", "none", False),
             (3, 1, 1, "", "none", False), (4, 1, 1, "", "none", False), (5, 1, 1, "", "top_edge_left", False),
             (6, 6, 1, "총괄부서", "top_box", True), (12, 1, 1, "", "top_edge_right", False),
             (13, 1, 1, "", "none", False), (14, 1, 1, "", "none", False), (15, 1, 1, "", "none", False),
             (16, 1, 1, "", "none", False), (17, 1, 1, "", "none", False)],
            # Row 1 (connector_row)
            [(0, 1, 1, "", "conn_edge_left", False), (1, 1, 1, "", "conn_normal", False),
             (2, 1, 1, "", "conn_normal", False), (3, 1, 1, "", "conn_normal", False),
             (4, 1, 1, "", "conn_normal", False), (5, 1, 1, "", "conn_normal", False),
             (6, 1, 1, "", "conn_mid_left", False), (7, 1, 1, "", "conn_normal", False),
             (8, 1, 1, "", "conn_normal", False), (9, 1, 1, "", "conn_mid_right", False),
             (10, 1, 1, "", "conn_normal", False), (11, 1, 1, "", "conn_normal", False),
             (12, 1, 1, "", "conn_normal", False), (13, 1, 1, "", "conn_normal", False),
             (14, 1, 1, "", "conn_normal", False), (15, 1, 1, "", "conn_normal", False),
             (16, 1, 1, "", "conn_normal", False), (17, 1, 1, "", "conn_edge_right", False)],
            # Row 2 (stem_row)
            [(0, 1, 1, "", "stem_first_left", False), (1, 1, 1, "", "stem_first_right", False),
             (2, 1, 1, "", "stem_gap", False), (3, 1, 1, "", "stem_inner_left", False),
             (4, 1, 1, "", "stem_inner_right", False), (5, 1, 1, "", "stem_gap", False),
             (6, 1, 1, "", "stem_inner_left", False), (7, 1, 1, "", "stem_inner_right", False),
             (8, 2, 1, "", "stem_gap", False), (10, 1, 1, "", "stem_inner_left", False),
             (11, 1, 1, "", "stem_inner_right", False), (12, 1, 1, "", "stem_gap", False),
             (13, 1, 1, "", "stem_inner_left", False), (14, 1, 1, "", "stem_inner_right", False),
             (15, 1, 1, "", "stem_gap", False), (16, 1, 1, "", "stem_last_left", False),
             (17, 1, 1, "", "stem_last_right", False)],
            # Row 3 (team_row)
            [(0, 2, 1, "팀1", "team", True), (2, 1, 1, "", "team_gap", False),
             (3, 2, 1, "팀2", "team", True), (5, 1, 1, "", "team_gap", False),
             (6, 2, 1, "팀3", "team", True), (8, 2, 1, "", "team_gap", False),
             (10, 2, 1, "팀4", "team", True), (12, 1, 1, "", "team_gap", False),
             (13, 2, 1, "팀5", "team", True), (15, 1, 1, "", "team_gap", False),
             (16, 2, 1, "팀6", "team", True)],
            # Row 4 (count_row)
            [(0, 2, 1, "(11명)", "count", False), (2, 1, 1, "", "count_gap", False),
             (3, 2, 1, "(22명)", "count", False), (5, 1, 1, "", "count_gap", False),
             (6, 2, 1, "(33명)", "count", False), (8, 2, 1, "", "count_gap", False),
             (10, 2, 1, "(44명)", "count", False), (12, 1, 1, "", "count_gap", False),
             (13, 2, 1, "(55명)", "count", False), (15, 1, 1, "", "count_gap", False),
             (16, 2, 1, "(66명)", "count", False)],
        ],
    },
    "six_irregular_3": {
        "rows": 6,
        "cols": 13,
        "count": 3,
        "cells": [
            # Row 0
            [(0, 1, 1, "", "none", False), (1, 1, 1, "", "none", False), (2, 1, 1, "", "none", False),
             (3, 1, 1, "", "none", False), (4, 1, 1, "", "cap_left", False), (5, 3, 1, "", "cap_mid", False),
             (8, 1, 1, "", "cap_right", False), (9, 1, 1, "", "none", False), (10, 1, 1, "", "none", False),
             (11, 1, 1, "", "none", False), (12, 1, 1, "", "none", False)],
            # Row 1
            [(0, 1, 1, "", "none", False), (1, 1, 1, "", "none", False), (2, 1, 1, "", "none", False),
             (3, 1, 1, "", "top_edge_left", False), (4, 5, 1, "총괄부서", "top_box", True),
             (9, 1, 1, "", "top_edge_right", False), (10, 1, 1, "", "none", False),
             (11, 1, 1, "", "none", False), (12, 1, 1, "", "none", False)],
            # Row 2
            [(0, 1, 1, "", "conn_edge_left", False), (1, 1, 1, "", "conn_normal", False),
             (2, 1, 1, "", "conn_normal", False), (3, 1, 1, "", "conn_normal", False),
             (4, 1, 1, "", "conn_box_left", False), (5, 1, 1, "", "conn_normal", False),
             (6, 1, 1, "", "conn_mid_left", False), (7, 1, 1, "", "conn_mid_right", False),
             (8, 1, 1, "", "conn_box_right", False), (9, 1, 1, "", "conn_normal", False),
             (10, 1, 1, "", "conn_normal", False), (11, 1, 1, "", "conn_normal", False),
             (12, 1, 1, "", "conn_edge_right", False)],
            # Row 3
            [(0, 1, 1, "", "stem_first_left", False), (1, 1, 1, "", "stem_first_right", False),
             (2, 3, 1, "", "stem_gap", False), (5, 1, 1, "", "stem_inner_left", False),
             (6, 1, 1, "", "stem_inner_right", False), (7, 4, 1, "", "stem_gap", False),
             (11, 1, 1, "", "stem_last_left", False), (12, 1, 1, "", "stem_last_right", False)],
            # Row 4
            [(0, 3, 1, "팀1", "team", True), (3, 2, 1, "", "team_gap", False),
             (5, 3, 1, "팀2", "team", True), (8, 3, 1, "", "team_gap", False),
             (11, 2, 1, "팀3", "team", True)],
            # Row 5
            [(0, 3, 1, "(11명)", "count", False), (3, 2, 1, "", "count_gap", False),
             (5, 3, 1, "(22명)", "count", False), (8, 3, 1, "", "count_gap", False),
             (11, 2, 1, "(33명)", "count", False)],
        ],
    },
}

_ROLE_BORDERS = {
    "none": {"top": "NONE", "bottom": "NONE", "left": "NONE", "right": "NONE"},
    "top_box": {"top": "SOLID", "bottom": "SOLID", "left": "SOLID", "right": "SOLID"},
    "team": {"top": "SOLID", "bottom": "SOLID", "left": "SOLID", "right": "SOLID"},
    "count": {"top": "SOLID", "bottom": "SOLID", "left": "SOLID", "right": "SOLID"},
    "cap_left": {"top": "SOLID", "bottom": "NONE", "left": "SOLID", "right": "NONE"},
    "cap_mid": {"top": "SOLID", "bottom": "NONE", "left": "NONE", "right": "NONE"},
    "cap_right": {"top": "SOLID", "bottom": "NONE", "left": "NONE", "right": "SOLID"},
    "top_edge_left": {"top": "NONE", "bottom": "NONE", "left": "NONE", "right": "SOLID"},
    "top_edge_right": {"top": "NONE", "bottom": "NONE", "left": "SOLID", "right": "NONE"},
    "conn_edge_left": {"top": "NONE", "bottom": "NONE", "left": "NONE", "right": "NONE"},
    "conn_normal": {"top": "NONE", "bottom": "SOLID", "left": "NONE", "right": "NONE"},
    "conn_box_left": {"top": "SOLID", "bottom": "SOLID", "left": "NONE", "right": "NONE"},
    "conn_box_right": {"top": "SOLID", "bottom": "SOLID", "left": "NONE", "right": "NONE"},
    "conn_mid_left": {"top": "NONE", "bottom": "SOLID", "left": "NONE", "right": "SOLID"},
    "conn_mid_right": {"top": "NONE", "bottom": "SOLID", "left": "SOLID", "right": "NONE"},
    "conn_edge_right": {"top": "NONE", "bottom": "NONE", "left": "NONE", "right": "NONE"},
    "stem_first_left": {"top": "SOLID", "bottom": "NONE", "left": "NONE", "right": "SOLID"},
    "stem_first_right": {"top": "SOLID", "bottom": "NONE", "left": "SOLID", "right": "NONE"},
    "stem_inner_left": {"top": "NONE", "bottom": "NONE", "left": "NONE", "right": "SOLID"},
    "stem_inner_right": {"top": "NONE", "bottom": "NONE", "left": "SOLID", "right": "NONE"},
    "stem_last_left": {"top": "SOLID", "bottom": "NONE", "left": "NONE", "right": "SOLID"},
    "stem_last_right": {"top": "SOLID", "bottom": "NONE", "left": "SOLID", "right": "NONE"},
    "stem_gap": {"top": "NONE", "bottom": "NONE", "left": "NONE", "right": "NONE"},
    "team_gap": {"top": "NONE", "bottom": "NONE", "left": "NONE", "right": "NONE"},
    "count_gap": {"top": "NONE", "bottom": "NONE", "left": "NONE", "right": "NONE"},
}


def _build_border_fill_elements(start_id: int):
    elements = []
    role_to_id = {}
    current_id = start_id

    for role, borders in _ROLE_BORDERS.items():
        for has_fill in (False, True):
            key = (role, has_fill)
            bid = str(current_id)
            current_id += 1
            role_to_id[key] = bid

            bf = ET.Element(HH + "borderFill", {
                "id": bid,
                "threeD": "0",
                "shadow": "0",
                "centerLine": "none",
                "breakCellSeparateLine": "0",
            })
            ET.SubElement(bf, HH + "slash", {"type": "none", "Crooked": "0", "isCounter": "0"})
            ET.SubElement(bf, HH + "backSlash", {"type": "none", "Crooked": "0", "isCounter": "0"})
            for side in ("left", "right", "top", "bottom"):
                btype = borders.get(side, "NONE")
                width = "0.12 mm" if btype != "NONE" else "0.1 mm"
                color = "#000000"
                ET.SubElement(bf, HH + f"{side}Border", {"type": btype.lower(), "width": width, "color": color})
            fill_el = ET.SubElement(bf, HH + "fillBrush")
            if has_fill:
                ET.SubElement(fill_el, HH + "winBrush", {
                    "faceColor": "#E6E6E6",
                    "hatchColor": "#FF000000",
                    "alpha": "0",
                })
            else:
                ET.SubElement(fill_el, HH + "winBrush", {
                    "faceColor": "none",
                    "hatchColor": "#FF000000",
                    "alpha": "0",
                })
            elements.append(bf)

    return elements, role_to_id


def _build_table_xml(model: dict, role_to_id: dict, tbl_id: int):
    total_cols = model["cols"]
    total_width = 50333
    unit_col_width = total_width // total_cols

    tbl = ET.Element(HP + "tbl", {
        "id": str(tbl_id),
        "zOrder": "0",
        "numberingType": "Table",
        "textWrap": "TopAndBottom",
        "textFlow": "BothSides",
        "lock": "0",
        "dropcapstyle": "None",
        "rowCnt": str(model["rows"]),
        "colCnt": str(model["cols"]),
    })
    ET.SubElement(tbl, HP + "sz", {"width": str(total_width), "height": "10000"})
    ET.SubElement(tbl, HP + "pos", {"treatAsChar": "0", "affectLSpacing": "0", "flowWithText": "1",
                                    "allowOverlap": "0", "holdAnchorAndSO": "0", "vertRelTo": "para",
                                    "horzRelTo": "para", "vertAlign": "top", "horzAlign": "left",
                                    "vertOffset": "0", "horzOffset": "0"})
    ET.SubElement(tbl, HP + "outMargin", {"left": "0", "right": "0", "top": "0", "bottom": "0"})
    ET.SubElement(tbl, HP + "inMargin", {"left": "510", "right": "510", "top": "141", "bottom": "141"})

    for r_idx, row_cells in enumerate(model["cells"]):
        tr = ET.SubElement(tbl, HP + "tr")
        for col, colSpan, rowSpan, text, role, has_fill in row_cells:
            bid = role_to_id.get((role, has_fill), "1")
            width = unit_col_width * colSpan
            tc = ET.SubElement(tr, HP + "tc", {
                "name": "",
                "header": "0",
                "hasMargin": "0",
                "protect": "0",
                "editable": "0",
                "dirty": "0",
                "borderFillIDRef": bid,
            })
            ET.SubElement(tc, HP + "cellAddr", {"rowAddr": str(r_idx), "colAddr": str(col)})
            ET.SubElement(tc, HP + "cellSpan", {"rowSpan": str(rowSpan), "colSpan": str(colSpan)})
            ET.SubElement(tc, HP + "cellSz", {"width": str(width), "height": "1500"})
            sub_list = ET.SubElement(tc, HP + "subList", {
                "id": "",
                "textDirection": "0",
                "lineWrap": "Break",
                "vertAlign": "center",
                "linkListIDRef": "0",
                "linkListNextIDRef": "0",
            })
            p = ET.SubElement(sub_list, HP + "p", {"id": "0", "paraPrIDRef": "0", "styleIDRef": "0", "pageBreak": "0", "columnBreak": "0"})
            run = ET.SubElement(p, HP + "run", {"charPrIDRef": "0"})
            if text:
                t_el = ET.SubElement(run, HP + "t")
                t_el.text = text

    return tbl


def make_org_catalog(destination: Path, *, profiles: tuple[str, ...] = ("six_even_4", "six_odd_5", "five_even_6", "six_irregular_3")) -> Path:
    dest_path = Path(destination)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(SOURCE, "r") as src_zip:
        header_xml_bytes = src_zip.read("Contents/header.xml")
        section0_xml_bytes = src_zip.read("Contents/section0.xml")
        file_entries = {info.filename: src_zip.read(info.filename)
                        for info in src_zip.infolist()
                        if not info.filename.startswith("Contents/section")}

    header_root = ET.fromstring(header_xml_bytes)
    border_fills_parent = header_root.find(".//" + HH + "borderFills")
    if border_fills_parent is None:
        border_fills_parent = ET.SubElement(header_root, HH + "borderFills")

    existing_ids = [int(bf.get("id", "0")) for bf in border_fills_parent.findall(HH + "borderFill")]
    start_id = max(existing_ids, default=0) + 1

    new_bfs, role_to_id = _build_border_fill_elements(start_id)
    for bf in new_bfs:
        border_fills_parent.append(bf)
    border_fills_parent.set("itemCnt", str(len(border_fills_parent.findall(HH + "borderFill"))))

    # section0 조립
    sec0_root = ET.fromstring(section0_xml_bytes)
    sec_pr_p = None
    for p in sec0_root.findall(HP + "p"):
        if p.find(".//" + HP + "secPr") is not None:
            sec_pr_p = copy.deepcopy(p)
            # secPr 내부의 기존 표 제거
            for tbl in list(sec_pr_p.iter(HP + "tbl")):
                for parent in sec_pr_p.iter():
                    if tbl in list(parent):
                        parent.remove(tbl)
            break

    sec0_root.clear()
    if sec_pr_p is not None:
        sec0_root.append(sec_pr_p)

    # #조직도 카테고리 헤더 문단
    cat_p = ET.SubElement(sec0_root, HP + "p", {"id": "1", "paraPrIDRef": "0", "styleIDRef": "0"})
    cat_run = ET.SubElement(cat_p, HP + "run", {"charPrIDRef": "0"})
    cat_t = ET.SubElement(cat_run, HP + "t")
    cat_t.text = "#조직도"

    tbl_counter = 100
    for prof_key in profiles:
        model = _FIXTURE_MODELS[prof_key]
        tbl_counter += 1
        tbl = _build_table_xml(model, role_to_id, tbl_counter)
        tbl_p = ET.SubElement(sec0_root, HP + "p", {"id": str(tbl_counter), "paraPrIDRef": "0", "styleIDRef": "0"})
        tbl_run = ET.SubElement(tbl_p, HP + "run", {"charPrIDRef": "0"})
        tbl_run.append(tbl)

    new_header_bytes = ET.tostring(header_root, encoding="utf-8")
    new_sec0_bytes = ET.tostring(sec0_root, encoding="utf-8")

    with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as dest_zip:
        for name, data in file_entries.items():
            dest_zip.writestr(name, data)
        dest_zip.writestr("Contents/header.xml", new_header_bytes)
        dest_zip.writestr("Contents/section0.xml", new_sec0_bytes)

    return dest_path
