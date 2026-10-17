"""강조 낱말: 예시 보고서의 항목기호 문장에서 일부 낱말만 굵게·다른 글꼴로 쓴 것을 배워 같은 계층의 같은 낱말에 입힌다.

사용자 결정(2026-10-16): 서식 복사는 예시 A의 서식을 해제한 사본에 다시 입혀 A와 100% 같아야 한다. 문장 안 강조
('- 휴먼명조 14 [중요 부분은 진하게 또는 한컴돋움(진하게)]'의 '진하게'·'한컴돋움')는 서식을 해제하면 근거가 사라지므로,
예시에서 낱말과 강조 모양(글꼴·굵게·기본 글자와의 크기 차)을 배워 둔다.

기본 글자는 문단에서 글자 수가 가장 많은 (글꼴, 굵게)이다. 그와 다른 run이 강조다. 항목기호 글자는 빼고,
구역 바로 아래 문단만 다룬다(표 칸은 표 서식 복제가 맡는다).
"""

from __future__ import annotations

import copy
import re
from collections import Counter

from defusedxml import ElementTree as ET

from .style_unify import parenthetical_spans, unify_marker

_AFTER_BOLD = ("underline", "strikeout", "outline", "shadow", "emboss", "engrave", "supscript", "subscript")


def _tag(element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _child(element, name):
    return next((x for x in element if _tag(x) == name), None)


class _Header:
    def __init__(self, header):
        self.header = header
        self.chars = {x.get("id"): x for x in header.iter() if _tag(x) == "charPr"}
        self.char_group = next((x for x in header.iter() if _tag(x) == "charProperties"), None)
        self.faces = {x.get("lang", "").lower(): x for x in header.iter() if _tag(x) == "fontface"}

    def face(self, char_id):
        char = self.chars.get(char_id)
        ref = _child(char, "fontRef") if char is not None else None
        group = self.faces.get("hangul")
        if ref is None or group is None:
            return None
        return next((f.get("face") for f in group if f.get("id") == ref.get("hangul")), None)

    def signature(self, char_id):
        char = self.chars.get(char_id)
        if char is None:
            return None
        return self.face(char_id), _child(char, "bold") is not None, int(char.get("height") or 0)


def _simple_runs(paragraph):
    """(run, 글) 목록. 글 요소가 하나뿐이고 안에 다른 요소(빈칸 묶음 등)가 없는 run만 다룬다. 아니면 None."""
    out = []
    for run in (x for x in paragraph if _tag(x) == "run"):
        texts = [x for x in run if _tag(x) == "t"]
        others = [x for x in run if _tag(x) != "t"]
        if not texts:
            if others:
                out.append((run, ""))
            continue
        if len(texts) != 1 or len(texts[0]):
            return None
        out.append((run, texts[0].text or ""))
    return out


def _main(runs, info):
    weights, sizes = Counter(), Counter()
    for run, text in runs:
        sig = info.signature(run.get("charPrIDRef"))
        if sig is not None and text.strip():
            weights[sig[:2]] += len(text.strip())
            sizes[sig] += len(text.strip())
    if not weights:
        return None, None
    main = weights.most_common(1)[0][0]
    size = max((s for s in sizes if s[:2] == main), key=sizes.get)[2]
    return main, size


def _key(text):
    """문장 비교 열쇠: 빈칸을 뺀 글(공백 규칙이 빈칸을 바꿔도 같은 문장으로 본다)."""
    return re.sub(r"\s", "", text or "")


def _marker_end(text):
    group, _, raw = unify_marker(text.strip())
    lead = len(text) - len(text.lstrip())
    return group, lead + len(raw) if raw else 0


def learn(header, sections) -> list:
    """[{'marker', 'text', 'font', 'bold', 'size_delta', 'fonts': {lang: font xml}}]. 같은 (계층, 낱말)은 처음 것."""
    info = _Header(header)
    found, seen = [], set()
    for section in sections:
        for p in (x for x in section if _tag(x) == "p"):
            runs = _simple_runs(p)
            if not runs:
                continue
            full = "".join(t for _, t in runs)
            group, marker_end = _marker_end(full)
            if not group:
                continue
            main, main_size = _main(runs, info)
            if main is None:
                continue
            position = 0
            for run, text in runs:
                start, position = position, position + len(text)
                sig = info.signature(run.get("charPrIDRef"))
                word = text.strip()
                if not word or sig is None or sig[:2] == main or start < marker_end:
                    continue
                key = (group, full.strip(), word)
                if key in seen:
                    continue
                seen.add(key)
                char = info.chars[run.get("charPrIDRef")]
                ref = _child(char, "fontRef")
                fonts = {}
                if sig[0] != main[0] and ref is not None:
                    for lang, ident in ref.attrib.items():
                        face = info.faces.get(lang.lower())
                        font = next((f for f in face if f.get("id") == ident), None) if face is not None else None
                        if font is not None:
                            fonts[lang] = ET.tostring(font, encoding="unicode")
                # 강조는 그 문장 안에서만 입힌다(context). 예전에는 같은 계층의 같은 낱말 모두에 입혀, 한 문장에서
                # 굵게 쓴 '학교'가 다른 문장의 '학교'까지 굵게 했다(교육부 업무계획 재연 시험, 2026-10-17).
                found.append({"marker": group, "text": word, "font": sig[0] if sig[0] != main[0] else None,
                              "bold": sig[1], "size_delta": sig[2] - main_size, "fonts": fonts,
                              "context": _key(full)})
    return found + learn_colors(header, sections)


def learn_colors(header, sections) -> list:
    """문서 대부분과 다른 글자색(예시의 파란 표시 글)을 배운다. 문단 전체가 그 색이면 문단 글 전체(whole),
    일부면 그 낱말을 열쇠로 둔다. 항목기호만 있는 run·한 글자는 배우지 않는다(다른 문단에 번지지 않게)."""
    info = _Header(header)
    colors, paragraphs = Counter(), []
    for section in sections:
        for p in (x for x in section if _tag(x) == "p"):
            runs = _simple_runs(p)
            if not runs:
                continue
            painted = [(run, text, (info.chars.get(run.get("charPrIDRef")).get("textColor") or "#000000").upper()
                        if info.chars.get(run.get("charPrIDRef")) is not None else None) for run, text in runs]
            for _, text, color in painted:
                if color:
                    colors[color] += len(text.strip())
            paragraphs.append(painted)
    if not colors:
        return []
    main = colors.most_common(1)[0][0]
    found, seen = [], set()
    for painted in paragraphs:
        full = "".join(t for _, t, _ in painted)
        group, marker_end = _marker_end(full)
        odd = {c for _, t, c in painted if t.strip() and c and c != main}
        if not odd:
            continue
        if len(odd) == 1 and all(c != main for _, t, c in painted if t.strip()):
            entry = {"kind": "color", "marker": group, "text": full.strip(), "color": odd.pop(), "whole": True}
        else:
            for _, text, color in painted:
                word = text.strip()
                if color in (None, main) or len(word) < 2 or word == unify_marker(word)[2]:
                    continue
                if (group, full.strip(), word, color) not in seen:
                    seen.add((group, full.strip(), word, color))
                    found.append({"kind": "color", "marker": group, "text": word, "color": color, "whole": False,
                                  "context": _key(full)})
            continue
        if (group, entry["text"]) not in seen:
            seen.add((group, entry["text"]))
            found.append(entry)
    return found


def _clone_like(template, xml):
    sample = ET.fromstring(xml)

    def build(node):
        made = type(template)(node.tag, dict(node.attrib))
        made.text, made.tail = node.text, node.tail
        for child in node:
            made.append(build(child))
        return made
    return build(sample)


def _font_id(info, lang, xml):
    group = info.faces.get(lang.lower())
    if group is None or not len(group):
        return None
    sample = ET.fromstring(xml)
    same = next((f for f in group if f.get("face") == sample.get("face") and f.get("type") == sample.get("type")), None)
    if same is not None:
        return same.get("id")
    clone = _clone_like(next(iter(group)), xml)
    clone.set("id", str(1 + max(int(f.get("id")) for f in group)))
    group.append(clone)
    group.set("fontCnt", str(len(group)))
    return clone.get("id")


def _styled(info, base_id, entry, cache):
    key = (base_id, id(entry))
    if key in cache:
        return cache[key]
    source = info.chars.get(base_id)
    if source is None or info.char_group is None:
        return base_id
    clone = copy.deepcopy(source)
    if entry.get("kind") == "color":
        clone.set("textColor", entry["color"])
        clone.set("id", str(1 + max(int(x.get("id")) for x in info.char_group)))
        info.char_group.append(clone)
        info.char_group.set("itemCnt", str(len(info.char_group)))
        info.chars[clone.get("id")] = clone
        cache[key] = clone.get("id")
        return cache[key]
    clone.set("height", str(max(100, int(source.get("height") or 1000) + int(entry.get("size_delta") or 0))))
    if entry.get("font"):
        ref = _child(clone, "fontRef")
        for lang, xml in (entry.get("fonts") or {}).items():
            new = _font_id(info, lang, xml)
            if new is not None and ref is not None:
                ref.set(lang, new)
    bold = _child(clone, "bold")
    if entry.get("bold") and bold is None:
        ns = clone.tag.rsplit("}", 1)[0] + "}"
        index = next((i for i, x in enumerate(clone) if _tag(x) in _AFTER_BOLD), len(clone))
        clone.insert(index, type(clone)(ns + "bold", {}))
    elif not entry.get("bold") and bold is not None:
        clone.remove(bold)
    clone.set("id", str(1 + max(int(x.get("id")) for x in info.char_group)))
    info.char_group.append(clone)
    info.char_group.set("itemCnt", str(len(info.char_group)))
    info.chars[clone.get("id")] = clone
    cache[key] = clone.get("id")
    return cache[key]


def _split(paragraph, runs, a, b):
    """글 위치 a·b에서 run을 나눠 [a, b)를 덮는 run 목록을 돌려준다."""
    covered, position = [], 0
    for run, text in list(runs):
        start, end = position, position + len(text)
        position = end
        if not text or end <= a or start >= b:
            continue
        cuts = sorted({max(start, a), min(end, b)} - {start, end})
        pieces, last = [], start
        for cut in cuts + [end]:
            pieces.append((last, cut))
            last = cut
        index = list(paragraph).index(run)
        t = next(x for x in run if _tag(x) == "t")
        made = []
        for offset, (s, e) in enumerate(pieces):
            if offset == 0:
                piece = run
            else:
                piece = copy.deepcopy(run)
                for child in [x for x in piece if _tag(x) != "t"]:
                    piece.remove(child)        # 컨트롤은 첫 조각에만 둔다
                paragraph.insert(index + offset, piece)
            next(x for x in piece if _tag(x) == "t").text = text[s - start:e - start]
            made.append((piece, s, e))
        for piece, s, e in made:
            if s >= a and e <= b:
                covered.append(piece)
    return covered


def apply(header, sections, learned) -> int:
    """정리할 문서의 같은 계층 문장에 나오는 같은 낱말에 강조 모양을 입힌다. 입힌 낱말 수."""
    if not learned:
        return 0
    info = _Header(header)
    if info.char_group is None:
        return 0
    cache, count = {}, 0
    for section in sections:
        for p in (x for x in section if _tag(x) == "p"):
            runs = _simple_runs(p)
            if not runs:
                continue
            full = "".join(t for _, t in runs)
            group, marker_end = _marker_end(full)
            entries = [e for e in learned if e.get("marker") == group and (group or e.get("kind") == "color")
                       and e.get("context") in (None, _key(full))]
            if not entries:
                continue
            spans = []
            for entry in entries:
                if entry.get("whole"):
                    if full.strip() != entry["text"]:
                        continue
                    at = full.index(entry["text"])
                else:
                    at = full.find(entry["text"], marker_end)
                if at < 0 or any(at < y and x < at + len(entry["text"]) for x, y, _ in spans):
                    continue
                spans.append((at, at + len(entry["text"]), entry))
            for a, b, entry in spans:
                runs = _simple_runs(p)
                for piece in _split(p, runs, a, b):
                    piece.set("charPrIDRef", _styled(info, piece.get("charPrIDRef"), entry, cache))
                count += 1
            if spans:
                for cache_el in [x for x in p if _tag(x) == "linesegarray"]:
                    p.remove(cache_el)
    return count


def overview_paren_delta(header, sections, table_kind):
    """개요 상자(제목 표 바로 다음 1×1 상자) 문단에서 괄호 안 글자를 바깥보다 줄인 폭(pt). 괄호가 없으면 None.

    서식 분석의 괄호 줄임은 항목기호 문장만 재서, 항목기호 없는 개요 글의 '(지구)' 줄임을 배우지 못했다
    (서식 재연 시험, 2026-10-17).
    """
    info = _Header(header)
    inside, outside = Counter(), Counter()
    for section in sections:
        previous = None
        for p in (x for x in section if _tag(x) == "p"):
            tables = [t for r in p if _tag(r) == "run" for t in r if _tag(t) == "tbl"]
            if not tables:
                if "".join("".join(t.itertext()) for r in p if _tag(r) == "run" for t in r if _tag(t) == "t").strip():
                    previous = None
                continue
            for table in tables:
                kind = table_kind(table) or ""
                if kind == "box" and (previous or "").startswith("title"):
                    for q in (x for x in table.iter() if _tag(x) == "p"):
                        runs = _simple_runs(q) or []
                        text = "".join(t for _, t in runs)
                        spans = parenthetical_spans(text, (), include_trailing=True)
                        position = 0
                        for run, part in runs:
                            sig = info.signature(run.get("charPrIDRef"))
                            for offset, letter in enumerate(part):
                                if sig is None or letter.isspace():
                                    continue
                                where = position + offset
                                (inside if any(a <= where < b for a, b in spans) else outside)[sig[2]] += 1
                            position += len(part)
                previous = kind
    if not inside or not outside:
        return None
    return round((outside.most_common(1)[0][0] - inside.most_common(1)[0][0]) / 100, 1)
