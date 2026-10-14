import json
from pathlib import Path
import tempfile
import unittest

from docfit_app.api_contract import ServiceError
from docfit_app.application_service import ApplicationService
from docfit_app.diagram_service import DiagramService
from docfit_app.settings_service import SettingsService


class DiagramServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = SettingsService(self.root / "settings.json")
        self.service = DiagramService(self.root, self.settings)
        self.diagram_id = "0123456789abcdef0123456789abcdef"
        self.snapshot = {"document": {"store": {"shape:1": {"typeName": "shape"}}}}

    def enable(self):
        self.settings.update(lambda values: values.update({
            "developer_mode": True, "diagram_editor_enabled": True,
        }))

    def test_feature_is_denied_until_both_flags_are_on(self):
        with self.assertRaises(ServiceError) as caught:
            self.service.list()
        self.assertEqual(caught.exception.code, "DIAGRAMS_DISABLED")
        self.settings.update(lambda values: values.update({"developer_mode": True}))
        with self.assertRaises(ServiceError):
            self.service.list()
        self.enable()
        self.assertEqual(self.service.list(), [])

    def test_save_load_list_and_delete(self):
        self.enable()
        saved = self.service.save(self.diagram_id, "민원 처리", self.snapshot)
        self.assertEqual(saved["id"], self.diagram_id)
        self.assertEqual(self.service.list()[0]["name"], "민원 처리")
        self.assertEqual(self.service.load(self.diagram_id)["snapshot"], self.snapshot)
        self.service.delete(self.diagram_id)
        self.assertEqual(self.service.list(), [])

    def test_disabling_developer_mode_blocks_all_operations_even_with_editor_enabled(self):
        self.enable()
        self.service.save(self.diagram_id, "보존할 도형", self.snapshot)
        self.settings.update(lambda values: values.update({"developer_mode": False}))
        for operation in (
            self.service.list,
            lambda: self.service.load(self.diagram_id),
            lambda: self.service.save(self.diagram_id, "수정 금지", self.snapshot),
            lambda: self.service.delete(self.diagram_id),
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(ServiceError) as caught:
                    operation()
                self.assertEqual(caught.exception.code, "DIAGRAMS_DISABLED")
        self.enable()
        self.assertEqual(self.service.load(self.diagram_id)["name"], "보존할 도형")

    def test_rejects_traversal_invalid_data_and_oversized_snapshots(self):
        self.enable()
        with self.assertRaises(ServiceError):
            self.service.load("..\\settings")
        with self.assertRaises(ServiceError):
            self.service.save(self.diagram_id, " ", self.snapshot)
        with self.assertRaises(ServiceError):
            self.service.save(self.diagram_id, "ok", "not an object")
        with self.assertRaises(ServiceError) as caught:
            self.service.save(self.diagram_id, "large", {"blob": "x" * (720 * 1024)})
        self.assertEqual(caught.exception.code, "DIAGRAM_TOO_LARGE")

    def test_failed_overwrite_preserves_previous_document(self):
        self.enable()
        self.service.save(self.diagram_id, "first", self.snapshot)
        with self.assertRaises(ServiceError):
            self.service.save(self.diagram_id, "second", {"bad": object()})
        self.assertEqual(self.service.load(self.diagram_id)["name"], "first")
        self.assertFalse(list(self.service.root.glob("*.tmp")))

    def test_symlink_document_is_not_followed(self):
        self.enable()
        outside = self.root / "outside.json"
        outside.write_text(json.dumps({"snapshot": self.snapshot}), encoding="utf-8")
        self.service.root.mkdir()
        path = self.service.root / f"{self.diagram_id}.json"
        try:
            path.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links are unavailable in this test account")
        with self.assertRaises(ServiceError):
            self.service.load(self.diagram_id)

    def test_application_api_enforces_flag_and_routes_storage(self):
        app = ApplicationService(self.root / "settings.json")
        with self.assertRaises(ServiceError):
            app.dispatch("diagram_list", [])
        app.store.update(lambda values: values.update({
            "developer_mode": True, "diagram_editor_enabled": True,
        }))
        saved = app.dispatch("diagram_save", [self.diagram_id, "업무", self.snapshot])
        self.assertEqual(app.dispatch("diagram_load", [self.diagram_id])["snapshot"], self.snapshot)
        self.assertEqual(saved["id"], self.diagram_id)


if __name__ == "__main__":
    unittest.main()
