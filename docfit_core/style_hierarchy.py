"""Indentation-first logical structure analysis for copied HWPX styles."""

from collections import Counter, defaultdict
import re


# 문두에서 쓰인 점 계열 기호는 하나의 서식 항목으로 취급한다.
DOT_MARKERS = frozenset("•·‧∙⋅ㆍ●")


def canonical_marker(marker):
    return "•" if marker in DOT_MARKERS else marker


def normalize_leading_dot(text):
    """문장 안의 가운데점은 보존하고 문두의 점 계열 기호만 바꾼다."""
    match = re.match(r"(\s*)([•·‧∙⋅ㆍ●])(?=\s|$)", text or "")
    return text[:match.start(2)] + "•" + text[match.end(2):] if match else text


MARKERS = (
    ("중제목", r"(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+|[가-하])(?=\s|[.．])"),
    ("소제목", r"(?:[□ㅁ■]|\d{1,2}[.．]?)(?=\s|$)"),
    ("본문", r"(?:[ㅇ○◦☞]|[가-하]\))(?=\s|$)"),
    ("내용", r"(?:-|\d+\))(?=\s|$)"),
    ("부연설명", r"(?:\*\*?|※|[•·‧∙⋅ㆍ●]|\([가-하0-9]+\)[.．]?)(?=\s|$)"),
)
ROLE_ORDER = ("중제목", "소제목", "본문", "내용", "부연설명")
ROLE_LABELS = {"제목": "1단계", "중제목": "2단계", "소제목": "3단계",
               "본문": "4단계", "내용": "5단계", "부연설명": "부연설명"}
LABEL_ROLES = {label: role for role, label in ROLE_LABELS.items()}


def display_role(role):
    return ROLE_LABELS.get(role, role)


def stored_role(label):
    return LABEL_ROLES.get(label, label)
CIRCLED_MARKER = re.compile(r"[①-⑳㉠-㉻❶-❿➊-➓](?=\s|$)")
CIRCLED_ROLES = ("본문", "내용", "부연설명")


def leading_marker(text):
    stripped = (text or "").lstrip()
    circled = CIRCLED_MARKER.match(stripped)
    if circled:
        # 역할은 기호만으로 정할 수 없으므로 문서 내 서식과 문맥으로 판정한다.
        return circled.group(), ""
    for role, pattern in MARKERS:
        match = re.match(pattern, stripped)
        if match:
            return canonical_marker(match.group()), role
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
    for index, record in enumerate(records):
        role = record["marker_role"]
        if CIRCLED_MARKER.fullmatch(record["marker"]):
            candidates = []
            for name in CIRCLED_ROLES:
                value = role_indent[name]
                if value is None:
                    continue
                font, size = role_typography[name]
                distance = abs(record["indent_hwpunit"] - value)
                penalty = (0 if record.get("font") == font else 150)
                penalty += abs((record.get("size_pt") or 0) - (size or 0)) * 100
                candidates.append((distance, distance + penalty,
                                   CIRCLED_ROLES.index(name), name))
            if candidates:
                role = min(candidates)[3]
            else:
                previous = records[index - 1]["role"] if index else ""
                role = "본문" if previous == "소제목" else "내용" if previous in ("본문", "내용") else "부연설명" if previous == "부연설명" else "미분류"
        elif not role:
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
    variants = []
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
        signatures = Counter((item.get("font"), item.get("size_pt"),
                              item.get("left", 0), item.get("indent", 0),
                              item.get("prev_spacing")) for item in items)
        for (font, size, left, indent, prev), count in signatures.most_common():
            variants.append({"role": role, "marker": marker, "count": count,
                             "kind": "반복" if count > 1 else "비반복",
                             "font": font, "size_pt": size,
                             "left_hwpunit": left, "first_line_hwpunit": indent,
                             "prev_spacing_hwpunit": prev})
    warnings = []
    for index, record in enumerate(records):
        role = record["role"]
        if CIRCLED_MARKER.fullmatch(record["marker"]) and all(
                role_indent[name] is None for name in CIRCLED_ROLES):
            warnings.append(f"{index + 1}번째 원문자의 역할은 비교할 서식이 없어 확인이 필요합니다.")
        later = [item["role"] for item in records[index + 1:]]
        if role == "소제목":
            # 소제목 바로 뒤의 부연설명은 0개 이상 허용하되 본문은 필수다.
            following = next((name for name in later if name != "부연설명"), None)
            if following != "본문":
                warnings.append(f"{index + 1}번째 3단계 아래에 4단계가 없습니다.")
        if role == "내용" and not any(item["role"] == "본문" for item in records[:index]):
            warnings.append(f"{index + 1}번째 5단계에 앞선 4단계가 없습니다.")
        if role == "부연설명" and (index == 0 or records[index - 1]["role"] not in
                                 ("소제목", "본문", "내용", "부연설명")):
            warnings.append(f"{index + 1}번째 부연설명에 짝이 되는 앞 항목이 없습니다.")
    return {"version": 1, "priority": ["indentation", "font", "size", "marker"],
            "auxiliary": "prev_spacing", "indent_levels_hwpunit": indent_levels,
            "ambiguous_marker_roles": {"원문자": list(CIRCLED_ROLES)},
            "styles": summary,
            "variants": variants,
            "role_sequence": [r["role"] for r in records],
            "warnings": warnings,
            "page_policy": {"subheading_with_bodies": True,
                            "optional_explanations_after_subheading": True,
                            "body_with_contents": True,
                            "explanation_with_parent": True}}


def hierarchy_summary(analysis):
    lines = ["들여쓰기 → 글꼴 → 크기 → 문두기호 순으로 판정; 문단 위 여백은 보조값",
             "논리적 구조: 1단계 > 2단계 > 3단계 > 4단계 > 5단계; 부연설명은 관련 항목과 같은 쪽",
             "원문자(① 등)는 서식에 따라 4단계 ㅇ, 5단계 -, 부연설명 기호를 대신할 수 있음"]
    for item in analysis["styles"]:
        values = ", ".join(f"{n / 100:g}pt" for n in item["prev_spacing_values"]) or "없음"
        lines.append(f"{display_role(item['role'])} [{item['marker']}] {item['count']}개 | "
                     f"들여쓰기 {item['indent_hwpunit'] / 100:g}pt | "
                     f"{item['font'] or '미상'} {item['size_pt'] or 0:g}pt | "
                     f"문단 위 여백 {values}")
    if analysis.get("warnings"):
        lines.append("구조 확인 필요: " + "; ".join(analysis["warnings"][:10]))
    return "\n".join(lines)
