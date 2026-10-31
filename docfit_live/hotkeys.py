"""전역 단축키 파싱과 Win32 메시지 스레드 서비스."""

from __future__ import annotations

import ctypes
import logging
import os
import re
import threading
from dataclasses import dataclass

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
WM_USER = 0x0400
PM_NOREMOVE = 0x0000
DEFAULT_HOTKEYS = {
    "panel": "Ctrl+Alt+J",
    "table_template": "Ctrl+Alt+T",
    "table_sketch": "Ctrl+Alt+S",
}

_MODIFIERS = {
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "alt": MOD_ALT,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
    "windows": MOD_WIN,
}
_logger = logging.getLogger(__name__)


def parse_hotkey(spec: str) -> tuple[int, int]:
    """단축키 문자열을 (modifier 비트, 가상 키 코드)로 바꾼다."""
    if not isinstance(spec, str) or not spec:
        raise ValueError("단축키를 입력해 주세요.")
    tokens = [part.strip() for part in spec.split("+")]
    if any(not token for token in tokens):
        raise ValueError("단축키에 빈 항목이 있습니다.")
    normalized = [token.casefold() for token in tokens]
    if len(set(normalized)) != len(normalized):
        raise ValueError("단축키 항목을 중복해서 입력할 수 없습니다.")

    modifiers = 0
    keys = []
    for token in tokens:
        modifier = _MODIFIERS.get(token.casefold())
        if modifier is not None:
            if modifiers & modifier:
                raise ValueError("같은 수식 키를 중복해서 입력할 수 없습니다.")
            modifiers |= modifier
        else:
            keys.append(token)
    if not modifiers:
        raise ValueError("단축키에는 Ctrl, Alt, Shift 또는 Win이 필요합니다.")
    if len(keys) != 1:
        raise ValueError("단축키에는 영문자·숫자·기능 키 하나를 지정해 주세요.")
    key = keys[0]
    upper = key.upper()
    if len(key) == 1 and "A" <= upper <= "Z":
        vk = ord(upper)
    elif len(key) == 1 and "0" <= key <= "9":
        vk = ord(key)
    else:
        match = re.fullmatch(r"f(\d{1,2})", key, flags=re.IGNORECASE)
        if not match or not 1 <= int(match.group(1)) <= 12:
            raise ValueError("지원하지 않는 단축키입니다. 영문자, 숫자, F1~F12를 사용해 주세요.")
        vk = 0x70 + int(match.group(1)) - 1
    return modifiers, vk


@dataclass(frozen=True)
class _Message:
    message: int
    wparam: int = 0
    lparam: int = 0


class _Win32Api:
    """요청 시점에만 USER32를 연결하는 Win32 어댑터."""

    def __init__(self):
        if os.name != "nt":
            raise OSError("전역 단축키 서비스는 Windows에서만 사용할 수 있습니다.")
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._pointer = ctypes.c_void_p
        self._long_ptr = ctypes.c_ssize_t

        self._user32.RegisterHotKey.argtypes = [self._pointer, ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
        self._user32.RegisterHotKey.restype = ctypes.c_int
        self._user32.UnregisterHotKey.argtypes = [self._pointer, ctypes.c_int]
        self._user32.UnregisterHotKey.restype = ctypes.c_int
        self._user32.GetMessageW.argtypes = [self._pointer, self._pointer, ctypes.c_uint, ctypes.c_uint]
        self._user32.GetMessageW.restype = ctypes.c_int
        self._user32.PostThreadMessageW.argtypes = [ctypes.c_uint, ctypes.c_uint, self._pointer, self._pointer]
        self._user32.PostThreadMessageW.restype = ctypes.c_int
        self._user32.PeekMessageW.argtypes = [self._pointer, self._pointer, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
        self._user32.PeekMessageW.restype = ctypes.c_int
        self._kernel32.GetCurrentThreadId.argtypes = []
        self._kernel32.GetCurrentThreadId.restype = ctypes.c_uint

        class MSG(ctypes.Structure):
            _fields_ = [("hwnd", self._pointer), ("message", ctypes.c_uint),
                        ("wParam", self._pointer), ("lParam", self._long_ptr),
                        ("time", ctypes.c_uint), ("pt_x", ctypes.c_long), ("pt_y", ctypes.c_long)]
        self._msg_type = MSG

    @staticmethod
    def _error():
        code = ctypes.get_last_error()
        return OSError(code, ctypes.FormatError(code).strip() if code else "Win32 함수가 실패했습니다.")

    def register_hotkey(self, hwnd, identifier, modifiers, vk):
        if not self._user32.RegisterHotKey(hwnd, identifier, modifiers, vk):
            return False, self._error()
        return True, None

    def unregister_hotkey(self, hwnd, identifier):
        if not self._user32.UnregisterHotKey(hwnd, identifier):
            raise self._error()
        return True

    def get_current_thread_id(self):
        return int(self._kernel32.GetCurrentThreadId())

    def peek_message(self, remove):
        msg = self._msg_type()
        self._user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0 if not remove else 1)
        return msg

    def get_message(self):
        msg = self._msg_type()
        result = int(self._user32.GetMessageW(ctypes.byref(msg), None, 0, 0))
        if result == -1:
            raise self._error()
        return result, _Message(int(msg.message), int(msg.wParam or 0), int(msg.lParam or 0))

    def post_thread_message(self, thread_id, message, wparam=0, lparam=0):
        if not self._user32.PostThreadMessageW(thread_id, message, wparam, lparam):
            raise self._error()
        return True


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


class HotkeyService:
    """Win32 메시지 전용 스레드에서 전역 단축키를 관리한다."""

    def __init__(self, bindings: dict[str, str], on_hotkey, *, api=None):
        if not isinstance(bindings, dict):
            raise ValueError("단축키 설정은 이름과 문자열의 사전이어야 합니다.")
        checked = {}
        combinations = set()
        for name, spec in bindings.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(spec, str):
                raise ValueError("단축키 이름과 값은 비어 있지 않은 문자열이어야 합니다.")
            combination = parse_hotkey(spec)
            if combination in combinations:
                raise ValueError("같은 단축키 조합을 여러 이름에 지정할 수 없습니다.")
            combinations.add(combination)
            checked[name] = spec
        if not callable(on_hotkey):
            raise ValueError("단축키 콜백은 호출할 수 있어야 합니다.")
        self.bindings = checked
        self._on_hotkey = on_hotkey
        self._api = api
        self._lock = threading.RLock()
        self._registration_lock = threading.Lock()
        self._ready = threading.Event()
        self._thread = None
        self._thread_id = None
        self._registered = {}
        self._failed = []
        self._stop_requested = False

    @property
    def failed(self):
        with self._lock:
            return [dict(item) for item in self._failed]

    def snapshot(self):
        with self._lock:
            return {"bindings": dict(self.bindings), "failed": [dict(item) for item in self._failed]}

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
            self._registered = {}
            self._failed = []
            self._thread = threading.Thread(target=self._run, name="global-hotkeys", daemon=True)
            self._thread.start()
            thread = self._thread
        if not self._ready.wait(5.0):
            self.stop(timeout=5.0)
            raise RuntimeError("단축키 메시지 스레드가 준비되지 않았습니다.")
        with self._lock:
            stop_requested = self._stop_requested
            thread_id = self._thread_id
        if stop_requested and thread_id is not None:
            self._post_quit(thread_id)

    def _post_quit(self, thread_id):
        try:
            self._get_api().post_thread_message(thread_id, WM_QUIT, 0, 0)
        except Exception:
            _logger.warning("단축키 스레드 종료 메시지를 게시하지 못했습니다.", exc_info=True)

    def stop(self, timeout: float = 2.0):
        with self._lock:
            thread = self._thread
            if thread is None:
                return
            self._stop_requested = True
            thread_id = self._thread_id
        if thread_id is not None:
            # Registration may be in progress. Serialize WM_QUIT with it so
            # stop() cannot return before an in-flight registration is undone.
            with self._registration_lock:
                if thread.is_alive():
                    self._post_quit(thread_id)
        if thread is not threading.current_thread():
            thread.join(max(0.0, timeout))
            if thread.is_alive():
                raise TimeoutError("단축키 서비스가 제한 시간 안에 종료되지 않았습니다.")
        if not thread.is_alive():
            with self._lock:
                if self._thread is thread:
                    self._thread = None
                    self._thread_id = None

    def _register_result(self, result):
        if isinstance(result, tuple):
            if len(result) < 2:
                return bool(result[0]), "등록 결과 설명이 없습니다."
            return bool(result[0]), result[1]
        return bool(result), None

    def _run(self):
        api = self._get_api()
        try:
            thread_id = api.get_current_thread_id()
            api.peek_message(False)
            with self._lock:
                self._thread_id = thread_id
                stop_requested = self._stop_requested
            next_id = 1
            for name, spec in self.bindings.items():
                with self._registration_lock:
                    with self._lock:
                        if self._stop_requested:
                            break
                    modifiers, vk = parse_hotkey(spec)
                    identifier = next_id
                    next_id += 1
                    try:
                        ok, reason = self._register_result(api.register_hotkey(None, identifier, modifiers, vk))
                        if not ok:
                            raise reason if isinstance(reason, BaseException) else OSError(str(reason or "운영체제가 등록을 거절했습니다."))
                        with self._lock:
                            self._registered[identifier] = name
                    except Exception as exc:
                        with self._lock:
                            self._failed = [*self._failed, {"name": name, "hotkey": spec, "reason": str(exc)}]
            # Publish readiness only after every requested registration has
            # either succeeded or been recorded as failed.
            with self._lock:
                stop_requested = self._stop_requested
                self._ready.set()
            if stop_requested:
                self._post_quit(thread_id)
            while True:
                result, message = api.get_message()
                if result == 0:
                    break
                if result < 0:
                    _logger.error("단축키 메시지 루프에서 오류가 발생했습니다.")
                    break
                msg, wparam, _ = _message_parts(message)
                if msg != WM_HOTKEY:
                    continue
                with self._lock:
                    name = self._registered.get(wparam)
                if name is not None:
                    try:
                        self._on_hotkey(name)
                    except Exception:
                        _logger.warning("단축키 콜백 처리 중 오류가 발생했습니다.", exc_info=True)
        except Exception:
            _logger.exception("단축키 메시지 스레드가 실패했습니다.")
            with self._lock:
                if not self._ready.is_set():
                    self._ready.set()
        finally:
            with self._registration_lock:
                with self._lock:
                    registered = list(self._registered)
                for identifier in registered:
                    try:
                        api.unregister_hotkey(None, identifier)
                    except Exception:
                        _logger.warning("단축키 %s 해제 실패", identifier, exc_info=True)
                    finally:
                        with self._lock:
                            self._registered.pop(identifier, None)

