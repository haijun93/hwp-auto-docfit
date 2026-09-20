"""Verify the Windows GUI can start without processing a document."""

import os
import base64
import io
from pathlib import Path
import runpy
import tempfile
import unittest
import urllib.error
from unittest.mock import Mock, patch


class StartupTest(unittest.TestCase):
    def test_release_version_and_exe_asset_selection(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="updater_test")
        version_tuple = namespace["_버전_튜플"]
        select_asset = namespace["_업데이트_자산_선택"]

        self.assertGreater(version_tuple("v1.66"), version_tuple("1.65"))
        preferred = {"name": "HWP_AutoDocFit.exe", "browser_download_url": "https://example.test/app.exe"}
        release = {"assets": [{"name": "notes.txt"}, preferred, {"name": "other.exe"}]}
        self.assertIs(select_asset(release), preferred)

    def test_gitlab_release_asset_is_normalized(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="gitlab_updater_test")
        select_asset = namespace["_업데이트_자산_선택"]

        release = {
            "assets": [{
                "name": "HWP_AutoDocFit.exe",
                "browser_download_url": "https://gitlab.example/releases/app.exe",
            }]
        }
        self.assertEqual(
            select_asset(release)["browser_download_url"],
            "https://gitlab.example/releases/app.exe",
        )

    def test_gitlab_without_releases_is_treated_as_up_to_date(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="no_release_updater_test")
        fetch_release = namespace["_최신_릴리스_조회"]
        not_found = urllib.error.HTTPError(
            namespace["UPDATE_API_URL"], 404, "Not Found", {}, None
        )
        self.addCleanup(not_found.close)

        with patch.object(namespace["urllib"].request, "urlopen", side_effect=not_found):
            self.assertIsNone(fetch_release())

    def test_pillow_is_available_and_embedded_cat_images_are_valid(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="pillow_test")

        image_module = namespace["Image"]
        self.assertIsNotNone(image_module)
        for variable_name in ("SETTINGS_CAT_BASE64", "MAIN_CAT_STATES_BASE64"):
            image_bytes = base64.b64decode(namespace[variable_name])
            with image_module.open(io.BytesIO(image_bytes)) as image:
                image.verify()

    def test_missing_pillow_triggers_install_and_retry(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="pillow_install_test")
        load_pillow = namespace["_load_pillow"]
        expected_modules = (object(), object(), object())
        import_pillow = Mock(side_effect=[ImportError("missing"), expected_modules])
        install_pillow = Mock()

        with patch.dict(load_pillow.__globals__, {
            "_import_pillow": import_pillow,
            "_install_pillow": install_pillow,
        }):
            self.assertEqual(load_pillow(), expected_modules)

        install_pillow.assert_called_once_with()
        self.assertEqual(import_pillow.call_count, 2)

    def test_frozen_app_never_runs_pip(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="frozen_dependency_test")
        install_pillow = namespace["_install_pillow"]
        run_command = Mock()

        with patch.object(namespace["sys"], "frozen", True, create=True), \
                patch.dict(install_pillow.__globals__, {"_run_dependency_command": run_command}):
            with self.assertRaisesRegex(RuntimeError, "PyInstaller"):
                install_pillow()

        run_command.assert_not_called()

    def test_partial_charshape_does_not_fill_unrequested_bold(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="charshape_test")

        class ParameterSet:
            def __init__(self):
                self.items = {}

            def SetItem(self, name, value):
                self.items[name] = value

        class Action:
            def __init__(self):
                self.parameters = ParameterSet()

            def CreateSet(self):
                return self.parameters

            def Execute(self, parameters):
                return True

        class FakeHwp:
            def __init__(self):
                self.action = Action()

            def CreateAction(self, name):
                self.action_name = name
                return self.action

        fake = FakeHwp()
        apply_charshape = namespace["문자모양_적용_현재선택"]
        apply_charshape.__globals__["hwp"] = fake
        apply_charshape(자간=0)
        self.assertEqual(fake.action_name, "CharShape")
        self.assertNotIn("Bold", fake.action.parameters.items)
        self.assertEqual(fake.action.parameters.items["SpacingHangul"], 0)

    def test_gui_initializes_without_callback_errors(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        with tempfile.TemporaryDirectory(prefix="hwp-docfit-test-") as settings_dir:
            with patch.dict(os.environ, {"APPDATA": settings_dir}):
                namespace = runpy.run_path(str(source), run_name="startup_test")
                root = namespace["TkinterDnD"].Tk()
                root.withdraw()
                callback_errors = []
                root.report_callback_exception = lambda *args: callback_errors.append(args)
                try:
                    app = namespace["HwpAutoDocFitGUI"](root)
                    root.update()
                    self.assertTrue(root.winfo_children())
                    self.assertEqual(callback_errors, [])
                    self.assertIsNone(app.worker)
                    self.assertFalse(app.running)
                    self.assertTrue(app.check_updates_on_start_var.get())
                    self.assertEqual(app.main_profile_combo.get(), "기본 보고서 서식")
                    self.assertIn("HWP/HWPX", app.format_drop_label.cget("text"))
                finally:
                    root.destroy()


if __name__ == "__main__":
    unittest.main()
