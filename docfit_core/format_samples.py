"""서식예시 폴더(C:\\HWP_AUTODOCFIT\\서식예시)의 예시 HWPX와 서식 설정을 맞춘다(알파, 2026-10-10 사용자 요청).

- 서식마다 예시 파일(HWPX) 하나를 사용자 폴더에 두고, 사용자는 그 파일을 한/글에서 직접 고쳐 서식을 바꾼다.
- 앱은 파일을 넣을 때의 사본(원본 사본)을 설정 폴더에 따로 둔다. '한 번에 적용'을 시작할 때 예시 파일의 해시가
  기록과 다르면, 원본 사본과 지금 파일을 같은 분석기로 읽어 '달라진 값만' 서식 설정에 옮긴다. 분석기의 한계로
  생기는 차이(사용자가 손대지 않은 값)는 양쪽에 똑같이 나타나 서로 지워지므로 설정을 흔들지 않는다.
- 이 모듈은 한/글·화면 없이 시험할 수 있는 순수 함수만 둔다. 실제 분석(hwpx_서식_분석)은 앱이 넘긴다.
"""

from __future__ import annotations

import copy
import hashlib
import re
from pathlib import Path

APP_HOME = Path(r"C:\HWP_AUTODOCFIT")      # 보안 모듈 DLL과 서식예시 폴더를 두는 최상위 폴더
LEGACY_APP_HOME = Path(r"C:\HwpAutomation")  # v1.72까지 보안 모듈 DLL을 두던 폴더
SAMPLE_FOLDER_NAME = "서식예시"
STANDARD_FILE = "기본 서식.hwpx"
# 앱 폴더 아래 다른 하위 폴더(2026-10-10 사용자 요청): 보안 모듈 DLL, 한/글 글자 상용구(HWP.IDO), 본문 상용구(IDIOM\*.HWP).
DLL_FOLDER_NAME = "dll"
DLL_FILE = "HwpAutoDocFitSecurity.dll"
REGISTRY_VALUE = "HwpAutoDocFitSecurity"          # HKCU\Software\HNC\HwpAutomation\Modules 값 이름 = RegisterModule 두 번째 인자
LEGACY_DLL_FILE = "MapoHwpAutoDocFitSecurity.dll"
LEGACY_REGISTRY_VALUE = "MapoHwpAutoDocFitSecurity"
CHAR_IDIOM_FOLDER_NAME = "글자상용구"
BODY_IDIOM_FOLDER_NAME = "본문상용구"


def app_subfolder(name: str, home: Path = APP_HOME) -> Path:
    return Path(home) / name

# 예시 파일에서 읽어 설정에 옮기는 서식 값 묶음. 이름·기관·요약처럼 사람이 붙인 값은 옮기지 않는다.
SYNC_KEYS = ("format", "options", "table_format", "precise_tables", "form_tables", "table_style", "report_header")


def sample_folder(home: Path = APP_HOME) -> Path:
    return Path(home) / SAMPLE_FOLDER_NAME


def file_name_for(name: str, standard: bool = False) -> str:
    """서식 이름으로 예시 파일 이름을 만든다(파일 이름에 못 쓰는 글자는 _로)."""
    if standard:
        return STANDARD_FILE
    safe = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "_", str(name or "")).strip(" ._")[:60] or "서식"
    if safe + ".hwpx" == STANDARD_FILE:
        safe += " (사용자)"
    return safe + ".hwpx"


def digest(path) -> str | None:
    """파일 SHA-256. 없거나 읽지 못하면 None."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()
    except OSError:
        return None


def snapshot(profile: dict) -> dict:
    return {k: copy.deepcopy(profile[k]) for k in SYNC_KEYS if k in (profile or {})}


def _merge(target, base, new, path, changed):
    """base → new에서 달라진 값만 target에 옮긴다. 옮긴 경로를 changed에 남긴다. 고친 target을 돌려준다."""
    if base == new:
        return target
    if isinstance(new, dict) and isinstance(base, dict) and isinstance(target, dict):
        for key in new:
            if key in base:
                target[key] = _merge(target.get(key, copy.deepcopy(base[key])), base[key], new[key],
                                     path + [str(key)], changed)
            else:
                target[key] = copy.deepcopy(new[key])
                changed.append("/".join(path + [str(key)]))
        return target
    seq = (list, tuple)       # JSON으로 저장한 서식은 리스트, 앱 기본값은 튜플일 수 있다
    if (isinstance(new, seq) and isinstance(base, seq) and isinstance(target, seq)
            and len(new) == len(base) == len(target)):
        target = list(target)
        for i, (b, n) in enumerate(zip(base, new)):
            target[i] = _merge(target[i], b, n, path + [str(i)], changed)
        return target
    changed.append("/".join(path))
    return copy.deepcopy(new)


def merge_changes(profile: dict, base: dict, new: dict) -> list[str]:
    """원본 사본 분석(base)과 지금 파일 분석(new)의 차이만 profile에 옮긴다(순수 함수, profile은 고침).

    사용자가 앱 화면(서식 세부사항 등)에서 고친 값은, 예시 파일에서 같은 값을 다시 고치지 않는 한 그대로 둔다.
    돌려주는 값은 옮긴 값의 경로 목록(예: 'format/기호_규칙/0/3')이다.
    """
    changed: list[str] = []
    for key in SYNC_KEYS:
        b, n = (base or {}).get(key), (new or {}).get(key)
        if n is None or b == n:
            continue
        if key not in profile or b is None:
            profile[key] = copy.deepcopy(n)
            changed.append(key)
        else:
            profile[key] = _merge(profile[key], b, n, [key], changed)
    return changed


_KEY_NAMES = {"format": "서식", "options": "선택 사항", "table_format": "표 글자", "precise_tables": "정밀 표",
              "form_tables": "서식 표", "table_style": "표 모양", "report_header": "보고서 머리"}


def describe(changed: list[str], limit: int = 6) -> str:
    """옮긴 값 경로를 로그용 짧은 문장으로."""
    if not changed:
        return "바뀐 서식 값 없음"
    shown = []
    for path in changed[:limit]:
        head, _, rest = path.partition("/")
        shown.append(_KEY_NAMES.get(head, head) + (f"·{rest}" if rest else ""))
    more = f" 외 {len(changed) - limit}개" if len(changed) > limit else ""
    return ", ".join(shown) + more
