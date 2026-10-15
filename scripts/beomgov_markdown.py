"""범정부오피스 호환 라벨 문서를 새 HWPX로 생성한다. Windows 한/글 COM 필요."""
import argparse
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from docfit_core.labeled_text import BEOMGOV_DIRECTIVE, parse_labeled_text
from docfit_core.hwpx import inspect_hwpx


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    if args.output.suffix.lower() != ".hwpx" or args.output.exists():
        parser.error("출력은 아직 존재하지 않는 .hwpx 경로여야 합니다.")
    text = args.source.read_text(encoding="utf-8-sig")
    if not text.strip():
        parser.error("입력 문서가 비어 있습니다.")
    if next((s.strip() for s in text.splitlines() if s.strip()), "") != BEOMGOV_DIRECTIVE:
        text = BEOMGOV_DIRECTIVE + "\n" + text
    parse_labeled_text(text)  # COM 실행 전에 입력 문법을 확인한다.
    errors = []
    with tempfile.TemporaryDirectory(prefix="docfit-beomgov-") as temp:
        staged = Path(temp) / "result.hwpx"
        def work():
            try:
                ns = runpy.run_path(str(ROOT / "hwp-auto-docfit.py"))
                ns["텍스트_hwpx_단독변환"](text, staged, AI_변환=False)
                # XML 서식 표 후처리 뒤 실제 조판·미리보기를 새로 저장한다.
                import pythoncom
                pythoncom.CoInitialize()
                app = None
                try:
                    app = ns["한글_COM_인스턴스_생성"](독립=True)
                    app.RegisterModule(ns["REGISTER_MODULE_NAME"], ns["REGISTER_MODULE_VALUE"])
                    if app.Open(str(staged), "HWPX", "forceopen:true") is False:
                        raise RuntimeError("생성한 문서를 다시 열지 못했습니다.")
                    if app.SaveAs(str(staged), "HWPX", "") is False:
                        raise RuntimeError("생성한 문서의 조판을 저장하지 못했습니다.")
                finally:
                    if app is not None:
                        app.Clear(1)
                        app.Quit()
                    pythoncom.CoUninitialize()
            except Exception as exc:
                errors.append(exc)
        worker = Thread(target=work, daemon=True)
        worker.start()
        worker.join()
        if errors:
            raise errors[0]
        inspect_hwpx(staged)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as destination, staged.open("rb") as source:
            shutil.copyfileobj(source, destination)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
