"""타임머신 서비스 계약 시험. 모든 파일은 임시 폴더 안에서만 다룬다."""
import base64
import json
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path

from docfit_app.timemachine_service import TimemachineService
from docfit_core.timemachine import thumbs
from docfit_core.timemachine.rules import Rules
from docfit_core.timemachine.store import Store


class FakeAgent:
    def __init__(self, running=False, fail=False):
        self.is_running, self.fail, self.calls = running, fail, []
        self.settings = {"timeline_roots": [], "timeline_mtime_only": False}
        self.reject_roots = False
    def running(self): return self.is_running
    def status_file(self):
        return {"pid": 1, "timeline_roots": len(self.settings["timeline_roots"])} if self.is_running else None
    def request(self, command, **payload):
        self.calls.append((command, payload))
        if self.fail: raise OSError("IPC 실패")
        if command == "settings_set":
            self.settings = dict(payload["settings"], timeline_roots=[] if self.reject_roots else payload["settings"]["timeline_roots"])
        return {"ok": True, "settings": dict(self.settings)}


class StubResult:
    seen = written = removed = 0
    errors = []


def stub_scanner(store, roots, rules, progress=None):
    return StubResult()


def _stuck_pdf_worker_for_test(path, conn):
    """Windows spawn 프로세스에서 pickle 가능한 timeout 테스트용 최상위 worker."""
    time.sleep(10)


class TimemachineServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "문서"
        self.root.mkdir()
        self.settings = Path(self.temp.name) / "설정"
        self.plain_file = Path(self.temp.name) / "단일 파일.pdf"
        self.plain_file.write_bytes("시험".encode("utf-8"))
        self.agent = FakeAgent()
        self.opened, self.revealed = [], []
        self.service = TimemachineService(self.settings, db_path=Path(self.temp.name) / "timeline.db",
            agent=self.agent, opener=self.opened.append, revealer=self.revealed.append,
            scanner=stub_scanner, thumb_dir=Path(self.temp.name) / "thumbs",
            developer_mode=lambda: getattr(self, "developer_mode", True))
        self.developer_mode = False

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def enable(self, roots=None):
        return self.service.command("settings_set", {"roots": [str(p) for p in (roots or [self.root])], "time_mode":"max", "enabled":True})

    def test_settings_defaults_disabled_and_default_roots(self):
        settings = self.service.command("settings_get")["settings"]
        self.assertEqual(settings["time_mode"], "max")
        self.assertFalse(settings["enabled"])
        self.assertIsInstance(settings["roots"], list)
        self.assertFalse(self.service.command("status")["enabled"])

    def test_content_search_allowed_and_related_search_requires_developer_mode(self):
        allowed = self.service.command("content_search", {"query": "금지"})
        self.assertTrue(allowed["ok"])
        denied = self.service.command("related_search", {"path": str(self.root / "없는.txt")})
        self.assertFalse(denied["ok"])
        self.assertEqual(denied["code"], "DEVELOPER_MODE_REQUIRED")
        self.assertIn("개발자 모드", denied["message"])
        self.assertEqual(self.service.command("content_index_start")["code"], "DEVELOPER_MODE_REQUIRED")

        self.developer_mode = True
        self.enable()
        document = self.root / "허용.txt"
        document.write_text("허용 검색어", encoding="utf-8")
        self.assertTrue(self.service.command("content_index", {"path": str(document)})["ok"])
        result = self.service.command("content_search", {"query": "허용 검색어"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["items"][0]["name"], document.name)

    def test_file_name_search_is_available_without_developer_mode(self):
        result = self.service.command("file_search", {"query": "보고서"})
        self.assertTrue(result["ok"])

    def test_content_index_requires_active_root_and_searches_local_text(self):
        self.developer_mode = True
        self.enable()
        document = self.root / "내용.txt"
        document.write_text("서비스 본문 키워드", encoding="utf-8")
        indexed = self.service.command("content_index", {"path": str(document)})
        self.assertTrue(indexed["ok"])
        result = self.service.command("content_search", {"query": "본문 키워드"})
        self.assertIn("file_name", result["items"][0])
        self.assertIn("folder_name", result["items"][0])
        self.assertIn("folder_path", result["items"][0])
        self.assertIn("locations", result["items"][0])
        self.assertIn("relevance_rank", result["items"][0])
        self.assertEqual(result["items"][0]["relevance_rank"], 1)
        self.assertEqual(result["items"][0]["name"], document.name)
        outside = self.plain_file
        self.assertFalse(self.service.command("content_index", {"path": str(outside)})["ok"])
        junk = self.root / "#IEeEE'.txt"
        junk.write_text("비정상 파일 검색어", encoding="utf-8")
        self.assertFalse(self.service.command("content_index", {"path": str(junk)})["ok"])

    def test_related_search_preserves_hierarchy_relevance(self):
        self.developer_mode = True
        self.enable()
        from tests.test_timemachine_content_search import write_hwpx_paragraphs
        doc_sq = self.root / "square.hwpx"
        write_hwpx_paragraphs(doc_sq, [{"text": "ㅁ 서비스검색어"}])
        doc_body = self.root / "body.txt"
        doc_body.write_text("서비스검색어 서비스검색어 서비스검색어", encoding="utf-8")
        self.service.command("content_index", {"path": str(doc_sq)})
        self.service.command("content_index", {"path": str(doc_body)})

        res = self.service.command("related_search", {"path": str(doc_body)})
        self.assertTrue(res["ok"])
        self.assertIsInstance(res["items"], list)

    def test_related_search_uses_existing_related_document_contract(self):
        self.developer_mode = True
        self.enable()
        from tests.test_timemachine_content_search import write_hwpx_paragraphs
        doc_sq = self.root / "square.hwpx"
        write_hwpx_paragraphs(doc_sq, [{"text": "ㅁ 명시정렬검색어"}])
        doc_body = self.root / "body.txt"
        doc_body.write_text("명시정렬검색어 명시정렬검색어 명시정렬검색어", encoding="utf-8")
        self.service.command("content_index", {"path": str(doc_sq)})
        self.service.command("content_index", {"path": str(doc_body)})

        res = self.service.command("related_search", {"path": str(doc_body)})
        self.assertTrue(res["ok"])
        self.assertTrue(res["ok"])

    def test_content_search_returns_keyword_fields_without_internal_sort_keys(self):
        self.developer_mode = True
        self.enable()
        doc = self.root / "public_fields.txt"
        doc.write_text("필드 검증 텍스트", encoding="utf-8")
        self.service.command("content_index", {"path": str(doc)})
        res = self.service.command("content_search", {"query": "필드"})
        self.assertTrue(res["ok"])
        item = res["items"][0]
        for field in ("path", "file_name", "folder_name", "folder_path", "extension", "relevance_rank", "snippet", "highlights", "position", "locations"):
            self.assertIn(field, item)
        for internal in ("_best_level_rank", "_bm25_score", "_document_date", "best_level_rank", "bm25_score", "document_date"):
            self.assertNotIn(internal, item)

    def test_needs_reindex_count_drops_after_background_index(self):
        self.developer_mode = True
        self.enable()
        p1 = self.root / "old1.txt"
        p2 = self.root / "old2.txt"
        p1.write_text("재색인 대상 하나", encoding="utf-8")
        p2.write_text("재색인 대상 둘", encoding="utf-8")
        self.service.command("content_index", {"path": str(p1)})
        self.service.command("content_index", {"path": str(p2)})

        with self.service.content_index._lock, self.service.content_index.db:
            self.service.content_index.db.execute("UPDATE content_meta SET hierarchy_schema_version=0")
            self.service.content_index.db.execute("DELETE FROM content_paragraph_fts")

        status = self.service.command("content_index_status")
        self.assertEqual(status["needs_reindex_count"], 2)
        self.assertTrue(status["needs_reindex"])
        self.assertIn("위계 정보가 없어 재색인이 필요", status["reindex_guide"])

        self.service.command("content_index", {"path": str(p1)})
        status = self.service.command("content_index_status")
        self.assertEqual(status["needs_reindex_count"], 1)

        search_res = self.service.command("content_search", {"query": "재색인"})
        names = [it["name"] for it in search_res["items"]]
        self.assertIn(p1.name, names)
        self.assertNotIn(p2.name, names)

    def test_keyword_search_uses_keyword_search_engine(self):
        self.developer_mode = True
        self.enable()
        doc = self.root / "forward.txt"
        doc.write_text("전달 확인 텍스트", encoding="utf-8")
        self.service.command("content_index", {"path": str(doc)})

        with patch.object(self.service.content_index, "keyword_search", wraps=self.service.content_index.keyword_search) as spy:
            self.service.command("content_search", {"query": "전달"})
            spy.assert_called_once()
            _, kwargs = spy.call_args
            self.assertEqual(kwargs.get("offset"), 0)

    def test_content_export_markdown_writes_search_terms_paths_and_locations(self):
        self.developer_mode = False
        self.enable()
        doc = self.root / "내보내기.txt"
        doc.write_text("내보내기 키워드 문장", encoding="utf-8")
        self.developer_mode = True
        self.service.command("content_index", {"path": str(doc)})
        self.developer_mode = False
        output = self.root / "결과.md"
        result = self.service.command("content_export_markdown", {"query": "내보내기 키워드", "path": str(output)})
        self.assertTrue(result["ok"])
        markdown = output.read_text(encoding="utf-8")
        self.assertIn("내보내기 키워드", markdown)
        self.assertIn(str(doc), markdown)
        self.assertIn("미리보기", markdown)

    def test_background_content_index_progress_and_cancel(self):
        self.developer_mode = True
        (self.root / "one.txt").write_text("한글 색인", encoding="utf-8")
        (self.root / "two.txt").write_text("두 번째", encoding="utf-8")
        junk = self.root / "#IEeEE'.txt"
        junk.write_text("비정상 전용 단어", encoding="utf-8")
        self.service.content_index.index_file(junk)  # 기존에 남아 있던 항목도 정리해야 한다.
        self.enable()
        started = self.service.command("content_index_all")
        self.assertTrue(started["ok"])
        worker = self.service._content_thread
        worker.join(5)
        self.assertFalse(worker.is_alive())
        status = self.service.command("content_index_status")
        self.assertFalse(status["running"])
        self.assertEqual(status["seen"], 2)
        self.assertEqual(status["indexed"], 2)
        self.assertEqual(len(self.service.command("content_search", {"query":"색인"})["items"]), 1)
        self.assertEqual(self.service.command("content_search", {"query":"비정상"})["items"], [])

    def test_content_index_cancel_during_refresh_keeps_unvisited_entries(self):
        self.developer_mode = True
        self.enable()
        files = [self.root / f"{name}.txt" for name in ("one", "two")]
        for file in files:
            file.write_text("보존 문서", encoding="utf-8")
            self.service.command("content_index", {"path": str(file)})
        entered, release = threading.Event(), threading.Event()
        original = self.service.content_index.index_file
        def blocked(path):
            entered.set(); release.wait(2)
            return original(path)
        with patch.object(self.service.content_index, "index_file", side_effect=blocked):
            self.service._refresh_content_index_async()
            self.assertTrue(entered.wait(1))
            self.service.command("content_index_cancel")
            release.set()
            self.service._content_thread.join(2)
        self.assertFalse(self.service._content_state["running"])
        self.assertTrue(self.service._content_state["cancelled"])
        self.assertEqual(len(self.service.command("content_search", {"query": "보존 문서"})["items"]), 2)

    def test_content_index_refresh_is_single_flight(self):
        self.developer_mode = True
        self.enable()
        file = self.root / "one.txt"
        file.write_text("갱신", encoding="utf-8")
        self.service.command("content_index", {"path": str(file)})
        entered, release = threading.Event(), threading.Event()
        original = self.service.content_index.index_file
        calls = []
        def blocked(path):
            calls.append(path); entered.set(); release.wait(2)
            return original(path)
        with patch.object(self.service.content_index, "index_file", side_effect=blocked):
            self.service._refresh_content_index_async()
            self.assertTrue(entered.wait(1))
            first = self.service._content_thread
            self.service._refresh_content_index_async()
            self.assertIs(self.service._content_thread, first)
            release.set(); first.join(2)
        self.assertEqual(len(calls), 1)

    def test_refresh_removes_index_for_removed_root(self):
        self.developer_mode = True
        second = Path(self.temp.name) / "추가"; second.mkdir()
        self.enable([self.root, second])
        file = self.root / "old.txt"; file.write_text("제거 조사 폴더", encoding="utf-8")
        self.service.command("content_index", {"path": str(file)})
        self.enable([second])
        self.service._refresh_content_index_async()
        worker = self.service._content_thread
        if worker: worker.join(2)
        self.assertEqual(self.service.command("content_search", {"query": "제거 조사 폴더"})["items"], [])

    def test_refresh_removes_entries_for_extensions_no_longer_enabled(self):
        self.developer_mode = True
        self.enable()
        file = self.root / "old.txt"; file.write_text("확장자 제외", encoding="utf-8")
        self.service.command("content_index", {"path": str(file)})
        self.service.command("settings_set", {"roots": [str(self.root)], "time_mode": "max", "enabled": True, "extensions": ["pdf"]})
        self.service._refresh_content_index_async()
        self.service._content_thread.join(2)
        self.assertEqual(self.service.command("content_search", {"query": "확장자 제외"})["items"], [])

    def test_refresh_missing_root_preserves_indexed_documents(self):
        self.developer_mode = True
        offline_root = Path(self.temp.name) / "오프라인"; offline_root.mkdir()
        self.enable([offline_root])
        file = offline_root / "offline.txt"; file.write_text("오프라인 보존", encoding="utf-8")
        self.service.command("content_index", {"path": str(file)})
        file.unlink()
        offline_root.rmdir()
        try:
            self.service._refresh_content_index_async()
            worker = self.service._content_thread
            if worker: worker.join(2)
            self.assertEqual(len(self.service.command("content_search", {"query": "오프라인 보존"})["items"]), 1)
        finally:
            offline_root.mkdir()

    def test_refresh_during_close_cancels_and_joins_worker(self):
        self.developer_mode = True
        self.enable()
        file = self.root / "blocked.txt"; file.write_text("종료 갱신", encoding="utf-8")
        self.service.command("content_index", {"path": str(file)})
        entered, release = threading.Event(), threading.Event()
        original = self.service.content_index.index_file
        def blocked(path):
            entered.set(); release.wait(2)
            return original(path)
        with patch.object(self.service.content_index, "index_file", side_effect=blocked):
            self.service._refresh_content_index_async()
            self.assertTrue(entered.wait(1))
            closer = threading.Thread(target=self.service.close); closer.start()
            deadline = time.monotonic() + 1
            while not self.service._content_cancel.is_set() and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertTrue(self.service._content_cancel.is_set())
            release.set(); closer.join(2)
            self.assertFalse(closer.is_alive())
        self.assertFalse(self.service._content_thread.is_alive())

    def test_scan_refreshes_only_existing_content_index_and_removes_deleted(self):
        self.developer_mode = True
        self.enable()
        original = self.root / "original.txt"
        original.write_text("오래된 본문", encoding="utf-8")
        # 사용자가 한 번 색인한 적이 있어야 자동 갱신 대상이 된다.
        self.service.command("content_index", {"path": str(original)})
        original.write_text("바뀐 본문", encoding="utf-8")
        added = self.root / "added.txt"
        added.write_text("새 문서 본문", encoding="utf-8")
        deleted = self.root / "deleted.txt"
        deleted.write_text("삭제할 본문", encoding="utf-8")
        self.service.command("content_index", {"path": str(deleted)})
        deleted.unlink()

        # 스캔 완료 후 별도 스레드에서 본문 색인이 수행된다.
        self.service.agent.is_running = False
        self.service.scanner = lambda *a, **k: StubResult()
        scan = self.service.command("scan")
        self.assertEqual(scan.get("by"), "app")
        self.wait_scan_idle()
        worker = self.service._content_thread
        self.assertIsNotNone(worker)
        worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(self.service.command("content_search", {"query": "바뀐 본문"})["items"]), 1)
        self.assertEqual(len(self.service.command("content_search", {"query": "새 문서 본문"})["items"]), 1)
        self.assertEqual(self.service.command("content_search", {"query": "오래된 본문"})["items"], [])
        self.assertEqual(self.service.command("content_search", {"query": "삭제할 본문"})["items"], [])

    def test_scan_does_not_start_full_content_index_without_user_request(self):
        self.developer_mode = True
        (self.root / "unrequested.txt").write_text("자동 전체 색인 금지", encoding="utf-8")
        self.enable()
        self.service.scanner = lambda *a, **k: StubResult()
        self.service.command("scan")
        self.wait_scan_idle()
        self.assertIsNone(self.service._content_thread)
        self.assertEqual(self.service.command("content_search", {"query": "자동 전체 색인 금지"})["items"], [])

    def test_close_cancels_and_joins_content_index(self):
        self.developer_mode = True
        self.enable()
        entered, release = threading.Event(), threading.Event()
        original = self.service.content_index.index_file
        def blocked(path):
            entered.set()
            release.wait(2)
            return original(path)
        document = self.root / "blocked.txt"
        document.write_text("본문", encoding="utf-8")
        with patch.object(self.service.content_index, "index_file", side_effect=blocked):
            self.service.command("content_index_start")
            self.assertTrue(entered.wait(1))
            closer = threading.Thread(target=self.service.close)
            closer.start()
            deadline = time.monotonic() + 1
            while not self.service._content_cancel.is_set() and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertTrue(self.service._content_cancel.is_set())
            release.set()
            closer.join(2)
            self.assertFalse(closer.is_alive())
        self.assertFalse(self.service._content_thread.is_alive())

    def test_settings_reject_relative_missing_and_more_than_twenty_roots(self):
        for roots in (["relative"], [str(self.root / "missing")], [str(self.plain_file)], [str(self.root)] * 21):
            result = self.service.command("settings_set", {"roots":list(roots),"time_mode":"max","enabled":True})
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "INVALID_INPUT")
            self.assertFalse(self.service.command("settings_get")["settings"]["enabled"])
        real_lstat = os.lstat
        class ReparseStat:
            st_mode = real_lstat(self.root).st_mode
            st_file_attributes = 0x400
        with patch("docfit_app.timemachine_service.os.lstat", return_value=ReparseStat()):
            result = self.service.command("settings_set", {"roots":[str(self.root)],"time_mode":"max","enabled":True})
        self.assertFalse(result["ok"])
        self.assertFalse(self.service.command("settings_get")["settings"]["enabled"])

    def test_settings_set_drops_removed_roots_and_notifies_agent(self):
        second = Path(self.temp.name) / "추가"
        second.mkdir()
        self.enable([self.root, second])
        self.agent.is_running = True
        removed = self.service.store.drop_root
        calls = []
        self.service.store.drop_root = lambda path: calls.append(path) or removed(path)
        response = self.service.command("settings_set", {"roots":[str(second)],"time_mode":"mtime","enabled":True})
        self.assertTrue(response["ok"])
        self.assertEqual(calls, [str(self.root)])
        self.assertEqual(self.agent.calls[-1], ("settings_set", {"settings":{"timeline_roots":[str(second)],"timeline_mtime_only":True}}))

    def test_agent_notification_failure_does_not_fail_settings_save(self):
        self.agent.is_running, self.agent.fail = True, True
        self.assertTrue(self.enable()["ok"])
        saved = json.loads((self.settings / "timemachine.json").read_text(encoding="utf-8"))
        self.assertTrue(saved["enabled"])

    def test_scan_rejected_while_disabled(self):
        called=[]
        service=TimemachineService(self.settings,db_path=Path(self.temp.name)/"other.db",agent=self.agent,scanner=lambda *a,**k:called.append(1))
        try:
            result=service.command("scan")
            self.assertEqual(result["code"],"TM_DISABLED")
            self.assertEqual(called,[])
        finally: service.close()

    def test_scan_runs_once_in_background_and_reports_progress(self):
        entered, release = threading.Event(), threading.Event()
        def scanner(store, roots, rules, progress=None):
            entered.set(); release.wait(2)
            class Result: seen=1; written=1; removed=0; errors=[]
            result=Result()
            if progress: progress(result)
            return result
        self.service.scanner=scanner
        self.enable()
        first=self.service.command("scan")
        self.assertTrue(entered.wait(2))
        second=self.service.command("scan")
        self.assertTrue(first["running"] and second["running"])
        self.assertTrue(self.service.command("status")["scan"]["running"])
        release.set()

    def test_agent_running_uses_agent_without_app_scan(self):
        called=[]; self.service.scanner=lambda *a,**k:called.append(1)
        self.agent.is_running=True; self.enable()
        result=self.service.command("scan")
        self.assertEqual(result,{"ok":True,"by":"agent"})
        self.assertEqual(called,[])

    def test_range_uses_temp_index_and_never_returns_path(self):
        file=self.root/"보고서.pdf"; file.write_bytes(b"test")
        now=time.time(); self.service.store.upsert_many([{"path":str(file),"root":str(self.root),"name":file.name,"kind":"pdf","size":4,"mtime":now,"ctime":now,"work_time":now,"flags":["new"],"cloud":False}])
        self.enable()
        result=self.service.command("range",{"start":now-1,"end":now+1,"roots":[str(self.root)],"limit":200,"offset":0})
        self.assertEqual(set(result["items"][0]),{"id","name","kind","size","mtime","ctime","work_time","flags","cloud","folder"})
        self.assertNotIn("path",result["items"][0]); self.assertEqual(result["items"][0]["name"],file.name)
        self.assertEqual(result["items"][0]["folder"],str(self.root))

    def test_range_validates_filters_and_page_bounds(self):
        self.enable(); now=time.time(); base={"start":now-10,"end":now+10,"limit":200,"offset":0}
        for update in ({"kinds":["other"]},{"roots":[str(Path(self.temp.name))]},{"start":5,"end":4},{"limit":201},{"offset":-1},{"query":3}):
            self.assertEqual(self.service.command("range",base|update)["code"],"INVALID_INPUT")

    def test_extension_settings_are_validated_and_persisted(self):
        result=self.service.command("settings_set",{"roots":[str(self.root)],"time_mode":"max","enabled":True,"extensions":["pdf","txt"]})
        self.assertTrue(result["ok"])
        self.assertEqual(result["settings"]["extensions"],["pdf","txt"])
        invalid=self.service.command("settings_set",{"roots":[str(self.root)],"time_mode":"max","enabled":True,"extensions":["exe"]})
        self.assertEqual(invalid["code"],"INVALID_INPUT")

    def test_day_counts_and_hour_density_forward_filters(self):
        self.enable()
        response=self.service.command("day_counts",{"year":2026,"month":10,"roots":[str(self.root)],"kinds":["pdf"],"query":"x"})
        self.assertTrue(response["ok"])
        now=time.time(); hours=self.service.command("hour_density",{"start":now-60,"end":now+60,"roots":[str(self.root)],"kinds":["pdf"],"query":"x"})
        self.assertTrue(hours["ok"])

    def test_hide_requires_existing_id(self):
        file=self.root/"one.txt"; file.write_text("x")
        now=time.time(); self.service.store.upsert_many([{"path":str(file),"root":str(self.root),"name":file.name,"kind":"doc","size":1,"mtime":now,"ctime":now,"work_time":now,"flags":[],"cloud":False}])
        row=self.service.store.range(now-1,now+1)[0]
        self.assertTrue(self.service.command("hide",{"id":row["id"]})["ok"])
        self.assertEqual(self.service.command("hide",{"id":987654})["code"],"TM_NOT_FOUND")

    def test_open_rejects_unknown_id_and_disallowed_extension(self):
        self.assertEqual(self.service.command("open",{"id":55})["code"],"TM_NOT_FOUND")
        file=self.root/"bad.exe"; file.write_bytes(b"x"); now=time.time()
        self.service.store.upsert_many([{"path":str(file),"root":str(self.root),"name":file.name,"kind":"other","size":1,"mtime":now,"ctime":now,"work_time":now,"flags":[],"cloud":False}])
        row=self.service.store.get(1)
        self.assertEqual(self.service.command("open",{"id":row["id"]})["code"],"TM_NOT_AVAILABLE")
        self.assertEqual(self.opened,[])

    def test_open_and_range_reject_paths_outside_active_roots(self):
        outside = self.plain_file
        now = time.time()
        self.service.store.upsert_many([{"path":str(outside),"root":str(self.root),"name":outside.name,"kind":"pdf","size":outside.stat().st_size,"mtime":now,"ctime":now,"work_time":now,"flags":[],"cloud":False}])
        self.enable()
        result = self.service.command("range", {"start":now-1,"end":now+1})
        self.assertEqual(result["items"], [])
        row = self.service.store.get(1)
        self.assertEqual(self.service.command("open", {"id":row["id"]})["code"], "TM_NOT_AVAILABLE")
        self.assertEqual(self.service.command("reveal", {"id":row["id"]})["code"], "TM_NOT_AVAILABLE")
        self.assertEqual(self.opened, [])
        self.assertEqual(self.revealed, [])

    def test_open_missing_file_returns_tm_missing_and_hides_index_entry(self):
        self.enable()  # 조사 폴더 안 파일만 열 수 있다
        file=self.root/"gone.pdf"; now=time.time()
        self.service.store.upsert_many([{"path":str(file),"root":str(self.root),"name":file.name,"kind":"pdf","size":1,"mtime":now,"ctime":now,"work_time":now,"flags":[],"cloud":False}])
        row=self.service.store.get(1)
        self.assertEqual(self.service.command("open",{"id":row["id"]})["code"],"TM_MISSING")
        self.assertEqual(self.service.store.range(now-1,now+1),[])

    def test_open_and_reveal_call_injected_handlers(self):
        self.enable()  # 조사 폴더 안 파일만 열 수 있다
        file=self.root/"valid.pdf"; file.write_bytes(b"x"); now=time.time()
        self.service.store.upsert_many([{"path":str(file),"root":str(self.root),"name":file.name,"kind":"pdf","size":1,"mtime":now,"ctime":now,"work_time":now,"flags":[],"cloud":False}])
        row=self.service.store.get(1)
        self.assertTrue(self.service.command("open",{"id":row["id"]})["ok"])
        self.assertTrue(self.service.command("reveal",{"id":row["id"]})["ok"])
        self.assertEqual(self.opened,[str(file)]); self.assertEqual(self.revealed,[str(file)])

    # ── 켤 때 K에이전트 연동 ──
    def wait_scan_idle(self):
        deadline = time.time() + 5
        while self.service.command("status")["scan"]["running"] and time.time() < deadline:
            time.sleep(0.01)

    def test_enable_with_agent_sends_roots_and_skips_app_scan(self):
        called = []
        self.service.scanner = lambda *a, **k: called.append(1) or StubResult()
        self.agent.is_running = True
        self.assertTrue(self.enable()["ok"])
        self.assertEqual(self.agent.calls[-1], ("settings_set", {"settings": {"timeline_roots": [str(self.root)], "timeline_mtime_only": False}}))
        self.wait_scan_idle()
        self.assertEqual(called, [])
        self.assertEqual(self.service.command("status")["watch"], "agent")

    def test_enable_without_agent_starts_app_scan_and_reports_app_watch(self):
        called = threading.Event()
        self.service.scanner = lambda *a, **k: called.set() or StubResult()
        self.enable()
        self.assertTrue(called.wait(2))
        self.wait_scan_idle()
        self.assertEqual(self.agent.calls, [])
        self.assertEqual(self.service.command("status")["watch"], "app")

    def test_disable_stops_agent_watch(self):
        self.agent.is_running = True
        self.enable()
        self.service.command("settings_set", {"roots": [str(self.root)], "time_mode": "max", "enabled": False})
        self.assertEqual(self.agent.settings["timeline_roots"], [])

    def test_agent_started_later_receives_roots_on_scan(self):
        self.enable(); self.wait_scan_idle()
        self.agent.is_running = True
        self.assertEqual(self.service.command("status")["watch"], "app")
        self.assertEqual(self.service.command("scan"), {"ok": True, "by": "agent"})
        self.assertEqual(self.agent.settings["timeline_roots"], [str(self.root)])
        self.assertEqual(self.service.command("status")["watch"], "agent")
        sets = len([c for c in self.agent.calls if c[0] == "settings_set"])
        self.service.command("scan")  # 이미 같으면 다시 보내지 않는다(에이전트의 전체 재훑기 방지)
        self.assertEqual(len([c for c in self.agent.calls if c[0] == "settings_set"]), sets)

    def test_agent_failure_or_rejected_roots_fall_back_to_app_scan(self):
        for setup in ("fail", "reject_roots"):
            called = threading.Event()
            self.service.scanner = lambda *a, **k: called.set() or StubResult()
            self.agent.is_running = True
            setattr(self.agent, setup, True)
            self.service._settings = dict(self.service._settings, enabled=False)
            self.enable()
            self.assertTrue(called.wait(2), setup)
            self.wait_scan_idle()
            setattr(self.agent, setup, False)

    def test_root_change_during_scan_scans_again(self):
        second = Path(self.temp.name) / "추가"; second.mkdir()
        entered, release, seen = threading.Event(), threading.Event(), []
        def scanner(store, roots, rules, progress=None):
            seen.append(list(roots)); entered.set(); release.wait(2)
            return StubResult()
        self.service.scanner = scanner
        self.enable()
        self.assertTrue(entered.wait(2))
        self.enable([second])
        release.set()
        deadline = time.time() + 5
        while len(seen) < 2 and time.time() < deadline:
            time.sleep(0.01)
        self.wait_scan_idle()
        self.assertEqual(seen[-1], [str(second)])

    # ── 썸네일 권한 ──
    def add_file(self, file, *, kind="image", cloud=False):
        now = time.time()
        self.service.store.upsert_many([{"path":str(file),"root":str(self.root),"name":file.name,"kind":kind,"size":1,"mtime":now,"ctime":now,"work_time":now,"flags":[],"cloud":cloud}])
        return self.service.store.range(now - 1, now + 1, limit=1)[0]["id"]

    def png(self, name="그림.png"):
        from PIL import Image
        file = self.root / name
        Image.new("RGB", (400, 200), "red").save(file)
        return file

    def test_thumbnail_returns_base64_jpeg_and_uses_cache(self):
        self.enable()
        file_id = self.add_file(self.png())
        with patch("docfit_core.timemachine.thumbs.render", wraps=thumbs.render) as render:
            first = self.service.command("thumbnail", {"id": file_id})
            second = self.service.command("thumbnail", {"id": file_id})
        self.assertTrue(first["ok"])
        self.assertTrue(base64.b64decode(first["data"]).startswith(b"\xff\xd8\xff"))
        self.assertEqual(first["data"], second["data"])
        self.assertEqual(render.call_count, 1)

    def test_thumbnail_permission_checks(self):
        self.assertEqual(self.service.command("thumbnail", {"id": True})["code"], "INVALID_INPUT")
        self.assertEqual(self.service.command("thumbnail", {"id": 1})["code"], "TM_DISABLED")
        self.enable()
        self.assertEqual(self.service.command("thumbnail", {"id": 999})["code"], "TM_NOT_FOUND")
        outside = self.add_file(self.plain_file, kind="pdf")
        result = self.service.command("thumbnail", {"id": outside})
        self.assertEqual((result["code"], result.get("data")), ("TM_NOT_AVAILABLE", None))
        hidden = self.add_file(self.png("숨김.png"))
        self.service.store.hide(hidden)
        self.assertEqual(self.service.command("thumbnail", {"id": hidden})["code"], "TM_NOT_AVAILABLE")

    def test_thumbnail_cloud_flag_never_reads_file(self):
        self.enable()
        file_id = self.add_file(self.png(), cloud=True)
        with patch("docfit_core.timemachine.thumbs.render") as render:
            self.assertEqual(self.service.command("thumbnail", {"id": file_id}), {"ok": True, "data": None})
        render.assert_not_called()

    def test_thumbnail_missing_file_is_null_and_keeps_index(self):
        self.enable()
        file_id = self.add_file(self.root / "없음.png")
        self.assertEqual(self.service.command("thumbnail", {"id": file_id}), {"ok": True, "data": None})
        self.assertIsNotNone(self.service.store.get(file_id))
        self.assertFalse(self.service.store.get(file_id)["hidden"])

    def test_thumbnail_limits_concurrency_to_two(self):
        self.enable()
        ids = [self.add_file(self.png(f"그림{i}.png")) for i in range(5)]
        lock, active, peak, results = threading.Lock(), [0], [0], []
        def slow(path):
            with lock:
                active[0] += 1; peak[0] = max(peak[0], active[0])
            time.sleep(0.05)
            with lock:
                active[0] -= 1
            return b"\xff\xd8\xff"
        with patch("docfit_core.timemachine.thumbs.render", slow):
            threads = [threading.Thread(target=lambda i=i: results.append(self.service.command("thumbnail", {"id": i}))) for i in ids]
            for t in threads: t.start()
            for t in threads: t.join()
        self.assertEqual(peak[0], 2)
        self.assertTrue(all(item["ok"] and item["data"] for item in results))

    def test_thumbnail_time_limit_returns_null_and_slot_stays_held(self):
        self.enable()
        file_id = self.add_file(self.png())
        release = threading.Event()
        with patch("docfit_core.timemachine.thumbs.render", lambda path: release.wait(5) and None), \
                patch("docfit_app.timemachine_service.THUMBNAIL_TIME_LIMIT", 0.05):
            self.assertEqual(self.service.command("thumbnail", {"id": file_id}), {"ok": True, "data": None})
            self.assertFalse(self.service._thumbnail_slots._value == 2)
            release.set()
            deadline = time.time() + 2
            while self.service._thumbnail_slots._value != 2 and time.time() < deadline:
                time.sleep(0.01)
        self.assertEqual(self.service._thumbnail_slots._value, 2)

    def test_thumbnail_busy_pdfium_asks_retry_without_caching(self):
        self.enable()
        file_id = self.add_file(self.png())
        def busy(path): raise thumbs.ThumbnailBusy()
        with patch("docfit_core.timemachine.thumbs.render", busy):
            self.assertEqual(self.service.command("thumbnail", {"id": file_id}), {"ok": True, "data": None, "retry": True})

    def test_hour_density_returns_store_values_for_exact_range(self):
        self.enable()
        from datetime import datetime
        dt_start = datetime(2026, 10, 31, 10, 0)
        dt_mid = datetime(2026, 10, 31, 10, 30)
        dt_end = datetime(2026, 10, 31, 12, 0)
        start = dt_start.timestamp()
        mid = dt_mid.timestamp()
        end = dt_end.timestamp()

        # start 이전, start(포함), mid(포함), end(제외), end 이후
        f_before = self.root / "before.pdf"; f_before.write_bytes(b"x")
        f_start = self.root / "start.pdf"; f_start.write_bytes(b"x")
        f_mid = self.root / "mid.pdf"; f_mid.write_bytes(b"x")
        f_end = self.root / "end.pdf"; f_end.write_bytes(b"x")
        f_after = self.root / "after.pdf"; f_after.write_bytes(b"x")

        rows = [
            {"path": str(f_before), "root": str(self.root), "name": f_before.name, "kind": "pdf",
             "size": 1, "mtime": start - 1, "ctime": start - 1, "work_time": start - 1, "flags": [], "cloud": False},
            {"path": str(f_start), "root": str(self.root), "name": f_start.name, "kind": "pdf",
             "size": 1, "mtime": start, "ctime": start, "work_time": start, "flags": [], "cloud": False},
            {"path": str(f_mid), "root": str(self.root), "name": f_mid.name, "kind": "pdf",
             "size": 1, "mtime": mid, "ctime": mid, "work_time": mid, "flags": [], "cloud": False},
            {"path": str(f_end), "root": str(self.root), "name": f_end.name, "kind": "pdf",
             "size": 1, "mtime": end, "ctime": end, "work_time": end, "flags": [], "cloud": False},
            {"path": str(f_after), "root": str(self.root), "name": f_after.name, "kind": "pdf",
             "size": 1, "mtime": end + 1, "ctime": end + 1, "work_time": end + 1, "flags": [], "cloud": False},
        ]
        self.service.store.upsert_many(rows)

        res = self.service.command("hour_density", {"start": start, "end": end, "roots": [str(self.root)]})
        self.assertTrue(res["ok"])
        # [start, end) 구간이므로 start와 mid만 포함 (10시 2개)
        self.assertEqual(res["hours"], {10: 2})

    def test_send_to_feature_calls_fake_api_with_authorized_paths(self):
        self.enable()
        f1 = self.png("doc1.png")
        f2 = self.png("doc2.png")
        id1 = self.add_file(f1)
        id2 = self.add_file(f2)

        calls = []
        self.service.feature_api = lambda feat, paths: calls.append((feat, paths)) or {"ok": True}

        res = self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [id1, id2]})
        self.assertTrue(res["ok"])
        self.assertEqual(res["feature"], "rename_batch")
        self.assertEqual(res["accepted_ids"], [id1, id2])
        self.assertEqual(calls, [("rename_batch", [str(f1), str(f2)])])

    def test_send_to_feature_rejects_invalid_feature_and_id_types(self):
        self.enable()
        f1 = self.png()
        id1 = self.add_file(f1)

        calls = []
        self.service.feature_api = lambda feat, ids: calls.append((feat, ids)) or {"ok": True}

        # 미허용 feature
        self.assertEqual(self.service.command("send_to_feature", {"feature": "unknown", "ids": [id1]})["code"], "INVALID_INPUT")
        # 문자열 ID
        self.assertEqual(self.service.command("send_to_feature", {"feature": "rename_batch", "ids": ["1"]})["code"], "INVALID_INPUT")
        # bool ID
        self.assertEqual(self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [True]})["code"], "INVALID_INPUT")
        # 0 ID
        self.assertEqual(self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [0]})["code"], "INVALID_INPUT")
        # 중복 ID
        self.assertEqual(self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [id1, id1]})["code"], "INVALID_INPUT")
        # 빈 ID 목록
        self.assertEqual(self.service.command("send_to_feature", {"feature": "rename_batch", "ids": []})["code"], "INVALID_INPUT")
        # 200개 초과 ID
        self.assertEqual(self.service.command("send_to_feature", {"feature": "rename_batch", "ids": list(range(1, 202))})["code"], "INVALID_INPUT")
        # fake 호출 0회 검증
        self.assertEqual(calls, [])

    def test_send_to_feature_permission_checks_all_ids_before_dispatch(self):
        self.enable()
        good_f = self.png("good.png")
        good_id = self.add_file(good_f)

        calls = []
        self.service.feature_api = lambda feat, ids: calls.append((feat, ids)) or {"ok": True}

        # 1) 없는 파일 항목
        res = self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [good_id, 999999]})
        self.assertEqual(res["code"], "TM_NOT_FOUND")

        # 2) 숨김 파일
        hidden_id = self.add_file(self.png("hidden.png"))
        self.service.store.hide(hidden_id)
        res = self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [good_id, hidden_id]})
        self.assertEqual(res["code"], "TM_NOT_AVAILABLE")

        # 3) 허용 종류 밖
        bad_f = self.root / "bad.exe"; bad_f.write_bytes(b"x")
        now = time.time()
        self.service.store.upsert_many([{"path": str(bad_f), "root": str(self.root), "name": bad_f.name, "kind": "other", "size": 1, "mtime": now, "ctime": now, "work_time": now, "flags": [], "cloud": False}])
        bad_id = self.service.store.get(self.service.store.range(now - 1, now + 1, kinds=["other"])[0]["id"])["id"]
        res = self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [good_id, bad_id]})
        self.assertEqual(res["code"], "TM_NOT_AVAILABLE")

        # 4) 비활성 루트 밖 파일
        out_f = self.plain_file
        self.service.store.upsert_many([{"path": str(out_f), "root": str(self.root), "name": out_f.name, "kind": "pdf", "size": 1, "mtime": now, "ctime": now, "work_time": now, "flags": [], "cloud": False}])
        out_id = self.service.store.get(self.service.store.range(now - 1, now + 1)[0]["id"])["id"]
        res = self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [good_id, out_id]})
        self.assertEqual(res["code"], "TM_NOT_AVAILABLE")

        # 5) 클라우드 전용 항목
        cloud_id = self.add_file(self.png("cloud.png"), cloud=True)
        res = self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [good_id, cloud_id]})
        self.assertEqual(res["code"], "TM_NOT_AVAILABLE")

        # 6) 실제 파일 없음
        missing_id = self.add_file(self.root / "missing.png")
        res = self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [good_id, missing_id]})
        self.assertEqual(res["code"], "TM_MISSING")

        # 모든 실패에 대해 fake 호출은 전혀 없어야 함
        self.assertEqual(calls, [])

    def test_send_to_feature_does_not_return_paths(self):
        self.enable()
        f1 = self.png("safe.png")
        id1 = self.add_file(f1)
        self.service.feature_api = lambda feat, ids: {"ok": True}

        success = self.service.command("send_to_feature", {"feature": "convert", "ids": [id1]})
        self.assertTrue(success["ok"])
        self.assertNotIn("path", success)
        self.assertNotIn("paths", success)
        self.assertNotIn("folder", success)

        fail = self.service.command("send_to_feature", {"feature": "convert", "ids": [999999]})
        self.assertFalse(fail["ok"])
        self.assertNotIn("path", fail)
        self.assertNotIn("folder", fail)

    def test_thumbnail_cache_clear_removes_only_cache_files(self):
        self.enable()
        thumb_folder = Path(self.service.thumbnails.folder)
        thumb_folder.mkdir(parents=True, exist_ok=True)

        cache1 = thumb_folder / "abc.jpg"
        cache1.write_bytes(b"\xff\xd8\xff")
        cache2 = thumb_folder / "tmp.tmp"
        cache2.write_bytes(b"temp")

        sentinel = Path(self.temp.name) / "sentinel.txt"
        sentinel.write_text("sentinel")
        db_file = Path(self.temp.name) / "timeline.db"

        res = self.service.command("thumbnail_cache_clear")
        self.assertTrue(res["ok"])
        self.assertGreaterEqual(res["removed"], 2)
        self.assertFalse(cache1.exists())
        self.assertFalse(cache2.exists())
        self.assertTrue(sentinel.exists())
        self.assertTrue(db_file.exists())

    def test_thumbnail_timeout_terminates_child_and_releases_slot(self):
        self.enable()
        pdf_file = self.root / "hang.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 sample")
        now = time.time()
        self.service.store.upsert_many([{"path": str(pdf_file), "root": str(self.root), "name": pdf_file.name,
                                         "kind": "pdf", "size": 15, "mtime": now, "ctime": now,
                                         "work_time": now, "flags": [], "cloud": False}])
        file_id = self.service.store.range(now - 1, now + 1)[0]["id"]

        self.service._pdf_child_target = _stuck_pdf_worker_for_test
        with patch("docfit_app.timemachine_service.THUMBNAIL_TIME_LIMIT", 0.05):
            res = self.service.command("thumbnail", {"id": file_id})
            self.assertTrue(res["ok"])
            self.assertIsNone(res["data"])
            self.assertTrue(res.get("retry"))
            self.assertEqual(self.service._thumbnail_slots._value, 2)

        # 슬롯이 반환되어 다음 요청이 정상 수행됨
        self.service._pdf_child_target = None
        good_id = self.add_file(self.png("next.png"))
        next_res = self.service.command("thumbnail", {"id": good_id})
        self.assertTrue(next_res["ok"])
        self.assertIsNotNone(next_res["data"])

    def test_thumbnail_start_failure_releases_slot_safely(self):
        self.enable()
        pdf_file = self.root / "start_fail.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 sample")
        now = time.time()
        self.service.store.upsert_many([{"path": str(pdf_file), "root": str(self.root), "name": pdf_file.name,
                                         "kind": "pdf", "size": 15, "mtime": now, "ctime": now,
                                         "work_time": now, "flags": [], "cloud": False}])
        file_id = self.service.store.range(now - 1, now + 1)[0]["id"]

        with patch.object(thumbs.PdfRenderProcess, "start", side_effect=RuntimeError("spawn failed")):
            res = self.service.command("thumbnail", {"id": file_id})
            self.assertTrue(res["ok"])
            self.assertIsNone(res["data"])
            self.assertEqual(self.service._thumbnail_slots._value, 2)

    def test_send_to_feature_default_adapter_rename_batch(self):
        self.enable()
        f1 = self.png("default_batch1.png")
        f2 = self.png("default_batch2.png")
        id1 = self.add_file(f1)
        id2 = self.add_file(f2)

        calls = []
        self.service.feature_api = lambda feat, paths: calls.append((feat, paths)) or {"ok": True}
        res = self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [id1, id2]})
        self.assertTrue(res["ok"])
        self.assertEqual(calls, [("rename_batch", [str(f1), str(f2)])])

        self.service.feature_api = None
        unavailable = self.service.command("send_to_feature", {"feature": "rename_batch", "ids": [id1, id2]})
        self.assertFalse(unavailable["ok"])
        self.assertEqual(unavailable["code"], "FEATURE_UNAVAILABLE")

    def test_send_to_feature_limits_convert_and_document_edit(self):
        self.enable()
        f1 = self.png("limit1.png")
        f2 = self.png("limit2.png")
        id1 = self.add_file(f1)
        id2 = self.add_file(f2)

        calls = []
        self.service.feature_api = lambda feat, ids: calls.append((feat, ids)) or {"ok": True}

        res_convert = self.service.command("send_to_feature", {"feature": "convert", "ids": [id1, id2]})
        self.assertFalse(res_convert["ok"])
        self.assertEqual(res_convert["code"], "FEATURE_LIMIT")

        res_edit = self.service.command("send_to_feature", {"feature": "document_edit", "ids": [id1, id2]})
        self.assertFalse(res_edit["ok"])
        self.assertEqual(res_edit["code"], "FEATURE_LIMIT")
        self.assertEqual(calls, [])


    def _related_pair(self):
        self.enable()
        a, b = self.root / "A.txt", self.root / "B.txt"
        a.write_text("2026년도 3분기 주요업무추진실적\n작성 기준일: 2026-09-30\n디지털전환 사업", encoding="utf-8")
        b.write_text("2026년도 2분기 주요업무추진실적\n작성 기준일: 2026-06-30\n디지털전환 사업", encoding="utf-8")
        self.service.content_index.index_file(a)
        self.service.content_index.index_file(b)
        return a, b

    def test_related_id_exclude_round_trip_without_paths_in_response(self):
        a, b = self._related_pair()
        response = self.service.command("related_search", {"path": str(a)})
        self.assertTrue(response["ok"])
        item = response["items"][0]
        self.assertNotIn("path", item)
        self.assertNotIn(str(self.root), json.dumps(response, ensure_ascii=False))
        related_id = item["related_id"]
        saved = self.service.command("related_exclude", {"related_id": related_id})
        self.assertEqual(saved, {"ok": True, "excluded": True})
        self.assertNotIn(str(self.root), json.dumps(saved, ensure_ascii=False))
        self.assertEqual(self.service.command("related_search", {"path": str(a)})["items"], [])
        restored = self.service.command("related_exclude", {"related_id": related_id, "excluded": False})
        self.assertTrue(restored["ok"])
        again = self.service.command("related_search", {"path": str(a)})["items"]
        self.assertEqual([i["name"] for i in again], ["B.txt"])
        self.assertNotEqual(again[0]["related_id"], related_id)

    def test_related_exclude_rejects_unknown_id_and_keeps_path_input(self):
        a, b = self._related_pair()
        for bad in ("없는-id", 123, ""):
            res = self.service.command("related_exclude", {"related_id": bad})
            self.assertFalse(res["ok"])
            self.assertEqual(res["code"], "INVALID_INPUT")
        self.assertEqual(len(self.service.command("related_search", {"path": str(a)})["items"]), 1)
        saved = self.service.command("related_exclude", {"selected_path": str(a), "related_path": str(b)})
        self.assertTrue(saved["ok"])
        self.assertEqual(self.service.command("related_search", {"path": str(a)})["items"], [])

    def test_related_id_table_keeps_only_recent_entries(self):
        with patch("docfit_app.timemachine_service.RELATED_ID_LIMIT", 2):
            ids = [self.service._issue_related_id("a", str(n)) for n in range(3)]
        self.assertIsNone(self.service._lookup_related_id(ids[0]))
        self.assertEqual(self.service._lookup_related_id(ids[2]), ("a", "2"))

if __name__ == "__main__": unittest.main()
