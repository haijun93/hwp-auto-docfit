"""Clean up text pasted from LLM chat windows (Gemini, Claude, ChatGPT, ...).

Chat UIs render Markdown, but copying that rendered text to the clipboard
often keeps the raw Markdown symbols (``**``, ``#``, ``-``, backticks, ...)
while losing the paragraph/list structure they were meant to describe:
sentences that were wrapped onto several lines run together, and list items
or headings end up glued to the sentence before them. ``clean_pasted_text``
turns that raw paste back into plain, readable paragraphs.
"""

from __future__ import annotations

import re

_INVISIBLE_MAP = str.maketrans({
    " ": " ",
    "​": "",
    "‌": "",
    "‍": "",
    "﻿": "",
})

_UNICODE_BULLETS = "•‣◦▪·∙"
_ASCII_BULLET = re.compile(r"^[-*+][ \t]+(?=\S)")
_UNICODE_BULLET = re.compile(rf"^[{_UNICODE_BULLETS}][ \t]*(?=\S)")
_NUMBERED_MARKER = re.compile(r"^(\d+[.)])(?:[ \t]+|(?=[^\d\s]))")
_CIRCLED_NUMBER = re.compile(r"^([①-⑳])[ \t]*(?=\S)")
_HEADING_MARKER = re.compile(r"^#{1,6}[ \t]+(?=\S)")
_BLOCKQUOTE_MARKER = re.compile(r"^(?:[ \t]*>[ \t]?)+")
_HR_LINE = re.compile(r"^([-*_=])(?:[ \t]*\1){2,}[ \t]*$")
_CODE_FENCE = re.compile(r"^```")
_TABLE_ROW = re.compile(r"^\|?.*\|.*\|?$")
_TABLE_SEPARATOR = re.compile(r"^\|?[ \t]*:?-{2,}:?[ \t]*(\|[ \t]*:?-{2,}:?[ \t]*)*\|?$")

_BOLD_ITALIC = re.compile(r"(\*\*\*|___)(?=\S)(.+?)(?<=\S)\1")
_BOLD = re.compile(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1")
_ITALIC = re.compile(r"(?<!\w)(\*|_)(?=[^\s*_])(.+?)(?<=[^\s*_])\1(?!\w)")
_STRIKE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~")
_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_CITATION_TAG = re.compile(r"【[^】]*】")
# 제미나이 등에서 각주 표시로 붙는 [1], [2][4] 같은 숫자 전용 대괄호.
# "[별표 21의2]"처럼 글자가 섞인 대괄호는 \d+로 걸리지 않아 그대로 남는다.
_CITATION_NUMBER = re.compile(r"[ \t]*(?:\[\d{1,4}\])+")
# 일부 채팅창은 강조 기호를 "\*\*text\*\*", "\~"처럼 백슬래시로 이스케이프한
# 채로 복사된다. 굵게/취소선 정규식은 이스케이프되지 않은 기호만 인식하므로,
# 다른 처리보다 먼저 백슬래시를 벗겨 일반 마크다운 기호로 되돌려 둔다.
_ESCAPED_MD_CHAR = re.compile(r"\\([\\`*_{}\[\]()#+\-.!~|>])")

_SENTENCE_END = r".!?…\"'”’」』"
_MARKER_GLUE = re.compile(
    rf"(?<=[{_SENTENCE_END}]) (?="
    rf"[-*+][ \t]|[{_UNICODE_BULLETS}]|\d+[.)](?:[ \t]|[^\d\s])|#{{1,6}}[ \t]|[①-⑳])"
)

# 계층 구조 변환(outline_pasted_text)에서 쓰는 문두기호. 1단계는 원문에
# 이미 "1." 같은 번호가 있으면 그대로 두고, 없을 때만 ㅁ을 붙인다.
_OUTLINE_TIER_MARKERS = ("ㅁ", "ㅇ", "-", "•")
_OUTLINE_ALREADY_NUMBERED = re.compile(r"^\d+[.)][ \t]")
_INDENTED_BULLET = re.compile(r"^([ \t]*)[-*+][ \t]+(?=\S)")
_UNINDENTED_NUMBER = re.compile(r"^\d+[.)][ \t]+(?=\S)")


def _strip_invisible(text: str) -> str:
    text = text.translate(_INVISIBLE_MAP)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return _ESCAPED_MD_CHAR.sub(r"\1", text)


def _strip_inline_markup(line: str) -> str:
    line = _CITATION_TAG.sub("", line)
    line = _CITATION_NUMBER.sub("", line)
    line = _INLINE_CODE.sub(r"\1", line)
    line = _IMAGE.sub(r"\1", line)
    line = _LINK.sub(r"\1", line)
    line = _BOLD_ITALIC.sub(r"\2", line)
    line = _BOLD.sub(r"\2", line)
    line = _ITALIC.sub(r"\2", line)
    line = _STRIKE.sub(r"\1", line)
    return line


def _structural_marker(line: str) -> tuple[str, str]:
    """Strip one block-level markdown marker. Returns (kind, cleaned_line)."""
    if _HR_LINE.match(line) or _TABLE_SEPARATOR.match(line):
        return "skip", ""
    line = _BLOCKQUOTE_MARKER.sub("", line)
    if _HEADING_MARKER.match(line):
        return "heading", _HEADING_MARKER.sub("", line).strip()
    if _ASCII_BULLET.match(line):
        rest = _ASCII_BULLET.sub("", line).strip()
        return ("list", f"- {rest}") if rest else ("skip", "")
    if _UNICODE_BULLET.match(line):
        rest = _UNICODE_BULLET.sub("", line).strip()
        return ("list", f"- {rest}") if rest else ("skip", "")
    match = _NUMBERED_MARKER.match(line)
    if match:
        rest = _NUMBERED_MARKER.sub("", line).strip()
        return ("list", f"{match.group(1)} {rest}") if rest else ("skip", "")
    match = _CIRCLED_NUMBER.match(line)
    if match:
        rest = _CIRCLED_NUMBER.sub("", line).strip()
        return ("list", f"{match.group(1)} {rest}") if rest else ("skip", "")
    if _TABLE_ROW.match(line):
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rest = "  ".join(cell for cell in cells if cell)
        return ("list", rest) if rest else ("skip", "")
    return "text", line


def clean_pasted_text(text: str) -> str:
    """Turn markdown-flavored chat output into plain, readable paragraphs.

    Headings, list items and quoted lines each become their own paragraph;
    ordinary sentences that were hard-wrapped across several lines are
    rejoined into a single flowing paragraph. Markdown emphasis, code
    fences/backticks, links, horizontal rules and table syntax are removed.
    """
    if not text or not text.strip():
        return ""

    text = _strip_invisible(text)
    text = _MARKER_GLUE.sub("\n", text)

    paragraphs: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            paragraphs.append(" ".join(current))
            current.clear()

    in_code_fence = False
    for raw_line in text.split("\n"):
        stripped = raw_line.strip()
        if _CODE_FENCE.match(stripped):
            in_code_fence = not in_code_fence
            flush()
            continue
        if in_code_fence:
            if stripped:
                flush()
                paragraphs.append(stripped)
            continue
        if not stripped:
            flush()
            continue
        kind, cleaned = _structural_marker(stripped)
        if kind == "skip":
            flush()
            continue
        cleaned = _strip_inline_markup(cleaned)
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
        if not cleaned:
            continue
        if kind in ("heading", "list"):
            flush()
            paragraphs.append(cleaned)
        else:
            current.append(cleaned)
    flush()

    return "\n\n".join(paragraphs).strip()


def _outline_bullet_tier(raw_line: str) -> int:
    """글머리 기호(``-``/``*``/``+``)의 들여쓰기 2칸당 한 단계씩 깊어진다.

    0칸(최상위 글머리)은 2단계(ㅇ), 2칸은 3단계(-), 4칸 이상은 모두
    4단계(•)로 묶는다 — 이 앱의 5단계 개조식 규칙(ㅁ→ㅇ→-→•)과 같다.
    """
    match = _INDENTED_BULLET.match(raw_line)
    depth = len(match.group(1).expandtabs(4)) // 2 if match else 0
    return min(depth + 1, len(_OUTLINE_TIER_MARKERS) - 1)


def outline_pasted_text(text: str) -> str:
    """마크다운 계층 구조를 ㅁ/ㅇ/-/• 개조식 문두기호로 바꾼다.

    표제(``#``~``######``, 또는 들여쓰기 없는 "1. " 숫자 항목)는 1단계로
    보고 이미 번호가 있으면 그대로 두며(없으면 ㅁ을 붙임), 글머리 기호는
    들여쓰기 깊이에 따라 ㅇ→-→•(3단계 이후는 모두 •) 순으로 매긴다. 줄바꿈
    으로 끊긴 같은 항목의 나머지 문장은 앞 항목에 이어 붙인다.
    """
    if not text or not text.strip():
        return ""

    text = _strip_invisible(text)
    text = _MARKER_GLUE.sub("\n", text)

    # 표제·글머리 기호는 (clean_pasted_text와 마찬가지로) 그 줄만으로 바로
    # 완결된 항목이 된다 — 다음 줄이 기호 없는 문장이라도 거기 이어붙이지
    # 않는다. 기호 없는 "text" 줄만 여러 줄에 걸쳐 하나로 이어 붙인다
    # (줄바꿈으로 끊긴 한 문장을 되살리는 이 기능 본연의 목적).
    items: list[tuple[int | None, str]] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            items.append((None, " ".join(current)))
            current.clear()

    in_code_fence = False
    for raw_line in text.split("\n"):
        stripped = raw_line.strip()
        if _CODE_FENCE.match(stripped):
            in_code_fence = not in_code_fence
            flush()
            continue
        if in_code_fence:
            if stripped:
                flush()
                items.append((None, stripped))
            continue
        if not stripped:
            flush()
            continue
        if _HR_LINE.match(stripped) or _TABLE_SEPARATOR.match(stripped):
            flush()
            continue
        no_quote = _BLOCKQUOTE_MARKER.sub("", stripped)
        if _HEADING_MARKER.match(no_quote):
            flush()
            items.append((0, _HEADING_MARKER.sub("", no_quote).strip()))
            continue
        if raw_line == stripped and _UNINDENTED_NUMBER.match(no_quote):
            # 들여쓰기 없는 숫자 항목만 1단계로 본다(들여쓰기가 있으면 하위
            # 순서 목록일 수 있어 글머리 기호와 똑같이 깊이로 판단한다).
            flush()
            items.append((0, no_quote))
            continue
        if _INDENTED_BULLET.match(raw_line):
            content = _INDENTED_BULLET.sub("", raw_line).strip()
            if content:
                flush()
                items.append((_outline_bullet_tier(raw_line), content))
            continue
        if _TABLE_ROW.match(no_quote):
            cells = [cell.strip() for cell in no_quote.strip("|").split("|")]
            content = "  ".join(cell for cell in cells if cell)
            if content:
                flush()
                items.append((1, content))
            continue
        current.append(no_quote)
    flush()

    rendered_lines: list[str] = []
    previous_tier: int | None = None
    for tier, raw_text in items:
        text_value = _strip_inline_markup(raw_text)
        text_value = re.sub(r"[ \t]{2,}", " ", text_value).strip()
        if not text_value:
            continue
        if tier is None:
            rendered = text_value
        elif tier == 0 and _OUTLINE_ALREADY_NUMBERED.match(text_value):
            rendered = text_value
        else:
            rendered = f"{_OUTLINE_TIER_MARKERS[tier]} {text_value}"
        if tier == 0 and previous_tier is not None and rendered_lines:
            rendered_lines.append("")
        rendered_lines.append(rendered)
        previous_tier = tier

    return "\n".join(rendered_lines).strip()
