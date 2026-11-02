import unittest
from types import SimpleNamespace

from desktop_web_ui import (
    _append_webview_rendering_arguments,
    _install_webview_rendering_guard,
)


class WebViewRenderingGuardTests(unittest.TestCase):
    def test_browser_flags_preserve_and_merge_existing_options(self):
        result = _append_webview_rendering_arguments(
            "--disable-features=ElasticOverscroll,CalculateNativeWinOcclusion --remote-debugging-port=1234"
        )
        self.assertEqual(result.count("--disable-features="), 1)
        self.assertIn("--disable-features=ElasticOverscroll,CalculateNativeWinOcclusion", result)
        self.assertIn("--remote-debugging-port=1234", result)
        self.assertEqual(result.count("--disable-renderer-backgrounding"), 1)
        self.assertEqual(result.count("--disable-background-timer-throttling"), 1)
        self.assertEqual(result.count("--disable-backgrounding-occluded-windows"), 1)

    def test_webview_applies_flags_before_core_initialization(self):
        class FakeWebView2:
            def __init__(self):
                self.CreationProperties = SimpleNamespace(
                    AdditionalBrowserArguments="--disable-features=ElasticOverscroll"
                )
                self.initialized_with = None

            def EnsureCoreWebView2Async(self, *args, **kwargs):
                self.initialized_with = self.CreationProperties.AdditionalBrowserArguments
                return "initialized"

        module = SimpleNamespace(WebView2=FakeWebView2)
        self.assertTrue(_install_webview_rendering_guard(module))
        webview = module.WebView2()
        self.assertEqual(webview.EnsureCoreWebView2Async(None), "initialized")
        self.assertIn("--disable-renderer-backgrounding", webview.initialized_with)
        self.assertIn("--disable-backgrounding-occluded-windows", webview.initialized_with)
        self.assertIn("--disable-features=ElasticOverscroll,CalculateNativeWinOcclusion", webview.initialized_with)

    def test_installing_guard_twice_does_not_wrap_again(self):
        class FakeWebView2:
            def EnsureCoreWebView2Async(self):
                return "ok"

        module = SimpleNamespace(WebView2=FakeWebView2)
        self.assertTrue(_install_webview_rendering_guard(module))
        guarded_type = module.WebView2
        self.assertTrue(_install_webview_rendering_guard(module))
        self.assertIs(module.WebView2, guarded_type)


if __name__ == "__main__":
    unittest.main()
