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


# 엔진 Role 번호(hierarchy/src/lib.rs) → 쪽 맞춤 문단 역할. 그 밖의 값은 판정 보류(None).
ENGINE_ROLE_NAMES = {4: "소제목", 5: "본문", 6: "내용", 7: "부연설명"}


def engine_role_of_last(paragraphs, settings=None, executable=None, timeout=TIMEOUT_SECONDS):
    """문단 목록(맥락 포함)의 마지막 문단 역할을 엔진으로 판정한다.

    꺼져 있거나 엔진이 실패·판정 보류면 None이며, 호출한 쪽은 기존 규칙을 그대로 쓴다.
    """
    result = analyze_levels(paragraphs, settings, executable=executable, timeout=timeout)
    if not result or not result["levels"]:
        return None
    return ENGINE_ROLE_NAMES.get(result["levels"][-1])


def _leading_width(text):
    body = str(text or "").rstrip("\r\n")
    return len(body) - len(body.lstrip(" \t 　"))


def engine_roles(items, settings=None, executable=None, timeout=TIMEOUT_SECONDS):
    """서식통일용: (키, 글) 목록(문서 순서)을 엔진 한 번 호출로 분석해 {키: 문단 역할}을 돌려준다.

    꺼져 있거나 엔진이 실패하면 빈 dict(호출한 쪽은 기존 규칙 그대로). 엔진이 판정을 보류한
    문단(장·절·표 칸·모호 등 ENGINE_ROLE_NAMES 밖의 값)은 결과에 넣지 않는다.
    """
    items = list(items)
    if not items or not (settings or {}).get("hierarchy_engine", False):
        return {}
    result = analyze_levels([{"text": text, "indent": _leading_width(text)} for _, text in items],
                            settings, executable=executable, timeout=timeout)
    if not result:
        return {}
    roles = {}
    for (key, _), level in zip(items, result["levels"]):
        role = ENGINE_ROLE_NAMES.get(level)
        if role:
            roles[key] = role
    return roles
