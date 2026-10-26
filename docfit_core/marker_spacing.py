"""항목기호 뒤 HWPX 탭을 일반 빈칸 1개로 정리한다. 원본·본문 탭·Run 서식 보존."""
import os
from pathlib import Path
import re
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
from defusedxml import ElementTree as ET

from .hwpx import open_hwpx_safely, validate_hwpx
from .batch_format import _serialize
from .marker_scheme import classify_marker
from . import text_edit

LEADING_SPACES = {"□": 0, "ㅁ": 0, "ㅇ": 1, "○": 1, "-": 3}

def invariant_rule(rule):
    """분석 원본은 보존하고 실행 규칙의 앞 빈칸만 최신 불변값으로 정한다."""
    if rule and len(rule) >= 2 and rule[0] in LEADING_SPACES:
        return (rule[0], LEADING_SPACES[rule[0]], *rule[2:])
    return rule

SEPARATORS = " \t\u00a0\u3000"
INLINE = {"tab": "\t", "fwSpace": " ", "nbSpace": " ", "lineBreak": "\n"}

def _tag(e):
    return e.tag.rsplit("}", 1)[-1]

def xml_text(element):
    """hp:t.text와 인라인 제어 뒤 tail을 순서대로 읽는다."""
    parts = []
    for t in element.iter():
        if _tag(t) != "t":
            continue
        parts.append(t.text or "")
        for child in t:
            parts.append(INLINE.get(_tag(child), ""))
            parts.append(child.tail or "")
    return "".join(parts)

def normalize_paragraph(p):
    # Never flatten fields, shapes, table cells or paragraphs with embedded objects.
    if any(_tag(x) in {"tbl", "pic", "ole", "fieldBegin", "fieldEnd"} for x in p.iter()):
        return False
    value = xml_text(p)
    classified = classify_marker(value)
    if classified is None:
        if re.match(r"^\s*[0-9]{4}[.．][0-9]{1,2}[.．][0-9]{1,2}", value):
            return False
        tight = re.match(
            r"^\s*([□ㅁㅇ○※•]|-(?!\d)|[①-⑳]|[0-9]{1,2}[.．]|[가나다라마바사아자차카타파하][.．]|[Ⅰ-Ⅿ]+[.．])(?=\S)",
            value,
        )
        if tight is None:
            return False
        marker_end = tight.end()
    else:
        marker_end = classified[1]
    end = marker_end
    while end < len(value) and value[end] in SEPARATORS:
        end += 1
    if end == len(value) or value[end] in "\r\n":
        return False
    # Account for controls before the marker (paragraph indentation), which
    # text_edit deliberately omits. Only prefix separator controls are replaced.
    position, before, selected = 0, 0, []
    for run in p:
        if _tag(run) != "run":
            continue
        for t in run:
            if _tag(t) != "t":
                continue
            position += len(t.text or "")
            for child in t:
                token = INLINE.get(_tag(child), "")
                if token:
                    if position < marker_end:
                        before += 1
                    elif marker_end <= position < end and token in SEPARATORS:
                        selected.append((t, child))
                    position += 1
                position += len(child.tail or "")
    if value[marker_end:end] == " " and not selected:
        return False
    for parent, node in reversed(selected):
        index = list(parent).index(node)
        replacement = " " + (node.tail or "")
        if index:
            previous = parent[index-1]
            previous.tail = (previous.tail or "") + replacement
        else:
            parent.text = (parent.text or "") + replacement
        parent.remove(node)
    literal = text_edit.paragraph_text(p)
    start = marker_end-before
    stop = start+(end-marker_end)
    text_edit.apply_text(p, literal[:start]+" "+literal[stop:])
    for cache in list(p):
        if _tag(cache) == "linesegarray":
            p.remove(cache)
    expected = value[:marker_end]+" "+value[end:]
    if xml_text(p) != expected:
        raise RuntimeError("항목기호 빈칸 처리의 본문 보존 검사 실패")
    return True

def normalize_hwpx(source, target):
    source, target = Path(source), Path(target)
    if source.resolve() == target.resolve() or target.exists() or target.is_symlink():
        raise ValueError("항목기호 빈칸 처리는 새 작업용 사본에만 적용합니다.")
    with open_hwpx_safely(source) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    changes = 0
    rewritten = []
    for info, original in entries:
        payload = original
        if re.fullmatch(r"Contents/section\d+\.xml", info.filename):
            root = ET.fromstring(original)
            changed = sum(normalize_paragraph(p) for p in root if _tag(p) == "p")
            if changed:
                payload = _serialize(root, original)
                changes += changed
        rewritten.append((info, payload))
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".marker_spaces_", dir=target.parent) as folder:
        staged = Path(folder)/"document.hwpx"
        with ZipFile(staged, "w") as archive:
            for info, payload in rewritten:
                archive.writestr(info, payload)
        validate_hwpx(staged)
        os.replace(staged, target)
    return changes
