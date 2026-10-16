"""앱 아이콘(2026-10-11 사용자 요청): 완료창 검은 고양이 그림으로 exe·창 아이콘을 쓴다."""
from pathlib import Path
import runpy
import tkinter as tk
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class AppIconTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(ROOT / 'hwp-auto-docfit.py'))

    def test_icon_file_has_small_and_large_sizes(self):
        아이콘 = self.ns['번들_앱아이콘_찾기']()
        self.assertIsNotNone(아이콘)
        with Image.open(아이콘) as image:
            크기 = image.info['sizes']
        for n in (16, 32, 48, 256):
            self.assertIn((n, n), 크기)

    def test_exe_builds_use_icon(self):
        workflow = (ROOT / '.github' / 'workflows' / 'build-windows-exe.yml').read_text(encoding='utf-8')
        build = (ROOT / 'build.bat').read_text(encoding='utf-8')
        self.assertIn('HWP_AutoDocFit.spec', workflow)
        self.assertIn('HWP_AutoDocFit.spec', build)
        import ast
        tree = ast.parse((ROOT / 'HWP_AutoDocFit.spec').read_text())
        exe = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'EXE')
        icon = ast.literal_eval(next(n for n in ast.walk(next(k.value for k in exe.keywords if k.arg == 'icon')) if isinstance(n, ast.Constant) and n.value == 'app_icon.ico'))
        self.assertEqual(icon, 'app_icon.ico')
        self.assertIn('--icon "resources\\app_icon.ico"', build)

    def test_tk_window_gets_icon(self):
        root = tk.Tk()
        try:
            root.withdraw()
            self.ns['_앱아이콘_적용'](root)          # 오류 없이 기본 아이콘을 바꾼다
            tk.Toplevel(root).destroy()
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()
