"""HWPX 표의 반복 정보단위 판정과 XML 전용 크기 조절 (COM 불필요)."""

from __future__ import annotations

import copy
from pathlib import Path

from defusedxml import ElementTree as ET

from . import table_catalog as catalog

HP = catalog._HP


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
    add("표(가로) · 모양 2", col=(0, 1, 4))
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
    plan = copy.deepcopy(PLANS[template["name"]]) if template.get("name") in PLANS else detect_plan(
        template["cell_meta"], template["rows"], template["cols"])
    for axis, length in (("row", template["rows"]), ("col", template["cols"])):
        if plan[axis] is not None:
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


def _resize_axis(table, axis, p, target, object_ids):
    cells = _meta(table)
    _validate(cells, int(table.get(axis + "Cnt")), axis, p)
    old_count, core, sep, start = (p[k] for k in ("count", "core", "sep", "start"))
    end = _end(p)
    stride = core + sep
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


def resize_table(tbl_element, plan, row_count=None, col_count=None, *, id_roots=()):
    """제자리 변경. plan의 count와 내부 복제 원본도 갱신하여 연속 조절을 지원한다.

    잘못된 요청은 원본 요소와 plan을 바꾸지 않는다.
    """
    working, updated = copy.deepcopy(tbl_element), copy.deepcopy(plan)
    object_ids = _ObjectIds((*id_roots, working))
    for axis, target in (("row", row_count), ("col", col_count)):
        if target is None:
            continue
        p = updated.get(axis)
        if p is None:
            raise ValueError("이 표에는 조절할 " + ("행" if axis == "row" else "열") + " 정보단위가 없습니다.")
        if type(target) is not int or not p["min"] <= target <= p["max"]:
            raise ValueError(f"정보단위 개수는 {p['min']}~{p['max']} 사이 정수로 지정해 주세요.")
        if target != p["count"]:
            _resize_axis(working, axis, p, target, object_ids)
        else:
            _validate(_meta(working), int(working.get(axis + "Cnt")), axis, p)
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


def export_resized(template_id, output_path, catalog_path=None, row_count=None, col_count=None) -> Path:
    record, _, _ = _load(template_id, catalog_path)
    plan = plan_for(record)
    # Other sections and header definitions may survive the catalog export.
    source = Path(catalog_path or catalog.default_catalog_path())
    with catalog._safe_archive(source) as archive:
        roots = [ET.fromstring(archive.read(name)) for name in archive.namelist()
                 if name.lower().endswith(".xml")]
    return catalog.export_template(template_id, output_path, catalog_path,
        table_transform=lambda table: resize_table(table, plan, row_count, col_count, id_roots=roots))


def preview(template_id, catalog_path=None, row_count=None, col_count=None) -> dict:
    record, table, header = _load(template_id, catalog_path)
    resize_table(table, plan_for(record), row_count, col_count)
    result = {k: record[k] for k in ("id", "name")}
    # Unlike the catalog's compact preview, return every resized cell.
    result.update(rows=int(table.get("rowCnt")), cols=int(table.get("colCnt")), cells=[], cell_meta=[])
    for i, row in enumerate(table.findall(HP + "tr")):
        texts, meta = [], []
        for j, cell in enumerate(row.findall(HP + "tc")):
            text = " ".join("".join(n.text or "" for n in catalog._cell_text_nodes(cell)).split())[:80]
            texts.append(text)
            meta.append(catalog._cell_meta(cell, i, j, text, header))
        result["cells"].append(texts)
        result["cell_meta"].append(meta)
    return result


def describe_units(catalog_path=None) -> list[dict]:
    result = []
    for record in catalog._scan(catalog_path or catalog.default_catalog_path()):
        item = {k: record[k] for k in ("id", "category", "name", "rows", "cols")}
        item["units"] = {axis: {k: p[k] for k in ("count", "min", "max", "core", "sep")} if p else None
                         for axis, p in plan_for(record).items()}
        result.append(item)
    return result
