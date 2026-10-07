"""문두기호별 내어쓰기 빈칸 규칙.

여러 줄 문장의 둘째 줄 이후는 '기호 끝 + 빈칸 N칸' 위치에 맞춘다(사용자 지정, 2026-10-07).
ㅇ은 빈칸 1칸, -는 빈칸 3칸, *·**·※(당구장 표시)는 빈칸 5칸이다.
"""

from __future__ import annotations

from .style_hierarchy import leading_marker

HANGING_BLANKS = {"ㅇ": 1, "-": 3, "*": 5, "**": 5, "※": 5}
_ALIASES = {"○": "ㅇ", "☞": "ㅇ"}


def hanging_blank_count(text: str | None) -> int | None:
    """문단 첫 문두기호의 내어쓰기 빈칸 수. 규칙이 없는 기호면 None."""
    marker, _ = leading_marker(text or "")
    return HANGING_BLANKS.get(_ALIASES.get(marker, marker))
