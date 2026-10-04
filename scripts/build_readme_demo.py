"""README 사례용으로 앱의 실제 처리 경로를 실행한다(화면 녹화 아님).

python scripts/build_readme_demo.py input.txt --out reports/readme-demo --mode spacing
python scripts/build_readme_demo.py input.txt --out reports/readme-demo --mode all

원본·사용자 설정은 변경하지 않는다. 기존 COM 세션에 연결하지 않으며,
보안 모듈이 이미 준비된 환경에서만 실행한다. 결과와 PDF는 지정한 폴더에 보관한다.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=("spacing", "all"), required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    out = (args.out / args.mode).resolve()
    out.mkdir(parents=True, exist_ok=False)
    copied = out / source.name
    shutil.copy2(source, copied)
    source_hash = digest(source)
    code_hash = digest(ROOT / "hwp-auto-docfit.py")
    ns = runpy.run_path(str(ROOT / "hwp-auto-docfit.py"), run_name="readme_demo")
    execute = ns["작업_실행"]
    g = execute.__globals__
    # 기존 사용자 창으로 fallback하지 않는다.
    g["한글_COM_인스턴스_생성"] = lambda 독립=True: g["win32"].DispatchEx("HwpFrame.HwpObject")
    defaults = copy.deepcopy(g["기본_설정"])
    g["설정_불러오기"] = lambda: copy.deepcopy(defaults)

    def prepared_security_only():
        registered = g["등록된_DLL_경로"]()
        if not registered or not Path(registered).is_file():
            raise RuntimeError("이미 등록된 한/글 자동화 모듈이 필요합니다.")
        if Path(registered).resolve() != g["TARGET_DLL"].resolve():
            raise RuntimeError("예시 실행 중 보안 설정을 변경하지 않습니다.")

    g["보안모듈_초기화"] = prepared_security_only
    # README 사례 제작은 다른 실행의 임시 자료를 정리하지 않는다.
    g["이전_작업_임시폴더_정리"] = lambda: 0
    g["표준서식_설정"] = copy.deepcopy(g["기본_서식프로파일"]()["format"])
    logs = []
    original_log = g["로그"]

    def log(message):
        logs.append(str(message))
        original_log(message)

    g["로그"] = log
    convert = g["텍스트_hwpx로_변환"]
    baseline = out / "before.hwpx"

    def convert_and_keep(text, target):
        result = convert(text, target)
        shutil.copy2(target, baseline)
        return result

    g["텍스트_hwpx로_변환"] = convert_and_keep
    started = time.monotonic()
    execute([str(copied)], 실행모드=args.mode, 자동닫기=True,
            표준서식=(args.mode == "all"), 검수=True, 로그파일=True,
            단어분리방지=True, 표준서식_세부=copy.deepcopy(defaults),
            라벨기호설정=copy.deepcopy(defaults["label_symbols"]),
            표준서식_문단위간격_pt={"box": 15, "circle": 10, "note": 3},
            준말_등록={"abbreviations": {}, "abbreviation_defaults": True})
    events = []
    while not g["gui_queue"].empty():
        events.append(g["gui_queue"].get_nowait())
    saved = [Path(e[2]) for e in events if e[0] == "saved"]
    errors = [e for e in events if e[0] in ("fatal_error", "document_error")]
    report = {"app_version": g["APP_VERSION"], "source_file": source.name,
              "source_sha256": source_hash, "source_unchanged": digest(source) == source_hash,
              "code_sha256": code_hash,
              "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "mode": args.mode, "elapsed_seconds": round(time.monotonic() - started, 2),
              "errors": errors, "saved": [p.name for p in saved],
              "review_items": copy.deepcopy(g["검수_문제목록"]),
              "output_hashes": {p.name: digest(p) for p in saved},
              "options": {"profile": "기본 보고서 서식", "verify": True,
                          "reset_spacing": True, "exclude_tables": False,
                          "exclude_pagefit": False, "passes": 1},
              "capture": "application processing API; native PDF output; not a GUI recording"}
    if not saved or errors:
        (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        raise RuntimeError(f"실제 처리 실패: {errors}")
    # 화면 캡처 대신 한/글 자체 PDF 저장으로 렌더링 결과를 확보한다.
    g["pythoncom"].CoInitialize()
    app = None
    try:
        app = g["win32"].DispatchEx("HwpFrame.HwpObject")
        if not app.RegisterModule(g["REGISTER_MODULE_NAME"], g["REGISTER_MODULE_VALUE"]):
            raise RuntimeError("내보내기 세션의 자동화 모듈을 사용할 수 없습니다.")
        report["hwp_version"] = str(app.Version)
        for name, path in (("before", baseline), ("after", saved[-1])):
            if app.Open(str(path), "HWPX", "forceopen:true") is False:
                raise RuntimeError(f"결과 열기 실패: {path.name}")
            if app.SaveAs(str(out / f"{name}.pdf"), "PDF", "") is False:
                raise RuntimeError(f"PDF 출력 실패: {name}")
            app.Clear(1)
    finally:
        if app is not None:
            app.Clear(1)
            app.Quit()
        g["pythoncom"].CoUninitialize()
        (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"mode": args.mode, "saved": report["saved"],
                      "source_unchanged": report["source_unchanged"],
                      "elapsed_seconds": report["elapsed_seconds"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
