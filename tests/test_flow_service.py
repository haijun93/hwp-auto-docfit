from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from docfit_app.application_service import ApplicationService
from docfit_app.api_contract import ServiceError
from docfit_app.diagram_service import DiagramService
from docfit_app.flow_service import FlowService
from docfit_app.settings_service import SettingsService
from desktop_web_ui import DesktopWebBridge


class FlowServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.store = SettingsService(self.folder / "settings.json")
        self.identity = "a" * 32
        self.snapshot = {"format": "docfit-flow", "version": 1, "nodes": [], "edges": []}

    def test_general_mode_storage_is_available_without_enabling_tldraw(self):
        service = FlowService(self.folder, self.store)
        service.save(self.identity, "일반 흐름도", self.snapshot)
        self.assertEqual(service.load(self.identity)["snapshot"], self.snapshot)
        self.assertEqual(service.list()[0]["name"], "일반 흐름도")
        with self.assertRaises(ServiceError):
            DiagramService(self.folder, self.store).list()
        self.assertFalse((self.folder / "diagrams").exists())
        service.delete(self.identity)
        self.assertEqual(service.list(), [])

    def test_native_api_uses_separate_storage_and_validates_format(self):
        app = ApplicationService(self.folder / "settings.json")
        app.dispatch("flow_editor", ["save", {"id": self.identity, "name": "일반", "snapshot": self.snapshot}])
        self.assertEqual(len(app.dispatch("flow_editor", ["list", {}])), 1)
        with self.assertRaises(ServiceError):
            app.dispatch("diagram_list", [])
        with self.assertRaises(ServiceError):
            app.dispatch("flow_editor", ["save", {"id": self.identity, "name": "invalid", "snapshot": {"document": {}}}])
        self.assertEqual(app.dispatch("flow_editor", ["load", {"id": self.identity}])["name"], "일반")

    def test_browser_bridge_routes_general_editor_without_developer_flag(self):
        bridge = DesktopWebBridge.__new__(DesktopWebBridge)
        bridge.gui = SimpleNamespace(_준말_서비스=lambda: SimpleNamespace(settings=self.store))
        bridge._tk = lambda fn: fn()
        bridge.flow_editor("save", {"id": self.identity, "name": "웹 흐름도", "snapshot": self.snapshot})
        self.assertEqual(bridge.flow_editor("load", {"id": self.identity})["name"], "웹 흐름도")
        with self.assertRaises(ServiceError):
            bridge.flow_editor("delete", {"id": "../settings"})
        bridge.flow_editor("delete", {"id": self.identity})

    def test_png_export_uses_validated_data_and_cannot_overwrite_a_document(self):
        import base64
        from unittest.mock import patch
        encoded = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aJ8sAAAAASUVORK5CYII="
        bridge = DesktopWebBridge.__new__(DesktopWebBridge)
        bridge.gui = SimpleNamespace(root=object(), _준말_서비스=lambda: SimpleNamespace(settings=self.store))
        bridge._tk = lambda fn, **kwargs: fn()
        original = self.folder / "original.hwpx"
        original.write_bytes(b"original document")
        with patch("tkinter.filedialog.asksaveasfilename", return_value=str(original)):
            with self.assertRaises(ServiceError):
                bridge.flow_editor("export_png", {"name": "흐름도", "base64": encoded})
        self.assertEqual(original.read_bytes(), b"original document")
        target = self.folder / "result.png"
        with patch("tkinter.filedialog.asksaveasfilename", return_value=str(target)):
            self.assertEqual(bridge.flow_editor("export_png", {"base64": encoded})["path"], str(target))
        self.assertEqual(target.read_bytes(), base64.b64decode(encoded))
        with patch("tkinter.filedialog.asksaveasfilename") as dialog:
            with self.assertRaises(ServiceError):
                bridge.flow_editor("export_png", {"base64": base64.b64encode(b"not PNG").decode()})
            dialog.assert_not_called()
        service = FlowService(self.folder, self.store)
        first = service.export_png(encoded)["path"]
        second = service.export_png(encoded)["path"]
        self.assertNotEqual(first, second)
