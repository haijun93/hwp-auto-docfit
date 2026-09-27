import unittest

from desktop_web_ui import DesktopWebBridge, _BrowserApi


class BrowserApiTests(unittest.TestCase):
    def test_only_commands_exposed_not_native_window_or_tk_graph(self):
        bridge = DesktopWebBridge(object())
        bridge.window = object()
        api = _BrowserApi(bridge)
        public = {name: getattr(api, name) for name in dir(api) if not name.startswith('_')}
        self.assertEqual(len(public), 17)
        self.assertTrue(all(callable(value) for value in public.values()))
        self.assertNotIn('gui', public)
        self.assertNotIn('window', public)
        self.assertNotIn('request_close', public)
        self.assertEqual(api.get_state, bridge.get_state)


if __name__ == '__main__':
    unittest.main()
