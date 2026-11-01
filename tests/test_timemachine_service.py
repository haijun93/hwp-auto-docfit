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
            scanner=stub_scanner, thumb_dir=Path(self.temp.name) / "thumbs")

    def tearDown(self):
        self.service.store.close()
        self.temp.cleanup()

    def enable(self, roots=None):
        return self.service.command("settings_set", {"roots": [str(p) for p in (roots or [self.root])], "time_mode":"max", "enabled":True})

    def test_settings_defaults_disabled_and_default_roots(self):
        settings = self.service.command("settings_get")["settings"]
        self.assertEqual(settings["time_mode"], "max")
        self.assertFalse(settings["enabled"])
        self.assertIsInstance(settings["roots"], list)
        self.assertFalse(self.service.command("status")["enabled"])

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
        finally: service.store.close()

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


if __name__ == "__main__": unittest.main()
