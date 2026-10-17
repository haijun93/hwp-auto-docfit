from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DistributionBuildTest(unittest.TestCase):
    def test_spec_has_separate_onefile_splash_and_onedir_targets(self):
        spec = (ROOT / "HWP_AutoDocFit.spec").read_text(encoding="utf-8")
        self.assertIn("installer_exe = EXE", spec)
        self.assertIn("COLLECT(installer_exe, a.binaries, a.datas", spec)
        self.assertIn("portable = EXE", spec)
        self.assertIn("Splash(", spec)
        self.assertIn("always_on_top=True", spec)
        self.assertIn("text_pos=None", spec)

    def test_installer_is_per_user_and_has_shortcuts_and_mutex(self):
        iss = (ROOT / "installer" / "setup.iss").read_text(encoding="utf-8")
        self.assertIn("PrivilegesRequired=lowest", iss)
        self.assertIn(r"{localappdata}\Programs\HWP_AutoDocFit", iss)
        self.assertIn(r"Global\HWP_AutoDocFit_SingleInstance_Mutex", iss)
        self.assertIn(r"Local\HWP_AutoDocFit_SingleInstance_Mutex", iss)
        self.assertIn("{autoprograms}", iss)
        self.assertIn("{autodesktop}", iss)
        self.assertIn("[UninstallDelete]", iss)

    def test_unified_build_script_emits_versioned_portable_and_setup(self):
        build = (ROOT / "build_dist.bat").read_text(encoding="utf-8")
        self.assertIn("Onefile and installer Onedir from one analysis", build)
        self.assertIn("HWP_AutoDocFit_v%VERSION%_Portable.exe", build)
        self.assertIn("HWP_AutoDocFit_v%VERSION%_Setup.exe", build)
        self.assertRegex(build, re.compile(r"where ISCC\.exe", re.IGNORECASE))

    def test_self_test_guard_precedes_gui_mutex_and_main(self):
        source = (ROOT / "hwp-auto-docfit.py").read_text(encoding="utf-8")
        selftest_guard = source.index('if __name__ == "__main__" and "--self-test" in _selftest_sys.argv:')
        mutex_check = source.index("if not _단일_인스턴스_확인():")
        entrypoint = source.rindex('if __name__ == "__main__":')
        self.assertLess(selftest_guard, mutex_check)
        self.assertLess(mutex_check, entrypoint)


if __name__ == "__main__":
    unittest.main()
