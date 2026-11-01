"""Windows 알림 영역 아이콘과 메뉴를 관리하는 지연 로드 트레이 서비스."""

from __future__ import annotations

import ctypes
import logging
import os
import threading
from dataclasses import dataclass

WM_QUIT = 0x0012
WM_USER = 0x0400
WM_APP = 0x8000
WM_TRAY = WM_APP + 0x31
WM_RBUTTONUP = 0x0205
WM_CONTEXTMENU = 0x007B
WM_LBUTTONDBLCLK = 0x0203
NIM_ADD = 0x00000000
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_SHOWTIP = 0x00000080
IDI_APPLICATION = 32512
TPM_RIGHTBUTTON = 0x0002
TPM_RETURNCMD = 0x0100
MF_STRING = 0x0000
SW_RESTORE = 9
MENU_HELPER = 1001
MENU_RESTORE = 1002
MENU_EXIT = 1003
_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Message:
    message: int
    wparam: int = 0
    lparam: int = 0


class _Win32Api:
    """USER32/SHELL32 어댑터. 인스턴스를 만들 때만 Windows DLL을 연다."""

    def __init__(self):
        if os.name != "nt":
            raise OSError("트레이 서비스는 Windows에서만 사용할 수 있습니다.")
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.pointer = ctypes.c_void_p
        self.long_ptr = ctypes.c_ssize_t

        class GUID(ctypes.Structure):
            _fields_ = [("Data1", ctypes.c_uint32), ("Data2", ctypes.c_uint16),
                        ("Data3", ctypes.c_uint16), ("Data4", ctypes.c_ubyte * 8)]

        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("hWnd", self.pointer),
                        ("uID", ctypes.c_uint), ("uFlags", ctypes.c_uint),
                        ("uCallbackMessage", ctypes.c_uint), ("hIcon", self.pointer),
                        ("szTip", ctypes.c_wchar * 128), ("dwState", ctypes.c_uint),
                        ("dwStateMask", ctypes.c_uint), ("szInfo", ctypes.c_wchar * 256),
                        ("uTimeoutOrVersion", ctypes.c_uint), ("szInfoTitle", ctypes.c_wchar * 64),
                        ("dwInfoFlags", ctypes.c_uint), ("guidItem", GUID), ("hBalloonIcon", self.pointer)]

        class MSG(ctypes.Structure):
            _fields_ = [("hwnd", self.pointer), ("message", ctypes.c_uint),
                        ("wParam", self.pointer), ("lParam", self.long_ptr),
                        ("time", ctypes.c_uint), ("pt_x", ctypes.c_long), ("pt_y", ctypes.c_long)]

        self.notify_type = NOTIFYICONDATAW
        self.msg_type = MSG
        self.user32.GetMessageW.argtypes = [self.pointer, self.pointer, ctypes.c_uint, ctypes.c_uint]
        self.user32.GetMessageW.restype = ctypes.c_int
        self.user32.PostThreadMessageW.argtypes = [ctypes.c_uint, ctypes.c_uint, self.pointer, self.pointer]
        self.user32.PostThreadMessageW.restype = ctypes.c_int
        self.user32.PeekMessageW.argtypes = [self.pointer, self.pointer, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
        self.user32.PeekMessageW.restype = ctypes.c_int
        self.user32.CreatePopupMenu.restype = self.pointer
        self.user32.AppendMenuW.argtypes = [self.pointer, ctypes.c_uint, ctypes.c_size_t, ctypes.c_wchar_p]
        self.user32.TrackPopupMenu.argtypes = [self.pointer, ctypes.c_uint, ctypes.c_int, ctypes.c_int,
                                                ctypes.c_int, self.pointer, self.pointer]
        self.user32.GetCursorPos.argtypes = [ctypes.POINTER(ctypes.c_long * 2)]
        self.user32.SetForegroundWindow.argtypes = [self.pointer]
        self.user32.DestroyMenu.argtypes = [self.pointer]
        self.user32.ShowWindow.argtypes = [self.pointer, ctypes.c_int]
        self.user32.IsIconic.argtypes = [self.pointer]
        self.user32.IsIconic.restype = ctypes.c_int
        self.user32.GetForegroundWindow.restype = self.pointer
        self.user32.GetActiveWindow.restype = self.pointer
        self.user32.GetWindow.restype = self.pointer
        self.kernel32.GetCurrentThreadId.restype = ctypes.c_uint

    def get_current_thread_id(self):
        return int(self.kernel32.GetCurrentThreadId())

    def peek_message(self, remove=False):
        msg = self.msg_type()
        self.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0 if not remove else 1)
        return msg

    def get_message(self):
        msg = self.msg_type()
        result = int(self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0))
        if result == -1:
            code = ctypes.get_last_error()
            raise OSError(code, ctypes.FormatError(code).strip())
        return result, _Message(int(msg.message), int(msg.wParam or 0), int(msg.lParam or 0))

    def post_thread_message(self, thread_id, message, wparam=0, lparam=0):
        if not self.user32.PostThreadMessageW(thread_id, message, wparam, lparam):
            code = ctypes.get_last_error()
            raise OSError(code, ctypes.FormatError(code).strip())

    def add_icon(self, thread_id):
        # A real HWND is not needed for Shell_NotifyIcon; a stable thread key is used as uID.
        data = self.notify_type()
        data.cbSize = ctypes.sizeof(data)
        data.uID = int(thread_id)
        data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP | NIF_SHOWTIP
        data.uCallbackMessage = WM_TRAY
        data.hIcon = self.user32.LoadIconW(None, ctypes.c_void_p(IDI_APPLICATION))
        data.szTip = "한글 문서 편집 도우미"
        if not self.shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(data)):
            code = ctypes.get_last_error()
            raise OSError(code, ctypes.FormatError(code).strip())
        self.data = data

    def remove_icon(self):
        data = getattr(self, "data", None)
        if data is not None:
            self.shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(data))
            self.data = None

    def show_menu(self, thread_id):
        menu = self.user32.CreatePopupMenu()
        try:
            self.user32.AppendMenuW(menu, MF_STRING, MENU_HELPER, "도우미 패널 열기")
            self.user32.AppendMenuW(menu, MF_STRING, MENU_RESTORE, "앱 창 복원")
            self.user32.AppendMenuW(menu, MF_STRING, MENU_EXIT, "종료")
            point = (ctypes.c_long * 2)()
            self.user32.GetCursorPos(ctypes.byref(point))
            # Foreground activation is required for dismissal after a menu choice.
            foreground = self.user32.GetForegroundWindow()
            self.user32.SetForegroundWindow(foreground)
            return int(self.user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON | TPM_RETURNCMD,
                                                   point[0], point[1], 0, None, None))
        finally:
            self.user32.DestroyMenu(menu)

    def is_iconic(self, hwnd):
        return bool(hwnd and self.user32.IsIconic(hwnd))

    def restore_window(self, hwnd):
        if hwnd:
            self.user32.ShowWindow(hwnd, SW_RESTORE)
        return bool(hwnd)


def _message_parts(message):
    if isinstance(message, _Message):
        return message.message, message.wparam, message.lparam
    if isinstance(message, dict):
        return int(message.get("message", 0)), int(message.get("wparam", 0)), int(message.get("lparam", 0))
    if isinstance(message, tuple):
        if len(message) == 3:
            return tuple(map(int, message))
        if len(message) == 2 and isinstance(message[1], _Message):
            return _message_parts(message[1])
    return int(message.message), int(message.wParam), int(message.lParam)


def handle_tray_message(message, *, show_menu, dispatch, restore_window, thread_id):
    """가짜 API 시험에서 그대로 쓰는 메뉴/콜백 분기."""
    msg, _wparam, event = _message_parts(message)
    if msg != WM_TRAY:
        return False
    if event in (WM_RBUTTONUP, WM_CONTEXTMENU):
        selection = show_menu(thread_id)
        actions = {MENU_HELPER: "panel", MENU_RESTORE: "restore", MENU_EXIT: "exit"}
        action = actions.get(selection)
        if action is not None:
            dispatch(action)
        return True
    if event == WM_LBUTTONDBLCLK:
        restore_window()
        return True
    return False


class TrayService:
    """전용 메시지 스레드에서 알림 아이콘과 컨텍스트 메뉴를 관리한다."""

    def __init__(self, on_action, *, api=None):
        if not callable(on_action):
            raise ValueError("트레이 동작 콜백은 호출할 수 있어야 합니다.")
        self._on_action = on_action
        self._api = api
        self._lock = threading.RLock()
        self._ready = threading.Event()
        self._thread = None
        self._thread_id = None
        self._stop_requested = False
        self._icon_added = False

    def _get_api(self):
        if self._api is None:
            self._api = _Win32Api()
        return self._api

    def start(self):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._ready = threading.Event()
            self._stop_requested = False
            self._thread = threading.Thread(target=self._run, name="live-tray", daemon=True)
            self._thread.start()
            thread = self._thread
        if not self._ready.wait(5.0):
            self.stop()
            raise RuntimeError("트레이 메시지 스레드가 준비되지 않았습니다.")
        if thread.is_alive() and not self._icon_added:
            raise RuntimeError("트레이 아이콘을 만들지 못했습니다.")

    def _dispatch(self, action):
        try:
            self._on_action(action)
        except Exception:
            _logger.warning("트레이 메뉴 요청 전달 중 오류", exc_info=True)

    def _run(self):
        api = self._get_api()
        try:
            thread_id = api.get_current_thread_id()
            api.peek_message(False)
            with self._lock:
                self._thread_id = thread_id
                stopping = self._stop_requested
            if stopping:
                self._ready.set()
                return
            api.add_icon(thread_id)
            self._icon_added = True
        except Exception:
            _logger.warning("트레이 초기화 실패", exc_info=True)
            self._ready.set()
            return
        self._ready.set()
        try:
            while True:
                result, message = api.get_message()
                if result <= 0:
                    break
                msg, _wp, _lp = _message_parts(message)
                if msg == WM_TRAY:
                    selected = []
                    handle_tray_message(
                        message,
                        show_menu=api.show_menu,
                        dispatch=selected.append,
                        restore_window=lambda: self._dispatch("restore"),
                        thread_id=thread_id,
                    )
                    if selected:
                        self._dispatch(selected[0])
                        if selected[0] == "exit":
                            break
        except Exception:
            _logger.warning("트레이 메시지 루프 실패", exc_info=True)
        finally:
            try:
                api.remove_icon()
            except Exception:
                _logger.warning("트레이 아이콘 제거 실패", exc_info=True)
            self._icon_added = False
            with self._lock:
                self._thread_id = None
                if self._thread is threading.current_thread():
                    self._thread = None

    def stop(self, timeout=2.0):
        with self._lock:
            thread = self._thread
            if thread is None:
                return
            self._stop_requested = True
            thread_id = self._thread_id
        if thread_id is not None and thread.is_alive():
            self._get_api().post_thread_message(thread_id, WM_QUIT, 0, 0)
        if thread is not threading.current_thread():
            thread.join(max(0.0, timeout))
            if thread.is_alive():
                raise TimeoutError("트레이 서비스가 제한 시간 안에 종료되지 않았습니다.")
        with self._lock:
            if self._thread is thread and not thread.is_alive():
                self._thread = None
                self._thread_id = None

