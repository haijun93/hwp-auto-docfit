"""몽땅클립보드 스티커 메모형 관리창의 위치·크기·항상 위 설정 저장·복원.

관리창은 앱 창 안에 떠 있는 이동 가능한 창이다. 백그라운드 기록(kagent.exe)과
생명주기가 분리되어 있어 이 모듈은 에이전트에 어떤 명령도 보내지 않는다.
설정은 앱 설정 파일의 ``kclip_window`` 항목 하나에만 저장한다.
"""

SETTINGS_KEY = "kclip_window"
MIN_WIDTH, MIN_HEIGHT = 320, 240
MAX_SIZE = 8000
MAX_OFFSET = 20000
DEFAULTS = {"x": None, "y": None, "width": 460, "height": 620, "always_on_top": False}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value != value:  # NaN
        return None
    return int(round(min(max(value, low), high)))


def normalize(value, base=None):
    """저장값을 검증한다. 잘못된 값은 버리고 ``base``(없으면 기본값)를 쓴다."""
    result = dict(DEFAULTS)
    if isinstance(base, dict):
        result.update(normalize(base))
    if not isinstance(value, dict):
        return result
    for key in ("x", "y"):
        if key in value:
            number = None if value[key] is None else _number(value[key], -MAX_OFFSET, MAX_OFFSET)
            if number is not None or value[key] is None:
                result[key] = number
    for key, low in (("width", MIN_WIDTH), ("height", MIN_HEIGHT)):
        number = _number(value.get(key), low, MAX_SIZE)
        if number is not None:
            result[key] = number
    if isinstance(value.get("always_on_top"), bool):
        result["always_on_top"] = value["always_on_top"]
    return result


def load(store):
    try:
        return normalize(store.read().get(SETTINGS_KEY))
    except Exception:
        return dict(DEFAULTS)


def save(store, payload):
    """기존 저장값에 ``payload``를 덧씌워 저장하고 저장된 값을 돌려준다."""
    saved = {}

    def change(current):
        merged = normalize(payload, base=current.get(SETTINGS_KEY))
        current[SETTINGS_KEY] = merged
        saved.update(merged)

    store.update(change)
    return dict(saved)


def command(store, action, payload=None, apply_topmost=None):
    """``kclip_window`` 화면 명령.

    - ``open``: 저장값을 돌려주고, 저장된 항상 위 설정을 앱 창에 적용한다.
    - ``set``: 위치·크기·항상 위를 저장하고 항상 위를 적용한다.
    - ``close``: 관리창을 닫을 때 앱 창의 원래 항상 위 설정으로 되돌린다(저장값은 유지).
    - ``get``: 저장값만 돌려준다.
    ``apply_topmost(enabled_or_None)``: None이면 앱 본래 설정으로 되돌린다.
    """
    payload = payload if isinstance(payload, dict) else {}
    if action == "get":
        return {"ok": True, "window": load(store)}
    if action == "open":
        window = load(store)
        _apply(apply_topmost, True if window["always_on_top"] else None)
        return {"ok": True, "window": window}
    if action == "set":
        window = save(store, payload)
        _apply(apply_topmost, True if window["always_on_top"] else None)
        return {"ok": True, "window": window}
    if action == "close":
        _apply(apply_topmost, None)
        return {"ok": True, "window": load(store)}
    return {"ok": False, "message": "지원하지 않는 관리창 명령입니다."}


def _apply(apply_topmost, enabled):
    if apply_topmost is None:
        return
    try:
        apply_topmost(enabled)
    except Exception:
        import logging
        logging.getLogger(__name__).warning("몽땅클립보드 관리창 항상 위 적용 실패", exc_info=True)
