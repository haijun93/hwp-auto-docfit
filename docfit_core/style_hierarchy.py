"""Indentation-first logical structure analysis for copied HWPX styles."""

from collections import Counter, defaultdict
import re


MARKERS = (
    ("중제목", r"(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+|[가-하])(?=\s|[.．])"),
    ("소제목", r"(?:[□ㅁ■]|\d{1,2}[.．]?)(?=\s|$)"),
    ("본문", r"(?:[ㅇ○◦☞]|[가-하]\))(?=\s|$)"),
    ("내용", r"(?:-|\d+\))(?=\s|$)"),
    ("부연설명", r"(?:\*\*?|※|[•·∙]|\([가-하0-9]+\)[.．]?)(?=\s|$)"),
)
ROLE_ORDER = ("중제목", "소제목", "본문", "내용", "부연설명")


def leading_marker(text):
    stripped = (text or "").lstrip()
    for role, pattern in MARKERS:
        match = re.match(pattern, stripped)
        if match:
            return match.group(), role
    return "", ""


def _most_common(counter, default=None):
    return counter.most_common(1)[0][0] if counter else default


def analyze_hierarchy(paragraphs):
    """Infer roles from marker + indent + font + size; spacing is diagnostic only.

    Each input has text, left/indent in HWP units, font, size_pt and
    optional prev_spacing.  No pagination is inferred from XML alone.
    """
    records = []
    for item in paragraphs:
        marker, marker_role = leading_marker(item.get("text", ""))
        indent = int(item.get("left", 0)) + int(item.get("indent", 0))
        records.append({**item, "marker": marker, "marker_role": marker_role,
                        "indent_hwpunit": indent})
    marked = [r for r in records if r["marker_role"]]
    role_indent = {
        role: _most_common(Counter(r["indent_hwpunit"] for r in marked
                                   if r["marker_role"] == role))
        for role in ROLE_ORDER
    }
    role_typography = {
        role: _most_common(Counter((r.get("font"), r.get("size_pt"))
                                   for r in marked if r["marker_role"] == role))
        for role in ROLE_ORDER
    }
    indent_levels = sorted(set(r["indent_hwpunit"] for r in records))
    styles = defaultdict(list)
    for record in records:
        role = record["marker_role"]
        if not role:
            # Unmarked paragraphs use indentation before typography. A lone
            # large first line is a title, not an invented list item.
            nearest = []
            for name, value in role_indent.items():
                if value is None:
                    continue
                font, size = role_typography[name]
                distance = abs(record["indent_hwpunit"] - value)
                penalty = (0 if record.get("font") == font else 150)
                penalty += abs((record.get("size_pt") or 0) - (size or 0)) * 100
                nearest.append((distance, distance + penalty, ROLE_ORDER.index(name), name))
            if nearest and min(nearest)[0] <= 100:
                role = min(nearest)[3]
            elif record is records[0] and record.get("size_pt", 0) > 0:
                sizes = [r.get("size_pt", 0) for r in records[1:] if r.get("size_pt", 0) > 0]
                role = "제목" if sizes and record["size_pt"] > max(sizes) else "미분류"
            else:
                role = "미분류"
        record["role"] = role
        key = (role, record["marker"] or "(없음)")
        styles[key].append(record)
    summary = []
    for (role, marker), items in sorted(styles.items(), key=lambda kv:
                                       (ROLE_ORDER.index(kv[0][0]) if kv[0][0] in ROLE_ORDER else 9,
                                        min(records.index(item) for item in kv[1]))):
        primary = _most_common(Counter((x.get("font"), x.get("size_pt"),
                                        x["indent_hwpunit"], x.get("left", 0),
                                        x.get("indent", 0)) for x in items))
        spaces = Counter(x.get("prev_spacing") for x in items
                         if x.get("prev_spacing") is not None)
        summary.append({"role": role, "marker": marker, "count": len(items),
                        "font": primary[0], "size_pt": primary[1],
                        "indent_hwpunit": primary[2],
                        "left_hwpunit": primary[3], "first_line_hwpunit": primary[4],
                        "prev_spacing_values": sorted(spaces),
                        "prev_spacing_typical": _most_common(spaces)})
    warnings = []
    for index, record in enumerate(records):
        role = record["role"]
        later = [item["role"] for item in records[index + 1:]]
        if role == "소제목" and (not later or later[0] != "본문"):
            warnings.append(f"{index + 1}번째 소제목 바로 뒤에 본문이 없습니다.")
        if role == "내용" and not any(item["role"] == "본문" for item in records[:index]):
            warnings.append(f"{index + 1}번째 내용에 앞선 본문이 없습니다.")
        if role == "부연설명" and (index == 0 or records[index - 1]["role"] not in
                                 ("소제목", "본문", "내용", "부연설명")):
            warnings.append(f"{index + 1}번째 부연설명에 짝이 되는 앞 항목이 없습니다.")
    return {"version": 1, "priority": ["indentation", "font", "size", "marker"],
            "auxiliary": "prev_spacing", "indent_levels_hwpunit": indent_levels,
            "styles": summary,
            "role_sequence": [r["role"] for r in records],
            "warnings": warnings,
            "page_policy": {"subheading_with_bodies": True,
                            "body_with_contents": True,
                            "explanation_with_parent": True}}


def hierarchy_summary(analysis):
    lines = ["들여쓰기 → 글꼴 → 크기 → 문두기호 순으로 판정; 문단 위 여백은 보조값",
             "논리적 구조: 중제목 > 소제목 > 본문 > 내용; 부연설명은 직전 항목과 같은 쪽"]
    for item in analysis["styles"]:
        values = ", ".join(f"{n / 100:g}pt" for n in item["prev_spacing_values"]) or "없음"
        lines.append(f"{item['role']} [{item['marker']}] {item['count']}개 | "
                     f"들여쓰기 {item['indent_hwpunit'] / 100:g}pt | "
                     f"{item['font'] or '미상'} {item['size_pt'] or 0:g}pt | "
                     f"문단 위 여백 {values}")
    if analysis.get("warnings"):
        lines.append("구조 확인 필요: " + "; ".join(analysis["warnings"][:10]))
    return "\n".join(lines)
