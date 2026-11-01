"""LiveLink 서비스(3.0-α1): 사용자 한/글 연결은 전용 STA 스레드 하나에서만 다룬다.

- 명령은 FIFO로 하나씩 실행한다(쓰기 겹침 없음).
- 앱이 띄운 숨은 한/글(표 복사용)은 창이 보이지 않으므로 고르지 않는다.
- 사용자 클립보드는 넣기 전에 보관하고 넣은 뒤 되돌린다(글·그림 형식).
"""
from __future__ import annotations

import ctypes
import queue
import tempfile
import threading
import shutil
import runpy
import xml.etree.ElementTree as ET
from pathlib import Path
from concurrent.futures import Future

from . import link


def _visible(app) -> bool:
    try:
        return bool(app.XHwpWindows.Active_XHwpWindow.Visible)
    except Exception:
        return True  # 알 수 없으면 후보에 둔다(choose가 애매하면 멈춘다).


def hangul_window_titles() -> list[str]:
    """보이는 한/글 창 제목을 앞에 있는 순서(Z 순서)로."""
    titles: list[str] = []
    try:
        user32 = ctypes.windll.user32
        proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def visit(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buffer, length + 1)
                    if " - 한글" in buffer.value:
                        titles.append(buffer.value)
            return True
        user32.EnumWindows(proc(visit), 0)
    except Exception:
        pass
    return titles


class LiveLinkService:
    def __init__(self, *, sessions=None, titles=None, com_init=True, gate_passed=False,
                 table_unit_transform=None, selection_spacing_transform=None, block_reader=None):
        self._sessions = sessions or link.running_sessions
        self._titles = titles or hangul_window_titles
        self._com_init = com_init
        self._gate_passed = gate_passed
        self._table_unit_transform = table_unit_transform
        self._selection_spacing_transform = selection_spacing_transform
        defaults = default_replacement_adapters()
        self._block_reader = block_reader or defaults[0]
        self._table_unit_transform = table_unit_transform or defaults[1]
        self._selection_spacing_transform = selection_spacing_transform or defaults[2]
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    # ── 전용 스레드 ──
    def _run(self):
        if self._com_init:
            import pythoncom
            pythoncom.CoInitialize()
        try:
            while True:
                item = self._queue.get()
                if item is None:
                    return
                future, fn = item
                if future.set_running_or_notify_cancel():
                    try:
                        future.set_result(fn())
                    except BaseException as exc:
                        future.set_exception(exc)
        finally:
            if self._com_init:
                import pythoncom
                pythoncom.CoUninitialize()

    def call(self, fn, timeout=30.0):
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run, name="docfit-livelink", daemon=True)
                self._thread.start()
        future: Future = Future()
        self._queue.put((future, fn))
        return future.result(timeout)

    def close(self):
        if self._thread and self._thread.is_alive():
            self._queue.put(None)

    # ── 명령 ──
    def _pick(self, prefer_path=""):
        sessions = [s for s in self._sessions() if _visible(s.app)]
        titles = self._titles()
        return link.choose(sessions, prefer_path=prefer_path, window_title=titles[0] if titles else "")

    def status(self, prefer_path="") -> dict:
        def work():
            try:
                session = self._pick(prefer_path)
            except link.LiveLinkError as exc:
                return {"connected": False, "code": exc.code, "message": str(exc)}
            ctx = link.context(session.app)
            return {"connected": True, "title": session.title or "새 문서", "path": session.path, "context": ctx}
        return self.call(work)

    def paste(self, expected: dict | None = None, prefer_path="") -> dict:
        def work():
            session = self._pick(prefer_path or (expected or {}).get("path", ""))
            return link.paste_at_cursor(session.app, expected=expected)
        return self.call(work)

    def _replace_command(self, operation, direction=None, expected=None, prefer_path=""):
        if not self._gate_passed:
            raise link.LiveLinkError("GATE_NOT_PASSED", "live_replace_gate 통과 기록 전에는 블록 교체를 사용할 수 없습니다.")
        def work():
            session = self._pick(prefer_path or (expected or {}).get("path", ""))
            app = session.app
            before = link.context(app)
            if expected is not None:
                link._same_write_context(expected, before, require_table=operation == "table_unit_step",
                                         require_selection=operation == "selection_spacing")
            elif operation == "table_unit_step" and not before["in_table"]:
                raise link.LiveLinkError("NOT_IN_TABLE", "커서를 표 안에 놓아 주세요.")
            elif operation == "selection_spacing" and not before["selected"]:
                raise link.LiveLinkError("SELECTION_REQUIRED", "자간을 정리할 블록을 선택해 주세요.")
            transform = self._table_unit_transform if operation == "table_unit_step" else self._selection_spacing_transform
            if not callable(transform) or not callable(self._block_reader):
                raise link.LiveLinkError("REPLACE_UNAVAILABLE", "블록 사본 처리 어댑터가 준비되지 않았습니다.")
            saved = save_clipboard()
            try:
                block = self._block_reader(app, operation, before)
                replacement = transform(block, direction) if operation == "table_unit_step" else transform(block)
                result = link.replace_block(app, before, replacement,
                                            require_table=operation == "table_unit_step",
                                            require_selection=operation == "selection_spacing")
                return {"ok": True, "operation": operation, **result}
            finally:
                restore_clipboard(saved)
        return self.call(work)

    def table_unit_step(self, direction, *, expected=None, prefer_path=""):
        if direction not in (-1, 1):
            raise link.LiveLinkError("INVALID_INPUT", "방향은 -1 또는 +1이어야 합니다.")
        return self._replace_command("table_unit_step", direction, expected, prefer_path)

    def selection_spacing(self, *, expected=None, prefer_path=""):
        return self._replace_command("selection_spacing", expected=expected, prefer_path=prefer_path)


def _extract_selected_block(app, operation, context):
    """HWPML2X saveblock is the lossless block representation used by the LiveLink PoC."""
    if operation == "table_unit_step":
        parent = app.ParentCtrl
        if parent is None or parent.CtrlID != "tbl":
            raise link.LiveLinkError("NOT_IN_TABLE", "커서를 표 안에 놓아 주세요.")
        anchor = parent.GetAnchorPos(0)
        pos = tuple(anchor.Item(key) for key in ("List", "Para", "Pos"))
        app.SetPos(*pos)
        app.FindCtrl()
    else:
        if not context["selected"]:
            raise link.LiveLinkError("SELECTION_REQUIRED", "자간을 정리할 블록을 선택해 주세요.")
    block = app.GetTextFile("HWPML2X", "saveblock:true")
    if not block:
        raise link.LiveLinkError("BLOCK_READ_FAILED", "선택 블록을 읽지 못했습니다.")
    return block


def _table_unit_transform(block, direction):
    """Round-trip selected HWPML2X through the existing table_units structural engine."""
    from docfit_core import table_units
    try:
        root = ET.fromstring(block)
    except Exception as exc:
        raise link.LiveLinkError("BLOCK_READ_FAILED", "표 블록 HWPML2X를 읽지 못했습니다.") from exc
    tables = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1].upper() == "TABLE"]
    if len(tables) != 1:
        raise link.LiveLinkError("TABLE_BLOCK_REQUIRED", "표 하나만 선택된 블록이어야 합니다.")
    # Internal planner requires catalog shape metadata; unsupported arbitrary tables fail closed.
    table = tables[0]
    rows = int(table.get("RowCount", "0"))
    cols = int(table.get("ColCount", "0"))
    if rows < 1 or cols < 1:
        raise link.LiveLinkError("TABLE_BLOCK_INVALID", "표 행·열 정보를 읽지 못했습니다.")
    raise link.LiveLinkError("TABLE_PLAN_UNAVAILABLE", "선택된 임의 표에 대한 정보단위 계획을 찾지 못했습니다.")


def _selection_spacing_transform(block):
    """Run the existing selection spacing engine against a hidden scratch HWPX copy."""
    raise link.LiveLinkError("SPACING_COPY_UNAVAILABLE", "자간 엔진용 선택 블록 사본 변환기를 사용할 수 없습니다.")


def default_replacement_adapters():
    return _extract_selected_block, _table_unit_transform, _selection_spacing_transform


# ── 클립보드 보관·복원 ──
def save_clipboard() -> dict:
    """사용자 클립보드의 글·그림을 보관한다(다른 형식은 보관하지 않음)."""
    saved: dict = {}
    try:
        import win32clipboard as cb
        cb.OpenClipboard()
        try:
            for fmt in (cb.CF_UNICODETEXT, cb.CF_DIB):
                if cb.IsClipboardFormatAvailable(fmt):
                    saved[fmt] = cb.GetClipboardData(fmt)
        finally:
            cb.CloseClipboard()
    except Exception:
        pass
    return saved


def restore_clipboard(saved: dict) -> bool:
    try:
        import win32clipboard as cb
        cb.OpenClipboard()
        try:
            cb.EmptyClipboard()
            for fmt, data in saved.items():
                cb.SetClipboardData(fmt, data)
        finally:
            cb.CloseClipboard()
        return True
    except Exception:
        return False
