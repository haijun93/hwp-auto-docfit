"""T17: 원본·결과 비교. 기본은 글 비교 HTML(2.0.6), 명시적 Tk 폴백은 기존 호출 유지."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from desktop_web_ui import DesktopWebBridge, _BrowserApi
from docfit_app.result_compare import build_report, document_lines


class TestV2T17(unittest.TestCase):
    def bridge(self, fallback=False, results=None):
        gui = Mock(ui_tk_fallback=fallback)
        gui.ui_tk_fallback_var = None
        gui._결과목록 = results or []
        bridge = DesktopWebBridge(gui)
        bridge._tk = Mock(side_effect=lambda callback, **kwargs: callback())
        bridge.get_state = Mock(return_value={"status": "대기 중"})
        return bridge, gui

    def test_missing_files_never_open_tk_or_claim_success(self):
        bridge, gui = self.bridge()
        for index in (0, 1, -1, None, "bad"):
            result = bridge.open_diff(index)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "DIFF_FILE_MISSING")
        gui.비교창_준비.assert_not_called()
        bridge._tk.assert_not_called()

    def test_explicit_fallback_preserves_existing_call_and_state(self):
        bridge, gui = self.bridge(True)
        self.assertEqual(bridge.open_diff(), {"status": "대기 중", "ok": True, "tk_fallback": True})
        gui.비교창_준비.assert_called_once_with()
        bridge._tk.assert_called_once_with(gui.비교창_준비, timeout=None, front=True)

    def test_text_results_open_a_side_by_side_report(self):
        with tempfile.TemporaryDirectory() as folder:
            original, result = Path(folder) / "원본.md", Path(folder) / "결과.md"
            original.write_text("가 문장\n나 문장\n다 문장\n", encoding="utf-8")
            result.write_text("가 문장\n나 고친 문장\n다 문장\n라 더한 문장\n", encoding="utf-8")
            bridge, gui = self.bridge(results=[{"원본": str(original), "결과": str(result)}])
            with patch("os.startfile", create=True) as start:
                outcome = bridge.open_diff(0)
            self.assertTrue(outcome["ok"])
            report = Path(outcome["report"])
            start.assert_called_once_with(str(report))
            page = report.read_text(encoding="utf-8")
            self.assertIn("나 고친 문장", page)
            self.assertIn("diff_add", page)
            self.assertIn("바뀐 줄 약 2줄", page)
            gui.비교창_준비.assert_not_called()

    def test_unsupported_format_is_a_clear_message(self):
        with tempfile.TemporaryDirectory() as folder:
            original, result = Path(folder) / "원본.hwp", Path(folder) / "결과.hwp"
            original.write_bytes(b"x")
            result.write_bytes(b"y")
            bridge, _ = self.bridge(results=[{"원본": str(original), "결과": str(result)}])
            outcome = bridge.open_diff(0)
            self.assertEqual(outcome["code"], "DIFF_UNSUPPORTED")
            self.assertIn("HWPX·PDF·MD·TXT", outcome["error"])

    def test_aliases_and_browser_entrypoints_use_the_same_path(self):
        bridge, _ = self.bridge()
        for name in ("compare_result", "launch_external_hwp_diff"):
            self.assertEqual(getattr(bridge, name)(1)["code"], "DIFF_FILE_MISSING")
        api = _BrowserApi(bridge)
        for name in ("open_diff", "compare_result", "launch_external_hwp_diff"):
            self.assertEqual(getattr(api, name)(0)["code"], "DIFF_FILE_MISSING")

    def test_hwpx_text_is_compared(self):
        sample = Path(__file__).resolve().parents[1] / "resources" / "서식예시" / "표 서식모음 추가.hwpx"
        lines = document_lines(sample)
        self.assertTrue(any("사업개요표" in line for line in lines))
        with tempfile.TemporaryDirectory() as folder:
            report = build_report(sample, sample, Path(folder) / "same.html")
            self.assertIn("바뀐 줄 약 0줄", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
