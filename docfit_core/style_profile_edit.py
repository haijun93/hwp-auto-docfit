"""Validate reviewed hierarchy styles and synchronize them with copy rules."""

from copy import deepcopy
from collections import Counter


FIELDS = ("font", "size", "indent", "spacing")
ROLES = ("제목", "중제목", "소제목", "본문", "내용", "부연설명", "미분류")


def apply_reviewed_styles(profile, rows):
    """Return a new profile; invalid edits never mutate the saved original."""
    updated = deepcopy(profile)
    hierarchy = updated.setdefault("style_hierarchy", {})
    original = hierarchy.get("variants", [])
    if len(rows) != len(original):
        raise ValueError("분석된 스타일 항목 수가 일치하지 않습니다.")
    cleaned = []
    for index, (source, row) in enumerate(zip(original, rows), 1):
        item = deepcopy(source)
        role = row.get("role")
        if role not in ROLES:
            raise ValueError(f"{index}번째 스타일의 계층 역할이 올바르지 않습니다.")
        font = str(row.get("font") or "").strip()
        if len(font) > 100:
            raise ValueError(f"{index}번째 글꼴 이름이 너무 깁니다.")
        try:
            size = float(row.get("size_pt"))
            left = int(round(float(row.get("left_hwpunit"))))
            indent = int(round(float(row.get("first_line_hwpunit"))))
            spacing = int(round(float(row.get("prev_spacing_hwpunit"))))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{index}번째 스타일의 숫자값을 확인해 주세요.") from exc
        if not 0 < size <= 1000 or any(abs(value) > 1_000_000 for value in (left, indent, spacing)) or spacing < 0:
            raise ValueError(f"{index}번째 스타일의 크기·여백 값이 범위를 벗어났습니다.")
        selected = {field: bool(row.get("apply", {}).get(field, True)) for field in FIELDS}
        item.update(role=role, font=font, size_pt=size, left_hwpunit=left,
                    first_line_hwpunit=indent, prev_spacing_hwpunit=spacing,
                    apply=selected)
        cleaned.append(item)
    hierarchy["variants"] = cleaned
    grouped = {}
    for item in cleaned:
        grouped.setdefault((item["role"], item["marker"]), []).append(item)
    hierarchy["styles"] = []
    for (role, marker), variants in grouped.items():
        primary = max(variants, key=lambda value: value["count"])
        spaces = Counter()
        for value in variants:
            spaces[value["prev_spacing_hwpunit"]] += value["count"]
        hierarchy["styles"].append({
            "role": role, "marker": marker,
            "count": sum(value["count"] for value in variants),
            "font": primary["font"], "size_pt": primary["size_pt"],
            "indent_hwpunit": primary["left_hwpunit"] + primary["first_line_hwpunit"],
            "left_hwpunit": primary["left_hwpunit"],
            "first_line_hwpunit": primary["first_line_hwpunit"],
            "prev_spacing_values": sorted(spaces),
            "prev_spacing_typical": spaces.most_common(1)[0][0],
        })
    hierarchy["reviewed"] = True
    fmt = updated["format"]
    fmt["스타일_속성선택"] = {}
    fmt["논리역할_규칙"] = {}
    fmt["문두기호_역할"] = {}
    # A marker can appear with several visual variants. The most frequent
    # reviewed variant is the deterministic application rule for that marker.
    chosen = {}
    for item in sorted(cleaned, key=lambda value: value["count"], reverse=True):
        marker = item["marker"]
        if marker != "(없음)" and item["role"] != "미분류":
            chosen.setdefault(marker, item)
    rules = {rule[0]: list(rule) for rule in fmt["기호_규칙"]}
    paragraph_shapes = fmt.setdefault("복사_문단모양", {})
    for marker, item in chosen.items():
        old = rules.get(marker, [marker, 0, item["font"], item["size_pt"], False, False])
        old[2], old[3] = item["font"], item["size_pt"]
        rules[marker] = old
        fmt["스타일_속성선택"][marker] = item["apply"]
        fmt["문두기호_역할"][marker] = item["role"]
        paragraph_shapes[marker] = {
            **paragraph_shapes.get(marker, {}),
            "LeftMargin": item["left_hwpunit"],
            "Indentation": item["first_line_hwpunit"],
            "PrevSpacing": item["prev_spacing_hwpunit"],
        }
        fmt["논리역할_규칙"].setdefault(item["role"], old)
        if marker in ("□", "ㅇ", "-", "※", "·", "•", "∙"):
            updated.setdefault("options", {}).setdefault("symbol_fonts", {})[marker] = {
                "font": item["font"], "size": f"{item['size_pt']:g}"}
    fmt["기호_규칙"] = list(rules.values())
    title = next((item for item in cleaned if item["role"] == "제목"), None)
    if title:
        fmt["제목_문단"].update(font=title["font"], size_pt=title["size_pt"])
        fmt["스타일_속성선택"]["(제목)"] = title["apply"]
        paragraph_shapes["(제목)"] = {
            "LeftMargin": title["left_hwpunit"],
            "Indentation": title["first_line_hwpunit"],
            "PrevSpacing": title["prev_spacing_hwpunit"],
        }
    return updated
