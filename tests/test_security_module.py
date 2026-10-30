"""한/글 자동화 보안 모듈 DLL이 SECURITY.md에 적은 것과 같은지(보안 검토 S9)."""
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecurityModuleTest(unittest.TestCase):
    def test_bundled_dll_matches_documented_hash(self):
        digest = hashlib.sha256((ROOT / "MapoHwpAutoDocFitSecurity.dll").read_bytes()).hexdigest().upper()
        self.assertIn(digest, (ROOT / "SECURITY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
