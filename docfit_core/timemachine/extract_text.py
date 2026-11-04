"""하위 호환 텍스트 추출 façade."""
from __future__ import annotations

from pathlib import Path
from .extractors import extract_document, records_to_text, ExtractionError


def extract_text(path: str | Path) -> str:
    """기존 content_search.extract_text 호출자를 위한 호환 함수.

    extract_document()로 레코드를 추출한 뒤 records_to_text()로 합성된 문자열을 반환한다.
    추출된 본문이 없으면 ExtractionError('empty', ...)를 발생시킨다.
    """
    records = extract_document(path)
    text = records_to_text(records)
    if not text.strip():
        raise ExtractionError("empty", "추출 가능한 본문 텍스트가 없음")
    return text
