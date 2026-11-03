"""실제 앱 판정 스크립트의 사용자 데이터 경로 격리 계약."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_related_docs.py"
SPEC = importlib.util.spec_from_file_location("verify_related_docs", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VerifyRelatedDocsIsolationTests(unittest.TestCase):
    def test_settings_and_content_index_resolve_inside_isolated_roots(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = MODULE.resolve_isolated_paths(
                {"APPDATA": str(root / "roaming"), "LOCALAPPDATA": str(root / "local")}, root)
            self.assertTrue(paths["settings"].is_relative_to(root))
            self.assertTrue(paths["timeline"].is_relative_to(root))
            self.assertEqual(paths["settings"], root / "roaming" / "HwpAutoDocFit" / "settings.json")
            self.assertEqual(paths["timeline"], root / "local" / "HwpAutoDocFit" / "timeline-content.sqlite")

    def test_mkdir_lock_is_acquired_and_only_owned_lock_is_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            lock = Path(folder) / ".app-test.lock"
            self.assertTrue(MODULE.acquire_lock(lock, timeout=0))
            self.assertTrue(lock.is_dir())
            self.assertFalse(MODULE.acquire_lock(lock, timeout=0))
            lock.rmdir()
            self.assertTrue(MODULE.acquire_lock(lock, timeout=0))

    def test_process_filter_uses_executable_path_and_excludes_siblings(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "test-root"
            child = root / "app_main.exe"
            sibling = Path(folder) / "other" / "app_main.exe"
            child.parent.mkdir(parents=True)
            sibling.parent.mkdir(parents=True)
            child.touch()
            sibling.touch()

            class FakeProcess:
                Error = RuntimeError

                def __init__(self, executable):
                    self.info = {"exe": str(executable)}

            fake_psutil = Mock()
            fake_psutil.process_iter.return_value = [FakeProcess(child), FakeProcess(sibling)]
            found = MODULE.process_executable_under(root, fake_psutil)
            self.assertEqual(len(found), 1)
            self.assertEqual(Path(found[0].info["exe"]).resolve(), child.resolve())

    def test_appdata_precedence_matches_settings_folder_implementation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = MODULE.resolve_isolated_paths(
                {"APPDATA": str(root / "roaming"), "LOCALAPPDATA": str(root / "local")}, root)
            self.assertEqual(paths["settings"].parents[1], root / "roaming")

    def test_without_appdata_uses_localappdata_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = MODULE.resolve_isolated_paths({"LOCALAPPDATA": str(root / "local")}, root)
            self.assertEqual(paths["settings"], root / "local" / "HwpAutoDocFit" / "settings.json")
            self.assertTrue(paths["timeline"].is_relative_to(root))


if __name__ == "__main__":
    unittest.main()
