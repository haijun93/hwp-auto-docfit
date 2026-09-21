from pathlib import Path
import runpy
import tempfile
import time
import tkinter as tk
from types import MethodType, SimpleNamespace
import unittest
from zipfile import ZipFile

from tests.test_korean_proofread import SECTION


class KoreanProofreadDialogTest(unittest.TestCase):
    def test_scan_list_and_persistent_exclusion(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("GUI display unavailable")
        root.withdraw()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.hwpx"
            with ZipFile(source, "w") as archive:
                archive.writestr("Contents/header.xml", "<head/>")
                archive.writestr("Contents/section0.xml", SECTION)
            namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
                                       run_name="proofread_dialog_test")
            cls = namespace["HwpAutoDocFitGUI"]
            state = SimpleNamespace(root=root, files=[str(source)], running=False)
            for name in ("_공공언어_검토", "_교정_목록갱신", "_교정_선택제외",
                         "_교정_제외관리", "_교정_승인"):
                setattr(state, name, MethodType(getattr(cls, name), state))
            state._공공언어_검토.__func__.__globals__["설정_폴더"] = lambda: Path(folder)
            try:
                state._공공언어_검토()
                queue = state._공공언어_검토.__func__.__globals__["gui_queue"]
                deadline = time.monotonic() + 5
                while queue.empty() and time.monotonic() < deadline:
                    root.update()
                    time.sleep(.02)
                event = queue.get_nowait()
                self.assertEqual(event[0], "proofread_scan_done")
                state._교정_작업중 = False
                state._교정_후보, state._교정_대상 = event[1], event[2]
                state._교정_목록갱신()
                self.assertGreater(len(state._교정_목록.get_children()), 0)
                first = state._교정_목록.get_children()[0]
                expression = state._교정_후보[int(first)]["source"]
                state._교정_목록.selection_set(first)
                state._교정_선택제외()
                self.assertIn(expression, namespace["load_exclusions"](Path(folder) / "proofreading_exclusions.json"))
                remaining = state._교정_목록.get_children()
                self.assertTrue(remaining)
                state._교정_목록.selection_set(remaining[0])
                state._교정_승인()
                deadline = time.monotonic() + 5
                while queue.empty() and time.monotonic() < deadline:
                    root.update()
                    time.sleep(.02)
                applied = queue.get_nowait()
                self.assertEqual(applied[0], "proofread_apply_done")
                self.assertEqual(applied[2], [])
                self.assertTrue(Path(applied[1][0][0]).is_file())
            finally:
                if hasattr(state, "_교정_임시폴더"):
                    state._교정_임시폴더.cleanup()
                root.destroy()


if __name__ == "__main__":
    unittest.main()
