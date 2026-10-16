"""Exercise real bridge dispatch without a Windows desktop or HWP COM."""

from concurrent.futures import Future, TimeoutError
from queue import Queue
from threading import Event, Thread
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from desktop_web_ui import DesktopWebBridge


class QueuedRoot:
    def __init__(self):
        self.callbacks = Queue()

    def after(self, delay, callback):
        self.callbacks.put(callback)


class RequestLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.root = QueuedRoot()
        self.bridge = DesktopWebBridge(SimpleNamespace(root=self.root))
        self.bridge.tk_stopped = Event()

    def call_in_thread(self, callback, timeout=None):
        outcome = Future()

        def call():
            try:
                outcome.set_result(self.bridge._tk(callback, timeout=timeout))
            except BaseException as exc:
                outcome.set_exception(exc)

        thread = Thread(target=call, daemon=True)
        thread.start()
        return thread, outcome, self.root.callbacks.get(timeout=2)

    def test_timed_out_queued_command_never_runs_later(self):
        callback = Mock()
        with self.assertRaisesRegex(RuntimeError, "초과"):
            self.bridge._tk(callback, timeout=0)
        self.root.callbacks.get_nowait()()
        callback.assert_not_called()

    def test_shutdown_releases_indefinite_wait_and_rejects_new_requests(self):
        callback = Mock()
        thread, outcome, dispatch = self.call_in_thread(callback)
        self.bridge._shutdown()
        with self.assertRaisesRegex(RuntimeError, "종료"):
            outcome.result(timeout=2)
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        dispatch()
        callback.assert_not_called()
        with self.assertRaisesRegex(RuntimeError, "종료"):
            self.bridge._tk(callback)
        self.assertTrue(self.root.callbacks.empty())
        self.bridge._shutdown()  # Repeated shutdown is safe.

    def test_running_callback_survives_timeout_without_invalid_future_state(self):
        entered, release = Event(), Event()
        calls, dispatch_errors = [], []

        class TimeoutAfterStart(Future):
            def result(self, timeout=None):
                if timeout is not None:
                    if not entered.wait(2):
                        raise AssertionError("callback did not start")
                    return super().result(timeout=0)
                return super().result(timeout=timeout)

        def callback():
            calls.append("started")
            entered.set()
            if not release.wait(2):
                raise AssertionError("callback was not released")
            calls.append("finished")

        def dispatch_safely(dispatch):
            try:
                dispatch()
            except BaseException as exc:
                dispatch_errors.append(exc)

        with patch("desktop_web_ui.Future", TimeoutAfterStart):
            thread, outcome, dispatch = self.call_in_thread(callback, timeout=1)
            tk_thread = Thread(target=dispatch_safely, args=(dispatch,), daemon=True)
            tk_thread.start()
            try:
                with self.assertRaisesRegex(RuntimeError, "실행 중"):
                    outcome.result(timeout=2)
            finally:
                release.set()
                tk_thread.join(timeout=2)
                thread.join(timeout=2)
        self.assertEqual(calls, ["started", "finished"])
        self.assertEqual(dispatch_errors, [])
        self.assertEqual(self.bridge._requests, set())

    def test_shutdown_during_callback_does_not_break_its_completion(self):
        thread, outcome, dispatch = self.call_in_thread(self.bridge._shutdown)
        dispatch()
        with self.assertRaisesRegex(RuntimeError, "종료"):
            outcome.result(timeout=2)
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())

    def test_callback_timeout_error_is_not_reported_as_dispatch_timeout(self):
        original = TimeoutError("operation-specific timeout")

        def callback():
            raise original

        thread, outcome, dispatch = self.call_in_thread(callback, timeout=2)
        dispatch()
        with self.assertRaises(TimeoutError) as caught:
            outcome.result(timeout=2)
        self.assertIs(caught.exception, original)
        thread.join(timeout=2)

    def test_scheduling_failure_does_not_leave_pending_request(self):
        self.root.after = Mock(side_effect=RuntimeError("Tk unavailable"))
        with self.assertRaisesRegex(RuntimeError, "종료"):
            self.bridge._tk(Mock())
        self.assertEqual(self.bridge._requests, set())

    def test_close_that_destroys_tk_is_accepted_by_webview(self):
        self.root.winfo_exists = Mock(return_value=True)

        def destroy():
            self.bridge._shutdown()
            self.root.winfo_exists.return_value = False

        self.bridge.gui.종료 = destroy
        outcome = Future()

        def close():
            try:
                outcome.set_result(self.bridge.request_close())
            except BaseException as exc:
                outcome.set_exception(exc)

        thread = Thread(target=close, daemon=True)
        thread.start()
        self.root.callbacks.get(timeout=2)()
        self.assertTrue(outcome.result(timeout=2))
        self.assertTrue(self.bridge.user_closing)
        thread.join(timeout=2)

    def test_cancelled_close_keeps_bridge_available(self):
        self.root.winfo_exists = Mock(return_value=True)
        self.root.after = lambda _delay, callback: callback()
        self.bridge.gui.종료 = Mock()  # User declines the existing close prompt.
        self.assertFalse(self.bridge.request_close())
        self.assertFalse(self.bridge.user_closing)
        self.assertEqual(self.bridge._tk(lambda: "still open"), "still open")


if __name__ == "__main__":
    unittest.main()
