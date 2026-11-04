"""EML 이메일 메시지 추출기 (RFC 헤더 및 본문 위치 분리)."""
from __future__ import annotations

import re
from email import policy
from email.parser import BytesParser
from pathlib import Path
from html.parser import HTMLParser

from .extractors import ExtractionError, ExtractionRecord


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str):
        if data:
            self.parts.append(data)

    def get_text(self) -> str:
        return " ".join(self.parts)


def _strip_html(html_content: str) -> str:
    """HTML 문자열에서 텍스트만 안전하게 추출한다."""
    try:
        parser = _HTMLTextExtractor()
        parser.feed(html_content)
        return parser.get_text()
    except Exception:
        return re.sub(r"<[^>]+>", " ", html_content)


def extract_eml(path: Path | str) -> list[ExtractionRecord]:
    """EML 파일에서 제목/발신/수신 및 본문 줄/문단 레코드를 추출한다.

    첨부 파일은 본문으로 색인하지 않으며, text/plain을 text/html보다 우선한다.
    """
    file_path = Path(path)
    try:
        raw = file_path.read_bytes()
    except OSError as exc:
        raise ExtractionError("corrupt", f"파일을 읽을 수 없음: {exc}") from exc

    if not raw.strip():
        raise ExtractionError("empty", "이메일 파일이 비어 있음")

    try:
        msg = BytesParser(policy=policy.default).parsebytes(raw)
    except Exception as exc:
        raise ExtractionError("corrupt", f"EML 메시지 파싱 실패: {exc}") from exc

    records: list[ExtractionRecord] = []
    seq = 1

    # 1. 헤더 (Subject, From, To)
    for header_name, label in (("subject", "제목"), ("from", "발신"), ("to", "수신")):
        val = msg.get(header_name)
        if val is not None:
            text = str(val).strip()
            if text:
                records.append(
                    ExtractionRecord(
                        text=text,
                        location_kind="message",
                        location_label=label,
                        sequence=seq,
                        section="헤더",
                    )
                )
                seq += 1

    # 2. 본문 (text/plain 우선, 없으면 text/html)
    plain_text = None
    html_text = None

    try:
        for part in msg.walk():
            if part.is_multipart():
                continue
            disp = part.get_content_disposition()
            if disp == "attachment":
                continue
            ctype = part.get_content_type()
            if ctype == "text/plain" and plain_text is None:
                try:
                    plain_text = part.get_content()
                except Exception as exc:
                    raise ExtractionError("decode_error", f"이메일 텍스트 디코딩 실패: {exc}") from exc
            elif ctype == "text/html" and html_text is None:
                try:
                    html_text = part.get_content()
                except Exception as exc:
                    raise ExtractionError("decode_error", f"이메일 HTML 디코딩 실패: {exc}") from exc
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("decode_error", f"이메일 파트 디코딩 실패: {exc}") from exc

    body = plain_text if plain_text is not None else (_strip_html(html_text) if html_text is not None else "")
    if body:
        normalized = body.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in normalized.split("\n") if line.strip()]
        for idx, line in enumerate(lines, 1):
            records.append(
                ExtractionRecord(
                    text=line,
                    location_kind="paragraph",
                    location_label=f"본문 문단 {idx}",
                    sequence=seq,
                    section="본문",
                )
            )
            seq += 1

    if not records:
        raise ExtractionError("empty", "추출 가능한 이메일 헤더 및 본문이 없음")

    return records
