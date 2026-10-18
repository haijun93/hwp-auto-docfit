"""OS file locks shared by native backend and legacy configuration writers."""
import os
from pathlib import Path


class LockUnavailable(OSError):
    pass


class ProcessLock:
    def __init__(self, path, *, blocking=True):
        self.path=Path(path);self.blocking=blocking;self.stream=None

    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        descriptor=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
        self.stream=os.fdopen(descriptor,'r+b')
        # Empty lock files work for both flock and msvcrt byte-range locks.
        # Pre-writing a byte here races when two callers create the file at once.
        self.stream.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(),msvcrt.LK_LOCK if self.blocking else msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(),fcntl.LOCK_EX | (0 if self.blocking else fcntl.LOCK_NB))
        except OSError as exc:
            self.stream.close();self.stream=None
            raise LockUnavailable('The storage lock is in use or unavailable') from exc
        return self

    def __exit__(self, *args):
        try:
            self.stream.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(),fcntl.LOCK_UN)
        finally:
            self.stream.close();self.stream=None
