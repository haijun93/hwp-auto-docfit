"""문두기호별 내어쓰기 빈칸 규칙.

- ㅇ·-: 둘째 줄 이후를 '기호 끝 + 빈칸 N칸' 위치에 맞춘다(ㅇ 1칸, - 3칸, 사용자 지정 2026-10-07).
- 부연설명(*·**·※): 바로 앞 ㅁ·ㅇ·- 문장의 내어쓰기 값에 빈칸 2칸을 더한다(사용자 지정 2026-10-07).
  ㅁ 뒤의 부연설명과 ㅇ·- 뒤의 부연설명은 앞 기호의 내어쓰기 값이 달라 값도 따로 정해진다.
"""

from __future__ import annotations

from .style_hierarchy import leading_marker

HANGING_BLANKS = {"ㅇ": 1, "-": 3}
SUPPLEMENT_EXTRA_BLANKS = 2
SUPPLEMENT_MARKERS = frozenset({"*", "**", "※"})
PARENT_MARKERS = frozenset({"□", "ㅇ", "-"})
_ALIASES = {"○": "ㅇ", "☞": "ㅇ"}


def _marker(text: str | None) -> str:
    marker, _ = leading_marker(text or "")
    return _ALIASES.get(marker, marker)


def hanging_blank_count(text: str | None) -> int | None:
    """ㅇ·- 문단의 내어쓰기 빈칸 수. 규칙이 없는 기호면 None."""
    return HANGING_BLANKS.get(_marker(text))


def is_supplement(text: str | None) -> bool:
    """부연설명(*·**·※) 문단인가."""
    return _marker(text) in SUPPLEMENT_MARKERS


def is_parent_marker(text: str | None) -> bool:
    """부연설명의 내어쓰기 기준이 되는 ㅁ·ㅇ·- 문단인가."""
    return _marker(text) in PARENT_MARKERS
