"""자료함 폴더 스캔 서비스: klib(box_scan)를 우선 쓰고, 쓸 수 없으면 기존 Python 증분 스캔으로 되돌아간다.

두 경로는 같은 명령(box_scan·box_scan_status·box_scan_cancel·box_scan_files)과 같은 상태 모양을 낸다.
폴백은 `LibraryService.index`를 그대로 호출하며 그 동작은 바꾸지 않는다. 원본 파일은 열지 않는다.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

from .library_bridge import LibraryBridgeError
from .library_service import ALLOWED_EXTENSIONS, LibraryService

SCAN_COMMANDS = frozenset({"box_scan", "box_scan_status", "box_scan_cancel", "box_scan_files"})
_PAGE = 1000


def default_fallback_db():
    base = os.environ.get("KLIB_TEST_ROOT") or os.path.join(
        os.environ.get("LOCALAPPDATA") or ".", "HwpAutoDocFit", "library")
    return Path(base) / "scan_fallback.db"


def _normalize_root(path):
    text = str(path or "").strip()
    stripped = text.rstrip("\\/")
    return stripped or text


def _idle():
    return {"ok": True, "state": "idle", "phase": "", "backend": None, "box_id": 0, "root": "",
            "discovered": 0, "total": 0, "processed": 0, "changed": 0, "removed": 0,
            "skipped_errors": 0, "message": "", "elapsed_ms": 0}


class FolderScanService:
    def __init__(self, bridge_factory=None, *, fallback_db=None, extensions=ALLOWED_EXTENSIONS):
        self._bridge_factory = bridge_factory
        self._fallback_db = fallback_db
        self._extensions = sorted(str(e).lower() for e in extensions)
        self._lock = threading.Lock()
        self._active = None          # "klib" | "python" | None
        self._py = _idle()
        self._py_cancel = threading.Event()
        self._py_thread = None
        self._service = None

    # ---- 명령 진입점 -------------------------------------------------
    def handle(self, request):
        cmd = request.get("cmd")
        try:
            if cmd == "box_scan":
                return self.start(request.get("box_id"), request.get("path"))
            if cmd == "box_scan_status":
                return self.status()
            if cmd == "box_scan_cancel":
                return self.cancel()
            if cmd == "box_scan_files":
                return {"ok": True, "files": self.files(request.get("box_id"), request.get("path"))}
        except (ValueError, RuntimeError) as exc:
            return {"ok": False, "message": str(exc)}
        return {"ok": False, "message": "허용되지 않은 폴더 스캔 명령입니다."}

    # ---- klib 선택 ----------------------------------------------------
    def _bridge(self):
        try:
            bridge = self._bridge_factory() if self._bridge_factory else None
        except Exception:
            return None
        if bridge is None:
            return None
        available = getattr(bridge, "available", None)
        if available is not None and not available():
            return None
        return bridge

    def _fallback_service(self):
        if self._service is None:
            self._service = LibraryService(self._fallback_db or default_fallback_db())
        return self._service

    # ---- 시작·상태·취소 ----------------------------------------------
    def start(self, box_id, path):
        if type(box_id) is not int:
            raise ValueError("자료함을 선택해 주세요.")
        root = _normalize_root(path)
        if not root:
            raise ValueError("스캔할 폴더를 지정해 주세요.")
        if self._py_thread is not None and self._py_thread.is_alive():
            return {"ok": False, "message": "이미 폴더 스캔이 진행 중입니다."}
        bridge = self._bridge()
        if bridge is not None:
            try:
                reply = bridge.request({"cmd": "box_scan", "box_id": box_id, "path": root,
                                        "extensions": self._extensions})
            except LibraryBridgeError:
                reply = None      # klib에 닿지 못함 → 기존 Python 스캔으로 폴백
            if reply is not None:
                if reply.get("ok") is True:
                    self._active = "klib"
                    return dict(reply, backend="klib")
                return reply     # 폴더 오류·이미 진행 중 등은 klib의 판단을 그대로 돌려준다
        return self._start_python(box_id, root)

    def _start_python(self, box_id, root):
        service = self._fallback_service()
        name = f"box-{box_id}"
        library = next((x for x in service.store.list_libraries() if x["name"] == name), None) \
            or service.create(name, "klib 없이 스캔한 자료함 폴더")
        service.add_folder(library["id"], root)   # 폴더가 아니거나 링크면 ValueError
        self._py_cancel.clear()
        started = time.monotonic()
        self._py = dict(_idle(), state="scanning", phase="enumerate", backend="python",
                        box_id=box_id, root=root)
        self._active = "python"

        def progress(found):
            self._py.update(discovered=found, elapsed_ms=int((time.monotonic() - started) * 1000))

        def run():
            try:
                result = service.index(library["id"], cancel=self._py_cancel, progress=progress)
            except Exception as exc:      # 스레드 안의 오류는 상태로만 알린다
                self._py.update(state="error", phase="", message=str(exc))
                return
            done = {"state": "cancelled" if result.get("cancelled") else "done", "phase": "",
                    "changed": result.get("indexed", 0), "removed": result.get("removed", 0),
                    "skipped_errors": len(result.get("errors", [])),
                    "elapsed_ms": int((time.monotonic() - started) * 1000)}
            if not result.get("cancelled"):
                total = len(self._list_python(library["id"], root))
                done.update(discovered=total, total=total, processed=total)
            else:
                done["message"] = "취소됨."
            self._py.update(done)

        self._py_thread = threading.Thread(target=run, name="library-scan-py", daemon=True)
        self._py_thread.start()
        return {"ok": True, "started": True, "backend": "python"}

    def status(self):
        if self._active == "klib":
            bridge = self._bridge()
            if bridge is None:
                return dict(_idle(), ok=False, state="error", backend="klib", message="klib를 사용할 수 없습니다.")
            try:
                reply = bridge.request({"cmd": "box_scan_status"})
            except LibraryBridgeError as exc:
                return dict(_idle(), ok=False, state="error", backend="klib", message=str(exc))
            out = dict(reply, backend="klib")
            out["changed"] = int(reply.get("added", 0)) + int(reply.get("updated", 0))
            return out
        return dict(self._py)

    def cancel(self):
        if self._active == "klib":
            bridge = self._bridge()
            if bridge is None:
                return {"ok": True, "cancelling": False}
            try:
                return bridge.request({"cmd": "box_scan_cancel"})
            except LibraryBridgeError as exc:
                return {"ok": False, "message": str(exc)}
        running = self._py_thread is not None and self._py_thread.is_alive()
        if running:
            self._py_cancel.set()
        return {"ok": True, "cancelling": running}

    def close(self):
        self.wait(5.0)
        if self._service is not None:
            self._service.close()
            self._service = None

    def wait(self, timeout=30.0):
        """시험·종료용: Python 폴백 스레드가 끝나길 기다린다(klib는 상태를 폴링)."""
        thread = self._py_thread
        if thread is not None:
            thread.join(timeout)

    # ---- 결과 파일 목록 ------------------------------------------------
    def files(self, box_id, path):
        if type(box_id) is not int:
            raise ValueError("자료함을 선택해 주세요.")
        root = _normalize_root(path)
        if self._active == "klib":
            bridge = self._bridge()
            if bridge is None:
                raise RuntimeError("klib를 사용할 수 없습니다.")
            out, offset = [], 0
            while True:
                reply = bridge.request({"cmd": "box_scan_files", "box_id": box_id, "path": root,
                                        "offset": offset, "limit": _PAGE})
                if reply.get("ok") is not True:
                    raise RuntimeError(reply.get("message", "스캔 결과를 읽지 못했습니다."))
                rows = reply.get("files", [])
                out.extend(r["path"] for r in rows)
                if len(rows) < _PAGE:
                    return sorted(out)
                offset += _PAGE
        service = self._fallback_service()
        library = next((x for x in service.store.list_libraries() if x["name"] == f"box-{box_id}"), None)
        return self._list_python(library["id"], root) if library else []

    def _list_python(self, library_id, root):
        service = self._fallback_service()
        out, offset = [], 0
        prefix = os.path.normcase(os.path.abspath(root))
        while True:
            rows = service.search(library_id, "", None, _PAGE, offset)
            out.extend(r["path"] for r in rows
                       if os.path.normcase(r["path"]).startswith(prefix.rstrip("\\/") + os.sep))
            if len(rows) < _PAGE:
                return sorted(out)
            offset += _PAGE
