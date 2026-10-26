"""Asynchronous T17 child-process service; accepts IDs via a trusted resolver.

Resolver(document_id, result_id) returns {left, right, revision, saved_revision}.
Paths are backend registry values, never paths supplied by the JS bridge.
Native rendering remains gated; headless=True is exclusively for tests.
"""
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
import os
from pathlib import Path
import secrets
import shutil
import stat
import subprocess
import sys
import threading
import time
from uuid import uuid4

from docfit_engine.diff_host import (ProtocolError, copy_root, encode_frame,
                                    read_frame, sha256_file)


class DiffError(RuntimeError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _error(code):
    return {'ok': False, 'error': {'code': code, 'message': code, 'retryable': False}}


def _identity(value):
    return type(value) is str and 1 <= len(value) <= 128


def _stamp(path):
    s = path.stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns


def isolate_file(source, destination):
    """Exclusive copy; compare identity/metadata/hash around the copy."""
    source, destination = Path(source).resolve(strict=True), Path(destination)
    if source.suffix.lower() not in ('.hwp', '.hwpx') or not source.is_file():
        raise DiffError('INVALID_PATH')
    before = _stamp(source)
    digest = sha256_file(source)
    with source.open('rb') as src, destination.open('xb') as dst:
        opened = os.fstat(src.fileno())
        if (opened.st_dev, opened.st_ino) != before[:2]:
            raise DiffError('SOURCE_CHANGED')
        shutil.copyfileobj(src, dst, 1024 * 1024)
    if (_stamp(source) != before or sha256_file(source) != digest
            or sha256_file(destination) != digest or _stamp(source) != before):
        raise DiffError('SOURCE_CHANGED')
    destination.chmod(stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    return {'path': str(destination.resolve()), 'sha256': digest}


class ProcessGuard:
    """Non-inheritable kill-on-close Job, assigned before the child runs."""
    def __init__(self, *, allow_fallback=False):
        self.job = None
        self.process = None
        if os.name == 'nt':
            try:
                import win32job
                self.job = win32job.CreateJobObject(None, '')
                info = win32job.QueryInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation)
                info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                win32job.SetInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation, info)
            except Exception:
                self.close()
                if not allow_fallback:
                    raise DiffError('PROCESS_GUARD_FAILED') from None
        elif not allow_fallback:
            raise DiffError('PROCESS_GUARD_FAILED')

    def spawn(self, command, **kwargs):
        # Popen closes the primary thread handle. NtResumeProcess resumes the
        # initially suspended process only after successful job assignment.
        suspended = os.name == 'nt' and self.job is not None
        flags = (0x00000004 | 0x08000000) if suspended else (0x08000000 if os.name == 'nt' else 0)
        process = subprocess.Popen(command, creationflags=flags, **kwargs)
        self.process = process
        try:
            if suspended:
                import ctypes
                from ctypes import wintypes
                import win32job
                win32job.AssignProcessToJobObject(self.job, int(process._handle))
                resume = ctypes.WinDLL('ntdll').NtResumeProcess
                resume.argtypes = [wintypes.HANDLE]
                resume.restype = ctypes.c_long
                if resume(int(process._handle)) < 0:
                    raise DiffError('PROCESS_GUARD_FAILED')
            return process
        except Exception:
            process.kill()
            process.wait(timeout=2)
            raise DiffError('PROCESS_GUARD_FAILED') from None

    def close(self):
        if self.job is not None:
            self.job.Close()
            self.job = None


@dataclass
class _Viewer:
    viewer_id: str
    key: tuple
    state: str = 'preparing'
    seq: int = 0
    events: list = field(default_factory=list)
    error: object = None
    process: object = None
    guard: object = None
    directory: object = None
    copies: dict = field(default_factory=dict)
    pending: dict = field(default_factory=dict)
    responses: OrderedDict = field(default_factory=OrderedDict)
    request_bodies: dict = field(default_factory=dict)
    navigation_seq: int = 0
    stop: threading.Event = field(default_factory=threading.Event)
    write_lock: threading.Lock = field(default_factory=threading.Lock)
    close_lock: threading.Lock = field(default_factory=threading.Lock)
    worker: object = None
    state_since: float = field(default_factory=time.monotonic)
    close_reason: str = 'cancel'
    latest_navigation: object = None


class DiffHostService:
    def __init__(self, resolver, *, root=None, python_executable=None, headless=False):
        if not callable(resolver):
            raise TypeError('a trusted result registry resolver is required')
        self.resolver = resolver
        self.root = Path(root) if root is not None else copy_root()
        self.python = str(python_executable or sys.executable)
        self.headless = headless
        self.lock = threading.RLock()
        self.viewers = {}
        self.open_cache = OrderedDict()
        self.closed = False

    def _event(self, viewer, event, data):
        viewer.seq += 1
        viewer.events.append({'seq': viewer.seq, 'event': event, 'data': deepcopy(data)})
        viewer.events[:] = viewer.events[-256:]

    def _state(self, viewer, state):
        with self.lock:
            viewer.state, viewer.state_since = state, time.monotonic()
            self._event(viewer, 'state', {'state': state})

    def _fail(self, viewer, code):
        with self.lock:
            if viewer.state == 'closed':
                return
            if viewer.error is None:
                viewer.error = _error(code)['error']
                self._state(viewer, 'failed')
        viewer.stop.set()

    def open_diff(self, document_id, result_id, expected_revision, request_id):
        if (not all(_identity(v) for v in (document_id, result_id, request_id))
                or type(expected_revision) is not int or expected_revision < 0):
            return _error('INVALID_REQUEST')
        key = (document_id, result_id, expected_revision)
        with self.lock:
            if self.closed:
                return _error('SERVICE_CLOSED')
            if request_id in self.open_cache:
                old, response = self.open_cache[request_id]
                return deepcopy(response) if old == key else _error('REQUEST_ID_REUSED')
            active = [v for v in self.viewers.values() if v.state != 'closed']
            for viewer in active:
                if viewer.key == key:
                    if viewer.state == 'ready':
                        self._send(viewer, 'focus', {})
                    response = {'ok': True, 'viewer_id': viewer.viewer_id, 'state': viewer.state}
                    self._cache_open(request_id, key, response)
                    return response
            if len(active) >= 2 or any(v.key[0] == document_id for v in active):
                return _error('VIEWER_LIMIT')
            viewer = _Viewer(str(uuid4()), key)
            self.viewers[viewer.viewer_id] = viewer
            self._state(viewer, 'preparing')
            response = {'ok': True, 'viewer_id': viewer.viewer_id, 'state': 'preparing'}
            self._cache_open(request_id, key, response)
            viewer.worker = threading.Thread(target=self._run, args=(viewer,), daemon=True)
            viewer.worker.start()
            return response

    def _cache_open(self, request_id, key, response):
        self.open_cache[request_id] = (key, deepcopy(response))
        if len(self.open_cache) > 256:
            self.open_cache.popitem(last=False)

    def _send(self, viewer, method, params, request_id=None):
        request_id = request_id or str(uuid4())
        frame = {'v': 1, 'id': request_id, 'viewer_id': viewer.viewer_id,
                 'method': method, 'params': params}
        body = encode_frame(frame)
        with self.lock:
            previous = viewer.request_bodies.get(request_id)
            if previous is not None:
                if previous != body:
                    raise DiffError('REQUEST_ID_REUSED')
                return request_id
            viewer.request_bodies[request_id] = body
            viewer.pending[request_id] = (time.monotonic(), method)
        # Never block the bridge/UI on a full child pipe.
        def write():
            try:
                with viewer.write_lock:
                    viewer.process.stdin.write(body)
                    viewer.process.stdin.flush()
            except (OSError, ValueError, AttributeError):
                self._fail(viewer, 'HOST_DISCONNECTED')
        threading.Thread(target=write, daemon=True).start()
        return request_id

    @staticmethod
    def _cache_response(viewer, frame):
        viewer.responses[frame['id']] = frame
        if len(viewer.responses) > 256:
            old, _ = viewer.responses.popitem(last=False)
            viewer.request_bodies.pop(old, None)

    def _read(self, viewer):
        try:
            while True:
                frame = read_frame(viewer.process.stdout)
                if frame is None:
                    break
                if frame.get('viewer_id') != viewer.viewer_id:
                    raise ProtocolError()
                with self.lock:
                    if 'id' in frame:
                        if (set(frame) not in ({'v', 'id', 'viewer_id', 'ok', 'result'},
                                               {'v', 'id', 'viewer_id', 'ok', 'error'})
                                or type(frame['ok']) is not bool or frame['id'] not in viewer.pending):
                            raise ProtocolError()
                        _, method = viewer.pending.pop(frame['id'])
                        self._cache_response(viewer, frame)
                        if not frame['ok'] and method == 'bootstrap':
                            self._fail(viewer, frame['error']['code'])
                    else:
                        if (set(frame) != {'v', 'viewer_id', 'event', 'seq', 'data'}
                                or frame['event'] not in ('ready', 'position', 'closed')
                                or type(frame['seq']) is not int or frame['seq'] <= getattr(viewer, '_host_seq', 0)
                                or type(frame['data']) is not dict):
                            raise ProtocolError()
                        viewer._host_seq = frame['seq']
                        self._event(viewer, frame['event'], frame['data'])
                        if frame['event'] == 'ready':
                            if viewer.state != 'opening' or viewer.stop.is_set():
                                raise ProtocolError()
                            self._state(viewer, 'ready')
                        elif frame['event'] == 'closed':
                            if not frame['data'].get('copy_hashes_match'):
                                self._fail(viewer, 'COPY_CHANGED')
                            viewer.stop.set()
        except (ProtocolError, OSError, ValueError, KeyError, TypeError):
            self._fail(viewer, 'INVALID_HOST_FRAME')
        finally:
            if not viewer.stop.is_set():
                self._fail(viewer, 'HOST_DISCONNECTED')

    @staticmethod
    def _drain_stderr(viewer):
        # Consume continuously without keeping paths, nonce or unbounded logs.
        try:
            while viewer.process.stderr.read(4096):
                pass
        except (OSError, ValueError):
            pass

    def _run(self, viewer):
        monitor_stop = threading.Event()
        deadline = time.monotonic() + 20

        def preparation_watch():
            while not monitor_stop.wait(.1):
                if time.monotonic() > deadline and viewer.state in ('preparing', 'starting'):
                    self._fail(viewer, 'PREPARATION_TIMEOUT')
                    return
        threading.Thread(target=preparation_watch, daemon=True).start()
        try:
            record = self.resolver(*viewer.key[:2])
            if not record:
                raise DiffError('RESULT_NOT_FOUND')
            if (record['revision'] != viewer.key[2] or record['saved_revision'] != viewer.key[2]):
                raise DiffError('UNSAVED_REVISION')
            self.root.mkdir(parents=True, exist_ok=True)
            viewer.directory = self.root / viewer.viewer_id
            viewer.directory.mkdir()  # Exclusive, never reuse an earlier session.
            for side in ('left', 'right'):
                if viewer.stop.is_set():
                    return
                source = Path(record[side])
                viewer.copies[side] = isolate_file(source, viewer.directory / (side + source.suffix.lower()))
            if viewer.stop.is_set():
                return
            self._state(viewer, 'starting')
            viewer.guard = ProcessGuard(allow_fallback=self.headless)
            command = [self.python, '-m', 'docfit_engine.diff_host']
            if self.headless:
                command.append('--headless')
            env = os.environ.copy()
            # Child copy root is fixed by LOCALAPPDATA, also for isolated test roots.
            if self.root != copy_root():
                if self.root.name != 'diff' or self.root.parent.name != 'HwpAutoDocFit':
                    raise DiffError('INVALID_COPY_ROOT')
                env['LOCALAPPDATA'] = str(self.root.parent.parent)
            viewer.process = viewer.guard.spawn(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE, bufsize=0, close_fds=True,
                                                cwd=str(Path(__file__).resolve().parent.parent), env=env)
            threading.Thread(target=self._read, args=(viewer,), daemon=True).start()
            threading.Thread(target=self._drain_stderr, args=(viewer,), daemon=True).start()
            self._state(viewer, 'opening')
            self._send(viewer, 'bootstrap', {'nonce': secrets.token_hex(32), 'viewer_id': viewer.viewer_id,
                       'parent_pid': os.getpid(), 'left': viewer.copies['left'],
                       'right': viewer.copies['right'], 'protocol': 1})
            last_heartbeat = time.monotonic()
            last_navigation = 0
            while not viewer.stop.wait(.05):
                now = time.monotonic()
                if viewer.process.poll() is not None:
                    raise DiffError('HOST_DISCONNECTED')
                with self.lock:
                    if any(now - sent > (15 if method == 'bootstrap' else 3)
                           for sent, method in viewer.pending.values()):
                        raise DiffError('HOST_TIMEOUT')
                    if viewer.latest_navigation and now - last_navigation >= 1 / 30:
                        request_id, params = viewer.latest_navigation
                        viewer.latest_navigation = None
                        self._send(viewer, 'navigate', params, request_id)
                        last_navigation = now
                if now - last_heartbeat >= 2:
                    self._send(viewer, 'heartbeat', {})
                    last_heartbeat = now
        except DiffError as exc:
            self._fail(viewer, exc.code)
        except Exception:
            self._fail(viewer, 'DIFF_PREPARATION_FAILED')
        finally:
            monitor_stop.set()
            self._cleanup(viewer)

    def _cleanup(self, viewer):
        with viewer.close_lock:
            self._state(viewer, 'closing')
            process = viewer.process
            if process is not None:
                try:
                    if process.poll() is None:
                        self._send(viewer, 'close', {'reason': viewer.close_reason})
                        process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._fail(viewer, 'HOST_CLOSE_TIMEOUT')
                    if viewer.guard:
                        viewer.guard.close()
                    if process.poll() is None:
                        process.kill()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self._fail(viewer, 'HOST_TEARDOWN_FAILED')
                        return  # Keep copies while their owning process is alive.
                finally:
                    for stream in (process.stdin, process.stdout, process.stderr):
                        stream.close()
            if viewer.guard:
                viewer.guard.close()
            for entry in viewer.copies.values():
                try:
                    if sha256_file(entry['path']) != entry['sha256']:
                        self._fail(viewer, 'COPY_CHANGED')
                except OSError:
                    self._fail(viewer, 'COPY_CHANGED')
            if viewer.directory and viewer.directory.exists():
                try:
                    for path in viewer.directory.iterdir():
                        path.chmod(stat.S_IWRITE | stat.S_IREAD)
                    shutil.rmtree(viewer.directory)
                except OSError:
                    self._fail(viewer, 'COPY_CLEANUP_FAILED')
            self._state(viewer, 'closed')

    def diff_status(self, viewer_id, after_seq=0):
        if type(after_seq) is not int or after_seq < 0:
            return _error('INVALID_REQUEST')
        with self.lock:
            viewer = self.viewers.get(viewer_id)
            if viewer is None:
                return _error('VIEWER_NOT_FOUND')
            return deepcopy({'ok': True, 'viewer_id': viewer_id, 'state': viewer.state,
                             'seq': viewer.seq, 'error': viewer.error,
                             'events': [e for e in viewer.events if e['seq'] > after_seq],
                             'responses': list(viewer.responses.values()),
                             'resync_required': bool(viewer.events and after_seq < viewer.events[0]['seq'] - 1)})

    def diff_navigate(self, viewer_id, side, page, sync=True):
        if side not in ('left', 'right') or type(page) is not int or page < 1 or type(sync) is not bool:
            return _error('INVALID_REQUEST')
        with self.lock:
            viewer = self.viewers.get(viewer_id)
            if not viewer or viewer.state != 'ready' or viewer.stop.is_set():
                return _error('VIEWER_NOT_READY')
            viewer.navigation_seq += 1
            request_id = str(uuid4())
            if viewer.latest_navigation:
                previous_id, _ = viewer.latest_navigation
                self._cache_response(viewer, {'v': 1, 'id': previous_id, 'viewer_id': viewer_id,
                                              'ok': True, 'result': {'coalesced': True}})
            viewer.latest_navigation = (request_id, {'side': side, 'page': page, 'sync': sync,
                                                    'navigation_seq': viewer.navigation_seq})
            return {'ok': True, 'viewer_id': viewer_id, 'request_id': request_id}

    def diff_close(self, viewer_id, reason='user'):
        if reason not in ('user', 'main_exit', 'cancel'):
            return _error('INVALID_REQUEST')
        with self.lock:
            viewer = self.viewers.get(viewer_id)
            if viewer is None:
                return _error('VIEWER_NOT_FOUND')
            viewer.close_reason = reason
            viewer.stop.set()
            return {'ok': True, 'viewer_id': viewer_id, 'state': viewer.state}

    def close(self):
        with self.lock:
            self.closed = True
            viewers = list(self.viewers.values())
            for viewer in viewers:
                viewer.close_reason = 'main_exit'
                viewer.stop.set()
        for viewer in viewers:
            if viewer.worker:
                viewer.worker.join(timeout=6)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
