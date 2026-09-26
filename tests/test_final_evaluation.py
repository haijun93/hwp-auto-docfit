import tempfile
import unittest
from pathlib import Path

from docfit_core.final_evaluation import build_work_goal, evaluate_work, write_evaluation_report


class FinalEvaluationTest(unittest.TestCase):
    def test_complete_run_is_achieved(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.hwpx"
            output.write_bytes(b"result")
            goal = build_work_goal("all", 1, {"body_spacing": True})
            report = evaluate_work(
                goal,
                [{"source": "source.hwpx", "output": str(output), "success": True,
                  "integrity_ok": True, "rule_checks": {"body_spacing": {"status": "passed"}}}],
                {"attempted": 4, "succeeded": 4},
                verification_enabled=True,
            )
        self.assertEqual(report["verdict"], "달성")
        self.assertEqual(report["score"], 100.0)
        self.assertFalse(report["blockers"])

    def test_missing_output_blocks_achievement(self):
        goal = build_work_goal("format", 1)
        report = evaluate_work(
            goal,
            [{"source": "source.hwpx", "output": "missing.hwpx", "success": True,
              "integrity_ok": None}],
        )
        self.assertEqual(report["verdict"], "확인 필요")
        self.assertTrue(any("결과물" in item for item in report["blockers"]))

    def test_no_measurable_items_are_excluded_not_failed(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.hwpx"
            output.touch()
            report = evaluate_work(
                build_work_goal("spacing", 1),
                [{"source": "source.hwpx", "output": str(output), "success": True,
                  "integrity_ok": None}],
                {"attempted": 0, "succeeded": 0},
            )
        criterion = next(item for item in report["criteria"] if item["key"] == "task_effectiveness")
        self.assertFalse(criterion["applicable"])
        self.assertEqual(report["verdict"], "부분 달성")
        self.assertTrue(report['blockers'])

    def test_missing_or_failed_rule_check_blocks_high_score(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'result.hwpx'
            output.touch()
            for checks in ({}, {'page_group': {'status': 'failed'}},
                           {'page_group': {'status': 'error'}}):
                report = evaluate_work(
                    build_work_goal('all', 1, {'page_group': True}),
                    [{'output': str(output), 'success': True, 'integrity_ok': True,
                      'rule_checks': checks}],
                    {'attempted': 25, 'succeeded': 25}, verification_enabled=True)
                self.assertNotEqual(report['verdict'], '달성')
                self.assertTrue(report['blockers'])

    def test_stages_without_result_checker_are_notes_not_blockers(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.hwpx"
            output.touch()
            report = evaluate_work(
                build_work_goal("all", 1, {"hanging_indent": True, "body_spacing": True,
                                           "word_check": True}),
                [{"output": str(output), "success": True, "integrity_ok": True,
                  "rule_checks": {"word_check": {"status": "passed"}}}],
                {"attempted": 3, "succeeded": 3}, verification_enabled=True)
        self.assertEqual(report["verdict"], "달성")
        self.assertFalse(report["blockers"])
        self.assertIn("body_spacing, hanging_indent", report["notes"][0])
        self.assertEqual(report["verification_coverage"][0]["not_checkable"],
                         ["body_spacing", "hanging_indent"])

    def test_group_longer_than_page_is_a_note_not_a_blocker(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.hwpx"
            output.touch()
            report = evaluate_work(
                build_work_goal("all", 1, {"page_group": True}),
                [{"output": str(output), "success": True, "integrity_ok": True,
                  "rule_checks": {"page_group": {"status": "passed", "issues": [],
                                                 "exempt": [{"text": "[한 쪽보다 긴 묶음] □ 활용대상"}]}}}],
                {"attempted": 1, "succeeded": 1}, verification_enabled=True)
        self.assertEqual(report["verdict"], "달성")
        self.assertTrue(any("한 쪽보다 긴 묶음 1개" in note for note in report["notes"]))

    def test_word_wider_than_cell_is_a_note_not_a_blocker(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.hwpx"
            output.touch()
            report = evaluate_work(
                build_work_goal("all", 1, {"control_word_check": True}),
                [{"output": str(output), "success": True, "integrity_ok": True,
                  "rule_checks": {"control_word_check": {
                      "status": "passed", "issues": [],
                      "exempt": [{"text": "[칸 폭보다 긴 단어] '질그랭이거점센터'"}]}}}],
                {"attempted": 1, "succeeded": 1}, verification_enabled=True)
        self.assertEqual(report["verdict"], "달성")
        self.assertTrue(any("칸 폭보다 긴 단어 1개" in note for note in report["notes"]))

    def test_number_check_review_is_a_note_not_a_blocker(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.hwpx"
            output.touch()
            report = evaluate_work(
                build_work_goal("all", 1, {"page_group": True}),
                [{"output": str(output), "success": True, "integrity_ok": True,
                  "rule_checks": {"page_group": {"status": "passed", "issues": []},
                                  "number_check": {"status": "passed", "checked": 3, "issues": [],
                                                   "review": [{"text": "'1,500억원'"}]}}}],
                {"attempted": 1, "succeeded": 1}, verification_enabled=True)
        self.assertEqual(report["verdict"], "달성")
        self.assertTrue(any("숫자 대조" in note and "1개" in note for note in report["notes"]))

    def test_missing_checker_result_still_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.hwpx"
            output.touch()
            report = evaluate_work(
                build_work_goal("all", 1, {"hanging_indent": True, "word_check": True}),
                [{"output": str(output), "success": True, "integrity_ok": True,
                  "rule_checks": {}}],
                {"attempted": 3, "succeeded": 3}, verification_enabled=True)
        self.assertNotEqual(report["verdict"], "달성")
        self.assertIn("word_check", report["blockers"][0])

    def test_unresolved_issue_produces_partial_achievement(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.hwpx"
            output.touch()
            report = evaluate_work(
                build_work_goal("all", 1),
                [{"source": "source.hwpx", "output": str(output), "success": True,
                  "integrity_ok": True}],
                {"attempted": 2, "succeeded": 2}, [{"text": "미해결"}], True,
            )
        self.assertEqual(report["verdict"], "부분 달성")
        self.assertTrue(report["blockers"])
        self.assertEqual(report["unresolved"], [{"text": "미해결"}])

    def test_report_is_written_as_korean_json(self):
        with tempfile.TemporaryDirectory() as folder:
            target = write_evaluation_report({"verdict": "달성"}, Path(folder) / "report.json")
            self.assertIn('"달성"', target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
