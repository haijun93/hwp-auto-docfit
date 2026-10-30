"""한/글에서 복사한 표(클립보드 'HTML Format')를 표그림판 그림(격자 선·칸 글)으로 바꾼다(2.0.5).

한/글은 표를 복사하면 HTML 조각도 함께 넣는다: 칸마다 폭·높이(pt), 네 변 테두리(종류·색·굵기), 병합(colspan·rowspan),
문단 정렬과 글이 들어 있다. 칸 폭·높이를 표그림판 격자(기본 5mm)로 반올림해 선을 긋고 글을 칸 왼쪽 위 격자에 둔다.
HTML은 표준 라이브러리 html.parser로 읽는다(XML 파서가 아니다). 크기·개수는 표그림판 한도 안으로 제한한다.
"""
from __future__ import annotations

import math
import re
from html.parser import HTMLParser

PT_TO_MM = 25.4 / 72
MAX_GRID = 200
MAX_CELLS = 2000
_MARGIN = 1  # 표 왼쪽 위를 격자 (1,1)에 둔다


class _TableParser(HTMLParser):
    """첫 최상위 표의 행·칸(속성·글·굵게·정렬)을 모은다. 칸 안 표는 글만 이어 붙인다."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.depth, self.done = [], 0, False
        self.cell, self.bold_depth, self.paragraph = None, 0, []

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        attrs = dict(attrs)
        if tag == "table":
            self.depth += 1
            return
        if self.depth != 1 and not (self.depth > 1 and self.cell is not None):
            return
        if self.depth == 1 and tag == "tr":
            self.rows.append([])
        elif self.depth == 1 and tag in ("td", "th") and self.rows:
            if sum(len(r) for r in self.rows) >= MAX_CELLS:
                raise ValueError("표 칸이 너무 많습니다.")
            self.cell = {"style": attrs.get("style") or "", "colspan": _int(attrs.get("colspan")),
                         "rowspan": _int(attrs.get("rowspan")), "lines": [], "bold": False, "align": ""}
            self.paragraph = []
        elif self.cell is not None:
            style = (attrs.get("style") or "").lower()
            if tag in ("b", "strong") or re.search(r"font-weight\s*:\s*(bold|[6-9]00)", style):
                self.bold_depth += 1
                self.cell["bold"] = True
            if tag == "p":
                match = re.search(r"text-align\s*:\s*(left|center|right|justify)", style)
                if match and not self.cell["align"]:
                    self.cell["align"] = match.group(1)
            if tag == "br":
                self._end_paragraph()

    def handle_endtag(self, tag):
        if self.done:
            return
        if tag == "table":
            self.depth -= 1
            if self.depth == 0:
                self.done = True
            return
        if self.cell is None:
            return
        if tag == "p":
            self._end_paragraph()
        elif self.depth == 1 and tag in ("td", "th"):
            self._end_paragraph()
            self.rows[-1].append(self.cell)
            self.cell = None

    def handle_data(self, data):
        if self.cell is not None and not self.done:
            self.paragraph.append(data)

    def _end_paragraph(self):
        if self.cell is not None and self.paragraph:
            text = re.sub(r"\s+", " ", "".join(self.paragraph).replace("\xa0", " ")).strip()
            self.cell["lines"].append(text)
        self.paragraph = []


def _int(value):
    try:
        return max(1, min(MAX_GRID, int(value)))
    except (TypeError, ValueError):
        return 1


def _pt(style, name):
    match = re.search(name + r"\s*:\s*([\d.]+)\s*pt", style, re.I)
    return float(match.group(1)) if match else None


def _border(style, side):
    """'border-top:solid #000000 1.70pt' → (굵기, 종류) 또는 None(선 없음)."""
    match = re.search(r"border-" + side + r"\s*:\s*([^;]+)", style, re.I)
    if not match:
        match = re.search(r"border\s*:\s*([^;]+)", style, re.I)
    if not match:
        return None
    value = match.group(1).lower()
    if "none" in value or "hidden" in value:
        return None
    size = re.search(r"([\d.]+)\s*pt", value)
    points = float(size.group(1)) if size else 0.5
    kind = "dash" if "dash" in value else "dot" if "dot" in value else "solid"
    if "double" in value:
        return ("double", "solid")
    # 한/글 0.12mm≈0.34pt(가는 선), 0.4mm≈1.13pt 이상은 굵은 선.
    return ("thick" if points >= 0.9 else "thin", kind)


def _place(rows):
    """병합을 풀어 각 칸의 (행, 열, 행 수, 열 수)를 정한다."""
    taken, cells = set(), []
    for r, row in enumerate(rows):
        c = 0
        for cell in row:
            while (r, c) in taken:
                c += 1
            rs, cs = cell["rowspan"], cell["colspan"]
            for dr in range(rs):
                for dc in range(cs):
                    taken.add((r + dr, c + dc))
            cells.append((r, c, rs, cs, cell))
            c += cs
    return cells


def _sizes(cells, count, axis, cell_mm):
    """열 폭·행 높이를 격자 칸 수로. 병합하지 않은 칸의 값을 먼저 쓰고, 모자라면 병합 칸으로 나눠 채운다."""
    measure = "width" if axis == "col" else "height"
    sizes = [None] * count
    for r, c, rs, cs, cell in cells:
        index, span = (c, cs) if axis == "col" else (r, rs)
        value = _pt(cell["style"], measure)
        if span == 1 and value and index < count:
            sizes[index] = max(sizes[index] or 0, value)
    for r, c, rs, cs, cell in cells:
        index, span = (c, cs) if axis == "col" else (r, rs)
        value = _pt(cell["style"], measure)
        missing = [i for i in range(index, min(count, index + span)) if sizes[i] is None]
        if value and missing:
            known = sum(sizes[i] or 0 for i in range(index, min(count, index + span)))
            share = max(0.0, value - known) / len(missing)
            for i in missing:
                sizes[i] = share or None
    fallback = 30.0 if axis == "col" else 20.0
    if axis == "row":
        # 행은 올림한다: 7mm 행을 5mm 한 칸으로 줄이면 글이 선에 겹쳐 고치기 어렵다.
        return [max(1, math.ceil((s or fallback) * PT_TO_MM / cell_mm - 0.2)) for s in sizes]
    return [max(1, round((s or fallback) * PT_TO_MM / cell_mm)) for s in sizes]


def sketch_from_html(html, cell_mm=5.0):
    """클립보드 HTML(문자열·바이트)에서 표그림판 그림 dict(grid·lines·texts)를 만든다."""
    if isinstance(html, bytes):
        html = html.decode("utf-8", errors="replace")
    if len(html) > 20 * 1024 * 1024:
        raise ValueError("복사한 내용이 너무 큽니다.")
    start = html.find("<!--StartFragment-->")
    parser = _TableParser()
    parser.feed(html[start:] if start >= 0 else html)
    rows = [row for row in parser.rows if row]
    if not rows:
        raise ValueError("클립보드에 한/글 표가 없습니다. 한/글에서 표를 선택해 복사(Ctrl+C)한 뒤 다시 눌러 주세요.")
    cells = _place(rows)
    n_rows = max(r + rs for r, _, rs, _, _ in cells)
    n_cols = max(c + cs for _, c, _, cs, _ in cells)
    widths, heights = _sizes(cells, n_cols, "col", cell_mm), _sizes(cells, n_rows, "row", cell_mm)
    xs, ys = [_MARGIN], [_MARGIN]
    for w in widths:
        xs.append(xs[-1] + w)
    for h in heights:
        ys.append(ys[-1] + h)
    if xs[-1] + _MARGIN > MAX_GRID or ys[-1] + _MARGIN > MAX_GRID:
        raise ValueError("표가 너무 커서 표그림판(200칸)에 들어가지 않습니다.")
    # 격자 한 칸 구간마다 선 서식을 정하고(이웃 칸이 다르면 굵은 쪽), 같은 서식끼리 이어 긋는다.
    rank = {"thin": 0, "thick": 1, "double": 2}
    segments = {}

    def mark(key, line):
        if line is None:
            return
        old = segments.get(key)
        if old is None or rank[line[0]] > rank[old[0]]:
            segments[key] = line

    texts = []
    for r, c, rs, cs, cell in cells:
        x0, x1, y0, y1 = xs[c], xs[c + cs], ys[r], ys[r + rs]
        for x in range(x0, x1):
            mark(("h", y0, x), _border(cell["style"], "top"))
            mark(("h", y1, x), _border(cell["style"], "bottom"))
        for y in range(y0, y1):
            mark(("v", x0, y), _border(cell["style"], "left"))
            mark(("v", x1, y), _border(cell["style"], "right"))
        text = "\n".join(line for line in cell["lines"] if line)
        if text:
            align = {"justify": "left"}.get(cell["align"], cell["align"]) or "center"
            texts.append({"x": x0, "y": y0, "text": text[:10000], "bold": cell["bold"], "align": align})
    lines = []
    for (kind, at, start), (width, style) in sorted(segments.items()):
        last = lines[-1] if lines else None
        if (last and last["_kind"] == kind and last["_at"] == at and last["width"] == width and last["style"] == style
                and last["_end"] == start):
            last["_end"] = start + 1
        else:
            lines.append({"_kind": kind, "_at": at, "_end": start + 1, "_start": start, "width": width, "style": style})
    result_lines = []
    for line in lines:
        if line["_kind"] == "h":
            coords = dict(x1=line["_start"], y1=line["_at"], x2=line["_end"], y2=line["_at"])
        else:
            coords = dict(x1=line["_at"], y1=line["_start"], x2=line["_at"], y2=line["_end"])
        result_lines.append({**coords, "width": line["width"], "style": line["style"]})
    grid = {"cols": max(36, xs[-1] + _MARGIN), "rows": max(50, ys[-1] + _MARGIN), "cell_mm": float(cell_mm)}
    return {"grid": grid, "lines": result_lines, "texts": texts, "images": [],
            "source": {"rows": n_rows, "cols": n_cols}}
