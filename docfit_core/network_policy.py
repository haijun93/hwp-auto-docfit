"""폐쇄망(인터넷이 안 되는 PC) 운영 정책.

기본값은 폐쇄망 모드다. 이 모드에서는 앱이 스스로 외부에 접속하지 않는다.
- 시작할 때 업데이트를 확인하지 않는다(수동 확인도 안내만 한다).
- kordoc은 KORDOC_OFFLINE=1로 실행해 AI 모델 내려받기를 막고, npx 내려받기를 쓰지 않는다.

설정 파일의 offline_mode(기본 True)를 따르며, 시험·관리용으로 환경 변수
DOCFIT_OFFLINE=1/0이 설정값보다 우선한다.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

SETTING_KEY = "offline_mode"
DEFAULT_OFFLINE = True


def settings_folder() -> Path:
    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    return Path(appdata) / "HwpAutoDocFit" if appdata else Path.home() / ".hwp_auto_docfit"


def offline_mode() -> bool:
    override = os.environ.get("DOCFIT_OFFLINE", "").strip()
    if override in ("0", "1"):
        return override == "1"
    try:
        with (settings_folder() / "settings.json").open("r", encoding="utf-8") as stream:
            value = json.load(stream).get(SETTING_KEY, DEFAULT_OFFLINE)
    except (OSError, ValueError, AttributeError):
        return DEFAULT_OFFLINE
    return value if isinstance(value, bool) else DEFAULT_OFFLINE


def offline_environment(base: dict[str, str] | None = None) -> dict[str, str]:
    """외부 도구(kordoc·npm·onnxruntime)가 네트워크에 접속하지 않도록 하는 실행 환경."""
    env = dict(os.environ if base is None else base)
    env.update({
        "KORDOC_OFFLINE": "1",
        "ORT_DISABLE_TELEMETRY": "1",
        "npm_config_offline": "true",
        "npm_config_update_notifier": "false",
        "NO_UPDATE_NOTIFIER": "1",
    })
    return env
