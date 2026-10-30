"""LiveLink 서비스(3.0-α1): 사용자 한/글 연결은 전용 STA 스레드 하나에서만 다룬다.

- 명령은 FIFO로 하나씩 실행한다(쓰기 겹침 없음).
- 앱이 띄운 숨은 한/글(표 복사용)은 창이 보이지 않으므로 고르지 않는다.
- 사용자 클립보드는 넣기 전에 보관하고 넣은 뒤 되돌린다(글·그림 형식).
"""
from __future__ import annotations

import ctypes
import queue
import threading
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
    def __init__(self, *, sessions=None, titles=None, com_init=True):
        self._sessions = sessions or link.running_sessions
        self._titles = titles or hangul_window_titles
        self._com_init = com_init
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
