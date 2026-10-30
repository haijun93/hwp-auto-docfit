"""외부 접속 정책.

폐쇄망 모드 설정은 2.0.4에서 없앴다(사용자 지시). 앱은 업데이트 확인만 외부에 접속하고,
변환 엔진(kordoc)은 언제나 모델 내려받기·npm 접속 없이 앱에 포함된 것만 쓴다(kordoc_bridge).
시험·관리용 환경 변수 DOCFIT_OFFLINE=1이면 업데이트도 내부 GitLab에만 접속한다.
"""
from __future__ import annotations

import os
from pathlib import Path



def settings_folder() -> Path:
    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    return Path(appdata) / "HwpAutoDocFit" if appdata else Path.home() / ".hwp_auto_docfit"


def offline_mode() -> bool:
    """시험·관리용 DOCFIT_OFFLINE=1일 때만 참(설정 파일의 옛 offline_mode 값은 쓰지 않는다)."""
    return os.environ.get("DOCFIT_OFFLINE", "").strip() == "1"


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
