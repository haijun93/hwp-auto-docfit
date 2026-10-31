"""K에이전트(kagent.exe) 연결: 상태 파일 읽기, 파이프 명령, 켜기·끄기·자동 시작.

에이전트는 앱과 따로 떠 있는 작은 네이티브 프로그램이다(kagent/). 앱은 화면만 맡고,
클립보드 기록·빠른 붙여넣기 팝업은 에이전트가 한다. 파이프는 현재 사용자만 열 수 있다.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "HwpAutoDocFit.KAgent"
MAX_RESPONSE = 64 * 1024 * 1024


class KAgentError(RuntimeError):
    pass


def data_dir():
    override = os.environ.get("KAGENT_DATA")
    if override:
        return Path(override)
    return Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "HwpAutoDocFit" / "kagent"


class KAgentClient:
    def __init__(self, folder=None, timeout=2.0):
        self.folder = Path(folder) if folder else data_dir()
        self.timeout = timeout

    def status_file(self):
        """에이전트가 변경 때마다 쓰는 상태. 꺼져 있으면 None."""
        path = self.folder / "status.json"
        for attempt in range(5):
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                return None
            except (OSError, ValueError):
                # 에이전트가 새 상태 파일로 바꾸는 순간에는 잠깐 열 수 없다.
                time.sleep(0.005 * (attempt + 1))
        return None

    def running(self):
        status = self.status_file()
        return bool(status and _pid_alive(status.get("pid")))

    def request(self, cmd, **payload):
        status = self.status_file()
        if not status or not status.get("pipe"):
            raise KAgentError("K클립보드가 켜져 있지 않습니다.")
        pipe = status["pipe"]
        if not str(pipe).startswith("\\\\.\\pipe\\HwpAutoDocFit.kagent."):
            raise KAgentError("상태 파일의 연결 이름을 확인해 주세요.")
        line = json.dumps(dict(payload, cmd=cmd), ensure_ascii=False).encode("utf-8") + b"\n"
        try:
            with open(pipe, "r+b", buffering=0) as stream:
                stream.write(line)
                chunks = []
                size = 0
                while True:
                    chunk = stream.read(1 << 16)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                    if chunk.endswith(b"\n") or size > MAX_RESPONSE:
                        break
        except OSError as error:
            raise KAgentError("K클립보드에 연결하지 못했습니다.") from error
        try:
            return json.loads(b"".join(chunks).decode("utf-8"))
        except ValueError as error:
            raise KAgentError("K클립보드 응답을 읽지 못했습니다.") from error


def _pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0 or os.name != "nt":
        return False
    import ctypes
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(handle)
    return code.value == 259  # STILL_ACTIVE


def installed_exe(folder=None):
    return (Path(folder) if folder else data_dir()) / "kagent.exe"


def install(bundled_exe, folder=None):
    """앱에 들어 있는 kagent.exe를 사용자 데이터 폴더로 복사한다(같으면 그대로)."""
    target = installed_exe(folder)
    target.parent.mkdir(parents=True, exist_ok=True)
    source = Path(bundled_exe)
    if not target.exists() or target.read_bytes() != source.read_bytes():
        temp = target.with_suffix(".new")
        shutil.copyfile(source, temp)
        os.replace(temp, target)
    return target


def start(exe=None, *, delay=0):
    exe = Path(exe) if exe else installed_exe()
    args = [str(exe)] + (["--delay", str(int(delay))] if delay else [])
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    return subprocess.Popen(args, creationflags=flags, close_fds=True)


def stop(timeout=3.0):
    client = KAgentClient()
    if client.running():
        try:
            client.request("quit")
        except KAgentError:
            pass


def set_autostart(enabled, exe=None):
    """로그인 때 30초 늦게 시작(관리자 권한 불필요, HKCU Run)."""
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE) as key:
        if enabled:
            exe = Path(exe) if exe else installed_exe()
            winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, f'"{exe}" --delay 30')
        else:
            try:
                winreg.DeleteValue(key, RUN_NAME)
            except FileNotFoundError:
                pass
