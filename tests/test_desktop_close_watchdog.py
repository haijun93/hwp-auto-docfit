"""Native close stays bounded without bypassing a live save confirmation."""
from queue import Queue
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from desktop_web_ui import DesktopWebBridge


class CloseWatchdogTests(unittest.TestCase):
    def setUp(self):
        self.callbacks = Queue()
        self.root = SimpleNamespace(after=lambda delay, cb: self.callbacks.put(cb), destroy=Mock())
        self.gui = SimpleNamespace(root=self.root, running=False, 종료=Mock())
        self.bridge = DesktopWebBridge(self.gui)
        self.bridge.tk_stopped = Event()
        self.addCleanup(self.bridge._shutdown)
        self.bridge.enable_close_guard()
        self.timers = []

        def timer(seconds, callback, args):
            timer = Mock(fire=lambda: callback(*args))
            self.timers.append(timer)
            return timer

        self.patcher = patch('desktop_web_ui.threading.Timer', side_effect=timer)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_second_native_close_releases_requests_and_cleans_up_without_tk_wait(self):
        with patch('docfit_core.hwp_process.kill_owned') as cleanup:
            self.assertFalse(self.bridge.request_close())
            self.assertTrue(self.bridge.request_close())
            callback = self.callbacks.get(timeout=2)
            callback()
            cleanup.assert_called_once_with()
        self.assertTrue(self.bridge.tk_stopped.is_set())
        self.assertTrue(self.bridge.user_closing)
        self.root.destroy.assert_called_once_with()
        self.gui.종료.assert_not_called()  # would prompt or touch Tk on the native thread

    def test_unanswered_first_close_exits_via_watcher(self):
        self.bridge._force_close = Mock()
        self.assertFalse(self.bridge.request_close())
        self.timers[0].fire()
        self.bridge._force_close.assert_called_once_with(native_event=False)
        self.assertIsNone(self.bridge._close_request)

    def test_polling_without_handling_close_does_not_disable_timeout(self):
        self.bridge._force_close = Mock()
        self.bridge.request_close()
        self.assertEqual(self.bridge._pending_dialog()['kind'], 'app_close')
        self.timers[0].fire()
        self.bridge._force_close.assert_called_once()

    def test_live_confirmation_can_wait_then_cancel_and_ask_again(self):
        self.bridge._force_close = Mock()
        self.bridge.request_close()
        identifier = self.bridge._close_request['id']
        self.assertEqual(self.bridge.acknowledge_close(identifier), {'ok': True})
        self.timers[0].fire()  # already dispatched timer loses to acknowledgement
        self.bridge._force_close.assert_not_called()
        self.assertEqual(self.bridge.resolve_dialog(identifier, False), {'accepted': False})
        self.assertFalse(self.bridge.request_close())
        self.assertNotEqual(self.bridge._close_request['id'], identifier)
        self.timers[0].fire()  # old generation must not close the new request
        self.bridge._force_close.assert_not_called()

    def test_stale_acknowledgement_does_not_disable_timeout(self):
        self.bridge._force_close = Mock()
        self.bridge.request_close()
        self.assertEqual(self.bridge.acknowledge_close('stale'), {'ok': False})
        self.timers[0].fire()
        self.bridge._force_close.assert_called_once()

    def test_accepted_close_uses_existing_tk_shutdown(self):
        self.bridge._tk = lambda cb, **kw: cb()
        self.root.winfo_exists = lambda: False
        self.bridge.request_close()
        identifier = self.bridge._close_request['id']
        self.bridge.acknowledge_close(identifier)
        self.assertEqual(self.bridge.resolve_dialog(identifier, True), {'accepted': True})
        self.gui.종료.assert_called_once_with()




class SmokeCdpPortTests(unittest.TestCase):
    def test_port_only_from_valid_smoke_variable(self):
        from desktop_web_ui import smoke_cdp_port
        self.assertIsNone(smoke_cdp_port({}))
        self.assertEqual(smoke_cdp_port({"DOCFIT_SMOKE_CDP_PORT": "57179"}), 57179)
        for bad in ("", "80", "70000", "9222; x", "-1"):
            self.assertIsNone(smoke_cdp_port({"DOCFIT_SMOKE_CDP_PORT": bad}))


if __name__ == '__main__':
    unittest.main()
