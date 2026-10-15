import unittest
from unittest.mock import Mock, patch

from scripts.browser_qa import launch_browser


class BrowserQaTests(unittest.TestCase):
    def test_windows_uses_isolated_headless_edge(self):
        playwright = Mock()
        with patch('scripts.browser_qa.sys.platform', 'win32'), patch.dict(
                'os.environ', {}, clear=True):
            launch_browser(playwright)
        playwright.chromium.launch.assert_called_once_with(channel='msedge', headless=True)

    def test_explicit_browser_path_wins(self):
        playwright = Mock()
        with patch.dict('os.environ', {'DOCFIT_QA_BROWSER_PATH': 'browser.exe'}):
            launch_browser(playwright)
        playwright.chromium.launch.assert_called_once_with(executable_path='browser.exe', headless=True)

    def test_bundled_browser_fallback(self):
        playwright = Mock()
        with patch('scripts.browser_qa.sys.platform', 'linux'), patch.dict(
                'os.environ', {}, clear=True), patch('scripts.browser_qa.Path.is_file', return_value=False):
            launch_browser(playwright)
        playwright.chromium.launch.assert_called_once_with(headless=True)


if __name__ == '__main__':
    unittest.main()
