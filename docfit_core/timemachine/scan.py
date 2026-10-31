"""조사 폴더 증분 스캔. 파일 내용은 읽지 않고 메타데이터(크기·수정·생성 시각)만 본다.

Windows의 os.scandir는 디렉터리 목록과 함께 stat 정보를 주므로 파일마다 추가 호출이 없다.
변경 없는 파일은 쓰지 않는다(변경 없음 = DB 쓰기 0).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .rules import Rules, cloud_only
from .store import path_key

CHUNK = 500


@dataclass
class ScanResult:
    seen: int = 0
    written: int = 0
    removed: int = 0
    skipped_dirs: int = 0
    errors: list = field(default_factory=list)
    cancelled: bool = False


def _stat_times(info):
    ctime = getattr(info, "st_birthtime", None) or info.st_ctime
    return info.st_mtime, ctime


def scan_root(store, root, rules=None, *, cancel=None, progress=None, chunk=CHUNK):
    """root 아래를 훑어 색인을 갱신한다. cancel()이 참이면 지금까지 한 것만 쓰고 멈춘다(삭제 정리는 생략)."""
    rules = rules or Rules()
    root = os.path.abspath(root)
    result = ScanResult()
    known = store.known(root)
    seen_keys = set()
    pending = []
    stack = [root]
    while stack:
        if cancel and cancel():
            result.cancelled = True
            break
        folder = stack.pop()
        try:
            iterator = os.scandir(folder)
        except OSError as error:
            result.errors.append((folder, error.__class__.__name__))
            continue
        with iterator:
            for item in iterator:
                try:
                    if item.is_symlink():
                        continue
                    info = item.stat(follow_symlinks=False)
                    attributes = getattr(info, "st_file_attributes", 0)
                    if item.is_dir(follow_symlinks=False):
                        if attributes & 0x400 or rules.skip_dir(item.name, attributes):  # 0x400 = 정션
                            result.skipped_dirs += 1
                        else:
                            stack.append(item.path)
                        continue
                    if rules.skip_file(item.name, attributes):
                        continue
                except OSError as error:
                    result.errors.append((item.path, error.__class__.__name__))
                    continue
                key = path_key(item.path)
                seen_keys.add(key)
                result.seen += 1
                mtime, ctime = _stat_times(info)
                if known.get(key) == (info.st_size, mtime, ctime):
                    continue
                work_time, flags = rules.work_time(ctime, mtime)
                pending.append(dict(path=item.path, root=root, name=item.name, kind=rules.kind(item.name),
                                    size=info.st_size, mtime=mtime, ctime=ctime, work_time=work_time, flags=flags,
                                    cloud=cloud_only(attributes)))
                if len(pending) >= chunk:
                    result.written += store.upsert_many(pending)
                    pending = []
                    if progress:
                        progress(result)
    result.written += store.upsert_many(pending)
    if not result.cancelled:
        gone = [key for key in known if key not in seen_keys]
        result.removed = store.delete_keys(gone) if gone else 0
    if progress:
        progress(result)
    return result


def scan_roots(store, roots, rules=None, *, cancel=None, progress=None):
    """여러 조사 폴더. 목록에서 빠진 폴더의 색인은 따로 drop_root로 지운다."""
    total = ScanResult()
    for root in roots:
        part = scan_root(store, root, rules, cancel=cancel, progress=progress)
        total.seen += part.seen
        total.written += part.written
        total.removed += part.removed
        total.skipped_dirs += part.skipped_dirs
        total.errors.extend(part.errors)
        if part.cancelled:
            total.cancelled = True
            break
    return total


def default_roots(home=None, environ=None):
    """사용자 결정 1: 바탕 화면·문서 폴더(OneDrive로 옮겨진 경우 포함). 다운로드는 기본 제외."""
    home = home or os.path.expanduser("~")
    environ = os.environ if environ is None else environ
    candidates = []
    for name in ("Desktop", "Documents", "바탕 화면", "문서"):
        for base in (home, environ.get("OneDrive") or "", environ.get("OneDriveCommercial") or ""):
            if base:
                candidates.append(os.path.join(base, name))
    seen, roots = set(), []
    for path in candidates:
        key = path_key(path)
        if key not in seen and os.path.isdir(path):
            seen.add(key)
            roots.append(path)
    return roots
