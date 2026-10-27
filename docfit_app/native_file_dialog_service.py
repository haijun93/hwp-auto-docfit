"""호스트 메모리에만 경로를 보관하는 네이티브 파일 선택 서비스."""
import copy
import ctypes
import ntpath
import os
from pathlib import Path
import stat
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from .api_contract import ServiceError

DOCUMENTS = frozenset({'.hwp', '.hwpx', '.pdf', '.doc', '.docx', '.txt', '.md'})
PURPOSES = {
    'add_files': ('open', DOCUMENTS),
    'add_folder': ('directory', DOCUMENTS),
    'add_format_file': ('open', frozenset({'.hwp', '.hwpx'})),
    'idioms': ('open', frozenset({'.hwp', '.hwpx', '.ido'})),
    'table_template': ('open', frozenset({'.hwpx'})),
    'flow_png': ('save', frozenset({'.png'})),
    'flow_hwpx': ('save', frozenset({'.hwpx'})),
}


def fail(code):
    raise ServiceError(code, '파일 선택을 다시 확인해 주세요.')


def native_dialog(purpose, mode, multiple):
    """Run a Tk-free Windows dialog in the current dedicated STA."""
    if os.name != 'nt':
        fail('DIALOG_UNAVAILABLE')
    # Tk-free Win32 fallback for pywin32 builds without IFileDialog wrappers.
    import win32ui
    import win32con
    from win32com.shell import shell, shellcon
    if mode == 'directory':
        result = shell.SHBrowseForFolder(0, None, 'Select folder',
            shellcon.BIF_RETURNONLYFSDIRS | shellcon.BIF_NEWDIALOGSTYLE)
        if not result or not result[0]:
            return []
        path = shell.SHGetPathFromIDList(result[0])
        return [os.fsdecode(path)]
    extensions = sorted(PURPOSES[purpose][1])
    flags = win32con.OFN_EXPLORER | win32con.OFN_NOCHANGEDIR | win32con.OFN_PATHMUSTEXIST
    flags |= win32con.OFN_FILEMUSTEXIST if mode == 'open' else win32con.OFN_OVERWRITEPROMPT
    if multiple:
        flags |= win32con.OFN_ALLOWMULTISELECT
    dialog = win32ui.CreateFileDialog(mode == 'open', extensions[0][1:], None, flags,
        'Supported files|' + ';'.join('*' + ext for ext in extensions) + '||')
    if dialog.DoModal() != win32con.IDOK:
        return []
    return list(dialog.GetPathNames())


class NativeFileDialogService:
    TTL = 300
    MAX_FILES = 1000

    def __init__(self, dialog=None, clock=time.monotonic):
        self._dialog = dialog or native_dialog
        self._clock = clock
        self._lock = threading.RLock()
        self._tokens = {}
        self._requests = {}
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='file-dialog-STA')

    def _policy(self, purpose, mode=None, multiple=False):
        if purpose not in PURPOSES:
            fail('INVALID_PURPOSE')
        expected, extensions = PURPOSES[purpose]
        if mode is not None and (mode != expected or type(multiple) is not bool or
                                 (multiple and (mode != 'open' or purpose != 'add_files'))):
            fail('INVALID_INPUT')
        return expected, extensions

    def _path(self, value, mode, extensions):
        if not isinstance(value, str) or not value or len(value) > 32767 or '\x00' in value:
            fail('INVALID_PATH')
        drive, tail = ntpath.splitdrive(value)
        if ':' in tail or value.startswith(('\\\\', '//', '\\\\?\\', '\\\\.\\')):
            fail('INVALID_PATH')
        path = Path(value)
        if not path.is_absolute():
            fail('INVALID_PATH')
        try:
            # 링크를 resolve하기 전에 모든 구성요소를 검사한다(부모 junction 포함).
            for part in (path, *path.parents):
                if part.exists() or part.is_symlink():
                    info = part.lstat()
                    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                        fail('INVALID_PATH')
            path = path.resolve(strict=mode != 'save')
            if mode == 'directory':
                if not path.is_dir():
                    fail('INVALID_PATH')
            else:
                if path.suffix.lower() not in extensions:
                    fail('UNSUPPORTED_FORMAT')
                if mode == 'open' and not path.is_file():
                    fail('INVALID_PATH')
                if mode == 'save' and (not path.parent.is_dir() or path.is_dir()):
                    fail('INVALID_PATH')
            return path
        except PermissionError:
            fail('ACCESS_DENIED')
        except (OSError, ValueError):
            fail('INVALID_PATH')

    @staticmethod
    def _identity(path):
        if not path.exists():
            return None
        info = path.stat()
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)

    def register_selection(self, purpose, paths):
        mode, extensions = self._policy(purpose)
        if not isinstance(paths, (list, tuple)) or not 1 <= len(paths) <= self.MAX_FILES:
            fail('INVALID_PATH')
        if purpose not in {'add_files', 'add_format_file'} and len(paths) != 1:
            fail('INVALID_PATH')
        canonical = list(dict.fromkeys(self._path(p, mode, extensions) for p in paths))
        identities = [self._identity(p) for p in canonical]
        token = str(uuid.uuid4())
        with self._lock:
            now = self._clock()
            self._tokens = {k: v for k, v in self._tokens.items() if v[0] > now}
            self._tokens[token] = (now + self.TTL, purpose, canonical, identities)
        return {'ok': True, 'cancelled': False, 'selection_id': token,
                'files': [{'name': p.name, 'size': p.stat().st_size if p.is_file() else 0}
                          for p in canonical]}

    def resolve_selection(self, selection_id, purpose):
        mode, extensions = self._policy(purpose)
        with self._lock:
            entry = self._tokens.get(selection_id)
            if entry is None or entry[0] <= self._clock():
                self._tokens.pop(selection_id, None)
                fail('SELECTION_EXPIRED')
            if entry[1] != purpose:
                fail('INVALID_PURPOSE')
            del self._tokens[selection_id]
        paths = [self._path(str(p), mode, extensions) for p in entry[2]]
        if [self._identity(p) for p in paths] != entry[3]:
            fail('OUTPUT_CHANGED' if mode == 'save' else 'SOURCE_CHANGED')
        return [str(p) for p in paths]

    def directory_files(self, paths, recursive=False):
        if type(recursive) is not bool or len(paths) != 1:
            fail('INVALID_INPUT')
        root = self._path(paths[0], 'directory', DOCUMENTS)
        found, seen = [], set()
        for folder, dirs, names in os.walk(root, followlinks=False):
            for name in dirs:
                self._path(str(Path(folder) / name), 'directory', DOCUMENTS)
            for name in sorted(names):
                candidate = Path(folder) / name
                if candidate.suffix.lower() not in DOCUMENTS:
                    continue
                candidate = self._path(str(candidate), 'open', DOCUMENTS)
                identity = self._identity(candidate)[:2]
                if identity not in seen:
                    seen.add(identity)
                    found.append(str(candidate))
                    if len(found) > self.MAX_FILES:
                        fail('DIRECTORY_LIMIT')
            if not recursive:
                break
        return sorted(found, key=str.casefold)

    def _run(self, purpose, mode, multiple):
        initialized = False
        try:
            if os.name == 'nt':
                hr = ctypes.OleDLL('ole32').CoInitializeEx(None, 2)
                if hr not in (0, 1):
                    fail('DIALOG_FAILED')
                initialized = True
            paths = self._dialog(purpose, mode, multiple)
            return self.register_selection(purpose, paths) if paths else {'ok': True, 'cancelled': True}
        finally:
            if initialized:
                ctypes.OleDLL('ole32').CoUninitialize()

    def submit_selection(self, request_id, purpose, mode='open', multiple=False):
        self._policy(purpose, mode, multiple)
        if not isinstance(request_id, str) or not 1 <= len(request_id) <= 128:
            fail('INVALID_INPUT')
        signature = (purpose, mode, multiple)
        with self._lock:
            if request_id in self._requests:
                previous, future = self._requests[request_id]
                if previous != signature:
                    fail('REQUEST_ID_REUSED')
                return future
            if len(self._requests) >= 256:
                completed = next((key for key, (_, job) in self._requests.items() if job.done()), None)
                if completed is None:
                    fail('BUSY')
                del self._requests[completed]
            future = self._executor.submit(self._run, purpose, mode, multiple)
            self._requests[request_id] = (signature, future)
            return future

    def selection_status(self, request_id):
        with self._lock:
            entry = self._requests.get(request_id)
        if entry is None:
            fail('INVALID_INPUT')
        return copy.deepcopy(entry[1].result()) if entry[1].done() else {'ok': True, 'pending': True, 'request_id': request_id}

    def select_files(self, request_id, purpose, mode='open', multiple=False):
        return copy.deepcopy(self.submit_selection(request_id, purpose, mode, multiple).result())

    def close(self):
        self._executor.shutdown(wait=False, cancel_futures=True)
        with self._lock:
            self._tokens.clear()
