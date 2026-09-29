"""붙임 묶음: '붙임 …'으로 시작해 '끝.'으로 마무리되는 문장 범위.

규칙: 첫 어절이 ``붙임``으로 시작하는 줄(뒤에 ``:``이 올 수 있다)부터, 마침표(``.``)로 끝나는 한 줄 문장이
이어지다 ``끝.``으로 끝나는 줄까지가 하나의 묶음이다. 붙임 줄 자체가 ``끝.``으로 끝나면 그 한 줄이 묶음이다.
묶음 안의 모든 문장은 글꼴 종류와 글꼴 크기를 문두기호 ``ㅇ`` 문장과 같게 한다.
"""

from __future__ import annotations

import re

_START = re.compile(r"^\s*붙임")
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
