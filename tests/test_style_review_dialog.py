import copy
from pathlib import Path
import runpy
import tkinter as tk
from tkinter import ttk
import unittest

from docfit_core.style_hierarchy import analyze_hierarchy


class StyleReviewDialogTest(unittest.TestCase):
    def test_confirm_commits_reviewed_profile(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("GUI display unavailable")
        root.withdraw()
        try:
            namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
                                       run_name="style_review_dialog_test")
            profile = {"name": "테스트", "format": {
                "기호_규칙": [("□", 0, "명조", 14, False, False)],
                "복사_문단모양": {}, "제목_문단": {"font": "명조", "size_pt": 18}},
                "options": {}, "style_hierarchy": analyze_hierarchy([
                    {"text": "□ 소제목", "left": 100, "font": "명조", "size_pt": 14}])}
            original = copy.deepcopy(profile)
            def confirm():
                dialog = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
                dialog.update()
                def descendants(widget):
                    for child in widget.winfo_children():
                        yield child
                        yield from descendants(child)
                size_entry = next(w for w in descendants(dialog)
                                  if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox)
                                  and w.grid_info().get("column") == 2)
                size_entry.delete(0, "end")
                size_entry.insert(0, "16")
                font_toggle = next(w for w in descendants(dialog)
                                   if isinstance(w, ttk.Checkbutton) and w.cget("text") == "글꼴 적용")
                font_toggle.invoke()
                button = next(w for w in descendants(dialog)
                              if isinstance(w, ttk.Button) and w.cget("text") == "확인하고 서식 저장")
                button.invoke()
            root.after(100, confirm)
            result = namespace["HwpAutoDocFitGUI"]._서식_구조_확인(None, profile, root)
            self.assertTrue(result)
            self.assertTrue(profile["style_hierarchy"]["reviewed"])
            self.assertEqual(profile["format"]["기호_규칙"][0][3], 16)
            self.assertFalse(profile["format"]["스타일_속성선택"]["□"]["font"])
            self.assertNotIn("reviewed", original["style_hierarchy"])
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
