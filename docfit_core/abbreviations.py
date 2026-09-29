"""준말(약어) → 본말 등록표.

한/글의 상용구(준말을 입력하고 Alt+I로 본말을 펼치는 기능)와 같은 개념을 앱 안에 만든 것이다.
'한 번에 적용'을 실행하면 문서의 줄 중 첫 어절이 등록한 준말이고 바로 뒤에 콜론(:)이 이어지는
줄을 본말로 바꾼다. 준말과 콜론 사이에는 빈칸이 있어도 된다.

본말의 종류:
    format  서식 표(제목1·제목2·개요·중제목·붙임). 콜론 뒤 글을 표의 글 칸(제목·개요는 A1, 중제목·붙임은
            번호·'붙임' 글자 다음 칸)에 넣고 준말 줄은 지운다.
    text    문구. 준말과 콜론을 본말로 바꾸고 콜론 뒤 글은 그대로 이어 붙인다.
"""

from __future__ import annotations

import re

# 서식 표 종류 → 화면에 보여 줄 이름
FORMAT_KINDS: dict[str, str] = {
    "title1": "제목 서식1 표",
    "title2": "제목 서식2 표 (쉼표 앞은 부제)",
    "overview": "개요(요지) 서식 표",
    "midtitle": "중제목 서식 표 (준말 끝 숫자 = 로마자 번호, 예: 로1 → Ⅰ)",
    "attach1": "붙임 서식1 표 (1행3열)",
    "attach2": "붙임 서식2 표 (1행2열)",
}
TYPES = ("format", "text")
TYPE_LABELS = {"format": "서식 표", "text": "문구"}

# '기본 준말 넣기'가 넣는 예시 등록(등록표는 처음에는 비어 있다).
DEFAULT_ENTRIES: dict[str, dict] = {
    "제목1": {"type": "format", "value": "title1"},
    "제목2": {"type": "format", "value": "title2"},
    "개요": {"type": "format", "value": "overview"},
    "붙임": {"type": "format", "value": "attach1"},
    **{f"로{n}": {"type": "format", "value": "midtitle"} for n in range(1, 11)},
}

_MAX_KEY = 12
# 준말 별칭: 등록표에 '제목'이 따로 없으면 '제목:'은 '제목1:'로 취급한다.
ALIASES = {"제목": "제목1"}
ROMAN = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"
_MAX_TEXT = 500


def clean_key(key: str) -> str:
    """준말 문자열을 다듬는다. 빈칸·콜론이 있거나 너무 길면 빈 문자열."""
    key = (key or "").strip()
    if not key or len(key) > _MAX_KEY or re.search(r"[\s:：]", key):
        return ""
    return key


def roman_of_key(key: str) -> str:
    """중제목 준말 끝의 숫자(1~12)를 로마자 번호로 바꾼다(로3 → Ⅲ). 숫자가 없거나 범위 밖이면 빈 글."""
    match = re.search(r"(\d{1,2})$", key or "")
    number = int(match.group(1)) if match else 0
    return ROMAN[number - 1] if 1 <= number <= len(ROMAN) else ""


def normalize(entries) -> dict[str, dict]:
    """저장된 등록표를 검사해 올바른 항목만 남긴다(설정 파일이 손상돼도 안전)."""
    result: dict[str, dict] = {}
    if not isinstance(entries, dict):
        return result
    for raw_key, spec in entries.items():
        key = clean_key(str(raw_key))
        if not key or not isinstance(spec, dict):
            continue
        kind, value = spec.get("type"), spec.get("value")
        if kind == "format" and value in FORMAT_KINDS:
            if value == "midtitle" and not roman_of_key(key):
                continue  # 번호를 알 수 없는 중제목 준말은 쓸 수 없다.
            result[key] = {"type": "format", "value": value}
        elif kind == "text" and isinstance(value, str) and value.strip() and len(value) <= _MAX_TEXT:
            result[key] = {"type": "text", "value": value.strip()}
    return result


def resolve_key(word: str, registry: dict[str, dict]):
    """줄 첫 어절을 등록된 준말로 풀어 준다. 등록되어 있으면 그대로, 별칭이면 별칭이 가리키는 등록 준말, 아니면 None."""
    if word in registry:
        return word
    alias = ALIASES.get(word)
    return alias if alias in registry else None


def match_line(text: str, registry: dict[str, dict]):
    """줄의 첫 어절이 등록한 준말이고 콜론이 이어지면 (준말, 콜론 뒤 글, 앞부분 글자 수)를 돌려준다.

    앞부분 글자 수는 줄 앞의 빈칸·준말·빈칸·콜론·빈칸까지의 길이다(문구 바꾸기에서 지울 범위).
    첫 어절에 콜론이 붙어 있어야 하므로 중간에 다른 낱말이 끼면 일치하지 않는다.
    """
    if not registry or not text:
        return None
    match = re.match(r"^(\s*)(\S+?)(\s*)([:：])(\s*)(.*)$", text, re.S)
    if not match:
        return None
    key = resolve_key(match.group(2), registry)
    if key is None:
        # 콜론 앞에 빈칸 없이 붙은 어절 전체가 준말이 아닌 경우(예: "일시:" 처럼 다른 낱말)는 제외
        return None
    return key, match.group(6).strip(), match.end(5)


def split_title2(text: str) -> tuple[str, str]:
    """제목2 글을 (부제, 제목)으로 나눈다. 첫 쉼표 앞이 부제, 뒤가 제목이다. 쉼표가 없으면 부제는 빈 글."""
    text = (text or "").strip()
    match = re.search(r"[,，]", text)
    if not match:
        return "", text
    sub, title = text[:match.start()].strip(), text[match.end():].strip()
    if not sub or not title:  # 한쪽이 비면 나눌 필요가 없다.
        return "", (sub or title)
    return sub, title


def upsert(entries: dict, key: str, kind: str, value: str) -> tuple[dict, str]:
    """등록표에 준말을 추가하거나 같은 준말을 덮어쓴다. (새 등록표, 오류 문구)를 돌려주며 오류가 없으면 문구는 빈 글."""
    clean = clean_key(key)
    if not clean:
        return entries, f"준말은 빈칸·콜론 없이 1~{_MAX_KEY}자로 적어 주세요."
    if kind == "format":
        if value not in FORMAT_KINDS:
            return entries, "서식 표 종류를 골라 주세요."
        if value == "midtitle" and not roman_of_key(clean):
            return entries, "중제목 준말은 끝에 1~12 숫자를 붙여 주세요(예: 로1 → Ⅰ, 로3 → Ⅲ)."
    elif kind == "text":
        value = (value or "").strip()
        if not value:
            return entries, "본말 문구를 적어 주세요."
        if len(value) > _MAX_TEXT:
            return entries, f"본말 문구는 {_MAX_TEXT}자 이하로 적어 주세요."
    else:
        return entries, "본말 종류를 골라 주세요."
    updated = dict(entries)
    updated[clean] = {"type": kind, "value": value}
    return updated, ""


def describe(spec: dict) -> tuple[str, str]:
    """등록 항목을 화면에 보여 줄 (종류 이름, 본말 설명)으로 바꾼다."""
    if spec.get("type") == "format":
        return TYPE_LABELS["format"], FORMAT_KINDS.get(spec.get("value"), str(spec.get("value")))
    return TYPE_LABELS["text"], str(spec.get("value", ""))
