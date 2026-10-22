import os
import unittest
from unittest.mock import patch
from docfit_app import shell_menu as menu


class Key:
    def __init__(self, path):
        self.path = path
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


class Registry:
    HKEY_CURRENT_USER, REG_SZ, KEY_READ, KEY_WRITE = 1, 1, 1, 2
    def __init__(self):
        self.data = {}
    def CreateKey(self, root, path):
        parts = path.split('\\')
        for index in range(1, len(parts) + 1):
            self.data.setdefault('\\'.join(parts[:index]), {})
        return Key(path)
    def OpenKey(self, root, path, *args):
        if path not in self.data:
            raise FileNotFoundError(path)
        return Key(path)
    def SetValueEx(self, key, name, _, kind, value):
        self.data[key.path][name] = value
    def QueryValueEx(self, key, name):
        if name not in self.data[key.path]:
            raise FileNotFoundError(name)
        return self.data[key.path][name], self.REG_SZ
    def EnumKey(self, key, index):
        prefix = key.path + '\\'
        children = sorted({p[len(prefix):].split('\\')[0] for p in self.data if p.startswith(prefix)})
        if index >= len(children):
            raise OSError('no more items')
        return children[index]
    def DeleteKey(self, root, path):
        del self.data[path]


class ShellMenuTests(unittest.TestCase):
    def setUp(self):
        self.reg = Registry()
        self.exe = r'C:\앱 폴더\HWP_AutoDocFit.exe'

    def test_register_exact_menu_and_quoted_commands(self):
        menu.register(self.exe, registry=self.reg)
        self.assertEqual(sum('DocFitCommand' in values for values in self.reg.data.values()), 6)
        base = menu.ROOT + r'\.hwp\shell\HwpAutoDocFit'
        self.assertEqual(self.reg.data[base]['MUIVerb'], '한글편집 후처리')
        commands = [v[''] for p, v in self.reg.data.items() if p.endswith('\\command')]
        self.assertEqual(len(commands), 12)
        self.assertIn(f'"{self.exe}" convert "%1" --to pdf --notify', commands)
        self.assertIn(f'"{self.exe}" "%1"', commands)
        self.assertEqual(sum('--to hwpx ' in c for c in commands), 1)
        self.assertEqual(sum('--to pdfz ' in c for c in commands), 1)

    def test_unregister_preserves_other_apps_and_is_idempotent(self):
        menu.register(self.exe, registry=self.reg)
        self.reg.data[menu.ROOT + r'\.pdf\shell\Other'] = {}
        menu.unregister(registry=self.reg)
        menu.unregister(registry=self.reg)
        self.assertFalse(menu.status(registry=self.reg)['registered'])
        self.assertTrue(any(p.endswith('Other') for p in self.reg.data))
        self.assertFalse(any('HwpAutoDocFit' in p for p in self.reg.data))

    def test_status_and_path_refresh_only_when_registered(self):
        with patch.object(menu, 'launch_command', return_value=[self.exe]):
            menu.refresh_registered(registry=self.reg)
            self.assertEqual(self.reg.data, {})
            menu.register(r'C:\old\launcher.exe', registry=self.reg)
            menu.refresh_registered(registry=self.reg)
            self.assertEqual(menu.status(registry=self.reg), {'registered': True, 'command': f'"{self.exe}"'})
            before = dict(self.reg.data)
            menu.refresh_registered(registry=self.reg)
            self.assertEqual(self.reg.data, before)

    def test_development_command_and_launcher_environment(self):
        parts = [r'C:\Python Path\python.exe', r'C:\개발 폴더\hwp-auto-docfit.py']
        entries = menu.menu_entries(parts)
        commands = [v[''] for p, v in entries.items() if p.endswith('\\command')]
        self.assertTrue(all(c.startswith('"' + parts[0] + '" "' + parts[1] + '" ') for c in commands))
        with patch.dict(os.environ, {'DOCFIT_LAUNCHER_PATH': self.exe}):
            self.assertEqual(menu.launch_command(), [self.exe])
