"""Validate page-paired screenshots and reviewer attestations for a release candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ENV_FIELDS = ("windows", "hancom_version", "resolution", "display_scale")
REQUIRED_CHECKPOINTS = {
    "input_baseline", "title_outline", "marker_indent", "spacing_control", "page_fit", "save_reopen"
}


def _png_info(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        raise ValueError(f"Invalid PNG screenshot: {path}")
    width, height = struct.unpack(">II", data[16:24])
    if not width or not height:
        raise ValueError(f"Empty PNG screenshot: {path}")
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
            "width": width, "height": height}


def validate(review_dir: Path) -> dict:
    manifest_path = review_dir / "visual_review.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    issues: list[str] = []
    if not manifest.get("reviewer") or not manifest.get("reviewed_at"):
        issues.append("reviewer and reviewed_at are required")
    environment = manifest.get("environment", {})
    for field in ENV_FIELDS:
        if not environment.get(field):
            issues.append(f"environment.{field} is required")
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        issues.append("at least one document is required")
        documents = []

    verified_docs = []

    def capture_info(raw: str | None, label: str) -> dict | None:
        if not raw:
            issues.append(f"{label} screenshot path is missing")
            return None
        image_path = (review_dir / raw).resolve()
        if not image_path.is_relative_to(review_dir.resolve()):
            issues.append(f"{label} screenshot must stay inside {review_dir}")
            return None
        if not image_path.is_file():
            issues.append(f"{label} screenshot does not exist: {raw}")
            return None
        try:
            return _png_info(image_path)
        except (OSError, ValueError) as exc:
            issues.append(str(exc))
            return None

    for doc_index, document in enumerate(documents):
        pages = document.get("pages") or []
        if not pages:
            issues.append(f"documents[{doc_index}] has no page pairs")
            continue
        seen_pages = set()
        verified_pages = []
        for page in pages:
            number = page.get("page")
            if not isinstance(number, int) or number < 1 or number in seen_pages:
                issues.append(f"documents[{doc_index}] has invalid/duplicate page number: {number}")
            seen_pages.add(number)
            if page.get("decision") != "pass":
                issues.append(f"page {number} is not marked pass")
            if not page.get("notes"):
                issues.append(f"page {number} requires reviewer notes (use '일치' when no difference found)")
            pair = {}
            for side in ("original_png", "result_png"):
                raw = page.get(side)
                if not raw:
                    issues.append(f"page {number} missing {side}")
                    continue
                info = capture_info(raw, f"page {number} {side}")
                if info:
                    pair[side] = info
            if len(pair) == 2:
                if (pair["original_png"]["width"], pair["original_png"]["height"]) != \
                        (pair["result_png"]["width"], pair["result_png"]["height"]):
                    issues.append(f"page {number} screenshot dimensions differ")
                verified_pages.append({"page": number, **pair, "decision": page.get("decision"),
                                       "notes": page.get("notes")})
        if seen_pages and seen_pages != set(range(1, max(seen_pages) + 1)):
            issues.append(f"documents[{doc_index}] page numbers must be contiguous from 1")
        verified_docs.append({"input": document.get("input"), "output": document.get("output"),
                              "pages": verified_pages})
        checkpoints = document.get("checkpoints") or []
        checkpoint_map = {item.get("id"): item for item in checkpoints}
        if len(checkpoint_map) != len(checkpoints):
            issues.append(f"documents[{doc_index}] has duplicate checkpoint ids")
        if not REQUIRED_CHECKPOINTS.issubset(checkpoint_map):
            issues.append(f"documents[{doc_index}] is missing required processing checkpoints")
        verified_checkpoints = []
        for checkpoint_id in sorted(REQUIRED_CHECKPOINTS):
            checkpoint = checkpoint_map.get(checkpoint_id)
            if not checkpoint:
                continue
            if checkpoint.get("decision") != "pass":
                issues.append(f"checkpoint {checkpoint_id} is not marked pass")
            if not checkpoint.get("notes"):
                issues.append(f"checkpoint {checkpoint_id} requires notes about side effects or differences")
            before = capture_info(checkpoint.get("before_png"), f"checkpoint {checkpoint_id} before")
            after = capture_info(checkpoint.get("after_png"), f"checkpoint {checkpoint_id} after")
            if before and after:
                if (before["width"], before["height"]) != (after["width"], after["height"]):
                    issues.append(f"checkpoint {checkpoint_id} screenshot dimensions differ")
                verified_checkpoints.append({"id": checkpoint_id, "label": checkpoint.get("label"),
                                             "before_png": before, "after_png": after,
                                             "decision": checkpoint.get("decision"), "notes": checkpoint.get("notes")})
        verified_docs[-1]["checkpoints"] = verified_checkpoints

    result = {"status": "pass" if not issues else "fail", "reviewer": manifest.get("reviewer"),
              "reviewed_at": manifest.get("reviewed_at"), "environment": environment,
              "documents": verified_docs, "issues": issues}
    if issues:
        return result

    verification_path = review_dir / "visual_review_verified.json"
    verification_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    gate_path = review_dir.parent / "release_gate.json"
    if gate_path.is_file():
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        if gate.get("status") != "automated_pass_visual_pending":
            result["issues"].append("release_gate.json is not in automated_pass_visual_pending state")
            result["status"] = "fail"
            return result
        expected_inputs = set((gate.get("input_sha256") or {}).keys())
        reviewed_inputs = {str(doc.get("input")) for doc in manifest.get("documents", [])}
        if expected_inputs and expected_inputs != reviewed_inputs:
            result["issues"].append("visual review document inputs do not match release_gate.json")
            result["status"] = "fail"
            return result
        gate["status"] = "pass"
        gate["release_ready"] = True
        gate["visual_review_result"] = str(verification_path)
        gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_dir", type=Path, help="release evidence visual-review directory")
    args = parser.parse_args()
    try:
        result = validate(args.review_dir.resolve())
    except (OSError, json.JSONDecodeError) as exc:
        result = {"status": "fail", "issues": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
