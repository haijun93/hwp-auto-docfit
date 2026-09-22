"""Local, read-only review of Korean report structure and visual consistency."""

from collections import Counter, defaultdict
from pathlib import Path
import re
from zipfile import ZipFile

from defusedxml.ElementTree import fromstring

from .hwpx import validate_hwpx
from .style_hierarchy import analyze_hierarchy, canonical_marker, display_role, leading_marker


PURPOSES = ("빠른 의사결정용", "상세 설명용")
DOCUMENT_KINDS = ("보고서", "계획서", "기안문")
PURPOSE_CHECKLIST = {
    ("보고서", "빠른 의사결정용"): "첫머리에서 판단할 사안과 결론을 파악할 수 있는지 확인하세요.",
    ("계획서", "빠른 의사결정용"): "첫머리에서 목표·핵심 실행 방안·일정을 파악할 수 있는지 확인하세요.",
    ("기안문", "빠른 의사결정용"): "첫머리에서 요청 사항과 결재가 필요한 내용을 파악할 수 있는지 확인하세요.",
}
FIELDS = ("font", "size_pt", "bold", "color", "left", "indent", "prev_spacing", "align")
FIELD_NAMES = {"font": "글꼴", "size_pt": "글자 크기", "bold": "굵기", "color": "글자색",
               "left": "왼쪽 여백", "indent": "첫 줄 들여쓰기", "prev_spacing": "문단 위 여백",
               "align": "줄 맞춤"}
_JUDGMENT = re.compile(r"(?:추진\s*검토|검토\s*고려|도입\s*추진\s*검토)")
_NOMINAL_END = re.compile(r"(?:추진|검토|실시|확대|개선)(?:\s*예정)?[.。]?$")
_SUBJECT = re.compile(r"[가-힣A-Za-z0-9]{1,20}(?:은|는|이|가)\s")
_SECTION = re.compile(r"Contents/section(\d+)\.xml$")


def _local(element):
    return element.tag.rsplit("}", 1)[-1]


def _child(element, name):
    return next((item for item in element if _local(item) == name), None) if element is not None else None


def _hwpunit(parent, name):
    node = _child(parent, name)
    if node is None or node.get("unit", "HWPUNIT") != "HWPUNIT":
        return None
    try:
        return int(node.get("value", "0"))
    except ValueError:
        return None


def _paragraph(para, fonts, chars, shapes, section, number, table=None):
    runs = []
    for run in para:
        if _local(run) != "run":
            continue
        text = "".join("".join(node.itertext()) for node in run if _local(node) == "t")
        if text:
            runs.append((run, text))
    text = "".join(value for _, value in runs).strip()
    if not text:
        return None
    # Prefer the longest run so a short emphasized label does not define the whole paragraph.
    run = max(runs, key=lambda item: len(item[1]))[0]
    char = chars.get(run.get("charPrIDRef"))
    shape = shapes.get(para.get("paraPrIDRef"))
    font_ref = _child(char, "fontRef")
    margin = _child(shape, "margin")
    align = _child(shape, "align")
    marker, marker_role = leading_marker(text)
    result = {"section": section, "number": number, "location": f"{section}구역 본문 {number}번",
              "text": text, "marker": marker, "marker_role": marker_role,
              "table": table, "font": fonts.get(font_ref.get("hangul")) if font_ref is not None else None,
              "size_pt": None, "bold": _child(char, "bold") is not None if char is not None else None,
              "color": char.get("textColor") if char is not None else None,
              "left": _hwpunit(margin, "left"), "indent": _hwpunit(margin, "intent"),
              "prev_spacing": _hwpunit(margin, "prev"),
              "align": align.get("horizontal") if align is not None else None}
    if char is not None:
        try:
            result["size_pt"] = float(char.get("height", "0")) / 100
        except ValueError:
            pass
    if table is not None:
        result["location"] = f"{section}구역 표 {table['index']} / {table['row'] + 1}행 {table['col'] + 1}열"
        result["role"] = "표 머리글" if table["row"] == 0 else "표 본문"
    return result


def extract_review_paragraphs(path):
    """Extract ordered body and cell paragraphs; never modify the HWPX archive."""
    validate_hwpx(path)
    body, cells = [], []
    with ZipFile(path) as archive:
        header = fromstring(archive.read("Contents/header.xml"))
        fonts = {}
        for group in header.iter():
            if _local(group) == "fontface" and group.get("lang") == "HANGUL":
                fonts.update({item.get("id"): item.get("face") for item in group if _local(item) == "font"})
        chars = {item.get("id"): item for item in header.iter() if _local(item) == "charPr"}
        shapes = {item.get("id"): item for item in header.iter() if _local(item) == "paraPr"}
        sections = sorted((name for name in archive.namelist() if _SECTION.fullmatch(name)),
                          key=lambda name: int(_SECTION.fullmatch(name).group(1)))
        table_index = 0
        for section_number, name in enumerate(sections, 1):
            root = fromstring(archive.read(name))
            paragraph_number = 0
            for item in root:
                if _local(item) != "p":
                    continue
                paragraph_number += 1
                paragraph = _paragraph(item, fonts, chars, shapes, section_number, paragraph_number)
                if paragraph:
                    body.append(paragraph)
                for table in (node for node in item.iter() if _local(node) == "tbl"):
                    table_index += 1
                    for row_index, row in enumerate(node for node in table if _local(node) == "tr"):
                        for col_index, cell in enumerate(node for node in row if _local(node) == "tc"):
                            context = {"index": table_index, "row": row_index, "col": col_index}
                            for para in (node for node in cell.iter() if _local(node) == "p"):
                                found = _paragraph(para, fonts, chars, shapes, section_number,
                                                   paragraph_number, context)
                                if found:
                                    cells.append(found)
    if body:
        hierarchy = analyze_hierarchy([{"text": item["text"], "font": item["font"],
                                        "size_pt": item["size_pt"], "left": item["left"] or 0,
                                        "indent": item["indent"] or 0,
                                        "prev_spacing": item["prev_spacing"]} for item in body])
        for item, role in zip(body, hierarchy["role_sequence"]):
            item["role"] = role
    return body, cells


def _issue(severity, category, item, message):
    return {"severity": severity, "category": category, "location": item["location"],
            "message": message, "context": item["text"][:180]}


def _structure_issues(body):
    issues = []
    for section in sorted({item["section"] for item in body}):
        items = [item for item in body if item["section"] == section]
        markers = defaultdict(dict)
        for item in items:
            role, marker = item["role"], item["marker"]
            if role in ("중제목", "소제목", "본문", "내용") and marker:
                markers[role].setdefault(marker, item)
        for role, entries in markers.items():
            if len(entries) > 1:
                marker_list = ", ".join(entries)
                issues.append(_issue("확인 필요", "계층 기호 혼용", list(entries.values())[1],
                                      f"같은 {display_role(role)}에 {marker_list} 기호가 사용됩니다. 의도한 구분인지 확인하세요."))
        has_subheading = any(item["role"] == "소제목" for item in items)
        seen_subheading = seen_body = False
        for item in items:
            role = item["role"]
            if role == "소제목":
                seen_subheading, seen_body = True, False
            elif role == "본문":
                if has_subheading and not seen_subheading:
                    issues.append(_issue("확인 필요", "상위 항목 확인", item,
                                          "3단계보다 앞에 4단계 항목이 있습니다. 독립 항목인지 확인하세요."))
                seen_body = True
            elif role == "내용" and not seen_body:
                issues.append(_issue("확인 필요", "상위 항목 확인", item,
                                      "앞에 연결할 4단계 항목이 보이지 않습니다."))
        for index, item in enumerate(items):
            if item["role"] != "소제목":
                continue
            following = []
            for later in items[index + 1:]:
                if later["role"] in ("제목", "중제목", "소제목"):
                    break
                following.append(later)
            if not any(later["role"] == "본문" for later in following):
                issues.append(_issue("확인 필요", "하위 내용 확인", item,
                                      "다음 상위 단계 전까지 4단계 항목이 보이지 않습니다. 표·그림으로 설명했는지 확인하세요."))
    return issues


def _reference(profile, role, marker):
    if not profile:
        return None
    for style in profile.get("style_hierarchy", {}).get("styles", []):
        if style.get("role") == role and canonical_marker(style.get("marker")) == marker:
            reference = {"font": style.get("font"), "size_pt": style.get("size_pt"),
                    "left": style.get("left_hwpunit"), "indent": style.get("first_line_hwpunit"),
                    "prev_spacing": style.get("prev_spacing_typical")}
            selected = profile.get("format", {}).get("스타일_속성선택", {}).get(marker, {})
            for key, option in (("font", "font"), ("size_pt", "size"),
                                ("left", "indent"), ("indent", "indent"),
                                ("prev_spacing", "spacing")):
                if selected.get(option) is False:
                    reference[key] = None
            return reference
    fmt = profile.get("format", {})
    if role == "제목" and fmt.get("제목_문단"):
        title = fmt["제목_문단"]
        return {"font": title.get("font"), "size_pt": title.get("size_pt"), "bold": title.get("bold")}
    for rule in fmt.get("기호_규칙", []):
        if canonical_marker(rule[0]) == marker:
            return {"font": rule[2], "size_pt": rule[3], "bold": rule[4]}
    return None


def _visual_issues(body, cells, profile):
    issues = []
    groups = defaultdict(list)
    for item in body:
        groups[("body", item["role"], item["marker"])].append(item)
    for item in cells:
        table = item["table"]
        groups[("cell", table["index"], item["role"], table["col"])].append(item)
    for key, items in groups.items():
        reference = _reference(profile, key[1], key[2]) if key[0] == "body" else None
        if len(items) < 3 and not reference:
            continue
        for field in FIELDS:
            # No HWPX shape available: avoid inventing a mismatch.
            values = Counter(item[field] for item in items if item[field] is not None)
            baseline = reference.get(field) if reference else None
            if baseline is None:
                baseline, count = values.most_common(1)[0] if values else (None, 0)
                if count < 2:
                    continue
            deviations = [item for item in items
                          if baseline is not None and item[field] is not None and item[field] != baseline]
            if deviations:
                observed = Counter(str(item[field]) for item in deviations)
                values = ", ".join(f"{value}({count})" for value, count in observed.most_common(3))
                issues.append(_issue("확인 필요", "서식 편차", deviations[0],
                                     f"{FIELD_NAMES[field]}: 기준 {baseline}, 다른 값 {values}. "
                                     f"같은 역할의 문단 {len(deviations)}개를 확인하세요."))
    ordinary = [item for item in body if item["role"] not in ("제목", "중제목", "소제목")]
    if len(ordinary) >= 4:
        bold = [item for item in ordinary if item["bold"] is True]
        if len(bold) / len(ordinary) >= 0.6:
            issues.append(_issue("선호 제안", "강조 밀도 확인", bold[0],
                                  "4·5단계와 부연설명의 굵은 글씨 비율이 높습니다. 강조할 핵심이 구분되는지 확인하세요."))
    return issues


def _expression_issues(body):
    issues = []
    for item in body:
        text = item["text"]
        if _JUDGMENT.search(text):
            issues.append(_issue("선호 제안", "표현 명료성", item,
                                 "판단·행위 단계가 겹쳐 보입니다. 실제 결정 수준을 확인하세요."))
        elif len(text) >= 35 and _NOMINAL_END.search(text) and not _SUBJECT.search(text):
            issues.append(_issue("선호 제안", "행위 주체 확인", item,
                                 "행위 주체가 명시되어야 하는 문맥인지 확인하세요. 개조식에서는 생략이 자연스러울 수 있습니다."))
    return issues


def review_document(path, profile=None, purpose="상세 설명용", document_kind="보고서"):
    """Return evidence-based suggestions, not automatic edits or semantic verdicts."""
    if purpose not in PURPOSES or document_kind not in DOCUMENT_KINDS:
        raise ValueError("지원하지 않는 문서 검토 설정입니다.")
    body, cells = extract_review_paragraphs(Path(path))
    issues = _structure_issues(body) + _visual_issues(body, cells, profile) + _expression_issues(body)
    if purpose == "빠른 의사결정용" and body:
        issues.append(_issue("선호 제안", "첫머리 검토", body[0],
                             PURPOSE_CHECKLIST[(document_kind, purpose)] + " 두괄식을 강제하지 않습니다."))
    outline = [{"location": item["location"], "role": display_role(item["role"]), "text": item["text"]}
               for item in body if item["role"] in ("제목", "중제목", "소제목")]
    return {"version": 1, "source": Path(path).name,
            "profile": profile.get("name") if profile else None,
            "document_kind": document_kind, "purpose": purpose,
            "body_count": len(body), "cell_count": len(cells), "outline": outline,
            "issues": issues}
