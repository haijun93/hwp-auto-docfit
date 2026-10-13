from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from desktop_web_ui import DesktopWebBridge, _BrowserApi
from docfit_app.abbreviation_service import AbbreviationService
from docfit_app.api_contract import ServiceError, response
from docfit_app.settings_service import SettingsService
from docfit_core.abbreviations import match_line
from docfit_core.table_style import default_style


class AbbreviationServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "settings.json"
        self.store = SettingsService(lambda: self.path)
        self.service = AbbreviationService(self.store)

    def write(self, settings):
        self.path.write_text(json.dumps(settings, ensure_ascii=False), encoding="utf-8")

    def test_new_settings_defaults_are_available_without_writing(self):
        snapshot = self.service.snapshot()
        self.assertTrue(snapshot["use_defaults"])
        self.assertTrue(all(row["builtin"] for row in snapshot["entries"]))
        self.assertIn("제목1", [row["key"] for row in snapshot["entries"]])
        self.assertFalse(self.path.exists())
        json.dumps(snapshot)

    def test_save_preserves_unrelated_settings_and_legacy_data(self):
        old = {"symbol_fonts": {"□": {"font": "사용자 글꼴"}},
               "stage_choices": {"all": {"table_style": False}},
               "future_setting": [1, 2], "abbreviations": {"old": {"future_type": "keep"}}}
        self.write(old)
        self.service.save("요약", "text", "추진 결과")
        saved = self.store.read()
        for key, value in old.items():
            if key != "abbreviations":
                self.assertEqual(saved[key], value)
        self.assertEqual(saved["abbreviations"]["old"], old["abbreviations"]["old"])
        self.assertEqual(match_line("요약: 내용", self.service.user_entries()), ("요약", "내용", 4))

    def test_rename_and_edit_keep_learned_table_style(self):
        style = dict(default_style(), source="배운 서식.hwpx")
        self.write({"abbreviations": {"표": {"type": "format", "value": "table", "style": style}}})
        self.service.save("새표", "format", "table", "표")
        self.assertEqual(self.store.read()["abbreviations"], {
            "새표": {"type": "format", "value": "table", "style": style}})
        self.service.save("새표", "format", "table", "새표")
        self.assertEqual(self.service.user_entries()["새표"]["style"], style)

    def test_duplicate_rename_is_rejected_without_destroying_either_entry(self):
        self.service.save("가", "text", "첫째")
        self.service.save("나", "text", "둘째")
        original = self.path.read_bytes()
        with self.assertRaises(ServiceError) as caught:
            self.service.save("나", "text", "덮기", "가")
        self.assertEqual(caught.exception.code, "DUPLICATE_KEY")
        self.assertEqual(self.path.read_bytes(), original)

    def test_default_override_and_delete_restore_inherited_entry(self):
        self.service.save("제목1", "text", "내 제목")
        row = next(row for row in self.service.snapshot()["entries"] if row["key"] == "제목1")
        self.assertFalse(row["builtin"])
        result = self.service.delete("제목1")
        row = next(row for row in result["entries"] if row["key"] == "제목1")
        self.assertTrue(row["builtin"])
        self.assertEqual(row["value"], "title1")
        with self.assertRaises(ServiceError):
            self.service.delete("제목1")

    def test_default_switch_and_user_entries_survive_reopening(self):
        self.service.save("요약", "text", "결과")
        self.service.set_defaults(False)
        reopened = AbbreviationService(SettingsService(self.path))
        self.assertFalse(reopened.defaults_enabled())
        self.assertEqual([row["key"] for row in reopened.snapshot()["entries"]], ["요약"])

    def test_validation_leaves_registry_unchanged(self):
        self.service.save("요약", "text", "결과")
        original = self.path.read_bytes()
        for args in [("두 어절", "text", "본문", ""), ("가", "text", "", ""),
                     ("가", "format", "midtitle", ""), ("가", "format", "unknown", ""),
                     ("가", "text", "x" * 501, ""), (None, "text", "본문", ""),
                     ("가", "text", "본문", "없는준말")]:
            with self.subTest(args=args[:2]), self.assertRaises(ServiceError):
                self.service.save(*args)
            self.assertEqual(self.path.read_bytes(), original)
        with self.assertRaises(ServiceError):
            self.service.set_defaults("false")

    def test_running_job_rejects_all_mutations(self):
        self.service.save("요약", "text", "결과")
        original = self.path.read_bytes()
        for action in [lambda: self.service.save("요약", "text", "바뀜", "요약", running=True),
                       lambda: self.service.delete("요약", running=True),
                       lambda: self.service.set_defaults(False, running=True),
                       lambda: self.service.replace_entries({}, running=True)]:
            with self.assertRaises(ServiceError) as caught:
                action()
            self.assertEqual(caught.exception.code, "JOB_RUNNING")
        self.assertEqual(self.path.read_bytes(), original)

    def test_tk_bulk_adapter_and_flutter_read_share_the_same_registry(self):
        entries = {"요약": {"type": "text", "value": "결과"},
                   "로3": {"type": "format", "value": "midtitle"}}
        self.service.replace_entries(deepcopy(entries))
        self.assertEqual(self.service.user_entries(), entries)
        self.service.save("요약", "text", "바뀐 결과", "요약")
        self.assertEqual(self.service.user_entries()["요약"]["value"], "바뀐 결과")

    def test_corrupt_settings_are_not_reset_or_overwritten(self):
        self.path.write_text("{broken", encoding="utf-8")
        result = response(lambda: self.service.save("요약", "text", "결과"))
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "SETTINGS_READ_FAILED")
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{broken")

    def test_malformed_format_value_does_not_break_snapshot_or_get_erased(self):
        malformed = {"type": "format", "value": []}
        self.write({"abbreviations": {"깨짐": malformed}, "abbreviation_defaults": False})
        self.assertEqual(self.service.snapshot()["entries"], [])
        self.service.save("요약", "text", "결과")
        self.assertEqual(self.store.read()["abbreviations"]["깨짐"], malformed)

    def test_replace_failure_keeps_original_and_cleans_temporary_output(self):
        self.service.save("요약", "text", "결과")
        original = self.path.read_bytes()
        with patch("docfit_app.settings_service.os.replace", side_effect=PermissionError("denied")):
            result = response(lambda: self.service.set_defaults(False))
        self.assertEqual(result["error"]["code"], "SETTINGS_WRITE_FAILED")
        self.assertEqual(self.path.read_bytes(), original)
        # The persistent process-lock sidecar must remain: unlinking a locked
        # inode would allow another writer to acquire a different lock.
        self.assertEqual(set(self.path.parent.iterdir()),
                         {self.path, self.path.with_name(self.path.name + '.lock')})

    def test_browser_api_returns_versioned_json_and_structured_job_error(self):
        gui = SimpleNamespace(root=SimpleNamespace(after=lambda _delay, callback: callback()),
                              running=False, _준말_서비스=lambda: self.service)
        api = _BrowserApi(DesktopWebBridge(gui))
        result = api.save_abbreviation("요약", "text", "결과")
        self.assertEqual(result["api_version"], 1)
        self.assertTrue(result["ok"])
        json.dumps(result)
        self.assertEqual(api.get_abbreviations()["data"], result["data"])
        gui.running = True
        result = api.delete_abbreviation("요약")
        self.assertEqual(result["error"], {"code": "JOB_RUNNING",
                         "message": "작업 중에는 준말을 바꿀 수 없습니다.", "recoverable": True})
        self.assertNotIn("_준말_서비스", vars(api))


if __name__ == "__main__":
    unittest.main()
