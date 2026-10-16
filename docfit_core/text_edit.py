"""문단 글을 XML에서 고친다(알파 1-c, 2026-10-11). 글 규칙(공백·따옴표·날짜 표기 등)이 만든 새 글을 run에 반영한다.

- 문단 글은 run 안 hp:t 글과 그 안 자식 요소 뒤 글(조각)을 이어 붙인 것이다. 자식 요소(고정폭 빈칸 등)는 글자로 세지 않고
  그대로 둔다(한/글 GetText와 같은 기준). 그래서 Beta 16 때처럼 숨은 글자 때문에 위치가 밀리는 일이 없다.
- 원래 글과 새 글의 차이(difflib)만 조각에 반영한다. 바뀐 글자는 원래 글자가 있던 조각에, 새로 넣는 글자는 바로 앞 글자의
  조각에 넣어 한/글 입력처럼 앞 글자의 글자 모양을 따른다.
"""

from __future__ import annotations

import difflib

from .spacing_reset import _tag


def _segments(p):
    """[(요소, 'text'|'tail')] 문단 글 조각 목록(문서 순서)."""
    out = []
    for r in p:
        if _tag(r) != "run":
            continue
        for t in r:
            if _tag(t) != "t":
                continue
            out.append((t, "text"))
            for c in t:
                out.append((c, "tail"))
    return out


def _get(seg):
    el, kind = seg
    return (el.text if kind == "text" else el.tail) or ""


def _set(seg, value):
    el, kind = seg
    if kind == "text":
        el.text = value
    else:
        el.tail = value


def paragraph_text(p) -> str:
    return "".join(_get(s) for s in _segments(p))


_SPACE_ELEMENTS = ("fwSpace", "nbSpace")


def drop_spaces_at(p, position: int, end: int | None = None) -> int:
    """글 위치 position~end(고정폭 빈칸을 세지 않는 위치, end가 없으면 position)에 있는 고정폭·묶음 빈칸 요소를 지운다. 지운 수.

    항목기호 뒤 빈칸 규칙용(2026-10-17): 'ㅇ[고정폭][고정폭]본문'은 GetText·paragraph_text에서 'ㅇ본문'으로 보여
    일반 빈칸을 하나 더 넣어 빈칸이 3칸이 됐다. 기호 바로 뒤의 고정폭 빈칸을 지우면 규칙이 일반 빈칸 1칸으로 맞춘다.
    """
    removed, count = 0, 0
    for r in p:
        if _tag(r) != "run":
            continue
        for t in r:
            if _tag(t) != "t":
                continue
            count += len(t.text or "")
            for c in list(t):
                if position <= count <= (position if end is None else end) and _tag(c) in _SPACE_ELEMENTS:
                    tail = c.tail or ""
                    index = list(t).index(c)
                    if index:
                        prev = t[index - 1]
                        prev.tail = (prev.tail or "") + tail
                    else:
                        t.text = (t.text or "") + tail
                    t.remove(c)
                    removed += 1
                    count += len(tail)
                    continue
                count += len(c.tail or "")
    if removed:
        for cache in [x for x in p if _tag(x) == "linesegarray"]:
            p.remove(cache)
    return removed


def apply_text(p, new_text: str) -> bool:
    """문단 p의 글을 new_text로 바꾼다(차이만 반영). 바꿨으면 True. 글 조각이 없으면 False."""
    segs = _segments(p)
    if not segs:
        return False
    owner = []                       # 원래 글 글자마다 조각 번호
    for i, s in enumerate(segs):
        owner += [i] * len(_get(s))
    old = "".join(_get(s) for s in segs)
    if old == new_text:
        return False
    pieces = [[] for _ in segs]
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new_text, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                pieces[owner[i1 + k]].append(old[i1 + k])
        elif op == "delete":
            continue
        else:                        # replace·insert: 원래 글자 자리(없으면 앞 글자 자리)에 넣는다
            at = owner[i1] if i1 < len(old) else (owner[i1 - 1] if i1 else 0)
            if op == "insert" and i1 > 0:
                at = owner[i1 - 1]
            pieces[at].append(new_text[j1:j2])
    for s, chars in zip(segs, pieces):
        _set(s, "".join(chars))
    if paragraph_text(p) != new_text:
        raise RuntimeError("문단 글 반영 검사 실패")
    for cache in [x for x in p if _tag(x) == "linesegarray"]:
        p.remove(cache)
    return True
