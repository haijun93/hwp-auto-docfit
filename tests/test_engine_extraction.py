"""Session binding, GUI isolation and security fallback regressions."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from docfit_engine.runtime import resolve
from docfit_engine.security import install_security_dll


class EngineExtractionTest(unittest.TestCase):
    def test_compatibility_export_executes_with_private_context_globals(self):
        class Driver:
            def Open(self, *args): return args
        first, second = {'__name__': 'first'}, {'__name__': 'second'}
        a = resolve('docfit_engine.com_driver', '한글_문서_열기', first)
        b = resolve('docfit_engine.com_driver', '한글_문서_열기', second)
        self.assertIs(a.__globals__, first)
        self.assertIs(b.__globals__, second)
        from docfit_engine.runtime import session_for
        context = session_for(first).new_context()
        self.assertIsNot(context.function('한글_문서_열기').__globals__, first)
        self.assertEqual(a(Driver(), 'file', 'HWPX'), ('file', 'HWPX', ''))

    def test_security_registration_failure_uses_localappdata(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); source=root/'source.dll'; source.write_bytes(b'dll')
            primary=root/'restricted'/'security.dll'
            registered=[]
            def register(path):
                if path == primary: raise PermissionError('policy')
                registered.append(path)
            selected=install_security_dll(source,primary,register,local_appdata=root/'local')
            self.assertEqual(selected,root/'local'/'HwpAutoDocFit'/'modules'/'security.dll')
            self.assertEqual(selected.read_bytes(),b'dll')
            self.assertEqual(registered,[selected])

    def test_com_driver_has_no_gui_imports(self):
        import ast
        path=Path(__file__).parents[1]/'docfit_engine'/'com_driver.py'
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node,ast.Import):
                self.assertFalse(any(alias.name.startswith('tkinter') for alias in node.names))
            elif isinstance(node,ast.ImportFrom):
                self.assertFalse((node.module or '').startswith('tkinter'))
