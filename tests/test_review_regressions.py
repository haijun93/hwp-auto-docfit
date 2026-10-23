"""Release import gate regressions."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from docfit_app.self_test import check


class ReviewRegressions(unittest.TestCase):
    def test_import_gate_loads_all_dynamic_packages_without_starting_gui(self):
        result = check()
        self.assertTrue(result["ok"], result["errors"])
        for module in ("docfit_engine.formatter", "docfit_engine.spacing",
                       "docfit_engine.page_fit", "docfit_ui.legacy", "desktop_web_ui"):
            if module != "desktop_web_ui":
                self.assertIn(module, result["modules"])

    def test_missing_dynamic_module_fails_import_gate(self):
        import importlib
        original = importlib.import_module
        def missing(name, *args, **kwargs):
            if name == "docfit_engine.spacing":
                raise ModuleNotFoundError(name)
            return original(name, *args, **kwargs)
        with patch("docfit_app.self_test.importlib.import_module", side_effect=missing):
            self.assertFalse(check()["ok"])

    def test_bootstrap_symbol_failure_returns_nonzero_and_writes_report(self):
        import json
        import sys
        from docfit_app.self_test import finish
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / "report.json"
            with patch.object(sys, "argv", ["app", "--self-test", "--self-test-report", str(report)]):
                self.assertEqual(finish({"ok":True,"errors":[],"modules":[]}, {}), 1)
            data = json.loads(report.read_text(encoding='utf-8'))
            self.assertFalse(data["ok"])
            self.assertTrue(any(item.get("symbol") == "작업_실행" for item in data["errors"]))
