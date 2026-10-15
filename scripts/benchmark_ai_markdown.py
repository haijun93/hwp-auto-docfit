"""Benchmark pasted-answer preprocessing; HWP/COM formatting is intentionally out of scope."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import statistics
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docfit_core.ai_answer import ai_answer_to_labeled_text, looks_like_ai_answer
from docfit_core.pasted_text import clean_pasted_text


CASES = ROOT / "tests" / "fixtures" / "markdown_eval_cases.json"
REPEATS = 7
SIZES = (1, 5, 20)


def process(text: str) -> tuple[str, str]:
    if looks_like_ai_answer(text):
        return "AI answer → labeled blocks", ai_answer_to_labeled_text(text)
    return "generic Markdown → cleaned text", clean_pasted_text(text)


def measure(text: str) -> dict:
    durations = []
    peak = 0
    result = ""
    for _ in range(REPEATS):
        tracemalloc.start()
        started = time.perf_counter()
        _route, result = process(text)
        durations.append(time.perf_counter() - started)
        _, current_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak = max(peak, current_peak)
    median = statistics.median(durations)
    return {
        "input_chars": len(text),
        "output_chars": len(result),
        "median_ms": round(median * 1000, 3),
        "chars_per_second": round(len(text) / median) if median else 0,
        "peak_python_bytes": peak,
        "output": result,
    }


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    report = []
    for case in cases:
        baseline = case["text"]
        route, converted = process(baseline)
        residue = [token for token in ("**", "```", "](", "|---", "[x]", "[ ]") if token in converted]
        sizes = []
        for multiplier in SIZES:
            text = "\n\n".join([baseline] * multiplier)
            timing = measure(text)
            timing.pop("output")
            sizes.append({"multiplier": multiplier, **timing})
        report.append({
            "case": case["name"],
            "expected_route": case["kind"],
            "actual_route": route,
            "route_matches": route.startswith("AI answer") == (case["kind"] == "ai"),
            "markdown_residue": residue,
            "scaling": sizes,
        })
    print(json.dumps({"scope": "preprocessing only; no HWP/COM document creation", "cases": report},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
