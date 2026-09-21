"""Run one real format pass on temporary copies of representative documents."""

import argparse
import copy
import json
import runpy
import shutil
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("documents", nargs="+", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    namespace = runpy.run_path(str(repo / "hwp-auto-docfit.py"), run_name="style_smoke_test")
    execution = namespace["작업_실행"]
    globals_ = execution.__globals__
    results = []
    with tempfile.TemporaryDirectory(prefix="docfit_style_smoke_") as folder:
        temporary = Path(folder)
        for index, source in enumerate(args.documents):
            copied = temporary / f"document_{index}{source.suffix.lower()}"
            shutil.copy2(source, copied)
            try:
                profile = namespace["한글파일_서식_분석"](source)
                globals_["표준서식_설정"] = copy.deepcopy(profile["format"])
                globals_["활성_정밀표_프로필"] = None
                execution(
                    [str(copied)], 문장부호기능=False, 자동닫기=True,
                    표준서식=True, 검수=True, 실행모드="format",
                    표준서식_세부={**profile["options"],
                                    "std_title_auto": False,
                                    "std_attachment_auto": False},
                )
                events = []
                while not globals_["gui_queue"].empty():
                    events.append(globals_["gui_queue"].get_nowait())
                saved = [event[2] for event in events if event[0] == "saved"]
                output = Path(saved[-1]) if saved else None
                results.append({"input_type": source.suffix.lower(),
                                "profile_roles": len(profile["style_hierarchy"]["styles"]),
                                "saved": bool(output and output.is_file()),
                                "output_valid": bool(output and output.is_file() and
                                                     namespace["validate_hwpx"](output)),
                                "page_group_stats": globals_["세트문장_통계"],
                                "review_items": len(globals_["검수_문제목록"]),
                                "terminal_events": [event[0] for event in events
                                                    if event[0] in ("saved", "finished", "document_error", "fatal_error")]})
            except Exception as exc:
                results.append({"input_type": source.suffix.lower(), "error": str(exc)})
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(item.get("saved") and item.get("output_valid") for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
