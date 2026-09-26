"""Pure, conservative decisions used by document style unification.

This module deliberately contains no HWP/COM calls.  It keeps frequency-based
inference and protected inline ranges testable without opening or mutating a
user document.
"""

from __future__ import annotations

from collections import Counter


def representative(values, minimum=3, ratio=0.6):
    """Return (value, votes, sample_count), or (None, votes, count) if unsure."""
    usable = [value for value in values if value is not None]
    if len(usable) < minimum:
        return None, 0, len(usable)
    counts = Counter(usable)
    best_count = max(counts.values())
    winners = [value for value, count in counts.items() if count == best_count]
    if len(winners) != 1 or best_count / len(usable) < ratio:
        return None, best_count, len(usable)
    return winners[0], best_count, len(usable)


def parenthetical_spans(text, protected=()):
    """Find balanced inline parentheses, excluding an already classified label.

    Only outermost pairs are returned, so nested explanatory parentheses are
    treated as one semantic span and can never receive the size reduction twice.
    Offsets are Python character offsets; the HWP adapter converts them to UTF-16.
    """
    text = text or ""
    opening = {"(": ")", "（": "）"}
    closing = {value: key for key, value in opening.items()}
    stack = []
    pairs = []
    for index, char in enumerate(text):
        if char in "\r\n":
            stack.clear()
            continue
        if char in opening:
            if not stack:
                stack.append((index, opening[char]))
            else:
                stack.append((index, opening[char]))
        elif char in closing and stack:
            start, expected = stack[-1]
            if expected != char:
                stack.clear()
                continue
            stack.pop()
            if not stack:
                pairs.append((start, index + 1))

    protected = tuple(protected or ())
    sentence_end = set(".!?。！？…")
    connectors = set(",，、;；:：")
    closing_quotes = set(")]）}」』”’\"'")

    def is_mid_sentence(end):
        for char in text[end:]:
            if char.isspace():
                continue
            if char in sentence_end:
                return False
            if char in connectors or char in closing_quotes:
                continue
            return True
        return False

    return tuple((start, end) for start, end in pairs
                 if is_mid_sentence(end)
                 and not any(start < other_end and other_start < end
                             for other_start, other_end in protected))


def complement_ranges(start, end, excluded=()):
    """Return the portions of [start, end) not covered by excluded ranges."""
    clipped = sorted((max(start, left), min(end, right))
                     for left, right in excluded if right > start and left < end)
    result = []
    cursor = start
    for left, right in clipped:
        if right <= cursor:
            continue
        if left > cursor:
            result.append((cursor, left))
        cursor = max(cursor, right)
    if cursor < end:
        result.append((cursor, end))
    return tuple(result)


def merge_adjacent(ranges):
    """Merge overlapping or contiguous two-item ranges, preserving order."""
    result = []
    for start, end in sorted(ranges):
        if end <= start:
            continue
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return tuple(result)
