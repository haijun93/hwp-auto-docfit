"""작업로그 파일·무결성검사 JSON·최종검수 JSON은 사용자가 켜기 전까지 꺼져 있다(기본값 + 예전 설정 1회 이전)."""
import json
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

KEYS = ('log_file', 'integrity_report_file', 'final_review_file')


class ReportFilesDefaultOffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.load = staticmethod(ns['설정_불러오기'])
        cls.defaults = ns['기본_설정']
        cls.g = ns['설정_불러오기'].__globals__

    def load_saved(self, saved):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'settings.json'
            if saved is not None:
                path.write_text(json.dumps(saved), encoding='utf-8')
            with patch.dict(self.g, {'설정_파일_경로': lambda: path}):
                return self.load()

    def test_defaults_are_off(self):
        for key in KEYS:
            self.assertFalse(self.defaults[key], key)
        self.assertFalse(self.g['무결성보고서파일_사용'])

    def test_first_run_has_all_off(self):
        loaded = self.load_saved(None)
        for key in KEYS:
            self.assertFalse(loaded[key], key)

    def test_old_settings_saved_with_on_are_turned_off_once(self):
        loaded = self.load_saved({key: True for key in KEYS})
        for key in KEYS:
            self.assertFalse(loaded[key], key)
        self.assertEqual(loaded['report_files_rev'], 2)

    def test_user_choice_after_the_migration_is_kept(self):
        loaded = self.load_saved({**{key: True for key in KEYS}, 'report_files_rev': 2})
        for key in KEYS:
            self.assertTrue(loaded[key], key)


if __name__ == '__main__':
    unittest.main()
