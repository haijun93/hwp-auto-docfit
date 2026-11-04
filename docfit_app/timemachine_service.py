"""타임머신 화면 명령과 기존 KAgent 색인 저장소의 앱 측 연결."""
from __future__ import annotations

import base64
import json
import logging
import math
import os
import secrets
import stat
import subprocess
import tempfile
import threading
import time
from collections import OrderedDict
from pathlib import Path

from docfit_core.timemachine import thumbs
from docfit_core.timemachine.content_search import ContentSearchIndex
from docfit_core.timemachine.related import related_documents
from docfit_core.timemachine.rules import DEFAULT_EXTENSIONS, IMAGE_EXTENSIONS, KINDS, Rules, SUPPORTED_EXTENSIONS
from docfit_core.timemachine.scan import default_roots, scan_roots
from docfit_core.timemachine.store import Store
from .kagent_client import KAgentClient, data_dir

THUMBNAIL_SLOTS = 2
THUMBNAIL_WAIT_SECONDS = 8.0
THUMBNAIL_TIME_LIMIT = 5.0
RELATED_ID_LIMIT = 1000


ALLOWED_FEATURES = frozenset(("rename_batch", "convert", "document_edit"))


class TimemachineService:
    def __init__(self, settings_root, *, db_path=None, agent=None, opener=None,
                 revealer=None, scanner=scan_roots, thumb_dir=None, feature_api=None,
                 developer_mode=None):
        self.settings_root = Path(settings_root)
        self.settings_path = self.settings_root / "timemachine.json"
        self.store = Store(db_path or data_dir() / "timeline.db")
        content_db = (Path(db_path).with_suffix(".content.sqlite") if db_path else data_dir() / "timeline-content.sqlite")
        self.content_index = ContentSearchIndex(content_db)
        self.agent = agent if agent is not None else KAgentClient()
        self.opener = opener if opener is not None else self._open_file
        self.revealer = revealer if revealer is not None else self._reveal_file
        self.scanner = scanner
        self.thumbnails = thumbs.ThumbnailCache(thumb_dir or data_dir() / "thumbs")
        self.feature_api = feature_api
        self.developer_mode = developer_mode or (lambda: False)
        self._pdf_child_target = None
        self._thumbnail_slots = threading.BoundedSemaphore(THUMBNAIL_SLOTS)
        self._settings_lock = threading.RLock()
        self._scan_lock = threading.Lock()
        self._content_lock = threading.RLock()
        self._content_cancel = threading.Event()
        self._content_thread = None
        self._content_pending_roots = None
        self._content_state = {"running": False, "seen": 0, "indexed": 0, "errors": 0,
                               "cancelled": False, "started_at": None, "finished_at": None}
        self._scan_state = {"running": False, "seen": 0, "written": 0, "removed": 0,
                            "errors": [], "started_at": None, "finished_at": None}
        self._rescan = False
        # 연관 항목 불투명 ID → (선택 경로, 연관 경로). 응답에 경로를 내보내지 않기 위한 대응표.
        self._related_ids = OrderedDict()
        self._related_lock = threading.Lock()
        self._settings = self._load_settings()

    def _issue_related_id(self, selected_path, related_path):
        """연관 항목마다 새 불투명 ID를 발급하고 최근 RELATED_ID_LIMIT개만 보관한다."""
        related_id = secrets.token_urlsafe(16)
        with self._related_lock:
            self._related_ids[related_id] = (selected_path, related_path)
            while len(self._related_ids) > RELATED_ID_LIMIT:
                self._related_ids.popitem(last=False)
        return related_id

    def _lookup_related_id(self, related_id):
        if not isinstance(related_id, str):
            return None
        with self._related_lock:
            return self._related_ids.get(related_id)

    @staticmethod
    def _open_file(path):
        os.startfile(path)

    @staticmethod
    def _reveal_file(path):
        subprocess.Popen(["explorer", "/select," + path])

    def _defaults(self):
        return {"roots": default_roots(), "time_mode": "max", "enabled": False, "extensions": list(DEFAULT_EXTENSIONS)}

    def close(self):
        self.cancel_content_index(wait=True)
        self.content_index.close()
        self.store.close()

    def _finish_content_index(self, cancel_event):
        with self._content_lock:
            self._content_state.update(running=False, cancelled=cancel_event.is_set(), finished_at=time.time())

    def _content_index_worker(self, roots, extensions, cancel_event=None):
        cancel_event = cancel_event or self._content_cancel
        seen = indexed = errors = 0
        rules = Rules(extensions=extensions, extra_extensions=extensions)  # 본문 색인 확장자(예: txt)는 타임라인 종류에 없어도 색인한다
        try:
            for root in roots:
                for folder, dirs, files in os.walk(root, followlinks=False):
                    if cancel_event.is_set(): break
                    dirs[:] = [d for d in dirs if not rules.skip_dir(d) and not cancel_event.is_set()]
                    for name in files:
                        if cancel_event.is_set():
                            break
                        ext = Path(name).suffix.lower().lstrip(".")
                        if ext not in extensions:
                            continue
                        path = os.path.join(folder, name)
                        if not self._path_in_active_root(path):
                            continue
                        if cancel_event.is_set(): break
                        with self._content_lock:
                            if self._content_pending_roots is not None:
                                self._content_pending_roots.discard(os.path.normcase(os.path.abspath(path)))
                        if ext in IMAGE_EXTENSIONS:
                            # 설계 의도: 디스크에 존재하는 이미지 파일은 pending 색인 큐에서 정상 제거하여
                            # 스캔 종료 후 불필요한 삭제 검사를 생략하고, 본문 텍스트 추출 대상이 아니므로
                            # index_file 호출을 건너뛰어 오류 및 처리 카운트를 증가시키지 않는다.
                            continue
                        if rules.skip_file(name):
                            self.content_index.remove_file(path)
                            continue
                        result = self.content_index.index_file(path)
                        seen += 1
                        indexed += bool(result["indexed"])
                        errors += bool(result["error"])
                        with self._content_lock:
                            self._content_state.update(seen=seen, indexed=indexed, errors=errors)
                    if cancel_event.is_set():
                        break
                if cancel_event.is_set():
                    break
            # 연결이 끊긴 드라이브의 문서는 지워진 것으로 보지 않는다.
            available = [os.path.normcase(os.path.abspath(root)) + os.sep for root in roots if os.path.isdir(root)]
            active_roots = [os.path.normcase(os.path.abspath(root)) + os.sep
                            for root in self._settings["roots"] if os.path.isdir(root)]
            with self._content_lock:
                pending = tuple(self._content_pending_roots or ())
            for path in pending:
                if cancel_event.is_set():
                    break
                normalized = os.path.normcase(os.path.abspath(path))
                in_scan_roots = normalized.startswith(tuple(available))
                in_active_roots = normalized.startswith(tuple(active_roots))
                extension_allowed = Path(path).suffix.lower().lstrip(".") in self._settings["extensions"]
                if in_scan_roots and (not in_active_roots or not extension_allowed or not os.path.exists(path)):
                    self.content_index.remove_file(path)
        finally:
            self._finish_content_index(cancel_event)

    def _start_content_index(self):
        with self._content_lock:
            if self._content_state["running"] or (self._content_thread and self._content_thread.is_alive()):
                return {"ok": True, **dict(self._content_state)}
            self._content_pending_roots = set(self.content_index.indexed_paths(roots=self._settings["roots"]))
            cancel_event = threading.Event()
            self._content_cancel = cancel_event
            self._content_state = {"running": True, "seen": 0, "indexed": 0, "errors": 0,
                                   "cancelled": False, "started_at": time.time(), "finished_at": None}
            self._content_thread = threading.Thread(target=self._content_index_worker,
                args=(list(self._settings["roots"]), frozenset(self._settings["extensions"]), cancel_event),
                name="timemachine-content-index", daemon=True)
            try:
                self._content_thread.start()
            except Exception as exc:
                self._content_state.update(running=False, finished_at=time.time())
                return self._error("TM_INDEX_FAILED", f"색인 작업을 시작하지 못했습니다: {exc}")
            return {"ok": True, **dict(self._content_state)}

    def cancel_content_index(self, *, wait=False, timeout=2.0):
        with self._content_lock:
            cancel_event = self._content_cancel
            worker = self._content_thread
            if not self._content_state["running"]:
                return {"ok": True, **dict(self._content_state)}
            cancel_event.set()
        if wait and worker and worker is not threading.current_thread():
            worker.join(timeout=max(0.0, timeout))
            if worker.is_alive():
                with self._content_lock:
                    return {"ok": False, "code": "TM_CANCEL_TIMEOUT", "message": "색인 작업 취소 대기 시간이 초과되었습니다.", **dict(self._content_state)}
        with self._content_lock:
            return {"ok": True, **dict(self._content_state)}

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
            extensions = self._validate_extensions(data.get("extensions", list(DEFAULT_EXTENSIONS)))
            return {"roots": roots, "time_mode": mode, "enabled": enabled, "extensions": extensions}
        except (OSError, ValueError, TypeError, KeyError):
            return defaults

    @staticmethod
    def _root_key(path):
        return os.path.normcase(os.path.normpath(os.path.abspath(path))).casefold()

    def _parts_under_root(self, path):
        """조사 폴더 아래의 폴더 이름만 돌려준다. 조사 폴더 자체의 상위(예: AppData, Temp)는 제외 규칙에 넣지 않는다."""
        file_path = os.path.normcase(os.path.normpath(os.path.abspath(path)))
        for root in self._settings["roots"]:
            root_path = os.path.normcase(os.path.normpath(os.path.abspath(root)))
            try:
                if os.path.commonpath((root_path, file_path)) == root_path:
                    return Path(os.path.relpath(file_path, root_path)).parts[:-1]
            except ValueError:
                continue
        return Path(path).parts[:-1]

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
            if any(part.casefold() == "$recycle.bin" for part in Path(path).parts):
                raise ValueError("Windows 휴지통($Recycle.Bin)은 타임머신 조사 폴더로 선택할 수 없습니다.")
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

    @staticmethod
    def _validate_extensions(values):
        allowed = set(SUPPORTED_EXTENSIONS)
        if not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values):
            raise ValueError("적용 확장자를 확인해 주세요.")
        result = []
        for value in values:
            ext = value.lower().lstrip(".")
            if ext not in allowed:
                raise ValueError("지원하지 않는 확장자입니다.")
            if ext not in result:
                result.append(ext)
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

    def _require_developer_mode(self):
        enabled = bool(self.developer_mode()) if callable(self.developer_mode) else False
        if not enabled:
            return self._error("DEVELOPER_MODE_REQUIRED", "본문검색은 개발자 모드에서만 사용할 수 있습니다.")
        return None

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
                "agent_running": self._agent_running(), "watch": self._watch_mode(), "scan": scan}

    def _watch_mode(self):
        """화면 표시용: 에이전트가 실제로 조사 폴더를 맡았을 때만 'agent'(켜져만 있으면 안 됨)."""
        roots = self._settings["roots"]
        if not self._settings["enabled"] or not roots or not self._agent_running():
            return "app"
        status = self.agent.status_file()
        return "agent" if status and status.get("timeline_roots") == len(roots) else "app"

    @classmethod
    def _same_roots(cls, left, right):
        return (isinstance(left, list) and isinstance(right, list) and
                sorted(cls._root_key(str(item)) for item in left) ==
                sorted(cls._root_key(str(item)) for item in right))

    @staticmethod
    def _agent_settings(settings):
        # 꺼진 타임머신의 폴더를 에이전트가 계속 감시하면 안 되므로 빈 목록을 보낸다.
        return {"timeline_roots": settings["roots"] if settings["enabled"] else [],
                "timeline_mtime_only": settings["time_mode"] == "mtime"}

    def _sync_agent(self, *, force=False):
        """에이전트에 조사 폴더를 맡긴다. 맡았으면 True, 아니면 앱이 색인해야 하므로 False.

        에이전트를 타임머신보다 나중에 켜면 에이전트 설정에 폴더가 없으므로, 보내기 전에 비교한다.
        """
        wanted = self._agent_settings(self._settings)
        try:
            if not self._agent_running():
                return False
            if not force:
                current = self.agent.request("settings_get")
                current = current.get("settings") if isinstance(current, dict) else None
                if (isinstance(current, dict) and
                        self._same_roots(current.get("timeline_roots"), wanted["timeline_roots"]) and
                        current.get("timeline_mtime_only") == wanted["timeline_mtime_only"]):
                    return True
            reply = self.agent.request("settings_set", settings=wanted)
            applied = reply.get("settings") if isinstance(reply, dict) else None
            # 에이전트가 거른 폴더(네트워크 경로 등)가 있으면 앱이 색인한다.
            return (isinstance(applied, dict) and
                    self._same_roots(applied.get("timeline_roots"), wanted["timeline_roots"]))
        except Exception:
            logging.getLogger(__name__).debug("KAgent 설정 알림을 전달하지 못했습니다.", exc_info=True)
            return False

    def _scan_worker(self, roots, mode):
        def progress(result):
            with self._scan_lock:
                self._scan_state.update(seen=result.seen, written=result.written,
                                        removed=result.removed,
                                        errors=[str(item[1]) for item in result.errors])
        try:
            result = self.scanner(self.store, roots, Rules(time_mode=mode, extensions=self._settings["extensions"]), progress=progress)
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
            self._refresh_content_index_async()
        except Exception as exc:
            logging.getLogger(__name__).exception("타임머신 색인 갱신 실패")
            with self._scan_lock:
                self._scan_state["errors"] = [type(exc).__name__]
        finally:
            with self._scan_lock:
                self._scan_state.update(running=False, finished_at=time.time())
                again, self._rescan = self._rescan, False
            if again:
                self._start_scan()

    def _start_scan(self, *, agent_ready=None, restart=False):
        if not self._settings["enabled"]:
            return self._error("TM_DISABLED", "타임머신을 켠 뒤 다시 훑어 주세요.")
        if agent_ready is None:
            agent_ready = self._sync_agent()
        with self._scan_lock:
            if self._scan_state["running"]:
                # 진행 중인 훑기는 예전 폴더 목록이므로 설정이 바뀌었으면 끝난 뒤 한 번 더 훑는다.
                self._rescan = self._rescan or restart
                return {"ok": True, "by": "app", "running": True}
            if agent_ready:
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

    def _refresh_content_index_async(self):
        with self._content_lock:
            if self._content_state["running"] or (self._content_thread and self._content_thread.is_alive()):
                return
            # 본문 색인을 쓴 적이 없으면(색인이 비어 있으면) 자동으로 시작하지 않는다.
            pending = set(self.content_index.indexed_paths(roots=self._settings["roots"]))
            if not pending:
                return
            self._content_pending_roots = pending
            cancel_event = threading.Event()
            self._content_cancel = cancel_event
            self._content_state = {"running": True, "seen": 0, "indexed": 0, "errors": 0,
                                   "cancelled": False, "started_at": time.time(), "finished_at": None}
            self._content_thread = threading.Thread(target=self._content_index_worker,
                args=(list(self._settings["roots"]), frozenset(self._settings["extensions"]), cancel_event),
                name="timemachine-content-index", daemon=True)
            self._content_thread.start()

    def _command(self, action, payload):
        if action in {"content_index", "content_index_all", "content_index_start",
                      "content_index_status", "content_index_progress", "content_index_cancel",
                      "content_search", "content_preview"}:
            denied = self._require_developer_mode()
            if denied is not None:
                return denied
        if action == "status":
            return self._status()
        if action == "settings_get" or (action == "settings" and not payload):
            return {"ok": True, "settings": dict(self._settings, roots=list(self._settings["roots"]))}
        if action in ("settings_set", "settings"):
            roots = self._validate_roots(payload.get("roots"))
            mode, enabled = payload.get("time_mode"), payload.get("enabled")
            if mode not in ("max", "mtime") or type(enabled) is not bool:
                raise ValueError("설정 값을 확인해 주세요.")
            extensions = self._validate_extensions(payload.get("extensions", self._settings["extensions"]))
            settings = {"roots": roots, "time_mode": mode, "enabled": enabled, "extensions": extensions}
            with self._settings_lock:
                old_roots = list(self._settings["roots"])
                changed = self._settings != settings
                removed = {self._root_key(root) for root in old_roots} - {self._root_key(root) for root in roots}
                self._save_settings(settings)
                self._settings = settings
                for root in old_roots:
                    if self._root_key(root) in removed:
                        self.store.drop_root(root)
            agent_ready = self._sync_agent(force=True)
            if enabled and changed:
                self._start_scan(agent_ready=agent_ready, restart=True)
            return {"ok": True, "settings": dict(settings, roots=list(roots))}
        if action == "scan":
            return self._start_scan()
        if action == "content_index":
            path = payload.get("path")
            content_rules = Rules(extensions=self._settings["extensions"], extra_extensions=self._settings["extensions"])
            if (not isinstance(path, str) or not self._path_in_active_root(path) or
                    Path(path).suffix.lower().lstrip(".") not in self._settings["extensions"] or
                    any(content_rules.skip_dir(part) for part in self._parts_under_root(path)) or
                    content_rules.skip_file(Path(path).name)):
                return self._error("INVALID_INPUT", "현재 조사 폴더의 허용된 문서를 선택해 주세요.")
            result = self.content_index.index_file(path)
            return {"ok": True, **result}
        if action in ("content_index_all", "content_index_start"):
            return self._start_content_index()
        if action in ("content_index_status", "content_index_progress"):
            with self._content_lock:
                state = dict(self._content_state)
            reindex_cnt = self.content_index.needs_reindex_count(roots=self._settings["roots"])
            state["needs_reindex_count"] = reindex_cnt
            state["needs_reindex"] = reindex_cnt > 0
            state["reindex_guide"] = "기존 본문 색인은 위계 정보가 없어 재색인이 필요합니다." if reindex_cnt > 0 else None
            return {"ok": True, **state}
        if action == "content_index_cancel":
            return self.cancel_content_index(wait=bool(payload.get("wait", False)), timeout=float(payload.get("timeout", 2.0)))
        if action == "content_search":
            query = payload.get("query")
            sort = payload.get("sort")
            if not sort or not isinstance(sort, str):
                sort = "hierarchy_relevance"
            rows = self.content_index.search(query, roots=self._settings["roots"], limit=payload.get("limit", 100), sort=sort)
            for row in rows:
                row["file_name"] = row["name"]
                row["folder_path"] = os.path.dirname(row["path"])
                row["folder_name"] = os.path.basename(row["folder_path"])
                row.pop("_best_level_rank", None)
                row.pop("_document_date", None)
                row.pop("_bm25_score", None)
            reindex_cnt = self.content_index.needs_reindex_count(roots=self._settings["roots"])
            return {
                "ok": True,
                "items": rows,
                "needs_reindex": reindex_cnt > 0,
                "needs_reindex_count": reindex_cnt,
                "reindex_guide": "기존 본문 색인은 위계 정보가 없어 재색인이 필요합니다." if reindex_cnt > 0 else None,
            }
        if action == "file_search":
            query = payload.get("query")
            return {"ok": True, "items": self.content_index.search_files(query, roots=self._settings["roots"], limit=payload.get("limit", 500))}
        if action == "related_search":
            path = payload.get("path")
            if not isinstance(path, str) or not self._path_in_active_root(path):
                return self._error("INVALID_INPUT", "현재 조사 폴더의 문서를 선택해 주세요.")
            limit = payload.get("limit", 100)
            if type(limit) is not int or not 1 <= limit <= 200:
                raise ValueError("결과 개수를 확인해 주세요.")
            exclusions = self.store.related_exclusions()
            result = related_documents(self.content_index, path, roots=self._settings["roots"],
                                       excluded_pairs=exclusions, limit=limit)
            # 경로는 내부 판정에만 쓰고 서비스 응답에는 불투명 related_id만 노출한다.
            for item in result["items"]:
                item["related_id"] = self._issue_related_id(path, item.pop("path"))
            return {"ok": True, **result}
        if action == "related_exclude":
            related_id = payload.get("related_id")
            if related_id is not None:
                pair = self._lookup_related_id(related_id)
                if pair is None:
                    return self._error("INVALID_INPUT", "연관 문서 항목을 다시 검색해 주세요.")
                left, right = pair
            else:
                left, right = payload.get("selected_path"), payload.get("related_path")
            excluded = payload.get("excluded", True)
            if (not isinstance(left, str) or not isinstance(right, str) or type(excluded) is not bool or
                    not self._path_in_active_root(left) or not self._path_in_active_root(right)):
                return self._error("INVALID_INPUT", "현재 조사 폴더의 두 문서를 선택해 주세요.")
            self.store.exclude_related(left, right, excluded)
            return {"ok": True, "excluded": excluded}
        if action == "content_errors":
            return {"ok": True, "items": self.content_index.errors(self._settings["roots"])}
        if action == "range":
            start, end, filters = self._filter_args(payload, range_required=True)
            newest = payload.get("newest_first", True)
            limit, offset = payload.get("limit", 200), payload.get("offset", 0)
            if type(newest) is not bool or type(limit) is not int or not 1 <= limit <= 200 or type(offset) is not int or offset < 0:
                raise ValueError("페이지 범위를 확인해 주세요.")
            if not filters["roots"]:
                return {"ok": True, "items": []}
            filters["extensions"] = self._settings["extensions"]
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
                filters["extensions"] = self._settings["extensions"]
                return {"ok": True, "days": self.store.day_counts(year, month, **filters)}
            start, end, range_filters = self._filter_args(payload, range_required=True)
            if not range_filters["roots"]:
                return {"ok": True, "hours": {}}
            range_filters["extensions"] = self._settings["extensions"]
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
        if action == "thumbnail":
            return self._thumbnail(payload.get("id"))
        if action == "thumbnail_cache_stats":
            return {"ok": True, **self.thumbnails.stats()}
        if action == "thumbnail_cache_clear":
            target_bytes = payload.get("target_bytes")
            if isinstance(target_bytes, int) and not isinstance(target_bytes, bool) and target_bytes >= 0:
                result = self.thumbnails.prune(target_bytes)
                return {"ok": True, "removed": result["removed_count"], "freed_bytes": result["removed_bytes"]}
            return {"ok": True, "removed": self.thumbnails.clear()}
        if action == "send_to_feature":
            return self._send_to_feature(payload.get("feature"), payload.get("ids"))
        return self._error("NOT_AVAILABLE", "지원하지 않는 타임머신 명령입니다.")

    def _send_to_feature(self, feature, file_ids):
        if feature not in ALLOWED_FEATURES:
            raise ValueError("지원하지 않는 기능입니다.")
        if (not isinstance(file_ids, list) or not (1 <= len(file_ids) <= 200) or
                any(isinstance(fid, bool) or not isinstance(fid, int) or fid <= 0 for fid in file_ids) or
                len(file_ids) != len(set(file_ids))):
            raise ValueError("파일 항목을 확인해 주세요.")

        if feature in ("convert", "document_edit") and len(file_ids) > 1:
            return self._error("FEATURE_LIMIT", "문서편집/파일변환은 한 번에 한 파일만 지원합니다.")

        paths = []
        for fid in file_ids:
            row = self.store.get(fid)
            if not row:
                return self._error("TM_NOT_FOUND", "파일 항목을 찾지 못했습니다.")
            if row["hidden"]:
                return self._error("TM_NOT_AVAILABLE", "지원하지 않는 파일입니다.")
            if Rules().kind(row["name"]) not in KINDS:
                return self._error("TM_NOT_AVAILABLE", "지원하지 않는 파일입니다.")
            path = row["path"]
            if not self._path_in_active_root(path, row.get("root")):
                return self._error("TM_NOT_AVAILABLE", "지원하지 않는 파일입니다.")
            if row["cloud"]:
                return self._error("TM_NOT_AVAILABLE", "클라우드 전용 파일은 지원하지 않습니다.")
            if not os.path.isfile(path):
                self.store.hide(fid)
                return self._error("TM_MISSING", "파일이 없어 목록에서 정리했습니다.")
            paths.append(path)

        if self.feature_api is not None:
            try:
                res = self.feature_api(feature, list(paths))
                if isinstance(res, dict) and res.get("ok") is False:
                    return self._error(res.get("code", "FEATURE_FAILED"),
                                       res.get("message", "기능 작업을 완료하지 못했습니다."))
                return {"ok": True, "feature": feature, "accepted_ids": list(file_ids)}
            except Exception as exc:
                return self._error("FEATURE_FAILED", str(exc))

        return self._error("FEATURE_UNAVAILABLE", "해당 기능을 사용할 수 없습니다.")

    def _thumbnail_allowed(self, row):
        """색인에 있고 지금 조사 폴더 안(연결 경로로 밖을 가리키지 않음)의 파일인지 본다."""
        path = row["path"]
        if (row["hidden"] or Rules().kind(row["name"]) not in KINDS or
                not self._path_in_active_root(path, row.get("root"))):
            return False
        if row["cloud"]:
            return True  # 내용을 열지 않고 아이콘으로 끝나므로 실제 경로를 확인할 필요가 없다.
        real = os.path.normcase(os.path.realpath(path)).casefold()
        for root in self._settings["roots"]:
            base = os.path.normcase(os.path.realpath(root)).casefold()
            try:
                if os.path.commonpath((base, real)) == base:
                    return True
            except ValueError:
                continue
        return False

    def _thumbnail(self, file_id):
        if type(file_id) is not int or file_id <= 0:
            raise ValueError("파일 항목을 확인해 주세요.")
        if not self._settings["enabled"]:
            return self._error("TM_DISABLED", "타임머신이 꺼져 있습니다.")
        row = self.store.get(file_id)
        if not row:
            return self._error("TM_NOT_FOUND", "파일 항목을 찾지 못했습니다.")
        if not self._thumbnail_allowed(row):
            return self._error("TM_NOT_AVAILABLE", "지원하지 않는 파일입니다.")
        path = row["path"]
        cached, key = thumbs.lookup(path, self.thumbnails, cloud=bool(row["cloud"]))
        if key is None or cached is not None:
            return self._thumbnail_result(cached)
        if not self._thumbnail_slots.acquire(timeout=THUMBNAIL_WAIT_SECONDS):
            return self._thumbnail_result(None, retry=True)
        if os.path.splitext(path)[1].lower() == ".pdf":
            proc = thumbs.PdfRenderProcess(path, target=self._pdf_child_target)
            try:
                proc.start()
                proc.join(THUMBNAIL_TIME_LIMIT)
                if proc.is_alive():
                    proc.terminate()
                    return self._thumbnail_result(None, retry=True)
                outcome = proc.get_result()
                if not outcome:
                    return self._thumbnail_result(None, retry=True)
                status, data = outcome
                if status == "busy":
                    return self._thumbnail_result(None, retry=True)
                if status == "ok" and data:
                    try:
                        self.thumbnails.put(key, data)
                    except OSError:
                        pass
                    return self._thumbnail_result(data)
                return self._thumbnail_result(None)
            except Exception:
                if proc.is_alive():
                    proc.terminate()
                return self._thumbnail_result(None, retry=True)
            finally:
                proc.close()
                self._thumbnail_slots.release()
        outcome = {}
        def work():
            # 멈춘 작업은 강제로 끝낼 수 없으므로 칸을 끝날 때까지 쥐고 있어 동시 2개 한도를 지킨다.
            try:
                outcome["data"] = thumbs.generate(path, key, self.thumbnails)
            except thumbs.ThumbnailBusy:
                outcome["busy"] = True
            finally:
                self._thumbnail_slots.release()
        worker = threading.Thread(target=work, name="timemachine-thumbnail", daemon=True)
        try:
            worker.start()
        except Exception:
            self._thumbnail_slots.release()
            return self._thumbnail_result(None, retry=True)
        worker.join(THUMBNAIL_TIME_LIMIT)
        return self._thumbnail_result(outcome.get("data"), retry=outcome.get("busy", False))

    @staticmethod
    def _thumbnail_result(data, *, retry=False):
        result = {"ok": True, "data": base64.b64encode(data).decode("ascii") if data else None}
        if retry:
            result["retry"] = True
        return result

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
