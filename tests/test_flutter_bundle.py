from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from desktop_web_ui import _resource_path
from docfit_core.flutter_bundle import REQUIRED_FILES, validate_bundle


class FlutterBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bundle = self.base / "desktop_web" / "flutter"
        for name in REQUIRED_FILES:
            path = self.bundle / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fixture")

    def test_complete_bundle_is_preferred_to_legacy_ui(self):
        self.assertEqual(validate_bundle(self.bundle), self.bundle)
        with patch("sys._MEIPASS", str(self.base), create=True):
            self.assertEqual(_resource_path(), self.bundle / "index.html")

    def test_packaging_rejects_absent_or_empty_renderer_and_font(self):
        for name in ("main.dart.js", "canvaskit/canvaskit.wasm", "assets/assets/NotoSansKR.ttf"):
            path = self.bundle / name
            path.write_bytes(b"")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, name.replace(".", r"\.")):
                validate_bundle(self.bundle)
            path.write_bytes(b"fixture")
        (self.bundle / "flutter_bootstrap.js").unlink()
        with self.assertRaisesRegex(ValueError, "flutter_bootstrap"):
            validate_bundle(self.bundle)

    def test_missing_flutter_build_keeps_runtime_emergency_fallback(self):
        (self.bundle / "main.dart.js").unlink()
        with patch("sys._MEIPASS", str(self.base), create=True):
            self.assertEqual(_resource_path(), self.base / "desktop_web" / "index.html")
