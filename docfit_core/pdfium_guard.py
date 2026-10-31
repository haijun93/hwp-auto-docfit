"""PDFium 호출 잠금. PDFium은 문서가 달라도 여러 스레드에서 동시에 부르면 안 된다(앱 전체가 죽을 수 있음).

타임머신 썸네일이 백그라운드에서 PDF를 그리게 되어, 앱 안의 PDFium 사용을 이 잠금 하나로 묶는다.
다른 기능은 무한정 기다리지 않는다: 썸네일이 손상된 PDF에서 멈춰도 변환·압축까지 멈추면 안 되기 때문이다.
"""
from __future__ import annotations

import threading
from contextlib import contextmanager

_LOCK = threading.RLock()
WAIT_SECONDS = 30.0


@contextmanager
def exclusive(timeout=WAIT_SECONDS):
    """기다려 잠그고 실행한다. 시간 안에 못 잠가도 실행은 한다(잠근 쪽이 멈춘 경우)."""
    acquired = _LOCK.acquire(timeout=timeout)
    try:
        yield
    finally:
        if acquired:
            _LOCK.release()


@contextmanager
def try_exclusive(timeout):
    """잠금을 얻었는지 돌려준다. 썸네일처럼 양보해도 되는 작업용."""
    acquired = _LOCK.acquire(timeout=timeout)
    try:
        yield acquired
    finally:
        if acquired:
            _LOCK.release()
