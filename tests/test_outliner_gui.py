"""아웃라이너 창(TODO 5순위): 단축키로 이동·완료·메모·접기·검색, 닫을 때 자동 저장 후 이어 쓰기."""
from pathlib import Path
import os
import runpy
import tempfile
import time
import unittest
from unittest.mock import patch


class OutlinerGuiTest(unittest.TestCase):
    def test_outliner_shortcuts_and_resume(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        with tempfile.TemporaryDirectory(prefix="hwp-docfit-outliner-") as folder:
            with patch.dict(os.environ, {"APPDATA": folder}):
                ns = runpy.run_path(str(source), run_name="outliner_ui_test")
                root = ns["TkinterDnD"].Tk()
                root.withdraw()
                errors = []
                root.report_callback_exception = lambda *args: errors.append(args)
                try:
                    app = ns["HwpAutoDocFitGUI"](root)
                    app._아웃라이너_열기()
                    window = app._아웃라이너_창

                    def texts(widget):
                        for child in widget.winfo_children():
                            if isinstance(child, ns["tk"].Text):
                                yield child
                            yield from texts(child)
                    outline = next(texts(window))
                    # 숨긴 창에는 키 이벤트가 전달되지 않으므로 창을 띄우고 포커스를 준다.
                    root.deiconify()
                    window.deiconify()
                    root.update()
                    self.assertTrue(window.winfo_viewable())
                    outline.focus_force()
                    root.update()
                    outline.delete("1.0", "end")
                    outline.insert("1.0", "# 계획\n- 개요\n  - 세부\n- 예산")
                    root.update()

                    def key(sequence, line, col="end"):
                        outline.mark_set("insert", f"{line}.{col}")
                        # 포커스가 실제로 옮겨진 뒤에 키를 보낸다(가끔 먼저 가서 무시되던 문제).
                        for _ in range(20):
                            outline.focus_force()
                            root.update()
                            if root.focus_get() is outline:
                                break
                            time.sleep(0.05)
                        outline.event_generate(sequence, when="tail")
                        root.update()

                    key("<Alt-Shift-Up>", 4)                 # '예산'을 '개요' 위로
                    self.assertEqual(outline.get("1.0", "end-1c").split("\n"),
                                     ["# 계획", "- 예산", "- 개요", "  - 세부"])
                    key("<Control-Return>", 2)               # '예산' 완료 표시
                    self.assertEqual(outline.get("2.0", "2.end"), "- [x] 예산")
                    key("<Shift-Return>", 3)                 # '개요' 아래 메모
                    outline.insert("insert", "배경")
                    self.assertEqual(outline.get("4.0", "4.end"), "  > 배경")
                    key("<Control-Up>", 3)                   # '개요' 접기 → 메모·세부 숨김
                    self.assertIn("hidden_fold", outline.tag_names("5.0"))
                    key("<Control-Down>", 3)
                    self.assertNotIn("hidden_fold", outline.tag_names("5.0"))
                    self.assertEqual(errors, [])

                    # 닫으면 자동 저장, 다시 열면 이어 쓰기
                    window.protocol("WM_DELETE_WINDOW")
                    window.tk.call(window.protocol("WM_DELETE_WINDOW"))
                    root.update()
                    self.assertIsNone(app._아웃라이너_창)
                    app._아웃라이너_열기()
                    root.update()
                    again = next(texts(app._아웃라이너_창))
                    self.assertIn("- [x] 예산", again.get("1.0", "end-1c"))
                    self.assertIn("  > 배경", again.get("1.0", "end-1c"))
                    self.assertEqual(errors, [])
                finally:
                    root.destroy()


if __name__ == "__main__":
    unittest.main()
