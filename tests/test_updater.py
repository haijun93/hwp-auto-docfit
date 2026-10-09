import unittest

from docfit_core.updater import expected_sha256, install_script, leftover_files, verify_download

H = "0B0034E718B3D8886D3A6B9D24815D7997FD69A4C5DB2EC3B657960DAAE57E25"


class ExpectedHashTest(unittest.TestCase):
    def test_asset_digest_first(self):
        self.assertEqual(expected_sha256({"description": f"SHA-256: `{'A' * 64}`"}, {"digest": "sha256:" + H.lower()}),
                         H.lower())

    def test_release_note_hash_gitlab_and_github(self):
        note = f"다운로드:\n- `HWP_AutoDocFit.exe`\n\nSHA-256: `{H}`"
        self.assertEqual(expected_sha256({"description": note}, {}), H.lower())
        self.assertEqual(expected_sha256({"body": note}, {}), H.lower())

    def test_placeholder_or_missing_is_none(self):
        self.assertIsNone(expected_sha256({"description": "SHA-256: `SHA256_PLACEHOLDER`"}, {}))
        self.assertIsNone(expected_sha256({}, {}))


class VerifyDownloadTest(unittest.TestCase):
    def test_ok(self):
        self.assertIsNone(verify_download(10, b"MZ\x90", H.lower(), 10, H))

    def test_rejects_empty_wrong_size_html_and_bad_hash(self):
        self.assertIn("비어", verify_download(0, b"", ""))
        self.assertIn("크기", verify_download(9, b"MZ", "", 10))
        self.assertIn("EXE", verify_download(10, b"<!DOCTYPE html>", ""))
        self.assertIn("SHA-256", verify_download(10, b"MZ", "0" * 64, None, H))

    def test_missing_hash_fails_closed(self):
        self.assertIn("SHA-256 정보가 없어", verify_download(10, b"MZ", H.lower(), 10, None))


class InstallScriptTest(unittest.TestCase):
    def test_script_renames_old_retries_and_restores(self):
        s = install_script()
        self.assertLess(s.index("내려받은 신버전 파일이 없습니다"), s.index("Move-Item -LiteralPath $Target -Destination $Old"))
        self.assertLess(s.index("Get-FileHash"), s.index("Move-Item -LiteralPath $Target -Destination $Old"))
        for 필수 in ("WaitPids", "$Target.old", "Move-Item -LiteralPath $Target -Destination $Old",
                    "Retry", "구버전 복구", "Start-Process -FilePath $Target", "Remove-Item -LiteralPath $Old"):
            self.assertIn(필수, s)
        # 검증에 실패했을 수 있는 내려받은 파일은 어떤 경우에도 실행하지 않는다(보안 검토, 2026-10-09).
        self.assertNotIn("Start-Process -FilePath $Downloaded", s)


class LeftoverTest(unittest.TestCase):
    def test_lists_old_and_stale(self):
        old, stale = leftover_files(["HWP_AutoDocFit.exe", "HWP_AutoDocFit.exe.old"],
                                    ["HWP_AutoDocFit-v1.72-beta.9.exe", "x.part", "HWP_AutoDocFit-v1.72-beta.9.ps1",
                                     "update.log", "keep.exe"], keep=("keep.exe",))
        self.assertEqual(old, ["HWP_AutoDocFit.exe.old"])
        self.assertEqual(sorted(stale), ["HWP_AutoDocFit-v1.72-beta.9.exe", "HWP_AutoDocFit-v1.72-beta.9.ps1", "x.part"])


if __name__ == "__main__":
    unittest.main()
