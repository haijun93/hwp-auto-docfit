"""Run the Ctrl+Z replacement gate on a disposable, app-owned Hancom test document.

This script is intentionally not invoked by implementation or unit tests.
It never opens a user document, saves a document, or kills a process.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time


def _text(app):
    return str(app.GetTextFile("HWPML2X", ""))


def measure(app, replacement: str) -> dict:
    """Replace a marked paragraph in a caller-created disposable test document."""
    app.HAction.Run("MoveDocEnd")
    app.HAction.Run("InsertText")
    action = app.HAction.GetDefault("InsertText", app.HParameterSet.HInsertText.HSet)
    action.SetItem("Text", "\r\nLIVELINK_GATE_ORIGINAL")
    if not app.HAction.Execute("InsertText", app.HParameterSet.HInsertText.HSet):
        raise RuntimeError("Could not create gate marker in disposable test document")
    app.HAction.Run("MoveParaBegin")
    start = tuple(app.GetPos())
    app.HAction.Run("MoveParaEnd")
    app.HAction.Run("MoveSelParaBegin")
    app.HAction.Run("MoveSelParaEnd")
    before = _text(app)
    if "LIVELINK_GATE_ORIGINAL" not in before:
        raise RuntimeError("Gate marker was not found in document snapshot")
    # Replace the active selected block exactly once; then issue exactly one Ctrl+Z equivalent.
    app.HAction.Run("Cancel")
    app.SetPos(*start)
    app.HAction.Run("MoveParaBegin")
    app.HAction.Run("MoveSelParaEnd")
    app.HAction.GetDefault("InsertText", app.HParameterSet.HInsertText.HSet)
    params = app.HParameterSet.HInsertText
    params.Text = replacement
    if not app.HAction.Execute("InsertText", params.HSet):
        raise RuntimeError("Gate replacement failed")
    changed = _text(app)
    app.HAction.Run("Undo")
    recovered = _text(app)
    return {"passed": changed != before and recovered == before, "undo_steps": 1,
            "original_sha256": _sha(before), "changed_sha256": _sha(changed),
            "recovered_sha256": _sha(recovered), "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}


def _sha(text):
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--ack-disposable-test-document", action="store_true")
    parser.add_argument("--enable-gate", action="store_true", help="기록 PASS 시 설정 live_replace_gate=true")
    args = parser.parse_args()
    if not args.ack_disposable_test_document:
        parser.error("시험용 한/글에서 만든 임시 문서에서만 실행할 수 있습니다")
    if os.environ.get("HWP_AUTODOCFIT_GATE_TEST") != "1":
        parser.error("시험 실행 환경에서 HWP_AUTODOCFIT_GATE_TEST=1을 설정해야 합니다")
    # COM object injection is explicit: caller must construct the test instance and pass it
    # to measure(); this CLI never discovers or attaches to arbitrary running Hangul sessions.
    parser.error("시험용 한/글 객체 주입기는 시험 하네스에서 measure(app, replacement)를 호출하세요")


if __name__ == "__main__":
    main()
