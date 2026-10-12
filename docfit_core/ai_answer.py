"""생성형 AI(챗GPT·클로드·제미나이) 답변을 복사한 그대로 개조식 문서로 바꾼다(알파, 2026-10-12).

답변 속 마크다운 구조(표제 ``#``, 번호 표제 ``1.``, 굵은 줄 표제, 글머리 ``* - +``, 들여쓰기 목록, 표, 인용, 참고 줄)를
읽어 ``labeled_text``와 같은 블록(제목·개요 상자·항목기호 문단·표)으로 만든다. 라벨(제목:/네모:/원:)을 AI에게 따로
시키지 않아도 된다. 순수 함수만 있어 한/글 없이 시험할 수 있다.

계층 규칙
    표제 순위 0 → □, 1 → ㅇ, 2 → -, 3 이상 → •   (표제가 하나도 없으면 최상위 글머리가 □)
    표제 아래 글머리·문단은 표제 바로 아래 단계에서 시작하고, 들여쓰기 칸 수가 아니라 **서로 다른 들여쓰기의 순서**로 한 단계씩 내려간다
    (2칸·3칸·4칸·탭 모두 같은 결과).
문장은 고치지 않는다. 항목기호와 구조만 바꾸며, 사실관계·말투(개조식 문체)는 사용자가 확인한다.
"""

from __future__ import annotations

import re

from docfit_core.labeled_text import looks_labeled
from docfit_core.pasted_text import (
    _BLOCKQUOTE_MARKER, _CODE_FENCE, _HR_LINE, _MARKER_GLUE, _TABLE_ROW, _TABLE_SEPARATOR, _strip_inline_markup,
    _strip_invisible, _ESCAPED_MD_CHAR,
)

TIER_MARKERS = ("□", "ㅇ", "-", "•")
_LABEL_BY_MARKER = {"□": "네모", "ㅇ": "원", "-": "바", "•": "점", "※": "당구", "*": "주석", "**": "주석2"}

_EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️‍]")
_MD_HEADING = re.compile(r"^(#{1,6})[ \t]+(?=\S)(.*)$")
_BULLET = re.compile(r"^([ \t]*)[-*+•‣◦▪·∙][ \t]+(?=\S)(.*)$")
_NUMBERED = re.compile(r"^([ \t]*)(?:\d{1,3}[.)]|\(\d{1,3}\)|[가-하][.)]|[①-⑳])[ \t]+(?=\S)(.*)$")
_BOLD_ONLY = re.compile(r"^\*\*([^*]+?)\*\*[ \t]*[:：]?$")
_NOTE_START = re.compile(r"^(?:※|ⓘ|[☞▶]|(?:참고|유의|주의|비고|알림)[ \t]*[:：])[ \t]*(.*)$")
_SENTENCE_END = re.compile(r"[.!?…。]$|(?:다|요|음|함|임)\.?$")
_STRONG_MD = re.compile(r"(\*\*|^#{1,6}[ \t]|^[ \t]*[-*+][ \t]+\S|^[ \t]*\d{1,3}[.)][ \t]+\S|【[^】]*】|\[\d{1,4}\])", re.M)
_ALREADY_REPORT = re.compile(r"^[ \t]*(?:□|ㅁ|ㅇ|○|※)[ \t]+\S", re.M)
_HEADING_NUMBER = re.compile(r"^(?:\d{1,2}[.)]|[가-하][.)]|[Ⅰ-Ⅻ][.)]?|[IVX]{1,4}\.|\(\d{1,2}\))[ \t]+(?=\S)")


def _clean(text: str) -> str:
    return _EMOJI.sub("", _strip_inline_markup(text)).strip()


def _heading_clean(text: str) -> str:
    """표제 글: 앞의 번호(1. 가. Ⅰ.)는 항목기호가 대신하므로 뗀다."""
    return _HEADING_NUMBER.sub("", _clean(text), count=1)


def looks_like_ai_answer(text: str) -> bool:
    """붙여넣은 글이 AI 채팅 답변(마크다운 구조)처럼 보이는지. 라벨 형식·이미 □ ㅇ 항목기호인 글은 아니다."""
    text = text or ""
    if not text.strip() or looks_labeled(text) or _ALREADY_REPORT.search(text):
        return False
    hits = _STRONG_MD.findall(text)
    return len(hits) >= 2


def _split_elements(text: str) -> list[dict]:
    """줄을 요소(표제·글머리·번호·굵은 줄·표·문단·참고)로 나눈다."""
    text = _strip_invisible(text)
    text = _ESCAPED_MD_CHAR.sub(r"\1", text)
    text = _MARKER_GLUE.sub("\n", text)
    elements: list[dict] = []
    fence = False
    previous_blank = True
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        stripped = raw.strip()
        if _CODE_FENCE.match(stripped):
            fence = not fence
            previous_blank = True
            continue
        if fence:
            if stripped:
                elements.append({"kind": "item", "indent": 0, "text": stripped, "numbered": False})
            continue
        if not stripped:
            previous_blank = True
            continue
        if _TABLE_SEPARATOR.match(stripped) and elements and elements[-1]["kind"] == "table":
            continue                                     # 표 머리글 아래 구분선: 같은 표로 이어 간다
        if _HR_LINE.match(stripped) or _TABLE_SEPARATOR.match(stripped):
            previous_blank = True
            continue
        quoted = bool(_BLOCKQUOTE_MARKER.match(stripped))
        line = _BLOCKQUOTE_MARKER.sub("", stripped) if quoted else raw.rstrip()
        stripped_line = line.strip()
        heading = _MD_HEADING.match(stripped_line)
        if heading and not quoted:
            elements.append({"kind": "heading", "key": ("md", len(heading.group(1))), "text": _heading_clean(heading.group(2)),
                             "after_blank": previous_blank})
            previous_blank = False
            continue
        if not quoted and _TABLE_ROW.match(stripped_line) and stripped_line.count("|") >= 2:
            cells = [_clean(cell) for cell in stripped_line.strip("|").split("|")]
            row = [cell for cell in cells]
            if elements and elements[-1]["kind"] == "table" and not previous_blank:
                elements[-1]["rows"].append(row)
            else:
                elements.append({"kind": "table", "rows": [row]})
            previous_blank = False
            continue
        note = _NOTE_START.match(stripped_line)
        if quoted or note:
            body = _clean(note.group(1) if note and not quoted else stripped_line)
            if note and quoted:
                body = _clean(note.group(1))
            if body:
                elements.append({"kind": "note", "text": body})
            previous_blank = False
            continue
        bullet = _BULLET.match(line)
        numbered = _NUMBERED.match(line)
        if bullet:
            elements.append({"kind": "item", "indent": len(bullet.group(1).expandtabs(4)),
                             "text": _clean(bullet.group(2)), "numbered": False})
            previous_blank = False
            continue
        if numbered:
            elements.append({"kind": "item", "indent": len(numbered.group(1).expandtabs(4)),
                             "text": _clean(numbered.group(2)), "numbered": True, "after_blank": previous_blank})
            previous_blank = False
            continue
        bold = _BOLD_ONLY.match(stripped_line)
        if bold:
            elements.append({"kind": "heading", "key": ("bold", 0), "text": _heading_clean(bold.group(1)).rstrip(":："),
                             "after_blank": previous_blank})
            previous_blank = False
            continue
        content = _clean(stripped_line)
        if not content:
            continue
        indented = bool(raw[:1].isspace())
        previous = elements[-1] if elements else None
        if previous and not previous_blank and (
                previous["kind"] == "para" or (previous["kind"] in ("item", "note") and indented)):
            previous["text"] += " " + content               # 줄바꿈으로 끊긴 같은 문장
        else:
            elements.append({"kind": "para", "text": content, "after_blank": previous_blank})
        previous_blank = False
    return elements


def _next_content(elements: list[dict], index: int):
    return elements[index + 1] if index + 1 < len(elements) else None


def _is_short_title(text: str) -> bool:
    return 0 < len(text) <= 40 and not _SENTENCE_END.search(text) and not text.endswith((":", "：", ",", "，", ";"))


def _classify(elements: list[dict]) -> None:
    """번호 표제·제목 같은 짧은 줄을 표제로 올린다(내용 목록과 구별)."""
    has_md = any(e["kind"] == "heading" and e["key"][0] == "md" for e in elements)
    numbered = [i for i, e in enumerate(elements) if e["kind"] == "item" and e["numbered"] and e["indent"] == 0]
    if numbered and not has_md:
        followed = [i for i in numbered if (_next_content(elements, i) or {"kind": "end"})["kind"]
                    in ("item", "para", "note", "table") and not (
                        _next_content(elements, i)["kind"] == "item" and _next_content(elements, i)["numbered"]
                        and _next_content(elements, i)["indent"] == 0)]
        if followed and all(len(elements[i]["text"]) <= 120 for i in numbered):
            for i in numbered:
                if _is_short_title(elements[i]["text"]) or i in followed:
                    elements[i].update(kind="heading", key=("num", 0), after_blank=True)
    for i, e in enumerate(elements):
        if e["kind"] != "para" or not e.get("after_blank", True) or not _is_short_title(e["text"]):
            continue
        nxt = _next_content(elements, i)
        if nxt is not None and nxt["kind"] in ("item", "table"):
            e.update(kind="heading", key=("plain", 0))
        elif e["text"].endswith(":") or e["text"].endswith("："):
            continue


def _rank_headings(elements: list[dict]) -> None:
    """표제마다 순위(0이 가장 큼)를 붙인다. 같은 모양은 같은 순위, 새 모양은 한 단계 아래."""
    kinds_present = {e["key"][0] for e in elements if e["kind"] == "heading"}
    alias = next((kind for kind in ("num", "bold") if kind in kinds_present), None)
    stack: list[tuple] = []
    for e in elements:
        if e["kind"] != "heading":
            continue
        key = e["key"]
        if key[0] == "plain" and alias:
            key = (alias, 0)
        elif key[0] == "plain" and "md" in kinds_present:
            key = ("md", 99)
        if key in stack:
            del stack[stack.index(key) + 1:]
        elif key[0] == "md":
            while stack and stack[-1][0] == "md" and stack[-1][1] >= key[1]:
                stack.pop()
            stack.append(key)
        else:
            stack.append(key)
        e["rank"] = len(stack) - 1


def _marker(tier: int) -> str:
    return TIER_MARKERS[min(tier, len(TIER_MARKERS) - 1)]


def parse_ai_answer(text: str) -> list[dict]:
    """AI 답변 글을 labeled_text 블록(title·box·para·table)으로 바꾼다."""
    elements = _split_elements(text)
    if not elements:
        return []
    _classify(elements)
    _rank_headings(elements)
    blocks: list[dict] = []
    # 문서 제목: 맨 앞의 단 하나뿐인 최상위 마크다운 표제(# 제목) 또는 굵은 첫 줄
    first = elements[0]
    title_text = None
    if first["kind"] == "heading" and first["key"][0] in ("md", "bold") and first.get("rank") == 0:
        same = [e for e in elements if e["kind"] == "heading" and e.get("rank") == 0 and e["key"] == first["key"]]
        others = [e for e in elements if e["kind"] == "heading" and e is not first]
        if len(same) == 1 and others:
            title_text = first["text"]
            elements = elements[1:]
            for e in elements:
                if e["kind"] == "heading":
                    e["rank"] = max(0, e["rank"] - 1)
    if title_text:
        blocks.append({"kind": "title1", "text": title_text})
    has_heading = any(e["kind"] == "heading" for e in elements)
    # 표제가 없으면 글머리가 □부터 시작한다. 다만 글머리 앞에 설명 문단이 있으면 그 문단 아래 목록이라 ㅇ부터 시작한다.
    first_body = next((e for e in elements if e["kind"] in ("para", "item", "table", "note")), None)
    flat_base = 1 if first_body is not None and first_body["kind"] == "para" else 0
    base = 0
    indent_stack: list[int] = []
    offset = 0
    intro = not has_heading
    seen_heading = False
    box_used = False

    def add_para(marker: str, value: str) -> None:
        if value:
            blocks.append({"kind": "para", "marker": marker, "text": value, "level": marker})

    for index, e in enumerate(elements):
        kind = e["kind"]
        if kind == "heading":
            seen_heading = True
            base = e["rank"] + 1
            indent_stack, offset = [], 0
            if e["text"]:
                add_para(_marker(e["rank"]), e["text"])
            continue
        if kind == "table":
            blocks.append({"kind": "table", "rows": [row for row in e["rows"] if any(row)]})
            continue
        if kind == "note":
            add_para("※", e["text"])
            continue
        if kind == "para":
            nxt = _next_content(elements, index)
            if not seen_heading and not box_used and not title_text and not any(
                    x["kind"] == "item" for x in elements[:index]):
                blocks.append({"kind": "box", "text": e["text"]})
                box_used = True
                continue
            if not seen_heading and not box_used and title_text:
                blocks.append({"kind": "box", "text": e["text"]})
                box_used = True
                continue
            tier = (base if seen_heading else 1) + offset
            if e["text"].endswith((":", "：")) and nxt is not None and nxt["kind"] == "item":
                add_para(_marker(tier), e["text"])
                offset = max(offset, 0) + 1
                indent_stack = []
                continue
            offset = 0
            add_para(_marker(tier), e["text"])
            continue
        # 글머리·번호 항목: 서로 다른 들여쓰기의 순서로 깊이를 정한다.
        while indent_stack and indent_stack[-1] > e["indent"]:
            indent_stack.pop()
        if not indent_stack or indent_stack[-1] < e["indent"]:
            indent_stack.append(e["indent"])
        depth = len(indent_stack) - 1
        tier = (base if has_heading else flat_base) + offset + depth
        add_para(_marker(tier), e["text"])
    return blocks


def blocks_to_labeled_text(blocks: list[dict]) -> str:
    """블록을 라벨 형식(제목:/개요:/네모:/원:/바:/표:) 글로 만든다. 한/글 문서 만들기(라벨 입력 모드)가 이 글을 읽는다."""
    lines: list[str] = []
    for block in blocks:
        kind = block["kind"]
        if kind in ("title", "title1", "title2"):
            lines.append(f"제목: {block['text']}")
        elif kind == "box":
            lines.append(f"개요: {block['text']}")
        elif kind == "ref":
            lines.append(f"참고: {block['text']}")
        elif kind == "table":
            lines.extend("표: " + " | ".join(row) for row in block["rows"])
        elif kind == "para":
            label = _LABEL_BY_MARKER.get(block["marker"])
            lines.append(f"{label}: {block['text']}" if label else f"{block['marker']} {block['text']}")
    return "\n".join(lines).strip()


def blocks_to_plain_text(blocks: list[dict]) -> str:
    """블록을 한/글 문서에 그대로 넣을 개조식 글로 만든다(제목 줄, 개요 문단, □ ㅇ - • ※ 항목, 표는 ' | ' 줄)."""
    lines: list[str] = []
    for block in blocks:
        kind = block["kind"]
        if kind in ("title", "title1", "title2", "box", "ref"):
            lines.append(block["text"])
        elif kind == "table":
            lines.extend(" | ".join(row) for row in block["rows"])
        elif kind == "para":
            if block["marker"] == "□" and lines and lines[-1] != "":
                lines.append("")
            lines.append(f"{block['marker']} {block['text']}")
    return "\n".join(lines).strip()


def ai_answer_to_labeled_text(text: str) -> str:
    return blocks_to_labeled_text(parse_ai_answer(text))


def ai_answer_to_outline_text(text: str) -> str:
    return blocks_to_plain_text(parse_ai_answer(text))
