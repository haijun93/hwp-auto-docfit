"""'항상 위': pywebview 6 창에는 set_on_top이 없고 on_top 속성만 있다(사용자 보고 2026-11-07)."""
import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location("desktop_web_ui_ontop", Path(__file__).resolve().parents[1] / "desktop_web_ui.py")


class WindowOnTopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(cls.module)

    def test_property_only_window(self):
        class Window:
            on_top = False
        w = Window()
        self.module._set_window_on_top(w, True)
        self.assertTrue(w.on_top)
        self.module._set_window_on_top(w, 0)
        self.assertIs(w.on_top, False)

    def test_legacy_setter_still_used(self):
        calls = []

        class Window:
            def set_on_top(self, value):
                calls.append(value)
        self.module._set_window_on_top(Window(), 1)
        self.assertEqual(calls, [True])

    def test_no_direct_set_on_top_calls_remain(self):
        source = (Path(__file__).resolve().parents[1] / "desktop_web_ui.py").read_text(encoding="utf-8")
        self.assertEqual(source.count(".set_on_top("), 0)


if __name__ == "__main__":
    unittest.main()
