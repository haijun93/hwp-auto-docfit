"""HWPX 표의 반복 정보단위 판정과 XML 전용 크기 조절 (COM 불필요)."""

from __future__ import annotations

import copy
import re
from pathlib import Path

from defusedxml import ElementTree as ET

from . import table_catalog as catalog

HP = catalog._HP


def _sub(parent, tag, attrib=None):
    str_attrib = {k: str(v) for k, v in (attrib or {}).items()}
    child = parent.makeelement(tag, str_attrib)
    parent.append(child)
    return child


def _axis(start, core, count, sep=0, *, axis="row"):
    return dict(start=start, core=core, sep=sep, count=count, min=1,
                max=8 if axis == "col" else 40 // core)


def _plans():
    result = {}

    def add(name, row=None, col=None):
        result[name] = {"row": _axis(*row) if row else None,
                        "col": _axis(*col, axis="col") if col else None}

    add("분야별과제표 · 모양 1", col=(0, 3, 3, 1))
    add("분야별과제표 · 모양 2", col=(0, 3, 2, 1))
    add("표(가로) · 모양 1", (1, 1, 5), (0, 1, 5))
    add("표(가로) · 모양 2", (0, 1, 1), (0, 1, 4))
    add("표(가로) · 모양 3", col=(2, 2, 1))
    add("현황표(가로) · 모양 1", col=(0, 2, 2))
    add("행사시간표 · 모양 1", (1, 1, 6))
    for number, count in enumerate((5, 5, 4, 4, 6), 1):
        add(f"추진절차(가로) · 모양 {number}", col=(0, 1, count, 1))
    add("추진절차(가로세로) · 모양 1", col=(0, 1, 4, 1))
    add("추진절차(세로) · 모양 1", (1, 1, 12))
    add("신구대조표 · 모양 2", (2, 1, 3))
    add("신구대조표 · 모양 3", (1, 1, 6))
    add("일정표(연간) · 모양 1", (2, 1, 5), (1, 4, 5))
    add("일정표(월별) · 모양 1", (1, 4, 6), (2, 1, 6))
    add("일정표(주간) · 모양 1", (2, 1, 9), (1, 1, 6))
    add("일정표(일간) · 모양 1", (1, 2, 9))
    add("행사표(1일) · 모양 1", (1, 8, 2))
    for category, count in (("부연설명", 7), ("라벨 서식", 6), ("표(가로)", 3),
                            ("현황표(가로)", 1), ("신구대조표", 1), ("조직도", 1)):
        for number in range(1, count + 1):
            result.setdefault(f"{category} · 모양 {number}", {"row": None, "col": None})
    org_chart_plan = {"row": None, "col": {"count": 5, "min": 2, "max": 10, "core": 2, "sep": 1, "kind": "org_chart"}}
    result["조직도"] = org_chart_plan
    result["조직도 · 모양 2"] = org_chart_plan
    return result


PLANS = _plans()


def _flat(meta):
    return [c for row in meta for c in (row if isinstance(row, list) else [row])]


def _end(p):
    return p["start"] + p["count"] * (p["core"] + p["sep"]) - p["sep"]


def _cover(c, axis, p):
    lo, hi = c[axis], c[axis] + c[axis + "Span"]
    # With one remaining unit, remember which cells originally covered the region.
    if p["count"] == 1 and "_covers" in p:
        return (c["row"], c["col"]) in p["_covers"]
    return c[axis + "Span"] > 1 and lo <= p["start"] and hi >= _end(p)


def _validate(cells, length, axis, p):
    if (any(type(p.get(k)) is not int for k in ("start", "core", "sep", "count", "min", "max"))
            or p["start"] < 0 or p["core"] < 1 or p["sep"] < 0
            or not 1 <= p["min"] <= p["count"] <= p["max"] or _end(p) > length):
        raise ValueError("정보단위 계획의 범위가 표 구조와 맞지 않습니다.")
    boundaries = {p["start"], _end(p)}
    for i in range(p["count"]):
        start = p["start"] + i * (p["core"] + p["sep"])
        boundaries.update((start, start + p["core"]))
    for c in cells:
        if _cover(c, axis, p):
            continue
        lo, hi = c[axis], c[axis] + c[axis + "Span"]
        if any(lo < b < hi for b in boundaries):
            raise ValueError("정보단위 경계를 가로지르는 병합 칸이 있습니다.")


def _unit_signature(cells, axis, p, index):
    lo = p["start"] + index * (p["core"] + p["sep"])
    leading, trailing = ("top", "bottom") if axis == "row" else ("left", "right")
    signature = []
    for c in cells:
        if not lo <= c[axis] < lo + p["core"] or _cover(c, axis, p):
            continue
        borders = []
        for side in ("top", "bottom", "left", "right"):
            exterior = ((side == leading and c[axis] == p["start"])
                        or (side == trailing and c[axis] + c[axis + "Span"] == _end(p)))
            borders.append(None if exterior else c.get("borders", {}).get(side, {}).get("type", "NONE"))
        signature.append((c["row"] - (lo if axis == "row" else 0),
                          c["col"] - (lo if axis == "col" else 0),
                          c["rowSpan"], c["colSpan"], c.get("style", {}).get("fill", ""),
                          tuple(borders)))
    return tuple(sorted(signature))


def _matching_signatures(signatures):
    # Only the region's two exterior edges are wildcards. All observed internal
    # and lateral edges must agree, including comparisons between middle units.
    if not signatures[0] or any(len(s) != len(signatures[0]) for s in signatures):
        return False
    for corresponding in zip(*signatures):
        if any(c[:5] != corresponding[0][:5] for c in corresponding):
            return False
        for edges in zip(*(c[5] for c in corresponding)):
            if len({edge for edge in edges if edge is not None}) > 1:
                return False
    return True


def detect_plan(cell_meta, rows, cols) -> dict:
    """글과 폭을 제외한 칸 구조·채움색·테두리 종류의 반복을 찾는다."""
    cells = _flat(cell_meta)
    result = {"row": None, "col": None}
    for axis, length in (("row", rows), ("col", cols)):
        best = None
        for start in range(3):
            for core in range(1, 5):
                for sep in range(2):
                    limit = min((length - start + sep) // (core + sep),
                                8 if axis == "col" else 40 // core)
                    for count in range(limit, 1, -1):
                        p = _axis(start, core, count, sep, axis=axis)
                        try:
                            _validate(cells, length, axis, p)
                        except ValueError:
                            continue
                        signatures = [_unit_signature(cells, axis, p, i) for i in range(count)]
                        if _matching_signatures(signatures):
                            score = (count, count * core + (count - 1) * sep, -start, -sep)
                            if best is None or score > best[0]:
                                best = (score, p)
                            break
        result[axis] = best[1] if best else None
    return result


def plan_for(template) -> dict:
    name = template.get("name")
    if name in PLANS:
        plan = copy.deepcopy(PLANS[name])
    elif template.get("category") == "조직도" and template.get("cols") == 14:
        plan = {"row": None, "col": {"count": 5, "min": 2, "max": 10, "core": 2, "sep": 1, "kind": "org_chart"}}
    else:
        plan = detect_plan(template["cell_meta"], template["rows"], template["cols"])

    for axis, length in (("row", template["rows"]), ("col", template["cols"])):
        if plan[axis] is not None:
            if plan[axis].get("kind") == "org_chart":
                continue
            try:
                _validate(_flat(template["cell_meta"]), length, axis, plan[axis])
            except ValueError:
                plan[axis] = None
    return plan


def _cells(table):
    return [(r, c) for r in table.findall(HP + "tr") for c in r.findall(HP + "tc")]


def _meta(table):
    return [catalog._cell_meta(c, 0, 0, "", None) for _, c in _cells(table)]


def _sizes(table, axis):
    """단일 행·열 실측을 우선하고 병합 칸의 크기로 나머지를 복원한다."""
    length = int(table.get(axis + "Cnt"))
    dim = "height" if axis == "row" else "width"
    cells = _meta(table)
    values = [None] * length
    for c in cells:
        if c[axis + "Span"] == 1:
            values[c[axis]] = c[dim]
    # Spanning cells supply the missing grid widths/heights where possible.
    for _ in range(length):
        changed = False
        for c in cells:
            indices = range(c[axis], c[axis] + c[axis + "Span"])
            missing = [i for i in indices if values[i] is None]
            if len(missing) == 1:
                values[missing[0]] = max(1, c[dim] - sum(values[i] or 0 for i in indices))
                changed = True
        if not changed:
            break
    for c in cells:
        indices = range(c[axis], c[axis] + c[axis + "Span"])
        missing = [i for i in indices if values[i] is None]
        if missing:
            remaining = max(len(missing), c[dim] - sum(values[i] or 0 for i in indices))
            for j, i in enumerate(missing):
                values[i] = remaining // len(missing) + (j < remaining % len(missing))
    if any(v is None for v in values):
        raise ValueError("표의 행 높이 또는 열 너비를 구할 수 없습니다.")
    return values


def _integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class _ObjectIds:
    def __init__(self, roots):
        self.used = set()
        self.next_id = 1
        self.z_order = -1
        for root in roots:
            for node in root.iter():
                for attr in ("id", "instId"):
                    value = _integer(node.get(attr))
                    if value is not None:
                        self.used.add(value)
                value = _integer(node.get("zOrder"))
                if value is not None:
                    self.z_order = max(self.z_order, value)

    def renew(self, root):
        for node in root.iter():
            # Paragraph/list IDs are HWPX sentinels, not drawing object IDs.
            if not node.tag.startswith(HP) or node.tag in (HP + "p", HP + "subList"):
                continue
            for attr in ("id", "instId"):
                if _integer(node.get(attr)) is not None:
                    while self.next_id in self.used:
                        self.next_id += 1
                    node.set(attr, str(self.next_id))
                    self.used.add(self.next_id)
                    self.next_id += 1
            if _integer(node.get("zOrder")) is not None:
                self.z_order += 1
                node.set("zOrder", str(self.z_order))


def _scale_nested_tables(cell, old_width, new_width):
    if old_width == new_width:
        return
    if old_width <= 0:
        raise ValueError("중첩 표의 바깥 칸 너비가 0 이하입니다.")
    for table in catalog._top_tables(cell):
        sz = table.find(HP + "sz")
        total = int(sz.get("width")) * new_width // old_width
        sizes = _sizes(table, "col")
        weight = sum(sizes)
        if weight <= 0:
            raise ValueError("중첩 표의 열 너비가 0 이하입니다.")
        # Shared boundaries preserve merged cells and correct rounding per row.
        edges = [0]
        for width in sizes:
            edges.append(edges[-1] + width)
        edges = [edge * total // weight for edge in edges]
        sz.set("width", str(total))
        for _, nested_cell in _cells(table):
            addr = nested_cell.find(HP + "cellAddr")
            span = nested_cell.find(HP + "cellSpan")
            lo = int(addr.get("colAddr"))
            hi = lo + int(span.get("colSpan"))
            cell_sz = nested_cell.find(HP + "cellSz")
            old = int(cell_sz.get("width"))
            new = edges[hi] - edges[lo]
            _scale_nested_tables(nested_cell, old, new)
            cell_sz.set("width", str(new))


_TOKENS = re.compile(r"[0-9]+:[0-5][0-9]|[0-9]+|[①-⑳]|[Ⅰ-Ⅻ]")


def _token_value(token):
    if ":" in token:
        hour, minute = map(int, token.split(":"))
        return hour * 60 + minute
    if "①" <= token <= "⑳":
        return ord(token) - ord("①") + 1
    if "Ⅰ" <= token <= "Ⅻ":
        return ord(token) - ord("Ⅰ") + 1
    return int(token)


def _increment_text(text, previous=None, steps=1):
    """같은 위치의 토큰 간격을 외삽한다. 시각은 자정 이후에도 24+시를 유지한다."""
    matches = list(_TOKENS.finditer(text))
    before = list(_TOKENS.finditer(previous or ""))
    def replace(index, match):
        token = match.group()
        value = _token_value(token)
        delta = 1
        if len(before) == len(matches):
            old = before[index].group()
            if (":" in old) == (":" in token):
                delta = value - _token_value(old) or 1
        month = text[match.end():].startswith("월")
        if month:
            delta = delta % 12 or 1
        value += delta * steps
        if ":" in token:
            return f"{value // 60:02d}:{value % 60:02d}"
        if "①" <= token <= "⑳":
            return chr(ord("①") + (value - 1) % 20)
        if "Ⅰ" <= token <= "Ⅻ":
            return chr(ord("Ⅰ") + (value - 1) % 12)
        if month:
            value = (value - 1) % 12 + 1
        return str(value).zfill(len(token)) if token.startswith("0") else str(value)
    result = text
    for index, match in reversed(list(enumerate(matches))):
        result = result[:match.start()] + replace(index, match) + result[match.end():]
    return result


def _fill_clone(cell, previous, fill, steps):
    if fill == "copy":
        return
    nodes = list(cell.iter(HP + "t"))
    for paragraph in cell.iter(HP + "p"):
        for cache in paragraph.findall(HP + "linesegarray"):
            paragraph.remove(cache)
    if fill == "blank":
        for node in nodes:
            node.text = ""
        return
    old_nodes = list(previous.iter(HP + "t")) if previous is not None else []
    # Process paragraphs together so tokens split across character-format runs work.
    for paragraph in cell.iter(HP + "p"):
        texts = [n for run in paragraph.findall(HP + "run") for n in run.findall(HP + "t")]
        if not texts:
            continue
        text = "".join(n.text or "" for n in texts)
        prior = "".join(old_nodes[nodes.index(n)].text or "" for n in texts
                        if nodes.index(n) < len(old_nodes)) if old_nodes else None
        offsets, offset = [], 0
        for node in texts:
            offsets.append(offset)
            offset += len(node.text or "")
        # Replace each token in its original run; unrelated text/run formatting stays intact.
        updated = _increment_text(text, prior, steps)
        new_matches = list(_TOKENS.finditer(updated))
        for match, new in reversed(list(zip(_TOKENS.finditer(text), new_matches))):
            for index in reversed(range(len(texts))):
                lo, hi = max(match.start(), offsets[index]), min(match.end(), offsets[index] + len(texts[index].text or ""))
                if lo < hi:
                    value = texts[index].text or ""
                    insert = new.group() if lo == match.start() else ""
                    texts[index].text = value[:lo - offsets[index]] + insert + value[hi - offsets[index]:]


def validate_input(fill="increment", cell_texts=None):
    if not isinstance(fill, str) or fill not in ("increment", "blank", "copy"):
        raise ValueError("글 처리 방식은 increment, blank, copy 중에서 골라 주세요.")
    if cell_texts is None:
        return
    if not isinstance(cell_texts, dict) or len(cell_texts) > 200:
        raise ValueError("칸 글은 200개 이하의 좌표별 글로 지정해 주세요.")
    for key, value in cell_texts.items():
        if (not isinstance(key, str) or not re.fullmatch(r"[0-9]{1,3},[0-9]{1,3}", key)
                or not isinstance(value, str) or len(value) > 1000
                or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value)):
            raise ValueError("칸 좌표와 글을 확인해 주세요(칸당 1000자 이하).")


def _apply_texts(table, cell_texts):
    """API 좌표는 XML의 칸 순번이 아니라 병합 칸의 실제 왼쪽 위 좌표다."""
    positions = {}
    for i, row in enumerate(table.findall(HP + "tr")):
        for j, cell in enumerate(row.findall(HP + "tc")):
            addr = cell.find(HP + "cellAddr")
            positions[(int(addr.get("rowAddr")), int(addr.get("colAddr")))] = (i, j, cell)
    for key, value in (cell_texts or {}).items():
        position = tuple(map(int, key.split(",")))
        if position not in positions:
            raise ValueError("입력할 칸의 왼쪽 위 좌표를 찾을 수 없습니다.")
        i, j, cell = positions[position]
        lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        catalog._apply_cell_edits(table, {f"{i}:{j}": lines[0]})
        paragraphs = catalog._cell_paragraphs(cell)
        for paragraph in paragraphs:
            for cache in paragraph.findall(HP + "linesegarray"):
                paragraph.remove(cache)
        if len(lines) > 1:
            first = paragraphs[0]
            parent = next(n for n in cell.iter() if first in list(n))
            for offset, line in enumerate(lines[1:], 1):
                new = copy.deepcopy(first)
                for n in new.iter(HP + "t"):
                    n.text = ""
                next(new.iter(HP + "t")).text = line
                parent.insert(list(parent).index(first) + offset, new)


def _resize_axis(table, axis, p, target, object_ids, fill):
    cells = _meta(table)
    _validate(cells, int(table.get(axis + "Cnt")), axis, p)
    old_count, core, sep, start = (p[k] for k in ("count", "core", "sep", "start"))
    end = _end(p)
    stride = core + sep
    originals_by_pos = {(int(c.find(HP + "cellAddr").get("rowAddr")),
                         int(c.find(HP + "cellAddr").get("colAddr"))): copy.deepcopy(c)
                        for _, c in _cells(table)}
    def fill_cell(cell, steps):
        addr = cell.find(HP + "cellAddr")
        key = [int(addr.get("rowAddr")), int(addr.get("colAddr"))]
        if not end - core <= key[0 if axis == "row" else 1] < end:
            return
        key[0 if axis == "row" else 1] -= stride
        previous = originals_by_pos.get(tuple(key)) if old_count > 1 else None
        _fill_clone(cell, previous, fill, steps)
    delta = (target - old_count) * stride
    covers = {(c["row"], c["col"]) for c in cells if _cover(c, axis, p)}
    sizes = _sizes(table, axis)
    rows = table.findall(HP + "tr")
    # Cache separator prototypes in the caller's plan so 2 -> 1 -> N is reversible.
    if sep and old_count > 1:
        sep_start = end - core - sep
        if axis == "row":
            prototype = [copy.deepcopy(r) for r in rows[sep_start:sep_start + sep]]
        else:
            prototype = [[copy.deepcopy(c) for c in r.findall(HP + "tc")
                          if sep_start <= int(c.find(HP + "cellAddr").get("colAddr")) < sep_start + sep]
                         for r in rows]
        p["_separator"] = (sep_start, prototype, sizes[sep_start:sep_start + sep])
    if target > old_count and sep and "_separator" not in p:
        raise ValueError("구분 줄의 복제 원본이 없습니다. 원본 템플릿에서 다시 조절해 주세요.")

    def adjust(cell, shift=0, covering=False):
        addr = cell.find(HP + "cellAddr")
        addr.set(axis + "Addr", str(int(addr.get(axis + "Addr")) + shift))
        if covering:
            span = cell.find(HP + "cellSpan")
            span.set(axis + "Span", str(int(span.get(axis + "Span")) + delta))

    last_start = end - core
    if axis == "row":
        last_rows = [copy.deepcopy(r) for r in rows[last_start:end]]
        if target < old_count:
            cut = start + target * stride - sep
            for r in rows[cut:end]:
                table.remove(r)
        else:
            insert_at = list(table).index(rows[end]) if end < len(rows) else list(table).index(rows[-1]) + 1
            for i in range(old_count, target):
                pieces = []
                if sep:
                    origin, prototype, _ = p["_separator"]
                    pieces.extend((r, start + i * stride - sep - origin) for r in copy.deepcopy(prototype))
                pieces.extend((r, (i - old_count + 1) * stride) for r in copy.deepcopy(last_rows))
                for r, shift in pieces:
                    for c in list(r.findall(HP + "tc")):
                        addr = c.find(HP + "cellAddr")
                        if (int(addr.get("rowAddr")), int(addr.get("colAddr"))) in covers:
                            r.remove(c)
                        else:
                            fill_cell(c, i - old_count + 1)
                            adjust(c, shift)
                    object_ids.renew(r)
                    table.insert(insert_at, r)
                    insert_at += 1
        for r, c in [(r, c) for r in rows for c in r.findall(HP + "tc") if r in list(table)]:
            addr = c.find(HP + "cellAddr")
            key = (int(addr.get("rowAddr")), int(addr.get("colAddr")))
            if key in covers:
                adjust(c, covering=True)
            elif key[0] >= end:
                adjust(c, delta)
    else:
        for r_index, r in enumerate(rows):
            originals = list(r.findall(HP + "tc"))
            last = [copy.deepcopy(c) for c in originals
                    if last_start <= int(c.find(HP + "cellAddr").get("colAddr")) < end
                    and (int(c.find(HP + "cellAddr").get("rowAddr")),
                         int(c.find(HP + "cellAddr").get("colAddr"))) not in covers]
            for c in originals:
                addr = c.find(HP + "cellAddr")
                key = (int(addr.get("rowAddr")), int(addr.get("colAddr")))
                if key in covers:
                    adjust(c, covering=True)
                elif target < old_count and start + target * stride - sep <= key[1] < end:
                    r.remove(c)
                elif key[1] >= end:
                    adjust(c, delta)
            if target > old_count:
                for i in range(old_count, target):
                    pieces = []
                    if sep:
                        origin, prototype, _ = p["_separator"]
                        pieces.extend((c, start + i * stride - sep - origin)
                                      for c in copy.deepcopy(prototype[r_index]))
                    pieces.extend((c, (i - old_count + 1) * stride) for c in copy.deepcopy(last))
                    for c, shift in pieces:
                        fill_cell(c, i - old_count + 1)
                        adjust(c, shift)
                        object_ids.renew(c)
                        r.append(c)
            ordered = sorted(r.findall(HP + "tc"), key=lambda c: int(c.find(HP + "cellAddr").get("colAddr")))
            for c in r.findall(HP + "tc"):
                r.remove(c)
            r.extend(ordered)

    if target < old_count:
        sizes = sizes[:start + target * stride - sep] + sizes[end:]
    else:
        extra = []
        for _ in range(target - old_count):
            extra.extend(p["_separator"][2] if sep else [])
            extra.extend(sizes[last_start:end])
        sizes = sizes[:end] + extra + sizes[end:]
    table.set(axis + "Cnt", str(len(sizes)))
    p["count"] = target
    p["_covers"] = covers
    sz = table.find(HP + "sz")
    if axis == "col":
        total = int(sz.get("width"))
        indices = [start + i * stride + j for i in range(target) for j in range(core)]
        variable = set(indices)
        fixed = sum(v for i, v in enumerate(sizes) if i not in variable)
        available, weight = total - fixed, sum(sizes[i] for i in indices)
        if available < len(indices):
            raise ValueError("표 폭이 정보단위를 배치하기에 부족합니다.")
        allocated = previous = 0
        for i in indices:
            allocated += sizes[i] * available
            # Cumulative rounding keeps every column integral and the sum exact.
            value = allocated // weight
            sizes[i] = value - previous
            previous = value
        if any(v <= 0 for v in sizes):
            raise ValueError("정보단위 열 너비가 0 이하입니다.")
    else:
        sz.set("height", str(sum(sizes)))
    dim = "height" if axis == "row" else "width"
    for _, cell in _cells(table):
        addr, span = cell.find(HP + "cellAddr"), cell.find(HP + "cellSpan")
        lo = int(addr.get(axis + "Addr"))
        hi = lo + int(span.get(axis + "Span"))
        cell_sz = cell.find(HP + "cellSz")
        new_size = sum(sizes[lo:hi])
        if axis == "col":
            _scale_nested_tables(cell, int(cell_sz.get("width")), new_size)
        cell_sz.set(dim, str(new_size))


def generate_org_chart(template_table_element, team_count, *, fill="increment", cell_texts=None, id_roots=()):
    """기준 표(모양 2)의 XML에서 역할별 칸 서식을 뽑아 N팀(2~10)짜리 조직도 표를 새로 조립한다."""
    validate_input(fill, cell_texts)
    if type(team_count) is not int or not 2 <= team_count <= 10:
        raise ValueError("조직도 팀 수는 2~10 사이 정수로 지정해 주세요.")

    tbl = template_table_element
    sz = tbl.find(HP + "sz")
    total_width = int(sz.get("width")) if sz is not None else 50333

    rows = tbl.findall(HP + "tr")
    if len(rows) < 6:
        raise ValueError("기준 조직도 표 구조(6행)를 찾을 수 없습니다.")

    row_heights = []
    for r in rows:
        tc = r.find(HP + "tc")
        csz = tc.find(HP + "cellSz") if tc is not None else None
        h = int(csz.get("height")) if csz is not None else 282
        row_heights.append(h)

    source_cells = {}
    for r_idx, r in enumerate(rows):
        for tc in r.findall(HP + "tc"):
            addr = tc.find(HP + "cellAddr")
            if addr is not None:
                source_cells[(int(addr.get("rowAddr")), int(addr.get("colAddr")))] = tc

    def proto(r, c):
        if (r, c) in source_cells:
            return source_cells[(r, c)]
        row_tcs = [tc for (row_idx, col_idx), tc in source_cells.items() if row_idx == r]
        return row_tcs[0] if row_tcs else list(source_cells.values())[0]

    top_box_tc = proto(1, 4)
    top_box_parts = [n.text or "" for n in catalog._cell_text_nodes(top_box_tc)]
    top_box_text = " ".join("".join(top_box_parts).split()) or "지역경제과"

    orig_cols = [0, 3, 6, 9, 12]
    orig_team_names = []
    orig_team_counts = []
    for c in orig_cols:
        if (4, c) in source_cells:
            t_str = " ".join("".join(n.text or "" for n in catalog._cell_text_nodes(source_cells[(4, c)])).split())
            if t_str:
                orig_team_names.append(t_str)
        if (5, c) in source_cells:
            cnt_str = " ".join("".join(n.text or "" for n in catalog._cell_text_nodes(source_cells[(5, c)])).split())
            if cnt_str:
                orig_team_counts.append(cnt_str)

    if not orig_team_names:
        orig_team_names = ["경제총괄팀", "시장경영팀", "시장시설팀", "동물보호팀", "생활경제팀"]
    if not orig_team_counts:
        orig_team_counts = ["(6명)", "(4명)", "(3명)", "(4명)", "(4명)"]

    team_names = []
    team_counts = []
    for i in range(team_count):
        if i < len(orig_team_names):
            t_name = orig_team_names[i]
            t_count = orig_team_counts[min(i, len(orig_team_counts) - 1)]
        else:
            steps = i - len(orig_team_names) + 1
            if fill == "blank":
                t_name, t_count = "", ""
            elif fill == "copy":
                t_name = orig_team_names[-1]
                t_count = orig_team_counts[-1]
            else:
                t_name = _increment_text(orig_team_names[-1], steps=steps)
                t_count = _increment_text(orig_team_counts[-1], steps=steps)
        team_names.append(t_name)
        team_counts.append(t_count)

    is_even = (team_count % 2 == 0)
    team_cols = {}
    gap_cols = {}
    weights = []
    cur = 0
    for t in range(team_count):
        team_cols[t] = (cur, cur + 1)
        weights.extend([8345, 8345])
        cur += 2
        if t < team_count - 1:
            if is_even and t == (team_count // 2) - 1:
                gap_cols[t] = [cur, cur + 1]
                weights.extend([2152, 2152])
                cur += 2
            else:
                gap_cols[t] = [cur]
                weights.append(4304)
                cur += 1

    total_cols = cur
    total_w = sum(weights)
    col_widths = []
    alloc = prev = 0
    for w in weights:
        alloc += w * total_width
        val = alloc // total_w
        col_widths.append(val - prev)
        prev = val

    def get_w(col, span):
        return sum(col_widths[col : col + span])

    if is_even:
        t_L = (team_count // 2) - 1
        t_R = team_count // 2
    else:
        t_mid = team_count // 2
        t_L = t_mid - 1
        t_R = t_mid + 1
    box_start = team_cols[t_L][1]
    box_end = team_cols[t_R][0]
    box_span = box_end - box_start + 1

    def make_cell(proto_tc, row_addr, col_addr, row_span, col_span, width, height, text=None):
        new_tc = copy.deepcopy(proto_tc)
        addr = new_tc.find(HP + "cellAddr")
        if addr is None:
            addr = _sub(new_tc, HP + "cellAddr")
        addr.set("rowAddr", str(row_addr))
        addr.set("colAddr", str(col_addr))

        span = new_tc.find(HP + "cellSpan")
        if span is None:
            span = _sub(new_tc, HP + "cellSpan")
        span.set("rowSpan", str(row_span))
        span.set("colSpan", str(col_span))

        sz_el = new_tc.find(HP + "cellSz")
        if sz_el is None:
            sz_el = _sub(new_tc, HP + "cellSz")
        sz_el.set("width", str(width))
        sz_el.set("height", str(height))

        if text is not None:
            for p in new_tc.iter(HP + "p"):
                for cache in p.findall(HP + "linesegarray"):
                    p.remove(cache)
            t_nodes = list(new_tc.iter(HP + "t"))
            if t_nodes:
                t_nodes[0].text = text
                for n in t_nodes[1:]:
                    n.text = ""
            else:
                p = new_tc.find(".//" + HP + "p")
                if p is None:
                    subList = new_tc.find(HP + "subList")
                    if subList is None:
                        subList = _sub(new_tc, HP + "subList")
                    p = _sub(subList, HP + "p")
                run = _sub(p, HP + "run")
                t_el = _sub(run, HP + "t")
                t_el.text = text
        return new_tc

    # Row 0
    r0_cells = []
    for col in range(box_start):
        r0_cells.append(make_cell(proto(0, 0), 0, col, 1, 1, get_w(col, 1), row_heights[0]))
    r0_cells.append(make_cell(proto(0, 4), 0, box_start, 1, 1, get_w(box_start, 1), row_heights[0]))
    if box_span > 2:
        r0_cells.append(make_cell(proto(0, 5), 0, box_start + 1, 1, box_span - 2, get_w(box_start + 1, box_span - 2), row_heights[0]))
    r0_cells.append(make_cell(proto(0, 9), 0, box_end, 1, 1, get_w(box_end, 1), row_heights[0]))
    for col in range(box_end + 1, total_cols):
        r0_cells.append(make_cell(proto(0, 0), 0, col, 1, 1, get_w(col, 1), row_heights[0]))

    # Row 1
    r1_cells = []
    for col in range(box_start - 1):
        r1_cells.append(make_cell(proto(1, 0), 1, col, 1, 1, get_w(col, 1), row_heights[1]))
    r1_cells.append(make_cell(proto(1, 3), 1, box_start - 1, 1, 1, get_w(box_start - 1, 1), row_heights[1]))
    r1_cells.append(make_cell(proto(1, 4), 1, box_start, 1, box_span, get_w(box_start, box_span), row_heights[1], text=top_box_text))
    r1_cells.append(make_cell(proto(1, 10), 1, box_end + 1, 1, 1, get_w(box_end + 1, 1), row_heights[1]))
    for col in range(box_end + 2, total_cols):
        r1_cells.append(make_cell(proto(1, 0), 1, col, 1, 1, get_w(col, 1), row_heights[1]))

    # Row 2
    r2_cells = []
    first_mid = team_cols[0][1]
    last_mid = team_cols[team_count - 1][0]
    for col in range(first_mid):
        r2_cells.append(make_cell(proto(2, 0), 2, col, 1, 1, get_w(col, 1), row_heights[2]))
    if not is_even:
        t_mid = team_count // 2
        cL, cR = team_cols[t_mid]
        gap_L = gap_cols[t_mid - 1][0]
        gap_R = gap_cols[t_mid][0]
        for col in range(first_mid, gap_L):
            p = proto(2, 4) if (box_start <= col <= box_end) else proto(2, 1)
            r2_cells.append(make_cell(p, 2, col, 1, 1, get_w(col, 1), row_heights[2]))
        r2_cells.append(make_cell(proto(2, 5), 2, gap_L, 1, 2, get_w(gap_L, 2), row_heights[2]))
        r2_cells.append(make_cell(proto(2, 7), 2, cR, 1, 2, get_w(cR, 2), row_heights[2]))
        for col in range(gap_R + 1, last_mid + 1):
            p = proto(2, 9) if (box_start <= col <= box_end) else proto(2, 10)
            r2_cells.append(make_cell(p, 2, col, 1, 1, get_w(col, 1), row_heights[2]))
    else:
        g_mid = (team_count // 2) - 1
        mid_L, mid_R = gap_cols[g_mid]
        for col in range(first_mid, mid_L):
            p = proto(2, 4) if (box_start <= col <= box_end) else proto(2, 1)
            r2_cells.append(make_cell(p, 2, col, 1, 1, get_w(col, 1), row_heights[2]))
        r2_cells.append(make_cell(proto(2, 5), 2, mid_L, 1, 1, get_w(mid_L, 1), row_heights[2]))
        r2_cells.append(make_cell(proto(2, 7), 2, mid_R, 1, 1, get_w(mid_R, 1), row_heights[2]))
        for col in range(mid_R + 1, last_mid + 1):
            p = proto(2, 9) if (box_start <= col <= box_end) else proto(2, 10)
            r2_cells.append(make_cell(p, 2, col, 1, 1, get_w(col, 1), row_heights[2]))
    for col in range(last_mid + 1, total_cols):
        r2_cells.append(make_cell(proto(2, 13), 2, col, 1, 1, get_w(col, 1), row_heights[2]))

    # Row 3
    r3_cells = []
    t_mid = (team_count // 2) if not is_even else -1
    for t in range(team_count):
        cL, cR = team_cols[t]
        if not is_even and t == t_mid:
            gap_L = gap_cols[t - 1][0]
            gap_R = gap_cols[t][0]
            r3_cells.append(make_cell(proto(3, 5), 3, gap_L, 1, 2, get_w(gap_L, 2), row_heights[3]))
            r3_cells.append(make_cell(proto(3, 7), 3, cR, 1, 2, get_w(cR, 2), row_heights[3]))
        else:
            if t == 0:
                pL, pR = proto(3, 0), proto(3, 1)
            elif t == team_count - 1:
                pL, pR = proto(3, 12), proto(3, 13)
            else:
                pL, pR = proto(3, 3), proto(3, 4)
            r3_cells.append(make_cell(pL, 3, cL, 1, 1, get_w(cL, 1), row_heights[3]))
            r3_cells.append(make_cell(pR, 3, cR, 1, 1, get_w(cR, 1), row_heights[3]))
        if t < team_count - 1:
            if not is_even and (t == t_mid - 1 or t == t_mid):
                pass
            elif is_even and t == (team_count // 2) - 1:
                g_col = gap_cols[t][0]
                r3_cells.append(make_cell(proto(3, 2), 3, g_col, 1, 2, get_w(g_col, 2), row_heights[3]))
            else:
                g_col = gap_cols[t][0]
                r3_cells.append(make_cell(proto(3, 2), 3, g_col, 1, 1, get_w(g_col, 1), row_heights[3]))

    # Row 4
    r4_cells = []
    for t in range(team_count):
        cL, cR = team_cols[t]
        proto_t = proto(4, min(t * 3, 12))
        r4_cells.append(make_cell(proto_t, 4, cL, 1, 2, get_w(cL, 2), row_heights[4], text=team_names[t]))
        if t < team_count - 1:
            if is_even and t == (team_count // 2) - 1:
                g_col = gap_cols[t][0]
                r4_cells.append(make_cell(proto(4, 2), 4, g_col, 1, 2, get_w(g_col, 2), row_heights[4], text=""))
            else:
                g_col = gap_cols[t][0]
                r4_cells.append(make_cell(proto(4, 2), 4, g_col, 1, 1, get_w(g_col, 1), row_heights[4], text=""))

    # Row 5
    r5_cells = []
    for t in range(team_count):
        cL, cR = team_cols[t]
        proto_c = proto(5, min(t * 3, 12))
        r5_cells.append(make_cell(proto_c, 5, cL, 1, 2, get_w(cL, 2), row_heights[5], text=team_counts[t]))
        if t < team_count - 1:
            if is_even and t == (team_count // 2) - 1:
                g_col = gap_cols[t][0]
                r5_cells.append(make_cell(proto(5, 2), 5, g_col, 1, 2, get_w(g_col, 2), row_heights[5], text=""))
            else:
                g_col = gap_cols[t][0]
                r5_cells.append(make_cell(proto(5, 2), 5, g_col, 1, 1, get_w(g_col, 1), row_heights[5], text=""))

    new_table = copy.deepcopy(template_table_element)
    new_table.set("rowCnt", "6")
    new_table.set("colCnt", str(total_cols))
    sz_el = new_table.find(HP + "sz")
    if sz_el is not None:
        sz_el.set("width", str(total_width))
        sz_el.set("height", str(sum(row_heights)))

    table_rows = new_table.findall(HP + "tr")
    all_rows = [r0_cells, r1_cells, r2_cells, r3_cells, r4_cells, r5_cells]
    for r_idx, r_elem in enumerate(table_rows[:6]):
        for old_tc in list(r_elem.findall(HP + "tc")):
            r_elem.remove(old_tc)
        for new_tc in all_rows[r_idx]:
            r_elem.append(new_tc)

    if cell_texts:
        _apply_texts(new_table, cell_texts)

    object_ids = _ObjectIds((*id_roots, new_table))
    object_ids.renew(new_table)
    return new_table


def resize_table(tbl_element, plan, row_count=None, col_count=None, *, id_roots=(), fill="increment", cell_texts=None):
    """제자리 변경. plan의 count와 내부 복제 원본도 갱신하여 연속 조절을 지원한다.

    잘못된 요청은 원본 요소와 plan을 바꾸지 않는다.
    """
    validate_input(fill, cell_texts)
    working, updated = copy.deepcopy(tbl_element), copy.deepcopy(plan)
    object_ids = _ObjectIds((*id_roots, working))
    col_plan = updated.get("col")
    if col_plan and col_plan.get("kind") == "org_chart":
        if row_count is not None:
            raise ValueError("이 표에는 조절할 행 정보단위가 없습니다.")
        if col_count is not None:
            if type(col_count) is not int or not col_plan["min"] <= col_count <= col_plan["max"]:
                raise ValueError(f"정보단위 개수는 {col_plan['min']}~{col_plan['max']} 사이 정수로 지정해 주세요.")
            target_count = col_count
        else:
            target_count = col_plan["count"]
        working = generate_org_chart(working, target_count, fill=fill, cell_texts=cell_texts, id_roots=id_roots)
        col_plan["count"] = target_count
        tbl_element.attrib.clear()
        tbl_element.attrib.update(working.attrib)
        tbl_element[:] = list(working)
        plan.clear()
        plan.update(updated)
        return
    for axis, target in (("row", row_count), ("col", col_count)):
        if target is None:
            continue
        p = updated.get(axis)
        if p is None:
            raise ValueError("이 표에는 조절할 " + ("행" if axis == "row" else "열") + " 정보단위가 없습니다.")
        if type(target) is not int or not p["min"] <= target <= p["max"]:
            raise ValueError(f"정보단위 개수는 {p['min']}~{p['max']} 사이 정수로 지정해 주세요.")
        if target != p["count"]:
            _resize_axis(working, axis, p, target, object_ids, fill)
        else:
            _validate(_meta(working), int(working.get(axis + "Cnt")), axis, p)
    _apply_texts(working, cell_texts)
    tbl_element.attrib.clear()
    tbl_element.attrib.update(working.attrib)
    tbl_element[:] = list(working)
    plan.clear()
    plan.update(updated)


def _load(template_id, catalog_path):
    source = Path(catalog_path or catalog.default_catalog_path())
    record = catalog._find_template(catalog._scan(source), str(template_id))
    with catalog._safe_archive(source) as archive:
        root = ET.fromstring(archive.read(record["section"]))
        table = catalog._top_tables(root.findall(HP + "p")[record["paragraph_index"]])[record["table_index"]]
        header = ET.fromstring(archive.read("Contents/header.xml")) if "Contents/header.xml" in archive.namelist() else None
    return record, table, catalog._header_lookup(header)


def export_resized(template_id, output_path, catalog_path=None, row_count=None, col_count=None, *, fill="increment", cell_texts=None) -> Path:
    validate_input(fill, cell_texts)
    record, _, _ = _load(template_id, catalog_path)
    plan = plan_for(record)
    # Other sections and header definitions may survive the catalog export.
    source = Path(catalog_path or catalog.default_catalog_path())
    with catalog._safe_archive(source) as archive:
        roots = [ET.fromstring(archive.read(name)) for name in archive.namelist()
                 if name.lower().endswith(".xml")]
    return catalog.export_template(template_id, output_path, catalog_path,
        table_transform=lambda table: resize_table(table, plan, row_count, col_count, id_roots=roots,
                                                   fill=fill, cell_texts=cell_texts))


def preview(template_id, catalog_path=None, row_count=None, col_count=None, *, fill="increment", cell_texts=None) -> dict:
    validate_input(fill, cell_texts)
    record, table, header = _load(template_id, catalog_path)
    resize_table(table, plan_for(record), row_count, col_count, fill=fill, cell_texts=cell_texts)
    result = {k: record[k] for k in ("id", "name")}
    # Unlike the catalog's compact preview, return every resized cell.
    result.update(rows=int(table.get("rowCnt")), cols=int(table.get("colCnt")), cells=[], cell_meta=[])
    for i, row in enumerate(table.findall(HP + "tr")):
        texts, meta = [], []
        for j, cell in enumerate(row.findall(HP + "tc")):
            text = " ".join("".join(n.text or "" for n in catalog._cell_text_nodes(cell)).split())[:80]
            texts.append(text)
            item = catalog._cell_meta(cell, i, j, text, header)
            nested = catalog._top_tables(cell)
            if nested:
                item["nested"] = [_nested_preview(t, header) for t in nested]
            meta.append(item)
        result["cells"].append(texts)
        result["cell_meta"].append(meta)
    return result


def _nested_preview(table, header):
    return {"rows": int(table.get("rowCnt")), "cols": int(table.get("colCnt")),
            "cell_meta": [[catalog._cell_meta(c, i, j, catalog._text(c), header)
                           for j, c in enumerate(r.findall(HP + "tc"))]
                          for i, r in enumerate(table.findall(HP + "tr"))]}


def _select_org_chart_record(org_records):
    """조직도 목록 중 기준 1개(모양 2 — 이름이 바뀌면 3N-1 규칙 홀수 최대 팀 표) 선택."""
    if not org_records:
        return None
    for r in org_records:
        if r.get("name") == "조직도 · 모양 2":
            return r
    candidates = []
    for r in org_records:
        cols = r.get("cols", 0)
        if (cols + 1) % 3 == 0:
            n = (cols + 1) // 3
            if n % 2 == 1:
                candidates.append((n, r))
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    return org_records[0]


def describe_units(catalog_path=None) -> list[dict]:
    result = []
    records = catalog._scan(catalog_path or catalog.default_catalog_path())
    org_records = [r for r in records if r.get("category") == "조직도"]
    chosen_org = _select_org_chart_record(org_records) if len(org_records) > 1 or (org_records and org_records[0].get("name") in ("조직도 · 모양 2", "조직도")) else None

    for record in records:
        if record.get("category") == "조직도":
            if chosen_org is not None:
                if record["id"] != chosen_org["id"]:
                    continue
            elif len(org_records) > 1 and record.get("name") not in ("조직도 · 모양 2", "조직도"):
                continue
        item = {k: record[k] for k in ("id", "category", "name", "rows", "cols")}
        if record.get("category") == "조직도" and (chosen_org is not None and record["id"] == chosen_org["id"]):
            item["name"] = "조직도"
        item["units"] = {axis: {k: p[k] for k in ("count", "min", "max", "core", "sep", "kind") if k in p} if p else None
                         for axis, p in plan_for(record).items()}
        result.append(item)



    return result
