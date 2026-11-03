"""HWP5 바이너리 문서 추출기 (kordoc 번들 브리지 기반, 한/글 COM 호출 없음)."""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from .. import kordoc_bridge
from .extractors import ExtractionError, ExtractionRecord


def extract_hwp(path: Path | str) -> list[ExtractionRecord]:
    """HWP5 문서를 kordoc 번들 런타임을 통해 마크다운으로 변환 후 레코드를 생성한다.

    한/글 COM을 절대 호출하지 않으며, 임의의 네트워크 설치를 시도하지 않는다.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise ExtractionError("corrupt", f"파일을 찾을 수 없음: {file_path}")

    with tempfile.TemporaryDirectory(prefix="tms_hwp_extract_") as tmpdir:
        target_md = Path(tmpdir) / "output.md"
        try:
            kordoc_bridge.parse_document(file_path, target_md, output_format="markdown")
        except kordoc_bridge.KordocUnavailableError as exc:
            raise ExtractionError("runtime_unavailable", f"kordoc 번들 런타임을 사용할 수 없음: {exc}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ExtractionError("extract_failed", f"kordoc 문서 변환 시간 초과: {exc}") from exc
        except Exception as exc:
            msg = str(exc).lower()
            if any(term in msg for term in ("암호", "password", "encrypted", "protect")):
                raise ExtractionError("encrypted", f"암호화된 HWP 문서: {exc}") from exc
            if any(term in msg for term in ("손상", "corrupt", "damaged", "invalid", "형식 오류")):
                raise ExtractionError("corrupt", f"손상된 HWP 문서: {exc}") from exc
            raise ExtractionError("extract_failed", f"HWP 문서 변환 실패: {exc}") from exc

        if not target_md.is_file():
            raise ExtractionError("extract_failed", "kordoc 변환 결과 파일이 생성되지 않음")

        try:
            content = target_md.read_text(encoding="utf-8")
        except UnicodeError as exc:
            raise ExtractionError("decode_error", f"변환된 마크다운 디코딩 실패: {exc}") from exc

    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.strip():
        raise ExtractionError("empty", "HWP 본문 텍스트가 없음")

    records: list[ExtractionRecord] = []
    seq = 1

    # 페이지 경계 패턴 (예: \f, <!-- page: 1 -->, <!-- Page 1 -->, <!-- page_break -->)
    page_marker_pattern = re.compile(
        r"(?:\f|<!--\s*page(?:\s*[:#]?\s*(\d+)|\s*break)?\s*-->)",
        re.IGNORECASE,
    )
    marker_matches = list(page_marker_pattern.finditer(normalized))
    if marker_matches:
        segments: list[tuple[int, str]] = []
        current_page = 1
        last_end = 0

        for m in marker_matches:
            chunk = normalized[last_end:m.start()]
            if last_end == 0 and not chunk.strip():
                # 문서 맨 앞의 페이지 마커인 경우 앞의 빈 영역은 건너뜀
                pass
            else:
                segments.append((current_page, chunk))
                current_page += 1

            # 마커에 명시적 쪽 번호가 있는 경우(예: <!-- page: 3 -->) 해당 번호로 갱신
            explicit_page = m.group(1)
            if explicit_page is not None:
                current_page = int(explicit_page)

            last_end = m.end()

        # 마지막 마커 이후 본문
        remaining_chunk = normalized[last_end:]
        segments.append((current_page, remaining_chunk))

        for page_num, chunk in segments:
            lines = [l.strip() for l in chunk.split("\n") if l.strip()]
            for line in lines:
                records.append(
                    ExtractionRecord(
                        text=line,
                        location_kind="page",
                        location_label=f"{page_num}쪽",
                        sequence=seq,
                        section=None,
                    )
                )
                seq += 1
    else:
        # 페이지 경계가 없으면 문단(단락) 단위 위치 부여
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", normalized) if p.strip()]
        for p_idx, para in enumerate(paragraphs, 1):
            records.append(
                ExtractionRecord(
                    text=para,
                    location_kind="paragraph",
                    location_label=f"문단 {p_idx}",
                    sequence=seq,
                    section=None,
                )
            )
            seq += 1

    if not records:
        raise ExtractionError("empty", "추출 가능한 HWP 본문이 없음")

    return records
