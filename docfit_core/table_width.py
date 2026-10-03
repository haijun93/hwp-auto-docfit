"""표 칸 너비: 가로로 칸이 둘 이상인 표의 열 너비를 칸 글자 수에 비례해 나눈다.

글자 수는 칸 안 문단에서 앞뒤 빈칸을 뺀 글자 수(글자 사이 빈칸 포함)다. 칸에 문단이 여럿이면 가장 긴
문단으로 센다. 예: A1 '도  시'(4자), B1 '마 을 여  행'(8자)이면 두 열 너비는 1:2다.

행이 둘 이상이면 1행(머리글)은 빼고, 2행부터 마지막 행까지 행마다 열별 글자 수 비율을 구한 뒤 그 평균
비율을 모든 행에 똑같이 적용한다(행마다 따로 맞추지 않는다). 병합 칸은 글자 수를 걸친 열에 똑같이 나눠
세고, 세로 병합 칸은 걸친 행마다 센다. 표 전체 폭은 쪽 좌우 여백 사이 최대 폭(본문 폭 − 표 바깥 여백)이다.

비율만 따르면 짧은 낱말 칸이 너무 좁아져 낱말이 갈라질 수 있으므로, 열마다 가장 긴 낱말(빈칸 없는 글자
묶음)이 한 줄에 들어갈 최소 폭을 지킨다. 그림·표·도형이 든 표, 너비가 절대값이 아닌 표, 글이 없는 표는
바꾸지 않는다.
"""

from __future__ import annotations

import re

from .format_elements import HeaderIndex, cell_paragraphs, run_text

_OBJECTS = {"tbl", "pic", "ole", "equation", "rect", "ellipse", "line", "arc", "polygon", "curve",
            "connectLine", "container", "textart", "chart", "video"}
_SPACES = " \t 　"


def _tag(element):
    return element.tag.rsplit("}", 1)[-1]


def _child(element, name):
    return next((x for x in element if _tag(x) == name), None)


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _cells(table):
    """(tc, 열, 행, 열 병합 수) 목록. 칸 주소·크기 정보가 없으면 None."""
    result = []
    for tr in (x for x in table if _tag(x) == "tr"):
        for tc in (x for x in tr if _tag(x) == "tc"):
            addr, span, size = _child(tc, "cellAddr"), _child(tc, "cellSpan"), _child(tc, "cellSz")
            if addr is None or size is None:
                return None
            col_span = _int(span.get("colSpan"), 1) if span is not None else 1
            result.append((tc, _int(addr.get("colAddr")), _int(addr.get("rowAddr")), max(1, col_span)))
    return result


def paragraph_texts(tc):
    """칸 문단 글 목록(고정폭·묶음 빈칸·탭도 한 글자로 센다)."""
    texts = []
    for p in cell_paragraphs(tc):
        text = "".join(run_text(run) for run in p if _tag(run) == "run").replace("\n", " ")
        texts.append(text.strip(_SPACES))
    return texts


def cell_length(tc):
    """칸 글자 수: 가장 긴 문단의 글자 수(앞뒤 빈칸 제외, 글자 사이 빈칸 포함)."""
    return max((len(text) for text in paragraph_texts(tc)), default=0)


def _half_width(ch):
    """한/글에서 글자 폭이 대략 반인 글자: 라틴 문자·숫자·문장부호, 일반 구두점(’ “ …), 반각 형태."""
    code = ord(ch)
    return code < 0x0370 or 0x2000 <= code <= 0x206F or 0xFF61 <= code <= 0xFFDC


def longest_word(tc):
    """가장 긴 낱말(빈칸 없는 글자 묶음)의 폭을 한글 글자 수 단위로 잰다(숫자·영문 등 반각 글자는 0.5)."""
    return max((sum(0.5 if _half_width(ch) else 1.0 for ch in word)
                for text in paragraph_texts(tc) for word in re.split(f"[{_SPACES}]+", text) if word), default=0)


def is_target(table):
    """비례 너비를 적용할 표인지: 가로로 칸 둘 이상, 개체 없음, 절대 너비, 칸 정보 완전, 글 있음."""
    cols = _int(table.get("colCnt"))
    size = _child(table, "sz")
    if cols < 2 or size is None or (size.get("widthRelTo") or "ABSOLUTE") != "ABSOLUTE":
        return False
    cells = _cells(table)
    if not cells:
        return False
    for tc, _, _, _ in cells:
        if any(_tag(x) in _OBJECTS for x in tc.iter() if x is not tc):
            return False
    return any(cell_length(tc) for tc, _, _, _ in cells)


def plan_widths(weights, floors, total):
    """열 너비(합 = total). weights 비율로 나누되 floors 아래로 내리지 않는다."""
    count = len(weights)
    if sum(floors) >= total:
        base = sum(floors) or count
        widths = [total * (f or 1) / base for f in floors]
    else:
        fixed, widths = set(), [0.0] * count
        while True:
            rest = total - sum(floors[i] for i in fixed)
            free = [i for i in range(count) if i not in fixed]
            share = sum(weights[i] for i in free)
            for i in range(count):
                if i in fixed:
                    widths[i] = floors[i]
                else:
                    # 남은 열이 모두 글자 없는 열이면 똑같이 나눈다.
                    widths[i] = rest * weights[i] / share if share else rest / len(free)
            low = {i for i in free if widths[i] < floors[i]}
            if not low:
                break
            fixed |= low
    result = [int(round(w)) for w in widths]
    result[result.index(max(result))] += total - sum(result)
    return result


def cap_floors(floors, total):
    """최소 폭 합이 표 폭의 95%를 넘으면 큰 값부터 같은 높이로 깎는다(짧은 낱말 열을 먼저 지킨다)."""
    limit = total * 0.95
    if sum(floors) <= limit:
        return list(floors)
    ordered, rest = sorted(floors), limit
    for n, value in enumerate(ordered):
        level = rest / (len(ordered) - n)
        if value > level:
            return [min(f, int(level)) for f in floors]
        rest -= value
    return list(floors)


def _grid(cells, rows):
    """행마다 열을 덮는 칸: grid[행][열] = (tc, 열 병합 수). 위 행에서 내려온 세로 병합 칸도 넣는다."""
    grid = {}
    for tc, col, row, span in cells:
        size = _child(tc, "cellSpan")
        row_span = max(1, _int(size.get("rowSpan"), 1)) if size is not None else 1
        for r in range(row, min(rows, row + row_span)):
            for c in range(col, col + span):
                grid.setdefault(r, {})[c] = (tc, span)
    return grid


def column_ratios(table):
    """열 너비 비율. 1행(머리글)을 빼고 2행부터 마지막 행까지 행마다 칸 글자 수 비율을 구해 평균한다.

    여러 열에 걸친 칸은 글자 수를 걸친 열에 똑같이 나눈다. 빈 칸이 있는 행(비고 칸이 빈 행, 일정표의 막대
    칸 등)은 그 열을 0으로 만들어 비율을 흐리므로, 모든 칸에 글이 있는 행이 있으면 그 행들로만 정한다.
    그런 행이 없으면 글이 있는 행 모두로, 그것도 없으면(행이 하나뿐이거나 2행 이후가 모두 빔) 1행으로
    정한다. 정할 수 없으면 None.
    """
    cells = _cells(table)
    if not cells:
        return None
    cols = _int(table.get("colCnt"))
    rows = max(_int(table.get("rowCnt")), max(row for _, _, row, _ in cells) + 1)
    grid = _grid(cells, rows)
    lengths = {id(tc): cell_length(tc) for tc, _, _, _ in cells}

    def ratios(row_numbers, full):
        found = []
        for r in row_numbers:
            values = []
            for c in range(cols):
                tc, span = grid.get(r, {}).get(c, (None, 1))
                values.append(lengths[id(tc)] / span if tc is not None else 0)
            total = sum(values)
            if total and (not full or all(values)):
                found.append([v / total for v in values])
        return found

    found = (ratios(range(1, rows), True) or ratios(range(1, rows), False)
             or ratios([0], True) or ratios([0], False))
    if not found:
        return None
    return [sum(row[c] for row in found) / len(found) for c in range(cols)]


def fit_table(table, body_width, index: HeaderIndex) -> bool:
    """표 폭을 본문 폭에 맞추고 열 너비를 칸 글자 수 비율(2행부터 행별 비율의 평균)로 나눈다. 바꿨으면 True."""
    if not body_width or not is_target(table):
        return False
    cells = _cells(table)
    cols = _int(table.get("colCnt"))
    out = _child(table, "outMargin")
    total = int(body_width) - ((_int(out.get("left")) + _int(out.get("right"))) if out is not None else 0)
    if total <= cols * 300:
        return False
    weights = column_ratios(table)
    if weights is None:
        return False
    # 최소 폭: 열 하나만 차지하는 칸(머리글 포함)의 가장 긴 낱말이 한 줄에 들어갈 폭. 한/글 글자 폭은
    # 글자 크기 × 장평에 자간·굵게 여유를 더해 넉넉히 잡는다.
    in_margin = _child(table, "inMargin")
    floors = [600] * cols
    for tc, col, _, span in cells:
        if span != 1 or not 0 <= col < cols:
            continue
        margin = _child(tc, "cellMargin") if tc.get("hasMargin") == "1" else in_margin
        side = (_int(margin.get("left")) + _int(margin.get("right"))) if margin is not None else 0
        char = 0
        for p in cell_paragraphs(tc):
            for run in (x for x in p if _tag(x) == "run"):
                values = index.char(run.get("charPrIDRef")) if run_text(run).strip() else None
                if values:
                    width = values["size"] * values["ratio"] / 100 * (100 + max(0, values["spacing"])) / 100
                    char = max(char, width * (1.08 if values["bold"] else 1.0))
        floors[col] = max(floors[col], int(longest_word(tc) * (char or 1000) * 1.1) + side + 200)
    # 최소 폭이 표 폭을 넘치면 긴 글자 묶음(날짜 범위·주소 등) 열부터 깎아 다른 열 몫을 빼앗지 않게 한다.
    floors = cap_floors(floors, total)
    widths = plan_widths(weights, floors, total)
    for tc, col, _, span in cells:
        _child(tc, "cellSz").set("width", str(sum(widths[col:col + span])))
        for p in cell_paragraphs(tc):
            for cache in [x for x in p if _tag(x) == "linesegarray"]:
                p.remove(cache)        # 줄 배치 캐시는 한/글이 새 폭으로 다시 계산한다
    _child(table, "sz").set("width", str(total))
    return True
