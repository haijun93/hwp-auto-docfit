"""연속된 연결 부호 문장을 한/글 목차 점선(채울 모양이 있는 탭)으로 정렬한다(알파, 2026-10-10 사용자 규칙).

목차·일정표처럼 여러 줄에 연이어 '왼쪽 글 + 연결 부호(점·선·여러 칸 빈칸) + 오른쪽 글'이 있으면, 연결 부호의
목적은 오른쪽 글의 첫 글자를 세로로 가지런히 맞추는 것이다. 이는 한/글 목차 점선 기능(채울 모양이 있는 탭)과
같다. 묶음의 연결 부호를 탭 하나로 바꾸고 공통 탭 위치·채울 모양을 주면, 부호 길이와 개수는 한/글이 줄마다
알아서 채운다.

- 탭 위치: 묶음에서 가장 긴 왼쪽 글 뒤(글자 종류별 폭 추정 + 여유 1.5글자). 언제나 왼쪽 정렬 탭이라 오른쪽 글의
  첫 글자가 내어쓰기처럼 한 세로선에 선다. 오른쪽 글이 본문 폭을 넘으면 넘지 않는 데까지 앞으로 당긴다.
- 채울 모양: 점 → 점선, 선 → 선, 여러 칸 빈칸 → 없음(탭 위치만 맞춤). 한/글 실제 그림 기준으로 leader 값을 고른다.
"""

from __future__ import annotations

import copy
import re

CONNECTOR = re.compile(r"[-‐‑–—―]{3,}|[.·∙•‥…]{3,}|(?<=\S) {3,}(?=\S)|(?<=\S)　{2,}(?=\S)")
# 한/글 2020 실측(2026-10-10): tabItem leader="DASH"는 점(·····), "DOT"은 짧은 선(-----)으로 그려진다.
LEADER = {"dot": ("DASH", 2), "line": ("DOT", 3), "space": ("NONE", 0)}
GAP_EM = 1.5


def _tag(e) -> str:
    return e.tag.rsplit("}", 1)[-1]


def kind_of(connector: str) -> str:
    if connector.strip() == "":
        return "space"
    return "line" if connector[0] in "-‐‑–—―" else "dot"


def char_em(ch: str) -> float:
    """글자 폭 추정(글자 크기 1em 기준)."""
    o = ord(ch)
    if ch == " ":
        return 0.5
    if ch == "　" or 0xAC00 <= o <= 0xD7A3 or 0x1100 <= o <= 0x11FF or 0x3130 <= o <= 0x318F \
            or 0x4E00 <= o <= 0x9FFF or 0xFF01 <= o <= 0xFF60 or 0x2460 <= o <= 0x24FF or 0x25A0 <= o <= 0x25FF \
            or 0x2160 <= o <= 0x217F or 0x3000 <= o <= 0x303F:
        return 1.0
    if ch in ".,:;·'`|!()[]{}":
        return 0.33
    return 0.55


def text_em(text: str) -> float:
    return sum(char_em(c) for c in text)


def split_connector(text: str):
    """문단 글에서 연결 부호가 하나 있으면 (왼쪽, 부호, 오른쪽), 없거나 둘 이상이면 None(순수 함수)."""
    found = list(CONNECTOR.finditer(text or ""))
    if len(found) > 1 and all(not m.group(0).strip() for m in found):
        # '일    시      2026. 10. 7.'처럼 글자 사이를 띄운 라벨 안 빈칸이 있으면 마지막 빈칸(값 바로 앞)이 연결 부호다.
        found = found[-1:]
    if len(found) != 1:
        return None
    m = found[0]
    left, right = text[:m.start()], text[m.end():]
    if not left.strip() or not right.strip():
        return None
    return left.rstrip(" "), m.group(0), right.lstrip(" ")


def _paragraph_t(p):
    """글이 든 hp:t가 하나뿐이고 그 안에 자식 요소가 없을 때 그 t. 아니면 None(바꾸지 않는다)."""
    ts = [t for r in p if _tag(r) == "run" for t in r if _tag(t) == "t"]
    with_text = [t for t in ts if (t.text or "") or len(t)]
    if len(with_text) != 1 or len(with_text[0]):
        return None
    return with_text[0]


class _Header:
    def __init__(self, header):
        self.header = header
        self.paras = {x.get("id"): x for x in header.iter() if _tag(x) == "paraPr"}
        self.chars = {x.get("id"): x for x in header.iter() if _tag(x) == "charPr"}
        self.tab_group = next((x for x in header.iter() if _tag(x) == "tabProperties"), None)
        self.para_group = next((x for x in header.iter() if _tag(x) == "paraProperties"), None)
        self.made_tabs, self.made_paras = {}, {}

    def size_pt(self, char_id) -> float:
        c = self.chars.get(char_id)
        try:
            return int(c.get("height", "1000")) / 100 if c is not None else 10.0
        except ValueError:
            return 10.0

    def margin_left(self, para_id) -> int:
        p = self.paras.get(para_id)
        if p is None:
            return 0
        for x in p.iter():
            if _tag(x) == "left":
                try:
                    v = int(x.get("value", "0"))
                except ValueError:
                    return 0
                # 문단 여백 값은 hp:case(HwpUnitChar)이면 HWPUNIT, default면 두 배 값이다. 처음 만나는 값(case)을 쓴다.
                return v
        return 0

    def tab_id(self, pos, kind, align):
        key = (pos, kind, align)
        if key in self.made_tabs:
            return self.made_tabs[key]
        group = self.tab_group
        ns_h = group.tag.rsplit("}", 1)[0] + "}"
        ns_p = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
        new_id = str(1 + max((int(x.get("id")) for x in group if (x.get("id") or "").isdigit()), default=-1))
        tab = type(group)(ns_h + "tabPr", {"id": new_id, "autoTabLeft": "0", "autoTabRight": "0"})
        switch = type(group)(ns_p + "switch", {})
        case = type(group)(ns_p + "case", {"{http://www.hancom.co.kr/hwpml/2011/paragraph}required-namespace":
                                          "http://www.hancom.co.kr/hwpml/2016/HwpUnitChar"})
        leader = LEADER[kind][0]
        case.append(type(group)(ns_h + "tabItem", {"pos": str(pos), "type": align, "leader": leader, "unit": "HWPUNIT"}))
        default = type(group)(ns_p + "default", {})
        default.append(type(group)(ns_h + "tabItem", {"pos": str(pos * 2), "type": align, "leader": leader}))
        switch.extend([case, default])
        tab.append(switch)
        group.append(tab)
        group.set("itemCnt", str(len(group)))
        self.made_tabs[key] = new_id
        return new_id

    def para_with_tab(self, para_id, tab_id):
        key = (para_id, tab_id)
        if key in self.made_paras:
            return self.made_paras[key]
        source = self.paras.get(para_id)
        if source is None:
            return para_id
        clone = copy.deepcopy(source)
        new_id = str(1 + max((int(x.get("id")) for x in self.para_group if (x.get("id") or "").isdigit()), default=-1))
        clone.set("id", new_id)
        clone.set("tabPrIDRef", tab_id)
        self.para_group.append(clone)
        self.para_group.set("itemCnt", str(len(self.para_group)))
        self.paras[new_id] = clone
        self.made_paras[key] = new_id
        return new_id


def groups_in(container):
    """같은 부모 안에서 연결 부호 문단이 2개 이상 이어진 묶음 [[(문단, t, 왼쪽, 부호, 오른쪽)…]]."""
    out, run = [], []
    for p in list(container):
        if _tag(p) != "p":
            continue
        t = _paragraph_t(p)
        parts = split_connector(t.text) if t is not None else None
        if parts and not any(_tag(x) == "tbl" for x in p.iter()):
            if run and kind_of(run[-1][3]) != kind_of(parts[1]):
                # 연결 부호 종류(점·선·빈칸)가 바뀌면 다른 묶음이다.
                if len(run) >= 2:
                    out.append(run)
                run = []
            run.append((p, t) + parts)
        else:
            if len(run) >= 2:
                out.append(run)
            run = []
    if len(run) >= 2:
        out.append(run)
    return out


def align_connectors(header_root, sections, text_width_of) -> dict:
    """모든 구역·칸의 연결 부호 묶음을 탭 정렬로 바꾼다. text_width_of(container) → 본문(칸) 폭 HWPUNIT."""
    head = _Header(header_root)
    if head.tab_group is None or head.para_group is None:
        return {"groups": 0, "paragraphs": 0}
    stats = {"groups": 0, "paragraphs": 0, "pulled": 0}
    containers = []
    for root in sections:
        containers.append(root)
        containers += [x for x in root.iter() if _tag(x) == "subList"]
    for container in containers:
        for group in groups_in(container):
            size = max(head.size_pt(t_parent_char(p, t)) for p, t, *_ in group)
            em = size * 100
            left = max(text_em(l) for _, _, l, _, _ in group) * em
            right = max(text_em(r) for _, _, _, _, r in group) * em
            margin = max(head.margin_left(p.get("paraPrIDRef")) for p, *_ in group)
            width = text_width_of(container) - margin
            # 오른쪽 글의 시작점이 한 세로선에 서도록 언제나 왼쪽 정렬 탭을 쓴다(사용자 규칙: 내어쓰기처럼 칼같이).
            # 오른쪽 글이 본문 폭을 넘으면 넘지 않는 데까지 탭을 앞으로 당기되 왼쪽 글(+0.5글자)보다 앞으로는 가지 않는다.
            pos = int(left + GAP_EM * em)
            align = "LEFT"
            if width > 0 and pos + right > width:
                pos = int(max(left + 0.5 * em, width - right))
                stats["pulled"] += 1
            kinds = {kind_of(c) for _, _, _, c, _ in group}
            kind = kinds.pop() if len(kinds) == 1 else "dot"
            tab = head.tab_id(pos, kind, align)
            for p, t, l, c, r in group:
                p.set("paraPrIDRef", head.para_with_tab(p.get("paraPrIDRef"), tab))
                for cache in [x for x in p if _tag(x) == "linesegarray"]:
                    p.remove(cache)
                ns_p = t.tag.rsplit("}", 1)[0] + "}"
                t.text = l
                tab_el = type(t)(ns_p + "tab", {"width": "0", "leader": str(LEADER[kind][1]),
                                                "type": "1" if align == "LEFT" else "2"})
                tab_el.tail = r
                t.append(tab_el)
                stats["paragraphs"] += 1
            stats["groups"] += 1
    return stats


def t_parent_char(p, t):
    for r in p:
        if _tag(r) == "run" and t in list(r):
            return r.get("charPrIDRef")
    return None
