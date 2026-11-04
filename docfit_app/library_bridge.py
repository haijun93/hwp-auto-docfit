"""On-demand client for the isolated Rust klib named-pipe process."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


class LibraryBridgeError(RuntimeError):
    pass


def data_dir():
    override = os.environ.get("KLIB_DATA")
    return Path(override) if override else Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "HwpAutoDocFit" / "klib"


class LibraryBridge:
    def __init__(self, *, exe=None, process=None, pipe_factory=None):
        self.exe = Path(exe) if exe else Path(__file__).resolve().parents[1] / "resources" / "klib.exe"
        self.process = process or subprocess
        self.pipe_factory = pipe_factory

    def install(self, bundled_exe, folder=None):
        target = Path(folder) if folder else data_dir()
        target.mkdir(parents=True, exist_ok=True)
        exe = target / "klib.exe"
        source = Path(bundled_exe)
        if not exe.exists() or exe.read_bytes() != source.read_bytes():
            temporary = exe.with_suffix(f".{os.getpid()}.new")
            shutil.copyfile(source, temporary)
            os.replace(temporary, exe)
        self.exe = exe
        return exe

    def _pipe_name(self):
        if self.pipe_factory:
            return self.pipe_factory()
        import win32pipe  # supplied by pywin32 on Windows
        import win32file
        import win32security
        import win32api
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
        sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
        return rf"\\.\pipe\HwpAutoDocFit.klib.{win32security.ConvertSidToStringSid(sid)}"

    def request(self, cmd, **payload):
        if os.name != "nt" and not self.pipe_factory:
            raise LibraryBridgeError("klib 파이프는 Windows에서만 사용할 수 있습니다.")
        pipe = self._pipe_name()
        try:
            import time
            import win32file
            try:
                handle = win32file.CreateFile(pipe, win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None,
                                              win32file.OPEN_EXISTING, 0, None)
            except Exception:
                self.process.Popen([str(self.exe)], close_fds=True)
                deadline = time.monotonic() + 5
                while True:
                    try:
                        handle = win32file.CreateFile(pipe, win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                                      0, None, win32file.OPEN_EXISTING, 0, None)
                        break
                    except Exception:
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(.05)
            request = json.dumps(dict(payload, cmd=cmd), ensure_ascii=False).encode("utf-8") + b"\n"
            win32file.WriteFile(handle, request)
            chunks = []
            while True:
                _, data = win32file.ReadFile(handle, 65536)
                chunks.append(data)
                if data.endswith(b"\n"):
                    break
            response = json.loads(b"".join(chunks).decode("utf-8"))
        except Exception as exc:
            raise LibraryBridgeError(f"klib 요청 실패: {exc}") from exc
        if not response.get("ok"):
            raise LibraryBridgeError(response.get("message", "klib 요청 실패"))
        return response

    def library_search(self, query, *, box_id=None, limit=20):
        if not isinstance(query, str) or not query.strip() or len(query) > 200:
            raise ValueError("검색어는 1~200자로 입력하세요.")
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("검색 결과 수는 1~200이어야 합니다.")
        payload = {"query": query, "limit": limit}
        if box_id is not None:
            if type(box_id) is not int:
                raise ValueError("자료함을 선택하세요.")
            payload["box_id"] = box_id
        return self.request("search", **payload).get("results", [])

