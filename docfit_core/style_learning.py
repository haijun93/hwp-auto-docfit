"""HWPX 학습 자료의 근거·역할·중복 유형을 수집한다. 원본과 사용자 설정은 바꾸지 않는다.

결과는 학습 후보 목록이다. 기관별 서식을 자동으로 섞거나 현재 문서에 적용하지 않는다.
공개 저장소에는 예시 문서·원문·외부 앱 코드를 포함하지 않는다.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

from defusedxml import ElementTree as ET

from .hwpx import open_hwpx_safely
from . import table_style
from .style_inventory import parse_header

SCHEMA_VERSION = 1
_REFS = {"borderFillIDRef": "borderFill", "charPrIDRef": "charPr",
         "paraPrIDRef": "paraPr", "tabPrIDRef": "tabPr", "styleIDRef": "style",
         "nextStyleIDRef": "style", "numberingIDRef": "numbering"}


def _tag(e):
    return e.tag.rsplit("}", 1)[-1]


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def _index(header):
    definitions = {(_tag(e), e.get("id")): e for e in header.iter() if e.get("id") is not None}
    fonts = {(face.get("lang", "").lower(), f.get("id")): (f.get("face"), f.get("type"))
             for face in header.iter() if _tag(face) == "fontface" for f in face if _tag(f) == "font"}
    return definitions, fonts


def _semantic(e, definitions, fonts, stack=()):
    """문서별 ID를 실제 정의로 치환하고 본문·배치 캐시를 비교에서 제외한다."""
    name = _tag(e)
    if name in ("t", "linesegarray", "pos", "cellSz", "sz"):
        return None
    attrs = {}
    for key, value in sorted(e.attrib.items()):
        if key in ("id", "instid", "zOrder", "pageBreak", "columnBreak"):
            continue
        if name == "fontRef":
            value = fonts.get((key.lower(), value), ("unresolved-font", key, value))
        elif key in _REFS:
            ref = (_REFS[key], value)
            if ref in definitions and ref not in stack:
                value = _semantic(definitions[ref], definitions, fonts, stack + (ref,))
            elif ref in stack:
                value = ("recursive-reference", ref[0])
            else:
                value = ("unresolved-reference", *ref)
        attrs[key] = value
    children = [_semantic(c, definitions, fonts, stack) for c in e]
    return [name, attrs, [c for c in children if c is not None]]


def table_fingerprint(header, table):
    """글·문서 내부 ID가 달라도 구조·실제 서식·열 폭 비율이 같으면 같은 유형."""
    definitions, fonts = _index(header)
    width = next((int(e.get("width", "0")) for e in table if _tag(e) == "sz"), 0)
    row_shapes = []
    for row in table:
        if _tag(row) != "tr":
            continue
        cells = []
        for cell in row:
            if _tag(cell) != "tc":
                continue
            shape = _semantic(cell, definitions, fonts)
            # 반복되는 행은 같은 유형이다. 가로 위치·병합·폭은 남긴다.
            def strip_row(value):
                if isinstance(value, list) and len(value) == 3 and isinstance(value[1], dict):
                    value[1].pop("rowAddr", None)
                    # 서식이 같은 연속 문단은 대표 문단 하나로 비교한다.
                    children = []
                    for c in value[2]:
                        strip_row(c)
                        if not children or children[-1] != c or c[0] != "p":
                            children.append(c)
                    value[2] = children
            strip_row(shape)
            cell_width = next((int(e.get("width", "0")) for e in cell if _tag(e) == "cellSz"), 0)
            cells.append([shape, round(cell_width / width, 3) if width else cell_width])
        if not row_shapes or row_shapes[-1] != cells:
            row_shapes.append(cells)
    table_attrs = {k: v for k, v in table.attrib.items()
                   if k not in ("id", "zOrder", "rowCnt", "borderFillIDRef")}
    fill = definitions.get(("borderFill", table.get("borderFillIDRef")))
    return _digest([table_attrs, _semantic(fill, definitions, fonts) if fill is not None else None, row_shapes])


def _role(table, nested):
    if nested:
        return "nested", False
    if any(e is not table and _tag(e) == "tbl" for e in table.iter()):
        return "composite_form", False
    if table_style.is_user_designed_table(table):
        return "diagram_or_design", False
    rows, cols = int(table.get("rowCnt", "0")), int(table.get("colCnt", "0"))
    if rows == cols == 1:
        return "box_or_title", False
    if rows == 1:
        return "heading_or_band", False
    # 결재란·제목을 데이터 표로 자동 채택하지 않는다. 역할 확인이 필요하다.
    return "grid_candidate" if rows >= 2 and cols >= 2 else "form_candidate", False


def inspect_learning_document(path, *, source_id=None, organization="미확인"):
    """표별 후보를 반환한다. 본문은 해시만 남기고 원문을 목록에 복제하지 않는다."""
    path = Path(path)
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    source_hash = hasher.hexdigest()
    source_id = source_id or path.name
    tables = []
    with open_hwpx_safely(path) as archive:
        header = ET.fromstring(archive.read("Contents/header.xml"))
        for section in sorted(n for n in archive.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)):
            root = ET.fromstring(archive.read(section))
            parents = {c: parent for parent in root.iter() for c in parent}
            for ordinal, table in enumerate((e for e in root.iter() if _tag(e) == "tbl"), 1):
                ancestor = parents.get(table)
                nested = False
                while ancestor is not None:
                    nested |= _tag(ancestor) == "tbl"
                    ancestor = parents.get(ancestor)
                role, eligible = _role(table, nested)
                content = [(e.text or "", tuple(c.tail or "" for c in e)) for e in table.iter() if _tag(e) == "t"]
                tables.append({"id": _digest([source_hash, source_id, section, ordinal]), "source_id": source_id,
                               "section": section, "ordinal": ordinal, "nested": nested,
                               "rows": int(table.get("rowCnt", "0")), "cols": int(table.get("colCnt", "0")),
                               "family": table_fingerprint(header, table), "content_hash": _digest(content),
                               "role": role, "review_status": "unreviewed", "eligible": eligible})
        definitions = parse_header(header)
    return {"source_id": source_id, "sha256": source_hash, "organization": organization,
            "definitions": definitions, "tables": tables}


def build_learning_catalog(paths, *, root=None, organization="미확인"):
    """중복된 표를 공유하는 문서끼리 묶어 학습/평가 자료 유출을 막는다.

    대표 후보는 문서 한 개당 한 표씩만 투표한다. 표가 100회 반복된 한 문서가
    다른 기관의 1회 표본을 압도하지 않게 한다. 역할 승인 전에는 적용 후보가 아니다.
    """
    root = Path(root).resolve() if root is not None else None
    documents = []
    for path in sorted({Path(p).resolve() for p in paths}, key=str):
        source_id = path.relative_to(root).as_posix() if root else path.as_posix()
        documents.append(inspect_learning_document(path, source_id=source_id, organization=organization))
    parent = list(range(len(documents)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    owners, families = {}, defaultdict(list)
    for i, document in enumerate(documents):
        for table in document["tables"]:
            key = table["family"]
            if key in owners:
                parent[find(i)] = find(owners[key])
            else:
                owners[key] = i
            families[key].append(table)
    components = defaultdict(list)
    for i, document in enumerate(documents):
        components[find(i)].append(document["sha256"])
    for i, document in enumerate(documents):
        group = _digest(sorted(set(components[find(i)])))
        bucket = int(group[:8], 16) % 10
        document["split_group"] = group
        document["split"] = "test" if bucket == 0 else "validation" if bucket == 1 else "train"
    groups = []
    for key, members in sorted(families.items()):
        sources = sorted({m["source_id"] for m in members})
        groups.append({"family": key, "occurrences": len(members), "source_count": len(sources),
                       "sources": sources, "representative_id": min(members, key=lambda m: (m["source_id"], m["ordinal"]))["id"],
                       "vote_weight_per_source": 1, "review_status": "unreviewed"})
    warnings = []
    splits = Counter(d["split"] for d in documents)
    if len(components) < 3 or len(splits) < 3:
        warnings.append("독립 평가군이 부족합니다. 다른 기관의 미사용 원본을 추가하기 전에는 학습 효과를 확정하지 않습니다.")
    return {"schema_version": SCHEMA_VERSION, "documents": documents, "families": groups,
            "summary": {"documents": len(documents), "tables": sum(len(d["tables"]) for d in documents),
                        "families": len(groups), "split_groups": len(components), "splits": dict(splits)},
            "warnings": warnings}


def learn_reviewed_data_table(path, candidate, *, approved_role):
    """사람이 데이터 표로 확인한 표 하나만 기존 표 서식 프로필로 만든다.

    목록 작성 후 원본이 달라졌으면 중단한다. 후보 번호는 구역 안에서 1부터 센다.
    결재란·제목·그림 표의 문서 전체 적용은 이 함수로 승인할 수 없다.
    """
    if approved_role != "data":
        raise ValueError("사람이 데이터 표로 확인한 후보만 data 역할로 학습할 수 있습니다.")
    current = inspect_learning_document(path, source_id=candidate["source_id"])
    match = next((r for r in current["tables"] if r["id"] == candidate["id"]), None)
    if match is None or match["family"] != candidate["family"]:
        raise ValueError("원본 또는 표가 바뀌었습니다. 학습 목록을 다시 만드세요.")
    if match["nested"] or match["role"] != "grid_candidate":
        raise ValueError("제목·상자·그림·중첩표는 일반 데이터 표 서식으로 학습하지 않습니다.")
    if match["rows"] * match["cols"] > 100_000:
        raise ValueError("표의 논리 격자가 너무 커서 학습하지 않습니다.")
    with open_hwpx_safely(path) as archive:
        header = ET.fromstring(archive.read("Contents/header.xml"))
        root = ET.fromstring(archive.read(match["section"]))
        tables = [e for e in root.iter() if _tag(e) == "tbl"]
        style = table_style.learn_from_table(header, tables[match["ordinal"] - 1], current["source_id"])
    if not table_style.valid_style(style):
        raise ValueError("표 서식 검증에 실패했습니다.")
    return {"schema_version": SCHEMA_VERSION, "role": "data", "review_status": "approved",
            "source_sha256": current["sha256"], "candidate_id": match["id"],
            "family": match["family"], "table_style": style}
