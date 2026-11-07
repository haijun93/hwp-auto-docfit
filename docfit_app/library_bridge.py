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

    "item_text_get", "item_text_set",  # 글 자료 사본 읽기·고치기(자료함 메모 편집기). 경로 인자 없음.

    "relation_add", "relation_delete", "relation_list", "relation_update", "box_export",

    "search", "index_file", "remove_file",

    "box_scan", "box_scan_status", "box_scan_cancel", "box_scan_files",

    "nb_create", "nb_list", "nb_update", "nb_delete",

    "nb_source_add", "nb_source_from_item", "nb_source_item", "nb_source_list", "nb_source_remove", "nb_source_paragraphs", "nb_index",

    "nb_search", "nb_transform", "nb_note_save", "nb_note_list", "nb_note_delete", "nb_export_md", "nb_compare",

} | frozenset(f"edit_{name}" for name in (

    # 메모 편집기 코어(editor_core, klib 파이프 edit_*). docs/EDITOR_CORE_DESIGN.md 4절.

    "ping", "open", "close", "info", "text", "lines", "insert", "delete", "replace",

    "begin_group", "end_group", "commit", "undo", "redo", "line_col", "offset", "to_utf16", "from_utf16",

    "find", "find_all", "replace_next", "replace_all",

    "md_parse", "md_inline", "md_block", "md_link", "md_rule", "md_code_block", "md_clear",

    "set_line_ending", "set_encoding", "save", "autosave",

)))

EDITOR_COMMANDS = frozenset(c for c in ALLOWED_COMMANDS if c.startswith("edit_"))

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

    def available(self):

        """klib를 쓸 수 있는지(실행 파일이 있고, 기본 파이프라면 Windows일 때만)."""

        if self.connector is _open_pipe and os.name != "nt":

            return False

        return self.executable.is_file() or self.connector is not _open_pipe

    def request_command(self, cmd, **payload):

        return self.request(dict(payload, cmd=cmd))

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

# 연결 앱으로 바로 열면 프로그램이 실행되는 확장자. 자료함 등록 자료는 사용자 확인 뒤에만, 등록되지 않은 경로는 차단한다.
RISKY_OPEN_EXTENSIONS = frozenset({
    ".exe", ".bat", ".cmd", ".com", ".ps1", ".psm1", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh",
    ".msi", ".msp", ".scr", ".pif", ".lnk", ".url", ".hta", ".cpl", ".msc", ".reg", ".jar", ".appref-ms",
})


class LibraryOpenError(LibraryBridgeError):
    """자료 열기 실패. code로 화면이 이유를 구분한다."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def is_risky_open_path(path):
    return os.path.splitext(str(path or "").strip().rstrip(". "))[1].lower() in RISKY_OPEN_EXTENSIONS


def open_library_item(item, *, opener=None, browser=None, allow_risky=None):

    """Open a referenced file/folder or an explicitly safe web link.

    opener(path)·browser(url)는 시험용 가짜 실행기를 넣는 자리다(기본: os.startfile·webbrowser.open).
    실행 파일(.exe·.bat·.ps1 등)은 item["confirmed"]가 참일 때만 연다(allow_risky=False면 항상 차단).
    """

    kind = str(item.get("kind") or "")
    source = str(item.get("source_path") or "").strip()
    if any(ch in source for ch in ("\n", "\r", "\0")):
        raise LibraryOpenError("INVALID_PATH", "줄바꿈이나 제어 문자가 든 경로는 열 수 없습니다.")
    if not source:
        raise LibraryOpenError("NO_SOURCE", "원본 파일 경로가 없는 자료입니다.")
    lowered = source.lower()
    if kind == "link" or lowered.startswith(("http://", "https://")):
        from urllib.parse import urlparse

        parsed = urlparse(source)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise LibraryOpenError("BLOCKED", "http/https 링크만 열 수 있습니다.")
        if browser is None:
            import webbrowser

            browser = webbrowser.open
        if not browser(source):
            raise LibraryOpenError("NO_APP", "기본 브라우저를 실행하지 못했습니다.")
        return True
    if "://" in source or lowered.startswith(("file:", "javascript:", "shell:", "ms-")):
        raise LibraryOpenError("BLOCKED", "파일·폴더 경로나 http/https 주소만 열 수 있습니다.")
    if not os.path.exists(source):
        raise LibraryOpenError("SOURCE_MISSING", "원본 파일을 찾을 수 없습니다(옮겨졌거나 삭제되었을 수 있습니다).")
    if not os.path.isdir(source) and is_risky_open_path(source):
        if allow_risky is False:
            raise LibraryOpenError("BLOCKED", "자료함에 등록되지 않은 실행 파일은 열 수 없습니다.")
        if not item.get("confirmed"):
            raise LibraryOpenError("CONFIRM_REQUIRED", "실행 파일입니다. 실행할지 확인이 필요합니다.")
    if opener is None:
        if os.name != "nt":
            raise LibraryOpenError("ERROR", "자료 열기는 Windows에서 지원됩니다.")
        opener = os.startfile
    try:
        opener(source)
    except OSError as exc:
        # 연결된 앱이 없으면 Windows가 ERROR_NO_ASSOCIATION(1155)을 돌려준다.
        if getattr(exc, "winerror", None) in (1155, 1156) or "association" in str(exc).lower():
            raise LibraryOpenError("NO_APP", "이 형식에 연결된 앱이 없습니다.") from exc
        raise LibraryOpenError("ERROR", f"자료를 열지 못했습니다: {exc}") from exc
    return True

def save_clipboard_image(bridge, box_id, display_name, png_bytes, *, space="temp"):

    import base64

    return bridge.request({"cmd": "item_add", "box_id": box_id, "kind": "capture",

        "source_path": "", "display_name": display_name, "space": space,

        "content": base64.b64encode(png_bytes).decode("ascii")})

def save_formatted_text(bridge, box_id, display_name, html, *, space="temp"):

    return bridge.request({"cmd": "item_add", "box_id": box_id, "kind": "rich_text",

        "source_path": "", "display_name": display_name, "space": space, "content": html})
