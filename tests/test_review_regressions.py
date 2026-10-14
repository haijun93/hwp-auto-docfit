"""Release import gate and interleaved draft-save revision regressions."""
import hashlib
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from docfit_app.document_tools_service import DocumentToolsService
from docfit_app.api_contract import ServiceError
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

    def test_interleaved_editor_cannot_receive_another_editors_revision(self):
        from docfit_infra.storage.process_lock import ProcessLock
        with tempfile.TemporaryDirectory() as folder:
            first, second = DocumentToolsService(folder), DocumentToolsService(folder)
            initial = first.command("outline.load", {})
            released, finished = threading.Event(), threading.Event()
            worker_errors = []
            class InterleavedLock:
                def __init__(self, *args, **kwargs):
                    self.lock = ProcessLock(*args, **kwargs)
                def __enter__(self):
                    return self.lock.__enter__()
                def __exit__(self, *args):
                    self.lock.__exit__(*args)
                    if not released.is_set():
                        released.set()
                        if not finished.wait(3):
                            raise AssertionError("second editor did not finish")
            def edit_second():
                try:
                    if not released.wait(3):
                        raise AssertionError("first editor did not release")
                    current = second.command("outline.load", {})
                    second.command("outline.save", {"text": "B의 편집\n둘째 줄", "revision": current["revision"]})
                except Exception as exc:
                    worker_errors.append(exc)
                finally:
                    finished.set()
            worker = threading.Thread(target=edit_second)
            with patch("docfit_app.document_tools_service.ProcessLock", InterleavedLock):
                worker.start()
                reply = first.command("outline.save", {"text": "A의 편집\n둘째 줄", "revision": initial["revision"]})
                worker.join(3)
            self.assertFalse(worker_errors)
            self.assertFalse(worker.is_alive())
            self.assertEqual(reply, {"text": "A의 편집\n둘째 줄",
                                    "revision": hashlib.sha256("A의 편집\n둘째 줄".encode()).hexdigest()})
            with self.assertRaises(ServiceError):
                first.command("outline.save", {"text": "A의 후속 편집", "revision": reply["revision"]})
            self.assertEqual(second.command("outline.load", {})["text"], "B의 편집\n둘째 줄")


    def test_bootstrap_symbol_failure_returns_nonzero_and_writes_report(self):
        import json
        import sys
        from docfit_app.self_test import finish
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / "report.json"
            with patch.object(sys, "argv", ["app", "--self-test", "--self-test-report", str(report)]):
                self.assertEqual(finish({"ok":True,"errors":[],"modules":[]}, {}), 1)
            data = json.loads(report.read_text())
            self.assertFalse(data["ok"])
            self.assertTrue(any(item.get("symbol") == "작업_실행" for item in data["errors"]))
