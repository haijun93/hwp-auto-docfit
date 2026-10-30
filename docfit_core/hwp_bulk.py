"""HWP → HWPX 일괄 변환(2.0.7): 파일 하나·폴더·로컬 드라이브 전체, 암호·배포용·기관 보안(DRM) 문서.

- 찾기: 시스템 폴더(Windows·Program Files·AppData 등)와 바로가기 연결(정션)은 건너뛴다.
- 결과: 원본 옆에 같은 이름의 .hwpx. 이미 있으면 건너뛰고 원본은 고치지 않는다.
- 암호 문서: 한/글 '문서 암호' 창에 사용자가 준 암호를 차례로 넣는다(창을 띄운 채 멈추지 않음).
  결과 HWPX도 같은 암호로 잠긴다(한/글 기본 동작, 보안 유지).
- 기관 보안(DRM): 이 PC의 문서보안 프로그램이 허용하면 그대로 열려 변환되고, 막히면 이유를 남긴다.
"""
from __future__ import annotations

import csv
import os
import stat
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 드라이브 전체를 찾을 때 들어가지 않는 폴더(소문자).
SKIP_DIRS = frozenset({
    "windows", "program files", "program files (x86)", "programdata", "$recycle.bin", "$windows.~bt",
    "$windows.~ws", "$winreagent", "system volume information", "recovery", "appdata", "msocache",
    "perflogs", "node_modules", ".git", ".svn", "__pycache__", "onedrivetemp", "config.msi",
})
OLE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
HWP3_SIGNATURE = b"HWP Document File"
MAX_FILES = 200_000

MSG_PASSWORD = "암호 문서: 입력한 암호가 맞지 않거나 암호를 넣지 않았습니다. '암호'칸에 문서 암호를 넣고 다시 변환하세요."
MSG_DRM = ("기관 보안(DRM) 문서: 이 PC의 문서보안 프로그램이 열기를 허용하지 않았습니다. "
           "보안 프로그램에서 해제(복호화)하거나 보안 프로그램이 설치된 PC에서 변환하세요.")
MSG_SAVE = "한/글이 HWPX 저장을 거부했습니다(배포용 문서처럼 저장이 막힌 문서일 수 있습니다)."


def classify(path: str | Path) -> str:
    """'hwp'(HWP 5), 'hwp3'(HWP 3.x), 'protected'(DRM 등으로 감싼 파일)."""
    try:
        with open(path, "rb") as stream:
            head = stream.read(32)
    except OSError:
        return "unreadable"
    if head.startswith(OLE_SIGNATURE):
        return "hwp"
    if head.startswith(HWP3_SIGNATURE):
        return "hwp3"
    return "protected"


def target_for(source: str | Path) -> Path:
    return Path(source).with_suffix(".hwpx")


def _skip_dir(entry: os.DirEntry) -> bool:
    name = entry.name.lower()
    if name in SKIP_DIRS or name.startswith("$"):
        return True
    try:
        info = entry.stat(follow_symlinks=False)
    except OSError:
        return True
    attributes = getattr(info, "st_file_attributes", 0)
    # 정션·바로가기 연결(재분석 지점)과 시스템 숨김 폴더는 들어가지 않는다(같은 폴더를 두 번 돌지 않게).
    return bool(entry.is_symlink() or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                or (attributes & stat.FILE_ATTRIBUTE_SYSTEM and attributes & stat.FILE_ATTRIBUTE_HIDDEN))


def find_hwp(roots, *, recursive=True, skip_existing=True, stop=None, on_progress=None, limit=MAX_FILES):
    """roots(파일·폴더·드라이브) 안의 .hwp 목록과 건너뛴 수(이미 HWPX 있음)."""
    found, skipped, seen_dirs, last = [], 0, 0, 0.0
    stack = []
    for root in roots:
        path = Path(root)
        if path.is_file():
            if path.suffix.lower() == ".hwp" and not path.is_symlink():
                if skip_existing and target_for(path).exists():
                    skipped += 1
                else:
                    found.append(path)
        elif path.is_dir():
            stack.append(path)
    while stack and len(found) < limit:
        if stop is not None and stop.is_set():
            break
        folder = stack.pop()
        seen_dirs += 1
        try:
            entries = list(os.scandir(folder))
        except OSError:
            continue
        for entry in sorted(entries, key=lambda e: e.name.lower(), reverse=True):
            try:
                if entry.is_dir(follow_symlinks=False):
                    if recursive and not _skip_dir(entry):
                        stack.append(Path(entry.path))
                elif entry.name.lower().endswith(".hwp") and entry.is_file(follow_symlinks=False):
                    source = Path(entry.path)
                    if skip_existing and target_for(source).exists():
                        skipped += 1
                    else:
                        found.append(source)
            except OSError:
                continue
        if on_progress and time.monotonic() - last > 0.3:
            last = time.monotonic()
            on_progress(dict(phase="scan", folders=seen_dirs, found=len(found), current=str(folder)))
    found.sort(key=lambda p: str(p).lower())
    return found, skipped


def local_drives():
    """고정 디스크 드라이브 목록(예: ['C:\\', 'D:\\']). 네트워크·CD 드라이브는 뺀다."""
    if os.name != "nt":
        return []
    import ctypes
    drives, mask = [], ctypes.windll.kernel32.GetLogicalDrives()
    for index in range(26):
        if mask & (1 << index):
            root = f"{chr(65 + index)}:\\"
            if ctypes.windll.kernel32.GetDriveTypeW(root) == 3:  # DRIVE_FIXED
                drives.append(root)
    return drives


def hwp_pids():
    """실행 중인 한/글(Hwp.exe) 프로세스 번호."""
    if os.name != "nt":
        return set()
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Hwp.exe", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, timeout=15,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    pids = set()
    for row in csv.reader(out.splitlines()):
        if len(row) > 1 and row[1].isdigit():
            pids.add(int(row[1]))
    return pids


class DialogResponder:
    """변환용 한/글 프로세스(pid)의 '문서 암호' 창에 암호를 차례로 넣고, 저장 확인 창은 기본 단추로 넘긴다.

    사용자의 다른 한/글 창은 건드리지 않는다(pid가 다르다). 확인 창은 열기·저장 중(phase)일 때만 답한다.
    """

    def __init__(self, pid, passwords=()):
        self.pid = pid
        self.passwords = [p for p in passwords if p]
        self.phase = None
        self.current = []
        self.attempts = 0
        self.gave_up = False
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="hwp-dialog-responder", daemon=True)

    def __enter__(self):
        if self.pid:
            self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()

    def begin(self, phase, passwords=None):
        """phase: 'open'(이번 열기에 넣을 암호 passwords) · 'save' · None(답하지 않음)."""
        self.phase = phase
        if phase == "open":
            self.current = list(passwords or [])
            self.attempts = 0
            self.gave_up = False

    def _dialogs(self):
        import win32gui
        import win32process
        found = []

        def collect(hwnd, _):
            try:
                if (win32process.GetWindowThreadProcessId(hwnd)[1] == self.pid
                        and win32gui.GetClassName(hwnd) == "HNC_DIALOG" and win32gui.IsWindowVisible(hwnd)):
                    found.append((hwnd, win32gui.GetWindowText(hwnd)))
            except Exception:
                pass
            return True
        win32gui.EnumWindows(collect, None)
        return found

    @staticmethod
    def _focus(hwnd):
        import ctypes
        import win32process

        class GuiThreadInfo(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint32), ("flags", ctypes.c_uint32), ("hwndActive", ctypes.c_void_p),
                        ("hwndFocus", ctypes.c_void_p), ("hwndCapture", ctypes.c_void_p),
                        ("hwndMenuOwner", ctypes.c_void_p), ("hwndMoveSize", ctypes.c_void_p),
                        ("hwndCaret", ctypes.c_void_p), ("rcCaret", ctypes.c_long * 4)]
        info = GuiThreadInfo(cbSize=ctypes.sizeof(GuiThreadInfo))
        thread = win32process.GetWindowThreadProcessId(hwnd)[0]
        if ctypes.windll.user32.GetGUIThreadInfo(thread, ctypes.byref(info)) and info.hwndFocus:
            return info.hwndFocus
        return hwnd

    @staticmethod
    def _key(hwnd, vk):
        import win32con
        import win32gui
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)

    def _run(self):
        import win32con
        import win32gui
        while not self._stop.wait(0.2):
            if self.phase is None:
                continue
            try:
                dialogs = self._dialogs()
            except Exception:
                continue
            for hwnd, title in dialogs:
                if "암호" in title:
                    target = self._focus(hwnd)
                    if self.phase == "open" and self.attempts < len(self.current):
                        password = self.current[self.attempts]
                        self.attempts += 1
                        for char in password:
                            win32gui.PostMessage(target, win32con.WM_CHAR, ord(char), 0)
                        time.sleep(0.2)
                        self._key(target, win32con.VK_RETURN)
                    else:
                        self.gave_up = True
                        self._key(target, win32con.VK_ESCAPE)
                    time.sleep(0.8)
                    break
                if title == "한글" and self.phase in {"open", "save"}:
                    # 열기: '암호가 틀립니다' 알림, 저장: '암호가 걸린 문서를 이 형식으로 저장할까요?' → 기본 단추(확인·저장).
                    time.sleep(0.2)
                    self._key(hwnd, win32con.VK_RETURN)
                    time.sleep(0.6)
                    break


@dataclass
class BulkResult:
    source: str
    status: str  # success | failed | skipped
    output: str = ""
    message: str = ""


def convert_one(app, source: Path, responder: DialogResponder | None = None) -> BulkResult:
    from docfit_core.hwpx import validate_hwpx
    target = target_for(source)
    if target.exists():
        return BulkResult(str(source), "skipped", str(target), "이미 HWPX가 있어 건너뛰었습니다.")
    kind = classify(source)
    if kind == "unreadable":
        return BulkResult(str(source), "failed", message="파일을 읽을 수 없습니다(다른 프로그램이 쓰는 중이거나 권한 없음).")
    temporary = target.with_name(f".~docfit_{os.getpid()}_{target.name}")
    temporary.unlink(missing_ok=True)
    opened = False
    try:
        opened = True
        fmt = "HWP" if kind != "hwp3" else ""
        # 1) 암호 창 없이 연다(일반·배포용·보안 프로그램이 풀어 주는 DRM 문서).
        ok = app.Open(str(source), fmt, "forceopen:true;suspendpassword:true")
        used_password = False
        if ok is False and kind == "protected":
            return BulkResult(str(source), "failed", message=MSG_DRM)
        if ok is False and kind == "hwp" and responder and responder.pid and responder.passwords:
            # 2) 암호 문서: 암호마다 다시 연다(틀리면 한/글이 열기를 끝내므로 한 번에 하나씩).
            for password in responder.passwords:
                try:
                    app.Clear(1)
                except Exception:
                    pass
                responder.begin("open", [password])
                ok = app.Open(str(source), fmt, "forceopen:true")
                responder.begin(None)
                if ok is not False:
                    used_password = True
                    break
        if ok is False:
            return BulkResult(str(source), "failed",
                              message=MSG_PASSWORD if kind == "hwp" else "한/글에서 문서를 열지 못했습니다.")
        if responder:
            responder.begin("save")
        if app.SaveAs(str(temporary), "HWPX", "") is False or not temporary.exists():
            return BulkResult(str(source), "failed", message=MSG_SAVE)
        validate_hwpx(temporary)
        os.link(temporary, target)
        note = ""
        if used_password:
            note = "암호 문서 → 같은 암호의 HWPX"
        elif kind == "protected":
            note = "기관 보안 문서를 이 PC의 보안 프로그램이 열어 변환"
        return BulkResult(str(source), "success", str(target), note)
    except Exception as exc:  # 한/글 COM 오류는 파일 하나만 실패로 남기고 계속한다.
        return BulkResult(str(source), "failed", message=f"변환 오류: {exc}")
    finally:
        if responder:
            responder.begin(None)
        if opened:
            try:
                app.Clear(1)  # 저장 묻지 않고 닫는다(원본을 덮어쓰지 않게).
            except Exception:
                pass
        temporary.unlink(missing_ok=True)


@dataclass
class BulkState:
    phase: str = "idle"  # idle | scan | convert | done | stopped | error
    found: int = 0
    skipped_existing: int = 0
    done: int = 0
    succeeded: int = 0
    failed: int = 0
    current: str = ""
    report: str = ""
    error: str = ""
    failures: list = field(default_factory=list)

    def as_dict(self):
        return dict(phase=self.phase, found=self.found, skipped_existing=self.skipped_existing, done=self.done,
                    succeeded=self.succeeded, failed=self.failed, current=self.current, report=self.report,
                    error=self.error, failures=self.failures[-200:])


def write_report(results, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"HWPX변환_결과_{datetime.now():%Y%m%d_%H%M%S}.csv"
    with open(path, "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["결과", "원본", "HWPX", "설명"])
        labels = {"success": "변환", "failed": "실패", "skipped": "건너뜀"}
        for item in results:
            writer.writerow([labels.get(item.status, item.status), item.source, item.output, item.message])
    return path


def run_bulk(roots, *, app_factory, state: BulkState, stop: threading.Event, passwords=(), skip_existing=True,
             report_dir: Path, recursive=True):
    """찾기 → 변환 → 결과 CSV. state를 계속 고쳐 화면이 진행 상황을 읽는다."""
    state.phase = "scan"

    def scanned(info):
        state.found, state.current = info["found"], info["current"]
    files, state.skipped_existing = find_hwp(roots, recursive=recursive, skip_existing=skip_existing,
                                             stop=stop, on_progress=scanned)
    state.found = len(files)
    results = []
    if not files or stop.is_set():
        state.phase = "stopped" if stop.is_set() else "done"
        return results
    state.phase = "convert"
    before = hwp_pids()
    app = app_factory()
    pid = next(iter(hwp_pids() - before), None)
    try:
        with DialogResponder(pid, passwords) as responder:
            for source in files:
                if stop.is_set():
                    break
                state.current = str(source)
                result = convert_one(app, source, responder)
                results.append(result)
                state.done += 1
                if result.status == "success":
                    state.succeeded += 1
                elif result.status == "failed":
                    state.failed += 1
                    state.failures.append(dict(source=result.source, message=result.message))
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    state.report = str(write_report(results, report_dir))
    state.current = ""
    state.phase = "stopped" if stop.is_set() else "done"
    return results
