"""실제 한/글 COM의 내장 PDF 저장을 사본으로 시험한다(추가 변환기 사용 없음)."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import shutil
import sys
from time import perf_counter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", required=True, type=Path, help="새 시험 결과 폴더")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("Windows와 한/글 COM 환경에서 실행하세요.")
    source = args.source.resolve(strict=True)
    if source.suffix.lower() != ".hwpx":
        parser.error("HWPX 시험 문서를 지정하세요.")
    from pypdf import PdfReader  # 시험 전용 의존성; PDF 변환 엔진에는 사용하지 않는다.

    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    from docfit_core.file_conversion import convert_to_pdf
    from docfit_core.hwpx import validate_hwpx

    validate_hwpx(source)
    original_hash = sha256(source.read_bytes()).hexdigest()
    args.out.mkdir(parents=True, exist_ok=False)
    copied = args.out / "source.hwpx"
    shutil.copy2(source, copied)
    target = args.out / "result.pdf"
    namespace = runpy.run_path(str(repo / "hwp-auto-docfit.py"), run_name="pdf_smoke")
    pythoncom = namespace["pythoncom"]
    pythoncom.CoInitialize()
    app = None
    started = perf_counter()
    try:
        app = namespace["한글_COM_인스턴스_생성"](독립=True)
        if not app.RegisterModule(namespace["REGISTER_MODULE_NAME"], namespace["REGISTER_MODULE_VALUE"]):
            raise RuntimeError("앱에 포함된 한/글 보안 모듈을 등록하지 못했습니다.")
        convert_to_pdf(app, copied, target)
    finally:
        try:
            if app is not None:
                try:
                    app.Clear(1)
                finally:
                    app.Quit()
        finally:
            pythoncom.CoUninitialize()
    reader = PdfReader(target)
    report = {
        "engine": "Hancom COM built-in PDF",
        "extra_converter_used": False,
        "pdf_pages": len(reader.pages),
        "pdf_bytes": target.stat().st_size,
        "text": "\n".join(page.extract_text() or "" for page in reader.pages),
        "source_unchanged": sha256(source.read_bytes()).hexdigest() == original_hash,
        "copy_unchanged": sha256(copied.read_bytes()).hexdigest() == original_hash,
        "seconds": round(perf_counter() - started, 3),
    }
    (args.out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["source_unchanged"] or not report["copy_unchanged"] or not report["pdf_pages"]:
        raise RuntimeError("PDF 생성 또는 원본 보존 검증에 실패했습니다.")


if __name__ == "__main__":
    main()
