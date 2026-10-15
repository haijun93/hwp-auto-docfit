"""표 칸 너비: 가로로 칸이 둘 이상인 표의 열 너비를 칸 글자 수에 비례해 나눈다.

글자 수는 칸 안 문단에서 앞뒤 빈칸을 뺀 글자 수(글자 사이 빈칸 포함)다. 칸에 문단이 여럿이면 가장 긴
문단으로 센다. 예: A1 '도  시'(4자), B1 '마 을 여  행'(8자)이면 두 열 너비는 1:2다.

행이 둘 이상이면 첫 행의 rowSpan으로 판별한 머리글 전체를 빼고, 본문 첫 행부터 마지막 행까지 행마다 열별 글자 수 비율을 구한 뒤 그 평균
비율을 모든 행에 똑같이 적용한다(행마다 따로 맞추지 않는다). 병합 칸은 글자 수를 걸친 열에 똑같이 나눠
세고, 세로 병합 칸은 걸친 행마다 센다. 표 전체 폭은 쪽 좌우 여백 사이 최대 폭(본문 폭 − 표 바깥 여백)이다.

비율만 따르면 짧은 낱말 칸이 너무 좁아져 낱말이 갈라질 수 있으므로, 열마다 가장 긴 낱말(빈칸 없는 글자
묶음)이 한 줄에 들어갈 최소 폭을 지킨다. 그림·표·도형이 든 표, 너비가 절대값이 아닌 표, 글이 없는 표는
바꾸지 않는다.
"""

from __future__ import annotations

import re

from .format_elements import HeaderIndex, cell_paragraphs, run_text
from .table_style import has_unit_caption, header_row_count, is_design_table

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
    if cols < 2 or size is None or (size.get("widthRelTo") or "ABSOLUTE") != "ABSOLUTE" or is_design_table(table):
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


def _grouped_header(cells):
    """첫 행에 아래 행의 여러 열을 묶는 머리글 칸(열 병합 2 이상, 행 병합 1)이 있으면 다단 머리글이다.

    첫 행 칸이 두 행에 걸쳐 있기만 한 표(예: '설치근거 | 근거 법규 목록 | 유형 | 상설/비상설' 아래에
    '법령상 강행/임의'가 오는 양식 표)는 다단 머리글이 아니다. 이런 표의 둘째 행까지 머리글로 빼면
    글이 많은 칸이 너비 계산에서 빠져 그 열이 좁아지고 글자가 겹친다.
    """
    for tc, _col, row, span in cells:
        if row == 0 and span > 1:
            size = _child(tc, "cellSpan")
            if (max(1, _int(size.get("rowSpan"), 1)) if size is not None else 1) == 1:
                return True
    return False


def column_ratios(table):
    """열 너비 비율. 공통 header_row_count로 머리글 전체를 빼고 본문 첫 행부터 마지막 행까지 행마다 칸 글자 수 비율을 구해 평균한다.

    여러 열에 걸친 칸은 글자 수를 걸친 열에 똑같이 나눈다. 빈 칸이 있는 행(비고 칸이 빈 행, 일정표의 막대
    칸 등)은 그 열을 0으로 만들어 비율을 흐리므로, 모든 칸에 글이 있는 행이 있으면 그 행들로만 정한다.
    다단 머리글 표의 본문이 빈 막대 칸이면 기존처럼 하위 머리글을 보조 기준으로 쓴다.
    그 밖에는 글이 있는 본문 행 모두로, 그것도 없으면 1행으로
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

    head = header_row_count(table) if _grouped_header(cells) else 1
    found = (ratios(range(head, rows), True)
             # Empty Gantt bars carry no usable body proportions; retain the
             # existing lower-header fallback instead of collapsing time columns.
             or (ratios(range(1, head), True) if head > 1 else [])
             or ratios(range(head, rows), False)
             or ratios([0], True) or ratios([0], False))
    if not found:
        return None
    return [sum(row[c] for row in found) / len(found) for c in range(cols)]


_RESERVE_MIN_SIZE = 1600


def _plan_with_empty_columns(cells, cols, weights, floors, total):
    """모든 칸이 빈 열(점선 칸·장식 칸·빈 비고 열)은 원래 너비 비율을 지키고, 나머지 폭만 글자 수 비율로 나눈다.

    빈 열은 글자 수가 0이라 최소 폭으로 줄어, '2026 추진실적 ……(8. 31. 현재)' 같은 장식 표의 점선 칸이
    사라지고 글 칸이 넓어져 모양이 깨졌다(test6 문화경제국 문서).
    """
    original = [0] * cols
    empty = [True] * cols
    for tc, col, _, span in cells:
        if span == 1 and 0 <= col < cols:
            original[col] = max(original[col], _int(_child(tc, "cellSz").get("width")))
        if "".join(paragraph_texts(tc)).strip():
            for c in range(max(0, col), min(cols, col + span)):
                empty[c] = False
    keep = [c for c in range(cols) if empty[c] and original[c] > 0]
    if not keep or len(keep) == cols or not sum(original):
        return plan_widths(weights, cap_floors(floors, total), total)
    kept = {c: int(original[c] * total / sum(original)) for c in keep}
    rest = total - sum(kept.values())
    others = [c for c in range(cols) if c not in kept]
    share = [weights[c] for c in others]
    share = [x / sum(share) for x in share] if sum(share) else [1 / len(others)] * len(others)
    widths = [0] * cols
    for c, width in zip(others, plan_widths(share, cap_floors([floors[c] for c in others], rest), rest)):
        widths[c] = width
    for c, width in kept.items():
        widths[c] = width
    return widths


def host_reserve(paragraph, table, index: HeaderIndex) -> int:
    """글자처럼 놓인 표 앞에 같은 문단에서 차지하는 폭(HWPUNIT): 표 앞 글(빈칸 포함)과 문단의 양수 왼쪽·오른쪽 여백·첫 줄 들여쓰기.

    예: '   '(빈칸 셋) 뒤에 놓인 표를 본문 폭 그대로 넓히면 빈칸 폭만큼 줄을 넘쳐 한/글이 표를 용지 밖으로 밀었다
    (test6 문화경제국 문서 '총 계 | 노래연습장 …' 표). 표가 글과 따로 놓이면(treatAsChar 아님) 0이다.
    """
    pos = _child(table, "pos")
    if paragraph is None or pos is None or pos.get("treatAsChar") != "1":
        return 0
    para = index.para(paragraph.get("paraPrIDRef")) or {}
    reserve = sum(max(0, int(para.get(key) or 0)) for key in ("left", "right", "indent"))
    for run in (x for x in paragraph if _tag(x) == "run"):
        values = index.char(run.get("charPrIDRef")) or {}
        # 표준서식이 나중에 본문 글자를 키우므로(최대 16pt) 표 앞 글 폭은 그 크기로 넉넉히 잡는다.
        size = max(values.get("size", 1000), _RESERVE_MIN_SIZE) * values.get("ratio", 100) / 100
        for child in run:
            if child is table:
                return reserve
            if _tag(child) == "t":
                text = (child.text or "") + "".join(c.tail or "" for c in child)
                # 한/글 빈칸 폭은 글꼴마다 달라 전각으로 넉넉히 잡는다(모자라면 표가 다음 줄로 밀려 용지 밖으로 나간다).
                reserve += int(sum(0.6 if _half_width(ch) and not ch.isspace() else 1.0 for ch in text) * size)
    return reserve


def _boundaries(cells, cols):
    """칸 너비로 열 경계 x 좌표(0 … 표 폭)를 푼다. 병합 칸만으로 정해지지 않거나 서로 어긋나면 None."""
    edges = {0: 0}
    spans = [(col, col + span, _int(_child(tc, "cellSz").get("width"))) for tc, col, _, span in cells]
    changed = True
    while changed:
        changed = False
        for left, right, width in spans:
            if left in edges and right not in edges:
                edges[right], changed = edges[left] + width, True
            elif right in edges and left not in edges:
                edges[left], changed = edges[right] - width, True
    if any(i not in edges for i in range(cols + 1)):
        return None
    if any(edges[right] - edges[left] != width for left, right, width in spans):
        return None
    return edges


def _scale_to_fit(table, cells, total):
    """캡션('(단위: 개소)')이 달린 표는 작성자가 꾸민 모양이라 열을 다시 나누지 않는다. 쪽 폭을 넘칠 때만
    모든 열을 같은 비율로 줄여 넣는다(캡션은 표 오른쪽 끝선에 맞춘 정렬 그대로 따라온다)."""
    size = _child(table, "sz")
    current = _int(size.get("width"))
    if not current or current <= total:
        return False
    ratio = total / current
    # 칸마다 따로 버리면 병합 칸과 나뉜 칸의 오른쪽 선이 1단위씩 어긋나고 행 합이 표 폭보다 작아진다.
    # 열 경계를 한 번만 반올림해 모든 칸이 같은 경계를 쓰게 한다.
    edges = _boundaries(cells, _int(table.get("colCnt")))
    if edges is not None:
        edges = {i: (total if x == current else int(round(x * ratio))) for i, x in edges.items()}
    for tc, col, _, span in cells:
        cell = _child(tc, "cellSz")
        if edges is not None:
            cell.set("width", str(edges[col + span] - edges[col]))
        else:
            cell.set("width", str(int(_int(cell.get("width")) * ratio)))
        for p in cell_paragraphs(tc):
            for cache in [x for x in p if _tag(x) == "linesegarray"]:
                p.remove(cache)
    size.set("width", str(total))
    caption = _child(table, "caption")
    if caption is not None and caption.get("lastWidth"):
        caption.set("lastWidth", str(total))
    return True


def fit_table(table, body_width, index: HeaderIndex, reserve: int = 0) -> bool:
    """표 폭을 본문 폭(표 앞 글·문단 여백 reserve를 뺀 폭)에 맞추고 열 너비를 칸 글자 수 비율로 나눈다. 바꿨으면 True."""
    if not body_width or not is_target(table):
        return False
    cells = _cells(table)
    cols = _int(table.get("colCnt"))
    out = _child(table, "outMargin")
    total = int(body_width) - ((_int(out.get("left")) + _int(out.get("right"))) if out is not None else 0) - max(0, reserve)
    if total <= cols * 300:
        return False
    if has_unit_caption(table):
        return _scale_to_fit(table, cells, total)
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
    widths = _plan_with_empty_columns(cells, cols, weights, floors, total)
    for tc, col, _, span in cells:
        _child(tc, "cellSz").set("width", str(sum(widths[col:col + span])))
        for p in cell_paragraphs(tc):
            for cache in [x for x in p if _tag(x) == "linesegarray"]:
                p.remove(cache)        # 줄 배치 캐시는 한/글이 새 폭으로 다시 계산한다
    _child(table, "sz").set("width", str(total))
    return True
