"""3.0-α1 LiveLink 서비스·브리지(가짜 한/글로 시험)."""
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from docfit_live import link
from docfit_live.service import LiveLinkService
from tests.test_live_link import FakeApp


def session(path, visible=True):
    app = FakeApp(path)
    app.XHwpWindows = SimpleNamespace(Active_XHwpWindow=SimpleNamespace(Visible=visible))
    return link.Session("m:" + path, app, path, path.rsplit("\\", 1)[-1])


class LiveServiceTest(unittest.TestCase):
    def service(self, sessions, titles=()):
        return LiveLinkService(sessions=lambda: sessions, titles=lambda: list(titles), com_init=False)

    def test_hidden_helper_hangul_is_never_chosen(self):
        user, hidden = session(r"C:\a\보고서.hwpx"), session("", visible=False)
        status = self.service([hidden, user]).status()
        self.assertTrue(status["connected"])
        self.assertEqual(status["title"], "보고서.hwpx")

    def test_front_window_decides_between_many(self):
        a, b = session(r"C:\a\가.hwpx"), session(r"C:\a\나.hwpx")
        svc = self.service([a, b], titles=["나.hwpx [C:\\a\\] - 한글", "가.hwpx - 한글"])
        self.assertEqual(svc.status()["title"], "나.hwpx")
        self.assertEqual(svc.paste()["undo_steps"], 1)
        self.assertEqual((a.app.runs, b.app.runs), ([], ["Paste"]))
        self.assertEqual(self.service([a, b]).status()["code"], "AMBIGUOUS")
        self.assertEqual(self.service([]).status()["code"], "NO_HANGUL")

    def test_commands_run_on_one_thread(self):
        svc, seen = self.service([]), set()
        for _ in range(3):
            svc.call(lambda: seen.add(threading.current_thread().name))
        self.assertEqual(seen, {"docfit-livelink"})
        with self.assertRaises(ValueError):
            svc.call(lambda: (_ for _ in ()).throw(ValueError("x")))
        svc.close()


class LiveBridgeTest(unittest.TestCase):
    def setUp(self):
        from desktop_web_ui import DesktopWebBridge, _BrowserApi
        self.gui = Mock(files=[], running=False)
        self.bridge = DesktopWebBridge(self.gui)
        self.user = session(r"C:\a\보고서.hwpx")
        self.bridge._live = LiveLinkService(sessions=lambda: [self.user], titles=lambda: [], com_init=False)
        self.assertTrue(callable(getattr(_BrowserApi(self.bridge), "live_link")))

    def test_insert_copies_then_pastes_once_and_restores_clipboard(self):
        order = []
        self.bridge.table_units = Mock(side_effect=lambda a, d: order.append(("copy", a, d)) or {"ok": True})
        with patch("docfit_live.service.save_clipboard", return_value={13: "사용자 글"}), \
                patch("docfit_live.service.restore_clipboard", side_effect=lambda s: order.append(("restore", s)) or True):
            result = self.bridge.live_link("insert", {"source": "table_units", "data": {"id": "g1:1"}})
        self.assertTrue(result["ok"], result)
        self.assertEqual((result["title"], result["undo_steps"]), ("보고서.hwpx", 1))
        self.assertEqual(order, [("copy", "copy", {"id": "g1:1"}), ("restore", {13: "사용자 글"})])
        self.assertEqual(self.user.app.runs, ["Paste"])

    def test_failed_copy_does_not_paste(self):
        self.bridge.table_sketch = Mock(return_value={"ok": False, "message": "표를 만들지 못했습니다."})
        with patch("docfit_live.service.save_clipboard", return_value={}):
            result = self.bridge.live_link("insert", {"source": "table_sketch", "data": {"lines": []}})
        self.assertFalse(result["ok"])
        self.assertEqual(self.user.app.runs, [])

    def test_rejects_bad_input_and_busy_app(self):
        self.assertFalse(self.bridge.live_link("insert", {"source": "exe", "data": {}})["ok"])
        self.assertFalse(self.bridge.live_link("unknown")["ok"])
        self.gui.running = True
        self.assertIn("문서 작업", self.bridge.live_link("insert", {"source": "image", "data": {}})["message"])
        self.assertEqual(self.bridge.live_link("status")["title"], "보고서.hwpx")


if __name__ == "__main__":
    unittest.main()
