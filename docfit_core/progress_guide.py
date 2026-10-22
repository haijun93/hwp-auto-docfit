"""진행 화면에 보여 줄 작업 유형별 단계 안내 문장.

로그보다 짧고 친절하게, 지금 무엇을 하는지 한 문장으로 알려 준다.
처리 코드가 넘기는 단계 이름을 앞부분 일치로 안내 항목에 연결한다.
"""

# (키, 안내 문장, 이 항목으로 연결할 단계 이름 앞부분)
GUIDE_ITEMS = (
    ("open", "문서를 열고 작업할 준비를 하고 있어요.", ("열기", "변환")),
    ("pre_format", "등록한 준말과 별표(*, **) 위첨자를 먼저 정리하고, 제목·개요·붙임처럼 먼저 정리할 부분의 서식을 맞추고 있어요.",
     ("준말 변환", "제목·개요 가로 크기", "별표 위첨자", "붙임 글꼴", "제목·개요·붙임 선행 서식", "기본 표 서식", "표 칸 너비",
      "표 정밀 서식")),
    ("space", "불필요한 공백과 문장부호 뒤 띄어쓰기를 정리하고 있어요.",
     ("공백 정규화", "문장부호 뒤 공백")),
    ("unify_survey", "문장들을 살펴 항목기호별로 가장 많이 쓴 대표 서식을 찾고 있어요.",
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


# ---- 기능별 맞춤 진행 화면(알파, 2026-10-15, docs/PROGRESS_FLOW_DESIGN.md) ----------------------------

# 안내 키 → 진행 화면의 짧은 단계 이름(2~8자). 설명은 GUIDE_ITEMS 문장을 지금 단계에서만 펼친다.
SHORT_NAMES = {
    "open": "문서 열기", "pre_format": "구조 정리", "space": "공백 정리", "unify_survey": "대표 서식 찾기",
    "unify_apply": "다른 문장 고치기", "standard": "표준 서식", "body_spacing": "본문 자간",
    "control_spacing": "표·글상자 자간", "short_line": "짧은 줄 모으기", "indent": "내어쓰기",
    "page_fit": "쪽 맞춤", "page_group": "쪽 배치", "table_unify": "표 서식 맞추기",
    "unify_recheck": "서식 재확인", "save": "저장·검사", "unify_verify": "다시 열어 검수", "done": "완료",
}

# 안내 키 → 그 단계를 이루는 세부 작업 키(stage_selection). 모두 꺼져 있으면 목록에서 뺀다.
# 비어 있으면(열기·저장 등) 항상 남긴다.
STEP_STAGES = {
    "pre_format": ("abbreviation", "text_table_convert", "asterisk_superscript", "attachment_font", "pre_format",
                   "table_style", "table_width", "precise_table"),
    "space": ("normalize_space", "punctuation_space"),
    "standard": ("standard_format", "parenthesis", "table_format", "single_cell_spacing", "star_align"),
    "body_spacing": ("reset_spacing", "body_spacing", "word_check"),
    "control_spacing": ("control_spacing", "control_word_check"),
    "short_line": ("short_line", "control_short_line"),
    "indent": ("hanging_indent", "supplement_indent"),
    "page_fit": ("page_fit", "page_layout_keep"),
    "page_group": ("page_group",),
    "table_unify": ("table_unify", "table_style"),
    "unify_recheck": ("style_unify",),
}
# 서식 통일 작업에서는 대표 서식 찾기·고치기·검수가 작업 그 자체라 거르지 않는다.
_ALWAYS = {"unify": {"unify_survey", "unify_apply", "unify_verify"}}

MODE_META = {
    "spacing": {"name": "자간 정리", "icon": "spacing", "running": "글자 간격을 다듬고 있어요",
                "finished": "글자 간격을 다듬었어요"},
    "unify": {"name": "서식 통일", "icon": "unify", "running": "문서 안 서식을 하나로 맞추고 있어요",
              "finished": "서식을 하나로 맞췄어요"},
    "format": {"name": "한 번에 적용", "icon": "all", "running": "표준 서식으로 문서를 정리하고 있어요",
               "finished": "문서 정리가 끝났어요"},
    "all": {"name": "한 번에 적용", "icon": "all", "running": "표준 서식으로 문서를 정리하고 있어요",
            "finished": "문서 정리가 끝났어요"},
    "file_format": {"name": "파일포맷 변경", "icon": "convert", "running": "파일 {count}개를 {target}로 바꾸고 있어요",
                    "finished": "파일 {count}개를 {target}로 바꿨어요"},
}

# 기다리는 동안 번갈아 보여 줄 짧은 안내(지루하지 않게, 지금 하는 일과 관련된 사실만).
TIPS = {
    "spacing": (
        "자간은 글자 사이 간격이에요. 줄 끝에서 단어가 갈라지지 않을 만큼만 아주 조금 줄여요.",
        "한두 글자만 남은 마지막 줄은 앞줄로 모아 읽기 좋게 만들어요.",
        "원본 파일은 그대로 두고 결과는 새 파일로 저장해요.",
        "카드의 '표 제외'를 켜면 표 안 글자는 건드리지 않아요.",
    ),
    "unify": (
        "문서에서 가장 많이 쓴 서식을 기준으로 삼아요. 기준과 같은 문장은 손대지 않아요.",
        "'(단위: 개소)' 표나 장식 막대 표처럼 직접 꾸민 표는 그대로 둬요.",
        "결과의 쪽 구성은 원본과 같게 맞춰요.",
        "저장한 뒤 다시 열어 서식이 제대로 맞았는지 한 번 더 확인해요.",
    ),
    "all": (
        "고른 서식 기준에 맞춰 글꼴·문단·표 모양을 차례로 입혀요.",
        "준말로 적은 제목·개요는 먼저 본말 서식으로 바꿔요.",
        "직접 꾸민 표는 서식 작업에서 빼고 그대로 둬요.",
        "마지막 쪽에 조금 남은 내용은 앞쪽으로 당길 수 있는지 살펴봐요.",
        "끝나면 결과를 다시 검수해 점수로 알려 드려요.",
    ),
    "file_format": (
        "원본 파일은 바꾸지 않고 같은 폴더에 새 파일을 만들어요.",
        "PDF와 그림은 한/글 내장 저장 기능으로 만들어요.",
        "다른 형식에서 다시 만든 문서는 모양이 원본과 조금 다를 수 있어요.",
    ),
}
TIPS["format"] = TIPS["all"]

_TARGET_LABELS = {"hwpx": "HWPX", "pdf": "PDF", "pdfz": "PDF 압축", "pdfm": "PDF 하나로 합치기", "docx": "DOCX", "epub": "EPUB", "png": "PNG", "jpg": "JPG",
                  "jpeg": "JPG"}


def _file_name(path):
    return str(path).replace("\\", "/").rsplit("/", 1)[-1]


def plan_keys(mode, selection=None):
    """작업 유형의 안내 키 목록에서 켜진 세부 작업이 하나도 없는 단계를 뺀 실행 순서."""
    from .stage_selection import enabled
    keys = MODE_GUIDES.get(mode, MODE_GUIDES["all"])
    if selection is None:
        return list(keys)
    keep = _ALWAYS.get(mode, set())
    return [key for key in keys
            if key in keep or not STEP_STAGES.get(key)
            or any(enabled(selection, stage, mode) for stage in STEP_STAGES[key])]


def progress_view(mode, key=None, visited=(), *, selection=None, running=False, files=(), doc=None,
                  results=(), failures=None, target=None, elapsed=None):
    """진행 화면 한 장에 필요한 값(기능별 제목·단계·문서 대기열·안내 문구)을 만든다(순수 함수).

    files: 작업 문서 경로 목록, doc: (지금 문서 순번 1부터, 전체 수) 또는 None,
    results: 저장된 결과 [{"source": 원본 파일 이름, "name": 결과 파일 이름}], failures: {원본 경로: 실패 이유}.
    """
    meta = MODE_META.get(mode, MODE_META["all"])
    files = [str(f) for f in files or ()]
    failures = {_file_name(path): reason for path, reason in dict(failures or {}).items()}
    results = list(results or ())
    total = len(files)
    index = (doc[0] if doc else 0) or 0
    finished = (not running) and bool(results or failures)

    queue = []
    for number, path in enumerate(files, 1):
        name = _file_name(path)
        result = next((item.get("name") for item in results if str(item.get("source")) == name), None)
        if name in failures:
            reason = str(failures[name] or "").strip().splitlines()
            state, note = "failed", (reason[0][:80] if reason else "처리하지 못했어요")
        elif result is not None:
            state, note = "done", result
        elif running and number == index:
            state, note = "active", ""
        else:
            state, note = "waiting", ""
        queue.append({"name": name, "state": state, "note": note})
    settled = sum(1 for item in queue if item["state"] in ("done", "failed"))

    steps, current = [], None
    if mode != "file_format":
        keys = [k for k in plan_keys(mode, selection) if k != "done"]
        seen = set(visited or ())
        position_of_key = keys.index(key) if key in keys else None
        for position, step in enumerate(keys):
            if finished:
                state = "done"
            elif step == key:
                state, current = "active", position
            elif step in seen or (position_of_key is not None and position < position_of_key):
                state = "done"
            else:
                state = "waiting"
            steps.append({"key": step, "name": SHORT_NAMES.get(step, step), "detail": _TEXT.get(step, ""),
                          "state": state})

    # 전체 진행 = (끝난 문서 + 지금 문서의 단계 진행) ÷ 문서 수. 문서가 하나면 단계 진행 그대로.
    if finished:
        ratio = 1.0
    elif mode == "file_format":
        ratio = settled / total if total else 0.0
    else:
        inner = (sum(1 for s in steps if s["state"] == "done") / len(steps)) if steps else 0.0
        before = max(settled, index - 1 if index else 0)
        ratio = (before + inner) / max(total, 1)
    ratio = max(0.0, min(1.0, ratio))

    label = _TARGET_LABELS.get(str(target or "").lower(), str(target or "").upper())
    if mode == "file_format":
        message = (f"{queue[index - 1]['name']} 파일을 바꾸고 있어요." if running and 0 < index <= total
                   else "파일을 하나씩 차례로 바꿔요.")
        now = f"{label} 변환" if running else ""
    else:
        message = _TEXT.get(key, "작업을 시작하면 지금 하는 일을 여기에서 알려 드려요.")
        active = next((s for s in steps if s["state"] == "active"), None)
        now = active["name"] if active else ""
    return {
        "mode": mode,
        "name": meta["name"],
        "icon": meta["icon"],
        "title": (meta["finished"] if finished else meta["running"]).format(count=total, target=label),
        "finished": finished,
        "running": bool(running),
        "message": message,
        "now": now,
        "steps": steps,
        "current": current,
        "doc": {"index": index, "total": total,
                "name": queue[index - 1]["name"] if 0 < index <= total else ""},
        "queue": queue,
        "ratio": round(ratio, 4),
        "tips": list(TIPS.get(mode, TIPS["all"])),
        "elapsed": int(elapsed) if elapsed is not None else None,
        "target": label,
    }
