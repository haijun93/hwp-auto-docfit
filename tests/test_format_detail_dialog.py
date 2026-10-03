"""서식 세부사항 창: 칸별 대표값을 고치고 이름을 바꿔 저장하면 프로필과 예시 표에 반영된다."""
import copy
from pathlib import Path
import runpy
import tempfile
import tkinter as tk
from tkinter import ttk
import unittest
import zipfile

from docfit_core import format_elements as fe


def _descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from _descendants(child)


class FormatDetailDialogTest(unittest.TestCase):
    def _profile(self, namespace, folder):
        header, section = namespace["제목_원본자료"]()
        table = next(x for x in section.iter() if namespace["제목_xml이름"](x) == "tbl")
        for p in list(section):
            section.remove(p)
        pt = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
        p = namespace["XML_자식_추가"](section, section, tag=pt + "p", attrib={"paraPrIDRef": "20", "styleIDRef": "0"})
        run = namespace["XML_자식_추가"](p, section, tag=pt + "run", attrib={"charPrIDRef": "8"})
        run.append(copy.deepcopy(table))
        path = Path(folder) / "example.hwpx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("Contents/header.xml", namespace["ET"].tostring(header, encoding="utf-8"))
            archive.writestr("Contents/section0.xml", namespace["ET"].tostring(section, encoding="utf-8"))
        profile = namespace["hwpx_서식_분석"](path)
        profile["name"] = "예시"
        return profile

    def test_edit_cell_value_and_rename(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("GUI display unavailable")
        root.withdraw()
        try:
            namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
                                       run_name="format_detail_dialog_test")
            with tempfile.TemporaryDirectory(prefix="docfit-detail-") as folder:
                profile = self._profile(namespace, folder)
            original = copy.deepcopy(profile)
            failures = []

            def edit():
                try:
                    dialog = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
                    dialog.update()
                    widgets = list(_descendants(dialog))
                    areas, elements = [w for w in widgets if isinstance(w, ttk.Treeview)][:2]
                    areas.selection_set("form/title1/para/A1/0")
                    dialog.update()
                    elements.selection_set("size")
                    dialog.update()
                    box = next(w for w in widgets if isinstance(w, ttk.Combobox))
                    self.assertEqual(box.get(), "27pt")
                    box.set("25")
                    next(w for w in widgets if isinstance(w, ttk.Button) and w.cget("text") == "값 바꾸기").invoke()
                    shown = elements.item("size", "values")[1]
                    self.assertIn("25pt", shown)
                    self.assertIn("분석값 27pt", shown)
                    name = next(w for w in widgets if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox))
                    name.delete(0, "end")
                    name.insert(0, "새 이름")
                except Exception as exc:   # 창 안 오류도 테스트 실패로 보인다.
                    failures.append(exc)
                next(w for w in _descendants(dialog)
                     if isinstance(w, ttk.Button) and w.cget("text") == "확인하고 서식 저장").invoke()

            root.after(150, edit)
            result = namespace["HwpAutoDocFitGUI"]._서식_세부사항_확인(None, profile, root, {"다른 서식"})
            self.assertEqual(failures, [])
            self.assertTrue(result)
            self.assertEqual(profile["name"], "새 이름")
            record = fe.sample_record(profile["form_tables"]["title1"])
            self.assertEqual(record["cells"]["A1"]["paras"][0]["size"], 2500)
            self.assertIn("서식 요소 대표값", profile["summary"])
            self.assertEqual(fe.sample_record(original["form_tables"]["title1"])["cells"]["A1"]["paras"][0]["size"], 2700)
        finally:
            root.destroy()

    def test_cancel_keeps_profile(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("GUI display unavailable")
        root.withdraw()
        try:
            namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
                                       run_name="format_detail_dialog_cancel_test")
            with tempfile.TemporaryDirectory(prefix="docfit-detail-") as folder:
                profile = self._profile(namespace, folder)
            original = copy.deepcopy(profile)

            def cancel():
                dialog = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
                next(w for w in _descendants(dialog)
                     if isinstance(w, ttk.Button) and w.cget("text") == "취소").invoke()

            root.after(150, cancel)
            self.assertFalse(namespace["HwpAutoDocFitGUI"]._서식_세부사항_확인(None, profile, root, ()))
            self.assertEqual(profile, original)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
