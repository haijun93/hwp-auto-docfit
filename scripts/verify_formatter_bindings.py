"""Exercise formatter import/patch compatibility and runtime isolation, without COM."""
import builtins
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def verify():
    from docfit_engine import formatter
    from docfit_engine.runtime import resolve, session_for

    # This import must succeed before the bootstrap has installed any symbol.
    from docfit_engine.formatter import 설정_파일_경로
    assert 설정_파일_경로.__globals__ is vars(formatter)
    marker = Path("c21-settings")
    formatter.설정_파일명 = "settings.json"
    with patch("docfit_engine.formatter.설정_폴더", return_value=marker) as dependency:
        assert 설정_파일_경로() == marker / "settings.json"
        dependency.assert_called_once_with()

    manifest = json.loads((ROOT / "scripts/formatter_split_manifest.json").read_text(encoding="utf-8"))
    moved = [name for names in manifest["modules"].values() for name in names]
    namespace = {"__name__": "c21_engine", "__builtins__": builtins.__dict__}
    for name in moved:
        namespace[name] = resolve("docfit_engine.formatter", name, namespace)
        raw = getattr(formatter, name)
        assert raw.__globals__ is vars(formatter), name
        assert raw.__module__ == "docfit_engine.formatter", name
        assert raw.__qualname__ == name, name
        template, facade = session_for(namespace).templates[name]
        assert template is raw, name
        assert facade is namespace[name], name

    patch_calls = 1
    if "제목_문단들" in moved:
        from docfit_engine.formatter import 제목_문단들
        with patch("docfit_engine.formatter.제목_자식", return_value=None) as dependency:
            assert 제목_문단들(object()) == []
            dependency.assert_called_once()
        patch_calls += 1
    if "_표_서명" in moved:
        # table module calls the title module's primitive through formatter.
        import hashlib
        import re
        formatter.hashlib = hashlib
        formatter.re = re
        with patch("docfit_engine.formatter.제목_셀들", return_value=[]) as dependency:
            formatter._표_서명([])
            dependency.assert_called_once_with([])
        patch_calls += 1

    isolated = 0
    if "제목_담당자_글_반영" in moved:
        session = session_for(namespace)
        first = session.new_context(state={"제목_담당자_글": "first"})
        second = session.new_context(state={"제목_담당자_글": "second"})
        first.invoke("제목_담당자_글_반영", "changed")
        assert first.state["제목_담당자_글"] == "changed"
        assert second.state["제목_담당자_글"] == "second"
        assert "제목_담당자_글" not in namespace
        assert first.function("제목_담당자_글_반영").__globals__ is first.state
        # Existing runtime callback overrides continue to resolve in run state.
        second.state["제목_자식"] = lambda *args: None
        assert second.invoke("제목_문단들", object()) == []
        isolated = 2

    try:
        formatter._install(_docfit_namespace=namespace, _docfit_symbol="C21_UNKNOWN")
    except KeyError as exc:
        assert exc.args == ("C21_UNKNOWN",)
    else:
        raise AssertionError("unknown symbol did not raise KeyError")
    return {"raw_exports_checked": len(moved), "effective_patch_calls": patch_calls,
            "isolated_contexts": isolated, "unknown_symbol": "KeyError", "status": "PASS"}


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
