"""타임머신 연관 문서 검색 코어 시험."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from docfit_app.timemachine_service import TimemachineService
from docfit_core.timemachine.content_search import ContentSearchIndex, extract_reference_date
from docfit_core.timemachine.related import related_documents
from docfit_core.timemachine.store import Store


class TimemachineRelatedTests(unittest.TestCase):
    def test_extract_reference_date_supports_explicit_and_period_forms(self):
        self.assertEqual(extract_reference_date("작성 기준일: 2026. 3. 31."), "2026-03-31")
        self.assertEqual(extract_reference_date("2026년도 2분기 주요업무"), "2026-06-01")
        self.assertEqual(extract_reference_date("기준일 없음"), None)

    def test_related_search_scores_evidence_sorts_by_reference_date_and_flags_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = ContentSearchIndex(root / "content.sqlite")
            try:
                docs = {
                    "선택.txt": "2026년도 3분기 주요업무추진실적\n작성 기준일: 2026. 9. 30.\n디지털전환 사업",
                    "이전.txt": "2026년도 2분기 주요업무추진실적\n작성 기준일: 2026. 6. 30.\n디지털전환 사업",
                    "기준일없음.txt": "2026년도 1분기 주요업무추진실적\n디지털전환 사업",
                    "무관.txt": "요리법과 여행 기록",
                }
                for name, body in docs.items():
                    path = root / name
                    path.write_text(body, encoding="utf-8")
                    self.assertTrue(index.index_file(path)["indexed"])
                selected = str(root / "선택.txt")
                result = related_documents(index, selected, roots=[str(root)])
                self.assertEqual(result["reference_date"], "2026-09-30")
                names = [item["name"] for item in result["items"]]
                self.assertEqual(names, ["이전.txt", "기준일없음.txt"])
                self.assertTrue(result["items"][0]["reference_date_found"])
                self.assertFalse(result["items"][1]["reference_date_found"])
                self.assertIn("period_pattern", {reason["type"] for reason in result["items"][0]["reasons"]})
                self.assertGreater(result["items"][0]["score"], 0)
            finally:
                index.close()

    def test_store_persists_and_removes_excluded_pairs(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "timeline.db"
            store = Store(db)
            store.exclude_related("/tmp/a.txt", "/tmp/b.txt")
            store.close()
            store = Store(db)
            try:
                self.assertEqual(len(store.related_exclusions()), 1)
                store.exclude_related("/tmp/b.txt", "/tmp/a.txt", False)
                self.assertEqual(store.related_exclusions(), [])
            finally:
                store.close()

    def test_service_related_commands_hide_paths_and_persist_exclusion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "docs"
            root.mkdir()
            settings = Path(temp) / "settings"
            service = TimemachineService(settings, db_path=Path(temp) / "timeline.db",
                                         scanner=lambda *a, **k: None, thumb_dir=Path(temp) / "thumbs")
            try:
                service._settings.update(roots=[str(root)], enabled=True)
                a, b = root / "A.txt", root / "B.txt"
                a.write_text("2026년도 3분기 주요업무추진실적\n작성 기준일: 2026-09-30\n디지털전환 사업", encoding="utf-8")
                b.write_text("2026년도 2분기 주요업무추진실적\n작성 기준일: 2026-06-30\n디지털전환 사업", encoding="utf-8")
                service.content_index.index_file(a)
                service.content_index.index_file(b)
                response = service.command("related_search", {"path": str(a)})
                self.assertTrue(response["ok"])
                self.assertEqual(response["items"][0]["name"], "B.txt")
                self.assertNotIn("path", response["items"][0])
                saved = service.command("related_exclude", {"selected_path": str(a), "related_path": str(b)})
                self.assertTrue(saved["ok"])
                self.assertEqual(service.command("related_search", {"path": str(a)})["items"], [])
            finally:
                service.close()
