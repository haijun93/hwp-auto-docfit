"""노트북 노트를 한/글 HWPX 문서로 만든다(COM 없이 파일만 생성).

문서 구성: 제목 → (노트북 이름) → 태그 줄 → 노트 본문 → 인용(인용 문단 + 출처 파일명·위치) → 출처 비교 표.
바탕 문서는 앱 내장 '기본 서식.hwpx'(쪽 여백·글꼴 목록)이고, 글자·문단·표 서식은 표 생성기
(docfit_core.table_builder)의 서식 풀·표 XML 함수를 그대로 쓴다. 만든 파일은 임시 파일에 쓴 뒤
defusedxml로 다시 읽어 구조를 확인하고 나서 대상 경로로 옮긴다. XML 파싱은 defusedxml만 쓴다.
"""
from __future__ import annotations

import copy
import io
import os
import re
import tempfile
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from .batch_format import _serialize
from .hwpx import open_hwpx_safely
from .table_builder import _cell, _child, _element, _Header, _table, _tag

MAX_TEXT = 20_000          # 본문·인용 한 칸 글자 수 상한
MAX_CITATIONS = 500
MAX_COMPARE_ROWS = 400
STYLES = {
    "title": {"font": "한컴돋움", "size": 18.0, "bold": True, "color": "#000000"},
    "meta": {"font": "한컴돋움", "size": 10.0, "bold": False, "color": "#555555"},
    "tags": {"font": "한컴돋움", "size": 11.0, "bold": False, "color": "#1F4E99"},
    "heading": {"font": "한컴돋움", "size": 14.0, "bold": True, "color": "#000000"},
    "body": {"font": "휴먼명조", "size": 13.0, "bold": False, "color": "#000000"},
    "quote": {"font": "휴먼명조", "size": 12.0, "bold": False, "color": "#333333"},
    "source": {"font": "한컴돋움", "size": 10.0, "bold": False, "color": "#666666"},
    "cell_head": {"font": "한컴돋움", "size": 11.0, "bold": True, "color": "#000000"},
    "cell": {"font": "휴먼명조", "size": 11.0, "bold": False, "color": "#000000"},
}
HEAD_FILL = "#E7EEF8"
COMPARE_HEADERS = ("출처", "위치", "근거 문단")
COMPARE_RATIOS = (25, 15, 60)
_INVALID = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


class NotebookHwpxError(ValueError):
    """노트북 내보내기 자료가 올바르지 않거나 만든 문서 검증에 실패했다."""


def clean_text(value, limit=MAX_TEXT) -> str:
    """XML에 쓸 수 없는 제어 문자를 빼고 줄바꿈을 \\n으로 맞춘다. 탭은 빈칸 하나로 바꾼다."""
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    return _INVALID.sub("", text)[:limit]


def _position(paragraph, location) -> str:
    """'문단 3 · 2쪽'처럼 위치를 쓴다. paragraph는 사람이 읽는 번호(1부터)."""
    parts = []
    if paragraph is not None and str(paragraph).strip() != "":
        parts.append(f"문단 {paragraph}")
    location = clean_text(location, 200).strip()
    if location:
        parts.append(location)
    return " · ".join(parts)


def normalize(doc) -> dict:
    """내보내기 자료를 검증·정리한다(모든 글은 clean_text를 거친다)."""
    if not isinstance(doc, dict):
        raise NotebookHwpxError("내보낼 노트 정보를 확인해 주세요.")
    title = clean_text(doc.get("title"), 300).strip() or "제목 없는 노트"
    tags = [clean_text(t, 40).strip() for t in (doc.get("tags") or []) if clean_text(t, 40).strip()]
    citations = []
    for item in (doc.get("citations") or [])[:MAX_CITATIONS]:
        if not isinstance(item, dict):
            continue
        quote = clean_text(item.get("quote")).strip()
        if not quote:
            continue
        citations.append({"quote": quote, "source_name": clean_text(item.get("source_name"), 300).strip() or "출처",
                          "position": _position(item.get("paragraph"), item.get("location"))})
    compare = None
    raw = doc.get("compare")
    if isinstance(raw, dict) and clean_text(raw.get("query"), 200).strip():
        groups = []
        for group in raw.get("groups") or []:
            if not isinstance(group, dict):
                continue
            hits = [{"position": _position(h.get("paragraph"), h.get("location")), "body": clean_text(h.get("body")).strip()}
                    for h in (group.get("hits") or []) if isinstance(h, dict)]
            groups.append({"source_name": clean_text(group.get("source_name"), 300).strip() or "출처", "hits": hits})
        compare = {"query": clean_text(raw.get("query"), 200).strip(), "groups": groups}
    return {"title": title, "notebook": clean_text(doc.get("notebook"), 200).strip(), "tags": tags,
            "body": clean_text(doc.get("body")), "citations": citations, "compare": compare}


def _para(pool, *, align="JUSTIFY", left=0, prev=0, next_=0):
    """기본 문단 모양(id 0)을 복제해 정렬·왼쪽 여백·문단 위아래 간격을 바꾼 ID(같은 값은 재사용)."""
    key = (align, left, prev, next_)
    cache = pool.__dict__.setdefault("_nb_paras", {})
    if key in cache:
        return cache[key]
    source = next(x for x in pool.groups["paraProperties"] if x.get("id") == "0")
    clone = copy.deepcopy(source)
    align_node = _child(clone, "align")
    if align_node is not None:
        align_node.set("horizontal", align)
    # hp:case(HwpUnitChar)는 HWPUNIT 그대로, hp:default는 두 배 값을 쓴다(한/글 저장 관례).
    holders = [(clone, 1)] + [(x, 2 if _tag(x) == "default" else 1) for x in clone.iter() if _tag(x) in ("case", "default")]
    for holder, scale in holders:
        for margin in (x for x in holder if _tag(x) == "margin"):
            for name, value in (("left", left), ("prev", prev), ("next", next_)):
                node = _child(margin, name)
                if node is not None:
                    node.set("value", str(value * scale))
    cache[key] = pool._append("paraProperties", clone)
    return cache[key]


def _paragraph(section, text, para, char):
    p = _element(section, "p", id=0, paraPrIDRef=para, styleIDRef=0, pageBreak=0, columnBreak=0, merged=0)
    run = _element(p, "run", charPrIDRef=char)
    _element(run, "t").text = text
    return p


def _compare_table(holder_run, compare, pool, body_width):
    """출처 비교 표: [출처 | 위치 | 근거 문단]. 출처 칸은 그 출처의 근거 행 수만큼 세로로 합친다."""
    rows = []                                   # (출처 이름, rowspan 또는 0(덮임), 위치, 근거)
    for group in compare["groups"]:
        hits = group["hits"] or [{"position": "", "body": "근거 문단 없음"}]
        for i, hit in enumerate(hits):
            rows.append((group["source_name"], len(hits) if i == 0 else 0, hit["position"], hit["body"]))
            if len(rows) >= MAX_COMPARE_ROWS:
                break
        if len(rows) >= MAX_COMPARE_ROWS:
            break
    if not rows:
        rows.append(("", 1, "", "비교할 출처가 없습니다"))
    # 잘린 마지막 출처의 rowspan이 표 밖으로 나가지 않게 맞춘다.
    fixed = []
    for index, (name, span, position, body) in enumerate(rows):
        fixed.append((name, min(span, len(rows) - index) if span else 0, position, body))
    total = sum(COMPARE_RATIOS)
    widths = [body_width * r // total for r in COMPARE_RATIOS]
    widths[-1] += body_width - sum(widths)
    line = ("SOLID", "0.12 mm", "#000000")
    sides = {"left": line, "right": line, "top": line, "bottom": line}
    head_border, body_border = pool.border(sides, HEAD_FILL), pool.border(sides, "")
    head_char, cell_char = pool.char(STYLES["cell_head"]), pool.char(STYLES["cell"])
    center, left = pool.center_para(), _para(pool, align="LEFT")
    height = 1800
    table = _table(holder_run, len(fixed) + 1, 3, body_width, height * (len(fixed) + 1), pool.border({}))
    tr = _element(table, "tr")
    for c, label in enumerate(COMPARE_HEADERS):
        _cell(tr, col=c, row=0, width=widths[c], height=height, border=head_border, para=center, char=head_char,
              text=label, header=True)
    for r, (name, span, position, body) in enumerate(fixed, 1):
        tr = _element(table, "tr")
        if span:
            _cell(tr, col=0, row=r, rowspan=span, width=widths[0], height=height * span, border=body_border,
                  para=center, char=cell_char, text=name)
        _cell(tr, col=1, row=r, width=widths[1], height=height, border=body_border, para=center, char=cell_char,
              text=position)
        _cell(tr, col=2, row=r, width=widths[2], height=height, border=body_border, para=left, char=cell_char,
              text=body)
    return table


def plain_text(doc) -> str:
    """미리보기(Preview/PrvText.txt)용 글."""
    lines = [doc["title"]]
    if doc["tags"]:
        lines.append("태그: " + " ".join("#" + t for t in doc["tags"]))
    lines.append(doc["body"])
    for c in doc["citations"]:
        lines.append(f"“{c['quote']}” — {c['source_name']}" + (f" · {c['position']}" if c["position"] else ""))
    if doc["compare"]:
        lines.append("출처 비교: " + doc["compare"]["query"])
    return "\n".join(lines)[:4000]


def build_notebook_hwpx(doc, base_path, target_path) -> Path:
    """노트(doc)를 HWPX로 target_path에 만든다. 임시 파일에 쓰고 다시 읽어 확인한 뒤 옮긴다(원자적 교체)."""
    doc = normalize(doc)
    with open_hwpx_safely(base_path) as z:
        contents = {info.filename: z.read(info.filename) for info in z.infolist()}
    sections = sorted(n for n in contents if re.fullmatch(r"Contents/section\d+\.xml", n))
    if not sections or "Contents/header.xml" not in contents:
        raise NotebookHwpxError("바탕 문서 구조를 확인해 주세요.")
    header_bytes, section_bytes = contents["Contents/header.xml"], contents[sections[0]]
    header, section = ET.fromstring(header_bytes), ET.fromstring(section_bytes)
    pool = _Header(header)
    page = next(x for x in section.iter() if _tag(x) == "pagePr")
    margin = _child(page, "margin")
    body_width = int(page.get("width")) - int(margin.get("left")) - int(margin.get("right"))

    # 첫 문단의 구역·단 설정만 남기고 바탕 문서 본문은 비운다(table_builder와 같은 방식).
    paragraphs = [p for p in section if _tag(p) == "p"]
    first = paragraphs[0]
    for p in paragraphs[1:]:
        section.remove(p)
    for child in list(first):
        if _tag(child) == "run":
            for item in list(child):
                if _tag(item) not in ("secPr", "ctrl"):
                    child.remove(item)
            if not len(child):
                first.remove(child)
        elif _tag(child) == "linesegarray":
            first.remove(child)

    chars = {role: pool.char(style) for role, style in STYLES.items()}
    body_para = _para(pool)
    heading_para = _para(pool, align="LEFT", prev=1200, next_=400)
    quote_para = _para(pool, left=2000, prev=600)
    source_para = _para(pool, align="RIGHT", left=2000)

    # 제목은 구역 설정 문단에 바로 쓴다(빈 첫 줄이 생기지 않게).
    first.set("paraPrIDRef", pool.center_para())
    title_run = _element(first, "run", charPrIDRef=chars["title"])
    _element(title_run, "t").text = doc["title"]
    if doc["notebook"]:
        _paragraph(section, "노트북: " + doc["notebook"], pool.center_para(), chars["meta"])
    if doc["tags"]:
        _paragraph(section, "태그: " + " ".join("#" + t for t in doc["tags"]), body_para, chars["tags"])
    _paragraph(section, "", body_para, chars["body"])
    for line in (doc["body"].split("\n") if doc["body"].strip() else []):
        _paragraph(section, line, body_para, chars["body"])

    if doc["citations"]:
        _paragraph(section, f"인용 ({len(doc['citations'])}건)", heading_para, chars["heading"])
        for item in doc["citations"]:
            for line in item["quote"].split("\n"):
                _paragraph(section, line, quote_para, chars["quote"])
            label = "— " + item["source_name"] + (f" · {item['position']}" if item["position"] else "")
            _paragraph(section, label, source_para, chars["source"])

    if doc["compare"]:
        _paragraph(section, "출처 비교: " + doc["compare"]["query"], heading_para, chars["heading"])
        holder = _element(section, "p", id=0, paraPrIDRef=pool.center_para(), styleIDRef=0, pageBreak=0,
                          columnBreak=0, merged=0)
        run = _element(holder, "run", charPrIDRef=chars["cell"])
        _compare_table(run, doc["compare"], pool, body_width)
        _element(run, "t")

    contents["Contents/header.xml"] = _serialize(header, header_bytes)
    contents[sections[0]] = _serialize(section, section_bytes)
    for extra in sections[1:]:
        contents.pop(extra)
    if "Preview/PrvText.txt" in contents:
        contents["Preview/PrvText.txt"] = plain_text(doc).encode("utf-8")

    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as out:
        if "mimetype" in contents:
            out.writestr("mimetype", contents.pop("mimetype"), compress_type=zipfile.ZIP_STORED)
        for name, data in contents.items():
            out.writestr(name, data)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".nb-", suffix=".hwpx.tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(buffer.getvalue())
        _verify(temporary, doc)
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target


# ---- 다시 읽기(검증·시험용) --------------------------------------------------------------------------

def _own_text(paragraph) -> str:
    parts = []

    def visit(node, top=False):
        if _tag(node) == "p" and not top:
            return
        if _tag(node) == "t" and node.text:
            parts.append(node.text)
        for child in node:
            visit(child)

    visit(paragraph, top=True)
    return "".join(parts)


def read_notebook_hwpx(path) -> dict:
    """만든 HWPX를 defusedxml로 다시 읽어 {paragraphs: [본문 문단 글], tables: [[[칸 글]]]}을 돌려준다.

    본문 문단은 구역 바로 아래 문단만(표 칸 문단 제외), 표는 행·열 순서의 칸 글(합친 칸은 한 번만)이다.
    """
    with open_hwpx_safely(path) as archive:
        names = archive.namelist()
        if "mimetype" not in names or archive.read("mimetype") != b"application/hwp+zip":
            raise NotebookHwpxError("HWPX mimetype이 올바르지 않습니다.")
        section_names = sorted(n for n in names if re.fullmatch(r"Contents/section\d+\.xml", n))
        if not section_names or "Contents/header.xml" not in names:
            raise NotebookHwpxError("HWPX 구역·머리 정보가 없습니다.")
        header = ET.fromstring(archive.read("Contents/header.xml"))
        root = ET.fromstring(archive.read(section_names[0]))
    char_ids = {x.get("id") for x in header.iter() if _tag(x) == "charPr"}
    para_ids = {x.get("id") for x in header.iter() if _tag(x) == "paraPr"}
    border_ids = {x.get("id") for x in header.iter() if _tag(x) == "borderFill"}
    for node in root.iter():
        name = _tag(node)
        if name == "run" and node.get("charPrIDRef") not in char_ids:
            raise NotebookHwpxError("없는 글자 모양을 가리키는 글이 있습니다.")
        if name == "p" and node.get("paraPrIDRef") not in para_ids:
            raise NotebookHwpxError("없는 문단 모양을 가리키는 문단이 있습니다.")
        if name in ("tc", "tbl") and node.get("borderFillIDRef") not in border_ids:
            raise NotebookHwpxError("없는 테두리를 가리키는 표가 있습니다.")
    paragraphs = [_own_text(p) for p in root if _tag(p) == "p"]
    tables = []
    for table in (x for x in root.iter() if _tag(x) == "tbl"):
        rows = []
        for tr in (x for x in table if _tag(x) == "tr"):
            rows.append(["\n".join(_own_text(p) for p in tc.iter() if _tag(p) == "p") for tc in tr if _tag(tc) == "tc"])
        if int(table.get("rowCnt", "0")) != len(rows):
            raise NotebookHwpxError("표 행 수가 rowCnt와 다릅니다.")
        tables.append(rows)
    return {"paragraphs": paragraphs, "tables": tables}


def _verify(path, doc) -> None:
    parsed = read_notebook_hwpx(path)
    text = "\n".join(parsed["paragraphs"])
    if not parsed["paragraphs"] or parsed["paragraphs"][0] != doc["title"]:
        raise NotebookHwpxError("만든 문서의 제목을 다시 읽지 못했습니다.")
    missing = [c["quote"] for c in doc["citations"] if c["quote"].split("\n")[0] not in text]
    if missing:
        raise NotebookHwpxError("만든 문서에서 인용 문단을 다시 읽지 못했습니다.")
    if bool(doc["compare"]) != bool(parsed["tables"]):
        raise NotebookHwpxError("만든 문서의 출처 비교 표를 확인하지 못했습니다.")
