"""표 칸 줄 간격·자간 한도(TCELL230): 설정 기본값·이전·폐기된 20자 분기."""
import json
from pathlib import Path
import unittest

from docfit_app.settings_schema import DEFAULTS
from docfit_core.config_store import migrate_settings

ROOT = Path(__file__).resolve().parents[1]


class TableLimitSettingsTest(unittest.TestCase):
    def test_defaults(self):
        self.assertEqual(DEFAULTS['table_linespacing_min'], '100')
        self.assertEqual(DEFAULTS['table_spacing_min'], '-25')
        # 본문 한도와 분리되어 있다.
        self.assertEqual(DEFAULTS['linespacing_min'], '140')
        self.assertLess(int(DEFAULTS['table_linespacing_min']), int(DEFAULTS['linespacing_min']))

    def test_migration_keeps_explicit_values_and_does_not_inject(self):
        saved = {'table_linespacing_min': '110', 'table_spacing_min': '-10'}
        out = migrate_settings(saved, DEFAULTS)
        self.assertEqual((out['table_linespacing_min'], out['table_spacing_min']), ('110', '-10'))
        out = migrate_settings({'retry_body': '15'}, DEFAULTS)   # 옛 설정: 새 키 없음 → 기본값은 병합 단계가 채운다
        self.assertNotIn('table_spacing_min', out)

    def test_old_body_linespacing_migration_does_not_touch_table_limit(self):
        out = migrate_settings({'linespacing_min': '160', 'table_linespacing_min': '100'}, DEFAULTS)
        self.assertEqual(out['linespacing_min'], '140')
        self.assertEqual(out['table_linespacing_min'], '100')


class LegacyWideCellRemovedTest(unittest.TestCase):
    def test_no_references_left(self):
        manifest = json.loads((ROOT / 'scripts/formatter_split_manifest.json').read_text(encoding='utf-8'))
        names = {n for group in manifest.values() if isinstance(group, list) for n in group}
        self.assertNotIn('넓은_표칸_줄인가', names)
        for rel in ('hwp-auto-docfit.py', 'docfit_engine/formatter_tables.py', 'docfit_engine/spacing.py'):
            self.assertNotIn('넓은_표칸', (ROOT / rel).read_text(encoding='utf-8'), rel)

    def test_main_script_keeps_crlf(self):
        data = (ROOT / 'hwp-auto-docfit.py').read_bytes()
        self.assertEqual(data.count(b'\n'), data.count(b'\r\n'))


if __name__ == '__main__':
    unittest.main()
