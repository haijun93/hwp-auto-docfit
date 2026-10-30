"""공용 파일 변환 경로·형식 규칙."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from docfit_core.kordoc_bridge import SUPPORTED_INPUT_EXTENSIONS

IMAGE_INPUT_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"})

# 그림 결과 형식(확장자 → Pillow 저장 형식). 한/글 PDF 저장본을 쪽마다 렌더링한다.
IMAGE_FORMATS = {"jpg": "JPEG", "png": "PNG"}
IMAGE_DPI = 150

# 결과 형식과 같은 형식의 입력(예: PDF→PDF)은 변환하지 않는다. PDF 압축(pdfz)은 PDF→PDF가 목적이라 뺀다.
SAME_FORMAT_SUFFIXES = {
    "hwpx": frozenset({".hwpx"}), "pdf": frozenset({".pdf"}), "docx": frozenset({".docx"}),
    "epub": frozenset({".epub"}), "html": frozenset({".html", ".htm"}), "jpg": frozenset({".jpg", ".jpeg"}),
    "png": frozenset({".png"}), "txt": frozenset({".txt"}), "md": frozenset({".md"}),
}


def is_same_format(source: str | Path, target_format: str) -> bool:
    return Path(source).suffix.lower() in SAME_FORMAT_SUFFIXES.get(str(target_format or "").lower(), ())
MAX_IMAGE_PAGES = 500
MAX_IMAGE_SIDE = 6000


def output_path_for(source: str | Path, target_format: str) -> Path:
    """원본 옆에 덮어쓰지 않는 결과 경로를 고른다."""
    source = Path(source)
    suffix = str(target_format or "").strip().lower().lstrip(".")
    if suffix not in CONVERSION_OUTPUTS:
        raise ValueError("지원하는 결과 형식은 HWPX, PDF, PDF 압축, DOCX, EPUB, HTML, JPG, PNG, TXT 또는 MD입니다.")
    if source.is_symlink() or not source.is_file():
        raise ValueError("원본이 일반 파일이 아니거나 심볼릭 링크입니다.")
    if source.suffix.lower() not in CONVERSION_INPUTS:
        raise ValueError(f"변환할 수 없는 입력 형식입니다: {source.suffix or '(확장자 없음)'}")

    stem = source.stem
    marker = f"({suffix.upper()}변경)"
    if suffix == "pdfz":
        # PDF 압축은 PDF만 받아 같은 PDF로 저장한다(재조판 없이 그림·스트림만 다시 저장).
        if source.suffix.lower() != ".pdf":
            raise ValueError("PDF 압축은 PDF 파일에만 쓸 수 있습니다.")
        suffix, marker = "pdf", "(PDF압축)"
    candidate = source.with_name(f"{stem}{marker}.{suffix}")
    index = 2
    # 여러 쪽 그림은 확장자를 뺀 같은 이름의 폴더에 저장하므로 폴더 이름도 비어 있어야 한다.
    while candidate.exists() or (suffix in IMAGE_FORMATS and candidate.with_suffix("").exists()):
        candidate = source.with_name(f"{stem}{marker} ({index}).{suffix}")
        index += 1
    return candidate


def _pandoc_executable(explicit: str | None = None) -> str:
    pandoc = explicit
    if not pandoc:
        from docfit_core.kordoc_runtime import ensure_pandoc
        pandoc = ensure_pandoc()
    pandoc = pandoc or shutil.which("pandoc.exe") or shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("내장 Pandoc을 사용할 수 없습니다. 앱 설치 파일이 손상되지 않았는지 확인해 주세요.")
    return pandoc


def convert_to_pandoc_format(source: str | Path, target: str | Path,
                             pandoc_executable: str | None = None) -> Path:
    """Convert supported sources to DOCX, EPUB, or standalone HTML with Pandoc."""
    from docfit_core.kordoc_bridge import parse_document

    source, target = Path(source), Path(target)
    if source.is_symlink() or not source.is_file() or source.suffix.lower() not in CONVERSION_INPUTS:
        raise ValueError("지원하는 문서 파일만 변환할 수 있습니다.")
    if target.suffix.lower() not in {".docx", ".epub", ".html", ".htm", ".md", ".txt"} or target.exists():
        raise ValueError("결과 경로가 잘못되었거나 이미 존재합니다.")
    pandoc = _pandoc_executable(pandoc_executable)

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="docfit_pandoc_convert_") as folder:
        temp_dir = Path(folder)
        markdown = temp_dir / "document.md"
        source_suffix = source.suffix.lower()
        if source_suffix in HTML_INPUTS | TEXT_INPUTS and source.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("HTML·TXT·MD 파일은 16MB 이하만 변환할 수 있습니다.")
        output_format = {".epub": "epub3", ".html": "html5", ".htm": "html5",
                         ".docx": "docx", ".md": "markdown", ".txt": "plain"}[target.suffix.lower()]
        if source_suffix in HTML_INPUTS | TEXT_INPUTS:
            input_format = "html" if source_suffix in HTML_INPUTS else "markdown"
            source_arg = str(source.resolve(strict=True))
            resource_path = str(temp_dir)
            markdown = None
        elif source_suffix in IMAGE_INPUT_EXTENSIONS:
            intermediate = temp_dir / "source.hwpx"
            convert_input_to_hwpx(source, intermediate)
            parse_document(intermediate, markdown, output_format="markdown")
            input_format, source_arg, resource_path = "markdown", str(markdown), str(temp_dir)
        else:
            parse_document(source, markdown, output_format="markdown", ocr=source_suffix == ".pdf")
            input_format, source_arg, resource_path = "markdown", str(markdown), str(temp_dir)
        if markdown is not None and not markdown.is_file():
            raise RuntimeError("문서를 읽은 결과가 만들어지지 않았습니다.")
        with tempfile.NamedTemporaryFile(prefix=".docfit_", suffix=target.suffix.lower(), dir=target.parent, delete=False) as stream:
            temp_output = Path(stream.name)
        temp_output.unlink()
        try:
            completed = subprocess.run(
                [pandoc, source_arg, f"--from={input_format}", f"--to={output_format}",
                 *( ["--standalone", "--embed-resources"] if target.suffix.lower() in {".html", ".htm"} else [] ),
                 f"--resource-path={resource_path}", "--output", str(temp_output)],
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


# 한/글이 직접 열어 PDF로 저장하는 입력 형식(확장자 → 한/글 Open 형식 이름).
HANCOM_PDF_DIRECT = {".hwpx": "HWPX", ".hwp": "HWP"}


def convert_hwpx_to_pdf(app, source: str | Path, target: str | Path) -> Path:
    """한/글 COM으로 HWPX·HWP를 PDF로 저장하고 PDF 서명·무덮어쓰기를 확인한다."""
    source, target = Path(source), Path(target)
    open_format = HANCOM_PDF_DIRECT.get(source.suffix.lower())
    if source.is_symlink() or not source.is_file() or open_format is None:
        raise ValueError("PDF 변환 원본은 일반 HWPX 또는 HWP 파일이어야 합니다.")
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
        # 암호 문서는 숨은 암호 창에서 멈추지 않고 바로 실패한다(2.0.7).
        if app.Open(str(source), open_format, "suspendpassword:true") is False:
            raise RuntimeError(f"한/글이 {open_format} 문서를 열지 못했습니다(암호 문서이면 암호를 풀고 다시 시도하세요).")
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
    """HWPX·HWP는 직접 PDF 저장, 다른 입력은 kordoc HWPX 중간 산출물로 렌더링한다."""
    import tempfile

    from docfit_core.kordoc_bridge import SUPPORTED_INPUT_EXTENSIONS, convert_to_hwpx

    source, target = Path(source), Path(target)
    if source.suffix.lower() not in CONVERSION_INPUTS:
        raise ValueError("변환할 수 없는 입력 형식입니다.")
    if source.suffix.lower() in HANCOM_PDF_DIRECT:
        return convert_hwpx_to_pdf(app, source, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="docfit_pdf_source_") as folder:
        intermediate = Path(folder) / "source.hwpx"
        convert_input_to_hwpx(source, intermediate)
        return convert_hwpx_to_pdf(app, intermediate, target)


def convert_to_images(app, source: str | Path, target: str | Path, *, dpi: int = IMAGE_DPI) -> Path:
    """한/글로 PDF를 만든 뒤 쪽마다 JPG·PNG 그림으로 저장한다.

    한 쪽 문서는 target 파일 하나, 여러 쪽 문서는 target에서 확장자를 뺀 새 폴더에
    '이름-001.jpg'처럼 쪽 번호를 붙여 저장하고 그 경로를 돌려준다. 기존 파일은 덮어쓰지 않는다.
    """
    import pypdfium2 as pdfium

    source, target = Path(source), Path(target)
    kind = target.suffix.lower().lstrip(".")
    if kind not in IMAGE_FORMATS:
        raise ValueError("그림 결과 형식은 JPG 또는 PNG만 사용할 수 있습니다.")
    folder = target.with_suffix("")
    if target.exists() or folder.exists():
        raise ValueError("그림 결과 경로가 이미 존재합니다.")
    created: list[Path] = []
    made_folder = False
    with tempfile.TemporaryDirectory(prefix="docfit_image_") as work:
        # PDF는 이미 쪽 배치가 있으므로 다시 조판하지 않고 그대로 쪽마다 그린다(한/글·변환 엔진 불필요).
        pdf = source if source.suffix.lower() == ".pdf" else convert_to_pdf(app, source, Path(work) / "render.pdf")
        document = pdfium.PdfDocument(str(pdf))
        try:
            count = len(document)
            if count == 0:
                raise RuntimeError("그림으로 바꿀 쪽이 없습니다.")
            if count > MAX_IMAGE_PAGES:
                raise RuntimeError(f"그림 변환은 {MAX_IMAGE_PAGES}쪽까지 지원합니다(현재 {count}쪽).")
            if count == 1:
                outputs = [target]
            else:
                folder.mkdir(parents=True, exist_ok=False)
                made_folder = True
                outputs = [folder / f"{target.stem}-{index:03d}.{kind}" for index in range(1, count + 1)]
            try:
                for index, output in enumerate(outputs):
                    page = document[index]
                    try:
                        width, height = page.get_size()
                        scale = min(dpi / 72, MAX_IMAGE_SIDE / max(width, height, 1))
                        bitmap = page.render(scale=scale)
                        try:
                            image = bitmap.to_pil()
                            if kind == "jpg":
                                image = image.convert("RGB")
                            with output.open("xb") as stream:
                                created.append(output)
                                if kind == "jpg":
                                    image.save(stream, IMAGE_FORMATS[kind], quality=92)
                                else:
                                    image.save(stream, IMAGE_FORMATS[kind], optimize=True)
                        finally:
                            bitmap.close()
                    finally:
                        page.close()
            except BaseException:
                for output in created:
                    output.unlink(missing_ok=True)
                if made_folder:
                    try:
                        folder.rmdir()
                    except OSError:
                        pass
                raise
        finally:
            document.close()
    return target if count == 1 else folder


def convert_hwp_to_hwpx(app, source: str | Path, target: str | Path) -> Path:
    """한/글 내장 저장으로 HWP를 HWPX 사본으로 변환한다. 외부 변환기 불필요."""
    from docfit_core.hwpx import validate_hwpx
    source, target = Path(source), Path(target)
    if source.is_symlink() or not source.is_file() or source.suffix.lower() != ".hwp":
        raise ValueError("일반 HWP 원본 파일을 선택해 주세요.")
    if target.suffix.lower() != ".hwpx" or target.exists() or target.is_symlink():
        raise ValueError("HWPX 결과 경로가 잘못되었거나 이미 존재합니다.")
    source, target = source.resolve(strict=True), target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="docfit_hwp_", suffix=".hwpx", dir=target.parent, delete=False) as stream:
        temporary = Path(stream.name)
    temporary.unlink()
    opened = False
    try:
        opened = True  # Failed Open may still leave a partial COM document.
        if app.Open(str(source), "HWP", "forceopen:true;suspendpassword:true") is False:
            raise RuntimeError("한/글에서 HWP 원본을 열지 못했습니다. 암호 문서는 'HWP 찾아 HWPX로'에서 암호를 넣어 변환하세요.")
        if app.SaveAs(str(temporary), "HWPX", "") is False:
            raise RuntimeError("한/글에서 HWPX 저장을 완료하지 못했습니다.")
        validate_hwpx(temporary)
        os.link(temporary, target)
        return target
    finally:
        if opened:
            try:
                app.Run("FileClose")
            except Exception:
                pass
        temporary.unlink(missing_ok=True)


TEXT_INPUTS = frozenset({".txt", ".md"})
HTML_INPUTS = frozenset({".html", ".htm"})
CONVERSION_INPUTS = SUPPORTED_INPUT_EXTENSIONS | TEXT_INPUTS | IMAGE_INPUT_EXTENSIONS | HTML_INPUTS
CONVERSION_OUTPUTS = frozenset({"hwpx", "pdf", "pdfz", "pdfm", "docx", "epub", "html", "jpg", "png", "txt", "md"})


def convert_input_to_hwpx(source: str | Path, target: str | Path) -> Path:
    """Render Markdown/text without sending plain text to a document parser."""
    import re
    from docfit_core.kordoc_bridge import convert_to_hwpx, generate_hwpx
    from docfit_core.hwpx import validate_hwpx
    source, target = Path(source), Path(target)
    if source.suffix.lower() in IMAGE_INPUT_EXTENSIONS:
        return convert_image_to_hwpx(source, target)
    if source.suffix.lower() in HTML_INPUTS:
        if source.is_symlink() or not source.is_file() or source.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("HTML 파일은 16MB 이하의 일반 파일이어야 합니다.")
        pandoc = _pandoc_executable()
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="docfit_html_") as folder:
            markdown = Path(folder) / "source.md"
            subprocess.run([pandoc, str(source.resolve(strict=True)), "--from=html", "--to=markdown",
                            f"--resource-path={folder}", "--output", str(markdown)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=600, check=True, shell=False)
            return convert_input_to_hwpx(markdown, target)
    if source.suffix.lower() not in TEXT_INPUTS:
        return convert_to_hwpx(source, target)
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("16MB 이하의 일반 TXT·MD 파일을 선택해 주세요.")
    if target.suffix.lower() != ".hwpx" or target.exists() or target.is_symlink():
        raise ValueError("새 HWPX 결과 경로를 선택해 주세요.")
    with source.open("rb") as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("TXT·MD 파일 크기가 16MB를 초과합니다.")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16")
    else:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("cp949")
    if source.suffix.lower() == ".txt":
        import string
        pattern = "([" + re.escape(string.punctuation) + "])"
        text = "\n".join(re.sub(pattern, r"\\\1", line) + "  " for line in text.splitlines())
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="docfit_text_") as folder:
        markdown = Path(folder) / "source.md"
        markdown.write_text(text, encoding="utf-8")
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".hwpx", delete=False) as stream:
            temporary = Path(stream.name)
        temporary.unlink()
        try:
            generate_hwpx(markdown, "보고서", temporary)
            validate_hwpx(temporary)
            os.link(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return target


def convert_image_to_hwpx(source: str | Path, target: str | Path) -> Path:
    """Normalize image frames, parse with kordoc Korean OCR, generate editable HWPX.

    Animated GIF/multipage TIFF frames are processed in order (maximum 100).
    OCR reconstructs text; it cannot guarantee the original scan's typography.
    """
    import warnings
    from PIL import Image, ImageOps
    from docfit_core.hwpx import validate_hwpx
    from docfit_core.kordoc_bridge import ocr_available, parse_document, generate_hwpx, KordocUnavailableError, OCR_UNAVAILABLE_MESSAGE
    source, target = Path(source), Path(target)
    if (source.suffix.lower() not in IMAGE_INPUT_EXTENSIONS or source.is_symlink()
            or not source.is_file() or source.stat().st_size > 64 * 1024 * 1024):
        raise ValueError("64MB 이하의 일반 이미지 파일을 선택해 주세요.")
    if target.suffix.lower() != ".hwpx" or target.exists() or target.is_symlink():
        raise ValueError("새 HWPX 결과 경로를 선택해 주세요.")
    if not ocr_available():
        raise KordocUnavailableError(OCR_UNAVAILABLE_MESSAGE)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="docfit_ocr_") as folder:
        work = Path(folder)
        texts = []
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(source) as image:
                count = getattr(image, "n_frames", 1)
                if count > 100:
                    raise ValueError("이미지는 파일당 100프레임까지 변환할 수 있습니다.")
                total_pixels = 0
                for index in range(count):
                    image.seek(index)
                    pixels = image.width * image.height
                    total_pixels += pixels
                    if pixels > 30_000_000 or total_pixels > 120_000_000:
                        raise ValueError("이미지 해상도가 제한을 넘습니다(프레임 3천만, 전체 1억 2천만 화소).")
                    with ImageOps.exif_transpose(image) as oriented:
                        with oriented.convert("RGBA") as rgba:
                            with Image.new("RGB", rgba.size, "white") as rgb:
                                rgb.paste(rgba, mask=rgba.getchannel("A"))
                                normalized = work / f"frame-{index + 1:03d}.png"
                                rgb.save(normalized, "PNG")
                    parsed = work / f"frame-{index + 1:03d}.md"
                    parse_document(normalized, parsed, ocr=True)
                    text = parsed.read_text(encoding="utf-8").strip()
                    if not text:
                        raise RuntimeError(f"{index + 1}번째 이미지에서 글자를 인식하지 못했습니다. 해상도·회전·대비를 확인해 주세요.")
                    texts.append(text)
        markdown = work / "document.md"
        markdown.write_text("\n\n---\n\n".join(texts), encoding="utf-8")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".hwpx", delete=False) as stream:
                temporary = Path(stream.name)
            temporary.unlink()
            generate_hwpx(markdown, "보고서", temporary, image_dir=work)
            validate_hwpx(temporary)
            os.link(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return target


def convert_hwpx_to_text(source: str | Path, target: str | Path) -> Path:
    """Export ordered paragraphs/tables using the safe HWPX parser, without COM."""
    from docfit_core.hwpx import inspect_hwpx, to_markdown
    source, target = Path(source), Path(target)
    if source.suffix.lower() != ".hwpx" or source.is_symlink() or not source.is_file():
        raise ValueError("일반 HWPX 원본을 선택해 주세요.")
    if target.suffix.lower() not in TEXT_INPUTS or target.exists() or target.is_symlink():
        raise ValueError("새 TXT·MD 결과 경로를 선택해 주세요.")
    document = inspect_hwpx(source)
    if target.suffix.lower() == ".md":
        text = to_markdown(document)
    else:
        text = "\n\n".join("\n".join("\t".join(row) for row in block.rows) if block.rows is not None else block.text for block in document.blocks)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target
