"""3.0 LiveLink 연결·문맥·넣기(가짜 한/글로 시험)."""
import unittest
from types import SimpleNamespace

from docfit_live.link import LiveLinkError, Session, choose, context, paste_at_cursor, running_sessions


class FakeMoniker:
    def __init__(self, name):
        self.name = name

    def GetDisplayName(self, ctx, other):
        return self.name


class FakeApp:
    def __init__(self, path, pos=(0, 1, 2), in_table=False):
        self.XHwpDocuments = SimpleNamespace(Active_XHwpDocument=SimpleNamespace(FullName=path))
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
        self.assertEqual([s.title for s in sessions], ["보고서.hwpx", ""])

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

    def test_context_and_single_paste(self):
        app = FakeApp(r"C:\a\가.hwpx", in_table=True)
        ctx = context(app)
        self.assertEqual((ctx["in_table"], ctx["page"], ctx["pos"]), (True, 3, [0, 1, 2]))
        result = paste_at_cursor(app, expected=ctx)
        self.assertEqual((result["undo_steps"], app.runs), (1, ["Paste"]))

    def test_paste_stops_when_cursor_moved(self):
        app = FakeApp(r"C:\a\가.hwpx")
        stale = {**context(app), "pos": [0, 9, 9]}
        with self.assertRaises(LiveLinkError) as raised:
            paste_at_cursor(app, expected=stale)
        self.assertEqual(raised.exception.code, "STALE_CONTEXT")
        self.assertEqual(app.runs, [])


if __name__ == "__main__":
    unittest.main()
