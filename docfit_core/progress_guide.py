"""진행 화면에 보여 줄 작업 유형별 단계 안내 문장.

로그보다 짧고 친절하게, 지금 무엇을 하는지 한 문장으로 알려 준다.
처리 코드가 넘기는 단계 이름을 앞부분 일치로 안내 항목에 연결한다.
"""

# (키, 안내 문장, 이 항목으로 연결할 단계 이름 앞부분)
GUIDE_ITEMS = (
    ("open", "문서를 열고 작업할 준비를 하고 있어요.", ("열기", "변환")),
    ("pre_format", "등록한 준말과 별표(*, **) 위첨자를 먼저 정리하고, 제목·개요·붙임처럼 먼저 정리할 부분의 서식을 맞추고 있어요.",
     ("준말 변환", "별표 위첨자", "붙임 글꼴", "제목·개요·붙임 선행 서식", "표 정밀 서식")),
    ("space", "불필요한 공백과 문장부호 뒤 띄어쓰기를 정리하고 있어요.",
     ("공백 정규화", "문장부호 뒤 공백")),
    ("unify_survey", "문장들을 살펴 문두기호별로 가장 많이 쓴 대표 서식을 찾고 있어요.",
     ("서식통일 조사", "서식통일")),
    ("unify_apply", "표준과 다른 문장만 찾아 서식·내어쓰기·자간·외톨이 글자를 한 번에 정리하고, 맞는 문장은 그대로 둬요.",
     ("서식통일 적용", "서식통일 표준 서식 적용")),
    ("standard", "선택한 표준 서식에 맞춰 글꼴·문단·표 모양을 적용하고 있어요.",
     ("보고서 표준서식", "문두 라벨", "표 서식", "셀 너비", "셀 안쪽 여백", "표 테두리",
      "표준 서식 기준 대표값 갱신")),
    ("body_spacing", "줄 끝에서 단어가 갈라지지 않도록 글자 간격을 조정하고 있어요.",
     ("본문 자간", "자간 조정", "개요·한 칸 표 자간", "단어 분리", "서식통일 교정 문장 자간")),
    ("control_spacing", "표와 글상자 안의 글자 간격도 같은 방식으로 다듬고 있어요.",
     ("표/컨트롤 자간", "표/컨트롤 단어")),
    ("short_line", "한두 글자만 남은 짧은 마지막 줄을 앞줄로 모으고 있어요.",
     ("짧은 마지막 줄", "표/컨트롤 줄 병합", "서식통일 교정 문장 줄 병합")),
    ("indent", "여러 줄 문장의 둘째 줄 시작 위치를 가지런히 맞추고 있어요.",
     ("최종 서식 기준 내어쓰기", "자간 조정 후 내어쓰기", "부연설명", "자간 조정 후 부연설명")),
    ("page_fit", "마지막 쪽에 조금 남은 내용을 앞쪽으로 당길 수 있는지 문단 간격을 살피고 있어요.",
     ("문단 아래 간격 페이지 맞춤",)),
    ("page_group", "함께 읽어야 할 문단이 쪽 사이로 갈라지지 않게 배치하고 있어요.",
     ("개별 문단 페이지 배치", "관련 문단 페이지 배치")),
    ("table_unify", "같은 종류의 표끼리 글꼴·크기가 다른 칸을 찾아 맞추고 있어요.",
     ("표 서식통일",)),
    ("unify_recheck", "앞선 작업 뒤에도 서식통일 결과가 그대로인지 다시 확인하고 있어요.",
     ("후속 작업 후 서식통일 재검증",)),
    ("save", "결과를 새 파일로 저장하고 원본과 내용이 같은지 검사하고 있어요.", ("저장",)),
    ("unify_verify", "저장한 결과를 다시 열어 서식이 제대로 맞았는지 확인하고 있어요.",
     ("서식통일 검수",)),
    ("done", "모든 작업이 끝났어요. 결과 확인에서 저장된 파일을 열어 보세요.", ("완료",)),
)

MODE_GUIDES = {
    "spacing": ("open", "body_spacing", "control_spacing", "short_line", "indent",
                "save", "done"),
    "unify": ("open", "unify_survey", "unify_apply", "table_unify", "page_fit", "save",
              "unify_verify", "done"),
    "format": ("open", "pre_format", "space", "unify_survey", "standard", "body_spacing",
               "indent", "page_fit", "page_group", "unify_recheck", "save", "done"),
    "all": ("open", "pre_format", "space", "unify_survey", "standard", "body_spacing",
            "control_spacing", "short_line", "indent", "page_fit", "page_group", "save",
            "done"),
}

_TEXT = {key: text for key, text, _ in GUIDE_ITEMS}
# 긴 이름이 먼저 맞도록 정렬한다(예: '자간 조정 후 내어쓰기'가 '자간 조정'보다 우선).
_PREFIXES = sorted(((prefix, key) for key, _, prefixes in GUIDE_ITEMS for prefix in prefixes),
                   key=lambda item: -len(item[0]))


def guide_key(stage_name):
    """단계 이름에 해당하는 안내 키를 돌려준다. 없으면 None."""
    name = str(stage_name or "").strip()
    for prefix, key in _PREFIXES:
        if name.startswith(prefix):
            return key
    return None


def guide_steps(mode):
    """작업 유형의 안내 문장 목록(실행 순서)."""
    return [_TEXT[key] for key in MODE_GUIDES.get(mode, MODE_GUIDES["all"])]


def guide_state(mode, key, visited=()):
    """진행 화면용 안내 상태: 문장 목록, 현재 위치, 지나간 위치."""
    keys = MODE_GUIDES.get(mode, MODE_GUIDES["all"])
    current = keys.index(key) if key in keys else None
    done = sorted({keys.index(k) for k in visited if k in keys and k != key})
    return {
        "steps": guide_steps(mode),
        "current": current,
        "done": done,
        "message": _TEXT.get(key, "작업을 시작하면 지금 하는 일을 여기에서 알려 드려요."),
    }
