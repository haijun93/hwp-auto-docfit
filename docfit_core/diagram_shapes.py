"""다이어그램(흐름도) 스냅샷을 한/글 '도형'(hp:container, hp:rect, hp:ellipse, hp:polygon, hp:line) HWPX로 변환한다.

순수 파이썬으로 동작하며 COM이나 외부 GUI가 필요하지 않습니다.
XML 파싱과 생성에는 defusedxml만 사용합니다.
"""

from __future__ import annotations

import copy
import math
import re
import zipfile
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as ET

from . import table_catalog as catalog

HP = catalog._HP
HH = catalog._HH
HC = catalog._HC

# 96 DPI 화면 기준: 1인치 = 96px = 7200 HWPUNIT -> 1px = 75 HWPUNIT
PX_TO_HWPUNIT = 75
MM_TO_HWPUNIT = 283.465


def _add(parent: Any, tag: str, **attrs: Any) -> Any:
    node = parent.makeelement(tag, {k: str(v) for k, v in attrs.items()})
    parent.append(node)
    return node


def _parse_hex_color(val: Any, default: str = "#000000") -> str:
    if isinstance(val, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", val.strip()):
        return val.strip().upper()
    return default


def _node_geometry(node: dict[str, Any]) -> tuple[float, float, float, float]:
    """노드의 (x, y, w, h)를 픽셀 단위로 추출."""
    pos = node.get("position", {})
    x = float(pos.get("x", 0))
    y = float(pos.get("y", 0))

    # 너비·높이 추출
    w = 120.0
    h = 60.0
    style = node.get("style", {})
    if isinstance(style, dict):
        if "width" in style:
            try:
                w = float(str(style["width"]).replace("px", "").strip())
            except ValueError:
                pass
        if "height" in style:
            try:
                h = float(str(style["height"]).replace("px", "").strip())
            except ValueError:
                pass

    data = node.get("data", {})
    if isinstance(data, dict):
        if "width" in data:
            try:
                w = float(data["width"])
            except (ValueError, TypeError):
                pass
        if "height" in data:
            try:
                h = float(data["height"])
            except (ValueError, TypeError):
                pass

    if "width" in node:
        try:
            w = float(node["width"])
        except (ValueError, TypeError):
            pass
    if "height" in node:
        try:
            h = float(node["height"])
        except (ValueError, TypeError):
            pass

    return x, y, max(10.0, w), max(10.0, h)


def _build_draw_text(parent: Any, text: str, width_unit: int, height_unit: int,
                     para_id: str = "1", char_id: str = "1") -> Any:
    """도형 안 글자(hp:drawText) 블록을 생성한다."""
    dt = _add(parent, HP + "drawText", lastWidth=str(width_unit), name="", editable="0")
    sub_list = _add(dt, HP + "subList",
                    textDirection="HORIZONTAL", lineWrap="BREAK", vertAlign="CENTER",
                    linkListIDRef="0", linkNextIDRef="0", textWidth="0", textHeight="0")

    lines = text.split("\n") if text else [""]
    for idx, line in enumerate(lines):
        p = _add(sub_list, HP + "p",
                 id=str(500000 + idx), paraPrIDRef=para_id, styleIDRef="0",
                 pageBreak="0", columnBreak="0", merged="0")
        run = _add(p, HP + "run", charPrIDRef=char_id)
        t_el = _add(run, HP + "t")
        t_el.text = line

    _add(dt, HP + "textMargin", left="283", right="283", top="283", bottom="283")
    return dt


def build_shape_element(node: dict[str, Any], shape_id: int, z_order: int,
                        offset_x: int, offset_y: int,
                        para_id: str = "1", char_id: str = "1") -> Any:
    """개별 노드를 한/글 자식 도형 XML 요소로 조립한다."""
    _, _, w_px, h_px = _node_geometry(node)
    w_unit = round(w_px * PX_TO_HWPUNIT)
    h_unit = round(h_px * PX_TO_HWPUNIT)

    node_type = str((node.get("data") or {}).get("shape", node.get("type", "rect"))).lower()
    data = node.get("data", {}) if isinstance(node.get("data"), dict) else {}
    style = node.get("style", {}) if isinstance(node.get("style"), dict) else {}

    label = str(data.get("label", node.get("label", "")))
    fill_color = _parse_hex_color(style.get("background", style.get("backgroundColor", data.get("fill", data.get("fillColor", "#FFFFFF")))), "#FFFFFF")
    border_color = _parse_hex_color(style.get("borderColor", data.get("stroke", data.get("lineColor", "#000000"))), "#000000")

    # 선 굵기
    border_width = 33  # 약 0.12mm (33 / 7200 inch)
    if "borderWidth" in style:
        try:
            bw = float(str(style["borderWidth"]).replace("px", "").strip())
            border_width = max(10, round(bw * 33))
        except ValueError:
            pass

    # 태그 결정: rect, ellipse, polygon
    if "circle" in node_type or "ellipse" in node_type:
        elem_tag = HP + "ellipse"
    elif "diamond" in node_type or "rhombus" in node_type:
        elem_tag = HP + "polygon"
    else:
        elem_tag = HP + "rect"

    dummy_parent = ET.fromstring("<wrapper/>")
    shape = _add(dummy_parent, elem_tag,
                 id=str(shape_id), zOrder=str(z_order),
                 numberingType="NONE", textWrap="TOP_AND_BOTTOM",
                 lock="0", dropCapStyle="None")

    # 묶음 자식 속성
    shape.set("groupLevel", "1")

    _add(shape, HP + "offset", x=str(offset_x), y=str(offset_y))
    _add(shape, HP + "orgSz", width=str(w_unit), height=str(h_unit))
    _add(shape, HP + "curSz", width=str(w_unit), height=str(h_unit))

    # 도형별 기하 구조
    if elem_tag == HP + "rect":
        ratio = "20" if ("round" in node_type or style.get("borderRadius")) else "0"
        shape.set("ratio", ratio)
        _add(shape, HC + "pt0", x="0", y="0")
        _add(shape, HC + "pt1", x=str(w_unit), y="0")
        _add(shape, HC + "pt2", x=str(w_unit), y=str(h_unit))
        _add(shape, HC + "pt3", x="0", y=str(h_unit))
    elif elem_tag == HP + "ellipse":
        shape.set("intervalDirty", "0")
        shape.set("hasArcPr", "0")
        shape.set("arcType", "NORMAL")
        cx = w_unit // 2
        cy = h_unit // 2
        _add(shape, HC + "center", x=str(cx), y=str(cy))
        _add(shape, HC + "ax1", x=str(w_unit), y=str(cy))
        _add(shape, HC + "ax2", x=str(cx), y=str(h_unit))
        _add(shape, HC + "startPt1", x=str(w_unit), y=str(cy))
        _add(shape, HC + "endPt1", x=str(w_unit), y=str(cy))
        _add(shape, HC + "startPt2", x="0", y="0")
        _add(shape, HC + "endPt2", x="0", y="0")
    elif elem_tag == HP + "polygon":
        cx = w_unit // 2
        cy = h_unit // 2
        _add(shape, HC + "pt0", x=str(cx), y="0")
        _add(shape, HC + "pt1", x=str(w_unit), y=str(cy))
        _add(shape, HC + "pt2", x=str(cx), y=str(h_unit))
        _add(shape, HC + "pt3", x="0", y=str(cy))

    # 선 모양 및 채우기
    _add(shape, HP + "lineShape",
         color=border_color, width=str(border_width), style="SOLID",
         headStyle="NORMAL", tailStyle="NORMAL", headSz="SMALL", tailSz="SMALL",
         outlineStyle="NORMAL", alpha="0")

    fill_brush = _add(shape, HC + "fillBrush")
    _add(fill_brush, HC + "winBrush", faceColor=fill_color, hatchColor="#FF000000", alpha="0")

    # 텍스트가 있으면 hp:drawText 추가
    if label:
        _build_draw_text(shape, label, w_unit, h_unit, para_id, char_id)

    # renderingInfo
    rend = _add(shape, HP + "renderingInfo")
    _add(rend, HC + "transMatrix", e1="1", e2="0", e3=str(offset_x), e4="0", e5="1", e6=str(offset_y))
    _add(rend, HC + "scaMatrix", e1="1", e2="0", e3="0", e4="0", e5="1", e6="0")
    _add(rend, HC + "rotMatrix", e1="1", e2="0", e3="0", e4="0", e5="1", e6="0")

    return shape


def build_edge_element(edge: dict[str, Any], edge_id: int, z_order: int,
                       nodes_by_id: dict[str, dict[str, Any]],
                       base_min_x: float, base_min_y: float) -> Any:
    """연결선(edge)을 한/글 선(hp:line) 요소로 조립한다."""
    src_id = str(edge.get("source", ""))
    tgt_id = str(edge.get("target", ""))

    src_node = nodes_by_id.get(src_id)
    tgt_node = nodes_by_id.get(tgt_id)

    if src_node and tgt_node:
        sx, sy, sw, sh = _node_geometry(src_node)
        tx, ty, tw, th = _node_geometry(tgt_node)
        # 중심점 연결
        p1_x = sx + sw / 2.0
        p1_y = sy + sh / 2.0
        p2_x = tx + tw / 2.0
        p2_y = ty + th / 2.0
    else:
        p1_x = 0.0
        p1_y = 0.0
        p2_x = 100.0
        p2_y = 100.0

    # 묶음 기준 상대 좌표
    u_x1 = round((p1_x - base_min_x) * PX_TO_HWPUNIT)
    u_y1 = round((p1_y - base_min_y) * PX_TO_HWPUNIT)
    u_x2 = round((p2_x - base_min_x) * PX_TO_HWPUNIT)
    u_y2 = round((p2_y - base_min_y) * PX_TO_HWPUNIT)

    min_x = min(u_x1, u_x2)
    min_y = min(u_y1, u_y2)
    w_unit = max(10, abs(u_x2 - u_x1))
    h_unit = max(10, abs(u_y2 - u_y1))

    dummy = ET.fromstring("<wrapper/>")
    line = _add(dummy, HP + "line",
                id=str(edge_id), zOrder=str(z_order),
                numberingType="NONE", textWrap="TOP_AND_BOTTOM",
                lock="0", dropCapStyle="None", isReverseHV="0")
    line.set("groupLevel", "1")

    _add(line, HP + "offset", x=str(min_x), y=str(min_y))
    _add(line, HP + "orgSz", width=str(w_unit), height=str(h_unit))
    _add(line, HP + "curSz", width=str(w_unit), height=str(h_unit))

    _add(line, HC + "startPt", x=str(u_x1 - min_x), y=str(u_y1 - min_y))
    _add(line, HC + "endPt", x=str(u_x2 - min_x), y=str(u_y2 - min_y))

    # 화살표 스타일
    has_arrow = bool(edge.get("markerEnd") or edge.get("arrow"))
    head_style = "ARROW" if has_arrow else "NORMAL"

    _add(line, HP + "lineShape",
         color="#000000", width="33", style="SOLID",
         headStyle=head_style, tailStyle="NORMAL", headSz="MEDIUM", tailSz="SMALL",
         outlineStyle="NORMAL", alpha="0")

    rend = _add(line, HP + "renderingInfo")
    _add(rend, HC + "transMatrix", e1="1", e2="0", e3=str(min_x), e4="0", e5="1", e6=str(min_y))
    _add(rend, HC + "scaMatrix", e1="1", e2="0", e3="0", e4="0", e5="1", e6="0")
    _add(rend, HC + "rotMatrix", e1="1", e2="0", e3="0", e4="0", e5="1", e6="0")

    return line


def diagram_to_hwpx(snapshot: dict[str, Any], output_path: str | Path) -> Path:
    """React Flow snapshot을 한/글 '도형' 개체들이 포함된 HWPX 문서로 생성한다."""
    if not isinstance(snapshot, dict):
        raise ValueError("다이어그램 데이터 형식이 올바르지 않습니다.")

    nodes = snapshot.get("nodes", [])
    edges = snapshot.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("노드 또는 연결선 목록을 확인해 주세요.")

    if not nodes:
        raise ValueError("다이어그램에 최소 1개 이상의 도형이 필요합니다.")

    target = Path(output_path)
    source = catalog.default_catalog_path()
    if target.resolve() == source.resolve() or target.suffix.lower() != ".hwpx":
        raise ValueError("올바른 .hwpx 대상 파일 경로를 지정해 주세요.")

    # 전체 바운딩 박스 계산 (px 단위)
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    nodes_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        nid = str(node.get("id", ""))
        nodes_by_id[nid] = node
        x, y, w, h = _node_geometry(node)
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x + w)
        max_y = max(max_y, y + h)

    total_w_px = max(100.0, max_x - min_x)
    total_h_px = max(60.0, max_y - min_y)
    total_w_unit = round(total_w_px * PX_TO_HWPUNIT)
    total_h_unit = round(total_h_px * PX_TO_HWPUNIT)

    record = catalog._scan(source)[0]
    with catalog._safe_archive(source) as archive:
        section_data = archive.read(record["section"])
        section = ET.fromstring(section_data)

        header_data = archive.read("Contents/header.xml")
        header = ET.fromstring(header_data)
        refs = header.find(HH + "refList")

        # 스타일 정의 함수
        def definition(group, tag, node):
            parent = refs.find(HH + group)
            ident = str(max((int(n.get("id", "0")) for n in parent), default=0) + 1)
            node.set("id", ident)
            parent.append(node)
            parent.set("itemCnt", str(len(parent)))
            return ident

        # 가운데 정렬 문단 모양
        para_node = copy.deepcopy(refs.find(HH + "paraProperties")[0])
        para_node.find(HH + "align").set("horizontal", "CENTER")
        for n in para_node.iter():
            if n.tag.rsplit("}", 1)[-1] in ("intent", "left", "right", "prev", "next") and "value" in n.attrib:
                n.set("value", "0")
        center_para_id = definition("paraProperties", "paraPr", para_node)

        # 기본 본문 글자 모양 (10pt 한컴돋움)
        char_node = copy.deepcopy(refs.find(HH + "charProperties")[0])
        char_node.set("height", "1000")
        basic_char_id = definition("charProperties", "charPr", char_node)

        # 컨테이너 요소 생성
        dummy = ET.fromstring("<wrapper/>")
        container = _add(dummy, HP + "container",
                         id="10000", zOrder="0",
                         numberingType="NONE", textWrap="TOP_AND_BOTTOM",
                         lock="0", dropCapStyle="None")
        container.set("groupLevel", "0")

        _add(container, HP + "orgSz", width=str(total_w_unit), height=str(total_h_unit))
        _add(container, HP + "curSz", width=str(total_w_unit), height=str(total_h_unit))

        rend = _add(container, HP + "renderingInfo")
        _add(rend, HC + "transMatrix", e1="1", e2="0", e3="0", e4="0", e5="1", e6="0")
        _add(rend, HC + "scaMatrix", e1="1", e2="0", e3="0", e4="0", e5="1", e6="0")
        _add(rend, HC + "rotMatrix", e1="1", e2="0", e3="0", e4="0", e5="1", e6="0")

        # 자식 도형들 추가
        curr_id = 1
        curr_z = 0
        for node in nodes:
            nx, ny, _, _ = _node_geometry(node)
            rel_x = round((nx - min_x) * PX_TO_HWPUNIT)
            rel_y = round((ny - min_y) * PX_TO_HWPUNIT)
            shape_el = build_shape_element(node, curr_id, curr_z, rel_x, rel_y,
                                           center_para_id, basic_char_id)
            container.append(shape_el)
            curr_id += 1
            curr_z += 1

        # 자식 연결선들 추가
        for edge in edges:
            edge_el = build_edge_element(edge, curr_id, curr_z, nodes_by_id, min_x, min_y)
            container.append(edge_el)
            curr_id += 1
            curr_z += 1

        # 컨테이너 본체 위치 및 크기 속성 (자식들 뒤에 배치)
        _add(container, HP + "sz", width=str(total_w_unit), height=str(total_h_unit))
        # 페이지 상단 좌측 기준 배치 (여백 1000 HWPUNIT)
        _add(container, HP + "pos",
             treatAsChar="0", affectLSpacing="0", flowWithText="0", allowOverlap="1",
             holdAnchorAndSO="0", vertRelTo="PAPER", horzRelTo="PAPER",
             vertAlign="TOP", horzAlign="LEFT", vertOffset="1000", horzOffset="1000")
        _add(container, HP + "outMargin", left="0", right="0", top="0", bottom="0")
        _add(container, HP + "shapeComment").text = "묶음 개체입니다."

        # section0.xml에 문단 만들고 컨테이너 넣기
        p_container = section.makeelement(HP + "p", dict(id="200000", paraPrIDRef=center_para_id, styleIDRef="0",
                                 pageBreak="0", columnBreak="0", merged="0"))
        run_el = _add(p_container, HP + "run", charPrIDRef=basic_char_id)
        run_el.append(container)

        # 기존 표나 본문 대신 컨테이너 문단으로 교체
        properties = catalog._section_properties_paragraph(section)
        section[:] = [n for n in (properties, p_container) if n is not None]

        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for info in archive.infolist():
                if info.filename == record["section"]:
                    data = ET.tostring(section, encoding="utf-8", xml_declaration=True)
                elif info.filename == "Contents/header.xml":
                    data = ET.tostring(header, encoding="utf-8", xml_declaration=True)
                elif info.filename in catalog._section_names(archive):
                    other = ET.fromstring(archive.read(info.filename))
                    prop = catalog._section_properties_paragraph(other)
                    other[:] = [] if prop is None else [prop]
                    data = ET.tostring(other, encoding="utf-8", xml_declaration=True)
                else:
                    data = archive.read(info.filename)
                output.writestr(info, data)

    return target


# 별칭 제공
convert_diagram_to_hwpx = diagram_to_hwpx
