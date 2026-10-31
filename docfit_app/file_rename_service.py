"""파일이름 탭 서비스: 목록·미리보기·적용·되돌리기·규칙 세트.

경로는 이 서비스(호스트 메모리)만 들고 있고 화면에는 항목 id·이름·폴더만 보낸다.
목록은 파일 선택 창·폴더 선택·끌어놓기(호스트가 받은 경로)로만 늘어난다.
"""
from __future__ import annotations

import json
import os
import re
import stat
import tempfile
import threading
import uuid
from pathlib import Path

from docfit_core.file_rename import (Entry, History, PlanStaleError, RuleError, build_plan, execute_plan,
                                     natural_key, undo, validate_rules)

MAX_ENTRIES = 10000
SYSTEM_DIRS = ("windows", "program files", "program files (x86)", "programdata", "$recycle.bin",
               "system volume information")
SORT_KEYS = ("name", "path", "size", "mtime", "ctime")
RULESET_NAME = re.compile(r"^[^\\/:*?\"<>|\x00-\x1f]{1,40}$")
DEFAULT_RULESETS = {
    "사진 촬영일+번호": [{"kind": "date", "source": "exif", "format": "YYYYMMDD", "position": "replace"},
                    {"kind": "number", "digits": 3, "sep": "_"}, {"kind": "ext_case", "mode": "lower"}],
    "결과 접미사 정리": [{"kind": "strip_result_suffix"}, {"kind": "cleanup"}],
    "공문서 파일명(날짜_부서_제목)": [{"kind": "template", "template": "{date}_{dept}_{title}", "dept": ""}],
}


class RenameServiceError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _hidden_or_system(path):
    try:
        attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM)) if hasattr(
        stat, "FILE_ATTRIBUTE_HIDDEN") else os.path.basename(path).startswith(".")


def _in_system_folder(path):
    parts = [part.casefold() for part in Path(path).parts[1:2]]
    return bool(parts) and parts[0] in SYSTEM_DIRS


class FileRenameService:
    def __init__(self, settings_root, *, dialogs=None, validate_path=None):
        self.folder = Path(settings_root) / "file_rename"
        self.history = History(self.folder / "history.jsonl")
        self._dialogs = dialogs
        self._validate = validate_path or self._default_validate
        self._lock = threading.RLock()
        self._entries = {}
        self._order = []
        self._plan = None
        self._last_run = None

    # ── 경로 ──────────────────────────────────────────────────────────────
    @staticmethod
    def _default_validate(path, mode):
        """절대 경로, 링크·정션 없음, 존재."""
        if not isinstance(path, str) or not path or "\x00" in path or len(path) > 32767:
            raise RenameServiceError("RENAME_PATH_REJECTED", "경로를 확인해 주세요.")
        candidate = Path(path)
        if not candidate.is_absolute():
            raise RenameServiceError("RENAME_PATH_REJECTED", "경로를 확인해 주세요.")
        for part in (candidate, *candidate.parents):
            try:
                info = part.lstat()
            except OSError:
                continue
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise RenameServiceError("RENAME_PATH_REJECTED", "바로가기·연결 폴더 안의 파일은 바꿀 수 없습니다.")
        ok = candidate.is_dir() if mode == "directory" else candidate.is_file()
        if not ok:
            raise RenameServiceError("RENAME_PATH_REJECTED", "파일을 찾을 수 없습니다.")
        return str(candidate.resolve())

    def add_paths(self, paths, *, recursive=False, include_hidden=False, as_folder=False):
        """파일과 폴더 경로를 목록에 더한다(폴더는 펼침). 이미 있는 파일은 건너뛴다."""
        if not isinstance(paths, (list, tuple)):
            raise RenameServiceError("INVALID_INPUT", "추가할 파일 목록을 확인해 주세요.")
        skipped, files = [], []
        for raw in paths:
            try:
                is_dir = isinstance(raw, str) and os.path.isdir(raw)
                path = self._validate(raw, "directory" if is_dir else "open")
            except RenameServiceError as error:
                skipped.append(dict(path=str(raw)[:260], reason=str(error)))
                continue
            if is_dir and as_folder:
                files.append(path)
            elif is_dir:
                files.extend(self._walk(path, recursive, include_hidden, skipped))
            else:
                files.append(path)
        added = []
        with self._lock:
            known = {self._entries[i].path.casefold() for i in self._order}
            for path in files:
                if path.casefold() in known:
                    continue
                if _in_system_folder(path):
                    skipped.append(dict(path=path, reason="Windows·프로그램 폴더 안 파일은 바꾸지 않습니다."))
                    continue
                if not include_hidden and _hidden_or_system(path):
                    skipped.append(dict(path=path, reason="숨김·시스템 파일입니다."))
                    continue
                if len(self._order) >= MAX_ENTRIES:
                    skipped.append(dict(path=path, reason=f"목록은 {MAX_ENTRIES:,}개까지입니다."))
                    break
                try:
                    entry = Entry.from_path(path, uuid.uuid4().hex[:12])
                except OSError:
                    skipped.append(dict(path=path, reason="파일 정보를 읽지 못했습니다."))
                    continue
                self._entries[entry.id] = entry
                self._order.append(entry.id)
                known.add(path.casefold())
                added.append(entry.id)
            self._plan = None
        return dict(self.listing(), added=len(added), skipped=skipped[:50], skipped_count=len(skipped))

    def _walk(self, root, recursive, include_hidden, skipped):
        found = []
        for folder, dirs, names in os.walk(root, followlinks=False):
            dirs[:] = sorted((d for d in dirs if include_hidden or not _hidden_or_system(os.path.join(folder, d))),
                             key=natural_key)
            for name in sorted(names, key=natural_key):
                path = os.path.join(folder, name)
                if os.path.islink(path):
                    continue
                found.append(path)
                if len(found) > MAX_ENTRIES:
                    skipped.append(dict(path=root, reason=f"폴더 안 파일이 {MAX_ENTRIES:,}개를 넘어 나머지는 뺐습니다."))
                    return found[:MAX_ENTRIES]
            if not recursive:
                break
        return found

    def _pick(self, purpose, mode, multiple):
        if self._dialogs is None:
            raise RenameServiceError("DIALOG_UNAVAILABLE", "파일 선택 창을 열 수 없습니다.")
        result = self._dialogs.select_files(uuid.uuid4().hex, purpose, mode, multiple)
        if result.get("cancelled"):
            return None
        return self._dialogs.resolve_selection(result["selection_id"], purpose)

    # ── 목록 ──────────────────────────────────────────────────────────────
    def _view(self, entry):
        return dict(id=entry.id, name=entry.name, folder=entry.folder, size=entry.size, mtime=entry.mtime,
                    ctime=entry.ctime, is_folder=entry.is_folder)

    def listing(self):
        with self._lock:
            return dict(ok=True, entries=[self._view(self._entries[i]) for i in self._order])

    def _ids(self, payload):
        ids = payload.get("ids")
        if not isinstance(ids, list) or not all(isinstance(i, str) and i in self._entries for i in ids):
            raise RenameServiceError("INVALID_INPUT", "항목을 확인해 주세요.")
        return ids

    def remove(self, payload):
        with self._lock:
            for item_id in self._ids(payload):
                self._order.remove(item_id)
                del self._entries[item_id]
            self._plan = None
        return self.listing()

    def clear(self):
        with self._lock:
            self._entries.clear()
            self._order.clear()
            self._plan = None
        return self.listing()

    def move(self, payload):
        delta = payload.get("delta")
        if delta not in (-1, 1):
            raise RenameServiceError("INVALID_INPUT", "이동 방향을 확인해 주세요.")
        with self._lock:
            ids = self._ids(payload)
            chosen = set(ids)
            order = self._order if delta < 0 else list(reversed(self._order))
            for index in range(1, len(order)):
                if order[index] in chosen and order[index - 1] not in chosen:
                    order[index - 1], order[index] = order[index], order[index - 1]
            self._order = order if delta < 0 else list(reversed(order))
        return self.listing()

    def sort(self, payload):
        key, reverse = payload.get("key", "name"), payload.get("reverse", False)
        if key not in SORT_KEYS or not isinstance(reverse, bool):
            raise RenameServiceError("INVALID_INPUT", "정렬 기준을 확인해 주세요.")
        getters = {"name": lambda e: natural_key(e.name), "path": lambda e: natural_key(e.path),
                   "size": lambda e: e.size, "mtime": lambda e: e.mtime, "ctime": lambda e: e.ctime}
        with self._lock:
            self._order.sort(key=lambda i: getters[key](self._entries[i]), reverse=reverse)
        return self.listing()

    # ── 미리보기·적용·되돌리기 ───────────────────────────────────────────
    def preview(self, payload):
        rules = payload.get("rules", [])
        overrides = payload.get("overrides") or {}
        excluded = payload.get("excluded") or []
        if not isinstance(overrides, dict) or not all(isinstance(k, str) and isinstance(v, str) and len(v) <= 255
                                                      for k, v in overrides.items()):
            raise RenameServiceError("INVALID_INPUT", "직접 고친 이름을 확인해 주세요.")
        if not isinstance(excluded, list):
            raise RenameServiceError("INVALID_INPUT", "제외 항목을 확인해 주세요.")
        with self._lock:
            entries = [self._entries[i] for i in self._order]
            try:
                plan = build_plan(entries, rules, overrides=overrides, excluded=excluded)
            except RuleError as error:
                raise RenameServiceError("RENAME_INVALID_RULE", str(error)) from None
            self._plan = plan
        items = [dict(id=i["id"], new_name=i["new_name"], status=i["status"], reason=i["reason"],
                      warnings=i["warnings"], overridden=i["overridden"]) for i in plan["items"]]
        return dict(ok=True, plan_id=plan["plan_id"], items=items, summary=plan["summary"])

    def apply(self, payload):
        with self._lock:
            plan = self._plan
            if plan is None or payload.get("plan_id") != plan["plan_id"]:
                raise RenameServiceError("RENAME_PLAN_STALE", "미리보기가 바뀌었습니다. 다시 확인해 주세요.")
            if plan["summary"]["executables"] and payload.get("confirm_executables") is not True:
                raise RenameServiceError("RENAME_CONFIRM", "실행 파일 이름 변경을 확인해 주세요.")
            if not plan["summary"]["ok"]:
                raise RenameServiceError("RENAME_NOTHING", "바꿀 항목이 없습니다.")
            try:
                result = execute_plan(plan, self.history)
            except PlanStaleError as error:
                self._plan = None
                raise RenameServiceError("RENAME_PLAN_STALE", str(error)) from None
            self._refresh([d["id"] for d in result["done"]], {d["id"]: d["path"] for d in result["done"]})
            self._plan = None
            self._last_run = result["run_id"]
        self._prune()
        return dict(self.listing(), run_id=result["run_id"], done=len(result["done"]), failed=result["failed"],
                    skipped=len(result["skipped"]))

    def undo(self, payload):
        run_id = payload.get("run_id") or self._last_run
        if not isinstance(run_id, str):
            raise RenameServiceError("RENAME_NO_HISTORY", "되돌릴 작업이 없습니다.")
        try:
            result = undo(self.history, run_id)
        except KeyError:
            raise RenameServiceError("RENAME_NO_HISTORY", "되돌릴 작업을 찾지 못했습니다.") from None
        with self._lock:
            run = self.history.get(result["run_id"])
            moved = {item_id: item["current"] for item_id, item in (run or {}).get("items", {}).items()}
            self._refresh(list(moved), moved)
            if run_id == self._last_run:
                self._last_run = None
            self._plan = None
        return dict(self.listing(), run_id=result["run_id"], done=len(result["done"]), failed=result["failed"])

    def _refresh(self, ids, new_paths):
        """이름이 바뀐 목록 항목의 경로·시각을 새로 읽는다(같은 id 유지)."""
        for item_id in ids:
            if item_id not in self._entries or item_id not in new_paths:
                continue
            try:
                self._entries[item_id] = Entry.from_path(new_paths[item_id], item_id)
            except OSError:
                pass

    def history_list(self, payload):
        limit = payload.get("limit", 20)
        if not isinstance(limit, int) or not 1 <= limit <= 200:
            raise RenameServiceError("INVALID_INPUT", "개수를 확인해 주세요.")
        runs = []
        for run in self.history.runs(limit=limit):
            names = [os.path.basename(item["original"]) for item in run["items"].values()]
            runs.append(dict(id=run["id"], kind=run["kind"], when=run["when"], count=len(names),
                             first_name=names[0] if names else "", undone=run["undone"]))
        return dict(ok=True, runs=runs)

    def _prune(self):
        try:
            self.history.prune()
        except OSError:
            pass

    # ── 규칙 세트 ─────────────────────────────────────────────────────────
    def _ruleset_path(self):
        return self.folder / "rulesets.json"

    def _load_rulesets(self):
        try:
            data = json.loads(self._ruleset_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = None
        return data if isinstance(data, dict) else dict(DEFAULT_RULESETS)

    def _save_rulesets(self, data):
        self.folder.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=self.folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=1)
            os.replace(temp, self._ruleset_path())
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    def rulesets(self, action, payload):
        data = self._load_rulesets()
        if action == "ruleset_list":
            return dict(ok=True, rulesets=[dict(name=k, rules=v) for k, v in data.items()])
        name = payload.get("name")
        if not isinstance(name, str) or not RULESET_NAME.match(name) or name != name.strip():
            raise RenameServiceError("INVALID_INPUT", "규칙 세트 이름은 40자 이내로 입력해 주세요.")
        if action == "ruleset_save":
            try:
                validate_rules(payload.get("rules"))
            except RuleError as error:
                raise RenameServiceError("RENAME_INVALID_RULE", str(error)) from None
            if name not in data and len(data) >= 100:
                raise RenameServiceError("INVALID_INPUT", "규칙 세트는 100개까지 저장할 수 있습니다.")
            data[name] = payload["rules"]
        elif action == "ruleset_delete":
            data.pop(name, None)
        self._save_rulesets(data)
        return dict(ok=True, rulesets=[dict(name=k, rules=v) for k, v in data.items()])

    # ── 진입점 ────────────────────────────────────────────────────────────
    def command(self, action, payload=None):
        payload = payload if isinstance(payload, dict) else {}
        try:
            if action == "list":
                return self.listing()
            if action == "pick_files":
                paths = self._pick("rename_files", "open", True)
                return self.listing() if paths is None else self.add_paths(paths)
            if action == "pick_folder":
                paths = self._pick("rename_folder", "directory", False)
                return self.listing() if paths is None else self.add_paths(
                    paths, recursive=payload.get("recursive") is True,
                    include_hidden=payload.get("include_hidden") is True,
                    as_folder=payload.get("as_folder") is True)
            if action == "remove":
                return self.remove(payload)
            if action == "clear":
                return self.clear()
            if action == "move":
                return self.move(payload)
            if action == "sort":
                return self.sort(payload)
            if action == "preview":
                return self.preview(payload)
            if action == "apply":
                return self.apply(payload)
            if action == "undo":
                return self.undo(payload)
            if action == "history":
                return self.history_list(payload)
            if action in ("ruleset_list", "ruleset_save", "ruleset_delete"):
                return self.rulesets(action, payload)
            raise RenameServiceError("NOT_AVAILABLE", "지원하지 않는 명령입니다.")
        except RenameServiceError as error:
            return dict(ok=False, code=error.code, message=str(error))
        except Exception as error:  # 선택 창 오류(ServiceError) 등: 화면에 이유만 보인다.
            code = getattr(error, "code", "RENAME_FAILED")
            return dict(ok=False, code=code, message=str(error) or "이름 바꾸기를 처리하지 못했습니다.")
