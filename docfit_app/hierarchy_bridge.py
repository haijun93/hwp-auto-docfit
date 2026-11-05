"""위계 엔진(hierarchy 실행 파일) 호출 브리지. 설정 hierarchy_engine이 켜졌을 때만 사용한다."""
import json
import subprocess
import sys
from pathlib import Path

TIMEOUT_SECONDS = 5.0
_NAME = "hierarchy.exe" if sys.platform == "win32" else "hierarchy"


def find_executable():
    repository = Path(__file__).resolve().parent.parent
    base = Path(getattr(sys, "_MEIPASS", repository))
    for candidate in (base / "resources" / "hierarchy.exe",
                      repository / "hierarchy" / "target" / "release" / _NAME,
                      repository / "hierarchy" / "target" / "release" / "hierarchy.exe"):
        if candidate.is_file():
            return candidate
    return None


def run_executable(executable, paragraphs, timeout=TIMEOUT_SECONDS):
    """실행 파일을 호출해 결과 dict를 돌려준다. 시간 초과·오류·형식 불일치는 None."""
    try:
        payload = json.dumps({"paragraphs": [
            {"text": str(p.get("text", "")), "indent": int(p.get("indent", 0) or 0),
             "font_size": float(p.get("font_size", 0) or 0)} for p in paragraphs]},
            ensure_ascii=False)
        done = subprocess.run([str(executable)], input=payload.encode("utf-8"),
                              capture_output=True, timeout=timeout, check=False)
        if done.returncode != 0:
            return None
        result = json.loads(done.stdout.decode("utf-8"))
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        return None
    if not isinstance(result, dict) or not isinstance(result.get("levels"), list) \
            or len(result["levels"]) != len(paragraphs):
        return None
    return result


def analyze_levels(paragraphs, settings=None, executable=None, timeout=TIMEOUT_SECONDS):
    """설정 hierarchy_engine이 True일 때만 분석한다. 꺼져 있거나 실패하면 None."""
    if not (settings or {}).get("hierarchy_engine", False):
        return None
    if not paragraphs:
        return {"levels": [], "confidence": 100, "ambiguous": [], "diagnostics": []}
    exe = executable or find_executable()
    if exe is None:
        return None
    return run_executable(exe, paragraphs, timeout)
