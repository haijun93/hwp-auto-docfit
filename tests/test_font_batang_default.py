"""기본 본문 글꼴은 휴먼명조가 아니라 함초롬바탕이다(2026-10-10). 예전 설정 파일의 휴먼명조는 한 번만 바꾼다."""
import json
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class FontBatangDefaultTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.ns = ns
        cls.g = ns['설정_불러오기'].__globals__

    def load_saved(self, saved):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'settings.json'
            if saved is not None:
                path.write_text(json.dumps(saved), encoding='utf-8')
            with patch.dict(self.g, {'설정_파일_경로': lambda: path}):
                return self.ns['설정_불러오기']()

    def test_defaults(self):
        d = self.ns['기본_설정']
        self.assertEqual(d['symbol_fonts']['-']['font'], '함초롬바탕')
        self.assertEqual(d['table_fonts']['body']['font'], '함초롬바탕')
        self.assertEqual(self.ns['표_헤더서식_본문_폰트'], '함초롬바탕')
        self.assertNotIn('휴먼명조', json.dumps(d, ensure_ascii=False))

    def test_old_saved_font_is_converted_once(self):
        saved = {'symbol_fonts': {'-': {'font': '휴먼명조', 'size': '14'}},
                 'table_fonts': {'body': {'font': '휴먼명조', 'size': '12'}}}
        loaded = self.load_saved(saved)
        self.assertEqual(loaded['symbol_fonts']['-']['font'], '함초롬바탕')
        self.assertEqual(loaded['table_fonts']['body']['font'], '함초롬바탕')

    def test_choice_after_migration_is_kept(self):
        saved = {'font_batang_rev': 2, 'table_fonts': {'body': {'font': '휴먼명조', 'size': '12'}}}
        self.assertEqual(self.load_saved(saved)['table_fonts']['body']['font'], '휴먼명조')


if __name__ == '__main__':
    unittest.main()
