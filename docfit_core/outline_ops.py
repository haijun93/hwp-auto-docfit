"""아웃라이너(워크플로위류) 편집 규칙 — 줄 목록만 다루는 순수 함수(TODO.md 5순위).

저장 형식(기존과 호환되는 마크다운):
  - 0단계 항목 "# 본문", N단계(N≥1) 항목 ((N-1)*2칸 들여쓰기) + "- 본문"
  - 완료 표시: 항목 본문 앞 "[x] " (GFM 작업 목록과 같은 표기)
  - 메모: 항목 바로 아래 "> 메모"(인용 표기) — 항목 글자 시작 칸에 맞춰 들여씀
접기·확대·검색 걸러 보기는 화면에서만 줄을 숨기므로 저장 내용은 바뀌지 않는다.
"""
from __future__ import annotations

완료_표시 = "[x] "


def parse(line: str) -> tuple[str, int, str]:
    """(종류, 깊이, 본문). 종류는 'item' | 'note' | 'text'. 메모의 깊이는 -1(위 항목을 따름)."""
    stripped = line.lstrip(" ")
    indent = len(line) - len(stripped)
    if stripped.startswith("# ") or stripped == "#":
        return "item", 0, stripped[2:]
    if stripped.startswith("- ") or stripped == "-":
        return "item", indent // 2 + 1, stripped[2:]
    if stripped.startswith("> ") or stripped == ">":
        return "note", -1, stripped[2:]
    return "text", 0, stripped


def depth(lines: list[str], i: int) -> int:
    """i번째 줄의 계층 깊이. 메모는 바로 위 항목의 깊이를 따른다."""
    kind, d, _ = parse(lines[i])
    if kind != "note":
        return d
    for k in range(i - 1, -1, -1):
        kind_k, d_k, _ = parse(lines[k])
        if kind_k != "note":
            return d_k
    return 0


def item_start(lines: list[str], i: int) -> int:
    """i가 메모 줄이면 그 메모가 딸린 항목 줄 번호."""
    while i > 0 and parse(lines[i])[0] == "note":
        i -= 1
    return i


def subtree_end(lines: list[str], i: int) -> int:
    """i번째 항목과 그 메모·하위 항목이 끝나는 다음 줄 번호(배타)."""
    d = depth(lines, i)
    j = i + 1
    while j < len(lines):
        kind, dj, _ = parse(lines[j])
        if kind != "note" and dj <= d:
            break
        j += 1
    return j


def move_block(lines: list[str], i: int, up: bool) -> tuple[list[str], int] | None:
    """i번째 항목(하위 포함)을 같은 계층의 앞/뒤 형제와 자리를 바꾼다. 못 옮기면 None."""
    i = item_start(lines, i)
    d = depth(lines, i)
    end = subtree_end(lines, i)
    if up:
        k = i - 1
        while k >= 0 and (parse(lines[k])[0] == "note" or depth(lines, k) > d):
            k -= 1
        if k < 0 or depth(lines, k) != d:
            return None
        return lines[:k] + lines[i:end] + lines[k:i] + lines[end:], k
    if end >= len(lines) or depth(lines, end) != d or parse(lines[end])[0] != "item":
        return None
    next_end = subtree_end(lines, end)
    return lines[:i] + lines[end:next_end] + lines[i:end] + lines[next_end:], i + (next_end - end)


def toggle_done(line: str) -> str:
    """항목의 완료 표시를 켜고 끈다(항목이 아니면 그대로)."""
    kind, d, body = parse(line)
    if kind != "item":
        return line
    prefix = line[: len(line) - len(body)]
    if body.startswith(완료_표시):
        return prefix + body[len(완료_표시):]
    return prefix + 완료_표시 + body


def is_done(line: str) -> bool:
    kind, _, body = parse(line)
    return kind == "item" and body.startswith(완료_표시)


def note_prefix(item_line: str) -> str:
    """항목 줄 아래에 붙일 메모 줄의 접두(항목 글자 시작 칸 + '> ')."""
    kind, _, body = parse(item_line)
    width = len(item_line) - len(body) if kind == "item" else 0
    return " " * width + "> "


def ancestors(lines: list[str], i: int) -> list[int]:
    """i번째 줄의 상위 항목 줄 번호들(가까운 것부터)."""
    result = []
    d = depth(lines, item_start(lines, i))
    for k in range(item_start(lines, i) - 1, -1, -1):
        kind, dk, _ = parse(lines[k])
        if kind == "item" and dk < d:
            result.append(k)
            d = dk
            if d == 0:
                break
    return result


def filter_visible(lines: list[str], query: str) -> set[int]:
    """검색어가 들어간 줄과 그 상위 항목 줄 번호(워크플로위식 걸러 보기)."""
    query = (query or "").strip().lower()
    if not query:
        return set(range(len(lines)))
    visible = set()
    for i, line in enumerate(lines):
        if query in parse(line)[2].lower():
            visible.add(i)
            visible.update(ancestors(lines, i))
            if parse(line)[0] == "note":
                visible.add(item_start(lines, i))
    return visible


def export_markdown(lines: list[str]) -> str:
    """개조식 변환용 텍스트: 완료 표시는 떼고 메모는 '※ 메모' 부연설명 줄로."""
    out = []
    for line in lines:
        kind, _, body = parse(line)
        if kind == "note":
            if body.strip():
                out.append("※ " + body.strip())
            continue
        if kind == "item" and body.startswith(완료_표시):
            line = line[: len(line) - len(body)] + body[len(완료_표시):]
        out.append(line)
    return "\n".join(out)
