"""자연 정렬과 번호 붙이기 순서."""
from __future__ import annotations

import re
import unicodedata

_DIGITS = re.compile(r"(\d+)")


def natural_key(text):
    """'file2' < 'file10' 순서가 되도록 숫자 덩어리를 정수로 비교한다(대소문자 무시)."""
    text = unicodedata.normalize("NFC", text).casefold()
    return [(0, int(part), part) if part.isdigit() else (1, 0, part) for part in _DIGITS.split(text) if part]


def number_sequence(entries, *, start=1, step=1, per_folder=False):
    """목록 순서대로 번호를 준다. 폴더별이면 폴더마다 따로 세며, 다른 폴더 파일이 사이에 끼어도 끊기지 않는다."""
    counters = {}
    result = []
    for entry in entries:
        key = entry.folder.casefold() if per_folder else ""
        index = counters.get(key, 0)
        counters[key] = index + 1
        result.append(start + index * step)
    return result
