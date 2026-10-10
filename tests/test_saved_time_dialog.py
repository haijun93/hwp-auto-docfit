"""완료창(2026-10-11 사용자 요청): 개발자 모드가 꺼져 있으면 검은 고양이와 절약 시간 한 줄만, 켜져 있으면 자세한 안내."""
from pathlib import Path
import runpy
import tkinter as tk
import types
import unittest


class SavedTimeDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.gui = cls.ns['HwpAutoDocFitGUI']

    def test_minutes_and_seconds_format(self):
        fmt = self.ns['절약시간_분초_표시']
        self.assertEqual(fmt(425), '07분 05초')
        self.assertEqual(fmt(0), '00분 00초')
        self.assertEqual(fmt(-30), '00분 00초')
        self.assertEqual(fmt(7505), '125분 05초')

    def test_cat_picture_is_bundled(self):
        self.assertIsNotNone(self.ns['번들_고양이_그림_찾기']())

    def _texts(self, window):
        out = []
        stack = [window]
        while stack:
            w = stack.pop()
            stack.extend(w.winfo_children())
            try:
                out.append(str(w.cget('text')))
            except tk.TclError:
                pass
        return out

    def test_dialog_shows_only_saved_time_with_cat(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest('화면 없음')
        root.withdraw()
        try:
            app = types.SimpleNamespace(root=root, _절약초=425)
            window = types.MethodType(self.gui._절약_완료창, app)(1, 0)
            texts = [t for t in self._texts(window) if t]
            self.assertIn('당신의 소중한 시간 07분 05초가 절약되었습니다.!', texts)
            self.assertNotIn('성공', ' '.join(texts))                 # 자세한 안내는 개발자 모드에서만
            self.assertTrue(hasattr(window, '_고양이'))
            window.destroy()
            failed = types.MethodType(self.gui._절약_완료창, app)(1, 2)
            self.assertTrue(any('처리하지 못했습니다' in t for t in self._texts(failed)))
            failed.destroy()
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()
