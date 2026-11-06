import json
import tempfile
import unittest
from pathlib import Path

from docfit_app.api_contract import ServiceError
from docfit_app.application_service import ApplicationService
from docfit_app.flow_service import FlowService
from docfit_app.settings_service import SettingsService


class FlowDraftTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.store = SettingsService(self.folder / "settings.json")
        self.snapshot = {"format": "docfit-flow", "version": 1,
                         "nodes": [{"id": "n1"}], "edges": []}
        self.identity = "b" * 32

    def service(self):
        return FlowService(self.folder, self.store)

    def test_draft_survives_restart_and_is_not_listed_as_document(self):
        self.service().save_draft("mindmap", None, "새 마인드맵", self.snapshot)
        restarted = self.service()  # 앱 재시작
        draft = restarted.load_draft("mindmap")
        self.assertTrue(draft["exists"])
        self.assertEqual(draft["snapshot"], self.snapshot)
        self.assertEqual(draft["name"], "새 마인드맵")
        self.assertIsNone(draft["id"])
        self.assertEqual(restarted.list(), [])

    def test_modes_are_independent_and_latest_write_wins(self):
        service = self.service()
        service.save_draft("diagram", None, "A", self.snapshot)
        newer = dict(self.snapshot, nodes=[])
        service.save_draft("diagram", self.identity, "A2", newer)
        self.assertEqual(service.load_draft("diagram")["name"], "A2")
        self.assertEqual(service.load_draft("diagram")["id"], self.identity)
        self.assertFalse(service.load_draft("mindmap")["exists"])

    def test_clear_after_normal_save_removes_draft(self):
        service = self.service()
        service.save_draft("diagram", None, "A", self.snapshot)
        service.save(self.identity, "A", self.snapshot)
        service.clear_draft("diagram")
        self.assertFalse(service.load_draft("diagram")["exists"])
        service.clear_draft("diagram")  # 없어도 오류 없음
        self.assertEqual(len(service.list()), 1)

    def test_corrupt_draft_is_discarded_without_crash(self):
        service = self.service()
        service.save_draft("paint", None, "A", self.snapshot)
        path = self.folder / "flows" / "recovery" / "paint.draft.json"
        path.write_text("{broken", encoding="utf-8")
        result = service.load_draft("paint")
        self.assertFalse(result["exists"])
        self.assertFalse(path.exists())

    def test_invalid_input_rejected(self):
        service = self.service()
        for args in (("../x", None, "A", self.snapshot), ("diagram", "bad id", "A", self.snapshot),
                     ("diagram", None, "", self.snapshot), ("diagram", None, "A", {"format": "x"}),
                     ("diagram", None, "A", dict(self.snapshot, nodes="no"))):
            with self.subTest(args=args), self.assertRaises(ServiceError):
                service.save_draft(*args)
        self.assertFalse((self.folder / "flows" / "recovery").exists())

    def test_no_temp_files_left_and_json_valid(self):
        service = self.service()
        for i in range(3):
            service.save_draft("diagram", None, f"A{i}", self.snapshot)
        files = sorted(p.name for p in (self.folder / "flows" / "recovery").iterdir())
        self.assertEqual(files, ["diagram.draft.json"])
        json.loads((self.folder / "flows" / "recovery" / "diagram.draft.json").read_text(encoding="utf-8"))

    def test_native_dispatch_roundtrip(self):
        app = ApplicationService(self.folder / "settings.json")
        app.dispatch("flow_editor", ["save_draft", {"mode": "diagram", "id": None, "name": "A", "snapshot": self.snapshot}])
        got = app.dispatch("flow_editor", ["load_draft", {"mode": "diagram"}])
        self.assertTrue(got["exists"])
        app.dispatch("flow_editor", ["clear_draft", {"mode": "diagram"}])
        self.assertFalse(app.dispatch("flow_editor", ["load_draft", {"mode": "diagram"}])["exists"])


if __name__ == "__main__":
    unittest.main()
