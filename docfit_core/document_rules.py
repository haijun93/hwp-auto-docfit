"""Pure, testable rules used by the HWP COM formatting pipeline."""

import difflib
import re


def text_edit_spans(original, transformed):
    """Return [(start, end, replacement), ...] turning original into transformed.

    Spans are index ranges in `original`'s coordinates and are safe to
    apply back-to-front (highest start first) without recomputing
    offsets in between, since only the changed regions are reported —
    everything else is left untouched.
    """
    if original == transformed:
        return []
    matcher = difflib.SequenceMatcher(a=original, b=transformed, autojunk=False)
    spans = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        spans.append((i1, i2, transformed[j1:j2]))
    return spans


YEAR_QUOTE_PATTERN = re.compile(r"['‘ʼ′`´](?=[0-9]{2}(?:년|\.[0-9]{1,2}(?![0-9])))")


def normalize_year_quotes(text):
    """Use U+2019 only before a two-digit year with 년 or a dotted month."""
    return YEAR_QUOTE_PATTERN.sub("’", text)


# 곧은 따옴표(", ')를 한글 표준 둥근따옴표(“ ”, ‘ ’)로 통일할 때 쓰는
# 여는/닫는 판정 기준. 줄 시작이거나 공백·여는 괄호·여는 따옴표 뒤에 오면
# 여는 따옴표로, 그 밖(글자·숫자·마침표 등 뒤)에는 닫는 따옴표로 본다 —
# 일반적인 스마트 따옴표 규칙과 같다.
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


def curly_single_quote_replacements(text):
    """Return [(index, replacement_char), ...] for each straight ' in text.

    A quote immediately preceded by a digit (6' as a feet/minute mark,
    37° 33' as a coordinate) is left alone — that's a unit mark, not a
    quotation, and there is no reliable way to tell it apart from a real
    one. Year-elision apostrophes ('26년) are handled separately by
    YEAR_QUOTE_PATTERN before this runs, so a plain ' that survives to
    here is judged as an ordinary quotation mark by the same
    open/close-by-context rule as the double-quote version above.
    """
    if not text or "'" not in text:
        return []
    replacements = []
    for index, ch in enumerate(text):
        if ch != "'":
            continue
        before = text[index - 1] if index > 0 else ""
        if before.isdigit():
            continue
        opening = before == "" or before in _DOUBLE_QUOTE_OPENING_CONTEXT
        replacements.append((index, "‘" if opening else "’"))
    return replacements


def normalize_curly_single_quotes(text):
    """Turn ordinary straight single quotes into Korean curly quotes (' ')."""
    replacements = curly_single_quote_replacements(text)
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


# 날짜·기간·시간 표기 부호 정리 -----------------------------------------------
#
# "2026. 3. 1 - 2026. 6. 30" 같은 표기에서 하이픈(-)·엔대시(–)·엠대시(—)를
# 물결표(~)로 바꾸고 날짜 뒤 빠진 온점을 채워 행정업무운영편람 표기 규칙에
# 맞춘다. 점(.)으로 연·월·일을 구분한 날짜 형태(\d{2,4}. \d{1,2}. \d{1,2})나
# 시:분(\d{1,2}:\d{2}) 형태 사이에 낀 대시류만 다루므로, 전화번호
# (02-123-4567)나 법령 조항(제4조-2), 사업 코드(IT-2026-01)처럼 점으로
# 구분되지 않는 하이픈은 애초에 패턴과 매치되지 않아 건드리지 않는다.
#
# 두 날짜가 같은 연도를 반복 표기한 경우(2026. 3. 1 - 2026. 6. 30에서 뒤쪽의
# "2026."을 생략해 "2026. 3. 1.~6. 30."으로 압축하는 것)는 자동으로 하지
# 않는다 — 두 날짜의 연도가 실제로 같은지까지 의미를 이해해야 하는 판단이라,
# 잘못 지우면 날짜 정보 자체가 사라지는 사고가 된다. 부호와 온점만 표준에
# 맞추고 내용은 그대로 둔다.
_DASH_CHARS = "-–—"  # 하이픈(-), 엔대시(–), 엠대시(—)
_DATE_CORE = r"\d{2,4}\.\s*\d{1,2}\.\s*\d{1,2}"  # 연.월.일, 온점 없이
_DATE_DOT = _DATE_CORE + r"\.?"  # 연.월.일, 끝 온점 있어도/없어도
_DATE_MONTH_DAY = r"\d{1,2}\.\s*\d{1,2}\.?"  # 월.일만 (기간 뒷부분용)
_TIME_HHMM = r"\d{1,2}:\d{2}"
_WEEKDAY_PAREN = r"\((?:월|화|수|목|금|토|일)\)"

_DATE_WEEKDAY_RE = re.compile(rf"({_DATE_CORE})\.?({_WEEKDAY_PAREN})\.?")
_DATE_TRAILING_DOT_RE = re.compile(rf"(?<!\d)({_DATE_CORE})(?!\.)(?!\d)")
_DATE_RANGE_SEP_RE = re.compile(
    rf"({_DATE_DOT})(\s*)[{_DASH_CHARS}](\s*)({_DATE_DOT}|{_DATE_MONTH_DAY})"
)
_TIME_RANGE_SEP_RE = re.compile(
    rf"({_TIME_HHMM})(\s*)[{_DASH_CHARS}](\s*)({_TIME_HHMM})"
)


def normalize_date_range_marks(text):
    """Standardize date/time range punctuation: dash-like chars -> ~,
    missing trailing dots after a dotted date, and dot placement around
    a following (요일) marker.
    """
    if not text:
        return text
    text = _DATE_WEEKDAY_RE.sub(lambda m: f"{m.group(1)}.{m.group(2)}", text)
    text = _DATE_TRAILING_DOT_RE.sub(lambda m: m.group(1) + ".", text)
    text = _DATE_RANGE_SEP_RE.sub(r"\1\2~\3\4", text)
    text = _TIME_RANGE_SEP_RE.sub(r"\1\2~\3\4", text)
    return text


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
