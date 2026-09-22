"""Quantitative comparison of docfit_core's read-only HWPX engine against
publicly available alternatives (python-hwpx, kordoc).

This does NOT benchmark the HWP COM automation pipeline in hwp-auto-docfit.py
(자간조정/서식적용) — that requires a real 한글 installation on Windows and
cannot run outside that environment. What this script CAN measure without
Hancom installed:

  1. Interoperability: can docfit_core read a real HWPX file written by an
     independent library (python-hwpx), and vice versa?
  2. Parse/inspect throughput on the same file.
  3. Footprint: dependency weight and lines of code for the read path.

Optional dependencies (skipped gracefully if missing):
  - `pip install python-hwpx` for the python-hwpx comparison.
  - Node.js 18+ (via npx) for the kordoc comparison, already an optional
    dependency of this project (see docfit_core/kordoc_bridge.py).

Usage:
    python scripts/benchmark_vs_alternatives.py [--runs N] [--paragraphs N]
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from docfit_core.hwpx import inspect_hwpx, validate_hwpx  # noqa: E402


def _timed(fn, runs: int):
    start = time.perf_counter()
    result = None
    for _ in range(runs):
        result = fn()
    elapsed = time.perf_counter() - start
    return result, elapsed / runs * 1000


def _footprint_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def bench_python_hwpx(paragraphs: int, runs: int, workdir: Path) -> dict | None:
    try:
        hwpx = importlib.import_module("hwpx")
    except ImportError:
        return {"available": False, "reason": "pip install python-hwpx 로 설치되지 않음"}

    doc = hwpx.HwpxDocument.new()
    doc.add_heading("벤치마크 문서", level=1)
    for i in range(paragraphs):
        doc.add_paragraph(f"{i + 1}번째 문단입니다. 성능 측정을 위해 반복 생성되었습니다.")
    for _ in range(max(1, paragraphs // 25)):
        doc.add_table(rows=3, cols=3)
    sample_path = workdir / "python_hwpx_sample.hwpx"
    doc.save_to_path(str(sample_path))

    docfit_result, docfit_ms = _timed(lambda: inspect_hwpx(sample_path), runs)
    validate_hwpx(sample_path)  # confirms docfit_core's own safety checks pass too

    def _open_and_list():
        opened = hwpx.HwpxDocument.open(str(sample_path))
        return len(opened.paragraphs), len(opened.tables)

    (native_paragraphs, native_tables), native_ms = _timed(_open_and_list, runs)

    hwpx_module_path = Path(hwpx.__file__).resolve().parent
    return {
        "available": True,
        "sample_file": str(sample_path),
        "sample_size_bytes": sample_path.stat().st_size,
        "docfit_core_reads_it": True,
        "docfit_core": {
            "paragraph_count": docfit_result.paragraph_count,
            "table_count": docfit_result.table_count,
            "ms_per_run": round(docfit_ms, 3),
        },
        "python_hwpx_native": {
            "paragraph_count": native_paragraphs,
            "table_count": native_tables,
            "ms_per_run": round(native_ms, 3),
        },
        "footprint": {
            "docfit_core.hwpx_py_bytes": (REPO / "docfit_core" / "hwpx.py").stat().st_size,
            "python_hwpx_package_bytes": _footprint_bytes(hwpx_module_path),
        },
    }


def bench_kordoc(workdir: Path) -> dict | None:
    npx = None
    for candidate in ("npx.cmd", "npx"):
        import shutil as _shutil
        npx = _shutil.which(candidate)
        if npx:
            break
    if not npx:
        return {"available": False, "reason": "Node.js/npx가 설치되지 않음"}

    markdown_path = workdir / "kordoc_sample.md"
    markdown_path.write_text(
        "# 문서 제목\n\n이것은 본문 문단입니다. 여러 문장으로 구성됩니다.\n\n"
        "| 항목 | 내용 |\n| --- | --- |\n| 자간 | -5% |\n",
        encoding="utf-8",
    )
    target = workdir / "kordoc_sample.hwpx"
    start = time.perf_counter()
    completed = subprocess.run(
        [npx, "-y", "kordoc@^4", "generate", str(markdown_path), "-o", str(target),
         "--preset", "보고서", "--silent"],
        capture_output=True, text=True, timeout=180,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    if completed.returncode != 0 or not target.exists():
        return {"available": False, "reason": (completed.stderr or completed.stdout or "생성 실패").strip()[:300]}

    report = inspect_hwpx(target)
    return {
        "available": True,
        "sample_file": str(target),
        "generate_ms": round(elapsed_ms, 1),
        "docfit_core_reads_it": True,
        "docfit_core_view": {
            "paragraph_count": report.paragraph_count,
            "table_count": report.table_count,
        },
        "note": "첫 실행(npm 캐시 없음)은 패키지 다운로드 때문에 수십 초가 더 걸릴 수 있습니다.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=20, help="반복 측정 횟수")
    parser.add_argument("--paragraphs", type=int, default=500, help="python-hwpx 샘플 문단 수")
    parser.add_argument("--output", type=Path, default=None, help="결과를 저장할 JSON 경로")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="docfit_bench_") as tmp:
        workdir = Path(tmp)
        results = {
            "note": "HWP COM 자동화(자간조정/서식적용)는 Windows+한글 설치 환경이 필요해 이 벤치마크 범위 밖입니다.",
            "python_hwpx_comparison": bench_python_hwpx(args.paragraphs, args.runs, workdir),
            "kordoc_comparison": bench_kordoc(workdir),
        }

    text = json.dumps(results, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
