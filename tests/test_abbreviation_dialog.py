"""준말 등록 창(Tk)이 등록표를 추가·삭제·저장하는지 확인한다. 화면을 띄울 수 없으면 건너뛴다."""
import unittest

from docfit_core.abbreviations import DEFAULT_ENTRIES, describe, upsert

try:
    import tkinter as tk
    from docfit_core.abbreviation_dialog import open_abbreviation_dialog
except ImportError:  # tkinter가 없는 환경
    tk = None


class UpsertTest(unittest.TestCase):
    def test_upsert_validates_and_overwrites(self):
        entries, error = upsert({}, '제목1', 'format', 'title1')
        self.assertEqual((entries, error), ({'제목1': {'type': 'format', 'value': 'title1'}}, ''))
        entries, error = upsert(entries, '제목1', 'format', 'overview')
        self.assertEqual(entries['제목1']['value'], 'overview')
        for args in (('두 어절', 'text', '문구'), ('a:', 'text', '문구'), ('가', 'text', ' '), ('가', 'format', '없음'), ('가', 'x', 'y')):
            same, error = upsert(entries, *args)
            self.assertTrue(error, args)
            self.assertEqual(same, entries)
        self.assertEqual(describe({'type': 'format', 'value': 'title2'})[0], '서식 표')


@unittest.skipIf(tk is None, 'tkinter 없음')
class DialogTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest('화면을 띄울 수 없는 환경')
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_add_delete_defaults_and_persist(self):
        store = {'요약': {'type': 'text', 'value': '문구'}}
        saved = []
        window = open_abbreviation_dialog(self.root, lambda: store, lambda data: saved.append(data))
        actions = window._docfit_actions
        key_var, type_var, format_var, text_var, status = actions['vars']
        tree = window.entries_view
        self.assertEqual(list(tree.get_children()), ['요약'])
        key_var.set('제목1')
        format_var.set('제목 서식1 표')
        actions['add']()
        self.assertEqual(saved[-1]['제목1'], {'type': 'format', 'value': 'title1'})
        key_var.set('두 어절')
        actions['add']()
        self.assertTrue(status.get())            # 오류 문구
        self.assertEqual(len(saved), 1)          # 저장되지 않음
        actions['defaults']()
        self.assertEqual(set(saved[-1]), {'요약', *DEFAULT_ENTRIES})
        tree.selection_set('요약')
        actions['remove']()
        self.assertNotIn('요약', saved[-1])
        window.destroy()

    def test_defaults_checkbox_is_saved(self):
        flags = []
        window = open_abbreviation_dialog(self.root, lambda: {}, lambda data: None, lambda: True, flags.append)
        actions = window._docfit_actions
        self.assertTrue(actions['defaults_var'].get())
        actions['defaults_var'].set(False)
        actions['defaults_changed']()
        self.assertEqual(flags, [False])
        window.destroy()


if __name__ == '__main__':
    unittest.main()
