"""Preview builds must not depend on ignored generated source or expose profile data."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("docfit_preview_settings_test", ROOT / "scripts/preview_settings.py")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class PreviewBuildTest(unittest.TestCase):
    def test_custom_profile_uses_temporary_defines_instead_of_dart_source(self):
        with tempfile.TemporaryDirectory() as folder:
            profile = Path(folder) / "profile.json"
            profile.write_text(json.dumps({"name": "PRIVATE_REVIEW_SAMPLE", "element_analysis": {}}), encoding="utf-8")
            seen = []
            def run(command, **kwargs):
                filename = Path(next(x.split("=", 1)[1] for x in command if x.startswith("--dart-define-from-file=")))
                defines = json.loads(filename.read_text(encoding="utf-8"))
                self.assertEqual(json.loads(defines["DOCFIT_PREVIEW_PROFILE"])["name"], "PRIVATE_REVIEW_SAMPLE")
                self.assertIn("tool/profile_preview.dart", command)
                seen.append(filename)
            tracked = ROOT / "flutter_ui/tool/preview_data.dart"
            before = tracked.read_bytes()
            with patch.dict(os.environ, {"FLUTTER": "fake-flutter"}), patch.object(preview.subprocess, "run", side_effect=run):
                preview.build(Path(folder) / "output", profile)
            self.assertEqual(tracked.read_bytes(), before)
            self.assertTrue(seen)
            self.assertTrue(all(not path.exists() for path in seen))

    def test_failed_settings_build_cleans_temporary_defines(self):
        seen = []
        def run(command, **kwargs):
            filename = Path(next(x.split("=", 1)[1] for x in command if x.startswith("--dart-define-from-file=")))
            data = json.loads(filename.read_text(encoding="utf-8"))
            self.assertTrue(json.loads(data["DOCFIT_PREVIEW_SETTINGS"])["fields"])
            seen.append(filename)
            raise subprocess.CalledProcessError(1, command)
        with patch.dict(os.environ, {"FLUTTER": "fake-flutter"}), patch.object(preview.subprocess, "run", side_effect=run):
            with self.assertRaises(subprocess.CalledProcessError):
                preview.build(Path("unused-output"))
        self.assertTrue(seen)
        self.assertTrue(all(not path.exists() for path in seen))
