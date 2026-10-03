"""패키지 전수 목록과 해석 범위.

모든 압축 항목을 보관 정보(크기·CRC·원본/내용 해시)와 함께 나열하고, XML 항목은 요소·속성을 빠짐없이
센다. 각 요소·속성을 이 프로그램이 '의미를 해석하는가'로 나눈다. 해석 목록(INTERPRETED)은 현재
분석기가 실제로 읽는 값만 담는다(예: 장평·자간은 한글 슬롯만 읽으므로 다른 언어 슬롯은 해석하지 않음).

상태: 해석 완료(요소와 모든 속성을 해석) / 일부 해석(요소는 알지만 해석하지 않는 속성이 있음) /
원문 보존만(요소를 해석하지 않음, 원본 그대로 보관만) / 손상(읽지 못함). 보존 성공과 해석 범위는 따로 보고한다.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256

from defusedxml import ElementTree as ET

from .package import PackageSnapshot

_LANG = {"hangul", "latin", "hanja", "japanese", "other", "symbol", "user"}
_SIDES = {"left", "right", "top", "bottom"}
# header.xml에서 의미를 읽는 요소와 속성
HEADER_INTERPRETED = {
    "head": set(), "refList": set(),
    "fontfaces": {"itemCnt"}, "fontface": {"lang", "fontCnt"}, "font": {"id", "face", "type"},
    "borderFills": {"itemCnt"}, "charProperties": {"itemCnt"}, "tabProperties": {"itemCnt"},
    "numberings": {"itemCnt"}, "bullets": {"itemCnt"}, "paraProperties": {"itemCnt"}, "styles": {"itemCnt"},
    "charPr": {"id", "height", "textColor", "shadeColor", "borderFillIDRef"},
    "fontRef": {"hangul", "latin"}, "ratio": {"hangul"}, "spacing": {"hangul"}, "relSz": {"hangul"},
    "offset": {"hangul"}, "bold": set(), "italic": set(), "underline": {"type"}, "strikeout": {"shape"},
    "outline": {"type"}, "shadow": {"type"}, "supscript": set(), "subscript": set(),
    "paraPr": {"id", "tabPrIDRef", "condense", "snapToGrid"}, "align": {"horizontal"},
    "heading": {"type", "idRef", "level"},
    "breakSetting": {"keepWithNext", "keepLines", "pageBreakBefore", "widowOrphan", "breakNonLatinWord"},
    "switch": set(), "case": {"required-namespace"}, "default": set(), "margin": set(),
    "intent": {"value", "unit"}, "left": {"value", "unit"}, "right": {"value", "unit"},
    "prev": {"value", "unit"}, "next": {"value", "unit"}, "lineSpacing": {"type", "value", "unit"},
    "border": {"borderFillIDRef"},
    "borderFill": {"id"}, "leftBorder": {"type", "width", "color"}, "rightBorder": {"type", "width", "color"},
    "topBorder": {"type", "width", "color"}, "bottomBorder": {"type", "width", "color"},
    "diagonal": {"type", "width", "color"}, "fillBrush": set(), "winBrush": {"faceColor"},
    "gradation": set(), "color": {"value"},
    "tabPr": {"id", "autoTabLeft", "autoTabRight"}, "tabItem": {"pos", "type", "leader"},
    "numbering": {"id", "start"}, "paraHead": {"level", "numFormat", "start"}, "bullet": {"id", "char"},
    "style": {"id", "type", "name", "engName", "paraPrIDRef", "charPrIDRef", "nextStyleIDRef"},
}
# section*.xml에서 의미를 읽는 요소와 속성(배치 캐시 linesegarray는 '한/글이 다시 계산하는 값'으로 안다)
SECTION_INTERPRETED = {
    "sec": set(), "p": {"id", "paraPrIDRef", "styleIDRef", "pageBreak"}, "run": {"charPrIDRef"},
    "t": set(), "fwSpace": set(), "nbSpace": set(), "lineBreak": set(), "tab": set(),
    "linesegarray": set(), "lineseg": {"textpos", "vertpos", "vertsize", "textheight", "baseline",
                                        "spacing", "horzpos", "horzsize", "flags"},
    "tbl": {"rowCnt", "colCnt", "borderFillIDRef"}, "sz": {"width", "height"},
    "outMargin": _SIDES, "inMargin": _SIDES, "tr": set(),
    "tc": {"borderFillIDRef", "hasMargin"}, "subList": {"vertAlign"},
    "cellAddr": {"colAddr", "rowAddr"}, "cellSpan": {"colSpan", "rowSpan"}, "cellSz": {"width", "height"},
    "cellMargin": _SIDES, "pagePr": {"width", "height", "landscape"},
    "margin": _SIDES | {"header", "footer", "gutter"},
}
# 서식과 무관한 포장 정보·미리보기·그림은 원문 보존만 한다.
_BINARY_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".wmf", ".emf", ".tif", ".tiff", ".ole", ".bin")


def _local(name):
    return name.rsplit("}", 1)[-1]


def _role(name):
    if name == "mimetype":
        return "mimetype"
    if name == "Contents/header.xml":
        return "header"
    if name.startswith("Contents/section") and name.endswith(".xml"):
        return "section"
    if name.startswith("BinData/"):
        return "bindata"
    if name.startswith("Preview/"):
        return "preview"
    if name.startswith("META-INF/") or name in ("Contents/content.hpf", "version.xml"):
        return "package"
    if name == "settings.xml":
        return "settings"
    return "other"


def inventory(source) -> dict:
    """패키지 전수 목록. source는 경로나 PackageSnapshot."""
    snapshot = source if isinstance(source, PackageSnapshot) else PackageSnapshot.load(source)
    result = {"path": snapshot.path, "format": snapshot.format, "sha256": snapshot.sha256,
              "size": len(snapshot.data), "parts": []}
    if snapshot.format != "hwpx":
        return result
    for name, entry in snapshot.entries.items():
        part = {"name": name, "role": _role(name), "method": entry.method, "size": entry.size,
                "compressed_size": entry.compressed_size, "crc": f"{entry.crc:08X}",
                "raw_sha256": entry.raw_sha256}
        try:
            content = snapshot.read(name)
            part["content_sha256"] = sha256(content).hexdigest()
        except Exception as exc:
            part.update(kind="damaged", error=str(exc))
            result["parts"].append(part)
            continue
        if name.lower().endswith((".xml", ".hpf", ".rdf")):
            part["kind"] = "xml"
            try:
                root = ET.fromstring(content)
                elements, attributes = Counter(), Counter()
                for element in root.iter():
                    local = _local(element.tag)
                    elements[local] += 1
                    for attr in element.attrib:
                        attributes[f"{local}@{_local(attr)}"] += 1
                part["elements"] = dict(elements)
                part["attributes"] = dict(attributes)
            except Exception as exc:
                part.update(kind="damaged", error=f"XML을 읽지 못함: {exc}")
        elif name.lower().endswith(_BINARY_SUFFIX) or part["role"] == "bindata":
            part["kind"] = "binary"
        else:
            part["kind"] = "text" if name != "mimetype" else "mimetype"
        result["parts"].append(part)
    return result


def coverage(listing) -> dict:
    """전수 목록에서 요소·속성별 해석 범위를 낸다. 해석하지 못한 항목이 하나라도 있으면 완전 해석이 아니다."""
    parts, totals = [], Counter()
    for part in listing.get("parts", []):
        role = part["role"]
        catalog = HEADER_INTERPRETED if role == "header" else SECTION_INTERPRETED if role == "section" else None
        entry = {"name": part["name"], "role": role, "kind": part.get("kind")}
        if part.get("kind") == "damaged":
            entry["status"] = "손상"
            entry["error"] = part.get("error")
        elif catalog is None:
            entry["status"] = "원문 보존만"
        else:
            unknown_elements = {k: v for k, v in part["elements"].items() if k not in catalog}
            unknown_attributes = {}
            for key, count in part["attributes"].items():
                local, attr = key.split("@", 1)
                if local not in catalog or attr not in catalog[local]:
                    unknown_attributes[key] = count
            element_total = sum(part["elements"].values())
            attribute_total = sum(part["attributes"].values())
            entry.update(
                elements_total=element_total,
                elements_interpreted=element_total - sum(unknown_elements.values()),
                attributes_total=attribute_total,
                attributes_interpreted=attribute_total - sum(unknown_attributes.values()),
                unknown_elements=dict(sorted(unknown_elements.items(), key=lambda kv: -kv[1])),
                unknown_attributes=dict(sorted(unknown_attributes.items(), key=lambda kv: -kv[1])),
                status=("해석 완료" if not unknown_elements and not unknown_attributes
                        else "일부 해석" if element_total > sum(unknown_elements.values()) else "원문 보존만"))
            for key in ("elements_total", "elements_interpreted", "attributes_total", "attributes_interpreted"):
                totals[key] += entry[key]
        parts.append(entry)
    complete = bool(parts) and all(p["status"] == "해석 완료" for p in parts
                                   if p["role"] in ("header", "section"))
    damaged = [p["name"] for p in parts if p["status"] == "손상"]
    preserved_only = [p["name"] for p in parts if p["status"] == "원문 보존만"]

    def ratio(done, total):
        return round(done / total, 4) if total else None

    if listing.get("format") != "hwpx":
        verdict = "원본 보관·동일 복제만 지원(내용 해석 지원 불가)"
    elif damaged:
        verdict = "손상 항목 있음"
    elif complete and not preserved_only:
        verdict = "원본 보존 완료·의미 해석 완료"
    else:
        verdict = "원본 보존 완료·의미 해석 미완료"
    return {"format": listing.get("format"), "sha256": listing.get("sha256"), "parts": parts,
            "elements_ratio": ratio(totals["elements_interpreted"], totals["elements_total"]),
            "attributes_ratio": ratio(totals["attributes_interpreted"], totals["attributes_total"]),
            "preserved_only_parts": preserved_only, "damaged_parts": damaged, "verdict": verdict}
