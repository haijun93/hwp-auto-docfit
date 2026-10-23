from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DistributionBuildTest(unittest.TestCase):
    def test_spec_builds_onedir_bundle_for_installer_and_smart_launcher(self):
        spec = (ROOT / "HWP_AutoDocFit.spec").read_text(encoding="utf-8")
        self.assertIn("installer_exe = EXE", spec)
        self.assertIn("COLLECT(installer_exe, a.binaries, a.datas", spec)
        self.assertNotIn("portable = EXE", spec)
        self.assertNotIn("Splash(", spec)

    def test_installer_is_per_user_and_closes_running_app_for_update(self):
        iss = (ROOT / "installer" / "setup.iss").read_text(encoding="utf-8")
        self.assertIn("PrivilegesRequired=lowest", iss)
        self.assertIn(r"{localappdata}\Programs\HWP_AutoDocFit", iss)
        # AppMutex aborts before Restart Manager can close the running copy.
        self.assertNotRegex(iss, r"(?m)^AppMutex=")
        self.assertIn("CloseApplications=yes", iss)
        self.assertIn("CloseApplicationsFilter=*.exe,*.dll,*.pyd", iss)
        self.assertIn('Flags: nowait; Check: WizardSilent', iss)
        self.assertIn("{autoprograms}", iss)
        self.assertIn("{autodesktop}", iss)
        self.assertIn("[UninstallDelete]", iss)

    def test_unified_build_script_emits_versioned_portable_and_setup(self):
        build = (ROOT / "build_dist.bat").read_text(encoding="utf-8")
        self.assertIn("Onedir app bundle for the installer and cached portable launcher", build)
        self.assertIn("scripts\\build_smart_launcher.py", build)
        self.assertIn("HWP_AutoDocFit_v%VERSION%_Portable.exe", build)
        self.assertIn("HWP_AutoDocFit_v%VERSION%_Setup.exe", build)
        self.assertRegex(build, re.compile(r"where ISCC\.exe", re.IGNORECASE))

    def test_github_and_gitlab_release_assets_distinguish_portable_and_setup(self):
        build = (ROOT / ".github" / "workflows" / "build-windows-exe.yml").read_text(encoding="utf-8")
        release = (ROOT / ".github" / "workflows" / "github-release.yml").read_text(encoding="utf-8")
        gitlab = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
        for source in (build, release, gitlab):
            self.assertIn("HWP_AutoDocFit_v${VERSION}_Portable.exe", source)
            self.assertIn("HWP_AutoDocFit_v${VERSION}_Setup.exe", source)
        self.assertIn("PORTABLE (Portable, no installation)", gitlab)
        self.assertIn("SETUP (Installer)", gitlab)

    def test_self_test_guard_precedes_gui_mutex_and_main(self):
        source = (ROOT / "hwp-auto-docfit.py").read_text(encoding="utf-8")
        selftest_guard = source.index('if __name__ == "__main__" and "--self-test" in _selftest_sys.argv:')
        mutex_check = source.index("if not _단일_인스턴스_확인():")
        entrypoint = source.rindex('if __name__ == "__main__":')
        self.assertLess(selftest_guard, mutex_check)
        self.assertLess(mutex_check, entrypoint)

    def test_release_test_procedure_makes_format_fidelity_the_only_final_acceptance_gate(self):
        procedure = (ROOT / "docs" / "RELEASE_TEST_PROCEDURE.md").read_text(encoding="utf-8")
        self.assertIn("서식재연검수절차", procedure)
        self.assertIn("서식 원본과 재연된 검수 결과물의 일치 여부만", procedure)
        self.assertIn("불일치가 하나라도 있으면 최종 검수 불합격", procedure)
        self.assertIn("최종 릴리즈 적합 판정은 위 서식 재연 일치 여부만으로 내린다", procedure)


if __name__ == "__main__":
    unittest.main()
