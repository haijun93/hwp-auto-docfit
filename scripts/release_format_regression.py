"""Fail-closed end-to-end formatting release test on a real Windows/Hancom PC."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], timeout_seconds: int) -> None:
    print("$", subprocess.list2cmdline(command), flush=True)
    process = subprocess.Popen(command, cwd=ROOT)
    try:
        return_code = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        # Stop the Python runner so this gate cannot report success or hang forever.
        # Hancom COM is an out-of-process server; its possible orphan is not killed
        # here because it may be a user-owned HWP process.
        process.kill()
        process.wait()
        raise SystemExit(
            f"Required regression step exceeded {timeout_seconds}s; release gate failed. "
            "Check/close the hidden Hancom automation instance before retrying."
        ) from exc
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("documents", nargs="+", type=Path, help="TXT/HWPX release regression inputs")
    parser.add_argument("--out-dir", required=True, type=Path, help="persistent folder for outputs and evidence")
    parser.add_argument("--mode", choices=("all", "format"), default="all")
    parser.add_argument("--timeout-seconds", type=int, default=300,
                        help="fail closed if a COM step does not finish (default: 300)")
    args = parser.parse_args()

    docs = [path.resolve() for path in args.documents]
    if any(not path.is_file() for path in docs):
        parser.error("All regression input files must exist")
    if len({path.stem.casefold() for path in docs}) != len(docs):
        parser.error("Input basenames must be unique to avoid overwriting evidence")
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    hashes = {str(path): sha256(path) for path in docs}
    results_dir = out / "results"
    logs_dir = out / "logs"
    audit_dir = out / "audits"
    for folder in (results_dir, logs_dir, audit_dir):
        folder.mkdir(parents=True, exist_ok=True)

    regression_json = out / "regression.json"
    regression = [sys.executable, str(ROOT / "scripts/regression_pc.py"),
                  *map(str, docs), "--mode", args.mode, "--verify", "--min-score", "100",
                  "--keep-dir", str(results_dir), "--log-dir", str(logs_dir), "--out", str(regression_json)]
    run(regression, args.timeout_seconds)
    report = json.loads(regression_json.read_text(encoding="utf-8"))
    if len(report) != len(docs) or any(not item.get("passed") for item in report):
        raise SystemExit("Regression test failed or omitted a required input")
    for source in docs:
        result = results_dir / f"{source.stem}.hwpx"
        if not result.is_file():
            raise SystemExit(f"Required processed output missing: {result}")
        audit_json = audit_dir / f"{source.stem}.json"
        run([sys.executable, str(ROOT / "scripts/audit_saved_result.py"),
             str(result), "--output", str(audit_json)], args.timeout_seconds)
        audit = json.loads(audit_json.read_text(encoding="utf-8"))
        if audit.get("input_unchanged") is not True:
            raise SystemExit(f"Audit changed or could not verify output integrity: {result}")
        if audit.get("status") != "pass":
            raise SystemExit(f"Saved-result audit did not pass: {audit_json}")
    changed = [path for path in docs if sha256(path) != hashes[str(path)]]
    if changed:
        raise SystemExit(f"Input originals were modified: {changed}")
    summary = {
        "status": "pass",
        "mode": args.mode,
        "input_sha256": hashes,
        "regression_report": str(regression_json),
        "result_directory": str(results_dir),
        "audit_directory": str(audit_dir),
        "manual_visual_review_required": True,
        "manual_visual_review": "Compare title, marker glyph styling, hanging alignment, and page layout in Hancom before release.",
    }
    summary_path = out / "release_gate.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
