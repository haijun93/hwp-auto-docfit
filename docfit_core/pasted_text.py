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

_SENTENCE_END = r".!?…\"'”’」』"
_MARKER_GLUE = re.compile(
    rf"(?<=[{_SENTENCE_END}]) (?="
    rf"[-*+][ \t]|[{_UNICODE_BULLETS}]|\d+[.)](?:[ \t]|[^\d\s])|#{{1,6}}[ \t]|[①-⑳])"
)


def _strip_invisible(text: str) -> str:
    text = text.translate(_INVISIBLE_MAP)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _strip_inline_markup(line: str) -> str:
    line = _CITATION_TAG.sub("", line)
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
