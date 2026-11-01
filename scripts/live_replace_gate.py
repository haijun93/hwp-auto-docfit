"""Run the Ctrl+Z replacement gate on a disposable, app-owned Hancom test document.

This script is intentionally not invoked by implementation or unit tests.
It never opens a user document, saves a document, or kills a process.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace


def _text(app):
    return str(app.GetTextFile("HWPML2X", ""))


def _sha(value):
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def measure(app, disposable_copy, replacement: str) -> dict:
    """Measure replacement/undo on an explicitly opened disposable copy.

    The caller supplies both COM objects; this module never attaches to a running
    user session, saves, or terminates a process.
    """
    path = str(getattr(disposable_copy, "FullName", "") or "")
    if not path or not Path(path).is_file():
        raise ValueError("disposable copy must be an existing file")
    before = _text(app)
    if not before:
        raise RuntimeError("Could not read disposable copy as HWPML2X")
    block = app.GetTextFile("HWPML2X", "saveblock:true")
    if not block:
        raise RuntimeError("Could not save selected block")
    params = app.HParameterSet.HInsertText
    app.HAction.GetDefault("InsertText", params.HSet)
    params.Text = replacement
    if app.HAction.Execute("InsertText", params.HSet) is False:
        raise RuntimeError("Replacement failed")
    changed = _text(app)
    if not app.HAction.Run("Undo"):
        raise RuntimeError("Undo failed")
    recovered = _text(app)
    return {"passed": changed != before and recovered == before,
            "undo_steps": 1, "original_sha256": _sha(before),
            "changed_sha256": _sha(changed), "recovered_sha256": _sha(recovered)}


def _select_test_marker(app):
    """Append and select a marker in the already copied disposable document."""
    app.HAction.Run("MoveDocEnd")
    params = app.HParameterSet.HInsertText
    app.HAction.GetDefault("InsertText", params.HSet)
    params.Text = "\r\nLIVELINK_GATE_ORIGINAL"
    if not app.HAction.Execute("InsertText", params.HSet):
        raise RuntimeError("Could not create gate marker")
    app.HAction.Run("MoveParaBegin")
    app.HAction.Run("MoveSelParaEnd")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Disposable test HWP/HWPX input; the script only opens a temporary copy")
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args(argv)
    result = {"passed": False, "code": "GATE_FAILED"}
    app = None
    try:
        source = args.source.resolve(strict=True)
        if not source.is_file():
            raise ValueError("source must be a test document")
        import shutil, tempfile
        with tempfile.TemporaryDirectory(prefix="docfit_live_gate_") as folder:
            copied = Path(folder) / source.name
            shutil.copy2(source, copied)
            import win32com.client
            app = win32com.client.DispatchEx("HWPFrame.HwpObject")
            opened = app.Open(str(copied), "", "forceopen:true")
            if opened is False:
                raise RuntimeError("Could not open disposable copy")
            _select_test_marker(app)
            result = measure(app, SimpleNamespace(FullName=str(copied)), "LIVELINK_GATE_REPLACED")
            result.update({"code": "OK" if result["passed"] else "UNDO_MISMATCH",
                           "source_sha256": __import__("hashlib").sha256(source.read_bytes()).hexdigest(),
                           "copy_only": True, "saved": False, "force_terminated": False})
            app.Clear(1)
            app.Quit()
            app = None
    except Exception as exc:
        result.update({"message": str(exc), "copy_only": True, "saved": False,
                       "force_terminated": False})
    finally:
        if app is not None:
            try:
                app.Clear(1)
            except Exception:
                pass
            try:
                app.Quit()
            except Exception:
                pass
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    main()
