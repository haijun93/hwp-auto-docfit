"""빈 줄 서식: 예시 보고서의 빈 줄(간격용 줄) 모양을 자리별로 배워 정리할 문서의 같은 자리 빈 줄에 입힌다.

보고서의 빈 줄은 서식이다. 제목 표 앞 150%, 개요 상자 뒤 오른쪽 정렬, 항목 사이 HY견고딕 5pt 간격용 줄,
문서 끝 170%처럼 자리마다 줄 간격·글자 크기·정렬이 다르다. 예전에는 빈 줄에 본문 대표 줄 간격만 입혀
예시 자신의 서식을 해제했다가 다시 입혀도 원래 모습이 나오지 않았다(서식 재연 시험, 2026-10-16).

자리(slot)는 (앞 요소 역할, 뒤 요소 역할, 연속 빈 줄 안 순번)이다. 역할은 제목 표·중제목 표·붙임 표·한 칸 상자·
일반 표·그림 등 개체·항목기호 묶음(□ ㅇ - ※ * …)·일반 문장, 문서 처음(start)·끝(end)이다.
표를 담은 글 없는 문단도 같은 방식으로 표 종류별(자리 'host|역할')로 배운다. 이 문단의 정렬이 표의 가로 위치다
(예: 예시의 데이터 표는 오른쪽 정렬 문단에 들어 있다).
구역 바로 아래 문단만 다룬다(표 칸 안 빈 줄은 표 서식 복제가 맡는다).
"""

from __future__ import annotations

from defusedxml import ElementTree as ET

from .style_unify import unify_marker

OBJECTS = {"tbl", "pic", "rect", "ellipse", "line", "container", "equation", "ole", "polygon", "curve", "arc",
           "textart", "connectLine"}


def _tag(element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _runs(paragraph):
    return [x for x in paragraph if _tag(x) == "run"]


def _text(paragraph) -> str:
    return "".join("".join(t.itertext()) for run in _runs(paragraph) for t in run if _tag(t) == "t")


def _objects(paragraph):
    return [x for run in _runs(paragraph) for x in run if _tag(x) in OBJECTS]


def is_blank(paragraph) -> bool:
    """글이 없거나 빈칸뿐이고 표·그림 같은 개체가 없는 문단."""
    return not _text(paragraph).strip() and not _objects(paragraph)


def role(paragraph, table_kind) -> str:
    """빈 줄이 아닌 문단의 역할. table_kind(tbl) → 'title1'·'midtitle2'·'attach1'·'box'·None(일반 표)."""
    objects = _objects(paragraph)
    if objects:
        first = objects[0]
        if _tag(first) != "tbl":
            return "object"
        kind = table_kind(first) or "table"
        return kind.rstrip("0123456789")
    group = unify_marker(_text(paragraph).strip())[0]
    return group or "text"


def slots(section, table_kind):
    """구역 바로 아래 빈 줄마다 (문단, 자리 열쇠 'prev|next|k'), 표만 담은 문단마다 (문단, 'host|역할')."""
    paragraphs = [p for p in section if _tag(p) == "p"]
    roles = [None if is_blank(p) else role(p, table_kind) for p in paragraphs]
    found = []
    for index, p in enumerate(paragraphs):
        if roles[index] is not None:
            if not _text(p).strip() and len(_objects(p)) == 1 and _tag(_objects(p)[0]) == "tbl":
                found.append((p, f"host|{roles[index]}"))
            continue
        before = next((r for r in reversed(roles[:index]) if r is not None), "start")
        after = next((r for r in roles[index + 1:] if r is not None), "end")
        k = 0
        while index - k - 1 >= 0 and roles[index - k - 1] is None:
            k += 1
        found.append((p, f"{before}|{after}|{k}"))
    return found


def _refs(header):
    groups = {}
    for name in ("fontfaces", "borderFills", "tabProperties", "charProperties", "paraProperties"):
        groups[name] = next((x for x in header.iter() if _tag(x) == name), None)
    return groups


def _by_id(group, ident):
    return next((x for x in group if x.get("id") == ident), None) if group is not None else None


def learn(header, sections, table_kind) -> dict:
    """예시 문서의 빈 줄 모양: {'slots': {열쇠: {'para': xml, 'char': xml, 'fonts': {lang: font xml},
    'border': xml|None, 'tab': xml|None}}}. 같은 자리에 여러 빈 줄이 있으면 처음 것."""
    groups = _refs(header)
    fonts = {ff.get("lang"): ff for ff in (groups["fontfaces"] if groups["fontfaces"] is not None else [])}
    result = {}
    for section in sections:
        for p, key in slots(section, table_kind):
            if key in result:
                continue
            para = _by_id(groups["paraProperties"], p.get("paraPrIDRef"))
            runs = _runs(p)
            char = _by_id(groups["charProperties"], runs[0].get("charPrIDRef")) if runs else None
            if para is None or char is None:
                continue
            ref = next((x for x in char if _tag(x) == "fontRef"), None)
            used = {}
            for lang, ident in (ref.attrib.items() if ref is not None else ()):
                face = fonts.get(lang.upper())
                font = _by_id(face, ident) if face is not None else None
                if font is not None:
                    used[lang] = ET.tostring(font, encoding="unicode")
            border = next((x for x in para.iter() if _tag(x) == "border"), None)
            fill = _by_id(groups["borderFills"], border.get("borderFillIDRef")) if border is not None else None
            tab = _by_id(groups["tabProperties"], para.get("tabPrIDRef"))
            char_fill = _by_id(groups["borderFills"], char.get("borderFillIDRef"))
            result[key] = {"para": ET.tostring(para, encoding="unicode"), "char": ET.tostring(char, encoding="unicode"),
                           "fonts": used,
                           "border": ET.tostring(fill, encoding="unicode") if fill is not None else None,
                           "char_border": ET.tostring(char_fill, encoding="unicode") if char_fill is not None else None,
                           "tab": ET.tostring(tab, encoding="unicode") if tab is not None else None}
    return {"version": 1, "slots": result} if result else {}


def _lookup(learned, key):
    slots_ = learned.get("slots") or {}
    if key in slots_:
        return slots_[key]
    if key.startswith("host|"):
        return None
    prefix = key.rsplit("|", 1)[0] + "|"
    same = sorted(k for k in slots_ if k.startswith(prefix))
    return slots_[same[-1]] if same else None       # 연속 빈 줄이 예시보다 많으면 예시의 마지막 빈 줄 모양


def _append(group, element):
    element.set("id", str(1 + max((int(x.get("id")) for x in group), default=-1)))
    group.append(element)
    group.set("itemCnt", str(len(group)))
    return element.get("id")


def _font_id(groups, lang, xml):
    face = next((x for x in groups["fontfaces"] if x.get("lang", "").lower() == lang.lower()), None)
    sample = ET.fromstring(xml)
    if face is None or not len(face):
        return None
    same = next((x for x in face if x.get("face") == sample.get("face") and x.get("type") == sample.get("type")), None)
    if same is not None:
        return same.get("id")
    clone = _clone(next(iter(face)), xml)
    clone.set("id", str(1 + max(int(x.get("id")) for x in face)))
    face.append(clone)
    face.set("fontCnt", str(len(face)))
    return clone.get("id")


def _clone(template, xml):
    """defusedxml로 읽은 요소를 대상 문서와 같은 요소 형식으로 복제한다."""
    sample = ET.fromstring(xml)

    def build(node):
        made = type(template)(node.tag, dict(node.attrib))
        made.text, made.tail = node.text, node.tail
        for child in node:
            made.append(build(child))
        return made
    return build(sample)


def apply(header, sections, learned, table_kind) -> int:
    """정리할 문서의 빈 줄에 예시의 같은 자리 빈 줄 모양을 입힌다. 바꾼 빈 줄 수."""
    if not (learned or {}).get("slots"):
        return 0
    groups = _refs(header)
    if any(groups[name] is None for name in ("fontfaces", "charProperties", "paraProperties")):
        return 0
    made, count = {}, 0
    for section in sections:
        for p, key in slots(section, table_kind):
            item = _lookup(learned, key)
            if item is None:
                continue
            ident = id(item)
            if ident not in made:
                template = next(iter(groups["paraProperties"]))
                para = _clone(template, item["para"])
                if item.get("border") and groups["borderFills"] is not None:
                    fill_id = _append(groups["borderFills"], _clone(template, item["border"]))
                    for border in (x for x in para.iter() if _tag(x) == "border"):
                        border.set("borderFillIDRef", fill_id)
                if item.get("tab") and groups["tabProperties"] is not None:
                    para.set("tabPrIDRef", _append(groups["tabProperties"], _clone(template, item["tab"])))
                char = _clone(template, item["char"])
                ref = next((x for x in char if _tag(x) == "fontRef"), None)
                if ref is not None:
                    for lang, xml in item.get("fonts", {}).items():
                        new = _font_id(groups, lang, xml)
                        if new is not None:
                            ref.set(lang, new)
                if item.get("char_border") and groups["borderFills"] is not None:
                    char.set("borderFillIDRef", _append(groups["borderFills"], _clone(template, item["char_border"])))
                made[ident] = (_append(groups["paraProperties"], para), _append(groups["charProperties"], char))
            para_id, char_id = made[ident]
            p.set("paraPrIDRef", para_id)
            if not key.startswith("host|"):
                for run in _runs(p):
                    run.set("charPrIDRef", char_id)
            for cache in [x for x in p if _tag(x) == "linesegarray"]:
                p.remove(cache)
            count += 1
    return count
