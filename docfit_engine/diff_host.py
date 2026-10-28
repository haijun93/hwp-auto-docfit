"""Isolated T17 wire-v1 host. All viewer operations belong to the main STA.

``--headless`` is an explicit integration-test adapter, never a production fallback.
The native OLE adapter deliberately fails closed until its read-only gate is certified.
"""
import argparse
from collections import OrderedDict
import hashlib
import hmac
import io
import json
import math
import os
from pathlib import Path
import queue
import re
import sys
import threading
import time

MAX_LINE = 64 * 1024
MAX_DEPTH = 16
METHODS = frozenset(('bootstrap', 'navigate', 'scroll', 'set_sync', 'focus', 'heartbeat', 'close'))


class ProtocolError(ValueError):
    def __init__(self, code='INVALID_FRAME'):
        super().__init__(code)
        self.code = code


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError()
        result[key] = value
    return result


def _constant(value):
    raise ProtocolError()


def _depth(value, level=1):
    if level > MAX_DEPTH:
        raise ProtocolError('DEPTH_LIMIT')
    if isinstance(value, dict):
        for item in value.values():
            _depth(item, level + 1)
    elif isinstance(value, list):
        for item in value:
            _depth(item, level + 1)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ProtocolError()


def decode_frame(line):
    if not isinstance(line, bytes) or not line.endswith(b'\n'):
        raise ProtocolError('INVALID_FRAMING')
    body = line[:-1]
    if body.endswith(b'\r'):
        body = body[:-1]
    if len(body) > MAX_LINE:
        raise ProtocolError('LINE_LIMIT')
    try:
        result = json.loads(body.decode('utf-8'), object_pairs_hook=_pairs,
                            parse_constant=_constant)
        _depth(result)
        if type(result) is not dict or type(result.get('v')) is not int or result['v'] != 1:
            raise ProtocolError()
        return result
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, ProtocolError):
            raise
        raise ProtocolError() from None


def encode_frame(message):
    _depth(message)
    try:
        data = json.dumps(message, ensure_ascii=True, allow_nan=False,
                          separators=(',', ':')).encode('utf-8')
    except (ValueError, TypeError):
        raise ProtocolError() from None
    if len(data) > MAX_LINE:
        raise ProtocolError('LINE_LIMIT')
    return data + b'\n'


def read_frame(stream):
    line = stream.readline(MAX_LINE + 3)
    if not line:
        return None
    return decode_frame(line)


def _text(value):
    return type(value) is str and 1 <= len(value) <= 128 and not any(ord(c) < 32 for c in value)


def validate_command(frame):
    if set(frame) != {'v', 'id', 'viewer_id', 'method', 'params'}:
        raise ProtocolError()
    if not _text(frame['id']) or not _text(frame['viewer_id']):
        raise ProtocolError()
    method, params = frame['method'], frame['params']
    if type(method) is not str or method not in METHODS or type(params) is not dict:
        raise ProtocolError()
    fields = {
        'bootstrap': {'nonce', 'viewer_id', 'parent_pid', 'left', 'right', 'protocol'},
        'navigate': {'side', 'page', 'sync', 'navigation_seq'},
        'scroll': {'side', 'page', 'fraction', 'sync', 'navigation_seq'},
        'set_sync': {'enabled'}, 'focus': set(), 'heartbeat': set(), 'close': {'reason'},
    }
    if set(params) != fields[method]:
        raise ProtocolError()
    if method in ('navigate', 'scroll'):
        if (params['side'] not in ('left', 'right') or type(params['page']) is not int
                or params['page'] < 1 or type(params['sync']) is not bool
                or type(params['navigation_seq']) is not int or params['navigation_seq'] < 0):
            raise ProtocolError()
        if method == 'scroll' and (type(params['fraction']) not in (int, float)
                                    or not 0 <= params['fraction'] <= 1):
            raise ProtocolError()
    if method == 'set_sync' and type(params['enabled']) is not bool:
        raise ProtocolError()
    if method == 'close' and params['reason'] not in ('user', 'main_exit', 'cancel'):
        raise ProtocolError()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def copy_root():
    return Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local/share')) / 'HwpAutoDocFit' / 'diff'


class ParentGuard:
    """Keep a process handle, so PID reuse cannot resurrect a dead parent."""
    def __init__(self, pid):
        self.handle = None
        if type(pid) is not int or pid <= 0 or not self._is_parent(pid):
            raise ProtocolError('PARENT_MISMATCH')
        if os.name == 'nt':
            import win32api
            self.handle = win32api.OpenProcess(0x00100000, False, pid)
        self.pid = pid

    @staticmethod
    def _is_parent(pid):
        parent = os.getppid()
        if parent == pid:
            return True
        if os.name != 'nt':
            return False
        # Windows venv python.exe is a redirector: its interpreter child has
        # the launcher as immediate parent. Verify exactly this extra hop.
        import ctypes
        from ctypes import wintypes
        class BasicInfo(ctypes.Structure):
            _fields_ = [('reserved', ctypes.c_void_p), ('peb', ctypes.c_void_p),
                        ('reserved2', ctypes.c_void_p * 2), ('pid', ctypes.c_size_t),
                        ('parent_pid', ctypes.c_size_t)]
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        query_name = kernel.QueryFullProcessImageNameW
        query_name.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                               ctypes.POINTER(wintypes.DWORD)]
        handle = kernel.OpenProcess(0x1000, False, parent)
        if not handle:
            return False
        try:
            name, length = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
            if not query_name(handle, 0, name, ctypes.byref(length)):
                return False
            if Path(name.value).resolve() != Path(sys.executable).resolve():
                return False
            query = ctypes.WinDLL('ntdll').NtQueryInformationProcess
            query.argtypes = [wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p,
                              wintypes.ULONG, ctypes.c_void_p]
            info = BasicInfo()
            return query(handle, 0, ctypes.byref(info), ctypes.sizeof(info), None) == 0 and info.parent_pid == pid
        finally:
            kernel.CloseHandle(handle)

    def alive(self):
        if self.handle is not None:
            import win32event
            return win32event.WaitForSingleObject(self.handle, 0) == win32event.WAIT_TIMEOUT
        return os.getppid() == self.pid

    def close(self):
        if self.handle is not None:
            self.handle.Close()
            self.handle = None


class HeadlessViewer:
    """Test-only deterministic page adapter; never claims real document rendering."""
    def __init__(self):
        self.pages = {'left': 1, 'right': 1}
        self.counts = {'left': 10, 'right': 7}

    def open(self, paths):
        return {'capabilities': {'headless': True, 'scroll_sync': False},
                'left': {'page_count': self.counts['left']},
                'right': {'page_count': self.counts['right']}, 'host_pid': os.getpid()}

    def navigate(self, side, page, sync):
        if page > self.counts[side]:
            raise ProtocolError('PAGE_OUT_OF_RANGE')
        self.pages[side] = page
        other = 'right' if side == 'left' else 'left'
        if sync:
            self.pages[other] = min(page, self.counts[other])
        return {'side': side, 'page': page, 'pages': dict(self.pages),
                'clamped': sync and page > self.counts[other]}

    def focus(self):
        pass

    def close(self):
        pass


class NativeViewer:
    def open(self, paths):
        # Do not Dispatch HwpObject (which could attach to a user's session).
        # Registered ActiveX alone does not certify a safe read-only OLE container.
        raise ProtocolError('OLE_NOT_AVAILABLE')

    def close(self):
        pass


class DiffHost:
    def __init__(self, output, *, headless=False, clock=time.monotonic, root=None):
        self.output = output
        self.clock = clock
        self.root = Path(root) if root is not None else copy_root()
        self.viewer = HeadlessViewer() if headless else NativeViewer()
        self.viewer_id = None
        self.nonce = None
        self.guard = None
        self.paths = {}
        self.hashes = {}
        self.last_heartbeat = clock()
        self.stopped = False
        self.reason = 'cancel'
        self.seq = 0
        self.sync = True
        self.navigation_seq = -1
        self.cache = OrderedDict()
        self.lock = threading.RLock()

    def emit(self, message):
        with self.lock:
            self.output.write(encode_frame(message))
            self.output.flush()

    def event(self, event, data):
        self.seq += 1
        self.emit({'v': 1, 'viewer_id': self.viewer_id, 'event': event,
                   'seq': self.seq, 'data': data})

    def expired(self):
        return self.clock() - self.last_heartbeat >= 10

    def bootstrap(self, frame):
        p = frame['params']
        if (type(p['nonce']) is not str or not re.fullmatch('[0-9a-f]{64}', p['nonce'])
                or p['viewer_id'] != frame['viewer_id'] or type(p['protocol']) is not int
                or p['protocol'] != 1 or not re.fullmatch('[0-9a-f-]{36}', p['viewer_id'])):
            raise ProtocolError('BOOTSTRAP_REJECTED')
        self.guard = ParentGuard(p['parent_pid'])
        directory = self.root.resolve() / p['viewer_id']
        for side in ('left', 'right'):
            entry = p[side]
            if type(entry) is not dict or set(entry) != {'path', 'sha256'}:
                raise ProtocolError('BOOTSTRAP_REJECTED')
            if type(entry['path']) is not str or type(entry['sha256']) is not str:
                raise ProtocolError('BOOTSTRAP_REJECTED')
            path = Path(entry['path'])
            if (path.suffix.lower() not in ('.hwp', '.hwpx') or path.stem != side
                    or path.is_symlink() or not path.is_file()
                    or path.resolve().parent != directory.resolve()
                    or directory.is_symlink() or not re.fullmatch('[0-9a-f]{64}', entry['sha256'])
                    or not hmac.compare_digest(sha256_file(path), entry['sha256'])
                    or path.stat().st_mode & 0o222):
                raise ProtocolError('COPY_VALIDATION_FAILED')
            self.paths[side], self.hashes[side] = path, entry['sha256']
        self.viewer_id, self.nonce = frame['viewer_id'], p['nonce']
        self.last_heartbeat = self.clock()
        return self.viewer.open(self.paths)

    def handle(self, frame):
        validate_command(frame)
        method, params = frame['method'], frame['params']
        if self.viewer_id is None and method != 'bootstrap':
            raise ProtocolError('BOOTSTRAP_REQUIRED')
        if self.viewer_id is not None and (frame['viewer_id'] != self.viewer_id or method == 'bootstrap'):
            raise ProtocolError('SESSION_MISMATCH')
        key = frame['id']
        body = encode_frame(frame)
        with self.lock:
            if key in self.cache:
                old, response = self.cache[key]
                if body != old:
                    raise ProtocolError('REQUEST_ID_REUSED')
                self.emit(response)
                return
        result = {}
        try:
            if method == 'bootstrap':
                result = self.bootstrap(frame)
            elif method == 'heartbeat':
                self.last_heartbeat = self.clock()
            elif method == 'close':
                self.reason, self.stopped = params['reason'], True
            elif method == 'set_sync':
                self.sync = params['enabled']
                result = {'enabled': self.sync}
            elif method == 'focus':
                self.viewer.focus()
            elif method == 'scroll':
                raise ProtocolError('UNSUPPORTED_FEATURE')
            elif method == 'navigate':
                if params['navigation_seq'] <= self.navigation_seq:
                    result = {'ignored': True}
                else:
                    result = self.viewer.navigate(params['side'], params['page'], params['sync'])
                    self.navigation_seq = params['navigation_seq']
                    self.event('position', dict(result, fraction=0,
                               navigation_seq=self.navigation_seq, origin='remote'))
            response = {'v': 1, 'id': key, 'viewer_id': frame['viewer_id'], 'ok': True, 'result': result}
        except ProtocolError as exc:
            response = {'v': 1, 'id': key, 'viewer_id': frame['viewer_id'], 'ok': False,
                        'error': {'code': exc.code, 'message': exc.code, 'retryable': False}}
            if method == 'bootstrap':
                self.stopped = True
        with self.lock:
            self.cache[key] = (body, response)
            if len(self.cache) > 256:
                self.cache.popitem(last=False)
            self.emit(response)
            if method == 'bootstrap' and response['ok']:
                self.event('ready', result)

    def teardown(self):
        try:
            self.viewer.close()
        finally:
            if self.guard:
                self.guard.close()
            matches = all(path.is_file() and sha256_file(path) == self.hashes[side]
                          for side, path in self.paths.items())
            if self.viewer_id:
                self.event('closed', {'reason': self.reason, 'copy_hashes_match': matches})


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args(argv)
    host = DiffHost(sys.stdout.buffer, headless=args.headless)
    inbox = queue.Queue(maxsize=256)
    eof = threading.Event()

    def reader():
        try:
            stream = io.FileIO(sys.stdin.fileno(), 'rb', closefd=False)
            while not host.stopped:
                frame = read_frame(stream)
                if frame is None:
                    break
                validate_command(frame)
                # Heartbeats do not wait behind a blocking COM operation.
                if frame['method'] == 'heartbeat' and host.viewer_id:
                    host.handle(frame)
                else:
                    inbox.put_nowait(frame)
        except (ProtocolError, OSError, queue.Full):
            pass
        finally:
            eof.set()

    def watchdog():
        while not host.stopped:
            if eof.wait(.1) or host.expired() or (host.guard and not host.guard.alive()):
                host.reason = 'parent_exit' if eof.is_set() else 'heartbeat_timeout'
                host.stopped = True
                # COM can hang: the service/job is the final cleanup authority.
                timer = threading.Timer(2, lambda: os._exit(1))
                timer.daemon = True
                timer.start()
                return

    com = None
    try:
        try:
            import pythoncom
            pythoncom.CoInitialize()
            com = pythoncom
        except ImportError:
            if not args.headless:
                raise ProtocolError('OLE_NOT_AVAILABLE')
        threading.Thread(target=reader, daemon=True).start()
        threading.Thread(target=watchdog, daemon=True).start()
        while not host.stopped:
            try:
                host.handle(inbox.get(timeout=.02))
            except queue.Empty:
                pass
            if com:
                com.PumpWaitingMessages()
        return 0
    except (ProtocolError, OSError):
        return 1
    finally:
        try:
            host.teardown()
        finally:
            if com:
                com.CoUninitialize()


if __name__ == '__main__':
    raise SystemExit(main())
