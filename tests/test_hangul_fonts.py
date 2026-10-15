"""한/글 글꼴 폴더 자동 인식(docfit_core.hangul_fonts, 2026-10-16)."""
import os
import unittest
from pathlib import Path
from unittest import mock

from docfit_core import hangul_fonts

MALGUN = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "malgun.ttf"


class HangulFontsTest(unittest.TestCase):
    def setUp(self):
        hangul_fonts.catalog.cache_clear()
        self.addCleanup(hangul_fonts.catalog.cache_clear)

    @unittest.skipUnless(MALGUN.is_file(), "Windows 맑은 고딕이 있는 PC에서만")
    def test_korean_family_name_is_read_from_name_table(self):
        self.assertIn(("맑은 고딕", "Malgun Gothic"), hangul_fonts._font_names(MALGUN))

    def test_hangul_private_ttf_folder_is_found_under_shared_data_path(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            shared = Path(folder) / "Shared"
            (shared / "TTF" / "Hwp").mkdir(parents=True)
            (shared / "TTF" / "Hwp" / "HMKMM.TTF").write_bytes(b"\0" * 16)
            (shared / "Fonts").mkdir()
            (shared / "Fonts" / "HMKSM.HFT").write_bytes(b"\0")       # HFT 폴더는 쓰지 않는다
            with mock.patch.object(hangul_fonts, "_registry_shared_dirs", return_value=[shared]), \
                    mock.patch.dict(os.environ, {"ProgramFiles(x86)": "", "ProgramFiles": ""}):
                dirs = hangul_fonts.hangul_font_dirs()
            self.assertEqual(dirs, [shared / "TTF" / "Hwp"])

    def test_font_file_only_serves_catalogued_fonts_inside_found_folders(self):
        entries = [{"name": "가짜 글꼴", "path": r"C:\Windows\system32\notepad.exe", "source": "system"}]
        with mock.patch.object(hangul_fonts, "catalog", return_value=entries):
            self.assertIsNone(hangul_fonts.font_file("가짜 글꼴"))            # 글꼴 확장자·폴더가 아니면 내주지 않는다
            self.assertIsNone(hangul_fonts.font_file("없는 글꼴"))

    @unittest.skipUnless(MALGUN.is_file(), "Windows 글꼴이 있는 PC에서만")
    def test_catalog_lists_korean_names_first(self):
        names = hangul_fonts.names()
        self.assertIn("맑은 고딕", names)
        first_latin = next(i for i, n in enumerate(names) if not hangul_fonts._is_korean(n))
        self.assertTrue(all(hangul_fonts._is_korean(n) for n in names[:first_latin]))
        self.assertEqual(hangul_fonts.font_file("맑은 고딕").name.lower(), "malgun.ttf")


if __name__ == "__main__":
    unittest.main()
