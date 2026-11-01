import queue
import threading
import unittest
from types import SimpleNamespace

from docfit_live.tray import (
    MENU_EXIT,
    MENU_HELPER,
    MENU_RESTORE,
    WM_QUIT,
    WM_RBUTTONUP,
    WM_TRAY,
    TrayService,
    handle_tray_message,
)


class FakeTrayApi:
    def __init__(self, selection=0):
        self.messages = queue.Queue()
        self.selection = selection
        self.added = []
        self.removed = 0
        self.posts = []
        self.thread_id = 827
        self.ready = threading.Event()
        self.menu_shown = threading.Event()

    def get_current_thread_id(self):
        return self.thread_id

    def peek_message(self, remove=False):
        return None

    def add_icon(self, thread_id):
        self.added.append(thread_id)

    def remove_icon(self):
        self.removed += 1

    def show_menu(self, thread_id):
        self.menu_shown.set()
        return self.selection

    def post_thread_message(self, thread_id, message, wparam=0, lparam=0):
        self.posts.append((thread_id, message, wparam, lparam))
        self.messages.put((0, SimpleNamespace(message=message, wParam=wparam, lParam=lparam)))

    def get_message(self):
        return self.messages.get()

    def post_menu(self, selection):
        self.selection = selection
        self.messages.put((1, SimpleNamespace(message=WM_TRAY, wParam=0, lParam=WM_RBUTTONUP)))


class TrayMessageTests(unittest.TestCase):
    def test_menu_selections_dispatch_expected_actions(self):
        for selection, expected in (
            (MENU_HELPER, "panel"), (MENU_RESTORE, "restore"), (MENU_EXIT, "exit")
        ):
            with self.subTest(selection=selection):
                calls = []
                handled = handle_tray_message(
                    (WM_TRAY, 0, WM_RBUTTONUP), show_menu=lambda _thread: selection,
                    dispatch=calls.append, restore_window=lambda: calls.append("double_click_restore"),
                    thread_id=827,
                )
                self.assertTrue(handled)
                self.assertEqual(calls, [expected])

    def test_unrelated_messages_are_ignored(self):
        calls = []
        self.assertFalse(handle_tray_message(
            (WM_TRAY + 1, 0, WM_RBUTTONUP), show_menu=lambda _thread: MENU_HELPER,
            dispatch=calls.append, restore_window=lambda: None, thread_id=827,
        ))
        self.assertEqual(calls, [])

    def test_stop_removes_icon_and_joins_message_thread(self):
        api = FakeTrayApi()
        actions = []
        service = TrayService(actions.append, api=api)
        service.start()
        self.assertEqual(api.added, [api.thread_id])
        service.stop()
        self.assertEqual(api.removed, 1)
        self.assertFalse(service._thread)
        self.assertEqual(api.posts[0][1], WM_QUIT)

    def test_menu_action_is_delivered_and_icon_removed_on_shutdown(self):
        api = FakeTrayApi(MENU_HELPER)
        actions = []
        service = TrayService(actions.append, api=api)
        service.start()
        api.post_menu(MENU_HELPER)
        self.assertTrue(api.menu_shown.wait(1.0))
        service.stop()
        self.assertEqual(actions, ["panel"])
        self.assertEqual(api.removed, 1)


if __name__ == "__main__":
    unittest.main()
