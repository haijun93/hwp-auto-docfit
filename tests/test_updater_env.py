"""업데이트로 새 exe를 띄울 때 PyInstaller 내부 변수를 넘기지 않는다(2026-10-10 'Failed to load Python DLL' 오류)."""
import unittest

from docfit_core.updater import install_script, launch_environment


class UpdaterEnvironmentTest(unittest.TestCase):
    def test_pyinstaller_variables_are_removed_and_reset_is_set(self):
        env = launch_environment({"PATH": "C:\Windows", "_PYI_ARCHIVE_FILE": "x.exe", "_PYI_APPLICATION_HOME_DIR": "C:\T\_MEI1",
                                  "_pyi_parent_process_level": "1", "_MEIPASS2": "C:\T\_MEI1", "TEMP": "C:\T"})
        self.assertEqual(env["PATH"], "C:\Windows")
        self.assertEqual(env["TEMP"], "C:\T")
        self.assertFalse([k for k in env if k.upper().startswith("_PYI_") or k.upper() == "_MEIPASS2"])
        self.assertEqual(env["PYINSTALLER_RESET_ENVIRONMENT"], "1")

    def test_install_script_clears_variables_before_starting_new_exe(self):
        script = install_script()
        clear = script.index("_PYI_*")
        self.assertLess(clear, script.index("Start-Process -FilePath $Target -PassThru"))
        self.assertIn("$env:PYINSTALLER_RESET_ENVIRONMENT = '1'", script)


if __name__ == '__main__':
    unittest.main()
