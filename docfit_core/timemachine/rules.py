"""타임머신 대상 규칙: 포함 확장자, 운영체제·브라우저·임시 파일 제외, 작업 시각 정의.

사용자 결정(2026-11-01): 작업 시각 = max(생성, 수정), 복사 가능성 표시, '수정 시각만' 설정 가능.
"""
from __future__ import annotations

import fnmatch
import os
import stat

KINDS = {
    "hwp": (".hwp", ".hwpx", ".hwt"),
    "doc": (".doc", ".docx", ".txt", ".md"),
    "sheet": (".xls", ".xlsx", ".xlsm", ".csv"),
    "slide": (".ppt", ".pptx"),
    "pdf": (".pdf",),
    "image": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"),
}
EXT_KIND = {ext: kind for kind, exts in KINDS.items() for ext in exts}

# 폴더 이름(대소문자 무시)이 이것이면 그 아래 전체를 건너뛴다.
EXCLUDED_DIRS = frozenset(name.casefold() for name in (
    "Windows", "Program Files", "Program Files (x86)", "ProgramData", "$Recycle.Bin", "System Volume Information",
    "AppData", "Temp", "Packages", "User Data", "Cache", "Code Cache", "GPUCache", "node_modules", ".git", ".venv",
    "venv", "__pycache__", ".dart_tool", ".gradle", ".idea", ".vscode",
))
EXCLUDED_NAMES = ("~$*", "~WRL*.tmp", "*.tmp", "*.crdownload", "*.part", "Thumbs.db", "desktop.ini", "*.asv",
                  "*.bak", "*.hwp.tmp", ".~lock.*", "*(무결성검사).json", ".rename-tmp-*")
COPY_SLACK_SECONDS = 2.0
_HIDDEN = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 2) | getattr(stat, "FILE_ATTRIBUTE_SYSTEM", 4)
_RECALL = 0x00400000 | 0x00040000 | 0x00001000  # RECALL_ON_DATA_ACCESS · RECALL_ON_OPEN · OFFLINE


class Rules:
    """설정으로 바꿀 수 있는 규칙 묶음(확장자 추가, 제외 폴더·이름 추가, 작업 시각 방식, 숨김 포함)."""

    def __init__(self, *, extra_extensions=(), extra_dirs=(), extra_names=(), time_mode="max", include_hidden=False):
        if time_mode not in ("max", "mtime"):
            raise ValueError("time_mode")
        self.extensions = dict(EXT_KIND)
        for ext in extra_extensions:
            ext = ext.lower() if ext.startswith(".") else "." + ext.lower()
            self.extensions.setdefault(ext, "other")
        self.dirs = EXCLUDED_DIRS | {d.casefold() for d in extra_dirs}
        self.names = tuple(n.casefold() for n in (*EXCLUDED_NAMES, *extra_names))
        self.time_mode = time_mode
        self.include_hidden = include_hidden

    def kind(self, name):
        return self.extensions.get(os.path.splitext(name)[1].lower())

    def skip_dir(self, name, attributes=0):
        if name.casefold() in self.dirs:
            return True
        return bool(not self.include_hidden and (attributes & _HIDDEN or name.startswith(".")))

    def skip_file(self, name, attributes=0):
        if self.kind(name) is None:
            return True
        folded = name.casefold()
        if any(fnmatch.fnmatchcase(folded, pattern) for pattern in self.names):
            return True
        return bool(not self.include_hidden and attributes & _HIDDEN)

    def work_time(self, ctime, mtime):
        """(작업 시각, 표시 플래그). 플래그: 'new'(새로 만든 뒤 저장), 'copied'(생성이 수정보다 늦음 = 복사 가능성)."""
        flags = []
        if ctime > mtime + COPY_SLACK_SECONDS:
            flags.append("copied")
        elif abs(ctime - mtime) <= COPY_SLACK_SECONDS:
            flags.append("new")
        value = mtime if self.time_mode == "mtime" else max(ctime, mtime)
        return value, flags


def cloud_only(attributes):
    """OneDrive '클라우드에만 있음': 내용을 읽으면 내려받기가 시작되므로 썸네일을 만들지 않는다."""
    return bool(attributes & _RECALL)
