"""Verify the Windows GUI can start without processing a document."""

import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch


class StartupTest(unittest.TestCase):
    def test_partial_charshape_does_not_fill_unrequested_bold(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="charshape_test")

        class ParameterSet:
            def __init__(self):
                self.items = {}

            def SetItem(self, name, value):
                self.items[name] = value

        class Action:
            def __init__(self):
                self.parameters = ParameterSet()

            def CreateSet(self):
                return self.parameters

            def Execute(self, parameters):
                return True

        class FakeHwp:
            def __init__(self):
                self.action = Action()

            def CreateAction(self, name):
                self.action_name = name
                return self.action

        fake = FakeHwp()
        apply_charshape = namespace["문자모양_적용_현재선택"]
        apply_charshape.__globals__["hwp"] = fake
        apply_charshape(자간=0)
        self.assertEqual(fake.action_name, "CharShape")
        self.assertNotIn("Bold", fake.action.parameters.items)
        self.assertEqual(fake.action.parameters.items["SpacingHangul"], 0)

    def test_gui_initializes_without_callback_errors(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        with tempfile.TemporaryDirectory(prefix="hwp-docfit-test-") as settings_dir:
            with patch.dict(os.environ, {"APPDATA": settings_dir}):
                namespace = runpy.run_path(str(source), run_name="startup_test")
                root = namespace["TkinterDnD"].Tk()
                root.withdraw()
                callback_errors = []
                root.report_callback_exception = lambda *args: callback_errors.append(args)
                try:
                    app = namespace["HwpAutoDocFitGUI"](root)
                    root.update()
                    self.assertTrue(root.winfo_children())
                    self.assertEqual(callback_errors, [])
                    self.assertIsNone(app.worker)
                    self.assertFalse(app.running)
                finally:
                    root.destroy()


if __name__ == "__main__":
    unittest.main()
