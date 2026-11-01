import unittest
from types import SimpleNamespace
from unittest.mock import patch

from docfit_live import link
from docfit_live.service import LiveLinkService
from tests.test_live_link import FakeApp
from docfit_live.service import _table_unit_transform, transform_selection_spacing


class FakeReplaceApp(FakeApp):
    def __init__(self, **kwargs):
        super().__init__(r"C:\a\sample.hwpx", in_table=kwargs.get("in_table", True))
        self.SelectionMode = int(kwargs.get("selected", False))
        self.replacements = []
        self.dialog_open = False

    def IsDialogOpen(self):
        return self.dialog_open

    def ReplaceSelection(self, value):
        self.replacements.append(value)
        return True


class LiveReplaceTest(unittest.TestCase):
    def service(self, app, gate=False):
        return LiveLinkService(sessions=lambda: [link.Session("fake", app, r"C:\a\sample.hwpx", "sample.hwpx")],
            titles=lambda: [], com_init=False, gate_passed=gate,
            block_reader=lambda *_: b"block", table_unit_transform=lambda block, direction: block + bytes([direction & 255]),
            selection_spacing_transform=lambda block: block + b" spacing")

    def test_gate_blocks_without_read_or_write(self):
        app = FakeReplaceApp()
        with self.assertRaises(link.LiveLinkError) as exc:
            self.service(app).table_unit_step(1)
        self.assertEqual(exc.exception.code, "GATE_NOT_PASSED")
        self.assertEqual(app.replacements, [])

    def test_stale_context_and_busy_dialog_do_not_write(self):
        app = FakeReplaceApp()
        stale = {**link.context(app), "pos": [9, 9, 9]}
        with self.assertRaises(link.LiveLinkError) as exc:
            self.service(app, True).table_unit_step(-1, expected=stale)
        self.assertEqual(exc.exception.code, "STALE_CONTEXT")
        app.dialog_open = True
        with self.assertRaises(link.LiveLinkError) as exc:
            self.service(app, True).table_unit_step(1)
        self.assertEqual(exc.exception.code, "DOCUMENT_BUSY")
        self.assertEqual(app.replacements, [])

    def test_selection_spacing_restores_clipboard_and_replaces_once(self):
        app = FakeReplaceApp(selected=True, in_table=False)
        svc = self.service(app, True)
        with patch("docfit_live.service.save_clipboard", return_value={13: "kept"}), \
             patch("docfit_live.service.restore_clipboard", return_value=True) as restore:
            result = svc.selection_spacing()
        self.assertTrue(result["replaced"])
        self.assertEqual(app.replacements, [b"block spacing"])
        restore.assert_called_once_with({13: "kept"})

    def test_hwpml2x_unit_adjustment_simple_and_merged(self):
        examples = [
            """<HWPML2X><TABLE RowCount="1" ColCount="4"><ROW>""" + "".join(
                f'<CELL><CELLADDR RowAddr="0" ColAddr="{i}"/><CELLSPAN RowSpan="1" ColSpan="1"/><CELLSZ Width="1000" Height="500"/></CELL>' for i in range(4)) + "</ROW></TABLE></HWPML2X>",
            """<HWPML2X><TABLE RowCount="2" ColCount="6"><ROW>""" + "".join(
                f'<CELL><CELLADDR RowAddr="0" ColAddr="{i}"/><CELLSPAN RowSpan="1" ColSpan="1"/><CELLSZ Width="1000" Height="500"/></CELL>' for i in range(6)) + "</ROW><ROW>" +
                '<CELL><CELLADDR RowAddr="1" ColAddr="0"/><CELLSPAN RowSpan="1" ColSpan="2"/><CELLSZ Width="2000" Height="500"/></CELL>' + "".join(
                f'<CELL><CELLADDR RowAddr="1" ColAddr="{i}"/><CELLSPAN RowSpan="1" ColSpan="1"/><CELLSZ Width="1000" Height="500"/></CELL>' for i in range(2, 6)) + "</ROW></TABLE></HWPML2X>"
        ]
        for source in examples:
            with self.subTest(source=source[:50]):
                reduced = _table_unit_transform(source, -1)
                increased = _table_unit_transform(source, 1)
                self.assertIn("<HWPML2X", reduced)
                self.assertNotEqual(reduced, source)
                self.assertNotEqual(increased, source)

    def test_unreadable_table_is_unsupported(self):
        with self.assertRaises(link.LiveLinkError) as raised:
            _table_unit_transform("<not-a-table/>", 1)
        self.assertEqual(raised.exception.code, "UNSUPPORTED_TABLE")

    def test_selection_spacing_stage_order_uses_injected_document(self):
        events = []
        class FakeCopy:
            def Close(self): events.append("close")
        doc = FakeCopy()
        result = transform_selection_spacing(b"block", save_block=lambda b: events.append("save") or b"saved",
            open_copy=lambda b: events.append(("open", b)) or doc,
            spacing_engine=lambda d: events.append(("engine", d is doc)),
            extract_block=lambda d: events.append(("extract", d is doc)) or b"adjusted")
        self.assertEqual(result, b"adjusted")
        self.assertEqual(events, ["save", ("open", b"saved"), ("engine", True), ("extract", True), "close"])


if __name__ == "__main__":
    unittest.main()
