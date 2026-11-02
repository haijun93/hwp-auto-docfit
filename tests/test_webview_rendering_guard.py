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

    def test_renderer_process_failure_reloads_initialized_page(self):
        class Event:
            def __init__(self):
                self.handler = None

            def __iadd__(self, handler):
                self.handler = handler
                return self

        class FakeWebView2:
            def __init__(self):
                self.CreationProperties = SimpleNamespace(AdditionalBrowserArguments="")
                self.CoreWebView2InitializationCompleted = Event()
                self.CoreWebView2 = SimpleNamespace(ProcessFailed=Event(), reloads=0)
                self.CoreWebView2.Reload = lambda: setattr(
                    self.CoreWebView2, "reloads", self.CoreWebView2.reloads + 1
                )

            def EnsureCoreWebView2Async(self, *args, **kwargs):
                self.CoreWebView2InitializationCompleted.handler(self, None)
                return "initialized"

        module = SimpleNamespace(WebView2=FakeWebView2)
        _install_webview_rendering_guard(module)
        view = module.WebView2()
        view.EnsureCoreWebView2Async()
        view.CoreWebView2.ProcessFailed.handler(view.CoreWebView2, None)
        self.assertEqual(view.CoreWebView2.reloads, 1)


if __name__ == "__main__":
    unittest.main()
