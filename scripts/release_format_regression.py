"""Fail-closed end-to-end formatting release test on a real Windows/Hancom PC."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VISUAL_CHECKPOINTS = (
    ("input_baseline", "입력 문서 기준 화면(처리 전)"),
    ("title_outline", "제목·개요 서식 적용 뒤"),
    ("marker_indent", "항목기호·내어쓰기 처리 뒤"),
    ("spacing_control", "자간·공백·표/컨트롤 후속 처리 뒤"),
    ("page_fit", "쪽 맞춤·문단 배치 뒤"),
    ("save_reopen", "저장·닫기·다시 열기 뒤"),
)


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
    parser.add_argument("--timeout-seconds", type=int, default=900,
                        help="fail closed if the full COM regression does not finish (default: 900)")
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
    visual_dir = out / "visual-review"
    for folder in (results_dir, logs_dir, audit_dir, visual_dir / "original", visual_dir / "result"):
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
    visual_review = {
        "status": "pending",
        "reviewer": "",
        "reviewed_at": "",
        "environment": {"windows": "", "hancom_version": "", "resolution": "", "display_scale": ""},
        "documents": [
            {
                "input": str(source),
                "output": str(results_dir / f"{source.stem}.hwpx"),
                "pages": [],
                "checkpoints": [
                    {"id": checkpoint_id, "label": label, "before_png": "", "after_png": "",
                     "decision": "pending", "notes": "단계 전후 화면 차이 및 새로 발생한 이상 여부 기록"}
                    for checkpoint_id, label in VISUAL_CHECKPOINTS
                ],
                "notes": "각 페이지 원본·결과 PNG 짝을 등록하고 화면 차이를 확인한 뒤 판정한다.",
            }
            for source in docs
        ],
        "criteria": [
            "제목·개요의 내용과 서식",
            "최상위 □/ㅁ 항목기호의 내어쓰기 없음",
            "하위 항목기호와 본문 시작 위치 정렬",
            "글꼴·크기·굵기·표·쪽 경계·줄바꿈",
            "저장 후 닫고 다시 연 결과의 모양 유지",
        ],
        "instruction": "각 문서의 모든 pages 및 checkpoints 캡처 짝을 직접 비교하고 판정한다. 자동검사는 이 판정을 대신하지 않는다.",
    }
    visual_json = visual_dir / "visual_review.json"
    visual_json.write_text(json.dumps(visual_review, ensure_ascii=False, indent=2), encoding="utf-8")
    (visual_dir / "README.md").write_text(
        "# 페이지별 화면 캡처 검수\n\n"
        "`original`과 `result`에 같은 페이지 번호의 무편집 PNG를 저장하고, "
        "`visual_review.json`에 페이지별 파일·검수 결과·차이를 기록합니다. "
        "TXT 입력은 원본에 페이지 서식이 없으므로, 원본 화면과의 서식 동일성을 주장하지 말고 "
        "승인된 서식 기준/참조 화면에 대한 결과 적합성을 확인합니다. 자세한 기준은 "
        "`docs/FORMAT_RELEASE_GATE.md`를 따릅니다.\n",
        encoding="utf-8",
    )
    summary = {
        "status": "automated_pass_visual_pending",
        "release_ready": False,
        "mode": args.mode,
        "input_sha256": hashes,
        "regression_report": str(regression_json),
        "result_directory": str(results_dir),
        "audit_directory": str(audit_dir),
        "visual_review_directory": str(visual_dir),
        "visual_review_manifest": str(visual_json),
        "manual_visual_review_required": True,
        "manual_visual_review": "Capture and compare all original/result pages in Hancom; release is blocked until visual_review.json is completed.",
    }
    summary_path = out / "release_gate.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
