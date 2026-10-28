"""텍스트 추가의 Flutter 경계와 명시적 Tk 폴백을 무인 검증한다."""
import unittest
from unittest import mock

from test_desktop_browser_api import _FakeGui, _Var, _bridge


class TextInputRoutingTest(unittest.TestCase):
    def test_flutter_rejects_both_legacy_entry_points_without_opening_tk(self):
        gui = _FakeGui()
        gui.ui_tk_fallback_var = _Var(False)
        gui._텍스트로_문서추가_열기 = mock.Mock(side_effect=AssertionError("Tk 창 호출"))
        bridge = _bridge(gui)
        with mock.patch("tkinter.Toplevel", side_effect=AssertionError("Tk 창 생성")):
            self.assertEqual(bridge.text_input(), {"ok": False, "error": "FLUTTER_ONLY"})
            self.assertEqual(bridge.run_tool("paste"), {"ok": False, "error": "FLUTTER_ONLY"})
        gui._텍스트로_문서추가_열기.assert_not_called()

    def test_explicit_fallback_opens_original_text_window_for_both_commands(self):
        gui = _FakeGui()
        gui.ui_tk_fallback_var = _Var(True)
        gui._텍스트로_문서추가_열기 = mock.Mock()
        bridge = _bridge(gui)
        with mock.patch.object(bridge, "get_state", return_value={"files": []}):
            self.assertEqual(bridge.text_input(), {"files": []})
            self.assertTrue(bridge.run_tool("paste"))
        self.assertEqual(gui._텍스트로_문서추가_열기.call_args_list, [mock.call(), mock.call()])

    def test_unknown_tool_still_rejected_in_flutter_and_fallback(self):
        for fallback in (False, True):
            gui = _FakeGui()
            gui.ui_tk_fallback_var = _Var(fallback)
            gui._텍스트로_문서추가_열기 = mock.Mock()
            with self.subTest(fallback=fallback), self.assertRaises(ValueError):
                _bridge(gui).run_tool("review")
            gui._텍스트로_문서추가_열기.assert_not_called()
