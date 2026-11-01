"""이름 변경 대상 항목과 이름 분해."""
from __future__ import annotations

import os
from dataclasses import dataclass


class RuleError(ValueError):
    """규칙 옵션이 잘못됐거나(규칙 단계) 특정 항목에 적용할 수 없을 때(항목 단계)."""


def split_name(name):
    """이름을 (stem, ext)로 나눈다. ext는 점을 포함하고, '.bashrc'처럼 점으로 시작하는 이름은 확장자가 없다."""
    dot = name.rfind(".")
    if dot <= 0:
        return name, ""
    return name[:dot], name[dot:]


@dataclass(frozen=True)
class Entry:
    id: str
    path: str
    size: int = 0
    mtime: float = 0.0
    ctime: float = 0.0
    is_folder: bool = False

    @property
    def folder(self):
        return os.path.dirname(self.path)

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def stem(self):
        return split_name(self.name)[0]

    @property
    def ext(self):
        return split_name(self.name)[1]

    @classmethod
    def from_path(cls, path, entry_id=None):
        path = os.path.abspath(path)
        st = os.stat(path)
        # Windows의 st_ctime은 생성 시각이다. 다른 OS는 st_birthtime이 있으면 그것을 쓴다.
        ctime = getattr(st, "st_birthtime", None) or st.st_ctime
        return cls(entry_id or path, path, st.st_size, st.st_mtime, ctime, os.path.isdir(path))

    def fingerprint(self):
        return (self.size, int(self.mtime * 1000))
