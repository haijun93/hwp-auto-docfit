"""이름 변경 이력(JSON Lines). rename 직전에 intent, 성공 뒤 done을 남겨 중단돼도 되돌릴 수 있게 한다."""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import uuid

MAX_AGE_DAYS = 30
MAX_RUNS = 1000


class History:
    def __init__(self, path):
        self.path = os.fspath(path)
        self._lock = threading.Lock()

    def new_run(self, kind="apply", **extra):
        run_id = uuid.uuid4().hex[:16]
        self.write(dict(op="begin", run=run_id, kind=kind, when=time.time(), **extra))
        return run_id

    def write(self, record):
        with self._lock:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            line = json.dumps(record, ensure_ascii=False) + "\n"
            with open(self.path, "a", encoding="utf-8") as stream:
                stream.write(line)
                stream.flush()
                os.fsync(stream.fileno())

    def records(self):
        """손상된 줄(전원 차단으로 잘린 마지막 줄 등)은 건너뛴다."""
        try:
            with open(self.path, encoding="utf-8", errors="replace") as stream:
                lines = stream.readlines()
        except FileNotFoundError:
            return []
        records = []
        for line in lines:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict) and isinstance(record.get("run"), str):
                records.append(record)
        return records

    def runs(self, limit=50):
        """최근 실행부터. 항목마다 원래 경로와 현재 경로(마지막 done 기준)를 계산한다."""
        runs = {}
        order = []
        for record in self.records():
            run = runs.get(record["run"])
            if record.get("op") == "begin":
                run = runs[record["run"]] = dict(id=record["run"], kind=record.get("kind", "apply"),
                                                 when=record.get("when", 0), undo_of=record.get("undo_of"),
                                                 items={}, finished=False, undone=False)
                order.append(record["run"])
            elif run is None:
                continue
            elif record.get("op") in ("intent", "done"):
                item = run["items"].setdefault(record["item"], dict(original=record["src"], current=record["src"],
                                                                     final=None, pending=None, failed=None))
                if record["op"] == "intent":
                    item["pending"] = (record["src"], record["dst"])
                    if record.get("final"):
                        item["final"] = record["dst"]
                else:
                    item["current"] = record["dst"]
                    item["pending"] = None
            elif record.get("op") == "fail":
                item = run["items"].get(record["item"])
                if item is not None:
                    item["failed"] = record.get("reason")
                    item["pending"] = None
            elif record.get("op") == "end":
                run["finished"] = True
        for run in runs.values():
            if run["undo_of"] in runs:
                runs[run["undo_of"]]["undone"] = True
        result = [runs[run_id] for run_id in reversed(order)]
        return result[:limit] if limit else result

    def get(self, run_id):
        return next((run for run in self.runs(limit=0) if run["id"] == run_id), None)

    def prune(self, *, max_age_days=MAX_AGE_DAYS, max_runs=MAX_RUNS, now=None):
        """오래된 실행을 지운다(원자적 교체)."""
        now = now or time.time()
        keep = {run["id"] for run in self.runs(limit=max_runs) if now - run["when"] <= max_age_days * 86400}
        records = [record for record in self.records() if record["run"] in keep]
        with self._lock:
            folder = os.path.dirname(self.path) or "."
            os.makedirs(folder, exist_ok=True)
            fd, temp = tempfile.mkstemp(dir=folder, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    for record in records:
                        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                os.replace(temp, self.path)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
        return len(keep)

    def clear(self):
        with self._lock:
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass
