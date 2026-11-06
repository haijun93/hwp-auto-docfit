"""On-demand client for the isolated Rust klib named-pipe process."""

from __future__ import annotations

import json

import os

import subprocess

import time

from pathlib import Path

MAX_REQUEST_BYTES = 64 * 1024

ALLOWED_COMMANDS = frozenset({

    "ping", "box_create", "box_list", "box_get", "box_update", "box_rename", "box_delete",

    "item_add", "item_get", "item_update", "item_rename", "item_move", "item_delete", "item_search",

    "relation_add", "relation_delete", "relation_list", "relation_update", "box_export",

    "search", "index_file", "remove_file",

    "nb_create", "nb_list", "nb_update", "nb_delete",

    "nb_source_add", "nb_source_list", "nb_source_remove", "nb_source_paragraphs", "nb_index",

    "nb_search", "nb_transform", "nb_note_save", "nb_note_list", "nb_note_delete", "nb_export_md",

})

class LibraryBridgeError(RuntimeError):

    pass

class LibraryBridge:

    def __init__(self, *, pipe_name=None, executable=None, test_root=None,

                 connector=None, popen=None, retries=8, retry_delay=0.05,

                 exe=None, process=None, pipe_factory=None):

        self.pipe_name = pipe_name or (pipe_factory() if pipe_factory else _current_user_pipe_name())

        base = Path(getattr(__import__("sys"), "_MEIPASS", Path(__file__).resolve().parent.parent))

        repository = Path(__file__).resolve().parent.parent

        if executable or exe:

            self.executable = Path(executable or exe)

        else:

            packaged = base / "resources" / "klib.exe"

            development = repository / "klib" / "target" / "release" / "klib.exe"

            self.executable = packaged if packaged.is_file() else development

        self.test_root = test_root if test_root is not None else os.environ.get("KLIB_TEST_ROOT")

        self.connector = connector or _open_pipe

        self.popen = popen or (process.Popen if process else subprocess.Popen)

        self.retries = retries

        self.retry_delay = retry_delay

    def request(self, request):

        if not isinstance(request, dict):

            raise LibraryBridgeError("자료함 요청은 JSON 객체여야 합니다.")

        command = request.get("cmd")

        if command not in ALLOWED_COMMANDS:

            raise LibraryBridgeError("허용되지 않은 자료함 명령입니다.")

        try:

            encoded = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

        except (TypeError, ValueError) as exc:

            raise LibraryBridgeError("자료함 요청을 JSON으로 인코딩할 수 없습니다.") from exc

        if len(encoded) > MAX_REQUEST_BYTES:

            raise LibraryBridgeError("자료함 요청이 64 KiB를 초과했습니다.")

        last_error = None

        started = False

        for attempt in range(self.retries):

            try:

                with self.connector(self.pipe_name) as pipe:

                    pipe.write(encoded + b"\n")

                    pipe.flush()

                    line = pipe.readline(MAX_REQUEST_BYTES + 1)

                if len(line) > MAX_REQUEST_BYTES:

                    raise LibraryBridgeError("klib 응답이 허용 크기를 초과했습니다.")

                if not line:

                    raise LibraryBridgeError("klib 파이프가 응답 없이 닫혔습니다.")

                return json.loads(line.decode("utf-8"))

            except LibraryBridgeError:

                raise

            except (OSError, TimeoutError, json.JSONDecodeError) as exc:

                last_error = exc

                if not started:

                    self._start()

                    started = True

                if attempt + 1 < self.retries:

                    time.sleep(self.retry_delay)

        raise LibraryBridgeError("klib 파이프에 연결하거나 응답을 읽지 못했습니다.") from last_error

    def _start(self):

        if not self.executable.is_file():

            raise LibraryBridgeError(f"klib 실행 파일을 찾을 수 없습니다: {self.executable}")

        env = os.environ.copy()

        if self.test_root is not None:

            env["KLIB_TEST_ROOT"] = str(self.test_root)

        self.popen([str(self.executable)], close_fds=True, env=env,

                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

def _current_user_pipe_name():

    if os.name == "nt":

        import ctypes

        from ctypes import wintypes

        # 64비트에서 핸들·포인터가 32비트로 잘리지 않도록 함수 형식을 지정한다(v2.2.18 자료함 SID 오류 수정).
        advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
        advapi32.OpenProcessToken.restype = wintypes.BOOL
        advapi32.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        advapi32.GetTokenInformation.restype = wintypes.BOOL
        advapi32.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
        advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL

        token = wintypes.HANDLE()

        if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):

            raise LibraryBridgeError("현재 사용자 SID를 확인하지 못했습니다.")

        try:

            size = wintypes.DWORD()

            advapi32.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))

            buf = ctypes.create_string_buffer(size.value)

            if not advapi32.GetTokenInformation(token, 1, buf, size, ctypes.byref(size)):

                raise LibraryBridgeError("현재 사용자 SID를 확인하지 못했습니다.")

            sid_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]

            text = wintypes.LPWSTR()

            if not advapi32.ConvertSidToStringSidW(sid_ptr, ctypes.byref(text)):

                raise LibraryBridgeError("현재 사용자 SID를 확인하지 못했습니다.")

            try:

                sid = text.value

            finally:

                kernel32.LocalFree(ctypes.cast(text, ctypes.c_void_p))

        finally:

            kernel32.CloseHandle(token)

        suffix = ""

        root = os.environ.get("KLIB_TEST_ROOT")

        if root:

            value = 0xCBF29CE484222325

            encoded = root.encode("utf-16le")

            for index in range(0, len(encoded), 2):

                unit = encoded[index] | (encoded[index + 1] << 8)

                value = ((value ^ unit) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF

            suffix = f".test.{value:016x}"

        return rf"\\.\pipe\HwpAutoDocFit.klib{suffix}.{sid}"

    raise LibraryBridgeError("자료함 파이프는 Windows에서만 사용할 수 있습니다.")

def _open_pipe(name):

    return open(name, "r+b", buffering=0)

def open_library_item(item):

    """Open a referenced file/folder or an explicitly safe web link."""

    import webbrowser

    kind = item.get("kind")

    source = item.get("source_path", "")

    if kind == "link":

        from urllib.parse import urlparse

        parsed = urlparse(source)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:

            raise LibraryBridgeError("http/https 링크만 열 수 있습니다.")

        return webbrowser.open(source)

    if os.name != "nt":

        raise LibraryBridgeError("자료 열기는 Windows에서 지원됩니다.")

    if not source or not os.path.exists(source):

        raise LibraryBridgeError("자료 경로를 찾을 수 없습니다.")

    os.startfile(source)

    return True

def save_clipboard_image(bridge, box_id, display_name, png_bytes, *, space="temp"):

    import base64

    return bridge.request({"cmd": "item_add", "box_id": box_id, "kind": "capture",

        "source_path": "", "display_name": display_name, "space": space,

        "content": base64.b64encode(png_bytes).decode("ascii")})

def save_formatted_text(bridge, box_id, display_name, html, *, space="temp"):

    return bridge.request({"cmd": "item_add", "box_id": box_id, "kind": "rich_text",

        "source_path": "", "display_name": display_name, "space": space, "content": html})
