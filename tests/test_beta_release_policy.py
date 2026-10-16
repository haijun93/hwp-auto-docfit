"""Release binaries cannot enable an SDK whose distribution is unapproved."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from docfit_app.diagram_service import DiagramService


class BetaReleasePolicyTests(unittest.TestCase):
    def test_frozen_sdk_is_disabled_even_when_both_flags_are_enabled(self):
        store = SimpleNamespace(read=lambda: {"developer_mode": True, "diagram_editor_enabled": True})
        service = DiagramService(Path.cwd(), store)
        with patch("docfit_app.diagram_service.sys.frozen", True, create=True):
            self.assertFalse(service.enabled())

    def test_release_tree_contains_only_sdk_placeholder(self):
        folder = Path(__file__).resolve().parents[1] / "flutter_ui/assets/diagram_editor"
        self.assertFalse(json.loads((folder / "asset-manifest.json").read_text())["sdk_included"])
        self.assertEqual([], list(folder.rglob("*.js")))
