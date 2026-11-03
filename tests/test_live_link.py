"""3.0 LiveLink 연결·문맥·넣기(가짜 한/글로 시험)."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from docfit_live.link import (
    LiveLinkError,
    Session,
    choose,
    context,
    export_selection_block,
    export_table_block,
    paste_at_cursor,
    replace_selection_block,
    replace_table_block,
    running_sessions,
)


class FakeMoniker:
    def __init__(self, name):
        self.name = name

    def GetDisplayName(self, ctx, other):
        return self.name


class FakeApp:
    def __init__(self, path, pos=(0, 1, 2), in_table=False, document_id="doc-default", selection_range=None):
        self.XHwpDocuments = SimpleNamespace(
            Active_XHwpDocument=SimpleNamespace(FullName=path, DocumentID=document_id)
        )
        self.XHwpWindows = SimpleNamespace(Active_XHwpWindow=SimpleNamespace(Visible=True, Hwnd=9))
        self._pos = pos
        self.SelectionMode = 0
        self.selection_range = selection_range
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
        saved = Session("m1", FakeApp(r"C: \가.hwpx"), r"C: \가.hwpx", "가.hwpx")
        blank = Session("m2", FakeApp(""), "", "")
        self.assertIs(choose([saved, blank], window_title="빈 문서 1 - 한글"), blank)
        self.assertIs(choose([saved, blank], window_title=r"가.hwpx [C:\a\] - 한글"), saved)
        with self.assertRaises(LiveLinkError):
            choose([saved, blank, Session("m3", FakeApp(""), "", "")], window_title="빈 문서 2 - 한글")

    def test_context_and_single_paste(self):
        app = FakeApp(r"C:\a\가.hwpx", in_table=True)
        ctx = context(app)
        self.assertEqual((ctx["in_table"], ctx["page"], ctx["pos"]), (True, 3, [0, 1, 2]))
        result = paste_at_cursor(app, expected=ctx, window_enabled=lambda hwnd: True)
        self.assertEqual((result["undo_steps"], app.runs), (1, ["Paste"]))

    def test_foreground_app_window_pastes_when_hangul_owner_is_enabled(self):
        app = FakeApp(r"C:\a\가.hwpx")
        checker = Mock(return_value=True)
        result = paste_at_cursor(app, window_enabled=checker)
        checker.assert_called_once_with(9)
        self.assertTrue(result["inserted"])
        self.assertEqual(app.runs, ["Paste"])

    def test_disabled_owner_blocks_without_paste(self):
        app = FakeApp(r"C:\a\가.hwpx")
        with self.assertRaises(LiveLinkError) as raised:
            paste_at_cursor(app, window_enabled=lambda hwnd: False)
        self.assertEqual(raised.exception.code, "DOCUMENT_BUSY")
        self.assertEqual(app.runs, [])

    def test_paste_stops_when_cursor_moved(self):
        app = FakeApp(r"C:\a\가.hwpx")
        stale = {**context(app), "pos": [0, 9, 9]}
        with self.assertRaises(LiveLinkError) as raised:
            paste_at_cursor(app, expected=stale, window_enabled=lambda hwnd: True)
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
    def test_context_includes_document_id_and_missing_id_is_not_match(self):
        # 1. 정상 DocumentID 반환
        app_valid = FakeApp(r"C:\a\가.hwpx", document_id="doc-uuid-1234")
        ctx = context(app_valid)
        self.assertEqual(ctx["document_id"], "doc-uuid-1234")

        # 2. DocumentID 누락/빈 값인 앱은 완전한 expected와 매칭 시 STALE_CONTEXT
        app_missing = FakeApp(r"C:\a\가.hwpx", in_table=True, document_id="")
        expected = {
            "path": r"C:\a\가.hwpx",
            "document_id": "doc-uuid-1234",
            "pos": [0, 1, 2],
            "selected": False,
            "in_table": True,
        }
        with self.assertRaises(LiveLinkError) as raised:
            replace_table_block(app_missing, b"dummy", expected=expected)
        self.assertEqual(raised.exception.code, "STALE_CONTEXT")

    def test_export_table_block_requires_measured_gettextfile_contract(self):
        app = FakeApp(r"C:\a\가.hwpx", in_table=True)
        get_calls = []
        app.GetTextFile = lambda *a, **kw: get_calls.append((a, kw)) or ""
        with self.assertRaises(NotImplementedError) as raised:
            export_table_block(app)
        self.assertIn("실측 결과", str(raised.exception))
        self.assertEqual(get_calls, [])
        self.assertEqual(app.runs, [])

    def test_replace_table_requires_complete_expected_and_rechecks_document_id(self):
        app = FakeApp(r"C:\a\가.hwpx", in_table=True, document_id="doc-1")
        mock_write = Mock()
        app.SetTextFile = mock_write

        valid_expected = {
            "path": r"C:\a\가.hwpx",
            "document_id": "doc-1",
            "pos": [0, 1, 2],
            "selected": False,
            "in_table": True,
        }

        # 1. 필수 expected 하나라도 누락 시 INVALID_ARGUMENT, SetTextFile 호출 0
        with self.assertRaises(LiveLinkError) as raised:
            replace_table_block(app, b"dummy", expected=None)
        self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")

        with self.assertRaises(LiveLinkError) as raised:
            replace_table_block(app, b"dummy", expected={})
        self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")

        for key in ("path", "document_id", "pos", "selected", "in_table"):
            bad = dict(valid_expected)
            del bad[key]
            with self.assertRaises(LiveLinkError) as raised:
                replace_table_block(app, b"dummy", expected=bad)
            self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")

        # 2. ID/path/pos/selected 불일치 시 STALE_CONTEXT
        for field, val in [("path", r"C:\other.hwpx"), ("document_id", "doc-2"), ("pos", [9, 9, 9]), ("selected", True)]:
            stale = dict(valid_expected, **{field: val})
            with self.assertRaises(LiveLinkError) as raised:
                replace_table_block(app, b"dummy", expected=stale)
            self.assertEqual(raised.exception.code, "STALE_CONTEXT")

        # 3. 대상 표 상태 불일치(표 밖) 시 NOT_IN_TABLE
        app_out = FakeApp(r"C:\a\가.hwpx", in_table=False, document_id="doc-1")
        with self.assertRaises(LiveLinkError) as raised:
            replace_table_block(app_out, b"dummy", expected=dict(valid_expected, in_table=False))
        self.assertEqual(raised.exception.code, "NOT_IN_TABLE")

        # 4. 완벽한 expected이지만 미실측 포맷은 NotImplementedError 안전 종료
        with self.assertRaises(NotImplementedError) as raised:
            replace_table_block(app, b"dummy", expected=valid_expected)
        self.assertIn("실측 필요", str(raised.exception))

        mock_write.assert_not_called()
        self.assertEqual(app.runs, [])

    def test_replace_selection_requires_complete_expected_and_rechecks_selection(self):
        app = FakeApp(r"C:\a\가.hwpx", document_id="doc-1", selection_range=[[0, 1, 2], [0, 1, 10]])
        app.SelectionMode = 1
        mock_write = Mock()
        app.SetTextFile = mock_write

        valid_expected = {
            "path": r"C:\a\가.hwpx",
            "document_id": "doc-1",
            "pos": [0, 1, 2],
            "selected": True,
            "in_table": False,
            "selection_range": [[0, 1, 2], [0, 1, 10]],
        }

        # 1. 필수 expected 누락 시 INVALID_ARGUMENT
        with self.assertRaises(LiveLinkError) as raised:
            replace_selection_block(app, b"dummy", expected=None)
        self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")

        with self.assertRaises(LiveLinkError) as raised:
            replace_selection_block(app, b"dummy", expected={})
        self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")

        bad_sr = dict(valid_expected)
        del bad_sr["selection_range"]
        with self.assertRaises(LiveLinkError) as raised:
            replace_selection_block(app, b"dummy", expected=bad_sr)
        self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")

        # 2. DocumentID/pos 불일치 시 STALE_CONTEXT
        stale_doc = dict(valid_expected, document_id="doc-2")
        with self.assertRaises(LiveLinkError) as raised:
            replace_selection_block(app, b"dummy", expected=stale_doc)
        self.assertEqual(raised.exception.code, "STALE_CONTEXT")

        # 3. 시작 위치(pos)는 같으나 selection_range 끝점만 바뀌었을 때 STALE_CONTEXT (지적 2 Fake 회귀 시험)
        app.selection_range = [[0, 1, 2], [0, 1, 25]]
        with self.assertRaises(LiveLinkError) as raised:
            replace_selection_block(app, b"dummy", expected=valid_expected)
        self.assertEqual(raised.exception.code, "STALE_CONTEXT")
        app.selection_range = [[0, 1, 2], [0, 1, 10]]

        # 4. 선택 없음 시 NO_SELECTION
        app_no_sel = FakeApp(r"C:\a\가.hwpx", document_id="doc-1")
        app_no_sel.SelectionMode = 0
        with self.assertRaises(LiveLinkError) as raised:
            replace_selection_block(app_no_sel, b"dummy", expected=dict(valid_expected, selected=False))
        self.assertEqual(raised.exception.code, "NO_SELECTION")

        # 5. 완벽한 expected이지만 미실측 포맷은 NotImplementedError 안전 종료
        with self.assertRaises(NotImplementedError) as raised:
            replace_selection_block(app, b"dummy", expected=valid_expected)
        self.assertIn("실측 필요", str(raised.exception))

        mock_write.assert_not_called()

        self.assertEqual(app.runs, [])


if __name__ == "__main__":
    unittest.main()
