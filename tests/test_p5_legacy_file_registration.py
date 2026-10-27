import ast
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import Mock


def _extract_file_add_func():
    legacy_file = Path(__file__).resolve().parent.parent / "docfit_ui" / "legacy.py"
    source = legacy_file.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "파일추가":
            module = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(module)
            code = compile(module, str(legacy_file), "exec")
            env = {
                "Path": Path,
                "os": os,
                "tk": tk,
                "지원_확장자": frozenset({".hwp", ".hwpx", ".txt", ".md", ".doc", ".docx", ".pdf"}),
            }
            exec(code, env)
            return env["파일추가"]
    raise RuntimeError("파일추가 메서드를 찾지 못했습니다.")


class FakeGUI:
    def __init__(self):
        self.files = []
        self.running = False
        self._안내단계 = 0
        self.file_count = Mock()
        self.file_list = Mock()
        self._원본폴더_버튼_갱신 = Mock()
        self._실행버튼_상태 = Mock()
        self._작업범위_초기화 = Mock()
        self._결과_초기화 = Mock()
        self._안내_설정 = Mock()


class TestP5LegacyFileRegistration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.file_add = _extract_file_add_func()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.gui = FakeGUI()

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_file_registration_keeps_extensions(self):
        hwpx = self.folder / "doc.hwpx"
        hwpx.write_bytes(b"hwpx")
        html = self.folder / "page.html"
        html.write_bytes(b"html")

        res_hwpx = self.file_add(self.gui, str(hwpx))
        self.assertTrue(res_hwpx)
        self.assertEqual(self.gui.files, [str(hwpx.resolve())])

        res_html = self.file_add(self.gui, str(html))
        self.assertFalse(res_html)
        self.assertEqual(self.gui.files, [str(hwpx.resolve())])

    def test_conversion_file_registration_accepts_html_and_pptx(self):
        html = self.folder / "document.html"
        html.write_text("<html></html>", encoding="utf-8")
        pptx = self.folder / "presentation.pptx"
        pptx.write_bytes(b"PK\x03\x04")

        res_html = self.file_add(self.gui, str(html), file_conversion=True)
        self.assertTrue(res_html)
        self.assertEqual(len(self.gui.files), 1)
        self.gui.file_count.configure.assert_called_with(text="1개 문서")
        self.gui.file_list.insert.assert_called_with(tk.END, str(html.resolve()))
        self.gui._작업범위_초기화.assert_called_once()
        self.gui._결과_초기화.assert_called_once()

        res_pptx = self.file_add(self.gui, str(pptx), file_conversion=True)
        self.assertTrue(res_pptx)
        self.assertEqual(len(self.gui.files), 2)
        self.gui.file_count.configure.assert_called_with(text="2개 문서")
        self.gui.file_list.insert.assert_called_with(tk.END, str(pptx.resolve()))

    def test_conversion_file_registration_rejects_invalid_and_duplicate(self):
        exe = self.folder / "bad.exe"
        exe.write_bytes(b"MZ")
        valid = self.folder / "valid.md"
        valid.write_text("# title", encoding="utf-8")

        self.assertFalse(self.file_add(self.gui, str(exe), file_conversion=True))
        self.assertEqual(len(self.gui.files), 0)

        missing = self.folder / "nonexistent.pptx"
        self.assertFalse(self.file_add(self.gui, str(missing), file_conversion=True))
        self.assertEqual(len(self.gui.files), 0)

        self.assertTrue(self.file_add(self.gui, str(valid), file_conversion=True))
        self.assertEqual(len(self.gui.files), 1)

        self.assertFalse(self.file_add(self.gui, str(valid), file_conversion=True))
        self.assertEqual(len(self.gui.files), 1)
        self.gui.file_count.configure.assert_called_once_with(text="1개 문서")


if __name__ == "__main__":
    unittest.main()
