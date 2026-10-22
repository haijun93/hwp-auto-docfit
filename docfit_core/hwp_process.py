"""Track only HWP processes created by this application."""
import csv
import io
from threading import Lock

_lock = Lock()
_owned = set()


def _run(args):
    import subprocess
    return subprocess.run(args, capture_output=True, text=True, check=False,
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                          timeout=3)


def hwp_pids(*, runner=None) -> set[int]:
    result = (runner or _run)(['tasklist', '/FI', 'IMAGENAME eq Hwp.exe', '/FO', 'CSV', '/NH'])
    if result.returncode:
        raise OSError('tasklist failed')
    pids = set()
    for row in csv.reader(io.StringIO(result.stdout)):
        if len(row) >= 2 and row[0].casefold() == 'hwp.exe':
            try:
                pids.add(int(row[1]))
            except ValueError:
                pass
    return pids


def register_owned(pids):
    with _lock:
        _owned.update(pid for pid in pids if isinstance(pid, int) and pid > 0)


def owned_pids():
    with _lock:
        return set(_owned)


def forget(pid):
    with _lock:
        _owned.discard(pid)


def kill_owned(log=None, *, runner=None) -> list[int]:
    runner = runner or _run
    killed = []
    # Serialize cleanup so concurrent callers cannot kill the same registration twice.
    with _lock:
        for pid in sorted(_owned.copy()):
            try:
                if pid not in hwp_pids(runner=runner):
                    _owned.discard(pid)
                    continue
                result = runner(['taskkill', '/PID', str(pid), '/T', '/F'])
                if result.returncode == 0:
                    killed.append(pid)
                    _owned.discard(pid)
            except Exception:
                continue
    if log and killed:
        log(f'앱이 띄운 한/글 강제 종료: {killed}')
    return killed
