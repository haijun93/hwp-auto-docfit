"""공용 파일포맷 변경 경로·형식 규칙."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from docfit_core.kordoc_bridge import SUPPORTED_INPUT_EXTENSIONS


def output_path_for(source: str | Path, target_format: str) -> Path:
    """원본 옆에 덮어쓰지 않는 결과 경로를 고른다."""
    source = Path(source)
    suffix = str(target_format or "").strip().lower().lstrip(".")
    if suffix not in {"hwpx", "pdf", "docx", "epub"}:
        raise ValueError("지원하는 결과 형식은 HWPX, PDF, DOCX 또는 EPUB입니다.")
    if source.is_symlink() or not source.is_file():
        raise ValueError("원본이 일반 파일이 아니거나 심볼릭 링크입니다.")
    if source.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
        raise ValueError(f"kordoc이 지원하지 않는 입력 형식입니다: {source.suffix or '(확장자 없음)'}")

    stem = source.stem
    marker = {"pdf": "(PDF변경)", "hwpx": "(HWPX변경)",
              "docx": "(DOCX변경)", "epub": "(EPUB변경)"}[suffix]
    candidate = source.with_name(f"{stem}{marker}.{suffix}")
    index = 2
    while candidate.exists():
        candidate = source.with_name(f"{stem}{marker} ({index}).{suffix}")
        index += 1
    return candidate


def convert_to_pandoc_format(source: str | Path, target: str | Path,
                             pandoc_executable: str | None = None) -> Path:
    """kordoc Markdown 파싱 후 Pandoc으로 DOCX/EPUB를 생성한다."""
    from docfit_core.kordoc_bridge import parse_document

    source, target = Path(source), Path(target)
    if source.is_symlink() or not source.is_file() or source.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
        raise ValueError("kordoc이 지원하는 일반 파일만 변환할 수 있습니다.")
    if target.suffix.lower() not in {".docx", ".epub"} or target.exists():
        raise ValueError("결과 경로가 잘못되었거나 이미 존재합니다.")
    pandoc = pandoc_executable or shutil.which("pandoc.exe") or shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("DOCX·EPUB 변환에는 Pandoc이 필요합니다. pandoc.org의 Windows 설치판을 설치해 주세요.")

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="docfit_pandoc_convert_") as folder:
        temp_dir = Path(folder)
        markdown = temp_dir / "document.md"
        parse_document(source, markdown, output_format="markdown", ocr=source.suffix.lower() == ".pdf")
        if not markdown.is_file():
            raise RuntimeError("kordoc 파싱 결과 Markdown 파일이 생성되지 않았습니다.")
        with tempfile.NamedTemporaryFile(prefix=".docfit_", suffix=target.suffix.lower(), dir=target.parent, delete=False) as stream:
            temp_output = Path(stream.name)
        temp_output.unlink()
        output_format = "epub3" if target.suffix.lower() == ".epub" else "docx"
        try:
            completed = subprocess.run(
                [pandoc, str(markdown), "--from=markdown", f"--to={output_format}",
                 f"--resource-path={temp_dir}", "--output", str(temp_output)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
                shell=False,
            )
            if completed.returncode != 0:
                message = (completed.stderr or completed.stdout or "Pandoc 변환 실패").strip()
                raise RuntimeError(message[-2000:])
            if not temp_output.is_file() or temp_output.stat().st_size == 0:
                raise RuntimeError("Pandoc 결과 파일이 생성되지 않았습니다.")
            os.link(temp_output, target)
        finally:
            temp_output.unlink(missing_ok=True)
    return target


def convert_hwpx_to_pdf(app, source: str | Path, target: str | Path) -> Path:
    """한/글 COM으로 HWPX를 PDF로 저장하고 PDF 서명·무덮어쓰기를 확인한다."""
    source, target = Path(source), Path(target)
    if source.is_symlink() or not source.is_file() or source.suffix.lower() != ".hwpx":
        raise ValueError("PDF 변환 원본은 일반 HWPX 파일이어야 합니다.")
    if target.suffix.lower() != ".pdf" or target.exists():
        raise ValueError("PDF 결과 경로가 잘못되었거나 이미 존재합니다.")
    source = source.resolve(strict=True)
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="docfit_pdf_", suffix=".pdf", dir=target.parent, delete=False) as stream:
        temporary = Path(stream.name)
    # 한/글의 SaveAs가 이미 존재하는 빈 파일에 덮어쓰기 질문을 띄우지 않도록
    # 고유 경로만 확보하고 실제 저장 직전 파일은 제거한다.
    temporary.unlink()
    opened = False
    try:
        if app.Open(str(source), "HWPX", "") is False:
            raise RuntimeError("한/글이 HWPX 문서를 열지 못했습니다.")
        opened = True
        if app.SaveAs(str(temporary), "PDF", "") is False:
            raise RuntimeError("한/글이 PDF로 저장하지 못했습니다.")
        with temporary.open("rb") as pdf_file:
            signature = pdf_file.read(5)
        if not temporary.is_file() or signature != b"%PDF-":
            raise RuntimeError("생성된 파일이 올바른 PDF가 아닙니다.")
        # hard link는 대상 이름이 작업 중 먼저 생성된 경우에도 덮어쓰지 않게 한다.
        os.link(temporary, target)
        return target
    finally:
        if opened:
            try:
                # 변환 전용 COM 세션에서 문서만 비운다. PDF 저장 후 일부 한/글
                # 버전의 FileClose가 저장 질문을 띄워 작업을 멈추는 것을 방지한다.
                app.Clear(1)
            except AttributeError:
                try:
                    app.Run("FileClose")
                except Exception:
                    pass
            except Exception:
                pass
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def convert_to_pdf(app, source: str | Path, target: str | Path) -> Path:
    """HWPX는 직접 PDF 저장, 다른 입력은 kordoc HWPX 중간 산출물로 렌더링한다."""
    import tempfile

    from docfit_core.kordoc_bridge import SUPPORTED_INPUT_EXTENSIONS, convert_to_hwpx

    source, target = Path(source), Path(target)
    if source.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
        raise ValueError("kordoc이 지원하지 않는 입력 형식입니다.")
    if source.suffix.lower() == ".hwpx":
        return convert_hwpx_to_pdf(app, source, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="docfit_pdf_source_") as folder:
        intermediate = Path(folder) / "source.hwpx"
        convert_to_hwpx(source, intermediate)
        return convert_hwpx_to_pdf(app, intermediate, target)
