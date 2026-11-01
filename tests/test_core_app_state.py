import unittest
from docfit_core.app_state import AppState, RunOptions


class AppStateTest(unittest.TestCase):
    def test_effective_format_and_table_exclusion(self):
        options = RunOptions(include_spacing=False, exclude_tables=True)
        self.assertEqual(options.effective_mode, "format")
        self.assertFalse(options.effective_table_spacing)
        choices = {"format": {"table_format": True}}
        result = options.resolve_stages(choices)
        self.assertFalse(result["table_format"])
        self.assertTrue(choices["format"]["table_format"])

    def test_reset_spacing_is_explicit_and_inputs_are_independent(self):
        options = RunOptions(mode="spacing", reset_spacing=False, spacing_exclude_reset=True, table_spacing=False)
        result = options.resolve_stages({})
        self.assertFalse(result["reset_spacing"])
        self.assertFalse(result["control_spacing"])
        first, second = AppState(), AppState()
        first.files.append("a.hwpx")
        first.options.include_spacing = False
        self.assertEqual(second.files, [])
        self.assertTrue(second.options.include_spacing)

    def test_invalid_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            RunOptions(mode="unknown")


class CoverageCacheTest(unittest.TestCase):
    def test_repeated_reads_reuse_analysis_and_replacement_invalidates(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from desktop_web_ui import DesktopWebBridge
        state = AppState(profiles={"a": {"name": "example", "element_analysis": {"v": 1}}})
        bridge = DesktopWebBridge(SimpleNamespace(state=state))
        with patch("desktop_web_ui._format_coverage", return_value={"count": 1}) as analyze:
            first = bridge._profiles()
            first[0]["coverage"]["count"] = 99
            self.assertEqual(bridge._profiles()[0]["coverage"]["count"], 1)
            self.assertEqual(analyze.call_count, 1)
            state.profiles["a"]["element_analysis"] = {"v": 2}
            bridge._profiles()
            self.assertEqual(analyze.call_count, 2)
            bridge.invalidate_format_coverage("a")
            bridge._profiles()
            self.assertEqual(analyze.call_count, 3)


class ConfigStoreTest(unittest.TestCase):
    def test_card_option_migration_all_combinations_and_idempotence(self):
        from itertools import product
        from docfit_core.config_store import migrate_settings
        from docfit_app.settings_schema import DEFAULTS
        keys = ("all_linespacing", "spacing_page_fit", "spacing_reset_existing")
        new = ("all_exclude_linespacing", "spacing_exclude_pagefit", "spacing_exclude_reset")
        for values in product((False, True), repeat=3):
            with self.subTest(values=values):
                moved = migrate_settings(dict(zip(keys, values)), DEFAULTS)
                self.assertEqual(tuple(moved[key] for key in new), tuple(not value for value in values))
                self.assertTrue(all(key not in moved for key in keys))
                self.assertEqual(migrate_settings(moved, DEFAULTS), moved)

    def test_card_option_defaults_preserve_current_behavior_and_reset_none_uses_stages(self):
        from docfit_core.config_store import migrate_settings
        from docfit_app.settings_schema import DEFAULTS
        self.assertFalse(DEFAULTS["all_exclude_linespacing"])
        self.assertTrue(DEFAULTS["spacing_exclude_pagefit"])
        self.assertFalse(DEFAULTS["spacing_exclude_reset"])
        moved = migrate_settings({"spacing_reset_existing": None,
                                  "stage_choices": {"spacing": {"reset_spacing": False}}}, DEFAULTS)
        self.assertTrue(moved["spacing_exclude_reset"])

    def test_margin_migration_keeps_custom_values_and_is_pure(self):
        from docfit_core.config_store import migrate_settings
        from docfit_app.settings_schema import DEFAULTS
        original = {"std_parspace_rev": 1}
        migrated = migrate_settings(original, DEFAULTS)
        self.assertEqual(migrated["std_parspace_circle"], DEFAULTS["std_parspace_circle"])
        self.assertEqual(original, {"std_parspace_rev": 1})
        custom = migrate_settings({"std_parspace_rev": 1, "std_parspace_circle": "12"}, DEFAULTS)
        self.assertEqual(custom["std_parspace_circle"], "12")

    def test_line_spacing_floor_moves_from_old_default_only(self):
        # 줄 간격 최솟값 기본 160% -> 140%(사용자 지시, 2026-10-15): 예전 기본값만 옮기고 직접 고친 값은 둔다.
        from docfit_core.config_store import migrate_settings
        from docfit_app.settings_schema import DEFAULTS
        self.assertEqual(DEFAULTS["linespacing_min"], "140")
        self.assertEqual(migrate_settings({"linespacing_min": "160"}, DEFAULTS)["linespacing_min"], "140")
        self.assertEqual(migrate_settings({"linespacing_min": "150"}, DEFAULTS)["linespacing_min"], "150")
        moved = migrate_settings({"linespacing_min": "160"}, DEFAULTS)
        self.assertEqual(migrate_settings({**moved, "linespacing_min": "160"}, DEFAULTS)["linespacing_min"], "160")
