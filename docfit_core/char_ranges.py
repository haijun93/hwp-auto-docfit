"""문단 안 글자 구간에 글자 모양(굵게·크기 줄임)을 XML로 입힌다(알파 1-b, 2026-10-11).

한/글로 구간을 선택해 글자 모양을 바꾸는 대신, 구간 경계에서 run을 나누고 바뀐 글자 모양(charPr 사본)을 붙인다.
- 글자 위치는 run 글(hp:t 글과 그 안 자식 요소 뒤 글)로 센다. 자식 요소(고정폭 빈칸 등)는 글자로 세지 않는다.
- 구간 경계가 글만 든 run(hp:t 하나, 자식 요소 없음) 안에 있을 때만 나눈다. 다른 run 안에 경계가 걸리면 그 구간은 건너뛴다.
- 같은 (원래 글자 모양, 바꿀 내용)은 글자 모양 하나를 다시 쓴다.
"""

from __future__ import annotations

import copy

from .spacing_reset import _plain_run, _tag, run_text


class CharStyles:
    def __init__(self, header):
        self.header = header
        self.group = next((x for x in header.iter() if _tag(x) == "charProperties"), None)
        self.chars = {x.get("id"): x for x in header.iter() if _tag(x) == "charPr"}
        self.made = {}

    def height_pt(self, char_id):
        c = self.chars.get(char_id)
        try:
            return int(c.get("height")) / 100 if c is not None else None
        except (TypeError, ValueError):
            return None

    def is_bold(self, char_id):
        c = self.chars.get(char_id)
        return c is not None and any(_tag(x) == "bold" for x in c)

    def variant(self, char_id, bold=False, shrink_pt=0.0):
        key = (char_id, bool(bold), float(shrink_pt))
        if key in self.made:
            return self.made[key]
        source = self.chars.get(char_id)
        if source is None or self.group is None:
            return char_id
        clone = copy.deepcopy(source)
        new_id = str(1 + max((int(x.get("id")) for x in self.group if (x.get("id") or "").isdigit()), default=-1))
        clone.set("id", new_id)
        if bold and not any(_tag(x) == "bold" for x in clone):
            ns = source.tag.rsplit("}", 1)[0] + "}" if "}" in source.tag else ""
            bold_el = type(source)(ns + "bold", {})
            # 한/글 순서(fontRef·ratio·spacing·relSz·offset 뒤, underline 앞)를 지키려고 underline 앞에 넣는다.
            kids = list(clone)
            at = next((i for i, x in enumerate(kids) if _tag(x) in ("italic", "underline", "strikeout", "outline",
                                                                     "shadow", "emboss", "engrave", "supscript",
                                                                     "subscript")), len(kids))
            clone.insert(at, bold_el)
        if shrink_pt:
            try:
                clone.set("height", str(max(100, int(clone.get("height")) - round(shrink_pt * 100))))
            except (TypeError, ValueError):
                pass
        self.group.append(clone)
        self.group.set("itemCnt", str(len(self.group)))
        self.chars[new_id] = clone
        self.made[key] = new_id
        return new_id


def paragraph_text(p) -> str:
    return "".join(run_text(r) for r in p if _tag(r) == "run")


def char_id_at(p, offset):
    """offset 글자가 든 run의 글자 모양 id. 없으면 None."""
    pos = 0
    for r in p:
        if _tag(r) != "run":
            continue
        n = len(run_text(r))
        if pos <= offset < pos + n:
            return r.get("charPrIDRef")
        pos += n
    return None


def _split_at(p, offset) -> bool:
    """offset 위치에 run 경계를 만든다. 경계가 이미 있으면 True, 나눌 수 없는 run 안이면 False."""
    pos = 0
    for r in [x for x in p if _tag(x) == "run"]:
        n = len(run_text(r))
        if offset == pos or offset == pos + n:
            return True
        if pos < offset < pos + n:
            if not _plain_run(r):
                return False
            cut = offset - pos
            t = r[0]
            tail = copy.deepcopy(r)
            tail[0].text = (t.text or "")[cut:]
            t.text = (t.text or "")[:cut]
            p.insert(list(p).index(r) + 1, tail)
            return True
        pos += n
    return offset == pos


def apply_ranges(p, ranges, styles: CharStyles) -> int:
    """ranges [(시작, 끝, {"bold": bool, "shrink_pt": float})]를 문단 p에 입힌다. 입힌 구간 수를 돌려준다."""
    applied = 0
    for start, end, change in ranges:
        if end <= start or not (_split_at(p, start) and _split_at(p, end)):
            continue
        pos = 0
        for r in [x for x in p if _tag(x) == "run"]:
            n = len(run_text(r))
            if start <= pos and pos + n <= end and n:
                r.set("charPrIDRef", styles.variant(r.get("charPrIDRef"), bold=change.get("bold", False),
                                                  shrink_pt=change.get("shrink_pt", 0.0)))
            pos += n
        applied += 1
    if applied:
        for cache in [x for x in p if _tag(x) == "linesegarray"]:
            p.remove(cache)
    return applied
