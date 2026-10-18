import json
import struct
import tempfile
import unittest
from pathlib import Path

from scripts.validate_visual_review import validate


class VisualReleaseReviewTests(unittest.TestCase):
    def test_requires_matching_page_screenshots_and_reviewer_attestation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            review = root / "visual-review"
            (review / "original").mkdir(parents=True)
            (review / "result").mkdir()
            png = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR" + struct.pack(">II", 800, 600)
            (review / "original/page-001.png").write_bytes(png)
            (review / "result/page-001.png").write_bytes(png)
            checkpoint_ids = ["input_baseline", "title_outline", "marker_indent", "spacing_control", "page_fit", "save_reopen"]
            checkpoints = []
            for checkpoint_id in checkpoint_ids:
                (review / "checkpoints").mkdir(exist_ok=True)
                (review / f"checkpoints/{checkpoint_id}-before.png").write_bytes(png)
                (review / f"checkpoints/{checkpoint_id}-after.png").write_bytes(png)
                checkpoints.append({"id": checkpoint_id, "label": checkpoint_id,
                                    "before_png": f"checkpoints/{checkpoint_id}-before.png",
                                    "after_png": f"checkpoints/{checkpoint_id}-after.png",
                                    "decision": "pass", "notes": "이상 없음"})
            (root / "release_gate.json").write_text(json.dumps({
                "status": "automated_pass_visual_pending", "release_ready": False
            }), encoding="utf-8")
            manifest = {
                "reviewer": "reviewer", "reviewed_at": "2026-10-18T12:00:00+09:00",
                "environment": {"windows": "Windows", "hancom_version": "Hancom", "resolution": "1920x1080",
                                 "display_scale": "100%"},
                "documents": [{"input": "source.hwpx", "output": "result.hwpx", "checkpoints": checkpoints, "pages": [{
                    "page": 1, "original_png": "original/page-001.png", "result_png": "result/page-001.png",
                    "decision": "pass", "notes": "일치"}]}],
            }
            (review / "visual_review.json").write_text(json.dumps(manifest), encoding="utf-8")

            result = validate(review)

            self.assertEqual(result["status"], "pass")
            gate = json.loads((root / "release_gate.json").read_text(encoding="utf-8"))
            self.assertEqual(gate["status"], "pass")
            self.assertTrue(gate["release_ready"])
            verified = json.loads((review / "visual_review_verified.json").read_text(encoding="utf-8"))
            self.assertEqual(verified["documents"][0]["pages"][0]["original_png"]["width"], 800)

    def test_rejects_missing_or_failed_page_capture_without_approving_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            review = root / "visual-review"
            review.mkdir()
            (root / "release_gate.json").write_text(json.dumps({
                "status": "automated_pass_visual_pending", "release_ready": False
            }), encoding="utf-8")
            (review / "visual_review.json").write_text(json.dumps({"documents": []}), encoding="utf-8")

            result = validate(review)

            self.assertEqual(result["status"], "fail")
            gate = json.loads((root / "release_gate.json").read_text(encoding="utf-8"))
            self.assertFalse(gate["release_ready"])


if __name__ == "__main__":
    unittest.main()
