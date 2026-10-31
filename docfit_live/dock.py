"""Win32 창 추적 및 한글 도우미 패널 배치."""
from __future__ import annotations

import ctypes
import logging
import threading
from ctypes import wintypes
from typing import Callable

logger = logging.getLogger(__name__)
Rect = tuple[int, int, int, int]
PanelRect = tuple[int, int, int, int]
MONITOR_DEFAULTTONEAREST = 2


def panel_rect(hangul_rect: Rect | None, monitor_work_rect: Rect,
               width: int = 360, side: str = "right") -> PanelRect | None:
    if width <= 0:
        raise ValueError("width must be positive")
    if side not in ("right", "left"):
        raise ValueError("side must be 'right' or 'left'")
    if hangul_rect is None:
        return None
    left, top, right, bottom = hangul_rect
    wl, wt, wr, wb = monitor_work_rect
    height = min(max(0, bottom - top), max(0, wb - wt))
    y = min(max(top, wt), wb - height)
    outside_right, outside_left = right, left - width
    inside_right, inside_left = right - width, left

    def fits(x: int) -> bool:
        return x >= wl and x + width <= wr

    candidates = ((outside_right, outside_left, inside_right)
                  if side == "right" else
                  (outside_left, outside_right, inside_left))
    if wr - wl < width:
        raise ValueError("monitor work area cannot contain the panel width")
    x = next((candidate for candidate in candidates if fits(candidate)), None)
    if x is None:  # 바깥 두 곳 모두 안 되면 한/글 창 안쪽 끝에 겹치되 작업 영역 밖으로는 나가지 않게
        x = min(max(candidates[-1], wl), wr - width)
    return x, y, width, height


def _user32():
    return ctypes.windll.user32


def _callback_type():
    """Resolve the Windows callback factory only when a Win32 call is made."""
    factory = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)
    return factory(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _handle_value(handle) -> int:
    """Convert a pointer-sized HWND/HMONITOR without truncating 64-bit values."""
    if isinstance(handle, int):
        return handle
    return ctypes.cast(handle, ctypes.c_void_p).value or 0


def find_hangul_window(prefer_title: str = "") -> int | None:
    """Z 순서에서 보이는 제목에 ' - 한글'이 포함된 창을 찾는다."""
    try:
        user32 = _user32()
        callback_type = _callback_type()
        matches: list[tuple[int, str]] = []

        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowTextW.restype = ctypes.c_int
        def visit(hwnd, _param):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    if user32.GetWindowTextW(hwnd, buffer, length + 1):
                        title = buffer.value
                        if " - 한글" in title:
                            matches.append((_handle_value(hwnd), title))
            return True

        callback = callback_type(visit)
        user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL
        user32.EnumWindows(callback, 0)
        if prefer_title:
            for hwnd, title in matches:
                if prefer_title in title:
                    return hwnd
        return matches[0][0] if matches else None
    except Exception:
        logger.exception("한글 창 검색에 실패했습니다")
        return None


class _RECT(ctypes.Structure):
    _fields_ = [(name, wintypes.LONG) for name in ("left", "top", "right", "bottom")]


def window_rect(hwnd: int) -> Rect | None:
    try:
        user32 = _user32()
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(_RECT)]
        user32.GetWindowRect.restype = wintypes.BOOL
        if user32.IsIconic(hwnd):
            return None
        rect = _RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return None
        return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        logger.exception("창 사각형 조회에 실패했습니다")
        return None


class _MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", _RECT),
                ("rcWork", _RECT), ("dwFlags", wintypes.DWORD)]


def monitor_work_rect(hwnd: int) -> Rect | None:
    try:
        user32 = _user32()
        user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        user32.MonitorFromWindow.restype = wintypes.HMONITOR
        user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(_MONITORINFO)]
        user32.GetMonitorInfoW.restype = wintypes.BOOL
        monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
        if not monitor:
            return None
        info = _MONITORINFO()
        info.cbSize = ctypes.sizeof(_MONITORINFO)
        if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return None
        r = info.rcWork
        return r.left, r.top, r.right, r.bottom
    except Exception:
        logger.exception("모니터 작업 영역 조회에 실패했습니다")
        return None


class DockTracker:
    def __init__(self, get_rect: Callable[[], tuple[Rect, Rect] | None],
                 move_panel: Callable[[PanelRect | None], None], interval: float = 0.25):
        if interval <= 0:
            raise ValueError("interval must be positive")
        self._get_rect, self._move_panel, self._interval = get_rect, move_panel, interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_rect: PanelRect | None = None
        self._has_moved = False
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._last_rect, self._has_moved = None, False
            self._thread = threading.Thread(target=self._run, name="docfit-dock-tracker", daemon=True)
            self._thread.start()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                bounds = self._get_rect()
                target = panel_rect(*bounds) if bounds is not None else None
                if not self._has_moved or target != self._last_rect:
                    self._move_panel(target)
                    self._last_rect, self._has_moved = target, True
            except Exception:
                logger.exception("도우미 패널 위치 추적에 실패했습니다")
            self._stop_event.wait(self._interval)

    def stop(self, timeout: float | None = 2.0) -> None:
        with self._lock:
            thread = self._thread
            self._stop_event.set()
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout)
