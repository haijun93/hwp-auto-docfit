"""TXT 및 MD 일반 텍스트 문서 추출기."""
from __future__ import annotations

import codecs
from pathlib import Path
from .extractors import ExtractionError, ExtractionRecord


def decode_text(raw: bytes) -> tuple[str, str]:
    """바이트 열의 인코딩을 판별하고 디코딩된 문자열과 인코딩명을 반환한다.

    순서: BOM 우선(UTF-8-SIG, UTF-16 LE/BE) -> UTF-8 strict -> CP949 strict.
    모두 실패하면 ExtractionError('decode_error', ...)를 발생시킨다.
    """
    if not raw:
        return "", "utf-8"

    if raw.startswith(codecs.BOM_UTF8):
        try:
            return raw.decode("utf-8-sig"), "utf-8-sig"
        except UnicodeError as exc:
            raise ExtractionError("decode_error", f"UTF-8 BOM 디코딩 실패: {exc}") from exc

    if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        try:
            return raw.decode("utf-16"), "utf-16"
        except UnicodeError as exc:
            raise ExtractionError("decode_error", f"UTF-16 BOM 디코딩 실패: {exc}") from exc

    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass

    try:
        return raw.decode("cp949"), "cp949"
    except UnicodeDecodeError as exc:
        raise ExtractionError("decode_error", f"텍스트 인코딩 판별 실패(UTF-8/CP949 모두 실패): {exc}") from exc


def extract_plain_text(path: Path | str) -> list[ExtractionRecord]:
    """TXT 및 MD 파일에서 줄 단위 위치를 포함한 추출 레코드를 생성한다."""
    file_path = Path(path)
    try:
        raw = file_path.read_bytes()
    except OSError as exc:
        raise ExtractionError("corrupt", f"파일을 읽을 수 없음: {exc}") from exc

    if not raw:
        raise ExtractionError("empty", "파일 내용이 비어 있음")

    text, _ = decode_text(raw)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    records: list[ExtractionRecord] = []
    seq = 1
    for line_idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped:
            records.append(
                ExtractionRecord(
                    text=stripped,
                    location_kind="line",
                    location_label=f"{line_idx}행",
                    sequence=seq,
                    section=None,
                )
            )
            seq += 1

    if not records:
        raise ExtractionError("empty", "추출 가능한 텍스트가 없음")
    return records
