"""표/다이어그램 편집기에서 만든 흐름표·기본 표를 한/글 HWPX 문서로 만든다(알파, 2026-10-15).

흐름표 모양은 '표 다이어그램 연습/추진일정 흐름표.hwpx'를 학습했다.
- 두 행: 위 행은 단계 이름(굵게, 바탕 #DFE6F7), 아래 행은 일정(흰 바탕). 두 행 사이만 이중선(0.5mm).
- 단계 사이 화살표(➜) 칸은 두 행을 합치고, 칸 폭은 표 폭의 약 3.85%다.
- 선은 #4C4C4C 0.4mm, 글은 한컴돋움 12pt 자간 -7%, 가운데 정렬, 칸 위아래 여백 1mm.
기본 표는 앱의 기본 표 서식(준말 '표', table_style)을 그대로 입히고, 사용자가 고른 글꼴·크기·굵게·색이 있으면
머리글·본문 칸에 덧입힌다. 바탕 문서는 앱에 포함된 '기본 서식.hwpx'(쪽 여백·글꼴 목록)다.
XML 파싱은 defusedxml만 쓴다. 입력 값은 모두 검증하고 범위를 제한한다.
"""
from __future__ import annotations

import copy
import io
import re
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from .batch_format import _serialize
from .hwpx import open_hwpx_safely
from .table_style import HeaderPool, apply_table_style, valid_style

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HH = "http://www.hancom.co.kr/hwpml/2011/head"
HC = "http://www.hancom.co.kr/hwpml/2011/core"

# 편집기에서 고를 수 있는 글꼴(공문서에 흔한 글꼴). 바탕 문서에 없는 글꼴은 글꼴 목록에 더한다.
FONTS = ("한컴돋움", "휴먼명조", "HY견고딕", "HY헤드라인M", "함초롬돋움", "함초롬바탕", "돋움", "맑은 고딕", "나눔고딕", "굴림")
ARROWS = ("➜", "⇨", "▶", "→", "➡")
MAX_FLOW_STEPS, MAX_ROWS, MAX_COLS, MAX_TEXT = 12, 40, 12, 200

# 학습한 흐름표 모양(추진일정 흐름표.hwpx).
FLOW_LINE = {"color": "#4C4C4C", "width": "0.4 mm"}
FLOW_SPLIT = {"type": "DOUBLE_SLIM", "width": "0.5 mm", "color": "#4C4C4C"}
FLOW_DEFAULTS = {
    "step": {"font": "한컴돋움", "size": 12, "bold": True, "color": "#000000", "fill": "#DFE6F7"},
    "date": {"font": "한컴돋움", "size": 12, "bold": False, "color": "#000000", "fill": "#FFFFFF"},
    "arrow": {"font": "한컴돋움", "size": 12, "bold": True, "color": "#000000", "fill": ""},
}
GRID_DEFAULTS = {
    "head": {"font": "한컴돋움", "size": 13, "bold": True, "color": "#000000", "fill": "#E7EEF8"},
    "body": {"font": "휴먼명조", "size": 12, "bold": False, "color": "#000000", "fill": ""},
}
ARROW_RATIO = 0.0385
ROW_HEIGHT = 3326


class TableSpecError(ValueError):
    """편집기에서 받은 표 정보가 올바르지 않다."""


def _text(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TableSpecError("칸 글은 문자여야 합니다.")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    if len(value) > MAX_TEXT:
        raise TableSpecError(f"칸 글은 {MAX_TEXT}자까지 넣을 수 있습니다.")
    if any(ord(ch) < 32 and ch not in "\n\t" for ch in value):
        raise TableSpecError("칸 글에 쓸 수 없는 문자가 있습니다.")
    return value


def _style(value, default):
    value = value if isinstance(value, dict) else {}
    font = value.get("font", default["font"])
    if font not in FONTS:
        raise TableSpecError("고를 수 있는 글꼴이 아닙니다.")
    try:
        size = float(value.get("size", default["size"]))
    except (TypeError, ValueError) as exc:
        raise TableSpecError("글꼴 크기를 확인해 주세요.") from exc
    if not 6 <= size <= 40:
        raise TableSpecError("글꼴 크기는 6~40pt로 지정해 주세요.")
    color = str(value.get("color", default["color"]) or "#000000")
    fill = str(value.get("fill", default["fill"]) or "")
    for item in (color, fill):
        if item and not re.fullmatch(r"#[0-9A-Fa-f]{6}", item):
            raise TableSpecError("색은 #RRGGBB 형식이어야 합니다.")
    return {"font": font, "size": round(size * 2) / 2, "bold": bool(value.get("bold", default["bold"])),
            "color": color.upper(), "fill": fill.upper()}


def normalize(spec):
    """편집기 표 정보를 검증해 정리한다. 흐름표 {'kind':'flow','steps':[{title,date}],'arrow','styles'},
    기본 표 {'kind':'grid','rows':[[글,…],…],'header_rows','styles'}."""
    if not isinstance(spec, dict):
        raise TableSpecError("표 정보를 확인해 주세요.")
    kind = spec.get("kind")
    styles = spec.get("styles") if isinstance(spec.get("styles"), dict) else {}
    if kind == "flow":
        steps = spec.get("steps")
        if not isinstance(steps, list) or not 2 <= len(steps) <= MAX_FLOW_STEPS:
            raise TableSpecError(f"흐름표 단계는 2~{MAX_FLOW_STEPS}칸입니다.")
        arrow = spec.get("arrow", ARROWS[0])
        if arrow not in ARROWS:
            raise TableSpecError("화살표 모양을 확인해 주세요.")
        return {"kind": "flow", "arrow": arrow,
                "steps": [{"title": _text(s.get("title")) if isinstance(s, dict) else _text(None),
                           "date": _text(s.get("date")) if isinstance(s, dict) else _text(None)} for s in steps],
                "styles": {role: _style(styles.get(role), default) for role, default in FLOW_DEFAULTS.items()}}
    if kind == "grid":
        rows = spec.get("rows")
        if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS:
            raise TableSpecError(f"표는 1~{MAX_ROWS}행입니다.")
        cols = max((len(r) for r in rows if isinstance(r, list)), default=0)
        if not 1 <= cols <= MAX_COLS or any(not isinstance(r, list) for r in rows):
            raise TableSpecError(f"표는 1~{MAX_COLS}열입니다.")
        header_rows = spec.get("header_rows", 1)
        if not isinstance(header_rows, int) or not 0 <= header_rows <= min(2, len(rows)):
            raise TableSpecError("머리글 행 수를 확인해 주세요.")
        return {"kind": "grid", "header_rows": header_rows,
                "rows": [[_text(r[c]) if c < len(r) else "" for c in range(cols)] for r in rows],
                "use_basic_style": spec.get("use_basic_style", True) is not False,
                "styles": {role: _style(styles.get(role), default) for role, default in GRID_DEFAULTS.items()},
                "custom": {role: isinstance(styles.get(role), dict) for role in GRID_DEFAULTS}}
    raise TableSpecError("표 종류는 흐름표 또는 기본 표입니다.")


# ---- header(글꼴·글자·테두리·문단 모양) -------------------------------------------------------------

def _tag(element):
    return element.tag.rsplit("}", 1)[-1]


def _child(element, name):
    return next((x for x in element if _tag(x) == name), None)


class _Header:
    def __init__(self, header):
        self.header = header
        self.groups = {name: next(x for x in header.iter() if _tag(x) == name)
                       for name in ("borderFills", "charProperties", "paraProperties")}
        self.fontfaces = [ff for ff in header.iter() if _tag(ff) == "fontface"]
        self._chars, self._borders, self._para = {}, {}, None

    def _append(self, group, element):
        items = self.groups[group]
        element.set("id", str(max([int(x.get("id")) for x in items if (x.get("id") or "").isdigit()] + [-1]) + 1))
        items.append(element)
        items.set("itemCnt", str(len(items)))
        return element.get("id")

    def font(self, face):
        """글꼴 이름의 언어별 글꼴 ID(모든 fontface에 같은 순번으로 둔다). 없으면 더한다."""
        ids = {}
        for group in self.fontfaces:
            found = next((f for f in group if f.get("face") == face), None)
            if found is None:
                sample = next(iter(group), None)
                found = type(group)(f"{{{HH}}}font", {"face": face, "type": "TTF", "isEmbedded": "0"})
                if sample is not None and _child(sample, "typeInfo") is not None:
                    found.append(copy.deepcopy(_child(sample, "typeInfo")))
                found.set("id", str(max([int(f.get("id")) for f in group if (f.get("id") or "").isdigit()] + [-1]) + 1))
                group.append(found)
                group.set("fontCnt", str(len(group)))
            ids[group.get("lang", "").lower()] = found.get("id")
        return ids

    def char(self, style, spacing=0):
        key = (style["font"], style["size"], style["bold"], style["color"], spacing)
        if key in self._chars:
            return self._chars[key]
        source = next(x for x in self.groups["charProperties"] if x.get("id") == "0")
        clone = copy.deepcopy(source)
        clone.set("height", str(int(style["size"] * 100)))
        clone.set("textColor", style["color"])
        ref = _child(clone, "fontRef")
        for lang, font_id in self.font(style["font"]).items():
            if ref is not None and lang in ref.attrib:
                ref.set(lang, font_id)
        gap = _child(clone, "spacing")
        if gap is not None:
            for lang in list(gap.attrib):
                gap.set(lang, str(spacing))
        for old in [x for x in clone if _tag(x) == "bold"]:
            clone.remove(old)
        if style["bold"]:
            index = next((i for i, x in enumerate(clone) if _tag(x) in (
                "underline", "strikeout", "outline", "shadow", "emboss", "engrave", "supscript", "subscript")), len(clone))
            clone.insert(index, type(clone)(f"{{{HH}}}bold", {}))
        self._chars[key] = self._append("charProperties", clone)
        return self._chars[key]

    def border(self, sides, fill=""):
        """sides: {'left': (종류, 굵기, 색), …}. 없는 쪽은 선 없음."""
        key = (tuple(sorted(sides.items())), fill)
        if key in self._borders:
            return self._borders[key]
        source = next(x for x in self.groups["borderFills"] if x.get("id") == "1")
        clone = copy.deepcopy(source)
        for name in ("left", "right", "top", "bottom"):
            line = _child(clone, name + "Border")
            kind, width, color = sides.get(name, ("NONE", "0.1 mm", "#000000"))
            if line is not None:
                line.attrib.update({"type": kind, "width": width, "color": color})
        for old in [x for x in clone if _tag(x) == "fillBrush"]:
            clone.remove(old)
        if fill:
            brush = type(clone)(f"{{{HC}}}fillBrush", {})
            brush.append(type(clone)(f"{{{HC}}}winBrush", {"faceColor": fill, "hatchColor": "#000000", "alpha": "0"}))
            clone.append(brush)
        self._borders[key] = self._append("borderFills", clone)
        return self._borders[key]

    def refill(self, border_id, fill):
        """테두리/배경 border_id를 그대로 두고 바탕색만 fill로 바꾼 복제 ID(fill이 비면 바탕 없음)."""
        key = ("refill", border_id, fill)
        if key in self._borders:
            return self._borders[key]
        source = next((x for x in self.groups["borderFills"] if x.get("id") == border_id), None)
        if source is None:
            return border_id
        clone = copy.deepcopy(source)
        for old in [x for x in clone if _tag(x) == "fillBrush"]:
            clone.remove(old)
        if fill:
            brush = type(clone)(f"{{{HC}}}fillBrush", {})
            brush.append(type(clone)(f"{{{HC}}}winBrush", {"faceColor": fill, "hatchColor": "#000000", "alpha": "0"}))
            clone.append(brush)
        self._borders[key] = self._append("borderFills", clone)
        return self._borders[key]

    def center_para(self):
        if self._para is None:
            source = next(x for x in self.groups["paraProperties"] if x.get("id") == "0")
            clone = copy.deepcopy(source)
            align = _child(clone, "align")
            if align is not None:
                align.set("horizontal", "CENTER")
            for line in (x for x in clone.iter() if _tag(x) == "lineSpacing"):
                if line.get("type") == "PERCENT":
                    line.set("value", "130")
            self._para = self._append("paraProperties", clone)
        return self._para


# ---- 표 XML ------------------------------------------------------------------------------------

def _element(parent, _tag_name, _ns=HP, **attributes):
    child = type(parent)(f"{{{_ns}}}{_tag_name}", {k: str(v) for k, v in attributes.items()})
    parent.append(child)
    return child


def _cell(tr, *, col, row, colspan=1, rowspan=1, width, height, border, para, char, text, margin=(141, 141, 141, 141),
          header=False):
    tc = _element(tr, "tc", name="", header=int(header), hasMargin=1, protect=0, editable=0, dirty=0,
                  borderFillIDRef=border)
    sub = _element(tc, "subList", id="", textDirection="HORIZONTAL", lineWrap="BREAK", vertAlign="CENTER",
                   linkListIDRef=0, linkListNextIDRef=0, textWidth=0, textHeight=0, hasTextRef=0, hasNumRef=0)
    for line in (text.split("\n") if text else [""]):
        p = _element(sub, "p", id=0, paraPrIDRef=para, styleIDRef=0, pageBreak=0, columnBreak=0, merged=0)
        run = _element(p, "run", charPrIDRef=char)
        _element(run, "t").text = line
    _element(tc, "cellAddr", colAddr=col, rowAddr=row)
    _element(tc, "cellSpan", colSpan=colspan, rowSpan=rowspan)
    _element(tc, "cellSz", width=width, height=height)
    _element(tc, "cellMargin", left=margin[0], right=margin[1], top=margin[2], bottom=margin[3])
    return tc


def _table(parent, rows, cols, width, height, border):
    table = _element(parent, "tbl", id=1_221_421_164, zOrder=0, numberingType="TABLE", textWrap="TOP_AND_BOTTOM",
                     textFlow="BOTH_SIDES", lock=0, dropcapstyle="None", pageBreak="CELL", repeatHeader=1,
                     rowCnt=rows, colCnt=cols, cellSpacing=0, borderFillIDRef=border, noAdjust=0)
    _element(table, "sz", width=width, widthRelTo="ABSOLUTE", height=height, heightRelTo="ABSOLUTE", protect=0)
    _element(table, "pos", treatAsChar=1, affectLSpacing=0, flowWithText=1, allowOverlap=0, holdAnchorAndSO=0,
             vertRelTo="PARA", horzRelTo="PARA", vertAlign="TOP", horzAlign="LEFT", vertOffset=0, horzOffset=0)
    _element(table, "outMargin", left=0, right=0, top=0, bottom=0)
    _element(table, "inMargin", left=510, right=510, top=141, bottom=141)
    return table


def _split(total, parts):
    """total을 parts 개로 나누되 합이 정확히 total이 되게 한다."""
    base = [total // parts] * parts
    for i in range(total - sum(base)):
        base[i] += 1
    return base


def build_flow(run, spec, pool, body_width):
    n = len(spec["steps"])
    styles = spec["styles"]
    arrow_w = int(round(body_width * ARROW_RATIO))
    step_ws = _split(body_width - arrow_w * (n - 1), n)
    line = ("SOLID", FLOW_LINE["width"], FLOW_LINE["color"])
    split = (FLOW_SPLIT["type"], FLOW_SPLIT["width"], FLOW_SPLIT["color"])
    step_border = pool.border({"left": line, "right": line, "top": line, "bottom": split}, styles["step"]["fill"])
    date_border = pool.border({"left": line, "right": line, "top": split, "bottom": line}, styles["date"]["fill"])
    arrow_border = pool.border({"left": line, "right": line}, styles["arrow"]["fill"])
    para = pool.center_para()
    chars = {role: pool.char(styles[role], -7) for role in styles}
    table = _table(run, 2, 2 * n - 1, body_width, ROW_HEIGHT * 2, pool.border({}))
    margin = (0, 0, 283, 283)
    first = _element(table, "tr")
    for i, step in enumerate(spec["steps"]):
        _cell(first, col=2 * i, row=0, width=step_ws[i], height=ROW_HEIGHT, border=step_border, para=para,
              char=chars["step"], text=step["title"], margin=margin)
        if i < n - 1:
            _cell(first, col=2 * i + 1, row=0, rowspan=2, width=arrow_w, height=ROW_HEIGHT * 2, border=arrow_border,
                  para=para, char=chars["arrow"], text=spec["arrow"], margin=margin)
    second = _element(table, "tr")
    for i, step in enumerate(spec["steps"]):
        _cell(second, col=2 * i, row=1, width=step_ws[i], height=ROW_HEIGHT, border=date_border, para=para,
              char=chars["date"], text=step["date"], margin=margin)
    return table


def build_grid(run, spec, pool, body_width):
    rows, head = spec["rows"], spec["header_rows"]
    cols = len(rows[0])
    widths = _split(body_width, cols)
    styles = spec["styles"]
    line = ("SOLID", "0.12 mm", "#000000")
    para = pool.center_para()
    borders = {role: pool.border({"left": line, "right": line, "top": line, "bottom": line}, styles[role]["fill"])
               for role in styles}
    chars = {role: pool.char(styles[role]) for role in styles}
    height = 1800
    table = _table(run, len(rows), cols, body_width, height * len(rows), pool.border({}))
    for r, values in enumerate(rows):
        tr = _element(table, "tr")
        role = "head" if r < head else "body"
        for c, value in enumerate(values):
            _cell(tr, col=c, row=r, width=widths[c], height=height, border=borders[role], para=para,
                  char=chars[role], text=value, header=r < head)
    return table


def _override(table, spec, pool):
    """기본 표 서식을 입힌 뒤, 사용자가 직접 고른 글자 서식·바탕을 머리글·본문 칸에 덧입힌다."""
    head = spec["header_rows"]
    for tc in (x for x in table.iter() if _tag(x) == "tc"):
        addr = _child(tc, "cellAddr")
        role = "head" if int(addr.get("rowAddr", "0")) < head else "body"
        if not spec["custom"][role]:
            continue
        style = spec["styles"][role]
        char = pool.char(style)
        for run in (x for x in tc.iter() if _tag(x) == "run"):
            run.set("charPrIDRef", char)
        if style["fill"]:
            tc.set("borderFillIDRef", pool.refill(tc.get("borderFillIDRef"), style["fill"]))


def build_table_hwpx(spec, base_path, target_path, *, basic_style=None):
    """spec(편집기 표 정보)로 표 하나가 든 HWPX를 target_path에 만든다. 돌려주는 값은 target_path."""
    spec = normalize(spec)
    with open_hwpx_safely(base_path) as z:
        contents = {info.filename: z.read(info.filename) for info in z.infolist()}
    sections = sorted(n for n in contents if re.fullmatch(r"Contents/section\d+\.xml", n))
    if not sections or "Contents/header.xml" not in contents:
        raise TableSpecError("바탕 문서 구조를 확인해 주세요.")
    header_bytes, section_bytes = contents["Contents/header.xml"], contents[sections[0]]
    header = ET.fromstring(header_bytes)
    section = ET.fromstring(section_bytes)
    pool = _Header(header)

    # 쪽 여백 사이 본문 폭.
    page = next(x for x in section.iter() if _tag(x) == "pagePr")
    margin = _child(page, "margin")
    body_width = int(page.get("width")) - int(margin.get("left")) - int(margin.get("right"))

    # 첫 문단의 구역·단 설정만 남기고 나머지 본문은 비운다.
    paragraphs = [p for p in section if _tag(p) == "p"]
    first = paragraphs[0]
    for p in paragraphs[1:]:
        section.remove(p)
    for child in list(first):
        if _tag(child) == "run":
            for item in list(child):
                if _tag(item) not in ("secPr", "ctrl"):
                    child.remove(item)
            if not len(child):
                first.remove(child)
        elif _tag(child) == "linesegarray":
            first.remove(child)

    holder = _element(section, "p", id=0, paraPrIDRef=pool.center_para(), styleIDRef=0, pageBreak=0,
                      columnBreak=0, merged=0)
    run = _element(holder, "run", charPrIDRef=0)
    if spec["kind"] == "flow":
        build_flow(run, spec, pool, body_width)
    else:
        table = build_grid(run, spec, pool, body_width)
        style = basic_style if spec["use_basic_style"] and valid_style(basic_style) else None
        if style is not None:
            apply_table_style(HeaderPool(header, style), table)
        _override(table, spec, pool)
    _element(run, "t")

    contents["Contents/header.xml"] = _serialize(header, header_bytes)
    contents[sections[0]] = _serialize(section, section_bytes)
    for extra in sections[1:]:
        contents.pop(extra)
    if "Preview/PrvText.txt" in contents:
        contents["Preview/PrvText.txt"] = _preview_text(spec).encode("utf-8")
    target = Path(target_path)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as out:
        if "mimetype" in contents:
            out.writestr("mimetype", contents.pop("mimetype"), compress_type=zipfile.ZIP_STORED)
        for name, data in contents.items():
            out.writestr(name, data)
    target.write_bytes(buffer.getvalue())
    return target


def _preview_text(spec):
    if spec["kind"] == "flow":
        return (" " + spec["arrow"] + " ").join(s["title"] for s in spec["steps"])
    return "\n".join("\t".join(row) for row in spec["rows"])
