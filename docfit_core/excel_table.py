"""엑셀 클립보드(HTML Format·글자)를 정리된 표 모델로 바꾼다.

엑셀은 서식을 조각 밖 <style>의 .xl63 같은 클래스에 두고, 조각에는 <table> 없이 <col>·<tr>만 넣는다.
칸 배경색은 표 서식이라 옵션으로 유지하고, 글자 단위 바탕색·빈칸·제어 문자는 버린다.
"""
from __future__ import annotations

import csv
import io
import re
from html.parser import HTMLParser

_NAMED_COLORS = {
    "black": "#000000", "white": "#FFFFFF", "red": "#FF0000", "green": "#008000", "blue": "#0000FF",
    "yellow": "#FFFF00", "aqua": "#00FFFF", "cyan": "#00FFFF", "fuchsia": "#FF00FF", "magenta": "#FF00FF",
    "silver": "#C0C0C0", "gray": "#808080", "grey": "#808080", "lime": "#00FF00", "maroon": "#800000",
    "navy": "#000080", "olive": "#808000", "purple": "#800080", "teal": "#008080", "orange": "#FFA500",
}
_NUMBER = r"(?:\d[\d,]*(?:\.\d+)?|\.\d+)"
_NUMERIC = re.compile(rf"(?:[+-]?{_NUMBER}%?|\({ _NUMBER }\)|[₩$€£¥]\s?[+-]?{_NUMBER})")
_CONTROL = re.compile(r"_x000[0-9A-Fa-f]_|[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f​-‍⁠﻿]")
_SPACES = re.compile(r"[ \t  -  　]+")


def _span(value):
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 1


def _style_value(style, *keys):
    for key in keys:
        match = re.search(rf"(?:^|[;\s]){key}\s*:\s*([^;]+)", style or "", re.I)
        if match:
            return match.group(1).strip()
    return ""


def _color(value):
    text = (value or "").strip().split()[0].lower() if (value or "").strip() else ""
    if re.fullmatch(r"#[0-9a-f]{6}", text):
        return text.upper()
    if re.fullmatch(r"#[0-9a-f]{3}", text):
        return "#" + "".join(ch * 2 for ch in text[1:]).upper()
    return _NAMED_COLORS.get(text, "")


def _width(style, attr):
    match = re.search(r"width\s*:\s*([\d.]+)\s*pt", style or "", re.I)
    if match:
        return float(match.group(1))
    try:
        return float(attr) * 0.75  # 픽셀 → pt
    except (TypeError, ValueError):
        return 0.0


def _class_styles(html):
    """<style>의 .xl63 {…} 클래스를 사전으로 모은다."""
    styles = {}
    for block in re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I):
        for name, body in re.findall(r"\.([\w-]+)\s*\{([^}]*)\}", block):
            styles[name.lower()] = re.sub(r"\s+", " ", body)
    return styles


class _Parser(HTMLParser):
    def __init__(self, classes):
        super().__init__(convert_charrefs=True)
        self.classes = classes
        self.rows, self.row, self.cell, self.widths = [], None, None, []
        self.highlights = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "col":
            self.widths.extend([_width(a.get("style"), a.get("width"))] * _span(a.get("span")))
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            style = self.classes.get((a.get("class") or "").lower(), "") + ";" + (a.get("style") or "")
            weight = _style_value(style, "font-weight").lower()
            self.cell = dict(
                text="", rowspan=_span(a.get("rowspan")), colspan=_span(a.get("colspan")),
                align=(_style_value(style, "text-align") or a.get("align") or "").lower(),
                bold=tag == "th" or weight in ("bold", "bolder") or (weight.isdigit() and int(weight) >= 600),
                color=_color(_style_value(style, "color")) or "#000000",
                fill=_color(a.get("bgcolor")) or _color(_style_value(style, "background", "background-color")),
                numeric=False)
        elif self.cell is not None:
            if tag == "br":
                self.cell["text"] += "\n"
            elif tag in ("b", "strong"):
                self.cell["bold"] = True
            color = _color(_style_value(a.get("style"), "color"))
            if color:
                self.cell["color"] = color
            if re.search(r"background|mso-highlight", a.get("style") or "", re.I):
                self.highlights += 1  # 글자 단위 바탕색은 옮기지 않는다.

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            # HTML 안의 줄바꿈은 소스 정렬일 뿐이고, 칸 안 줄바꿈은 <br>로 온다.
            self.cell["text"] += re.sub(r"[\r\n\t]+", " ", data)


def _clean_text(value, counts=None):
    """앞뒤·연속 빈칸, 특수 공백, 제어 문자, 맨 앞 작은따옴표를 없애고 칸 안 줄바꿈은 유지한다."""
    text, removed = _CONTROL.subn("", value)
    lines = []
    spaces = 0
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        tidy = _SPACES.sub(" ", line).strip()
        spaces += tidy != line
        lines.append(tidy)
    result = "\n".join(lines).strip("\n")
    quoted = result.startswith("'")
    if quoted:
        result = result[1:].lstrip()
    if counts is not None:
        counts["symbols"] += removed + quoted
        counts["spaces"] += spaces
    return result


def _html_text(data):
    if isinstance(data, bytes):
        # 머리의 위치 값은 바이트 기준이므로 복호화 전에 자른다.
        match = re.search(rb"StartHTML:\s*(\d+)", data)
        return data[int(match.group(1)) if match else 0:].decode("utf-8", "replace")
    return data


def _fragment(html):
    match = re.search(r"<!--\s*StartFragment\s*-->(.*?)<!--\s*EndFragment\s*-->", html, re.S | re.I)
    return match.group(1) if match else html


def _tsv_rows(tsv):
    rows = list(csv.reader(io.StringIO(tsv), delimiter="\t", quotechar='"'))
    return [[dict(text=value, rowspan=1, colspan=1, align="", bold=False, fill="", color="", numeric=False)
             for value in row] for row in rows if row]


def _place(rows):
    """병합을 풀어 칸마다 격자 위치(row·col)를 정한다."""
    taken = set()
    for y, row in enumerate(rows):
        x = 0
        for cell in row:
            while (y, x) in taken:
                x += 1
            cell["row"], cell["col"] = y, x
            for dy in range(cell["rowspan"]):
                for dx in range(cell["colspan"]):
                    taken.add((y + dy, x + dx))
            x += cell["colspan"]


def _trim(rows):
    """글자도 배경도 없는 끝 행·끝 열을 지운다."""
    _place(rows)
    used = [c for row in rows for c in row if c["text"] or c["fill"]]
    last_row = max((c["row"] + c["rowspan"] for c in used), default=0)
    last_col = max((c["col"] + c["colspan"] for c in used), default=0)
    kept = []
    for row in rows[:last_row]:
        cells = [c for c in row if c["col"] < last_col]
        for cell in cells:
            cell["colspan"] = min(cell["colspan"], last_col - cell["col"])
            cell["rowspan"] = min(cell["rowspan"], last_row - cell["row"])
        kept.append(cells)
    # 선행 빈 행·열도 표 격자의 일부이므로 실제 좌표를 유지한다.
    return kept, last_row, last_col


def parse_clipboard(html_data=None, tsv=None, *, clean=True):
    """표 모델과 정리 건수를 돌려준다. 칸마다 text·row·col·rowspan·colspan·align·bold·fill이 있다."""
    counts = dict(background=0, spaces=0, symbols=0)
    rows, widths = [], []
    if html_data:
        html = _html_text(html_data)
        parser = _Parser(_class_styles(html))
        parser.feed(_fragment(html))
        rows, widths = parser.rows, parser.widths
        counts["background"] = parser.highlights
    if not rows and tsv:
        rows = _tsv_rows(tsv)
    if not rows:
        raise ValueError("클립보드에서 엑셀 표를 찾지 못했습니다. 엑셀에서 셀을 복사한 뒤 다시 눌러 주세요.")
    for row in rows:
        for cell in row:
            if clean:
                cell["text"] = _clean_text(cell["text"], counts)
            cell["numeric"] = bool(_NUMERIC.fullmatch(cell["text"]))
            if cell["align"] not in ("left", "center", "right"):
                cell["align"] = "right" if cell["numeric"] else "left"
    rows, height, width = _trim(rows)
    if not height or not width:
        raise ValueError("복사한 셀에 내용이 없습니다.")
    return dict(rows=rows, row_count=height, col_count=width, widths=(widths + [0.0] * width)[:width],
                cleaned=counts)
