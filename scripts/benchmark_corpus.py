"""Benchmark HWP/HWPX conversion, inspection and precise table cloning on a corpus."""

from __future__ import annotations

import argparse
import json
import runpy
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * ratio))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_folder = args.folder.resolve()
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    namespace = runpy.run_path(str(repo / "hwp-auto-docfit.py"), run_name="corpus_benchmark")
    validate = namespace["validate_hwpx"]
    inspect = namespace["inspect_hwpx"]
    analyze = namespace["hwpx_서식_분석"]
    apply_tables = namespace["정밀표_서식_적용"]

    files = sorted(
        (path for path in source_folder.rglob("*") if path.is_file() and path.suffix.lower() in {".hwp", ".hwpx"}),
        key=lambda path: str(path).lower(),
    )
    results: list[dict] = []
    app = None
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="hwp_docfit_corpus_") as temp_name:
        temp = Path(temp_name)
        try:
            for index, source in enumerate(files):
                item = {
                    "file": str(source.relative_to(source_folder)),
                    "input_format": source.suffix.lower().lstrip("."),
                    "bytes": source.stat().st_size,
                }
                try:
                    working = temp / f"{index:03d}_{source.stem}.hwpx"
                    conversion_started = time.perf_counter()
                    if source.suffix.lower() == ".hwp":
                        if app is None:
                            namespace["보안모듈_초기화"]()
                            namespace["pythoncom"].CoInitialize()
                            app = namespace["win32"].Dispatch("HwpFrame.HwpObject")
                            if not app.RegisterModule(namespace["REGISTER_MODULE_NAME"], namespace["REGISTER_MODULE_VALUE"]):
                                raise RuntimeError("한글 보안 모듈 등록 실패")
                        if app.Open(str(source), Format="HWP", arg="forceopen:true") is False:
                            raise RuntimeError("HWP 열기 실패")
                        if app.SaveAs(str(working), "HWPX", "") is False:
                            raise RuntimeError("HWPX 변환 실패")
                    else:
                        shutil.copy2(source, working)
                    item["conversion_seconds"] = round(time.perf_counter() - conversion_started, 4)

                    inspection_started = time.perf_counter()
                    security = validate(working)
                    structure = inspect(working)
                    item["inspection_seconds"] = round(time.perf_counter() - inspection_started, 4)
                    item["zip_entries"] = security["entry_count"]
                    item["paragraphs"] = structure.paragraph_count
                    item["tables"] = structure.table_count
                    item["images"] = structure.image_count

                    analysis_started = time.perf_counter()
                    profile = analyze(working)
                    item["analysis_seconds"] = round(time.perf_counter() - analysis_started, 4)
                    item["precise_table_profiles"] = len(profile.get("precise_tables", {}).get("tables", []))

                    clone_started = time.perf_counter()
                    cloned = temp / f"{index:03d}_{source.stem}_cloned.hwpx"
                    clone_result = apply_tables(working, cloned, profile.get("precise_tables"))
                    validate(cloned)
                    cloned_structure = inspect(cloned)
                    item["clone_seconds"] = round(time.perf_counter() - clone_started, 4)
                    item["tables_applied"] = clone_result["applied"]
                    item["tables_skipped"] = clone_result["skipped"]
                    item["structure_preserved"] = (
                        structure.paragraph_count == cloned_structure.paragraph_count
                        and structure.table_count == cloned_structure.table_count
                        and structure.image_count == cloned_structure.image_count
                    )
                    item["ok"] = item["structure_preserved"]
                except Exception as exc:
                    item["ok"] = False
                    item["error"] = f"{type(exc).__name__}: {exc}"
                item["total_seconds"] = round(sum(float(item.get(key, 0)) for key in (
                    "conversion_seconds", "inspection_seconds", "analysis_seconds", "clone_seconds"
                )), 4)
                results.append(item)
        finally:
            if app is not None:
                try:
                    app.Quit()
                except Exception:
                    pass
            try:
                namespace["pythoncom"].CoUninitialize()
            except Exception:
                pass

    durations = [item["total_seconds"] for item in results]
    summary = {
        "source": str(source_folder),
        "files": len(results),
        "hwp": sum(item["input_format"] == "hwp" for item in results),
        "hwpx": sum(item["input_format"] == "hwpx" for item in results),
        "success": sum(bool(item["ok"]) for item in results),
        "failed": sum(not bool(item["ok"]) for item in results),
        "tables_found": sum(int(item.get("tables", 0)) for item in results),
        "tables_applied": sum(int(item.get("tables_applied", 0)) for item in results),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "mean_file_seconds": round(statistics.mean(durations), 4) if durations else 0,
        "median_file_seconds": round(statistics.median(durations), 4) if durations else 0,
        "p95_file_seconds": round(percentile(durations, 0.95), 4),
    }
    payload = {"summary": summary, "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
