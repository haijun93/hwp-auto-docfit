"""Pure, conservative decisions used by document style unification.

This module deliberately contains no HWP/COM calls.  It keeps frequency-based
inference and protected inline ranges testable without opening or mutating a
user document.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from docfit_core.style_hierarchy import leading_marker


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


def parenthetical_spans(text, protected=(), include_trailing=False):
    """Find balanced inline parentheses, excluding an already classified label.

    include_trailing=True also returns parentheses that end the sentence, e.g.
    '전기버스 4대(※차량원복시 23인승)', which follow the same -2pt rule.

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
                 if (include_trailing or is_mid_sentence(end))
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


# ---- 문서 체계(계층) 판별 -------------------------------------------------
# 번호가 매겨진 문두기호는 번호마다 따로 묶으면 표본이 하나씩밖에 없다. 같은 계열은
# 하나의 그룹 기호로 모은다(예: '1.' '2.' '12.' → '1.', 'Ⅰ' 'Ⅱ' → 'Ⅰ').
_CLASS_PATTERNS = (
    (re.compile(r"\d{1,2}[.．]?"), "1."),
    (re.compile(r"\d+\)"), "1)"),
    (re.compile(r"\(\d+\)[.．]?"), "(1)"),
    (re.compile(r"[가-하][.．]?"), "가."),
    (re.compile(r"[가-하]\)"), "가)"),
    (re.compile(r"\([가-하]\)[.．]?"), "(가)"),
    (re.compile(r"[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.．]?"), "Ⅰ"),
    (re.compile(r"[①-⑳]"), "①"),
    (re.compile(r"[㉠-㉻]"), "㉠"),
    (re.compile(r"[❶-❿]"), "❶"),
    (re.compile(r"[➊-➓]"), "➊"),
)
# 한/글이 원문자 번호(󰊱 󰊲 …)를 사용자 정의 영역(PUA) 글자로 저장하는 경우가 있다.
_PUA_CIRCLED = re.compile(r"[\U000F02B1-\U000F02C4]")
# '1.「마포 교육의 달」'처럼 번호 뒤 공백 없이 제목이 붙은 경우. '1.5배'처럼 숫자가
# 이어지면 소수이므로 번호로 보지 않는다.
_TIGHT_NUMBER = re.compile(r"\d{1,2}[.．](?=[^\d\s.．,，])")
_EXTRA_DOTS = frozenset("・")


def marker_class(marker):
    """문두기호를 번호와 무관한 그룹 기호로 바꾼다."""
    if not marker:
        return ""
    if _PUA_CIRCLED.fullmatch(marker):
        return "\U000F02B1"
    for pattern, name in _CLASS_PATTERNS:
        if pattern.fullmatch(marker):
            return name
    return marker


def unify_marker(text):
    """서식통일용 (그룹 기호, 역할, 실제 기호). 문두기호가 없으면 ('', '', '')."""
    stripped = (text or "").lstrip(" \t\u00a0\u3000")
    marker, role = leading_marker(stripped)
    if not marker:
        if stripped[:1] and _PUA_CIRCLED.match(stripped):
            marker, role = stripped[0], "중제목"
        elif stripped[:1] in _EXTRA_DOTS:
            marker, role = "•", "부연설명"
        else:
            tight = _TIGHT_NUMBER.match(stripped)
            if tight:
                marker, role = tight.group(), "소제목"
    if not marker:
        return "", "", ""
    return marker_class(marker), role or "원문자", marker


def hierarchy_levels(sequence):
    """문서 순서로 나열한 그룹 기호에서 바깥 → 안쪽 계층 순서를 추정한다.

    처음 나온 기호는 바로 앞 기호의 하위로 쌓고, 이미 쌓인 기호가 다시 나오면
    그 단계로 돌아간다. 깊이만 세면 □가 장 제목 바로 아래와 '1.' 아래에 모두 나올 때
    순서가 뒤집히므로, 두 기호 가운데 어느 쪽이 상위로 더 자주 놓였는지를 센다.
    """
    stack, first = [], {}
    ancestors = Counter()
    for index, key in enumerate(sequence):
        if not key:
            continue
        first.setdefault(key, index)
        if key in stack:
            del stack[stack.index(key) + 1:]
        else:
            stack.append(key)
        for upper in stack[:-1]:
            ancestors[(upper, key)] += 1

    def rank(key):
        return sum(1 for other in first
                   if other != key and ancestors[(other, key)] > ancestors[(key, other)])

    return sorted(first, key=lambda key: (rank(key), first[key]))


# 붙임·별첨 등 본문과 다른 서식 체계를 쓸 수 있는 구역의 제목. '참고'는 번호나 괄호가
# 있을 때만 구역 제목으로 본다('※ 참고' 같은 문장 속 표현과 구분).
_ATTACHMENT_HEADING = re.compile(
    r"\s*(?:[\[<〈【(]\s*(?:붙임|별첨|첨부|참고)\s*\d*\s*[\]>〉】)]"
    r"|(?:붙임|별첨|첨부)(?:\s*\d+)?(?=\s|$|[.．:：])"
    r"|참고\s*\d+(?=\s|$|[.．:：]))")


def attachment_heading(text):
    """붙임·별첨 구역 제목이면 짧은 이름('붙임 2' 등), 아니면 ''."""
    text = str(text or "")
    match = _ATTACHMENT_HEADING.match(text)
    if not match or len(text.strip()) > 60:
        return ""
    return re.sub(r"[\[\]<>〈〉【】()\s]+", " ", match.group()).strip()


def style_change_points(sequences, *, minimum=5, share=0.2, purity=0.9, agree=2):
    """여러 계층이 같은 곳에서 함께 서식을 바꾸는 지점(새 서식 체계가 시작하는 문단 번호).

    sequences: {계층: [(문단 번호, 서식값), ...]}. 계층마다 앞뒤가 각각 minimum개 이상이면서
    그 계층 문장의 share 이상이고, purity 이상 한 값으로 일관되게 갈리는 가장 뚜렷한 지점을
    찾는다. agree개 이상의 계층이 겹치는 구간에서 바뀔 때만 체계 경계로 본다. 몇 문장만,
    또는 취합 문서의 한 부서 구간처럼 작은 부분만 다른 서식이면 경계가 아니라 예외로 남아
    통일된다. 경계로 나뉜 구간 안에서 다시 찾는다(체계가 셋 이상인 경우).
    """
    def best_cut(seq):
        n = len(seq)
        side = max(minimum, math.ceil(n * share))
        if n < side * 2:
            return None
        left, right = Counter(), Counter(value for _, value in seq)
        best = None
        for cut in range(1, n):
            value = seq[cut - 1][1]
            left[value] += 1
            right[value] -= 1
            if cut < side or n - cut < side:
                continue
            lv, lc = left.most_common(1)[0]
            rv, rc = right.most_common(1)[0]
            if lv == rv or lc / cut < purity or rc / (n - cut) < purity:
                continue
            score = lc / cut + rc / (n - cut)
            if best is None or score > best[0]:
                best = (score, seq[cut - 1][0], seq[cut][0])
        return best and best[1:]

    def split(lo, hi, depth):
        if depth > 4:
            return []
        cuts = []
        for seq in sequences.values():
            part = sorted(item for item in seq if lo <= item[0] < hi and item[1] is not None)
            cut = best_cut(part)
            if cut:
                cuts.append(cut)
        found = None
        for last, first in cuts:
            overlap = [c for c in cuts if c[0] < first and last < c[1]]
            if len(overlap) >= agree:
                point = max(c[0] for c in overlap) + 1
                if found is None or point < found:
                    found = point
        if found is None:
            return []
        return split(lo, found, depth + 1) + [found] + split(found, hi, depth + 1)

    return split(float("-inf"), float("inf"), 0)


def looks_like_cover(items, body_size, *, ratio=1.3, minimum=1800):
    """첫 쪽이 표지인지 판정한다.

    items: (글자, 가장 큰 글자 크기 HWPUNIT, 가운데 정렬 여부, 본문형 문장 여부).
    가장 큰 글자가 본문 대표 크기보다 확연히 크고(1.3배, 최소 18pt) 가운데 정렬이며,
    첫 쪽 글자 대부분이 본문형(ㅇ·- 등) 문장이 아니면 표지로 본다.
    """
    texts = [item for item in items if str(item[0]).strip()]
    if not texts or not body_size:
        return False
    largest = max(texts, key=lambda item: item[1] or 0)
    if (largest[1] or 0) < max(minimum, body_size * ratio) or not largest[2]:
        return False
    total = sum(len(str(item[0]).strip()) for item in texts)
    body_like = sum(len(str(item[0]).strip()) for item in texts if item[3])
    return body_like / total < 0.5


def vocabulary_fallback(values, vocabulary, *, share=0.4, minimum=3):
    """엄격한 다수 기준을 넘지 못한 값 가운데, 문서의 다른 계층이 대표로 쓰는 값이
    유일한 최다값이면 그 값을 돌려준다. 근거가 없으면 None.
    """
    usable = [value for value in values if value is not None]
    if len(usable) < minimum:
        return None
    counts = Counter(usable).most_common()
    best, votes = counts[0]
    if len(counts) > 1 and counts[1][1] == votes:
        return None
    if votes / len(usable) < share or best not in vocabulary:
        return None
    return best


def dominant(weighted, *, ratio=0.6):
    """(값, 길이) 목록에서 길이 기준 ratio 이상을 차지하는 값. 없으면 None."""
    counts = Counter()
    for value, length in weighted:
        counts[value] += max(0, int(length))
    total = sum(counts.values())
    if not total:
        return None
    value, amount = counts.most_common(1)[0]
    return value if amount / total >= ratio else None
