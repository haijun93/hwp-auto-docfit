"""Pure tests for paired Beta/Alpha evaluation statistics and decision gates."""
from __future__ import annotations

import runpy
import unittest
from pathlib import Path


MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "compare_versions_pc.py"))


class PairedEvaluationTest(unittest.TestCase):
    def test_order_alternates_to_balance_warmup_bias(self):
        self.assertEqual([MODULE["execution_order"](n) for n in range(4)],
                         [("beta", "alpha"), ("alpha", "beta"), ("beta", "alpha"), ("alpha", "beta")])

    def test_paired_delta_positive_means_alpha_is_slower(self):
        self.assertEqual(MODULE["paired_deltas"]([100, 200], [105, 190]), [5.0, -5.0])

    def test_percentile_interpolates(self):
        self.assertEqual(MODULE["percentile"]([1, 2, 3, 4], .5), 2.5)

    def test_markdown_markers_are_counted_without_retaining_text(self):
        self.assertGreaterEqual(MODULE["markdown_marker_count"]("## Heading\n**bold**\n- item\n"), 4)

    def test_stage_times_parse_top_stage_line(self):
        parsed = MODULE["parse_stage_times"]("[처리 시간 계측] 오래 걸린 단계(상위 2): 페이지 맞춤 12.5초(40%, 1회) / 저장 3초(10%, 1회)")
        self.assertEqual(parsed, {"페이지 맞춤": 12.5, "저장": 3.0})

    def test_fewer_than_three_pairs_is_not_claimed_as_clean(self):
        case = {"runs": {"beta": [{"seconds": 10, "passed": True}],
                         "alpha": [{"seconds": 10, "passed": True}]}}
        result = MODULE["summarize_case"](case, threshold_pct=5, repeat=1)
        self.assertEqual(result["verdict"], "insufficient_data")
        self.assertIsNone(result["metrics"]["paired_delta_bootstrap_95_ci"])

    def test_quality_loss_is_regression_even_if_faster(self):
        case = {"runs": {"beta": [{"seconds": 100, "passed": True, "score": 100, "layout_same": True}],
                         "alpha": [{"seconds": 50, "passed": False, "score": 90, "layout_same": False}]}}
        result = MODULE["summarize_case"](case, threshold_pct=5, repeat=1)
        self.assertEqual(result["verdict"], "regression")
        self.assertTrue(result["metrics"]["quality_regressions"])

    def test_three_consistent_pairs_can_pass_threshold(self):
        case = {"runs": {"beta": [{"seconds": 100, "passed": True, "score": 100} for _ in range(3)],
                         "alpha": [{"seconds": 102, "passed": True, "score": 100} for _ in range(3)]}}
        result = MODULE["summarize_case"](case, threshold_pct=5, repeat=3)
        self.assertEqual(result["verdict"], "no_detected_regression")
        self.assertEqual(result["metrics"]["paired_delta_median_percent"], 2.0)

    def test_markdown_report_formats_pass_rates_and_structure_metrics(self):
        report = {"verdict": "no_detected_regression", "config": {"tier": "quick", "repeat": 3,
                  "modes": ["format"], "time_regression_threshold_pct": 5},
                  "cases": [{"document": "sample.txt", "mode": "format", "verdict": "no_detected_regression",
                  "metrics": {"beta_seconds": {"median": 10}, "alpha_seconds": {"median": 9},
                  "paired_delta_median_percent": -10, "beta_pass_rate": "3/3", "alpha_pass_rate": "3/3",
                  "output_comparison": {"available_pairs": 3, "text_identical_pairs": 0,
                  "median_markdown_markers_beta": 8, "median_markdown_markers_alpha": 0,
                  "median_outline_markers_beta": 4, "median_outline_markers_alpha": 0}}}]}
        rendered = MODULE["_markdown_report"](report)
        self.assertIn("3/3 / 3/3", rendered)
        self.assertNotIn("3/3/3/3", rendered)
        self.assertIn("Markdown 표식 중앙값 8 → 0", rendered)


if __name__ == "__main__":
    unittest.main()
