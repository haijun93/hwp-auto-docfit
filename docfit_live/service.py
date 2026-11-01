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
    """Adjust one unit in a selected HWPML2X table using table_units rules."""
    from docfit_core import table_units
    try:
        root = ET.fromstring(block)
        tables = [n for n in root.iter() if n.tag.rsplit("}", 1)[-1].lower() in ("table", "tbl")]
        if len(tables) != 1:
            raise ValueError("one table required")
        table = tables[0]
        hp = table_units.HP
        aliases = {"row": "tr", "cell": "tc", "celladdr": "cellAddr", "cellspan": "cellSpan",
                   "cellsz": "cellSz", "para": "p", "run": "run", "text": "t"}
        attr_alias = {"rowcount": "rowCnt", "colcount": "colCnt", "rowcnt": "rowCnt", "colcnt": "colCnt",
                      "rowaddr": "rowAddr", "coladdr": "colAddr", "rowspan": "rowSpan", "colspan": "colSpan"}
        for node in table.iter():
            key = node.tag.rsplit("}", 1)[-1].lower()
            if key in aliases:
                node.tag = hp + aliases[key]
            for name, value in list(node.attrib.items()):
                target = attr_alias.get(name.lower())
                if target:
                    node.set(target, value)
        cells = list(table.iter(hp + "tc"))
        if not cells:
            raise ValueError("no cells")
        rows = int(table.get("rowCnt", "0")); cols = int(table.get("colCnt", "0"))
        if rows < 1 or cols < 1:
            coords = []
            for i, cell in enumerate(cells):
                addr, span = cell.find(hp + "cellAddr"), cell.find(hp + "cellSpan")
                r = int(addr.get("rowAddr", i)) if addr is not None else i
                c = int(addr.get("colAddr", 0)) if addr is not None else 0
                rs = int(span.get("rowSpan", 1)) if span is not None else 1
                cs = int(span.get("colSpan", 1)) if span is not None else 1
                coords.append((r + rs, c + cs))
            rows, cols = max(x[0] for x in coords), max(x[1] for x in coords)
        table.set("rowCnt", str(rows)); table.set("colCnt", str(cols))
        meta = [table_units.catalog._cell_meta(c, 0, 0, "", None) for c in cells]
        plan = table_units.plan_for({"cell_meta": meta, "rows": rows, "cols": cols})
        axis = "col" if plan["col"] else "row" if plan["row"] else None
        if axis is None:
            raise ValueError("no matching information-unit plan")
        target = plan[axis]["count"] + direction
        table_units.resize_table(table, plan,
            row_count=target if axis == "row" else None,
            col_count=target if axis == "col" else None)
        return ET.tostring(root, encoding="unicode")
    except link.LiveLinkError:
        raise
    except Exception as exc:
        raise link.LiveLinkError("UNSUPPORTED_TABLE", "The table block could not be parsed or its unit structure was unsupported.") from exc


def _selection_spacing_transform(block):
    raise link.LiveLinkError("SPACING_COPY_UNAVAILABLE", "선택 자간 정리는 아직 한/글 사본 연결이 끝나지 않았습니다.")


def transform_selection_spacing(block, *, save_block, open_copy, spacing_engine, extract_block):
    """Call stages in order: save block, open copy, spacing engine, extract block."""
    saved = save_block(block)
    copy_doc = open_copy(saved)
    try:
        spacing_engine(copy_doc)
        return extract_block(copy_doc)
    finally:
        close = getattr(copy_doc, "Close", None)
        if callable(close):
            close()


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
