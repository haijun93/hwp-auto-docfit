"""3.0 LiveLink 연결·문맥·넣기(가짜 한/글로 시험)."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from docfit_live.link import LiveLinkError, Session, choose, context, paste_at_cursor, running_sessions


class FakeMoniker:
    def __init__(self, name):
        self.name = name

    def GetDisplayName(self, ctx, other):
        return self.name


class FakeApp:
    def __init__(self, path, pos=(0, 1, 2), in_table=False):
        self.XHwpDocuments = SimpleNamespace(Active_XHwpDocument=SimpleNamespace(FullName=path))
        self.XHwpDocuments.Active_XHwpDocument.DocumentID = 17
        self.XHwpWindows = SimpleNamespace(Active_XHwpWindow=SimpleNamespace(Visible=True, Hwnd=9))
        self._pos = pos
        self.SelectionMode = 0
        self.ParentCtrl = SimpleNamespace(CtrlID="tbl") if in_table else None
        self.runs = []
        self.HAction = SimpleNamespace(Run=lambda name: self.runs.append(name) or True)

    def GetPos(self):
        return self._pos

    def KeyIndicator(self):
        return (True, 1, 1, 3, 1, 1, 0, "")


class FakeRot:
    def __init__(self, entries):
        self.entries = entries

    def EnumRunning(self):
        return [FakeMoniker(name) for name, _ in self.entries]

    def GetObject(self, moniker):
        return dict(self.entries)[moniker.name]


class LiveLinkTest(unittest.TestCase):
    def test_only_hangul_entries_from_rot(self):
        a, b = FakeApp(r"C:\문서\보고서.hwpx"), FakeApp("")
        rot = FakeRot([("!HwpObject.96.1:1", a), ("!Excel.Application", object()), ("!HwpObject.96.1:2", b)])
        sessions = running_sessions(rot=rot, bind_ctx=None, dispatch=lambda x: x)
        self.assertEqual(len(sessions), 2)
        self.assertEqual(sessions[0].path, r"C:\문서\보고서.hwpx")

    def test_choose_never_guesses_between_many(self):
        one = Session("m1", FakeApp(r"C:\a\가.hwpx"), r"C:\a\가.hwpx", "가.hwpx")
        two = Session("m2", FakeApp(r"C:\a\나.hwpx"), r"C:\a\나.hwpx", "나.hwpx")
        self.assertIs(choose([one, two], window_title="나.hwpx - 한글"), two)
        self.assertIs(choose([one, two], prefer_path=r"C:\a\가.hwpx"), one)
        self.assertIs(choose([one]), one)
        with self.assertRaises(LiveLinkError) as raised:
            choose([one, two], window_title="메모장")
        self.assertEqual(raised.exception.code, "AMBIGUOUS")
        with self.assertRaises(LiveLinkError):
            choose([])

    def test_unsaved_new_document_is_chosen_only_when_single(self):
        saved = Session("m1", FakeApp(r"C:\가.hwpx"), r"C:\가.hwpx", "가.hwpx")
        blank = Session("m2", FakeApp(""), "", "")
        self.assertIs(choose([saved, blank], window_title="빈 문서 1 - 한글"), blank)
        self.assertIs(choose([saved, blank], window_title="가.hwpx [C:\a\] - 한글"), saved)
        with self.assertRaises(LiveLinkError):
            choose([saved, blank, Session("m3", FakeApp(""), "", "")], window_title="빈 문서 2 - 한글")

    def test_context_and_single_paste(self):
        app = FakeApp(r"C:\a\가.hwpx", in_table=True)
        ctx = context(app)
        self.assertEqual((ctx["in_table"], ctx["page"], ctx["pos"]), (True, 3, [0, 1, 2]))
        result = paste_at_cursor(app, expected=ctx)
        self.assertEqual((result["undo_steps"], app.runs), (1, ["Paste"]))

    def test_foreground_app_window_pastes_when_hangul_owner_is_enabled(self):
        app = FakeApp(r"C:\a\가.hwpx")
        with patch("docfit_live.link.ctypes.windll", create=True) as windll:
            windll.user32.IsWindowEnabled.return_value = 1
            windll.user32.GetForegroundWindow.return_value = 999  # 도우미 앱이 전경
            result = paste_at_cursor(app)
        self.assertTrue(result["inserted"])
        self.assertEqual(app.runs, ["Paste"])

    def test_disabled_owner_blocks_without_paste(self):
        app = FakeApp(r"C:\a\가.hwpx")
        with patch("docfit_live.link.ctypes.windll", create=True) as windll:
            windll.user32.IsWindowEnabled.return_value = 0
            with self.assertRaises(LiveLinkError) as raised:
                paste_at_cursor(app)
        self.assertEqual(raised.exception.code, "DOCUMENT_BUSY")
        self.assertEqual(app.runs, [])

    def test_paste_stops_when_cursor_moved(self):
        app = FakeApp(r"C:\a\가.hwpx")
        stale = {**context(app), "pos": [0, 9, 9]}
        with self.assertRaises(LiveLinkError) as raised:
            paste_at_cursor(app, expected=stale)
        self.assertEqual(raised.exception.code, "STALE_CONTEXT")
        self.assertEqual(app.runs, [])

    def test_document_or_window_change_never_runs_paste(self):
        app = FakeApp(r"C:\a\가.hwpx")
        stale = context(app)
        stale["document_id"] = 18
        with self.assertRaises(LiveLinkError):
            paste_at_cursor(app, expected=stale)
        self.assertEqual(app.runs, [])
        app.XHwpWindows.Active_XHwpWindow.Visible = False
        with self.assertRaises(LiveLinkError) as raised:
            paste_at_cursor(app)
        self.assertEqual(raised.exception.code, "DOCUMENT_BUSY")
        self.assertEqual(app.runs, [])

    def test_save_action_is_denied_without_document_change(self):
        app = FakeApp(r"C:\a\가.hwpx")
        from docfit_live.link import _run_allowed
        with self.assertRaises(LiveLinkError):
            _run_allowed(app, "FileSave")
        self.assertEqual(app.runs, [])


if __name__ == "__main__":
    unittest.main()
