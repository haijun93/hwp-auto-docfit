"""별표(*, **) 위첨자 규칙.

규칙: 문두기호 문장(□·ㅇ·- 등으로 시작하는 문장)에서 단어 바로 뒤에 붙여 쓴 ``*`` 또는 ``**``는
위첨자(한/글 단축키 Shift+Alt+P)로 한다. 줄 맨 앞에서 문두기호로 쓴 ``* ``·``** ``, 앞에 빈칸이 있는
별표, 세 개 이상 이어진 별표, 곱셈 같은 ``3*4``·``a*b``는 대상이 아니다.
"""

from __future__ import annotations

import re

from .style_hierarchy import leading_marker

# 별표 한 개 또는 두 개가 빈칸·별표가 아닌 글자 바로 뒤에 붙어 있고, 뒤에 별표나 영문·숫자가 이어지지 않을 때.
_MARK = re.compile(r"(?<=[^\s*])(\*{1,2})(?![*A-Za-z0-9])")


def applies_to(text: str) -> bool:
    """문두기호로 시작하는 문장인지(위첨자 규칙을 적용할 문장인지)."""
    marker, _ = leading_marker(text or "")
    return bool(marker)


def mark_spans(text: str) -> list[tuple[int, int]]:
    """문장에서 위첨자로 만들 별표의 (시작, 끝) 위치 목록. 문두기호 문장이 아니면 빈 목록."""
    if not applies_to(text):
        return []
    marker_end = len(text) - len(text.lstrip()) + len(leading_marker(text)[0])
    return [match.span() for match in _MARK.finditer(text) if match.start() >= marker_end]
