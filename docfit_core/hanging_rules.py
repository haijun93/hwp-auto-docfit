"""문두기호별 내어쓰기 빈칸 규칙.

- ㅇ·-: 둘째 줄 이후를 '기호 끝 + 빈칸 N칸' 위치에 맞춘다(ㅇ 1칸, - 3칸, 사용자 지정 2026-10-07).
- 부연설명(*·**·※): 둘째 줄을 자기 글 시작 위치(기호와 뒤 빈칸 바로 다음)에 맞춘다(사용자 지정 2026-10-07).
- 앞줄에 문두기호 문장이 없는 단독 ※는 ㅇ와 같은 규칙(1칸)을 쓴다.
"""

from __future__ import annotations

from .style_hierarchy import leading_marker

HANGING_BLANKS = {"ㅇ": 1, "-": 3}
SUPPLEMENT_MARKERS = frozenset({"*", "**", "※"})
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


def is_standalone_note(text: str | None, previous_text: str | None) -> bool:
    """앞 문두기호 문장의 보충설명이 아닌 단독 ※ 문단인가(ㅇ 규칙을 쓴다, 사용자 지정 2026-10-07).

    previous_text는 바로 앞의 ※가 아닌 문단이다(연속된 ※ 줄은 건너뛰고 넘긴다).
    """
    return _marker(text) == "※" and not _marker(previous_text)
