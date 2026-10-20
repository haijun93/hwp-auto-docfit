"""본문 항목기호의 문두 공백을 일괄 서식 규칙에 맞춰 검수·보정한다."""

from collections import Counter
from docfit_core.batch_format import apply_batch
from docfit_core.style_hierarchy import leading_marker


_PREFIX_CHARS = " \t\u00a0\u3000"
_ALIASES = {"ㅁ": "□", "○": "ㅇ", "◦": "ㅇ", "☞": "ㅇ"}


def expected_prefix(text, rules):
    """(기호, 현재 공백수, 목표 공백수). 항목기호가 아니면 None."""
    if not text:
        return None
    stripped = text.lstrip(_PREFIX_CHARS)
    if stripped.startswith("붙임") and (len(stripped) == 2 or stripped[2] in " :：\t"):
        return "붙임", len(text) - len(stripped), 0
    marker, role = leading_marker(stripped)
    if not role:
        return None
    key = _ALIASES.get(marker, marker)
    if marker == "**":
        key = "*"
    targets = {str(rule[0]): int(rule[1]) for rule in rules}
    if key not in targets:
        return None
    target = max(0, targets[key] - (1 if marker == "**" else 0))
    return marker, len(text) - len(stripped), target


def normalize_prefix(text, rules):
    info = expected_prefix(text, rules)
    if info is None:
        return text
    stripped = text.lstrip(_PREFIX_CHARS)
    return " " * info[2] + stripped


def audit_hwpx_prefixes(source, rules):
    """저장된 HWPX 본문의 항목기호 공백 수를 읽기 전용으로 검사한다."""
    measured = Counter()
    mismatches = []

    def plan(text, _paragraph):
        if text is None:
            return None
        info = expected_prefix(text, rules)
        if info is None:
            return None
        measured[info[0]] += 1
        if info[1] != info[2]:
            mismatches.append({"marker": info[0], "actual": info[1],
                               "expected": info[2], "text": text})
        return None

    apply_batch(source, None, plan)
    return {"measured": dict(measured), "mismatches": mismatches}
