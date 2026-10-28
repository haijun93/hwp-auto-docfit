"""작업 수명과 배치 사건 스트림. UI/COM 객체는 저장하지 않는다."""
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import threading
import uuid

from .api_contract import ServiceError

TERMINAL = {'done', 'failed', 'cancelled'}
EVENT_TYPES = TERMINAL | {'started', 'progress', 'item_done', 'item_failed', 'log', 'dialog'}
LIGHT_KINDS = {'inspect', 'preview', 'catalog'}
_creation_lock = threading.Lock()


def _alive(thread):
    return bool(thread is not None and getattr(thread, 'is_alive', lambda: False)())


class JobManager:
    def __init__(self, *, capacity=2000, cancel_timeout=10, cleanup=None, state_path=None):
        self._lock = threading.RLock()
        self._events = deque(maxlen=capacity)
        self._jobs = {}
        self._seq = 0
        self._closed = False
        self.cancel_timeout = cancel_timeout
        self._cleanup = cleanup
        self._state_path = state_path
        self._recover()

    def _recover(self):
        if self._state_path is None:
            return
        import json
        from pathlib import Path
        try:
            records = json.loads(Path(self._state_path).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return
        if not isinstance(records, list):
            return
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get('id'), str):
                continue
            identifier = record['id']
            self._jobs[identifier] = dict(id=identifier, job_id=identifier, kind=record.get('kind', 'unknown'),
                state='queued', progress={'file':0, 'total':0, 'stage':'', 'percent':0},
                params={}, cancel_requested=False, stop=threading.Event(), thread=None, timer=None)
            self.report(identifier, 'failed', {'code':'ORPHANED_JOB', 'message':'이전 실행이 종료되어 작업을 복구하지 않았습니다.'})
        self._persist()

    def _persist(self):
        if self._state_path is None:
            return
        import json
        from pathlib import Path
        path = Path(self._state_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(json.dumps([{'id':j['id'], 'kind':j['kind']} for j in self._jobs.values()
            if j['state'] not in TERMINAL]), encoding='utf-8')
        temporary.replace(path)

    def begin(self, kind, params=None, *, stop_event=None):
        if not isinstance(kind, str) or not kind or (params is not None and not isinstance(params, dict)):
            raise ServiceError('INVALID_INPUT', '작업 종류·입력을 확인해 주세요.')
        with self._lock:
            if self._closed:
                raise ServiceError('BACKEND_CLOSING', '앱이 종료 중입니다.')
            if kind not in LIGHT_KINDS and any(
                    j['kind'] not in LIGHT_KINDS and (j['state'] not in TERMINAL or
                    _alive(j.get('thread'))) for j in self._jobs.values()):
                raise ServiceError('JOB_RUNNING', '문서 작업이 끝난 뒤 다시 실행해 주세요.')
            identifier = str(uuid.uuid4())
            self._jobs[identifier] = dict(id=identifier, job_id=identifier, kind=kind,
                params=deepcopy(params or {}), state='queued', progress={'file':0, 'total':0, 'stage':'', 'percent':0},
                cancel_requested=False, stop=stop_event or threading.Event(), thread=None, timer=None)
            self._persist()
            return identifier

    def start(self, kind, params, runner, *, job_id=None):
        identifier = job_id or self.begin(kind, params)
        def execute():
            self.report(identifier, 'started', {})
            try:
                if not self.cancelled(identifier):
                    result = runner(lambda type, data: self.report(identifier, type, data),
                                    lambda: self.cancelled(identifier))
                else:
                    result = None
                self.report(identifier, 'cancelled' if self.cancelled(identifier) else 'done',
                            {'result': result})
            except Exception as exc:
                self.report(identifier, 'cancelled' if self.cancelled(identifier) else 'failed',
                            {'code':getattr(exc, 'code', 'JOB_FAILED'), 'message':str(exc)})
        thread = threading.Thread(target=execute, daemon=True, name='docfit-job-' + identifier)
        with self._lock:
            self._jobs[identifier]['thread'] = thread
            thread.start()
        return identifier

    def run_inline(self, kind, params, runner):
        """동기 공개 API의 반환값을 유지하면서 같은 문서 슬롯을 사용한다."""
        identifier = self.begin(kind, params)
        self.report(identifier, 'started', {})
        try:
            result = runner(lambda type, data: self.report(identifier, type, data),
                            lambda: self.cancelled(identifier))
            self.report(identifier, 'done', {'result':result})
            return result
        except Exception as exc:
            self.report(identifier, 'cancelled' if self.cancelled(identifier) else 'failed',
                        {'code':getattr(exc, 'code', 'JOB_FAILED'), 'message':str(exc)})
            raise

    def attach(self, identifier, thread):
        """기존 GUI worker의 종료 전 다음 COM 작업이 들어오지 않도록 보유한다."""
        with self._lock:
            self._jobs[identifier]['thread'] = thread

    def thread(self, identifier):
        with self._lock:
            return self._get(identifier)['thread']

    def report(self, identifier, type, data):
        if type not in EVENT_TYPES or not isinstance(data, dict):
            raise ServiceError('INVALID_INPUT', '사건 형식을 확인해 주세요.')
        data = deepcopy(data)
        with self._lock:
            job = self._get(identifier)
            if job['state'] in TERMINAL:
                return
            if type == 'started':
                if job['state'] != 'queued':
                    return
                job['state'] = 'running'
            elif type in TERMINAL:
                if type == 'done' and job['cancel_requested']:
                    type = 'cancelled'
                job['state'] = type
                if job['timer']:
                    job['timer'].cancel()
                if type == 'done':
                    job['progress']['percent'] = 100
            elif type == 'progress':
                job['progress'].update(data)
                job['progress']['percent'] = max(0, min(100, float(job['progress']['percent'])))
                if 'percent' in data:
                    data['percent'] = job['progress']['percent']
            self._seq += 1
            self._events.append(dict(seq=self._seq, job_id=identifier, type=type,
                at=datetime.now(timezone.utc).isoformat(), data=data))
            if type in TERMINAL:
                self._persist()

    def _get(self, identifier):
        if not isinstance(identifier, str) or identifier not in self._jobs:
            raise ServiceError('JOB_NOT_FOUND', '작업을 찾을 수 없습니다.')
        return self._jobs[identifier]

    def status(self, identifier):
        with self._lock:
            job = self._get(identifier)
            return deepcopy({k:job[k] for k in ('id', 'job_id', 'kind', 'state', 'progress', 'cancel_requested')})

    def latest(self):
        with self._lock:
            return self.status(next(reversed(self._jobs))) if self._jobs else None

    def cancelled(self, identifier):
        with self._lock:
            return self._get(identifier)['stop'].is_set()

    def cancel(self, identifier):
        with self._lock:
            job = self._get(identifier)
            if job['state'] not in TERMINAL and not job['cancel_requested']:
                job['cancel_requested'] = True
                job['stop'].set()
                self.report(identifier, 'log', {'code':'CANCEL_REQUESTED', 'message':'안전 지점에서 중단합니다.'})
                job['timer'] = threading.Timer(self.cancel_timeout, self._timeout, (identifier,))
                job['timer'].daemon = True
                job['timer'].start()
            return self.status(identifier)

    def _timeout(self, identifier):
        # 새 작업을 허용하기 전에 정리가 끝나야 한다. 종료 사건은 worker의 실제 종료 뒤에만 낸다.
        with self._lock:
            job = self._get(identifier)
            if job['state'] in TERMINAL:
                return
            try:
                from docfit_core.hwp_process import kill_owned
                killed = (self._cleanup or kill_owned)()
                self.report(identifier, 'log', {'code':'CANCEL_TIMEOUT', 'owned_pids':killed or []})
            except Exception as exc:
                self.report(identifier, 'log', {'code':'CLEANUP_FAILED', 'message':str(exc)})

    def events(self, after_seq=0, max=200):
        if type(after_seq) is not int or after_seq < 0 or type(max) is not int or not 1 <= max <= 200:
            raise ServiceError('INVALID_INPUT', '사건 커서·묶음 크기를 확인해 주세요.')
        with self._lock:
            oldest = self._events[0]['seq'] if self._events else self._seq + 1
            batch = [deepcopy(e) for e in self._events if e['seq'] > after_seq][:max]
            return dict(events=batch, next_seq=batch[-1]['seq'] if batch else after_seq,
                        latest_seq=self._seq, oldest_seq=oldest, gap=after_seq < oldest - 1)

    get_events = events

    def shutdown(self, timeout=10):
        with self._lock:
            self._closed = True
            active = [j['id'] for j in self._jobs.values() if j['state'] not in TERMINAL]
        for identifier in active:
            self.cancel(identifier)
        import time
        deadline = time.monotonic() + timeout
        for identifier in active:
            thread = self._jobs[identifier]['thread']
            if thread and thread is not threading.current_thread():
                thread.join(max(0, deadline - time.monotonic()))
        for identifier in active:
            if self.status(identifier)['state'] not in TERMINAL:
                self._timeout(identifier)


def manager_for(gui):
    # Tk 스레드에서 생성·접근한다.
    with _creation_lock:
        if not isinstance(getattr(gui, '_job_manager', None), JobManager):
            import os
            from pathlib import Path
            folder = Path(os.environ.get('APPDATA') or Path.home()) / 'HwpAutoDocFit'
            gui._job_manager = JobManager(state_path=folder / 'desktop-jobs.json')
        return gui._job_manager


def prepare_legacy(gui):
    """GUI가 대기로 복귀했는데 종료 튜플이 빠진 기존 worker를 실패로 회수한다."""
    manager = manager_for(gui)
    identifier = getattr(gui, '_job_id', None)
    if identifier and not gui.running and manager.status(identifier)['state'] not in TERMINAL:
        if not _alive(manager.thread(identifier)):
            manager.report(identifier, 'failed', {'code':'JOB_INTERRUPTED', 'message':'작업 종료 알림 없이 실행이 끝났습니다.'})
    return manager


def legacy_event(manager, identifier, item):
    """튜플을 JSON 가능한 값만 가진 사건으로 변환한다. 콜백/Event는 전송하지 않는다."""
    if not identifier:
        return
    event, *values = item
    progress = manager.status(identifier)['progress']
    if event == 'doc_begin':
        n, total = int(values[0]), int(values[1])
        manager.report(identifier, 'progress', dict(file=n, total=total, stage='document',
                       percent=100 * (n - 1) / total if total else 0, name=str(values[2])))
    elif event in ('step', 'status', 'guide'):
        manager.report(identifier, 'progress', {'stage':str(values[0])})
    elif event == 'progress':
        fraction = max(0, min(100, float(values[0]))) / 100
        total, n = progress['total'], progress['file']
        manager.report(identifier, 'progress', {'percent':100 * (max(0, n - 1) + fraction) / total if total else 0})
    elif event in ('saved', 'document_error'):
        manager.report(identifier, 'item_done' if event == 'saved' else 'item_failed',
                       {'source':str(values[0]), 'output' if event == 'saved' else 'message':str(values[1])})
        manager.report(identifier, 'progress', {'percent':100 * progress['file'] / progress['total'] if progress['total'] else 0})
    elif event in ('finished', 'file_conversion_finished'):
        manager.report(identifier, 'done', {'success':values[0], 'failed':values[1]})
    elif event in ('stopped', 'file_conversion_stopped'):
        manager.report(identifier, 'cancelled', {})
    elif event in ('fatal_error', 'conversion_error'):
        manager.report(identifier, 'failed', {'code':'JOB_FAILED', 'message':str(values[0])})
    elif event == 'log':
        manager.report(identifier, 'log', {'message':str(values[0])})
    elif event.startswith('style_unify_') and event.endswith('_review'):
        manager.report(identifier, 'dialog', {'kind':event})
