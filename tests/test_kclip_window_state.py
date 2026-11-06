import copy
import unittest

from docfit_app import kclip_window_state as state


class _Store:
    def __init__(self, data=None):
        self.data = data or {}

    def read(self):
        return copy.deepcopy(self.data)

    def update(self, change):
        updated = copy.deepcopy(self.data)
        change(updated)
        self.data = updated
        return updated


class KClipWindowStateTest(unittest.TestCase):
    def test_defaults_when_nothing_saved(self):
        self.assertEqual(state.load(_Store()), state.DEFAULTS)

    def test_save_and_restore_geometry_and_topmost(self):
        store = _Store({"always_on_top": True, "other": 1})
        saved = state.save(store, {"x": 120, "y": 40.6, "width": 500, "height": 600, "always_on_top": True})
        self.assertEqual(saved, {"x": 120, "y": 41, "width": 500, "height": 600, "always_on_top": True})
        self.assertEqual(state.load(store), saved)
        # 다른 설정은 건드리지 않는다.
        self.assertEqual(store.data["other"], 1)
        self.assertTrue(store.data["always_on_top"])

    def test_partial_update_keeps_previous_values(self):
        store = _Store()
        state.save(store, {"x": 10, "y": 20, "width": 700, "height": 500})
        state.save(store, {"always_on_top": True})
        self.assertEqual(state.load(store), {"x": 10, "y": 20, "width": 700, "height": 500, "always_on_top": True})

    def test_invalid_values_are_clamped_or_ignored(self):
        store = _Store({state.SETTINGS_KEY: {"x": "a", "y": True, "width": 10, "height": 99999,
                                             "always_on_top": "yes"}})
        self.assertEqual(state.load(store), {"x": None, "y": None, "width": state.MIN_WIDTH,
                                             "height": state.MAX_SIZE, "always_on_top": False})
        self.assertEqual(state.load(_Store({state.SETTINGS_KEY: "broken"})), state.DEFAULTS)
        self.assertEqual(state.normalize({"x": float("nan"), "y": -10 ** 9})["y"], -state.MAX_OFFSET)

    def test_unreadable_settings_fall_back_to_defaults(self):
        class Broken(_Store):
            def read(self):
                raise OSError("locked")
        self.assertEqual(state.load(Broken()), state.DEFAULTS)

    def test_command_applies_topmost_and_close_restores_app_setting(self):
        store = _Store()
        applied = []
        result = state.command(store, "open", None, applied.append)
        self.assertTrue(result["ok"])
        self.assertEqual(applied, [None])
        state.command(store, "set", {"always_on_top": True}, applied.append)
        self.assertEqual(applied[-1], True)
        result = state.command(store, "open", {}, applied.append)
        self.assertTrue(result["window"]["always_on_top"])
        self.assertEqual(applied[-1], True)
        state.command(store, "close", {}, applied.append)
        self.assertIsNone(applied[-1])
        # 닫아도 저장값은 남아 다음에 다시 항상 위로 열린다.
        self.assertTrue(state.command(store, "get")["window"]["always_on_top"])
        self.assertFalse(state.command(store, "bogus")["ok"])

    def test_topmost_failure_does_not_break_saving(self):
        store = _Store()

        def boom(_):
            raise RuntimeError("no window")
        result = state.command(store, "set", {"width": 600}, boom)
        self.assertTrue(result["ok"])
        self.assertEqual(state.load(store)["width"], 600)

    def test_window_commands_never_touch_agent(self):
        import sys
        before = "docfit_app.kclip_service" in sys.modules
        store = _Store()
        for action in ("open", "set", "close", "get"):
            state.command(store, action, {"x": 1})
        self.assertEqual("docfit_app.kclip_service" in sys.modules, before)


class KClipWindowDispatchTest(unittest.TestCase):
    def test_browser_api_exposes_kclip_window(self):
        import desktop_web_ui

        class Bridge:
            def __getattr__(self, name):
                return name
        api = desktop_web_ui._BrowserApi(Bridge())
        self.assertEqual(api.kclip_window, "kclip_window")

    def test_bridge_kclip_window_saves_and_toggles_native_topmost(self):
        import desktop_web_ui

        store = _Store({"always_on_top": False})

        class Window:
            def __init__(self):
                self.on_top = []

            def set_on_top(self, value):
                self.on_top.append(value)

        class Service:
            settings = store

        class Gui:
            def _준말_서비스(self):
                return Service()

        bridge = desktop_web_ui.DesktopWebBridge.__new__(desktop_web_ui.DesktopWebBridge)
        bridge.gui = Gui()
        bridge.window = Window()
        bridge._tk = lambda fn: fn()
        result = bridge.kclip_window("set", {"x": 5, "always_on_top": True})
        self.assertTrue(result["ok"])
        self.assertEqual(bridge.window.on_top, [True])
        bridge.kclip_window("close")
        self.assertEqual(bridge.window.on_top, [True, False])
        self.assertTrue(store.data[state.SETTINGS_KEY]["always_on_top"])


if __name__ == "__main__":
    unittest.main()
