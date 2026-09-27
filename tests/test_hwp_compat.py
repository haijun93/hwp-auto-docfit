"""한컴오피스 NEO/2020 COM 자동화 호환성 검사."""
from pathlib import Path
import runpy
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


class HwpComCompatibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))

    def test_dispatchex_is_preferred_and_dispatch_is_fallback(self):
        create = self.ns["한글_COM_인스턴스_생성"]
        instance = object()
        com = SimpleNamespace(
            DispatchEx=Mock(side_effect=OSError("DispatchEx unavailable")),
            Dispatch=Mock(return_value=instance),
        )
        with patch.dict(create.__globals__, {"win32": com}):
            self.assertIs(create(), instance)
        com.DispatchEx.assert_called_once_with("HwpFrame.HwpObject")
        com.Dispatch.assert_called_once_with("HwpFrame.HwpObject")

    def test_open_uses_positional_arguments_first(self):
        open_document = self.ns["한글_문서_열기"]
        app = SimpleNamespace(Open=Mock(return_value=True))
        self.assertTrue(open_document(app, Path("sample.hwpx"), "HWPX", "forceopen:true"))
        app.Open.assert_called_once_with("sample.hwpx", "HWPX", "forceopen:true")

    def test_open_retries_named_arguments_for_early_bound_wrappers(self):
        open_document = self.ns["한글_문서_열기"]
        app = SimpleNamespace(Open=Mock(side_effect=[TypeError("keyword-only wrapper"), True]))
        self.assertTrue(open_document(app, "sample.hwp", "HWP", ""))
        self.assertEqual(app.Open.call_count, 2)
        self.assertEqual(app.Open.call_args_list[1].kwargs, {"Format": "HWP", "arg": ""})


if __name__ == "__main__":
    unittest.main()
