"""External engine contract without Node/network execution."""
import subprocess
import unittest
from unittest.mock import patch
from docfit_core import kordoc_bridge as bridge


class KordocContractTest(unittest.TestCase):
    def test_mismatching_installed_version_is_rejected(self):
        with patch.object(bridge, "_node_major", return_value=20), patch.object(
                bridge, "engine_version", return_value="kordoc 4.21.5"):
            with self.assertRaisesRegex(bridge.KordocUnavailableError, "버전 불일치"):
                bridge.check_engine_contract()

    def test_incompatible_node_is_rejected_before_engine_execution(self):
        with patch.object(bridge, "_node_major", return_value=18), patch.object(
                bridge, "engine_version") as version:
            with self.assertRaises(bridge.KordocUnavailableError):
                bridge.check_engine_contract()
            version.assert_not_called()

    def test_exit_two_and_skipped_items_are_structured(self):
        result = subprocess.CompletedProcess([], 2,
            '{"skipped": [{"object": "p1"}], "warnings": ["partial"]}', "warning")
        with patch.object(bridge, "check_engine_contract", return_value={"compatible": True}), \
                patch.object(bridge, "run_kordoc", return_value=result):
            report = bridge.run_kordoc_result(["patch"])
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["skipped"], [{"object": "p1"}])
        self.assertEqual(report["warnings"], ["partial", "warning"])
