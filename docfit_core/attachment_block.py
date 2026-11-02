"""붙임 묶음: '붙임 …'으로 시작해 '끝.'으로 마무리되는 문장 범위.

규칙: 첫 어절이 ``붙임``으로 시작하는 줄(뒤에 ``:``이 올 수 있다)부터, 마침표(``.``)로 끝나는 한 줄 문장이
이어지다 ``끝.``으로 끝나는 줄까지가 하나의 묶음이다. 붙임 줄 자체가 ``끝.``으로 끝나면 그 한 줄이 묶음이다.
묶음 안의 모든 문장은 글꼴 종류와 글꼴 크기를 항목기호 ``ㅇ`` 문장과 같게 한다. 번호 붙임 목록의
항목 위치와 들여쓰기는 「2025 행정업무운영 편람」 예시를 따른다.
"""

from __future__ import annotations

import re

_START = re.compile(r"^\s*붙임")
_ITEM = re.compile(r"^(?P<indent>[ \t\u00a0\u3000]*)(?P<number>\d+)\.(?=\s|$|「)")
_HEADER = re.compile(r"^(?P<indent>[ \t\u00a0\u3000]*)붙임(?P<gap>[ \t\u00a0\u3000]*)(?P<colon>[:：]?)(?P<after>[ \t\u00a0\u3000]*)(?P<item>\d+\.(?=\s|$|「).*)$")
MAX_LINES = 30  # 묶음이 이보다 길면 붙임 목록이 아니라고 본다.


def is_start(text: str | None) -> bool:
    return bool(text) and bool(_START.match(text))


def is_end(text: str | None) -> bool:
    return bool(text) and text.rstrip().endswith("끝.")


def find_blocks(texts: list) -> list[tuple[int, int]]:
    """문단 글 목록에서 붙임 묶음의 (시작, 끝) 위치(끝 포함)를 찾는다.

    texts의 각 항목은 문단 글이며, 일반 글이 아닌 문단(표·그림 등)은 None으로 준다. 묶음 안의 문장은
    모두 빈 글이 아니고 마침표로 끝나거나 번호 항목이어야 하며, 그렇지 않으면 그 붙임 줄은 묶음이 아니다.
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
            # 번호 항목은 줄 끝 마침표가 없어도('… 1부') 묶음이다(불변 규칙은 마침표 유무로 꺼지지 않는다).
            if not text or not text.strip() or not (text.rstrip().endswith(".") or is_numbered_item(text)):
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


def blank_line_plan(texts: list, kinds: list) -> tuple[list[int], list[int]]:
    """붙임 묶음 앞 빈 줄을 1줄로 맞출 계획: (지울 빈 문단 인덱스, 앞에 빈 줄을 넣을 붙임 문단 인덱스).

    붙임 위에 글이 있으면 그 글과 붙임 사이에 빈 줄을 꼭 1줄 둔다(없으면 넣고, 여럿이면 1줄만 남긴다,
    사용자 지정 2026-10-08). kinds의 'blank'가 빈 문단이며, 붙임 위에 글이 없으면 손대지 않는다.
    """
    delete: list[int] = []
    insert: list[int] = []
    for start, _ in find_blocks(texts):
        k = start - 1
        blanks = []
        while k >= 0 and kinds[k] == "blank":
            blanks.append(k)
            k -= 1
        if k < 0:
            continue
        if not blanks:
            insert.append(start)
        else:
            delete.extend(blanks[1:])
    return delete, insert


def find_trailing_numbered_blocks(texts: list) -> list[tuple[int, int]]:
    """문서 끝 번호 붙임 묶음의 (첫 항목, 마지막 항목)을 찾는다.

    불변 규칙(사용자 2026-11-01): 붙임 뒤 숫자 1의 위치에 2. 이후 번호를 맞추고, 각 항목은
    번호+빈칸 뒤 본문 첫 글자 기준으로 내어쓴다. 항목 중간의 마침표 유무로 규칙이 꺼지지 않는다.
    """
    last = max((i for i, text in enumerate(texts) if text and text.strip()), default=-1)
    if last < 0 or not is_end(texts[last]):
        return []
    item_end = last - 1 if texts[last].strip() == "끝." else last
    i = item_end
    while i >= 0 and i >= last - MAX_LINES and texts[i] and is_numbered_item(texts[i]):
        if is_numbered_header(texts[i]):
            return [(i, item_end)] if item_end > i else []
        i -= 1
    return []
