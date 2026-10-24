"""T17: 기본 Flutter 경로는 미구현 안내, 명시적 Tk 폴백은 기존 호출 유지."""
import unittest
from unittest.mock import Mock
from desktop_web_ui import DesktopWebBridge, _BrowserApi


class TestV2T17(unittest.TestCase):
    def bridge(self, fallback=False):
        gui = Mock(ui_tk_fallback=fallback)
        gui.ui_tk_fallback_var = None
        bridge = DesktopWebBridge(gui)
        bridge._tk = Mock(side_effect=lambda callback, **kwargs: callback())
        bridge.get_state = Mock(return_value={"status": "대기 중"})
        return bridge, gui

    def test_default_never_opens_tk_or_claims_success(self):
        bridge, gui = self.bridge()
        for index in (0, 1, -1, None, "bad"):
            result = bridge.open_diff(index)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "DIFF_BACKEND_NOT_READY")
            self.assertIn("아직 연결되지 않았습니다", result["error"])
        gui.비교창_준비.assert_not_called()
        bridge._tk.assert_not_called()

    def test_explicit_fallback_preserves_existing_call_and_state(self):
        bridge, gui = self.bridge(True)
        self.assertEqual(bridge.open_diff(), {"status": "대기 중", "ok": True, "tk_fallback": True})
        gui.비교창_준비.assert_called_once_with()
        bridge._tk.assert_called_once_with(gui.비교창_준비, timeout=None, front=True)

    def test_aliases_cannot_bypass_default_guard(self):
        bridge, gui = self.bridge()
        for name in ("compare_result", "launch_external_hwp_diff"):
            self.assertEqual(getattr(bridge, name)(1)["code"], "DIFF_BACKEND_NOT_READY")
        gui.비교창_준비.assert_not_called()
        bridge._tk.assert_not_called()

    def test_browser_exposes_guarded_entrypoints(self):
        bridge, _ = self.bridge()
        api = _BrowserApi(bridge)
        for name in ("open_diff", "compare_result", "launch_external_hwp_diff"):
            self.assertEqual(getattr(api, name)(0)["code"], "DIFF_BACKEND_NOT_READY")


if __name__ == "__main__":
    unittest.main()
