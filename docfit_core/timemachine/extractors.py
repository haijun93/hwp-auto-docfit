"""타임머신 다형식 본문 추출 계약 및 디스패처."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

LocationKind = Literal["page", "sheet_row", "paragraph", "line", "message"]
VALID_REASON_CODES = frozenset({
    "unsupported",
    "encrypted",
    "corrupt",
    "empty",
    "runtime_unavailable",
    "decode_error",
    "extract_failed",
})


@dataclass(frozen=True)
class ExtractionRecord:
    text: str
    location_kind: LocationKind
    location_label: str  # 예: "3쪽", "매출 12행", "문단 4", "8행", "본문"
    sequence: int  # 문서 내 1부터 시작하는 안정적 순서
    section: str | None = None  # 시트명, 헤더/본문 구분, HWP 섹션 등
    hierarchy_level: str | None = None
    is_table_cell: bool = False
    style_name: str | None = None
    outline_level: int | None = None


class ExtractionError(ValueError):
    """문서 추출 중 발생하는 정규화된 오류."""

    def __init__(self, reason_code: str, message: str):
        super().__init__(f"{reason_code}: {message}")
        self.reason_code = reason_code
        self.message = message

    def __str__(self) -> str:
        return f"{self.reason_code}: {self.message}"


def records_to_text(records: list[ExtractionRecord]) -> str:
    """추출 기록을 FTS 본문 및 기존 검색 스니펫용 합성 문자열로 변환한다."""
    chunks: list[str] = []
    for record in records:
        stripped = record.text.strip()
        if not stripped:
            continue
        if record.location_label:
            chunks.append(f"⟦{record.location_label}⟧ {stripped}")
        else:
            chunks.append(stripped)
    return "\n".join(chunks)


def extract_document(path: str | Path, *, hierarchy_records: list | None = None) -> list[ExtractionRecord]:
    """확장자별 추출기를 호출해 위치가 보존된 추출 기록 목록을 돌려준다."""
    p = Path(path)
    ext = p.suffix.lower().lstrip(".")
    if not ext:
        raise ExtractionError("unsupported", f"확장자가 없는 파일: {p.name}")

    if ext in ("txt", "md"):
        from .extractors_text import extract_plain_text
        records = extract_plain_text(p)
        return _apply_hierarchy(records, hierarchy_records)
    elif ext == "hwpx":
        from .extractors_hwpx import extract_hwpx
        records = extract_hwpx(p, hierarchy_records=hierarchy_records)
        return records
    elif ext == "hwp":
        from .extractors_hwp import extract_hwp
        records = extract_hwp(p)
        return _apply_hierarchy(records, hierarchy_records)
    elif ext == "docx":
        from .extractors_ooxml import extract_docx
        records = extract_docx(p)
        return _apply_hierarchy(records, hierarchy_records)
    elif ext == "pptx":
        from .extractors_ooxml import extract_pptx
        records = extract_pptx(p)
        return _apply_hierarchy(records, hierarchy_records)
    elif ext == "xlsx":
        from .extractors_ooxml import extract_xlsx
        records = extract_xlsx(p)
        return _apply_hierarchy(records, hierarchy_records)
    elif ext == "xls":
        from .extractors_ooxml import extract_xls
        records = extract_xls(p)
        return _apply_hierarchy(records, hierarchy_records)
    elif ext == "pdf":
        from .extractors_pdf import extract_pdf
        records = extract_pdf(p)
        return _apply_hierarchy(records, hierarchy_records)
    elif ext == "eml":
        from .extractors_eml import extract_eml
        records = extract_eml(p)
        return _apply_hierarchy(records, hierarchy_records)
    else:
        raise ExtractionError("unsupported", f"지원하지 않는 문서 형식: .{ext}")


def _apply_hierarchy(records: list[ExtractionRecord], hierarchy_records: list | None) -> list[ExtractionRecord]:
    """기존 HWPX/Office 구조 판정 결과를 추출 위치 레코드에 결합한다."""
    if not hierarchy_records:
        return records
    by_text: dict[str, list] = {}
    for item in hierarchy_records:
        by_text.setdefault(item.text.strip(), []).append(item)
    merged = []
    for record in records:
        candidates = by_text.get(record.text.strip())
        item = candidates.pop(0) if candidates else None
        if item is None:
            merged.append(record)
        else:
            merged.append(ExtractionRecord(
                text=record.text, location_kind=record.location_kind,
                location_label=record.location_label, sequence=record.sequence,
                section=record.section, hierarchy_level=item.level,
                is_table_cell=item.is_table_cell, style_name=item.style_name,
                outline_level=item.outline_level,
            ))
    return merged


