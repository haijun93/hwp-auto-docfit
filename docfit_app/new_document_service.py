"""Create a writable document from a registered HWPX snapshot."""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def create_copy(source, documents_dir, name=None):
    source = Path(source).expanduser().resolve(strict=True)
    if source.suffix.lower() != '.hwpx' or not source.is_file():
        raise ValueError('등록된 HWPX 서식을 찾을 수 없습니다.')
    folder = Path(documents_dir).expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    stem = Path(name).stem.strip() if name else source.stem
    if not stem or stem in {'.', '..'}:
        stem = source.stem
    target = folder / f'{stem}.hwpx'
    index = 2
    while target.exists():
        target = folder / f'{stem} ({index}).hwpx'
        index += 1
    shutil.copy2(source, target)
    return target


def user_documents():
    return Path(os.environ.get('USERPROFILE', Path.home())) / 'Documents'
