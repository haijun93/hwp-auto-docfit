"""Pure, testable rules used by the HWP COM formatting pipeline."""

import re


YEAR_QUOTE_PATTERN = re.compile(r"['‘ʼ′`´](?=[0-9]{2}(?:년|\.[0-9]{1,2}(?![0-9])))")


def normalize_year_quotes(text):
    """Use U+2019 only before a two-digit year with 년 or a dotted month."""
    return YEAR_QUOTE_PATTERN.sub("’", text)


# 곧은 큰따옴표(")를 한글 표준 둥근따옴표(" ")로 통일할 때 쓰는 여는/닫는
# 판정 기준. 줄 시작이거나 공백·여는 괄호·여는 따옴표 뒤에 오면 여는
# 따옴표로, 그 밖(글자·숫자·마침표 등 뒤)에는 닫는 따옴표로 본다 —
# 일반적인 스마트 따옴표 규칙과 같다.
#
# 작은따옴표(')는 여기서 다루지 않는다. 발·분(6' 2") 표기나 영어
# 축약형(don't)과 진짜 인용부호를 안정적으로 구분할 방법이 없어,
# 잘못 바꾸면 오히려 문서를 망친다 — 연도 앞 표기(YEAR_QUOTE_PATTERN)처럼
# 문맥이 분명한 좁은 규칙만 다룬다.
_DOUBLE_QUOTE_OPENING_CONTEXT = frozenset(" \t\n　([{「『【‘“")


def straight_double_quote_replacements(text):
    """Return [(index, replacement_char), ...] for each straight " in text."""
    if not text or '"' not in text:
        return []
    replacements = []
    for index, ch in enumerate(text):
        if ch != '"':
            continue
        before = text[index - 1] if index > 0 else ""
        opening = before == "" or before in _DOUBLE_QUOTE_OPENING_CONTEXT
        replacements.append((index, "“" if opening else "”"))
    return replacements


def normalize_straight_double_quotes(text):
    """Turn straight double quotes into Korean curly quotes (" ")."""
    replacements = straight_double_quote_replacements(text)
    if not replacements:
        return text
    chars = list(text)
    for index, replacement in replacements:
        chars[index] = replacement
    return "".join(chars)


# 문두 기호(□/ㅇ/-/※ 등) 바로 뒤에 스페이스 대신 탭이나 전각공백이 온
# 경우도 표준 반각 공백 한 칸으로 통일 대상으로 본다.
_MARKER_SPACE_ALTERNATES = ("\t", "　", " ")


def marker_space_fix(text, marker_end):
    """Decide what's needed to normalize the space after a leading marker.

    Returns None if nothing to do (already exactly one regular space, or
    there is no room for one), "insert" if a space should simply be
    added, or "replace" if the following character is some other
    whitespace (tab, full-width space, NBSP) that should become a plain
    space instead of being left in place next to a newly inserted one.
    """
    if marker_end is None or marker_end >= len(text):
        return None
    next_char = text[marker_end]
    if next_char == " ":
        return None
    if next_char in _MARKER_SPACE_ALTERNATES:
        return "replace"
    return "insert"


LEVELS = ("box", "circle", "dash", "note")


def paragraph_level(text):
    stripped = (text or "").lstrip()
    if not stripped:
        return None
    marker = stripped[0]
    if marker == "□":
        return "box"
    if marker in ("ㅇ", "○", "☞"):
        return "circle"
    if marker == "-":
        return "dash"
    if marker in ("*", "※", "→", "•", "·", "‧", "∙", "⋅", "ㆍ", "●"):
        return "note"
    return None


class ParagraphSpacingTracker:
    """Keep one document's previous recognized level, without COM dependencies."""

    def __init__(self):
        self.previous = None

    def reset(self):
        self.previous = None

    def spacing_for(self, text, base_spacing, return_percent=150):
        if not 100 <= return_percent <= 400:
            raise ValueError("복귀배율은 100~400%여야 합니다.")
        level = paragraph_level(text)
        if level is None:
            return None
        previous = self.previous
        self.previous = level
        base = base_spacing.get(level)
        if base is None:
            return None
        if previous is not None and LEVELS.index(previous) > LEVELS.index(level):
            return round(base * return_percent / 100)
        return base
