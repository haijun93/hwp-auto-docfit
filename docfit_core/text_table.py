"""Detect box-drawing "ASCII art" tables sitting in plain paragraph text.

AI 채팅 답변을 문서에 붙여넣을 때, 표가 마크다운 대신 유니코드 박스 그림
문자로 그려진 채로 들어오는 경우가 흔하다::

    ┌──────────┬──────────────────────────────────────┐
    │ 구  분   │ 내  용                               │
    ├──────────┼──────────────────────────────────────┤
    │ 추진 방향│ 기술 발전 차단 후 함대 도착 시 일괄 점령*│
    └──────────┴──────────────────────────────────────┘

이 모듈은 문단 텍스트 목록에서 이런 블록을 찾아 실제 표로 만들 수 있는
행·열 문자열 격자로 바꾼다. 한/글 COM 조작은 하지 않는다(순수 텍스트 처리).
"""

from __future__ import annotations

_BORDER_CHARS = frozenset("┌┬┐├┼┤└┴┘─")
_TOP_LEFT = "┌"
_BOTTOM_LEFT = "└"
_CELL_SEP = "│"


def classify_line(line: str) -> str:
    """한 줄(앞뒤 공백 제거 전)을 "border" / "content" / "other"로 분류한다."""
    stripped = line.strip()
    if not stripped:
        return "other"
    if all(ch in _BORDER_CHARS for ch in stripped):
        return "border"
    if stripped.startswith(_CELL_SEP) and stripped.endswith(_CELL_SEP) and stripped.count(_CELL_SEP) >= 2:
        return "content"
    return "other"


def _split_cells(content_line: str) -> list[str]:
    inner = content_line.strip()[1:-1]  # 양 끝 │ 제거
    return [cell.strip() for cell in inner.split(_CELL_SEP)]


def parse_box_table(lines: list[str]) -> list[list[str]] | None:
    """블록 전체가 유효한 박스 그림 표이면 셀 문자열 행렬을, 아니면 ``None``을 돌려준다.

    유효 조건:
        - 첫 줄은 왼쪽 위 모서리(┌)가 있는 테두리 줄
        - 마지막 줄은 왼쪽 아래 모서리(└)가 있는 테두리 줄
        - 그 사이는 테두리(구분선) 또는 │로 감싼 내용 줄만 있어야 함
        - 내용 줄이 하나 이상 있어야 함(테두리만 있는 빈 표는 무효)

    행마다 칸 수가 다르면(드물게 잘못 붙여넣은 경우) 빈 칸으로 채워 맞춘다.
    """
    if len(lines) < 3:
        return None
    kinds = [classify_line(line) for line in lines]
    if kinds[0] != "border" or _TOP_LEFT not in lines[0]:
        return None
    if kinds[-1] != "border" or _BOTTOM_LEFT not in lines[-1]:
        return None
    if any(kind == "other" for kind in kinds[1:-1]):
        return None
    content_rows = [
        _split_cells(line) for line, kind in zip(lines[1:-1], kinds[1:-1]) if kind == "content"
    ]
    if not content_rows:
        return None
    width = max(len(row) for row in content_rows)
    return [row + [""] * (width - len(row)) for row in content_rows]


def _find_block_end(lines: list[str], kinds: list[str], start: int) -> int | None:
    """``start``(┌ 테두리 줄)에서 시작하는 블록의 마지막 줄(└ 테두리) 인덱스를 찾는다.

    도중에 테두리·내용 줄이 아닌 줄이 나오면 블록이 닫히지 않은 것이므로 ``None``.
    """
    end = start + 1
    while end < len(lines) and kinds[end] in ("border", "content"):
        if kinds[end] == "border" and _BOTTOM_LEFT in lines[end]:
            return end
        end += 1
    return None


def find_box_tables(lines: list[str]) -> list[tuple[int, int, list[list[str]]]]:
    """``lines`` 안의 모든 박스 그림 표 블록을 찾는다.

    각 항목은 ``(시작_인덱스, 끝_인덱스, 행렬)``이며 끝_인덱스는 포함(inclusive)이다.
    표들은 서로 겹치지 않으며 문서에 나온 순서대로 반환한다.
    """
    kinds = [classify_line(line) for line in lines]
    matches: list[tuple[int, int, list[list[str]]]] = []
    index = 0
    while index < len(lines):
        if kinds[index] == "border" and _TOP_LEFT in lines[index]:
            end = _find_block_end(lines, kinds, index)
            if end is not None:
                rows = parse_box_table(lines[index:end + 1])
                if rows is not None:
                    matches.append((index, end, rows))
                index = end
        index += 1
    return matches
