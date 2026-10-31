import json
import queue
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from docfit_live.hotkeys import (
    DEFAULT_HOTKEYS,
    MOD_ALT,
    MOD_CONTROL,
    MOD_SHIFT,
    MOD_WIN,
    WM_HOTKEY,
    WM_QUIT,
    HotkeyService,
    parse_hotkey,
)


class FakeApi:
    def __init__(self, failures=None, register_gate=None):
        self.messages = queue.Queue()
        self.failures = failures or {}
        self.register_gate = register_gate
        self.registered = []
        self.unregistered = []
        self.posts = []
        self.registered_event = threading.Event()
        self.thread_id = 731

    def get_current_thread_id(self):
        return self.thread_id

    def peek_message(self, remove):
        return None

    def register_hotkey(self, hwnd, identifier, modifiers, vk):
        if self.register_gate is not None:
            self.register_gate.wait()
        if identifier in self.failures:
            return False, RuntimeError(self.failures[identifier])
        self.registered.append((hwnd, identifier, modifiers, vk))
        self.registered_event.set()
        return True, None

    def unregister_hotkey(self, hwnd, identifier):
        self.unregistered.append((hwnd, identifier))
        return True

    def post_thread_message(self, thread_id, message, wparam=0, lparam=0):
        self.posts.append((thread_id, message, wparam, lparam))
        self.messages.put((1, SimpleNamespace(message=message, wParam=wparam, lParam=lparam)))
        return True

    def get_message(self):
        message = self.messages.get()
        if message[1].message == WM_QUIT:
            return 0, message[1]
        return message

    def post_hotkey(self, identifier):
        self.messages.put((1, SimpleNamespace(message=WM_HOTKEY, wParam=identifier, lParam=0)))


class HotkeyParserTests(unittest.TestCase):
    def test_parse_hotkey_accepts_modifiers_letters_digits_and_function_keys(self):
        self.assertEqual(parse_hotkey("Ctrl+Alt+J"), (MOD_CONTROL | MOD_ALT, ord("J")))
        self.assertEqual(parse_hotkey(" Control + shift + 9 "), (MOD_CONTROL | MOD_SHIFT, ord("9")))
        self.assertEqual(parse_hotkey("win+f12"), (MOD_WIN, 0x7B))
        self.assertEqual(parse_hotkey("ALT+control+j"), (MOD_ALT | MOD_CONTROL, ord("J")))

    def test_parse_hotkey_rejects_empty_unknown_duplicate_and_missing_key(self):
        invalid = ("", "Ctrl+Bogus", "Ctrl+Ctrl+J", "Ctrl+J+K", "Ctrl+", "J", "Ctrl+F0", "Alt+F13", "Ctrl+한")
        for spec in invalid:
            with self.subTest(spec=spec):
                with self.assertRaisesRegex(ValueError, "[가-힣]"):
                    parse_hotkey(spec)


class HotkeyServiceTests(unittest.TestCase):
    def setUp(self):
        self.services = []

    def tearDown(self):
        for service in self.services:
            service.stop()

    def make_service(self, bindings, callback, api):
        service = HotkeyService(bindings, callback, api=api)
        self.services.append(service)
        return service

    def test_service_registers_bindings_and_dispatches_matching_message(self):
        api = FakeApi()
        received = queue.Queue()
        service = self.make_service(DEFAULT_HOTKEYS, received.put, api)
        service.start()
        self.assertTrue(api.registered_event.wait(1))
        self.assertEqual(len(api.registered), 3)
        api.post_hotkey(2)
        self.assertEqual(received.get(timeout=1), "table_template")
        self.assertTrue(received.empty())

    def test_service_keeps_running_when_one_registration_fails(self):
        api = FakeApi(failures={1: "이미 사용 중"})
        received = queue.Queue()
        service = self.make_service(DEFAULT_HOTKEYS, received.put, api)
        service.start()
        self.assertTrue(api.registered_event.wait(1))
        self.assertEqual(service.failed, [{"name": "panel", "hotkey": DEFAULT_HOTKEYS["panel"], "reason": "이미 사용 중"}])
        self.assertEqual([entry[1] for entry in api.registered], [2, 3])
        api.post_hotkey(3)
        self.assertEqual(received.get(timeout=1), "table_sketch")

    def test_service_stop_posts_quit_and_unregisters_successes(self):
        api = FakeApi(failures={2: "점유"})
        service = self.make_service(DEFAULT_HOTKEYS, Mock(), api)
        service.start()
        service.stop()
        self.assertIn((api.thread_id, WM_QUIT, 0, 0), api.posts)
        self.assertEqual(api.unregistered, [(None, 1), (None, 3)])

    def test_slow_registration_then_repeated_stop_are_safe(self):
        gate = threading.Event()
        api = FakeApi(register_gate=gate)
        service = self.make_service({"panel": "Ctrl+Alt+J"}, Mock(), api)
        opener = threading.Timer(0.1, gate.set)  # 등록이 늦어도 start()는 등록을 마칠 때까지 기다린다
        opener.start()
        service.start()
        self.assertTrue(gate.is_set())
        service.stop()
        service.stop()
        self.assertEqual([entry[1] for entry in api.registered], [1])
        self.assertEqual(api.unregistered, [(None, 1)])
        self.assertIn((api.thread_id, WM_QUIT, 0, 0), api.posts)
        self.assertFalse(service._thread and service._thread.is_alive())

    def test_service_start_waits_until_registration_failures_are_published(self):
        gate = threading.Event()
        api = FakeApi(failures={1: "이미 사용 중"}, register_gate=gate)
        service = self.make_service({"panel": "Ctrl+Alt+J"}, Mock(), api)
        started = threading.Event()

        def start_service():
            service.start()
            started.set()

        thread = threading.Thread(target=start_service)
        thread.start()
        self.assertFalse(started.wait(0.05))
        gate.set()
        self.assertTrue(started.wait(1))
        thread.join(1)
        self.assertEqual(service.failed, [{"name": "panel", "hotkey": "Ctrl+Alt+J", "reason": "이미 사용 중"}])
        service.stop()

    def test_service_callback_error_does_not_kill_message_loop(self):
        api = FakeApi()
        received = queue.Queue()

        def callback(name):
            if name == "panel":
                raise RuntimeError("callback error")
            received.put(name)

        service = self.make_service(DEFAULT_HOTKEYS, callback, api)
        service.start()
        api.post_hotkey(1)
        api.post_hotkey(2)
        self.assertEqual(received.get(timeout=1), "table_template")
        self.assertTrue(service._thread.is_alive())


class LiveHotkeyBridgeTests(unittest.TestCase):
    def bridge(self, tmp_path):
        from desktop_web_ui import DesktopWebBridge

        gui = SimpleNamespace(_한글_서비스=lambda: SimpleNamespace(settings=None))
        bridge = DesktopWebBridge.__new__(DesktopWebBridge)
        bridge.gui = gui
        bridge._hotkeys = None
        bridge._hotkey_lock = threading.RLock()
        bridge._hotkey_state_lock = threading.Lock()
        bridge._last_hotkey = None
        bridge._last_hotkey_at = None
        bridge._test_settings_path = tmp_path / "settings.json"
        from docfit_app.settings_service import SettingsService
        bridge._configuration = lambda: SimpleNamespace(store=SettingsService(bridge._test_settings_path))
        return bridge

    def test_live_hotkeys_get_uses_defaults_and_is_browser_exposed(self):
        from desktop_web_ui import _BrowserApi

        bridge = self.bridge(self._tmp_path())
        bridge._ensure_hotkeys = lambda: SimpleNamespace(snapshot=lambda: {"bindings": dict(DEFAULT_HOTKEYS), "failed": []})
        result = bridge.live_hotkeys("get")
        self.assertEqual(result["bindings"], DEFAULT_HOTKEYS)
        self.assertEqual(result["failed"], [])
        self.assertTrue(callable(_BrowserApi(bridge).live_hotkeys))

    def _tmp_path(self):
        from tempfile import TemporaryDirectory
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        from pathlib import Path
        return Path(directory.name)

    def test_live_hotkeys_set_persists_and_preserves_other_settings(self):
        bridge = self.bridge(self._tmp_path())
        bridge._configuration().store.update(lambda settings: settings.update({"other": "keep"}))
        made = []

        class Service:
            def __init__(self, bindings, callback):
                self.bindings = dict(bindings)
                self.callback = callback
            def start(self):
                self.started = True
            def stop(self):
                self.stopped = True
            def snapshot(self):
                return {"bindings": self.bindings, "failed": []}

        def factory(bindings, callback):
            service = Service(bindings, callback)
            made.append(service)
            return service

        import docfit_live.hotkeys as hotkeys
        original = hotkeys.HotkeyService
        self.addCleanup(setattr, hotkeys, "HotkeyService", original)
        hotkeys.HotkeyService = factory
        result = bridge.live_hotkeys("set", {"bindings": {"panel": "Ctrl+Shift+P"}})
        self.assertTrue(result["ok"])
        saved = bridge._configuration().store.read()
        self.assertEqual(saved["other"], "keep")
        self.assertEqual(saved["hotkeys"]["panel"], "Ctrl+Shift+P")
        self.assertEqual(result["bindings"]["table_template"], DEFAULT_HOTKEYS["table_template"])
        self.assertEqual(len(made), 1)

    def test_live_hotkeys_set_rejects_duplicate_or_invalid_without_mutation(self):
        bridge = self.bridge(self._tmp_path())
        before = bridge._configuration().store.read()
        for bindings in (
            {"panel": "Ctrl+Alt+J", "table_template": "Control+ALT+j"},
            {"panel": "Ctrl+F13"},
            {"unknown": "Ctrl+Alt+J"},
        ):
            result = bridge.live_hotkeys("set", {"bindings": bindings})
            self.assertFalse(result["ok"])
            self.assertEqual(bridge._configuration().store.read(), before)
            self.assertIsNone(bridge._hotkeys)

    def test_live_hotkey_callback_updates_state_only(self):
        bridge = self.bridge(self._tmp_path())
        bridge._hotkey_callback("panel")
        state = {"last_hotkey": bridge._last_hotkey, "last_hotkey_at": bridge._last_hotkey_at}
        self.assertEqual(state["last_hotkey"], "panel")
        self.assertTrue(state["last_hotkey_at"])

    def test_live_hotkeys_unknown_action_returns_error(self):
        bridge = self.bridge(self._tmp_path())
        result = bridge.live_hotkeys("unknown")
        self.assertFalse(result["ok"])
        self.assertTrue(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
