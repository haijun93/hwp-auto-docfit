"""'상용구 파일저장' 기능: 번들 HWP.IDO를 한/글 전용 폴더로 복사하는 로직을 검증한다."""

import os
from pathlib import Path
import runpy
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
BUNDLED_IDIOM_FILE = Path(__file__).resolve().parents[1] / "resources" / "HWP.IDO"


class IdiomFileSaveTest(unittest.TestCase):
    def test_bundled_idiom_file_is_found_next_to_script(self):
        namespace = runpy.run_path(str(SOURCE), run_name="idiom_bundle_lookup_test")
        found = namespace["번들_상용구_파일_찾기"]()
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "HWP.IDO")
        self.assertEqual(found, BUNDLED_IDIOM_FILE)

    def test_target_folder_prefers_folder_that_already_has_idiom_file(self):
        namespace = runpy.run_path(str(SOURCE), run_name="idiom_folder_prefers_existing_test")
        find_folder = namespace["상용구_전용폴더_찾기"]
        with tempfile.TemporaryDirectory(prefix="hwp-idiom-test-") as appdata:
            hwp_root = Path(appdata) / "HNC" / "User" / "Hwp"
            (hwp_root / "60").mkdir(parents=True)
            (hwp_root / "90").mkdir(parents=True)
            (hwp_root / "60" / "HWP.IDO").write_text("existing", encoding="utf-8")
            with patch.dict(os.environ, {"APPDATA": appdata}):
                self.assertEqual(find_folder(), hwp_root / "60")

    def test_target_folder_falls_back_to_highest_numbered_folder(self):
        namespace = runpy.run_path(str(SOURCE), run_name="idiom_folder_fallback_test")
        find_folder = namespace["상용구_전용폴더_찾기"]
        with tempfile.TemporaryDirectory(prefix="hwp-idiom-test-") as appdata:
            hwp_root = Path(appdata) / "HNC" / "User" / "Hwp"
            (hwp_root / "60").mkdir(parents=True)
            (hwp_root / "90").mkdir(parents=True)
            with patch.dict(os.environ, {"APPDATA": appdata}):
                self.assertEqual(find_folder(), hwp_root / "90")

    def test_target_folder_is_none_when_hnc_folder_is_missing(self):
        namespace = runpy.run_path(str(SOURCE), run_name="idiom_folder_missing_test")
        find_folder = namespace["상용구_전용폴더_찾기"]
        with tempfile.TemporaryDirectory(prefix="hwp-idiom-test-") as appdata:
            with patch.dict(os.environ, {"APPDATA": appdata}):
                self.assertIsNone(find_folder())

    def test_save_button_copies_bundled_file_and_reports_success(self):
        with tempfile.TemporaryDirectory(prefix="hwp-idiom-save-test-") as appdata:
            hwp_root = Path(appdata) / "HNC" / "User" / "Hwp" / "60"
            hwp_root.mkdir(parents=True)
            with patch.dict(os.environ, {"APPDATA": appdata}):
                namespace = runpy.run_path(str(SOURCE), run_name="idiom_save_click_test")
                root = namespace["TkinterDnD"].Tk()
                root.withdraw()
                try:
                    app = namespace["HwpAutoDocFitGUI"](root)
                    결과들 = []
                    가짜_messagebox = SimpleNamespace(
                        showerror=lambda *a, **k: 결과들.append(("error", a, k)),
                        showinfo=lambda *a, **k: 결과들.append(("info", a, k)),
                        askyesno=lambda *a, **k: True,
                    )
                    with patch.dict(app._상용구파일_저장_클릭.__globals__, {"messagebox": 가짜_messagebox}):
                        app._상용구파일_저장_클릭()
                    대상 = hwp_root / "HWP.IDO"
                    self.assertTrue(대상.is_file())
                    self.assertEqual(대상.read_bytes(), BUNDLED_IDIOM_FILE.read_bytes())
                    self.assertEqual([종류 for 종류, _, _ in 결과들], ["info"])
                finally:
                    root.destroy()

    def test_save_button_asks_before_overwriting_existing_idiom_file(self):
        with tempfile.TemporaryDirectory(prefix="hwp-idiom-overwrite-test-") as appdata:
            hwp_root = Path(appdata) / "HNC" / "User" / "Hwp" / "60"
            hwp_root.mkdir(parents=True)
            기존_경로 = hwp_root / "HWP.IDO"
            기존_경로.write_text("사용자가 이미 등록한 상용구", encoding="utf-8")
            with patch.dict(os.environ, {"APPDATA": appdata}):
                namespace = runpy.run_path(str(SOURCE), run_name="idiom_overwrite_click_test")
                root = namespace["TkinterDnD"].Tk()
                root.withdraw()
                try:
                    app = namespace["HwpAutoDocFitGUI"](root)
                    확인_호출됨 = []
                    가짜_messagebox = SimpleNamespace(
                        showerror=lambda *a, **k: None,
                        showinfo=lambda *a, **k: None,
                        askyesno=lambda *a, **k: (확인_호출됨.append(True) or False),
                    )
                    with patch.dict(app._상용구파일_저장_클릭.__globals__, {"messagebox": 가짜_messagebox}):
                        app._상용구파일_저장_클릭()
                    self.assertTrue(확인_호출됨)
                    # 사용자가 '아니오'를 선택했으므로 기존 파일은 그대로 남아 있어야 한다.
                    self.assertEqual(기존_경로.read_text(encoding="utf-8"), "사용자가 이미 등록한 상용구")
                finally:
                    root.destroy()


if __name__ == "__main__":
    unittest.main()
