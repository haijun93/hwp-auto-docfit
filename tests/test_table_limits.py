import runpy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from docfit_core.config_store import ConfigStore, migrate_settings
from docfit_app.settings_schema import DEFAULTS
from docfit_core.table_limits import TableLimits, spacing_floor


class TableLimitsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_defaults_and_existing_settings(self):
        self.assertEqual(TableLimits.from_settings(DEFAULTS), TableLimits(100, -25))
        old = {'linespacing_min': '150', 'retry_table': '5'}
        merged = {**DEFAULTS, **migrate_settings(old, DEFAULTS)}
        self.assertEqual(merged['linespacing_min'], '150')
        self.assertEqual(TableLimits.from_settings(merged), TableLimits())
        self.assertEqual(TableLimits.from_settings({'table_linespacing_min': '120', 'table_spacing_min': '-15'}), TableLimits(120, -15))

    def test_invalid_limits(self):
        for settings in ({'table_linespacing_min': 99}, {'table_spacing_min': -26}, {'table_spacing_min': 1}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                TableLimits.from_settings(settings)

    def test_absolute_budget_includes_mixed_negative_spacing(self):
        for original, budget in (([0, 0], 25), ([-24, -10], 1), ([-25], 0), ([-30], 0), ([50], 75)):
            self.assertEqual(TableLimits().shrink_budget(original), budget)

    def test_body_and_single_cell_exception(self):
        doc = Mock()
        ns = {'hwp': doc, '현재_표셀인가': lambda: True, '한칸표_보호영역': {3}}
        for area, expected in ((0, -50), (2, -25), (3, -50)):
            self.assertEqual(spacing_floor(ns, area), expected)

    def test_table_and_body_line_floors(self):
        fn = self.ns['보고서_줄간격_적용']
        doc = Mock()
        doc.LineSpacingMethod.return_value = 0
        action = doc.CreateAction.return_value
        action.Execute.return_value = True
        with patch.dict(fn.__globals__, {'hwp': doc, '세트문장_최소줄간격_퍼센트': 140,
                                       '표칸_줄간격_하한': 100}):
            self.assertTrue(fn([((2, 0, 0), 0, 160)], 20))
            action.CreateSet.return_value.SetItem.assert_any_call('LineSpacing', 100)
            action.CreateSet.return_value.SetItem.reset_mock()
            self.assertTrue(fn([((0, 0, 0), 0, 160)], 20))
            action.CreateSet.return_value.SetItem.assert_any_call('LineSpacing', 140)
            self.assertFalse(fn([((2, 0, 0), 0, 90)], 20))
            self.assertFalse(fn([((2, 0, 0), 1, 160)], 20))

    def test_no_partial_write_below_spacing_floor(self):
        fn = self.ns['단어모드_자간적용']
        doc = Mock()
        doc.GetPos.return_value = (2, 0, 0)
        runs = [((2, 0, 0), (2, 0, 2), (-24,) * 7)]
        with patch.dict(fn.__globals__, {'hwp': doc, '현재_표셀인가': lambda: True,
                                       '한칸표_보호영역': set(), '표칸_자간_하한': -25}):
            with self.assertRaises(self.ns['문두보호_조정불가']):
                fn(runs, -2)
        doc.CreateAction.assert_not_called()
