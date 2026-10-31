"""계획(Plan) 만들기와 안전 검사. 파일 시스템은 읽기만 한다."""
from __future__ import annotations

import hashlib
import json
import os

from .rules import apply_rules

FORBIDDEN = set('\\/:*?"<>|')
RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
EXECUTABLE_EXTS = {".exe", ".bat", ".cmd", ".ps1", ".lnk", ".dll", ".sys", ".msi", ".vbs", ".js", ".com", ".scr"}
MAX_NAME = 255
LONG_PATH_WARN = 260
MAX_PATH = 32767


def invalid_name_reason(name):
    """Windows에서 쓸 수 없는 이름이면 이유, 쓸 수 있으면 None."""
    if not name or not name.strip():
        return "이름이 비어 있습니다."
    if any(ch in FORBIDDEN for ch in name):
        return '쓸 수 없는 글자(\\ / : * ? " < > |)가 있습니다.'
    if any(ord(ch) < 32 for ch in name):
        return "제어 문자가 있습니다."
    if name.split(".")[0].rstrip(" ").upper() in RESERVED:
        return "Windows 예약 이름(CON·NUL·COM1 등)입니다."
    if name[-1] in ". ":
        return "이름 끝에 마침표나 공백을 쓸 수 없습니다."
    if len(name) > MAX_NAME:
        return f"이름이 {MAX_NAME}자를 넘습니다."
    return None


def _key(path):
    return os.path.normcase(os.path.normpath(path)).casefold()


def build_plan(entries, rules, *, overrides=None, excluded=(), exists=os.path.lexists, today=None, exif_reader=None):
    """미리보기 계획. 항목 상태: ok·unchanged·conflict·invalid·skipped.

    overrides: {entry_id: 새 이름} — 사용자가 직접 고친 이름(규칙 결과를 덮어씀).
    """
    overrides = overrides or {}
    excluded = set(excluded)
    results = apply_rules(entries, rules, today=today, exif_reader=exif_reader)
    items = []
    for entry, (new_name, error, warnings) in zip(entries, results):
        item = dict(id=entry.id, old_path=entry.path, old_name=entry.name, new_name=new_name, new_path=None,
                    status="ok", reason=None, warnings=sorted(warnings), overridden=entry.id in overrides,
                    fingerprint=list(entry.fingerprint()))
        if entry.id in overrides:
            item["new_name"] = new_name = overrides[entry.id]
        if entry.id in excluded:
            item.update(status="skipped", reason="목록에서 제외했습니다.")
        elif error:
            item.update(status="invalid", reason=error)
        elif not isinstance(new_name, str) or invalid_name_reason(new_name):
            item.update(status="invalid", reason=invalid_name_reason(new_name if isinstance(new_name, str) else ""))
        else:
            item["new_path"] = os.path.join(entry.folder, new_name)
            if new_name == entry.name:
                item["status"] = "unchanged"
            elif len(item["new_path"]) > MAX_PATH:
                item.update(status="invalid", reason="경로가 너무 깁니다.")
            else:
                if len(item["new_path"]) >= LONG_PATH_WARN:
                    item["warnings"].append("long_path")
                old_ext, new_ext = entry.ext.lower(), os.path.splitext(new_name)[1].lower()
                if old_ext != new_ext:
                    item["warnings"].append("ext_changed")
                if old_ext in EXECUTABLE_EXTS or new_ext in EXECUTABLE_EXTS:
                    item["warnings"].append("executable")
        items.append(item)
    _mark_conflicts(items, exists)
    summary = {status: 0 for status in ("ok", "unchanged", "conflict", "invalid", "skipped")}
    for item in items:
        summary[item["status"]] += 1
    summary["executables"] = sum("executable" in item["warnings"] for item in items if item["status"] == "ok")
    return dict(plan_id=_plan_id(items), items=items, summary=summary)


def _mark_conflicts(items, exists):
    """목록 안 중복과 디스크의 다른 파일과의 충돌. 상태가 바뀌면 다시 검사한다(연쇄 충돌)."""
    changed = True
    while changed:
        changed = False
        moving = {_key(i["old_path"]) for i in items if i["status"] == "ok"}
        staying = {_key(i["old_path"]) for i in items if i["status"] != "ok"}
        targets = {}
        for item in items:
            if item["status"] == "ok":
                targets.setdefault(_key(item["new_path"]), []).append(item)
        for key, group in targets.items():
            if len(group) > 1:
                for item in group:
                    item.update(status="conflict", reason="목록 안에서 새 이름이 겹칩니다.")
                changed = True
                continue
            item = group[0]
            if key == _key(item["old_path"]):
                continue  # 대소문자만 바뀜: 실행기가 임시 이름을 거친다.
            if key in staying or (key not in moving and exists(item["new_path"])):
                item.update(status="conflict", reason="같은 이름의 파일이 이미 있습니다.")
                changed = True


def _plan_id(items):
    payload = [(i["old_path"], i["new_path"], i["status"], i["fingerprint"]) for i in items]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode("utf-8")).hexdigest()[:32]
