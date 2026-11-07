"""job 사건·오류 봉투 공용 도우미 (docs/IPC_JOBS_DESIGN.md 5.4·5.5). 외부 의존성 없음."""
import json
import time

from .api_contract import ServiceError

RESULT_MAX = 262144
MESSAGE_MAX = 500
PROGRESS_MIN_INTERVAL = 0.1  # 초당 10건 상한


def job_error(exc):
    """예외 → JobError {code,message,recoverable}. 기존 {code,message}에 recoverable만 추가."""
    if isinstance(exc, ServiceError):
        code, recoverable = exc.code, exc.recoverable
    elif isinstance(exc, (ValueError, TypeError, IndexError, KeyError)):
        code, recoverable = 'INVALID_INPUT', True
    else:
        code = getattr(exc, 'code', None)
        code = code if isinstance(code, str) and code else 'JOB_FAILED'
        recoverable = bool(getattr(exc, 'recoverable', True))
    return {'code': code, 'message': str(exc)[:MESSAGE_MAX], 'recoverable': recoverable}


def fit_result(result, limit=RESULT_MAX):
    """job_status용 결과. 직렬화가 한도를 넘으면 RESULT_TOO_LARGE 표식만 돌려준다."""
    try:
        size = len(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    except (TypeError, ValueError):
        return {'result_omitted': 'RESULT_NOT_SERIALIZABLE'}
    if size > limit:
        return {'result_omitted': 'RESULT_TOO_LARGE', 'size': size}
    return result


class ProgressThrottle:
    """진행 사건을 초당 10건 이하로 합친다. 마지막 값은 flush()로 보낸다."""

    def __init__(self, report, *, interval=PROGRESS_MIN_INTERVAL, clock=time.monotonic):
        self._report, self._interval, self._clock = report, interval, clock
        self._last = None
        self._pending = None

    def __call__(self, data):
        now = self._clock()
        if self._last is None or now - self._last >= self._interval:
            self._last, self._pending = now, None
            self._report('progress', data)
        else:
            self._pending = data

    def flush(self):
        if self._pending is not None:
            data, self._pending = self._pending, None
            self._report('progress', data)
