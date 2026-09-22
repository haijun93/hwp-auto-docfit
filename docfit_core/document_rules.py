"""Pure, testable rules used by the HWP COM formatting pipeline."""

import re


YEAR_QUOTE_PATTERN = re.compile(r"['‘ʼ′`´](?=[0-9]{2}(?:년|\.[0-9]{1,2}(?![0-9])))")


def normalize_year_quotes(text):
    """Use U+2019 only before a two-digit year with 년 or a dotted month."""
    return YEAR_QUOTE_PATTERN.sub("’", text)


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
