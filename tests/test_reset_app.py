"""원상복구 및 초기화 도구(hwp-auto-docfit-reset.py) 단위 테스트."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import importlib.util

# hwp-auto-docfit-reset.py 모듈 로드
spec = importlib.util.spec_from_file_location(
    "hwp_auto_docfit_reset",
    Path(__file__).resolve().parents[1] / "hwp-auto-docfit-reset.py",
)
reset_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reset_mod)


class ResetAppTest(unittest.TestCase):
    def test_settings_folders_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            appdata = Path(temp_dir) / "appdata"
            appdata.mkdir()
            docfit_dir = appdata / "HwpAutoDocFit"
            docfit_dir.mkdir()

            with patch.dict(os.environ, {"APPDATA": str(appdata), "LOCALAPPDATA": ""}):
                folders = reset_mod.설정_폴더_목록()
                self.assertIn(docfit_dir, folders)

    def test_security_dll_removal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auto_dir = Path(temp_dir) / "HwpAutomation"
            auto_dir.mkdir()
            dll_file = auto_dir / "MapoHwpAutoDocFitSecurity.dll"
            dll_file.write_text("dummy dll", encoding="utf-8")

            with patch.object(reset_mod, "HWP_AUTOMATION_DIR", auto_dir), \
                 patch.object(reset_mod, "TARGET_DLL", dll_file):
                self.assertTrue(dll_file.exists())
                ok, msg = reset_mod.보안_DLL_제거()
                self.assertTrue(ok)
                self.assertFalse(dll_file.exists())
                # 빈 폴더도 삭제되었는지 확인
                self.assertFalse(auto_dir.exists())

    def test_security_dll_removal_preserves_other_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auto_dir = Path(temp_dir) / "HwpAutomation"
            auto_dir.mkdir()
            dll_file = auto_dir / "MapoHwpAutoDocFitSecurity.dll"
            dll_file.write_text("dummy dll", encoding="utf-8")
            other_file = auto_dir / "other_security.dll"
            other_file.write_text("keep this", encoding="utf-8")

            with patch.object(reset_mod, "HWP_AUTOMATION_DIR", auto_dir), \
                 patch.object(reset_mod, "TARGET_DLL", dll_file):
                ok, msg = reset_mod.보안_DLL_제거()
                self.assertTrue(ok)
                self.assertFalse(dll_file.exists())
                # 다른 파일이 있으므로 폴더는 보존되어야 함
                self.assertTrue(auto_dir.exists())
                self.assertTrue(other_file.exists())

    def test_registry_removal_logic(self):
        from unittest.mock import MagicMock
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.QueryInfoKey.return_value = (0, 0, 0)
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_ALL_ACCESS = 2
        mock_winreg.KEY_READ = 3

        with patch.object(reset_mod, "winreg", mock_winreg):
            ok, msg = reset_mod.레지스트리_제거()
            self.assertTrue(ok)
            mock_winreg.DeleteValue.assert_called_with(mock_key, "MapoHwpAutoDocFitSecurity")

    def test_settings_folder_removal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_dir = Path(temp_dir) / "HwpAutoDocFit"
            settings_dir.mkdir()
            (settings_dir / "settings.json").write_text("{}", encoding="utf-8")

            with patch.object(reset_mod, "설정_폴더_목록", return_value=[settings_dir]):
                self.assertTrue(settings_dir.exists())
                ok, msg = reset_mod.설정폴더_제거()
                self.assertTrue(ok)
                self.assertFalse(settings_dir.exists())


if __name__ == '__main__':
    unittest.main()
