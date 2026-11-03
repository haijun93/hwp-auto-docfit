"""PDF 문서 추출기 (pypdfium2 독점 잠금 및 페이지 자원 해제)."""
from __future__ import annotations

from pathlib import Path

from ..pdfium_guard import WAIT_SECONDS, try_exclusive
from .extractors import ExtractionError, ExtractionRecord

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None


def extract_pdf(path: Path | str, *, pdfium_module=None) -> list[ExtractionRecord]:
    """pypdfium2를 사용하여 페이지별 텍스트와 1-based 쪽 번호 위치를 추출한다.

    독점 잠금을 적용하며 문서와 페이지 객체는 예외 발생 여부와 무관하게 finally에서 닫힌다.
    """
    engine = pdfium_module or pdfium
    if engine is None:
        raise ExtractionError("runtime_unavailable", "PDF 지원에 필요한 pypdfium2 모듈 없음")

    file_path = Path(path)
    if not file_path.is_file():
        raise ExtractionError("corrupt", f"파일을 찾을 수 없음: {file_path}")

    with try_exclusive(WAIT_SECONDS) as acquired:
        if not acquired:
            raise ExtractionError("extract_failed", "PDFium 독점 잠금 획득 실패 (대기 시간 초과)")

        doc = None
        try:
            try:
                doc = engine.PdfDocument(str(file_path))
            except Exception as exc:
                msg = str(exc).lower()
                if any(term in msg for term in ("password", "encrypted", "암호")):
                    raise ExtractionError("encrypted", f"암호화된 PDF 문서: {exc}") from exc
                raise ExtractionError("corrupt", f"손상되었거나 열 수 없는 PDF: {exc}") from exc

            records: list[ExtractionRecord] = []
            seq = 1
            page_count = len(doc)

            for i in range(page_count):
                page = None
                textpage = None
                try:
                    page = doc.get_page(i)
                    if hasattr(page, "get_textpage"):
                        textpage = page.get_textpage()
                        text = textpage.get_text_range() if hasattr(textpage, "get_text_range") else ""
                    else:
                        text = page.extract_text() if hasattr(page, "extract_text") else ""

                    stripped = (text or "").strip()
                    if stripped:
                        records.append(
                            ExtractionRecord(
                                text=stripped,
                                location_kind="page",
                                location_label=f"{i + 1}쪽",
                                sequence=seq,
                                section=None,
                            )
                        )
                        seq += 1
                finally:
                    if textpage is not None and hasattr(textpage, "close"):
                        try:
                            textpage.close()
                        except Exception:
                            pass
                    if page is not None and hasattr(page, "close"):
                        try:
                            page.close()
                        except Exception:
                            pass

            if not records:
                raise ExtractionError("empty", "추출 가능한 PDF 텍스트가 없음")

            return records

        finally:
            if doc is not None and hasattr(doc, "close"):
                try:
                    doc.close()
                except Exception:
                    pass
