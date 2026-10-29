"""격자 선 그림을 병합 표와 HWPX로 변환한다. COM을 사용하지 않는다."""
from __future__ import annotations

import base64
import binascii
import copy
import math
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from . import table_catalog as catalog

HP = catalog._HP
HH = catalog._HH
HC = catalog._HC
# 칸 배경 그림(2026-10-30 사용자 요청): 그림 하나 8MB, 그림 수 100개까지.
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGES = 100


def _image_kind(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    return None


def _clean_images(images, cols, rows, warnings):
    if images is None:
        return []
    if not isinstance(images, list) or len(images) > MAX_IMAGES:
        raise ValueError(f"칸 그림은 {MAX_IMAGES}개까지 넣을 수 있습니다.")
    clean, seen = [], set()
    for i, item in enumerate(images):
        try:
            x, y, encoded = item["x"], item["y"], item["data"]
            if type(x) is not int or type(y) is not int or not (0 <= x < cols and 0 <= y < rows) or not isinstance(encoded, str):
                raise ValueError
            if encoded.startswith("data:"):
                encoded = encoded.split(",", 1)[1]
            if len(encoded) > MAX_IMAGE_BYTES * 4 // 3 + 8:
                raise ValueError
            data = base64.b64decode(encoded, validate=True)
            kind = _image_kind(data)
            if kind is None or len(data) > MAX_IMAGE_BYTES or (x, y) in seen:
                raise ValueError
            seen.add((x, y))
            clean.append(dict(x=x, y=y, data=encoded, kind=kind))
        except (TypeError, KeyError, ValueError, binascii.Error):
            warnings.append(f"칸 그림 {i+1}: PNG·JPG가 아니거나 위치·크기가 잘못되어 제외했습니다.")
    return clean
UNIT_MM = 283.465
NONE = ("none", "solid")


def normalize(sketch):
    if not isinstance(sketch, dict) or not isinstance(sketch.get("grid"), dict):
        raise ValueError("격자와 그림 데이터를 확인해 주세요.")
    grid = sketch["grid"]
    cols, rows, mm = grid.get("cols"), grid.get("rows"), grid.get("cell_mm", 5.0)
    if (type(cols) is not int or type(rows) is not int or not 1 <= cols <= 200 or
            not 1 <= rows <= 200 or isinstance(mm, bool) or not isinstance(mm, (int, float)) or
            not math.isfinite(mm) or not 0.5 <= mm <= 50):
        raise ValueError("격자는 1~200칸, 칸 간격은 0.5~50mm로 지정해 주세요.")
    raw = sketch.get("lines", [])
    texts = sketch.get("texts", [])
    if not isinstance(raw, list) or len(raw) > 10000 or not isinstance(texts, list) or len(texts) > 10000:
        raise ValueError("선·글 데이터가 너무 많거나 형식이 잘못되었습니다.")
    groups, warnings = {}, []
    for i, line in enumerate(raw):
        try:
            x1, y1, x2, y2 = (line[k] for k in ("x1", "y1", "x2", "y2"))
            width, style = line.get("width", "thin"), line.get("style", "solid")
            if (any(type(v) is not int for v in (x1, y1, x2, y2)) or
                    not (0 <= x1 <= cols and 0 <= x2 <= cols and 0 <= y1 <= rows and 0 <= y2 <= rows) or
                    (x1, y1) == (x2, y2) or
                    not (x1 == x2 or y1 == y2 or abs(x2-x1) == abs(y2-y1)) or
                    width not in ("thin", "thick", "double") or style not in ("solid", "dash", "dot")):
                raise ValueError
            if (x2, y2) < (x1, y1):
                x1, y1, x2, y2 = x2, y2, x1, y1
            kind = "v" if x1 == x2 else "h" if y1 == y2 else "b" if y2 > y1 else "s"
            intercept = x1 if kind == "v" else y1 if kind == "h" else y1-x1 if kind == "b" else y1+x1
            start, end = (y1, y2) if kind == "v" else (x1, x2)
            groups.setdefault((kind, intercept, width, style), []).append((start, end))
        except (TypeError, KeyError, ValueError):
            warnings.append(f"선 {i+1}: 격자 밖·0길이·잘못된 좌표/기울기/서식을 제외했습니다.")
    lines = []
    for (kind, intercept, width, style), intervals in sorted(groups.items()):
        merged = []
        for start, end in sorted(intervals):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(end, merged[-1][1])
            else:
                merged.append([start, end])
        for start, end in merged:
            point = lambda t: (intercept, t) if kind == "v" else (t, intercept if kind == "h" else t+intercept if kind == "b" else intercept-t)
            x1, y1 = point(start)
            x2, y2 = point(end)
            lines.append(dict(x1=x1, y1=y1, x2=x2, y2=y2, width=width, style=style))
    clean_texts = []
    for i, item in enumerate(texts):
        if (not isinstance(item, dict) or type(item.get("x")) is not int or type(item.get("y")) is not int or
                not 0 <= item["x"] < cols or not 0 <= item["y"] < rows or
                not isinstance(item.get("text"), str) or len(item["text"]) > 10000 or
                any(ord(ch) < 32 and ch not in "\n\t\r" for ch in item["text"]) or
                type(item.get("bold", False)) is not bool or item.get("align", "center") not in ("left", "center", "right")):
            warnings.append(f"글 {i+1}: 위치나 서식이 잘못되어 제외했습니다.")
        else:
            clean_texts.append({**item, "bold": item.get("bold", False), "align": item.get("align", "center")})
    images = _clean_images(sketch.get("images"), cols, rows, warnings)
    return dict(grid=dict(cols=cols, rows=rows, cell_mm=float(mm)), lines=lines, texts=clean_texts, images=images), warnings


def _layout(sketch, _split_lines=()):
    drawing, warnings = normalize(sketch)
    lines = drawing["lines"]
    if not lines:
        return dict(ok=True, rows=0, cols=0, cells=[], width_mm=0, height_mm=0,
                    warnings=warnings + ["표로 만들 선을 그려 주세요."], x_coords=[], y_coords=[])
    xs = sorted({v for l in lines for v in (l["x1"], l["x2"])})
    ys = sorted({v for l in lines for v in (l["y1"], l["y2"])})
    if len(xs) < 2 or len(ys) < 2:
        return dict(ok=True, rows=0, cols=0, cells=[], width_mm=(xs[-1]-xs[0])*drawing["grid"]["cell_mm"],
                    height_mm=(ys[-1]-ys[0])*drawing["grid"]["cell_mm"], warnings=warnings+["표는 가로·세로 범위가 필요합니다."], x_coords=xs, y_coords=ys)
    horizontal = [l for l in lines if l["y1"] == l["y2"]]
    vertical = [l for l in lines if l["x1"] == l["x2"]]
    diagonals = [l for l in lines if l not in horizontal and l not in vertical]
    # 겹친 다른 서식은 굵은 선 우선, 같은 굵기는 solid > dash > dot.
    rank = lambda s: (("none", "thin", "thick", "double").index(s[0]), ("dot", "dash", "solid").index(s[1]))
    def edge(kind, fixed, start, end):
        candidates = [(l["width"], l["style"]) for l in (horizontal if kind == "h" else vertical)
                      if (l["y1"] if kind == "h" else l["x1"]) == fixed and
                      (l["x1"] if kind == "h" else l["y1"]) <= start and
                      (l["x2"] if kind == "h" else l["y2"]) >= end]
        return max(candidates, key=rank, default=NONE)
    def bounds(region):
        rr, cc = zip(*region)
        return min(rr), min(cc), max(rr)+1, max(cc)+1
    def sides(r, c, re, ce):
        return dict(top=[edge("h", ys[r], xs[k], xs[k+1]) for k in range(c, ce)],
                    bottom=[edge("h", ys[re], xs[k], xs[k+1]) for k in range(c, ce)],
                    left=[edge("v", xs[c], ys[k], ys[k+1]) for k in range(r, re)],
                    right=[edge("v", xs[ce], ys[k], ys[k+1]) for k in range(r, re)])
    def rectangular(region):
        r, c, re, ce = bounds(region)
        if len(region) != (re-r)*(ce-c):
            return False
        # 끝이 막히지 않은 내부 선도 병합으로 지우지 않는다.
        return (not any(edge("h", ys[j], xs[k], xs[k+1]) != NONE for j in range(r+1, re) for k in range(c, ce)) and
                not any(edge("v", xs[k], ys[j], ys[j+1]) != NONE for k in range(c+1, ce) for j in range(r, re)) and
                all(len(set(v)) == 1 for v in sides(r, c, re, ce).values()))
    def components(blocked):
        unseen = {(r, c) for r in range(len(ys)-1) for c in range(len(xs)-1)}
        result = []
        while unseen:
            seed = min(unseen)
            unseen.remove(seed)
            region, stack = {seed}, [seed]
            while stack:
                r, c = stack.pop()
                for other, boundary in (((r-1, c), edge("h", ys[r], xs[c], xs[c+1])),
                                        ((r+1, c), edge("h", ys[r+1], xs[c], xs[c+1])),
                                        ((r, c-1), edge("v", xs[c], ys[r], ys[r+1])),
                                        ((r, c+1), edge("v", xs[c+1], ys[r], ys[r+1]))):
                    if other in unseen and boundary == NONE and (r, c) not in blocked and other not in blocked:
                        unseen.remove(other)
                        region.add(other)
                        stack.append(other)
            result.append(region)
        return result
    initial = components(set())
    candidates = [bounds(g) for g in initial if rectangular(g)]
    def corner(l, box):
        r, c, re, ce = box
        return ((l["x1"], l["y1"]), (l["x2"], l["y2"])) in (
            ((xs[c], ys[r]), (xs[ce], ys[re])), ((xs[c], ys[re]), (xs[ce], ys[r])))
    split = [l for l in diagonals if l in _split_lines or not any(corner(l, box) for box in candidates)]
    # 중간 대각선은 원래 종이의 1칸마다 꼭짓점을 만들어 정확한 45도 선으로 남긴다.
    for l in split:
        xs = sorted(set(xs) | set(range(l["x1"], l["x2"]+1)))
        ys = sorted(set(ys) | set(range(min(l["y1"], l["y2"]), max(l["y1"], l["y2"])+1)))
    # 다른 경계가 대각선을 자르면 반대 축에도 교점을 추가한다.
    while True:
        new_x, new_y = set(xs), set(ys)
        for l in diagonals:
            slope = 1 if l["y2"] > l["y1"] else -1
            new_y.update(l["y1"]+slope*(x-l["x1"]) for x in xs if l["x1"] <= x <= l["x2"])
            new_x.update(l["x1"]+slope*(y-l["y1"]) for y in ys if min(l["y1"],l["y2"]) <= y <= max(l["y1"],l["y2"]))
        if new_x == set(xs) and new_y == set(ys):
            break
        xs, ys = sorted(new_x), sorted(new_y)
    def diag_in(l, box):
        r, c, re, ce = box
        midx, midy = (xs[c]+xs[ce])/2, (ys[r]+ys[re])/2
        slope = 1 if l["y2"] > l["y1"] else -1
        return l["x1"] < midx < l["x2"] and ys[r] < l["y1"]+slope*(midx-l["x1"]) < ys[re]
    blocked = {(r,c) for r in range(len(ys)-1) for c in range(len(xs)-1)
               if any(diag_in(l, (r,c,r+1,c+1)) for l in split)}
    boxes = []
    for region in components(blocked):
        boxes.extend([bounds(region)] if rectangular(region) else [(r,c,r+1,c+1) for r,c in sorted(region)])
    # 다른 대각선의 분할로 큰 칸이 깨졌으면 기존 꼭짓점 대각선도 분할해야 한다.
    additional = [l for l in diagonals if l not in split and not any(corner(l, box) for box in boxes)]
    if additional:
        return _layout(sketch, split + additional)
    cells = []
    for r,c,re,ce in boxes:
        border = {k:v[0] for k,v in sides(r,c,re,ce).items()}
        ds = {}
        for l in diagonals:
            if corner(l, (r,c,re,ce)) or (l in split and diag_in(l,(r,c,re,ce))):
                direction = "backslash" if l["y2"] > l["y1"] else "slash"
                ds[direction] = max(ds.get(direction, NONE), (l["width"],l["style"]), key=rank)
        cell = dict(row=r, col=c, rowspan=re-r, colspan=ce-c,
                    borders={k:v[0] for k,v in border.items()}, border_styles={k:v[1] for k,v in border.items()},
                    diagonal="cross" if len(ds)==2 else next(iter(ds), "none"), text="", texts=[], diagonal_styles=ds)
        for t in drawing["texts"]:
            if xs[c] <= t["x"] < xs[ce] and ys[r] <= t["y"] < ys[re]:
                cell["texts"].append(t)
        cell["text"] = "\n".join(t["text"] for t in cell["texts"])
        # 칸 배경 그림: 칸 안에 놓인 첫 그림(번호만 싣고 그림 자료는 drawing["images"]에 둔다).
        for k, image in enumerate(drawing["images"]):
            if xs[c] <= image["x"] < xs[ce] and ys[r] <= image["y"] < ys[re]:
                cell["image"] = k
                break
        cells.append(cell)
    for t in drawing["texts"]:
        if not xs[0] <= t["x"] < xs[-1] or not ys[0] <= t["y"] < ys[-1]:
            warnings.append("표 범위 밖의 글을 제외했습니다.")
    for image in drawing["images"]:
        if not xs[0] <= image["x"] < xs[-1] or not ys[0] <= image["y"] < ys[-1]:
            warnings.append("표 범위 밖의 칸 그림을 제외했습니다.")
    mm = drawing["grid"]["cell_mm"]
    return dict(ok=True, rows=len(ys)-1, cols=len(xs)-1, cells=sorted(cells,key=lambda c:(c["row"],c["col"])),
                width_mm=(xs[-1]-xs[0])*mm, height_mm=(ys[-1]-ys[0])*mm,
                warnings=warnings, x_coords=xs, y_coords=ys)


def preview(sketch):
    return _layout(sketch)


def _add(parent, tag, **attrs):
    node = parent.makeelement(tag, {k:str(v) for k,v in attrs.items()})
    parent.append(node)
    return node


def to_hwpx(sketch, path):
    result = _layout(sketch)
    images = normalize(sketch)[0]["images"]
    if not result["cells"]:
        raise ValueError("표로 만들 가로·세로 범위가 필요합니다.")
    target = Path(path)
    source = catalog.default_catalog_path()
    if target.resolve() == source.resolve() or target.suffix.lower() != ".hwpx":
        raise ValueError("새 .hwpx 파일 경로를 지정해 주세요.")
    record = catalog._scan(source)[0]
    # 기존 표 템플릿 서비스와 동일한 문서 바탕·구역 속성을 재사용한다.
    with catalog._safe_archive(source) as archive:
        section_data = archive.read(record["section"])
        section = ET.fromstring(section_data)
        paragraph = catalog._paragraph_with_table(section.findall(HP+"p")[record["paragraph_index"]], record["table_index"])
        table = catalog._top_tables(paragraph)[0]
        header_data = archive.read("Contents/header.xml")
        header = ET.fromstring(header_data)
        refs = header.find(HH+"refList")
        def definition(group, tag, node):
            parent = refs.find(HH+group)
            ident = str(max((int(n.get("id", "0")) for n in parent), default=0)+1)
            node.set("id", ident)
            parent.append(node)
            parent.set("itemCnt", str(len(parent)))
            return ident
        chars, paras = {}, {}
        for bold in (False, True):
            node = copy.deepcopy(refs.find(HH+"charProperties")[0])
            node.set("height", "1000")
            for n in list(node):
                if n.tag == HH+"bold": node.remove(n)
            if bold: _add(node, HH+"bold")
            chars[bold] = definition("charProperties", "charPr", node)
        for align in ("left", "center", "right"):
            node = copy.deepcopy(refs.find(HH+"paraProperties")[0])
            node.find(HH+"align").set("horizontal", align.upper())
            for n in node.iter():
                if n.tag.rsplit("}",1)[-1] in ("intent", "left", "right", "prev", "next") and "value" in n.attrib:
                    n.set("value", "0")
            paras[align] = definition("paraProperties", "paraPr", node)
        border_cache = {}
        bin_items = {}  # 그림 번호 → (manifest id, 파일 이름, 자료)
        def bin_item(index):
            if index not in bin_items:
                image = images[index]
                ident = f"sketchimg{len(bin_items)+1}"
                bin_items[index] = (ident, f"BinData/{ident}.{image['kind']}", base64.b64decode(image["data"]), image["kind"])
            return bin_items[index][0]
        def border_id(cell):
            key = repr((cell["borders"], cell.get("border_styles"), cell["diagonal"],cell.get("diagonal_styles"), cell.get("image")))
            if key in border_cache: return border_cache[key]
            parent = refs.find(HH+"borderFills")
            node = parent.makeelement(HH+"borderFill", dict(threeD="0",shadow="0",centerLine="NONE",breakCellSeparateLine="0"))
            for name, value in (("slash","slash"),("backSlash","backslash")):
                _add(node, HH+name, type="CENTER" if cell["diagonal"] in (value,"cross") else "NONE", Crooked="0", isCounter="0")
            def line_attrs(width, style):
                return dict(type="NONE" if width=="none" else "DOUBLE_SLIM" if width=="double" else {"solid":"SOLID","dash":"DASH","dot":"DOT"}[style],
                            width={"none":"0.12 mm","thin":"0.12 mm","thick":"0.4 mm","double":"0.5 mm"}[width],color="#000000")
            for side in ("left","right","top","bottom"):
                _add(node, HH+side+"Border", **line_attrs(cell["borders"][side],cell.get("border_styles",{}).get(side,"solid")))
            diag = max(cell.get("diagonal_styles",{}).values(), key=lambda v:("thin","thick","double").index(v[0]), default=("thin","solid"))
            _add(node, HH+"diagonal", **line_attrs(*diag))
            if cell.get("image") is not None:
                # 칸 배경 그림: 크기에 맞추어(TOTAL) 채운다 — 한/글 '셀 테두리/배경 > 그림'과 같다.
                brush = _add(_add(node, HC+"fillBrush"), HC+"imgBrush", mode="TOTAL")
                _add(brush, HC+"img", binaryItemIDRef=bin_item(cell["image"]), bright="0", contrast="0", effect="REAL_PIC", alpha="0")
            border_cache[key] = definition("borderFills", "borderFill", node)
            return border_cache[key]
        invisible = border_id(dict(borders={s:"none" for s in ("top","bottom","left","right")}, diagonal="none"))
        proto = copy.deepcopy(table.find(HP+"tr/"+HP+"tc"))
        for child in list(table):
            if child.tag not in (HP+"sz",HP+"pos",HP+"inMargin",HP+"outMargin"): table.remove(child)
        table.attrib.update(rowCnt=str(result["rows"]), colCnt=str(result["cols"]), borderFillIDRef=invisible, repeatHeader="0", pageBreak="CELL", cellSpacing="0")
        mm = normalize(sketch)[0]["grid"]["cell_mm"]
        xs, ys = result["x_coords"],result["y_coords"]
        ux = [round((x-xs[0])*mm*UNIT_MM) for x in xs]
        uy = [round((y-ys[0])*mm*UNIT_MM) for y in ys]
        table.find(HP+"sz").attrib.update(width=str(ux[-1]),height=str(uy[-1]))
        for tag in ("inMargin","outMargin"):
            table.find(HP+tag).attrib.update({s:"0" for s in ("left","right","top","bottom")})
        row_nodes = [_add(table, HP+"tr") for _ in range(result["rows"])]
        for index, cell in enumerate(result["cells"]):
            r,c,rs,cs = (cell[k] for k in ("row","col","rowspan","colspan"))
            tc = copy.deepcopy(proto)
            tc.attrib.update(borderFillIDRef=border_id(cell),hasMargin="1",header="0")
            sub = tc.find(HP+"subList")
            sub[:] = []
            sub.set("vertAlign", "CENTER")
            for item in cell["texts"] or [dict(text="",bold=False,align="center")]:
                for line in item["text"].split("\n"):
                    p = _add(sub,HP+"p",id=100000+index,paraPrIDRef=paras[item["align"]],styleIDRef="0",pageBreak="0",columnBreak="0",merged="0")
                    run = _add(p,HP+"run",charPrIDRef=chars[item["bold"]])
                    _add(run,HP+"t").text = line
            tc.find(HP+"cellAddr").attrib.update(rowAddr=str(r),colAddr=str(c))
            tc.find(HP+"cellSpan").attrib.update(rowSpan=str(rs),colSpan=str(cs))
            tc.find(HP+"cellSz").attrib.update(width=str(ux[c+cs]-ux[c]),height=str(uy[r+rs]-uy[r]))
            tc.find(HP+"cellMargin").attrib.update({s:str(round(0.5*UNIT_MM)) for s in ("left","right","top","bottom")})
            row_nodes[r].append(tc)
        properties = catalog._section_properties_paragraph(section)
        section[:] = [n for n in (properties,paragraph) if n is not None]
        target.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED) as output:
            for info in archive.infolist():
                if info.filename == record["section"]:
                    data = ET.tostring(section,encoding="utf-8",xml_declaration=True)
                elif info.filename == "Contents/header.xml":
                    data = ET.tostring(header,encoding="utf-8",xml_declaration=True)
                elif info.filename == "Contents/content.hpf" and bin_items:
                    manifest = archive.read(info.filename).decode("utf-8")
                    entries = "".join(
                        f'<opf:item id="{ident}" href="{name}" media-type="image/{"png" if kind == "png" else "jpg"}" isEmbeded="1"/>'
                        for ident, name, _data, kind in bin_items.values())
                    if "</opf:manifest>" not in manifest:
                        raise ValueError("문서 목록(content.hpf)을 찾지 못했습니다.")
                    data = manifest.replace("</opf:manifest>", entries + "</opf:manifest>", 1).encode("utf-8")
                elif info.filename in catalog._section_names(archive):
                    other = ET.fromstring(archive.read(info.filename))
                    prop = catalog._section_properties_paragraph(other)
                    other[:] = [] if prop is None else [prop]
                    data = ET.tostring(other,encoding="utf-8",xml_declaration=True)
                else: data = archive.read(info.filename)
                output.writestr(info,data)
            for _ident, name, data, _kind in bin_items.values():
                output.writestr(name, data)
    return target
