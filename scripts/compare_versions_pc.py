r"""Paired, repeatable Windows/한글 A/B evaluation for Beta vs Alpha.

Example (quick representative-page excerpt, three paired repeats):
  python scripts/compare_versions_pc.py --beta-root ..\beta --alpha-root . \
      --corpus %APPDATA%\HwpAutoDocFit\test_corpus.json --tier quick \
      --mode unify --repeat 3 --unify-full-format 0 --require-same-layout \
      --out-dir %TEMP%\docfit-ab

Inputs are passed to regression_pc.py, which works on temporary copies. Quick tier
creates/reuses one content-hash keyed five-page excerpt and gives the exact same
excerpt to both versions. Each repeat alternates Beta→Alpha / Alpha→Beta order.
The report contains medians, paired deltas, quality/layout gates, stage timings,
and output structure fingerprints; it never stores source document text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import runpy
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


VERSIONS = ("beta", "alpha")
MODES = ("all", "format", "unify", "spacing")
STAGE_LINE = re.compile(r"^\[처리 시간 계측\] 오래 걸린 단계\(상위 \d+\): (.*)$", re.M)
STAGE_ITEM = re.compile(r"([^/]+?)\s+([\d.]+)초(?:\([^)]*\))?")
MARKDOWN_PATTERNS = (
    re.compile(r"(?m)^\s{0,3}#{1,6}\s+"),
    re.compile(r"(?<!\\)(?:\*\*|__)"),
    re.compile(r"(?m)^\s*[-*+]\s+"),
    re.compile(r"(?m)^\s*>\s?"),
    re.compile(r"`{1,3}"),
    re.compile(r"\[(?:cite|oaicite|source|web)[:_][^\]]*\]", re.I),
)
OUTLINE_MARKER = re.compile(r"(?m)^\s*(?:□|ㅇ|○|●|[-*])\s+")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values: list[float], ratio: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * ratio
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(ordered[lower], 4)
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower), 4)


def paired_deltas(beta: list[float], alpha: list[float]) -> list[float]:
    """Per-pair percent changes, where positive means Alpha took longer."""
    return [100.0 * (a - b) / b for b, a in zip(beta, alpha) if b > 0]


def bootstrap_median_ci(values: list[float], seed: int = 740213, samples: int = 4000) -> list[float] | None:
    """Deterministic percentile interval over paired deltas (descriptive, not a p-value)."""
    if len(values) < 3:
        return None
    import random
    rng = random.Random(seed)
    medians = [statistics.median(rng.choices(values, k=len(values))) for _ in range(samples)]
    return [percentile(medians, .025), percentile(medians, .975)]


def execution_order(pair_index: int) -> tuple[str, str]:
    """Alternating pair order balances warm-up and time-of-day bias."""
    return ("beta", "alpha") if pair_index % 2 == 0 else ("alpha", "beta")


def parse_stage_times(log_text: str) -> dict[str, float]:
    match = STAGE_LINE.search(log_text)
    if not match:
        return {}
    parsed: dict[str, float] = {}
    for part in match.group(1).split(" / "):
        item = STAGE_ITEM.search(part)
        if item:
            parsed[item.group(1).strip()] = float(item.group(2))
    return parsed


def markdown_marker_count(text: str) -> int:
    return sum(len(pattern.findall(text)) for pattern in MARKDOWN_PATTERNS)


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=15)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def version_info(root: Path) -> dict[str, Any]:
    return {"root": str(root), "commit": _git(root, "rev-parse", "HEAD"),
            "dirty": bool(_git(root, "status", "--porcelain"))}


def collect_documents(args: argparse.Namespace) -> list[Path]:
    if args.corpus:
        value = json.loads(args.corpus.read_text(encoding="utf-8"))
        raw = value.get("documents", []) if isinstance(value, dict) else value
    else:
        raw = args.documents
    documents = [Path(item).expanduser().resolve() for item in raw]
    if not documents:
        raise ValueError("시험할 문서를 지정하거나 --corpus 목록을 제공하세요.")
    missing = [str(path) for path in documents if not path.is_file()]
    if missing:
        raise FileNotFoundError("입력 파일이 없습니다: " + ", ".join(missing))
    return documents


def make_quick_excerpt(beta_root: Path, source: Path) -> Path:
    helper = beta_root / "scripts" / "test_tier_pc.py"
    if not helper.is_file():
        raise FileNotFoundError(f"quick tier 발췌 도구가 없습니다: {helper}")
    namespace = runpy.run_path(str(helper), run_name="docfit_beta_excerpt_helper")
    excerpt = Path(namespace["발췌본_만들기"](source)).resolve()
    if not excerpt.is_file():
        raise RuntimeError(f"발췌본을 만들지 못했습니다: {excerpt}")
    return excerpt


def output_summary(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    # Parse with the evaluator's parser for consistent Beta/Alpha comparisons.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from docfit_core.hwpx import inspect_hwpx
    inspection = inspect_hwpx(path)
    return {
        "sha256": sha256_file(path),
        "text_sha256": inspection.text_sha256,
        "paragraphs": inspection.paragraph_count,
        "tables": inspection.table_count,
        "images": inspection.image_count,
        "controls": inspection.control_count,
        "sections": inspection.section_count,
        "markdown_markers": markdown_marker_count(inspection.text),
        "outline_marker_paragraphs": len(OUTLINE_MARKER.findall(inspection.text)),
        "warnings": len(inspection.warnings),
    }


def _run_one(root: Path, version: str, document: Path, mode: str, trial: int,
             case_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    run_dir = case_dir / f"trial-{trial:02d}" / version
    log_dir, keep_dir = run_dir / "logs", run_dir / "output"
    run_dir.mkdir(parents=True, exist_ok=True)
    argv = [sys.executable, str(root / "scripts" / "regression_pc.py"), str(document),
            "--mode", mode, "--out", str(run_dir / "result.json"),
            "--log-dir", str(log_dir), "--keep-dir", str(keep_dir),
            "--min-score", str(args.min_score)]
    if args.require_same_layout:
        argv.append("--require-same-layout")
    if args.unify_full_format is not None:
        argv.extend(("--unify-full-format", args.unify_full_format))
    for flag in args.flag:
        argv.extend(("--flag", flag))
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    started = time.perf_counter()
    error = None
    try:
        with (run_dir / "stdout.txt").open("w", encoding="utf-8") as stdout:
            completed = subprocess.run(argv, cwd=root, stdout=stdout, stderr=subprocess.STDOUT,
                                       timeout=args.timeout, env=env, check=False)
        exit_code = completed.returncode
    except subprocess.TimeoutExpired:
        exit_code, error = None, f"timeout after {args.timeout}s"
    except OSError as exc:
        exit_code, error = None, f"{type(exc).__name__}: {exc}"
    wall_seconds = time.perf_counter() - started
    record: dict[str, Any] = {"version": version, "trial": trial, "exit_code": exit_code,
                              "error": error, "wall_seconds": round(wall_seconds, 3),
                              "document_sha256": sha256_file(document), "passed": False}
    result_path = run_dir / "result.json"
    if result_path.is_file():
        try:
            rows = json.loads(result_path.read_text(encoding="utf-8"))
            row = rows[0] if rows else {}
            record.update({"app_version": row.get("app_version"), "commit": row.get("commit"),
                           "settings": row.get("settings"), "seconds": row.get("seconds"),
                           "score": row.get("score"), "passed": bool(row.get("passed")),
                           "checks": row.get("checks"), "pages": row.get("pages"),
                           "layout_same": row.get("layout_same")})
        except (OSError, ValueError, IndexError) as exc:
            record["error"] = f"invalid regression result: {exc}"
    log_files = list(log_dir.glob("*.log")) if log_dir.is_dir() else []
    if log_files:
        log_text = log_files[0].read_text(encoding="utf-8", errors="replace")
        record["stage_seconds"] = parse_stage_times(log_text)
        record["stage_summary"] = next((line.split(": ", 1)[-1].strip() for line in log_text.splitlines()
                                        if line.startswith("[처리 시간 계측] 분류별:")), None)
    outputs = list(keep_dir.glob("*.hwpx")) if keep_dir.is_dir() else []
    record["output"] = output_summary(outputs[0]) if outputs else None
    if exit_code not in (0, None) and not error:
        record["error"] = f"regression_pc exit code {exit_code}"
    return record


def _quality_regression(beta_runs: list[dict], alpha_runs: list[dict]) -> list[str]:
    issues: list[str] = []
    for index, (beta, alpha) in enumerate(zip(beta_runs, alpha_runs), 1):
        if beta.get("passed") and not alpha.get("passed"):
            issues.append(f"trial {index}: Beta passed but Alpha failed")
        if beta.get("score") is not None and alpha.get("score") is not None and alpha["score"] < beta["score"]:
            issues.append(f"trial {index}: Alpha score {alpha['score']} < Beta {beta['score']}")
        if beta.get("layout_same") is True and alpha.get("layout_same") is False:
            issues.append(f"trial {index}: Beta preserved layout but Alpha did not")
    return issues


def compare_outputs(beta_runs: list[dict], alpha_runs: list[dict]) -> dict[str, Any]:
    """Compare output content/structure without copying document text to the report."""
    pairs = []
    for beta, alpha in zip(beta_runs, alpha_runs):
        before, after = beta.get("output"), alpha.get("output")
        if not before or not after:
            continue
        pairs.append({
            "text_identical": before["text_sha256"] == after["text_sha256"],
            "markdown_markers_beta": before["markdown_markers"],
            "markdown_markers_alpha": after["markdown_markers"],
            "outline_markers_beta": before["outline_marker_paragraphs"],
            "outline_markers_alpha": after["outline_marker_paragraphs"],
            "paragraph_delta_alpha_minus_beta": after["paragraphs"] - before["paragraphs"],
            "table_delta_alpha_minus_beta": after["tables"] - before["tables"],
            "image_delta_alpha_minus_beta": after["images"] - before["images"],
        })
    if not pairs:
        return {"available_pairs": 0, "pairs": []}
    return {
        "available_pairs": len(pairs),
        "text_identical_pairs": sum(row["text_identical"] for row in pairs),
        "median_markdown_markers_beta": statistics.median(row["markdown_markers_beta"] for row in pairs),
        "median_markdown_markers_alpha": statistics.median(row["markdown_markers_alpha"] for row in pairs),
        "median_outline_markers_beta": statistics.median(row["outline_markers_beta"] for row in pairs),
        "median_outline_markers_alpha": statistics.median(row["outline_markers_alpha"] for row in pairs),
        "pairs": pairs,
    }


def summarize_case(case: dict[str, Any], threshold_pct: float, repeat: int) -> dict[str, Any]:
    beta_runs, alpha_runs = case["runs"]["beta"], case["runs"]["alpha"]
    beta_times = [float(row["seconds"]) for row in beta_runs if isinstance(row.get("seconds"), (int, float))]
    alpha_times = [float(row["seconds"]) for row in alpha_runs if isinstance(row.get("seconds"), (int, float))]
    paired = paired_deltas(beta_times, alpha_times)
    ci = bootstrap_median_ci(paired)
    quality_issues = _quality_regression(beta_runs, alpha_runs)
    median_delta = statistics.median(paired) if paired else None
    alpha_passes = sum(bool(row.get("passed")) for row in alpha_runs)
    beta_passes = sum(bool(row.get("passed")) for row in beta_runs)
    if quality_issues:
        verdict = "regression"
    elif len(paired) < 3 or beta_passes != repeat or alpha_passes != repeat:
        verdict = "insufficient_data"
    elif median_delta is not None and median_delta > threshold_pct:
        verdict = "regression" if ci and ci[0] > 0 else "inconclusive"
    elif median_delta is not None and median_delta < -threshold_pct and ci and ci[1] < 0:
        verdict = "improved"
    else:
        verdict = "no_detected_regression"
    case.update({
        "metrics": {
            "beta_seconds": {"n": len(beta_times), "median": round(statistics.median(beta_times), 3) if beta_times else None,
                             "p95": percentile(beta_times, .95)},
            "alpha_seconds": {"n": len(alpha_times), "median": round(statistics.median(alpha_times), 3) if alpha_times else None,
                              "p95": percentile(alpha_times, .95)},
            "paired_delta_percent": [round(value, 2) for value in paired],
            "paired_delta_median_percent": round(median_delta, 2) if median_delta is not None else None,
            "paired_delta_bootstrap_95_ci": ci,
            "beta_pass_rate": f"{beta_passes}/{repeat}",
            "alpha_pass_rate": f"{alpha_passes}/{repeat}",
            "quality_regressions": quality_issues,
            "output_comparison": compare_outputs(beta_runs, alpha_runs),
        },
        "verdict": verdict,
    })
    return case


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [f"# Beta–Alpha 비교시험 — {report['verdict']}", "",
             f"- 시험 조건: {report['config']['tier']} tier · {report['config']['repeat']}회 반복 · "
             f"모드 `{', '.join(report['config']['modes'])}` · 순서 교차(BA/AB)",
             f"- 입력 해시 기준으로 동일 문서 사본을 양쪽 버전에 전달했습니다.",
             f"- 시간 임계값: +{report['config']['time_regression_threshold_pct']}% 초과", "",
             "| 입력 | 모드 | Beta 중앙값(초) | Alpha 중앙값(초) | 짝별 시간차 중앙값 | Beta/Alpha 합격 | 판정 |",
             "|---|---|---:|---:|---:|---:|---|"]
    for case in report["cases"]:
        metrics = case["metrics"]
        lines.append(f"| {case['document']} | {case['mode']} | {metrics['beta_seconds']['median']} | "
                     f"{metrics['alpha_seconds']['median']} | {metrics['paired_delta_median_percent']}% | "
                     f"{metrics['beta_pass_rate']} / {metrics['alpha_pass_rate']} | {case['verdict']} |")
        output = metrics.get("output_comparison", {})
        if output.get("available_pairs"):
            lines.append("")
            lines.append(f"- 출력 구조 `{case['document']}`: Markdown 표식 중앙값 "
                         f"{output['median_markdown_markers_beta']} → {output['median_markdown_markers_alpha']}, "
                         f"개요기호 문단 중앙값 {output['median_outline_markers_beta']} → "
                         f"{output['median_outline_markers_alpha']}; 본문 텍스트 해시 동일 "
                         f"{output['text_identical_pairs']}/{output['available_pairs']}쌍")
    lines.extend(("", "## 판정 기준", "",
                  "점수·결과 생성·요구된 쪽 구성의 베타 대비 하락은 회귀입니다. 처리시간은 각 반복쌍의 "
                  "Alpha−Beta 비율을 계산하고 중앙값과 부트스트랩 95% 구간(기술통계)을 함께 냅니다. "
                  "반복 3회 미만 또는 품질검사 미완료는 자료 부족이며, +임계값을 넘지만 구간이 0을 포함하면 판정 보류입니다.", "",
                  "## 유의사항", "",
                  "중앙값과 교차 순서는 PC 부하·한/글 COM 조판 변동을 완화하지만 제거하지는 않습니다. "
                  "`no_detected_regression`은 시험 범위 안에서 회귀가 검출되지 않았다는 뜻이지, 모든 문서에서 성능이 같다는 보증은 아닙니다.", ""))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("documents", nargs="*", type=Path)
    parser.add_argument("--corpus", type=Path, help="JSON {documents:[...]} 또는 경로 배열")
    parser.add_argument("--beta-root", required=True, type=Path)
    parser.add_argument("--alpha-root", required=True, type=Path)
    parser.add_argument("--tier", choices=("quick", "full"), default="quick")
    parser.add_argument("--mode", action="append", choices=MODES, required=True)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=100.0)
    parser.add_argument("--require-same-layout", action="store_true")
    parser.add_argument("--unify-full-format", choices=("0", "1"))
    parser.add_argument("--time-regression-threshold-pct", type=float, default=5.0)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--flag", action="append", default=[], metavar="NAME=0|1")
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.repeat < 1 or args.timeout < 1:
        parser.error("--repeat과 --timeout은 1 이상이어야 합니다.")
    beta_root, alpha_root = args.beta_root.resolve(), args.alpha_root.resolve()
    for root in (beta_root, alpha_root):
        if not (root / "scripts" / "regression_pc.py").is_file():
            parser.error(f"회귀시험 도구가 없습니다: {root / 'scripts' / 'regression_pc.py'}")
    documents = collect_documents(args)
    args.out_dir = args.out_dir.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    input_hashes = {str(path): sha256_file(path) for path in documents}
    prepared = [(path, make_quick_excerpt(beta_root, path)
                 if args.tier == "quick" and path.suffix.lower() in {".hwp", ".hwpx"} else path)
                for path in documents]
    cases: list[dict[str, Any]] = []
    for doc_index, (original, prepared_doc) in enumerate(prepared, 1):
        for mode in args.mode:
            case_id = f"d{doc_index}-{hashlib.sha256(str(original).encode()).hexdigest()[:8]}-{mode}"
            case: dict[str, Any] = {"document": original.name, "input_sha256": input_hashes[str(original)],
                                    "tested_document": str(prepared_doc), "tested_sha256": sha256_file(prepared_doc),
                                    "mode": mode, "runs": {"beta": [], "alpha": []}}
            case_dir = args.out_dir / case_id
            for trial in range(1, args.repeat + 1):
                for version in execution_order(trial - 1):
                    root = beta_root if version == "beta" else alpha_root
                    result = _run_one(root, version, prepared_doc, mode, trial, case_dir, args)
                    case["runs"][version].append(result)
                    if sha256_file(original) != input_hashes[str(original)]:
                        raise RuntimeError(f"원본 입력이 변했습니다(시험 중단): {original}")
                    if sha256_file(prepared_doc) != case["tested_sha256"]:
                        raise RuntimeError(f"시험 사본이 변했습니다(시험 중단): {prepared_doc}")
                    print(f"[{case_id}] pair {trial}/{args.repeat} {version}: "
                          f"{result.get('seconds', 'n/a')}s score={result.get('score', 'n/a')} "
                          f"pass={result.get('passed')}", flush=True)
            cases.append(summarize_case(case, args.time_regression_threshold_pct, args.repeat))
    verdicts = {case["verdict"] for case in cases}
    global_verdict = ("regression" if "regression" in verdicts else
                      "inconclusive" if verdicts & {"inconclusive", "insufficient_data"} else
                      "improved" if verdicts == {"improved"} else "no_detected_regression")
    report = {
        "schema_version": 1,
        "created_at_local": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "environment": {"platform": platform.platform(), "python": platform.python_version(),
                        "logical_cpus": os.cpu_count()},
        "versions": {"beta": version_info(beta_root), "alpha": version_info(alpha_root)},
        "config": {"tier": args.tier, "repeat": args.repeat, "modes": args.mode,
                   "min_score": args.min_score, "require_same_layout": args.require_same_layout,
                   "unify_full_format": args.unify_full_format,
                   "time_regression_threshold_pct": args.time_regression_threshold_pct,
                   "order": "BA, AB, BA..."},
        "verdict": global_verdict,
        "cases": cases,
    }
    (args.out_dir / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out_dir / "comparison.md").write_text(_markdown_report(report), encoding="utf-8")
    print(f"A/B 판정: {global_verdict} — {args.out_dir / 'comparison.md'}", flush=True)
    return 0 if global_verdict in {"improved", "no_detected_regression"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
