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
        with Image.open(아이콘) as 이미지:
            크기 = 이미지.info['sizes']
        for n in (16, 32, 48, 256):
            self.assertIn((n, n), 크기)

    def test_exe_builds_use_icon(self):
        self.assertIn('--icon resources/app_icon.ico',
                      (ROOT / '.github' / 'workflows' / 'build-windows-exe.yml').read_text(encoding='utf-8'))
        self.assertEqual((ROOT / 'build.bat').read_text(encoding='utf-8').count('--icon "resources\\app_icon.ico"'), 2)

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
