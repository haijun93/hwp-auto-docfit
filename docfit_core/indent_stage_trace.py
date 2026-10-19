"""Opt-in, read-only COM paragraph-indent trace for a local formatting run.

Set ``DOCFIT_INDENT_TRACE_JSONL`` to an output file to record marker geometry
after each pipeline stage.  The normal application path has no trace overhead.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re


_MARKER = re.compile(r"^\s*(?:[ㅁ□ㅇ○](?=\s)|\*\*?(?=\s)|-(?=\s))")


def trace_enabled() -> bool:
    return bool(os.environ.get("DOCFIT_INDENT_TRACE_JSONL"))


def capture_stage(stage: str, hwp, start, text_at_caret, next_paragraph) -> None:
    """Record COM left/indent for every main-body marker, restoring the caret."""
    destination = os.environ.get("DOCFIT_INDENT_TRACE_JSONL")
    if not destination or hwp is None:
        return
    original = hwp.GetPos()
    entries = []
    try:
        start()
        while True:
            text = text_at_caret() or ""
            if _MARKER.match(text):
                left = int(hwp.ParaShape.Item("LeftMargin"))
                indent = int(hwp.ParaShape.Item("Indentation"))
                entries.append({
                    "position": list(hwp.GetPos()[:2]),
                    "text": text.strip(),
                    "left_com": left,
                    "indent_com": indent,
                    "first_origin_com": left + indent,
                    "continuation_origin_com": left,
                })
            if not next_paragraph():
                break
    finally:
        hwp.SetPos(*original)
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"stage": stage, "paragraphs": entries}, ensure_ascii=False) + "\n")


def capture_saved_stage(stage: str, hwpx_path: str | Path) -> None:
    """Record saved HWPX values before/after the last reference repair."""
    destination = os.environ.get("DOCFIT_INDENT_TRACE_JSONL")
    if not destination:
        return
    from .release_format_audit import inspect_hanging_indent

    findings = inspect_hanging_indent(hwpx_path)["findings"]
    entries = []
    for item in findings:
        left, indent = item["left"], item["indent"]
        if left is None or indent is None:
            continue
        entries.append({
            "text": item["text"].strip(),
            "left_xml": left,
            "indent_xml": indent,
            "first_origin_xml": left + indent,
            "continuation_origin_xml": left,
        })
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"stage": stage, "paragraphs": entries}, ensure_ascii=False) + "\n")
