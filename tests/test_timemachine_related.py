"""타임머신 연관 문서 검색 코어 시험."""
import sqlite3
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
                self.assertEqual(result["items"][0]["reference_date_basis"], "explicit")
                # 본문의 대상 분기는 기준일 근거로 인정하되 '기간' 근거임을 표시한다.
                self.assertTrue(result["items"][1]["reference_date_found"])
                self.assertEqual(result["items"][1]["reference_date"], "2026-03-31")
                self.assertEqual(result["items"][1]["reference_date_basis"], "period")
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
                                         scanner=lambda *a, **k: None, thumb_dir=Path(temp) / "thumbs", developer_mode=lambda: True)
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

    def test_related_candidates_joins_paragraphs_per_document(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = ContentSearchIndex(root / "content.sqlite")
            try:
                doc_path = str((root / "multi_p.txt").resolve())
                with index._lock, index.db:
                    index.db.execute("INSERT INTO content_meta(path,size,mtime,ctime,reference_date,hierarchy_schema_version) VALUES(?,?,?,?,?,?)",
                                     (doc_path, 10, 1.0, 1.0, "2026-06-30", 1))
                    # 문단 3개 삽입 (순서: 0, 1, 2)
                    for i, text in enumerate(["문단 영", "문단 일", "문단 이"]):
                        index.db.execute(
                            "INSERT INTO content_paragraph_fts(path,name,paragraph_index,level,level_rank,body) VALUES(?,?,?,?,?,?)",
                            (doc_path, "multi_p.txt", i, "body", 8, text)
                        )
                selected, _ = index.related_candidates(doc_path)
                self.assertIsNotNone(selected)
                self.assertEqual(selected["body"], "문단 영\n문단 일\n문단 이")
            finally:
                index.close()

    def test_related_candidate_date_survives_paragraph_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = ContentSearchIndex(root / "content.sqlite")
            try:
                p1 = root / "p1.txt"
                p2 = root / "p2.txt"
                p1.write_text("2026년도 3분기 주요업무추진실적\n작성 기준일: 2026-09-30\n디지털전환 사업", encoding="utf-8")
                p2.write_text("2026년도 2분기 주요업무추진실적\n작성 기준일: 2026-06-30\n디지털전환 사업", encoding="utf-8")
                index.index_file(p1)
                index.index_file(p2)
                selected, candidates = index.related_candidates(str(p1.resolve()))
                self.assertEqual(selected["reference_date"], "2026-09-30")
                self.assertEqual(len(candidates), 1)
                self.assertEqual(candidates[0]["reference_date"], "2026-06-30")
            finally:
                index.close()

    def test_related_excluded_paths_still_apply_to_document_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            index = ContentSearchIndex(root / "content.sqlite")
            try:
                p1 = root / "self.txt"
                p1.write_text("문단 1\n문단 2\n문단 3", encoding="utf-8")
                index.index_file(p1)
                selected, candidates = index.related_candidates(str(p1.resolve()))
                self.assertIsNotNone(selected)
                # 자기 자신 문서는 후보에 없어야 함
                self.assertEqual(candidates, [])
            finally:
                index.close()

    def test_related_legacy_rows_remain_readable_during_reindex(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy_db = root / "legacy.sqlite"
            db = sqlite3.connect(legacy_db)
            db.executescript("""
                CREATE TABLE content_meta(path TEXT PRIMARY KEY,size INTEGER,mtime REAL,reference_date TEXT);
                CREATE VIRTUAL TABLE content_fts USING fts5(path UNINDEXED,name UNINDEXED,body,tokenize='trigram');
            """)
            db.execute("INSERT INTO content_meta VALUES('/tmp/old1.txt',1,1,'2026-01-01')")
            db.execute("INSERT INTO content_fts VALUES('/tmp/old1.txt','old1.txt','구형 본문 내용')")
            db.execute("INSERT INTO content_meta VALUES('/tmp/old2.txt',1,1,'2026-02-01')")
            db.execute("INSERT INTO content_fts VALUES('/tmp/old2.txt','old2.txt','구형 후보 내용')")
            db.commit()
            db.close()

            index = ContentSearchIndex(legacy_db)
            try:
                selected, candidates = index.related_candidates("/tmp/old1.txt")
                self.assertIsNotNone(selected)
                self.assertEqual(selected["body"], "구형 본문 내용")
                self.assertEqual(len(candidates), 1)
                self.assertEqual(candidates[0]["name"], "old2.txt")
            finally:
                index.close()
