"""On-demand metadata indexing and filename search for v4.0 libraries."""

from __future__ import annotations

import os

import stat

import threading

from pathlib import Path

from docfit_core.library import LibraryStore

from docfit_core.library.store import path_key

ALLOWED_EXTENSIONS = frozenset({".hwp", ".hwpx", ".docx", ".doc", ".xlsx", ".xls",

                                ".pptx", ".ppt", ".pdf", ".txt", ".md", ".png",

                                ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"})

class LibraryService:

    """Explicit-root library operations. Scans run only when requested."""

    def __init__(self, db_path, *, extensions=ALLOWED_EXTENSIONS):

        self.store = LibraryStore(db_path)

        self.extensions = frozenset(str(ext).lower() for ext in extensions)

        self._lock = threading.Lock()

    def close(self):

        self.store.close()

    def create(self, name, description=""):

        return self.store.create(name, description)

    def add_folder(self, library_id, folder):

        path = os.path.abspath(os.fspath(folder))

        try:

            info = os.lstat(path)

        except OSError as exc:

            raise ValueError("존재하는 폴더를 선택해 주세요.") from exc

        if (not stat.S_ISDIR(info.st_mode) or os.path.islink(path) or

                getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):

            raise ValueError("심볼릭 링크나 정션이 아닌 폴더를 선택해 주세요.")

        return self.store.add_root(library_id, path)

    def index(self, library_id, *, cancel=None):

        if not self._lock.acquire(blocking=False):

            raise RuntimeError("자료함 색인이 이미 진행 중입니다.")

        indexed, removed, skipped, errors = 0, 0, 0, []

        try:

            if not self.store.get(library_id):

                raise ValueError("자료함을 찾을 수 없습니다.")

            for root_row in self.store.roots(library_id):

                root = root_row["path"]

                found = []

                known = self.store.known_under(library_id, root)

                root_failed = False

                stack = [root]

                while stack:

                    if cancel and cancel.is_set():

                        return {"ok": False, "cancelled": True, "indexed": indexed, "removed": removed,

                                "skipped": skipped, "errors": errors}

                    current = stack.pop()

                    try:

                        with os.scandir(current) as entries:

                            for entry in entries:

                                try:

                                    info = entry.stat(follow_symlinks=False)

                                    if stat.S_ISDIR(info.st_mode):

                                        if not entry.is_symlink() and not (getattr(info, "st_file_attributes", 0) & 0x400):

                                            stack.append(entry.path)

                                    elif (stat.S_ISREG(info.st_mode) and

                                          Path(entry.name).suffix.lower() in self.extensions):

                                        metadata = {"path": entry.path, "size": info.st_size,

                                                    "mtime": info.st_mtime, "ctime": info.st_ctime}

                                        found.append(metadata)

                                        old = known.get(path_key(entry.path))

                                        if old == (info.st_size, info.st_mtime, info.st_ctime):

                                            continue

                                    else:

                                        skipped += 1

                                except OSError as exc:

                                    skipped += 1

                                    root_failed = True

                                    if len(errors) < 100:

                                        errors.append({"path": entry.path, "error": type(exc).__name__})

                    except OSError as exc:

                        skipped += 1

                        root_failed = True

                        if len(errors) < 100:

                            errors.append({"path": current, "error": type(exc).__name__})

                indexed += self.store.upsert_files(library_id, [

                    item for item in found

                    if known.get(path_key(item["path"])) != (item["size"], item["mtime"], item["ctime"])

                ])

                # A partial/permission-failed scan cannot prove files vanished.

                if not root_failed:

                    removed += self.store.remove_missing(library_id, root, [item["path"] for item in found])

            return {"ok": True, "cancelled": False, "indexed": indexed, "removed": removed,

                    "skipped": skipped, "errors": errors}

        finally:

            self._lock.release()

    def search(self, library_id, query="", extensions=None, limit=200, offset=0):

        return self.store.search(library_id, query, extensions, limit, offset)

    def command(self, action, payload):

        """Narrow application bridge contract for the first v4.0 vertical slice."""

        if not isinstance(payload, dict):

            raise ValueError("자료함 요청 형식이 올바르지 않습니다.")

        if action == "list":

            return {"ok": True, "libraries": self.store.list_libraries()}

        if action == "create":

            item = self.create(payload.get("name", ""), payload.get("description", ""))

            return {"ok": True, "library": item}

        library_id = payload.get("library_id")

        if isinstance(library_id, bool) or not isinstance(library_id, int):

            raise ValueError("자료함을 선택해 주세요.")

        if action == "add_folder":

            root = self.add_folder(library_id, payload.get("path", ""))

            return {"ok": True, "root": root}

        if action == "index":

            return self.index(library_id)

        if action == "search":

            return {"ok": True, "results": self.search(

                library_id, payload.get("query", ""), payload.get("extensions"),

                payload.get("limit", 200), payload.get("offset", 0))}

        if action == "open":

            from .library_bridge import open_library_item

            return {"ok": True, "opened": open_library_item(payload)}

        if action == "add_clipboard_image":

            import base64

            raw = base64.b64decode(payload.get("png_base64", ""), validate=True)

            path = self._save_blob(payload, raw, ".png")

            return {"ok": True, "item": self.store.add_item(payload["library_id"], path=str(path), name=payload.get("name", path.name))}

        if action == "add_formatted_text":

            raw = payload.get("html", "").encode("utf-8")

            path = self._save_blob(payload, raw, ".html")

            return {"ok": True, "item": self.store.add_item(payload["library_id"], path=str(path), name=payload.get("name", path.name))}

        raise ValueError("지원하지 않는 자료함 명령입니다.")

    def _save_blob(self, payload, data, suffix):

        import re

        import uuid

        box_id = payload.get("box_id")

        if type(box_id) is not int or not self.store.get(box_id):

            raise ValueError("자료함을 찾을 수 없습니다.")

        folder = Path(self.store._path).parent / "boxes" / str(box_id) / "items"

        folder.mkdir(parents=True, exist_ok=True)

        name = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "_", str(payload.get("name") or "자료"))[:100]

        target = folder / f"{name}-{uuid.uuid4().hex[:8]}{suffix}"

        target.write_bytes(data)

        return target
