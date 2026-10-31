"""타임머신 서비스 계약 시험. 모든 파일은 임시 폴더 안에서만 다룬다."""
import json
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path

from docfit_app.timemachine_service import TimemachineService
from docfit_core.timemachine.rules import Rules
from docfit_core.timemachine.store import Store


class FakeAgent:
    def __init__(self, running=False, fail=False):
        self.is_running, self.fail, self.calls = running, fail, []
    def running(self): return self.is_running
    def request(self, command, **payload):
        self.calls.append((command, payload))
        if self.fail: raise OSError("IPC 실패")


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
            agent=self.agent, opener=self.opened.append, revealer=self.revealed.append)

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


if __name__ == "__main__": unittest.main()
