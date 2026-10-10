"""기본 표 서식(준말 '표'의 본말): 예시 표에서 위치별 서식을 배우고 문서의 일반 표에 적용한다.

표의 칸 위치를 행(머리글·첫 본문·본문·마지막)과 열(첫 열·가운데·마지막 열)로 나눠 예시 표의 같은
위치 칸 서식을 옮긴다. 칸마다
- 테두리·바탕: 예시 칸의 테두리/배경(borderFill)을 쓰되, 왼쪽·오른쪽 선은 칸이 놓인 열 위치, 위·아래
  선은 칸이 놓인 행 위치의 예시 칸에서 가져와 크기가 다른 표·병합 칸에서도 바깥선이 맞게 한다.
  칸 배경이 그림(사진 등)이면 칸 내용이므로 선만 바꾸고 그림 채우기는 그대로 둔다.
- 글자: 칸 글자 모양을 복제해 글꼴(언어별)·크기·장평·자간을 예시 값으로 바꾸고, 예시가 굵으면 굵게를
  더한다(글자색·밑줄 같은 강조와 본문 칸의 기존 굵게는 그대로 둔다).
- 정렬: 머리글과 한 줄에 들어가는 짧은 문단만 예시 정렬로 바꾸고, 여러 줄 긴 글은 원래 정렬을 둔다.
  내장 기본값은 본문 칸(2행부터) 가운데 첫 열이 아닌 칸(B2·B3 …)의 문장을 왼쪽 정렬한다(칸의 text_align).
  왼쪽 정렬은 여러 줄 글에도 어색하지 않으므로 길이와 관계없이 입히고, 숫자·날짜만 있는 칸은 예시 정렬을 둔다.
- 세로 정렬: 예시 칸 값.
칸 크기·안쪽 여백은 내용에 따라 달라 바꾸지 않는다. XML 파싱은 defusedxml만 쓴다.
"""

from __future__ import annotations

import base64
import copy
import json
import re
import unicodedata
import zipfile
import zlib
from pathlib import Path

from defusedxml import ElementTree as ET

VERSION = 1
SIDES = ("leftBorder", "rightBorder", "topBorder", "bottomBorder")
# 글자 모양에서 굵게(bold)가 들어갈 자리: 이 요소들 앞에 넣는다(HWPX 요소 순서).
_BOLD_BEFORE = ("underline", "strikeout", "outline", "shadow", "emboss", "engrave", "supscript", "subscript")


def _tag(element):
    return element.tag.rsplit("}", 1)[-1]


def _child(element, name):
    return next((x for x in element if _tag(x) == name), None)


def _ns(element):
    return element.tag[:element.tag.index("}") + 1] if element.tag.startswith("{") else ""


def _xml(element):
    return ET.tostring(element, encoding="unicode")


def _cells(table):
    return [tc for tr in table if _tag(tr) == "tr" for tc in tr if _tag(tc) == "tc"]


def _position(tc):
    """(행, 열, 행 병합 수, 열 병합 수)."""
    addr, span = _child(tc, "cellAddr"), _child(tc, "cellSpan")
    row = int(addr.get("rowAddr", "0")) if addr is not None else 0
    col = int(addr.get("colAddr", "0")) if addr is not None else 0
    rows = int(span.get("rowSpan", "1")) if span is not None else 1
    cols = int(span.get("colSpan", "1")) if span is not None else 1
    return row, col, max(1, rows), max(1, cols)


def _size(table):
    return int(table.get("rowCnt", "0")), int(table.get("colCnt", "0"))


def _paragraphs(tc):
    sub = _child(tc, "subList")
    return [] if sub is None else [p for p in sub if _tag(p) == "p"]


def _text(element):
    """글 요소(t)의 글자와 그 안 요소(빈칸·탭 등) 뒤 글자까지 모은다."""
    parts = []
    for t in element.iter():
        if _tag(t) == "t":
            parts.append(t.text or "")
            parts.extend(sub.tail or "" for sub in t)
    return "".join(parts)


# 흐름도 표의 화살표 칸 글자. 이런 칸이 있는 표(추진절차 흐름도)는 데이터 표가 아니라 서식을 입히지 않는다.
_ARROWS = frozenset("→⇒⇨➔➜➡➞➝▶▷►⇩↓⬇▼▽⟶⟹")


def _is_arrow_cell(tc):
    text = "".join(_text(tc).split())
    return bool(text) and all(ch in _ARROWS for ch in text)


def is_grid_table(table):
    """기본 표 서식 대상 모양인가: 2행 2열 이상이고, 칸 안에 다른 표가 없고, 화살표만 든 칸(흐름도)이 없고,
    본문 행에 칸이 둘 이상인 표.

    본문 행이 모두 한 칸(전체 너비 병합)인 표는 '< 핵심 추진과제 >'·'개선 필요사항' 같은 제목이 달린 설명
    상자라 데이터 표 서식을 입히지 않는다(실측: 2026년 교육부 업무계획 자료).
    """
    rows, cols = _size(table)
    if rows < 2 or cols < 2:
        return False
    cells = _cells(table)
    if any(_tag(x) == "tbl" for tc in cells for x in tc.iter()) or any(map(_is_arrow_cell, cells)):
        return False
    head = _header_rows(table)
    starts = [_position(tc)[0] for tc in cells]
    return any(starts.count(row) >= 2 for row in range(head, rows))


def _header_rows(table):
    """머리글 행 수: 첫 행 칸 중 가장 긴 행 병합(첫 행이 두 행에 걸친 머리글이면 2). 본문 행은 하나 이상 남긴다.

    모든 행에 걸친 칸(비교표의 가운데 구분 칸 등)은 머리글 높이로 보지 않는다.
    """
    rows, _ = _size(table)
    spans = [_position(tc)[2] for tc in _cells(table) if _position(tc)[0] == 0 and _position(tc)[2] < rows]
    return max(1, min(max(spans or [1]), rows - 1))


def _section_names(archive):
    names = [n for n in archive.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)]
    return sorted(names, key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[-1]).group(1)))


# ---------------------------------------------------------------- 학습

def learn_table_style(path, source_name=None):
    """HWPX 예시 문서의 표(칸이 가장 많은 일반 표)에서 기본 표 서식을 배운다."""
    with zipfile.ZipFile(path) as archive:
        header = ET.fromstring(archive.read("Contents/header.xml"))
        sections = [ET.fromstring(archive.read(name)) for name in _section_names(archive)]
    tables = [t for root in sections for t in root.iter() if _tag(t) == "tbl" and is_grid_table(t)]
    if not tables:
        raise ValueError("예시 문서에서 2행 2열 이상인 표를 찾지 못했습니다.")
    return learn_from_table(header, max(tables, key=lambda t: len(_cells(t))), source_name or Path(path).name)


def learn_from_table(header, table, source_name=""):
    fills = {x.get("id"): x for x in header.iter() if _tag(x) == "borderFill"}
    chars = {x.get("id"): x for x in header.iter() if _tag(x) == "charPr"}
    paras = {x.get("id"): x for x in header.iter() if _tag(x) == "paraPr"}
    fonts = {ff.get("lang", "").lower(): {f.get("id"): f for f in ff}
             for ff in header.iter() if _tag(ff) == "fontface"}
    rows, cols = _size(table)
    grid = [[0] * cols for _ in range(rows)]
    cells, borders, char_specs = [], {}, {}

    def border_id(fill_id):
        fill = fills.get(fill_id)
        if fill is None:
            raise ValueError(f"예시 표의 테두리 설정(borderFill {fill_id})이 없습니다.")
        clone = copy.deepcopy(fill)
        clone.attrib.pop("id", None)
        text = _xml(clone)
        for key, value in borders.items():
            if value == text:
                return key
        key = f"b{len(borders)}"
        borders[key] = text
        return key

    def char_id(char_pr):
        ref, ratio, spacing = (_child(char_pr, name) for name in ("fontRef", "ratio", "spacing"))
        spec = {
            "height": int(char_pr.get("height", "1000")),
            "bold": _child(char_pr, "bold") is not None,
            "fonts": {lang: _xml(fonts[lang][fid]) for lang, fid in (ref.attrib.items() if ref is not None else [])
                      if fid in fonts.get(lang, {})},
            "ratio": dict(ratio.attrib) if ratio is not None else {},
            "spacing": dict(spacing.attrib) if spacing is not None else {},
        }
        text = json.dumps(spec, ensure_ascii=False, sort_keys=True)
        for key, value in char_specs.items():
            if json.dumps(value, ensure_ascii=False, sort_keys=True) == text:
                return key
        key = f"c{len(char_specs)}"
        char_specs[key] = spec
        return key

    for tc in _cells(table):
        row, col, row_span, col_span = _position(tc)
        # 칸의 대표 글자 모양 = 글이 가장 긴 글 묶음(run), 정렬은 그 글 묶음이 든 문단의 정렬
        runs = [(p, r) for p in _paragraphs(tc) for r in p if _tag(r) == "run"]
        if not runs:
            raise ValueError("예시 표에 글자 모양을 알 수 없는 칸이 있습니다.")
        para, run = max(runs, key=lambda item: len(_text(item[1]).strip()))
        char_pr = chars.get(run.get("charPrIDRef"))
        if char_pr is None:
            raise ValueError(f"예시 표의 글자 모양(charPr {run.get('charPrIDRef')})이 없습니다.")
        para_pr = paras.get(para.get("paraPrIDRef"))
        align = next((x.get("horizontal") for x in para_pr.iter() if _tag(x) == "align"),
                     None) if para_pr is not None else None
        sub = _child(tc, "subList")
        # 칸 문단 줄 간격(hp:case가 있으면 실제 값 쪽)도 배운다(서식 복사 전면 복제 2단계).
        line = None
        if para_pr is not None:
            scope = next((x for x in para_pr.iter() if _tag(x) == "case"), para_pr)
            spacing = next((x for x in scope.iter() if _tag(x) == "lineSpacing"), None)
            if spacing is not None and (spacing.get("value") or "").lstrip("-").isdigit():
                line = {"type": spacing.get("type") or "PERCENT", "value": int(spacing.get("value"))}
        cells.append({"border": border_id(tc.get("borderFillIDRef")), "char": char_id(char_pr),
                      "align": align, "valign": sub.get("vertAlign") if sub is not None else None,
                      "line": line})
        for r in range(row, min(rows, row + row_span)):
            for c in range(col, min(cols, col + col_span)):
                grid[r][c] = len(cells) - 1
    table_fill = copy.deepcopy(fills[table.get("borderFillIDRef")]) if table.get("borderFillIDRef") in fills else None
    if table_fill is not None:
        table_fill.attrib.pop("id", None)
    in_margin = _child(table, "inMargin")
    return {"version": VERSION, "source": source_name, "rows": rows, "cols": cols,
            "header_rows": _header_rows(table), "grid": grid, "cells": cells,
            "borders": borders, "chars": char_specs,
            "table_border": _xml(table_fill) if table_fill is not None else None,
            "in_margin": {k: in_margin.get(k) for k in ("left", "right", "top", "bottom") if in_margin.get(k)}
            if in_margin is not None else None}


def valid_style(style):
    """저장된 표 서식이 적용할 수 있는 모양인지 본다(설정 파일이 손상돼도 안전)."""
    try:
        rows, cols = int(style["rows"]), int(style["cols"])
        grid, cells = style["grid"], style["cells"]
        if style.get("version") != VERSION or rows < 2 or cols < 2 or len(grid) != rows:
            return False
        if any(len(row) != cols or any(not 0 <= int(i) < len(cells) for i in row) for row in grid):
            return False
        return all(cell["border"] in style["borders"] and cell["char"] in style["chars"] for cell in cells)
    except (KeyError, TypeError, ValueError):
        return False


def describe_style(style):
    """화면에 보여 줄 짧은 설명(예: '표서식예시.hwpx 5×3 표, 머리글 한컴돋움 13pt 굵게 · 본문 함초롬바탕 12pt')."""
    if not valid_style(style):
        return "알 수 없는 표 서식"

    def font(cell_index):
        spec = style["chars"][style["cells"][cell_index]["char"]]
        face = re.search(r'face="([^"]+)"', spec["fonts"].get("hangul", "")) if spec.get("fonts") else None
        return (f"{face.group(1) if face else '글꼴'} {spec['height'] / 100:g}pt"
                + (" 굵게" if spec.get("bold") else ""))

    head = style["grid"][0][min(1, style["cols"] - 1)]
    body = style["grid"][min(style["header_rows"] + 1, style["rows"] - 1)][min(1, style["cols"] - 1)]
    return (f"{style.get('source') or '예시'} {style['rows']}×{style['cols']} 표, "
            f"머리글 {font(head)} · 본문 {font(body)}")


# 표서식예시.hwpx(5×3 행사 일정표)에서 배운 내장 기본값. 준말 '표'에 따로 학습한 서식이 없으면 쓴다.
_DEFAULT_STYLE_DATA = (
    "eNrtWs9v2zYU/lcC7irYovwjmbAVWPxjNZAlQO32kgYBLdGWGkoUKLpOEBQYsB0K5DAMWIECSw+97bDDDr3tT4rzP+zRshLJy5pW"
    "trskpg82H6X3PfLT98Qn0afoJRWxz0NkYwPFfCQcimx0+ev55Ofzydm7ydvXk7PzkjeOjpGBBB/HyK4ZyOEMGhUDeZS4VBwmBwBh"
    "KHwX2fv7poEN68DYrxhVowa/dWPT2ILfrw0MhzC0sGXgioGrBwcAR5nC2z9FfS4AD0bQNyGe4xHVdlSbMH8Io0SN1m6v9QQ6Xs71"
    "vDKy7ngxd2sx90rGHWfcm51u70ln+2mvdStE9T8gPnEEtcXc64tPYHOxEWzpCdy7CUAqJ+6QzKcqhW30TRibdtLZ9hnbOA5YGNvQ"
    "+e1z5EkZ2eXyeDwueSR0eFByeOlIlOFuE7CyZWJcVveX5+jKC3+al8MFBS/pCUqb4GKCEXvE5eOZ4dBQUrHjhxQ6dvd2W9DXF5Qc"
    "NeBO1KUREUTS2WE4/9F0FjEjsbchT6KMU0NwfkTdGawfN/hIIc/scuLYJ85Rt6gzowO5PeVvznvsu9JT55awtREEalacceX9lTn9"
    "XGMIf+jNgXT3djrNz0ORPFoYo8+l5EEeprn3dHunddjd6fyQA6vdguX6ZMhDwj4ynI8iYHsAitwWo9hLzLEfTq2NAXFoI3Vqtlv1"
    "9iY4eUQ6XuNfWIRFHrm+ZuU54HI+AR5B3sDipBNjBYlRQI86M+5WZlg6M+5uZnz+wqMTY1mJUVlaYuiqaLX3/qLavEnnBcazmMRv"
    "kl5VS+++1B0PTns1rb17srI/OOnVtfTW6z3EnVDdplbdmj3k3wnZbWnZrdcT9P+vulfJ7sJ0q8Ax1bdHFWPIxhXTVDsJzEW2FCNq"
    "oAEP5fREEN9wxFKxqu6CMvVTBagHd2hevjmf/P3h4pezye8/KhUnU+z12lORtII+dd1UNbMrA6d0wgEHhMBnJ73Eo934rnf4/V7v"
    "caehqJnOCLrrYESCR1xIn4dpQsDwBYllmixSgDKfEeGT2UlYvSsQQVeeMDozGZWg1gEXwawj8F2W5Iyyjh+nEXGGdsWTSnMGwKEm"
    "rxh5wMkLoskrRt4LEpGQxlTzV4w/Lr3ppqwmrwB58UkAi4lmrxh7o1grrxh3UOEIhZwrXLBpZlbixEqXlsTK3CuTjjT5E+tKzYk5"
    "uzzKgHhxRBw/HOYiZuNlo83FykbKxclEgRiqbMO5as26rtYGhMWrK9cqWfX8Mfnw+uL9nxd//Xb505sVCKg2L6Dqva/Y1pC/pRZt"
    "a8jfsuu2NaRwqaXbF+Wvfgt/1o38WXn+rHn+rBx/Vo6/6sqrtzUU4DILuLWj72HWcBBFkj6jh1f/9tUvf/Wewxd9+/sPNh0t2Q=="
)


def default_style():
    """내장 기본 표 서식(표서식예시.hwpx에서 배운 값).

    예시 표의 본문 칸은 가운데 정렬이지만, 내장 기본값은 본문 칸(머리글 아래) 가운데 첫 열이 아닌 칸의
    문장을 왼쪽 정렬한다(2026-10-03 사용자 요청: '함대 이동에 약 450년 소요 예상' 같은 B2·B3 … 칸 문장).
    """
    style = json.loads(zlib.decompress(base64.b64decode(_DEFAULT_STYLE_DATA)).decode("utf-8"))
    for row in style["grid"][style["header_rows"]:]:
        for index in row[1:]:
            style["cells"][index]["text_align"] = "LEFT"
    return style


def encode_style(style):
    """표 서식을 내장 기본값 형식(zlib 압축 base64)으로 만든다."""
    raw = json.dumps(style, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(zlib.compress(raw, 9)).decode("ascii")


# ---------------------------------------------------------------- 적용

def _row_roles(row, row_span, rows, head):
    """(위 선 위치, 대표 위치, 아래 선 위치). 위치 = header/first/body/last."""
    bottom = row + row_span - 1
    top_role = "header" if row < head else ("first" if row == head else "body")
    # 머리글에서 시작해 본문까지 내려오는 칸(모든 행에 걸친 구분 칸 등)은 본문 칸 서식을 쓴다.
    base = ("header" if bottom < head else "body" if row < head else
            "first" if row == head else "last" if row == rows - 1 else "body")
    bottom_role = "header" if bottom < head else ("last" if bottom == rows - 1 else "body")
    return top_role, base, bottom_role


def _col_roles(col, col_span, cols):
    """(왼쪽 선 위치, 대표 위치, 오른쪽 선 위치). 위치 = first/middle/last."""
    right = col + col_span - 1
    left_role = "first" if col == 0 else "middle"
    base = "first" if col == 0 else ("last" if right == cols - 1 else "middle")
    right_role = "last" if right == cols - 1 else "middle"
    return left_role, base, right_role


def _sample_rows(style):
    """위치별로 가져올 예시 표 행 번호: (위 선, 대표, 아래 선) 사전."""
    rows, head = style["rows"], style["header_rows"]
    first = min(head, rows - 1)
    middle = head + 1 if head + 1 <= rows - 2 else rows - 1   # 첫 본문·마지막이 아닌 본문 행이 있으면 그 행
    top = {"header": 0, "first": first, "body": head + 1 if head + 1 < rows else first}
    base = {"header": 0, "first": first, "body": middle, "last": rows - 1}
    bottom = {"header": head - 1, "body": rows - 2 if rows - 2 >= head else rows - 1, "last": rows - 1}
    return top, base, bottom


def _sample_cols(style):
    cols = style["cols"]
    left = {"first": 0, "middle": 1 if cols >= 2 else 0}
    base = {"first": 0, "middle": 1 if cols >= 3 else cols - 1, "last": cols - 1}
    right = {"middle": cols - 2 if cols >= 2 else 0, "last": cols - 1}
    return left, base, right


class HeaderPool:
    """문서 header에 테두리·글자·문단 모양과 글꼴을 중복 없이 더하고 새 ID를 돌려준다."""

    def __init__(self, header, style):
        self.header, self.style = header, style
        self.groups = {name: next((x for x in header.iter() if _tag(x) == name), None)
                       for name in ("borderFills", "charProperties", "paraProperties")}
        if any(group is None for group in self.groups.values()):
            raise ValueError("문서 머리 정보(header.xml)에 서식 목록이 없습니다.")
        self.fontfaces = {ff.get("lang", "").lower(): ff for ff in header.iter() if _tag(ff) == "fontface"}
        self._borders, self._chars, self._paras, self._fonts, self._parsed = {}, {}, {}, {}, {}

    def _append(self, group_name, element):
        group = self.groups[group_name]
        element.set("id", str(max([int(x.get("id")) for x in group if (x.get("id") or "").isdigit()] + [-1]) + 1))
        group.append(element)
        group.set("itemCnt", str(len(group)))
        return element.get("id")

    def parsed_border(self, key):
        if key not in self._parsed:
            self._parsed[key] = ET.fromstring(self.style["borders"][key])
        return self._parsed[key]

    def picture_fill(self, border_id):
        """문서 테두리/배경 border_id의 채우기가 그림(imgBrush)이면 그 fillBrush 요소, 아니면 None."""
        source = next((x for x in self.groups["borderFills"] if x.get("id") == border_id), None)
        fill = _child(source, "fillBrush") if source is not None else None
        return fill if fill is not None and any(_tag(x) == "imgBrush" for x in fill) else None

    def border(self, element):
        text = _xml(element)
        if text not in self._borders:
            self._borders[text] = self._append("borderFills", copy.deepcopy(element))
        return self._borders[text]

    def font(self, lang, font_xml):
        key = (lang, font_xml)
        if key in self._fonts:
            return self._fonts[key]
        group = self.fontfaces.get(lang)
        sample = ET.fromstring(font_xml)
        if group is None:
            return None
        found = next((f for f in group if f.get("face") == sample.get("face")
                      and (f.get("type") or "") == (sample.get("type") or "")), None)
        if found is None:
            found = sample
            found.set("id", str(max([int(f.get("id")) for f in group if (f.get("id") or "").isdigit()] + [-1]) + 1))
            group.append(found)
            group.set("fontCnt", str(len(group)))
        self._fonts[key] = found.get("id")
        return self._fonts[key]

    def char(self, base_id, spec_key):
        key = (base_id, spec_key)
        if key in self._chars:
            return self._chars[key]
        spec = self.style["chars"][spec_key]
        source = next((x for x in self.groups["charProperties"] if x.get("id") == base_id), None)
        if source is None:
            source = next(iter(self.groups["charProperties"]))
        clone = copy.deepcopy(source)
        clone.set("height", str(spec["height"]))
        ref = _child(clone, "fontRef")
        if ref is not None:
            for lang, font_xml in spec.get("fonts", {}).items():
                font_id = self.font(lang, font_xml)
                if font_id is not None and lang in ref.attrib:
                    ref.set(lang, font_id)
        for name in ("ratio", "spacing"):
            target = _child(clone, name)
            if target is not None and spec.get(name):
                target.attrib.update({k: v for k, v in spec[name].items() if k in target.attrib})
        if spec.get("bold") and _child(clone, "bold") is None:
            bold = type(clone)(_ns(clone) + "bold", {})
            index = next((i for i, x in enumerate(clone) if _tag(x) in _BOLD_BEFORE), len(clone))
            clone.insert(index, bold)
        self._chars[key] = self._append("charProperties", clone)
        return self._chars[key]

    def para_line(self, base_id, line):
        """문단 모양 base_id의 줄 간격을 line(종류·값)으로 바꾼 복제 ID. 같으면 그대로.

        hp:switch가 있으면 case는 실제 값, default는 %가 아니면 두 배 값을 함께 고친다.
        """
        key = (base_id, "line", line["type"], line["value"])
        if key in self._paras:
            return self._paras[key]
        source = next((x for x in self.groups["paraProperties"] if x.get("id") == base_id), None)
        if source is None:
            self._paras[key] = base_id
            return base_id
        clone = copy.deepcopy(source)
        case = next((x for x in clone.iter() if _tag(x) == "case"), None)
        default = next((x for x in clone.iter() if _tag(x) == "default"), None)
        scopes = [(case, 1), (default, 2)] if case is not None else [(clone, 1)]
        changed = False
        for scope, factor in scopes:
            spacing = next((x for x in scope.iter() if _tag(x) == "lineSpacing"), None) if scope is not None else None
            if spacing is None:
                continue
            value = str(line["value"] * (1 if line["type"] == "PERCENT" else factor))
            if spacing.get("type") != line["type"] or spacing.get("value") != value:
                spacing.set("type", line["type"])
                spacing.set("value", value)
                changed = True
        self._paras[key] = self._append("paraProperties", clone) if changed else base_id
        return self._paras[key]

    def para_align(self, base_id, align):
        key = (base_id, align)
        if key in self._paras:
            return self._paras[key]
        source = next((x for x in self.groups["paraProperties"] if x.get("id") == base_id), None)
        current = next((x for x in source.iter() if _tag(x) == "align"), None) if source is not None else None
        if current is None or current.get("horizontal") == align:
            self._paras[key] = base_id
            return base_id
        clone = copy.deepcopy(source)
        next(x for x in clone.iter() if _tag(x) == "align").set("horizontal", align)
        self._paras[key] = self._append("paraProperties", clone)
        return self._paras[key]


def _number_like(text):
    """숫자 칸(금액·수량·비율·날짜·시간 등)인지: 숫자가 있고, 숫자·빈칸·기호를 빼면 글자가 두 자 이하."""
    return bool(re.search(r"\d", text)) and len(re.sub(r"[\d\s\W_]", "", text)) <= 2


def _fits_one_line(paragraph, tc, table, height, ratio):
    """문단 글이 칸 한 줄에 들어가는지 어림한다(한글·전각 = 글자 크기, 반각 = 절반)."""
    text = _text(paragraph).strip()
    if not text:
        return True
    size, margin = _child(tc, "cellSz"), (_child(tc, "cellMargin") if tc.get("hasMargin") == "1"
                                          else _child(table, "inMargin"))
    width = int(size.get("width", "0")) if size is not None else 0
    if margin is not None:
        width -= int(margin.get("left", "510")) + int(margin.get("right", "510"))
    else:
        width -= 1020
    needed = sum(height if unicodedata.east_asian_width(ch) in ("W", "F", "A") else height / 2 for ch in text)
    return needed * ratio / 100 <= width


def apply_table_style(pool, table):
    """표 하나에 기본 표 서식을 적용하고 서식을 바꾼 칸 수를 돌려준다."""
    style = pool.style
    rows, cols = _size(table)
    head = _header_rows(table)
    top_rows, base_rows, bottom_rows = _sample_rows(style)
    left_cols, base_cols, right_cols = _sample_cols(style)
    grid, cells = style["grid"], style["cells"]
    count = 0
    for tc in _cells(table):
        row, col, row_span, col_span = _position(tc)
        top_role, base_role, bottom_role = _row_roles(row, row_span, rows, head)
        left_role, base_col, right_role = _col_roles(col, col_span, cols)
        base = cells[grid[base_rows[base_role]][base_cols[base_col]]]
        edge_cells = {
            "leftBorder": cells[grid[base_rows[base_role]][left_cols[left_role]]],
            "rightBorder": cells[grid[base_rows[base_role]][right_cols[right_role]]],
            "topBorder": cells[grid[top_rows[top_role]][base_cols[base_col]]],
            "bottomBorder": cells[grid[bottom_rows[bottom_role]][base_cols[base_col]]],
        }
        composed = copy.deepcopy(pool.parsed_border(base["border"]))
        for side, source_cell in edge_cells.items():
            source = _child(pool.parsed_border(source_cell["border"]), side)
            current = _child(composed, side)
            if source is not None and current is not None:
                composed[list(composed).index(current)] = copy.deepcopy(source)
        # 칸 배경 그림(사진)을 예시 바탕으로 덮으면 그림이 문서에서 사라진다(실측: 10월 확대간부회의 자료 5장).
        picture = pool.picture_fill(tc.get("borderFillIDRef"))
        if picture is not None:
            current = _child(composed, "fillBrush")
            if current is not None:
                composed.remove(current)
            composed.append(copy.deepcopy(picture))   # fillBrush는 borderFill의 마지막 요소
        tc.set("borderFillIDRef", pool.border(composed))
        sub = _child(tc, "subList")
        if sub is not None and base.get("valign"):
            sub.set("vertAlign", base["valign"])
        spec = style["chars"][base["char"]]
        ratio = int((spec.get("ratio") or {}).get("hangul", "100"))
        text_align = base.get("text_align") if base_role != "header" else None
        for paragraph in _paragraphs(tc):
            for run in (r for r in paragraph if _tag(r) == "run"):
                run.set("charPrIDRef", pool.char(run.get("charPrIDRef"), base["char"]))
            # 본문 문장 정렬(text_align)이 있으면 길이와 관계없이 입힌다. 숫자·날짜 칸은 예시 정렬을 따른다.
            sentence = bool(text_align) and not _number_like(_text(paragraph).strip())
            align = text_align if sentence else base.get("align")
            if align and paragraph.get("paraPrIDRef") is not None and (
                    sentence or base_role == "header"
                    or _fits_one_line(paragraph, tc, table, spec["height"], ratio)):
                paragraph.set("paraPrIDRef", pool.para_align(paragraph.get("paraPrIDRef"), align))
            if base.get("line") and paragraph.get("paraPrIDRef") is not None:
                paragraph.set("paraPrIDRef", pool.para_line(paragraph.get("paraPrIDRef"), base["line"]))
            for lineseg in [x for x in paragraph if _tag(x) == "linesegarray"]:
                paragraph.remove(lineseg)
        count += 1
    if style.get("table_border"):
        table.set("borderFillIDRef", pool.border(ET.fromstring(style["table_border"])))
    in_margin = _child(table, "inMargin")
    if style.get("in_margin") and in_margin is not None:
        in_margin.attrib.update(style["in_margin"])
    return count
