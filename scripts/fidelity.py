"""원본 보존 경로 명령줄 도구(STYLE_FIDELITY_DESIGN.md 첫 구현 범위).

  coverage <문서> [--json 파일]        압축 항목 전수 목록과 요소·속성 해석 범위
  copy <원본> <사본>                   바이트 그대로 복제하고 해시 일치 확인
  objects <문서> [--json 파일]         고칠 수 있는 문단(파트·객체 경로·글) 목록
  patch <원본> <계획.json> <결과> [--allow-partial] [--native]
                                       계획대로 글만 바꾸고 다층 검증(--native: 한/글로 열어 확인)

계획 예:
  {"source_sha256": "<원본 SHA-256>",
   "operations": [{"op": "replace_text", "part": "Contents/section0.xml", "object": "/p[3]",
                   "old": "9월", "new": "10월"}]}
원본 파일은 읽기만 한다. 결과는 항상 다른 경로에 쓴다.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from docfit_core.fidelity import (apply_patch, copy_exact, coverage, inventory,  # noqa: E402
                                  list_objects)


def native_open(path):
    """별도 한/글 인스턴스로 결과를 열고 임시 사본으로 저장해 본다(사용자 한/글 창과 무관)."""
    import runpy
    import tempfile
    import pythoncom
    import win32com.client

    ns = runpy.run_path(str(ROOT / "hwp-auto-docfit.py"), run_name="fidelity_native")
    pythoncom.CoInitialize()
    app = win32com.client.DispatchEx("HwpFrame.HwpObject")
    try:
        app.RegisterModule(ns["REGISTER_MODULE_NAME"], ns["REGISTER_MODULE_VALUE"])
        opened = app.Open(str(path), "HWPX", "forceopen:true") is not False
        pages = None
        saved = False
        resaved = None
        if opened:
            try:
                app.Run("MoveDocEnd")
                pages = int(app.XHwpDocuments.Active_XHwpDocument.XHwpDocumentInfo.CurrentPage) + 1
            except Exception:
                pages = None
            resaved = Path(tempfile.mkdtemp(prefix="docfit_native_")) / "resaved.hwpx"
            saved = app.SaveAs(str(resaved), "HWPX", "") is not False
        return {"opened": opened, "pages": pages, "resaved": saved,
                "resaved_path": str(resaved) if saved else None}
    finally:
        try:
            app.Clear(1)
            app.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()


def dump(data, target):
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if target:
        Path(target).write_text(text, encoding="utf-8")
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("coverage"); p.add_argument("document"); p.add_argument("--json")
    p = sub.add_parser("copy"); p.add_argument("source"); p.add_argument("target")
    p = sub.add_parser("objects"); p.add_argument("document"); p.add_argument("--json")
    p = sub.add_parser("patch"); p.add_argument("source"); p.add_argument("plan"); p.add_argument("target")
    p.add_argument("--allow-partial", action="store_true"); p.add_argument("--native", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "coverage":
        listing = inventory(args.document)
        report = {"inventory": listing, "coverage": coverage(listing)}
        if args.json:
            dump(report, args.json)
        cov = report["coverage"]
        print(f"판정: {cov['verdict']} / SHA-256 {listing['sha256']}")
        for part in cov["parts"]:
            extra = ""
            if "elements_total" in part:
                extra = (f" 요소 {part['elements_interpreted']}/{part['elements_total']}"
                         f" 속성 {part['attributes_interpreted']}/{part['attributes_total']}")
            print(f"  {part['status']:8} {part['name']}{extra}")
        return 0
    if args.command == "copy":
        print(dump(copy_exact(args.source, args.target), None))
        return 0
    if args.command == "objects":
        objects = list_objects(args.document)
        if args.json:
            dump(objects, args.json)
        for item in objects:
            print(f"{item['part']}  {item['object']}  {item['text'][:60]}")
        return 0
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    report = apply_patch(args.source, plan, args.target, allow_partial=args.allow_partial,
                         native=native_open if args.native else None)
    print(dump(report, None))
    return 0 if report.get("verdict") not in ("실패",) else 1


if __name__ == "__main__":
    sys.exit(main())
