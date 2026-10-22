"""UI와 CLI가 함께 쓰는 파일 변환 실행기. progress는 기존 GUI 이벤트 튜플을 받는다."""
from pathlib import Path
import shutil
import threading


def _runtime():
    # UI 부트스트랩 없이 기존 엔진의 독립 COM 생성 함수를 바인딩한다.
    import pythoncom
    import win32com.client as win32
    from docfit_engine.runtime import resolve
    from docfit_core.format_samples import REGISTRY_VALUE
    runtime = dict(win32=win32, pythoncom=pythoncom,
                   REGISTER_MODULE_NAME='FilePathCheckDLL', REGISTER_MODULE_VALUE=REGISTRY_VALUE)
    runtime['한글_COM_인스턴스_생성'] = resolve('docfit_engine.com_driver', '한글_COM_인스턴스_생성', runtime)
    return runtime


def run_conversion(files, target, output_dir=None, progress=None, stop_event=None, *, runtime_factory=None, log=None):
    """변환 결과 dict 목록을 반환한다. 원본과 기존 결과는 덮어쓰지 않는다."""
    from docfit_core.file_conversion import (
        IMAGE_FORMATS, CONVERSION_OUTPUTS, convert_input_to_hwpx, convert_hwpx_to_text,
        convert_hwp_to_hwpx, convert_to_images, convert_to_pandoc_format, convert_to_pdf, output_path_for,
        is_same_format, IMAGE_INPUT_EXTENSIONS,
    )

    files = [str(Path(f).resolve()) for f in files]
    target_format = str(target).lower()
    if target_format not in CONVERSION_OUTPUTS:
        raise ValueError('지원하지 않는 결과 형식입니다.')
    if not files:
        return []
    if target_format == 'pdfm' and len(files) < 2:
        raise ValueError('PDF 합치기는 파일이 2개 이상 필요합니다.')
    중단_event = stop_event or threading.Event()
    runtime_factory = runtime_factory or _runtime
    로그 = log or (lambda message: None)
    results = []

    class Events:
        def put(self, event):
            if event[0] == 'saved':
                results.append(dict(source=event[1], output=event[2], status='success', error=None))
            elif event[0] == 'document_error':
                results.append(dict(source=event[1], output=None,
                                    status='skipped' if is_same_format(event[1], target_format) else 'failed', error=event[2]))
            elif event[0] == 'fatal_error':
                results.append(dict(source=None, output=None, status='failed', error=event[1]))
            if progress:
                progress(event)
    gui_queue = Events()

    def relocate(path):
        if output_dir is None:
            return path
        folder = Path(output_dir).resolve()
        folder.mkdir(parents=True, exist_ok=True)
        candidate = folder / path.name
        base, index = candidate, 2
        while candidate.exists() or candidate.with_suffix('').exists() or str(candidate) in files:
            candidate = base.with_name(f'{base.stem} ({index}){base.suffix}')
            index += 1
        return candidate
    successes, failures = 0, 0
    app = None
    com_initialized = False
    # PDF 하나로 합치기(pdfm): PDF·그림은 그대로, 나머지는 한/글로 임시 PDF를 만든 뒤 순서대로 합친다.
    합칠_부분, 합치기_임시 = [], None
    합치기_한글필요 = target_format == "pdfm" and any(
        Path(f).suffix.lower() != ".pdf" and Path(f).suffix.lower() not in IMAGE_INPUT_EXTENSIONS for f in files)
    try:
        변환할_파일 = [f for f in files if not is_same_format(f, target_format)]
        그림_한글필요 = target_format in IMAGE_FORMATS and any(Path(f).suffix.lower() != ".pdf" for f in 변환할_파일)
        if (target_format == "pdf" and 변환할_파일) or 합치기_한글필요 or 그림_한글필요 or (target_format == "hwpx" and any(Path(f).suffix.lower() == ".hwp" for f in files)):
            runtime = runtime_factory()
            pythoncom = runtime["pythoncom"]
            한글_COM_인스턴스_생성 = runtime["한글_COM_인스턴스_생성"]
            REGISTER_MODULE_NAME = runtime["REGISTER_MODULE_NAME"]
            REGISTER_MODULE_VALUE = runtime["REGISTER_MODULE_VALUE"]
            pythoncom.CoInitialize()
            com_initialized = True
            app = 한글_COM_인스턴스_생성(독립=True)
            if app.RegisterModule(REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE) is False:
                raise RuntimeError("앱에 포함된 한/글 보안 모듈을 등록하지 못했습니다.")
            try:
                app.Visible = False
            except Exception:
                pass
        for number, source_text in enumerate(files, 1):
            if 중단_event.is_set():
                break
            source = Path(source_text)
            gui_queue.put(("doc_begin", number, len(files), source.name))
            if target_format != "pdfm" and is_same_format(source, target_format):
                # 이미 결과와 같은 형식이면 바꾸지 않는다(예: PDF→PDF, 2026-10-22 사용자 지시).
                gui_queue.put(("document_error", str(source), f"이미 {target_format.upper()} 파일이라 건너뛰었습니다."))
                로그(f"파일 변환 건너뜀(같은 형식): {source.name}")
                failures += 1   # 실패 목록·완료 문구의 수가 맞도록 건너뛴 파일도 '처리 못 함'으로 센다
                continue
            if target_format == "pdfm":
                try:
                    if source.suffix.lower() == ".pdf" or source.suffix.lower() in IMAGE_INPUT_EXTENSIONS:
                        합칠_부분.append((source.name, source))
                    else:
                        if 합치기_임시 is None:
                            import tempfile as _tempfile
                            합치기_임시 = Path(_tempfile.mkdtemp(prefix="docfit_merge_parts_"))
                        임시_pdf = 합치기_임시 / f"{number:04d}.pdf"
                        convert_to_pdf(app, source, 임시_pdf)
                        합칠_부분.append((source.name, 임시_pdf))
                    successes += 1
                except Exception as exc:
                    failures += 1
                    if app is not None:
                        try:
                            app.Clear(1)
                        except Exception:
                            pass
                    gui_queue.put(("document_error", str(source), str(exc)))
                    로그(f"PDF 합치기 준비 실패: {source.name} — {exc}")
                continue
            try:
                target = relocate(output_path_for(source, target_format))
                if target_format == "hwpx":
                    if source.suffix.lower() == ".hwp":
                        convert_hwp_to_hwpx(app, source, target)
                    else:
                        convert_input_to_hwpx(source, target)
                elif target_format in {"txt", "md"} and source.suffix.lower() == ".hwpx":
                    convert_hwpx_to_text(source, target)
                elif target_format in {"txt", "md", "docx", "epub", "html"}:
                    convert_to_pandoc_format(source, target)
                elif target_format in IMAGE_FORMATS:
                    target = convert_to_images(app, source, target)
                elif target_format == "pdfz":
                    from docfit_core.pdf_compress import compress_pdf
                    압축결과 = compress_pdf(source, target)
                    로그(f"PDF 압축: {source.name} {압축결과.summary()}")
                else:
                    convert_to_pdf(app, source, target)
                successes += 1
                gui_queue.put(("saved", str(source), str(target), None))
                로그(f"파일 변환 완료: {source.name} → {target.name}")
            except Exception as exc:
                failures += 1
                if app is not None:
                    try:
                        app.Clear(1)
                    except Exception:
                        pass
                gui_queue.put(("document_error", str(source), str(exc)))
                로그(f"파일 변환 실패: {source.name} — {exc}")
        if target_format == "pdfm" and not 중단_event.is_set():
            from docfit_core.pdf_merge import merge_to_pdf, merged_output_path
            첫_원본 = str(files[0])
            if failures:
                # 일부가 빠진 합본은 만들지 않는다(쪽이 빠진 문서를 완성본으로 착각하지 않게).
                gui_queue.put(("document_error", 첫_원본, f"파일 {failures}개를 PDF로 바꾸지 못해 합치지 않았습니다."))
                successes = 0
            elif 합칠_부분:
                try:
                    합본 = merge_to_pdf(합칠_부분, relocate(merged_output_path([Path(f) for f in files])))
                    gui_queue.put(("saved", 첫_원본, str(합본.target), None))
                    로그(f"PDF 하나로 합치기 완료: {합본.target.name} ({합본.summary()})")
                    successes = 1
                except Exception as exc:
                    failures, successes = failures + 1, 0
                    gui_queue.put(("document_error", 첫_원본, str(exc)))
                    로그(f"PDF 하나로 합치기 실패: {exc}")
        if 중단_event.is_set():
            if target_format == "pdfm":
                successes = 0   # 중단하면 합본을 만들지 않으므로 성공으로 세지 않는다
            gui_queue.put(("file_conversion_stopped", successes, failures))
        else:
            gui_queue.put(("file_conversion_finished", successes, failures))
    except Exception as exc:
        gui_queue.put(("fatal_error", str(exc)))
    finally:
        if 합치기_임시 is not None:
            shutil.rmtree(합치기_임시, ignore_errors=True)
        if app is not None:
            try:
                app.Clear(1)
                app.Quit()
            except Exception:
                pass
        if com_initialized:
            pythoncom.CoUninitialize()

    return results
