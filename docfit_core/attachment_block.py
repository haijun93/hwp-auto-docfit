"""붙임 묶음: '붙임 …'으로 시작해 '끝.'으로 마무리되는 문장 범위.

규칙: 첫 어절이 ``붙임``으로 시작하는 줄(뒤에 ``:``이 올 수 있다)부터, 마침표(``.``)로 끝나는 한 줄 문장이
이어지다 ``끝.``으로 끝나는 줄까지가 하나의 묶음이다. 붙임 줄 자체가 ``끝.``으로 끝나면 그 한 줄이 묶음이다.
묶음 안의 모든 문장은 글꼴 종류와 글꼴 크기를 문두기호 ``ㅇ`` 문장과 같게 한다. 번호 붙임 목록의
항목 위치와 들여쓰기는 「2025 행정업무운영 편람」 예시를 따른다.
"""

from __future__ import annotations

import re

_START = re.compile(r"^\s*붙임")
_ITEM = re.compile(r"^(?P<indent>[ \t\u00a0\u3000]*)(?P<number>\d+)\.(?=\s|$)")
_HEADER = re.compile(r"^(?P<indent>[ \t\u00a0\u3000]*)붙임(?P<gap>[ \t\u00a0\u3000]*)(?P<colon>[:：]?)(?P<after>[ \t\u00a0\u3000]*)(?P<item>\d+\.(?=\s|$).*)$")
MAX_LINES = 30  # 묶음이 이보다 길면 붙임 목록이 아니라고 본다.


def is_start(text: str | None) -> bool:
    return bool(text) and bool(_START.match(text))


def is_end(text: str | None) -> bool:
    return bool(text) and text.rstrip().endswith("끝.")


def find_blocks(texts: list) -> list[tuple[int, int]]:
    """문단 글 목록에서 붙임 묶음의 (시작, 끝) 위치(끝 포함)를 찾는다.

    texts의 각 항목은 문단 글이며, 일반 글이 아닌 문단(표·그림 등)은 None으로 준다. 묶음 안의 문장은
    모두 빈 글이 아니고 마침표로 끝나야 하며, 그렇지 않으면 그 붙임 줄은 묶음이 아니다.
    """
    blocks: list[tuple[int, int]] = []
    i = 0
    while i < len(texts):
        if not is_start(texts[i]):
            i += 1
            continue
        end = None
        for j in range(i, min(len(texts), i + MAX_LINES)):
            text = texts[j]
            if not text or not text.strip() or not text.rstrip().endswith("."):
                break
            if is_end(text):
                end = j
                break
        if end is None:
            i += 1
        else:
            blocks.append((i, end))
            i = end + 1
    return blocks


def is_numbered_item(text: str | None) -> bool:
    """번호와 마침표가 문두 어절인 붙임 항목인지 판정한다."""
    return bool(text) and bool(_ITEM.match(text) or _HEADER.match(text))


def is_numbered_header(text: str | None) -> bool:
    """붙임 표시와 첫 번호가 같은 문단에 적힌 첫 항목인지 판정한다."""
    return bool(text) and bool(_HEADER.match(text))


def numbered_item_offset(text: str | None) -> int | None:
    """문단 문자열에서 번호 마커(예: '2.')가 시작하는 글자 오프셋을 반환한다."""
    if not text:
        return None
    match = _HEADER.match(text)
    if match:
        return match.start("item")
    match = _ITEM.match(text)
    return match.start("number") if match else None


def find_trailing_numbered_blocks(texts: list) -> list[tuple[int, int]]:
    """문서 끝에 놓인, 번호 붙임 항목이 둘 이상인 붙임~끝. 묶음을 찾는다."""
    last = max((i for i, text in enumerate(texts) if text and text.strip()), default=-1)
    if last < 0:
        return []
    result = []
    for start, end in find_blocks(texts):
        if end != last or not is_numbered_header(texts[start]):
            continue
        item_end = end if is_numbered_item(texts[end]) else end - 1
        if item_end <= start or not all(is_numbered_item(texts[i]) for i in range(start, item_end + 1)):
            continue
        if item_end - start < 1:
            continue
        if item_end < end and (texts[item_end + 1] or "").strip() != "끝.":
            continue
        result.append((start, item_end))
    return result
