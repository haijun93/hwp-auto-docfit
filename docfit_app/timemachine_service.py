"""타임머신 화면 명령과 기존 KAgent 색인 저장소의 앱 측 연결."""
from __future__ import annotations

import json
import logging
import math
import os
import stat
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from docfit_core.timemachine.rules import KINDS, Rules
from docfit_core.timemachine.scan import default_roots, scan_roots
from docfit_core.timemachine.store import Store
from .kagent_client import KAgentClient, data_dir


class TimemachineService:
    def __init__(self, settings_root, *, db_path=None, agent=None, opener=None,
                 revealer=None, scanner=scan_roots):
        self.settings_root = Path(settings_root)
        self.settings_path = self.settings_root / "timemachine.json"
        self.store = Store(db_path or data_dir() / "timeline.db")
        self.agent = agent if agent is not None else KAgentClient()
        self.opener = opener if opener is not None else self._open_file
        self.revealer = revealer if revealer is not None else self._reveal_file
        self.scanner = scanner
        self._settings_lock = threading.RLock()
        self._scan_lock = threading.Lock()
        self._scan_state = {"running": False, "seen": 0, "written": 0, "removed": 0,
                            "errors": [], "started_at": None, "finished_at": None}
        self._settings = self._load_settings()

    @staticmethod
    def _open_file(path):
        os.startfile(path)

    @staticmethod
    def _reveal_file(path):
        subprocess.Popen(["explorer", "/select," + path])

    def _defaults(self):
        return {"roots": default_roots(), "time_mode": "max", "enabled": False}

    def _load_settings(self):
        defaults = self._defaults()
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            roots = data["roots"]
            mode = data["time_mode"]
            enabled = data["enabled"]
            roots = self._validate_roots(roots)
            if mode not in ("max", "mtime") or type(enabled) is not bool:
                raise ValueError("settings")
            return {"roots": roots, "time_mode": mode, "enabled": enabled}
        except (OSError, ValueError, TypeError, KeyError):
            return defaults

    @staticmethod
    def _root_key(path):
        return os.path.normcase(os.path.normpath(os.path.abspath(path))).casefold()

    def _path_in_active_root(self, path, stored_root=None):
        if not isinstance(path, str) or not os.path.isabs(path):
            return False
        normalized_stored_root = self._root_key(stored_root) if isinstance(stored_root, str) else None
        for root in self._settings["roots"]:
            if normalized_stored_root is not None and self._root_key(root) != normalized_stored_root:
                continue
            try:
                root_path = os.path.normcase(os.path.normpath(os.path.abspath(root))).casefold()
                file_path = os.path.normcase(os.path.normpath(os.path.abspath(path)))
                file_path = file_path.casefold()
                if os.path.commonpath((root_path, file_path)) == root_path:
                    return True
            except (OSError, ValueError):
                continue
        return False

    @staticmethod
    def _validate_roots(roots):
        if not isinstance(roots, list) or len(roots) > 20:
            raise ValueError("조사 폴더는 최대 20개까지 지정할 수 있습니다.")
        result, seen = [], set()
        for raw in roots:
            if not isinstance(raw, str) or not os.path.isabs(raw):
                raise ValueError("조사 폴더는 절대 경로로 지정해 주세요.")
            path = os.path.abspath(raw)
            try:
                info = os.lstat(path)
            except OSError as exc:
                raise ValueError("존재하는 폴더를 선택해 주세요.") from exc
            attributes = getattr(info, "st_file_attributes", 0)
            if (not stat.S_ISDIR(info.st_mode) or os.path.islink(path) or
                    attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
                raise ValueError("심볼릭 링크나 정션이 아닌 폴더를 선택해 주세요.")
            key = TimemachineService._root_key(path)
            if key not in seen:
                result.append(path)
                seen.add(key)
        return result

    def _save_settings(self, settings):
        self.settings_root.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="timemachine-", suffix=".tmp", dir=self.settings_root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(settings, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.settings_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _error(code, message):
        return {"ok": False, "code": code, "message": message}

    def _agent_running(self):
        return bool(self.agent.running())

    def _filter_args(self, payload, *, range_required=False):
        kinds = payload.get("kinds")
        roots = payload.get("roots", self._settings["roots"])
        query = payload.get("query", "")
        if kinds is not None and (not isinstance(kinds, list) or any(k not in KINDS for k in kinds)):
            raise ValueError("종류 필터를 확인해 주세요.")
        if roots is not None and (not isinstance(roots, list) or any(
                not isinstance(root, str) or self._root_key(root) not in
                {self._root_key(item) for item in self._settings["roots"]} for root in roots)):
            raise ValueError("현재 조사 폴더 안에서 선택해 주세요.")
        if not isinstance(query, str) or len(query) > 200:
            raise ValueError("이름 검색은 200자 이하로 입력해 주세요.")
        filters = {"kinds": kinds, "roots": roots, "query": query or None}
        if not range_required:
            return filters
        start, end = payload.get("start"), payload.get("end")
        if (isinstance(start, bool) or isinstance(end, bool) or
                not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or
                not math.isfinite(start) or not math.isfinite(end) or start >= end):
            raise ValueError("조회 기간을 확인해 주세요.")
        return start, end, filters

    def _status(self):
        with self._scan_lock:
            scan = dict(self._scan_state, errors=list(self._scan_state["errors"]))
        return {"ok": True, **self._settings, "stats": self.store.stats(),
                "agent_running": self._agent_running(), "scan": scan}

    def _scan_worker(self, roots, mode):
        def progress(result):
            with self._scan_lock:
                self._scan_state.update(seen=result.seen, written=result.written,
                                        removed=result.removed,
                                        errors=[str(item[1]) for item in result.errors])
        try:
            result = self.scanner(self.store, roots, Rules(time_mode=mode), progress=progress)
            with self._settings_lock:
                current = list(self._settings["roots"])
            retained = {self._root_key(root) for root in current}
            for root in roots:
                if self._root_key(root) not in retained:
                    self.store.drop_root(root)
            with self._scan_lock:
                self._scan_state.update(seen=result.seen, written=result.written,
                                        removed=result.removed,
                                        errors=[str(item[1]) for item in result.errors])
        except Exception as exc:
            logging.getLogger(__name__).exception("타임머신 색인 갱신 실패")
            with self._scan_lock:
                self._scan_state["errors"] = [type(exc).__name__]
        finally:
            with self._scan_lock:
                self._scan_state.update(running=False, finished_at=time.time())

    def _start_scan(self):
        if not self._settings["enabled"]:
            return self._error("TM_DISABLED", "타임머신을 켠 뒤 다시 훑어 주세요.")
        with self._scan_lock:
            if self._scan_state["running"]:
                return {"ok": True, "by": "app", "running": True}
            if self._agent_running():
                return {"ok": True, "by": "agent"}
            self._scan_state.update(running=True, seen=0, written=0, removed=0,
                                    errors=[], started_at=time.time(), finished_at=None)
            roots, mode = list(self._settings["roots"]), self._settings["time_mode"]
            worker = threading.Thread(target=self._scan_worker, args=(roots, mode),
                                      name="timemachine-scan", daemon=True)
            try:
                worker.start()
            except Exception as exc:
                self._scan_state.update(running=False, finished_at=time.time(),
                                        errors=[type(exc).__name__])
                return self._error("TM_SCAN_FAILED", "색인 작업을 시작하지 못했습니다.")
        return {"ok": True, "by": "app", "running": True}

    def _command(self, action, payload):
        if action == "status":
            return self._status()
        if action == "settings_get":
            return {"ok": True, "settings": dict(self._settings, roots=list(self._settings["roots"]))}
        if action == "settings_set":
            roots = self._validate_roots(payload.get("roots"))
            mode, enabled = payload.get("time_mode"), payload.get("enabled")
            if mode not in ("max", "mtime") or type(enabled) is not bool:
                raise ValueError("설정 값을 확인해 주세요.")
            settings = {"roots": roots, "time_mode": mode, "enabled": enabled}
            with self._settings_lock:
                old_roots = list(self._settings["roots"])
                removed = {self._root_key(root) for root in old_roots} - {self._root_key(root) for root in roots}
                self._save_settings(settings)
                self._settings = settings
                for root in old_roots:
                    if self._root_key(root) in removed:
                        self.store.drop_root(root)
            try:
                if self._agent_running():
                    self.agent.request("settings_set", settings={"timeline_roots": roots,
                                         "timeline_mtime_only": mode == "mtime"})
            except Exception:
                logging.getLogger(__name__).debug("KAgent 설정 알림을 전달하지 못했습니다.", exc_info=True)
            return {"ok": True, "settings": dict(settings, roots=list(roots))}
        if action == "scan":
            return self._start_scan()
        if action == "range":
            start, end, filters = self._filter_args(payload, range_required=True)
            newest = payload.get("newest_first", True)
            limit, offset = payload.get("limit", 200), payload.get("offset", 0)
            if type(newest) is not bool or type(limit) is not int or not 1 <= limit <= 200 or type(offset) is not int or offset < 0:
                raise ValueError("페이지 범위를 확인해 주세요.")
            if not filters["roots"]:
                return {"ok": True, "items": []}
            rows = self.store.range(start, end, **filters, newest_first=newest, limit=limit, offset=offset)
            rows = [row for row in rows if self._path_in_active_root(row["path"], row.get("root"))]
            items = [{"id": row["id"], "name": row["name"], "kind": row["kind"],
                      "size": row["size"], "mtime": row["mtime"], "ctime": row["ctime"],
                      "work_time": row["work_time"], "flags": row["flags"], "cloud": row["cloud"],
                      "folder": os.path.dirname(row["path"])} for row in rows]
            return {"ok": True, "items": items}
        if action in ("day_counts", "hour_density"):
            filters = self._filter_args(payload)
            if action == "day_counts":
                year, month = payload.get("year"), payload.get("month")
                if type(year) is not int or type(month) is not int or not 1 <= year <= 9999 or not 1 <= month <= 12:
                    raise ValueError("달력 날짜를 확인해 주세요.")
                if not filters["roots"]:
                    return {"ok": True, "days": {}}
                return {"ok": True, "days": self.store.day_counts(year, month, **filters)}
            start, end, range_filters = self._filter_args(payload, range_required=True)
            if not range_filters["roots"]:
                return {"ok": True, "hours": {}}
            return {"ok": True, "hours": self.store.hour_density(start, end, **range_filters)}
        if action == "hide":
            file_id = payload.get("id")
            if type(file_id) is not int or file_id <= 0:
                raise ValueError("파일 항목을 확인해 주세요.")
            if not self.store.hide(file_id):
                return self._error("TM_NOT_FOUND", "파일 항목을 찾지 못했습니다.")
            return {"ok": True}
        if action in ("open", "reveal"):
            file_id = payload.get("id")
            if type(file_id) is not int or file_id <= 0:
                raise ValueError("파일 항목을 확인해 주세요.")
            row = self.store.get(file_id)
            if not row:
                return self._error("TM_NOT_FOUND", "파일 항목을 찾지 못했습니다.")
            path = row["path"]
            if (Rules().kind(row["name"]) not in KINDS or
                    not self._path_in_active_root(path, row.get("root"))):
                return self._error("TM_NOT_AVAILABLE", "지원하지 않는 파일입니다.")
            if not os.path.isfile(path):
                self.store.hide(file_id)
                return self._error("TM_MISSING", "파일이 없어 목록에서 정리했습니다.")
            try:
                (self.opener if action == "open" else self.revealer)(path)
            except Exception:
                logging.getLogger(__name__).exception("타임머신 파일 작업 실패")
                return self._error("TM_OPEN_FAILED" if action == "open" else "TM_REVEAL_FAILED",
                                   "파일을 열지 못했습니다." if action == "open" else "폴더를 열지 못했습니다.")
            return {"ok": True}
        return self._error("NOT_AVAILABLE", "지원하지 않는 타임머신 명령입니다.")

    def command(self, action, payload=None):
        if not isinstance(action, str) or not isinstance(payload, (dict, type(None))):
            return self._error("INVALID_INPUT", "명령 입력을 확인해 주세요.")
        try:
            return self._command(action, payload or {})
        except ValueError as exc:
            return self._error("INVALID_INPUT", str(exc))
        except Exception:
            logging.getLogger(__name__).exception("타임머신 명령 처리 실패")
            return self._error("TM_FAILED", "타임머신 작업을 완료하지 못했습니다.")
