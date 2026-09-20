"""Defensive HWPX inspection, structural summaries and Markdown export.

The editor deliberately keeps this module independent from Hancom COM.  HWP
files are converted to a temporary HWPX snapshot by the caller, after which
the same deterministic parser is used for both formats.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path, PurePosixPath
import re
from typing import Iterable
from zipfile import BadZipFile, ZipFile, ZipInfo

from defusedxml import ElementTree as ET


@dataclass(frozen=True)
class HwpxLimits:
    max_entries: int = 10_000
    max_total_size: int = 512 * 1024 * 1024
    max_file_size: int = 128 * 1024 * 1024
    max_compression_ratio: int = 1_000


class HwpxSecurityError(ValueError):
    """Raised when an HWPX archive is malformed or violates safety limits."""


@dataclass
class DocumentBlock:
    type: str
    text: str = ""
    level: int | None = None
    rows: list[list[str]] | None = None
    section: int = 1


@dataclass
class DocumentInspection:
    path: str
    blocks: list[DocumentBlock]
    section_count: int
    paragraph_count: int
    table_count: int
    image_count: int
    control_count: int
    text: str
    text_sha256: str
    warnings: list[str]

    def summary(self) -> dict:
        data = asdict(self)
        data.pop("blocks", None)
        data.pop("text", None)
        return data


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _safe_member_name(info: ZipInfo) -> None:
    name = info.filename.replace("\\", "/")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", name):
        raise HwpxSecurityError(f"안전하지 않은 압축 경로입니다: {info.filename}")
    # Unix symlinks are not valid document members and can escape extraction.
    if ((info.external_attr >> 16) & 0o170000) == 0o120000:
        raise HwpxSecurityError(f"심볼릭 링크가 포함되어 있습니다: {info.filename}")


def validate_hwpx(path: str | Path, limits: HwpxLimits | None = None) -> dict:
    """Validate archive structure without extracting anything to disk."""
    limits = limits or HwpxLimits()
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    try:
        with ZipFile(source) as archive:
            infos = archive.infolist()
            if len(infos) > limits.max_entries:
                raise HwpxSecurityError(
                    f"압축 항목이 너무 많습니다({len(infos):,} > {limits.max_entries:,})."
                )
            total = 0
            names: set[str] = set()
            for info in infos:
                _safe_member_name(info)
                names.add(info.filename.replace("\\", "/"))
                if info.file_size > limits.max_file_size:
                    raise HwpxSecurityError(
                        f"압축 내부 파일이 너무 큽니다: {info.filename} ({info.file_size:,}바이트)"
                    )
                total += info.file_size
                if total > limits.max_total_size:
                    raise HwpxSecurityError(
                        f"압축 해제 예상 크기가 제한을 넘습니다({total:,}바이트)."
                    )
                if info.file_size and info.compress_size == 0:
                    raise HwpxSecurityError(f"비정상 압축 항목입니다: {info.filename}")
                if info.compress_size and info.file_size / info.compress_size > limits.max_compression_ratio:
                    raise HwpxSecurityError(f"비정상 압축률이 감지되었습니다: {info.filename}")
            section_names = sorted(
                (name for name in names if re.fullmatch(r"Contents/section\d+\.xml", name)),
                key=lambda value: int(re.search(r"\d+", value).group()),
            )
            if "Contents/header.xml" not in names:
                raise HwpxSecurityError("HWPX 필수 파일 Contents/header.xml이 없습니다.")
            if not section_names:
                raise HwpxSecurityError("HWPX 본문 섹션을 찾지 못했습니다.")
            bad = archive.testzip()
            if bad:
                raise HwpxSecurityError(f"CRC 검사가 실패했습니다: {bad}")
            return {
                "entry_count": len(infos),
                "total_uncompressed_size": total,
                "section_names": section_names,
            }
    except BadZipFile as exc:
        raise HwpxSecurityError("올바른 HWPX ZIP 문서가 아닙니다.") from exc


def _own_text(element: ET.Element) -> str:
    parts: list[str] = []

    def visit(node: ET.Element, root: bool = False) -> None:
        name = _local_name(node.tag)
        if not root and name in {"p", "tbl"}:
            return
        if name == "t" and node.text:
            parts.append(node.text)
        elif name in {"lineBreak", "br"}:
            parts.append("\n")
        elif name == "tab":
            parts.append("\t")
        for child in node:
            visit(child)

    visit(element, True)
    return "".join(parts)


def _table_rows(table: ET.Element) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.iter():
        if _local_name(row.tag) != "tr":
            continue
        cells: list[str] = []
        for cell in row:
            if _local_name(cell.tag) not in {"tc", "cell"}:
                continue
            text = " ".join(
                value.strip() for value in (_own_text(p) for p in cell.iter() if _local_name(p.tag) == "p")
                if value.strip()
            )
            cells.append(text.replace("|", "\\|"))
        if cells:
            rows.append(cells)
    return rows


def _paragraph_level(text: str) -> int | None:
    stripped = text.strip()
    if not stripped:
        return None
    if re.match(r"^(제\s*\d+\s*[장절]|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.．])", stripped):
        return 1
    if re.match(r"^(\d+[.．]|[가-하][.．])\s*\S", stripped):
        return 2
    return None


def _direct_content(root: ET.Element) -> Iterable[ET.Element]:
    """Yield body paragraphs/tables without duplicating content inside tables."""
    for child in root:
        name = _local_name(child.tag)
        if name == "p":
            yield child
            # HWPX tables are commonly controls nested below a paragraph/run.
            # Yield only outermost tables; cell paragraphs are handled by the
            # table renderer and must not be emitted again as body paragraphs.
            for nested in child.iter():
                if nested is not child and _local_name(nested.tag) == "tbl":
                    yield nested
        elif name == "tbl":
            yield child
        elif name not in {"header", "footer"}:
            yield from _direct_content(child)


def inspect_hwpx(path: str | Path, limits: HwpxLimits | None = None) -> DocumentInspection:
    source = Path(path)
    validation = validate_hwpx(source, limits)
    blocks: list[DocumentBlock] = []
    warnings: list[str] = []
    table_count = 0
    control_count = 0
    image_count = 0
    with ZipFile(source) as archive:
        image_count = sum(
            1 for name in archive.namelist()
            if name.lower().startswith("bindata/") and not name.endswith("/")
        )
        for section_index, name in enumerate(validation["section_names"], 1):
            try:
                root = ET.fromstring(archive.read(name))
            except Exception as exc:
                raise HwpxSecurityError(f"본문 XML을 안전하게 읽지 못했습니다: {name}") from exc
            control_count += sum(
                1 for element in root.iter()
                if _local_name(element.tag) in {"ctrl", "container", "equation", "ole"}
            )
            for element in _direct_content(root):
                kind = _local_name(element.tag)
                if kind == "p":
                    text = _own_text(element).strip()
                    if text:
                        blocks.append(DocumentBlock("paragraph", text, _paragraph_level(text), section=section_index))
                elif kind == "tbl":
                    rows = _table_rows(element)
                    blocks.append(DocumentBlock("table", rows=rows, section=section_index))
                    table_count += 1
    plain_text = "\n".join(block.text for block in blocks if block.text)
    return DocumentInspection(
        path=str(source),
        blocks=blocks,
        section_count=len(validation["section_names"]),
        paragraph_count=sum(block.type == "paragraph" for block in blocks),
        table_count=table_count,
        image_count=image_count,
        control_count=control_count,
        text=plain_text,
        text_sha256=sha256(plain_text.encode("utf-8")).hexdigest(),
        warnings=warnings,
    )


def _markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    lines = ["| " + " | ".join(normalized[0]) + " |"]
    lines.append("| " + " | ".join(["---"] * width) + " |")
    lines.extend("| " + " | ".join(row) + " |" for row in normalized[1:])
    return "\n".join(lines)


def to_markdown(document: DocumentInspection) -> str:
    output = [f"<!-- HWP AutoDocFit Markdown export: {Path(document.path).name} -->", ""]
    for block in document.blocks:
        if block.type == "table":
            rendered = _markdown_table(block.rows or [])
            if rendered:
                output.extend((rendered, ""))
        elif block.text:
            prefix = "#" * block.level + " " if block.level else ""
            output.extend((prefix + block.text, ""))
    return "\n".join(output).rstrip() + "\n"


def export_markdown(source: str | Path, target: str | Path | None = None) -> Path:
    source = Path(source)
    target_path = Path(target) if target else source.with_suffix(".md")
    document = inspect_hwpx(source)
    target_path.write_text(to_markdown(document), encoding="utf-8")
    return target_path


def compare_documents(before: DocumentInspection, after: DocumentInspection) -> dict:
    similarity = SequenceMatcher(None, before.text, after.text, autojunk=False).ratio()
    issues: list[dict[str, str]] = []
    if after.paragraph_count == 0 and before.paragraph_count:
        issues.append({"severity": "error", "message": "결과 문서의 본문을 찾지 못했습니다."})
    elif before.text and len(after.text) < len(before.text) * 0.8:
        issues.append({"severity": "error", "message": "결과 문서의 본문 분량이 20% 이상 감소했습니다."})
    elif similarity < 0.9:
        issues.append({"severity": "warning", "message": f"본문 일치도가 낮습니다({similarity:.1%})."})
    for label, old, new in (
        ("표", before.table_count, after.table_count),
        ("이미지", before.image_count, after.image_count),
        ("섹션", before.section_count, after.section_count),
    ):
        if old != new:
            issues.append({"severity": "warning", "message": f"{label} 개수가 변경되었습니다({old} → {new})."})
    return {
        "ok": not any(item["severity"] == "error" for item in issues),
        "text_similarity": round(similarity, 6),
        "before": before.summary(),
        "after": after.summary(),
        "issues": issues,
    }
