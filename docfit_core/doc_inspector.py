"""COM 없는 제한 크기 문서 지문. 진단은 추천이며 실제 문서 검증을 대신하지 않는다."""
from collections import Counter, defaultdict
from pathlib import Path
import math
import re
import time
import struct
import zipfile
import zlib

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from .style_hierarchy import leading_marker

MAX_XML_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_ENTRIES = 2048
MAX_FILES = 100
SCAN_SECONDS = .08
EXTERNAL_DRAFT_EXTENSIONS = frozenset({
    '.doc', '.docx', '.xls', '.xlsx', '.pptx', '.hml', '.pdf',
    '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff', '.gif',
})


def _unknown():
    return {"mode": "spacing", "tables": True, "pages": 5, "complete": False}


def _xml(archive, info, budget):
    if (info.file_size > min(MAX_XML_BYTES, budget) or info.flag_bits & 1
            or (info.file_size > 65536 and info.file_size / max(1, info.compress_size) > 200)):
        raise ValueError("진단 크기 제한")
    with archive.open(info) as stream:
        data = stream.read(min(MAX_XML_BYTES, budget) + 1)
    if len(data) > min(MAX_XML_BYTES, budget):
        raise ValueError("진단 크기 제한")
    return ET.fromstring(data), len(data)


def _inspect(path, deadline):
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        with path.open("rb") as stream:
            raw = stream.read(256 * 1024 + 1)
        sample = raw[:256 * 1024]
        try:
            text = sample.decode("utf-16" if sample.startswith((b'\xff\xfe', b'\xfe\xff')) else "utf-8-sig")
        except UnicodeError:
            text = sample.decode("cp949", errors="replace")
        tables = bool(re.search(r"[┌┏┬┳│┃].*[─━│┃]|^\s*\|?.+\|.+\n\s*\|?\s*:?-{3}", text, re.M))
        complete = len(raw) <= 256 * 1024
        return {"mode": "all", "tables": tables or not complete,
                "pages": max(1, math.ceil(len(text.splitlines()) / 40)), "complete": complete}
    if suffix in EXTERNAL_DRAFT_EXTENSIONS:
        # 원본 서식을 추측하지 않는다. 변환 초안임을 알리고 전체 서식 적용을 추천한다.
        return {"mode": "all", "tables": True, "pages": 5, "complete": False}
    if suffix != ".hwpx":
        return _unknown()
    # ZipFile 자체가 중앙 디렉터리 전체를 먼저 읽으므로 생성 전에도 크기를 제한한다.
    if path.stat().st_size > 64 * 1024 * 1024:
        return _unknown()
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - 65557))
        tail = stream.read(65557)
    eocd = tail.rfind(b'PK\x05\x06')
    if eocd < 0 or len(tail) - eocd < 22:
        return _unknown()
    entries = struct.unpack_from('<H', tail, eocd + 10)[0]
    directory_bytes = struct.unpack_from('<I', tail, eocd + 12)[0]
    if entries > MAX_ENTRIES or directory_bytes > 1024 * 1024:
        return _unknown()
    # 압축 폭탄 방어(보안 검토 S2): 항목 크기·압축률 상한을 검사하는 공용 열기를 쓴다.
    from docfit_core.hwpx import open_hwpx_safely
    with open_hwpx_safely(path) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_ENTRIES or len({x.filename for x in infos}) != len(infos):
            return _unknown()
        sections = sorted((x for x in infos if re.fullmatch(r"Contents/section\d+\.xml", x.filename)),
                          key=lambda x: int(re.search(r"section(\d+)", x.filename)[1]))
        if not sections:
            return _unknown()
        budget = MAX_TOTAL_BYTES
        fonts = {}
        headers = [x for x in infos if x.filename == "Contents/header.xml"]
        if headers:
            header, used = _xml(archive, headers[0], budget)
            budget -= used
            font_names = {font.get("id"): font.get("face") for group in header.findall(".//{*}fontface")
                          if group.get("lang", "").upper() == "HANGUL" for font in group.findall("{*}font")}
            for item in header.findall(".//{*}charPr"):
                ref = item.find("{*}fontRef")
                font_id = ref.get("hangul") if ref is not None else None
                fonts[item.get("id")] = (font_names.get(font_id) or font_id, item.get("height"))
        styles = defaultdict(set)
        tables = False
        count = 0
        characters = 0
        breaks = 0
        marked = False
        for info in sections:
            if time.monotonic() > deadline:
                return _unknown()
            section, used = _xml(archive, info, budget)
            budget -= used
            tables |= section.find(".//{*}tbl") is not None
            table_paragraphs = {p for table in section.findall(".//{*}tbl") for p in table.iter()
                                if p.tag.rsplit("}", 1)[-1] == "p"}
            for para in section.iter():
                if para.tag.rsplit("}", 1)[-1] != "p":
                    continue
                count += 1
                if count % 128 == 0 and time.monotonic() > deadline:
                    return _unknown()
                breaks += para.get("pageBreak") == "1"
                runs = para.findall("{*}run")
                parts = [("".join(t.text or "" for t in run.findall("{*}t")), run) for run in runs]
                text = "".join(part for part, _ in parts)
                characters += len(text)
                marker, role = leading_marker(text)
                # 표 머리글/셀 글꼴과 본문 글꼴의 차이는 정상이며 서식 혼재로 보지 않는다.
                if not marker or para in table_paragraphs:
                    continue
                marked = True
                if role and parts:
                    _, primary = max(parts, key=lambda item: len(item[0]))
                    style = fonts.get(primary.get("charPrIDRef"))
                    if style and all(v is not None for v in style):
                        styles[role].add(style)
        mode = "unify" if any(len(values) > 1 for values in styles.values()) else "spacing"
        if not marked and not tables:
            mode = "all"
        return {"mode": mode, "tables": tables, "pages": max(1, breaks + 1, math.ceil(count / 40), math.ceil(characters / 1800)),
                "complete": True}


def inspect_documents(paths: list[str]) -> dict:
    """대개 0.1초 안에 경량 진단. 예산·크기 초과/불명 문서는 보수적인 옵션을 유지한다."""
    paths = list(paths)
    deadline = time.monotonic() + SCAN_SECONDS
    reports = []
    for index, value in enumerate(paths):
        try:
            if index >= MAX_FILES or time.monotonic() > deadline:
                report = _unknown()
            else:
                path = Path(value)
                report = _unknown() if path.is_symlink() or not path.is_file() else _inspect(path, deadline)
        except (OSError, ValueError, RuntimeError, EOFError, zlib.error, zipfile.BadZipFile, ET.ParseError, DefusedXmlException):
            report = _unknown()
        reports.append(report)
    # 원문 텍스트 초안이 하나라도 있으면 전수 양식 적용을 추천한다.
    draft = any(Path(value).suffix.lower() in {".txt", ".md"} | EXTERNAL_DRAFT_EXTENSIONS for value in paths)
    mode = "all" if draft else Counter(r["mode"] for r in reports).most_common(1)[0][0] if reports else "spacing"
    reason = {"all": "초안 텍스트 감지 · 한 번에 적용을 추천해요.",
              "unify": "같은 문단 역할에 글꼴·크기가 섞여 있어 서식 통일을 추천해요.",
              "spacing": "기존 양식을 유지하며 자간 정리를 추천해요."}[mode]
    external = sorted({Path(value).suffix.lstrip('.').upper() for value in paths
                       if Path(value).suffix.lower() in EXTERNAL_DRAFT_EXTENSIONS})
    if external:
        reason = f"외부 포맷 {', '.join(external)} 감지 → 구조 추출 후 공문서 양식 자동 적용"
    tables = any(r["tables"] for r in reports)
    pages = max((r["pages"] for r in reports), default=0)
    return {"recommended_mode": mode, "reason": reason, "has_tables": tables,
            "estimated_pages": pages, "show_table_option": tables,
            "show_page_range": len(paths) == 1 and Path(paths[0]).suffix.lower() in {".hwp", ".hwpx"} and pages >= 5,
            "is_single_file": len(paths) == 1, "scan_complete": all(r["complete"] for r in reports)}
