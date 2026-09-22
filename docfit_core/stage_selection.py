"""User-selectable processing stages, in execution order."""

FORMAT_STAGES = (
    ("pre_format", "제목·개요·붙임 선행 서식"),
    ("precise_table", "일반 표 정밀 서식 복제"),
    ("normalize_space", "공백 정규화"),
    ("punctuation_space", "문장부호 뒤 공백 보정"),
    ("standard_format", "보고서 표준서식"),
    ("parenthesis", "문두 라벨·괄호 서식"),
    ("supplement_indent", "부연설명 들여쓰기"),
    ("table_format", "표 머리글·본문 서식"),
    ("single_cell_spacing", "개요·한 칸 표 자간 조정"),
    ("hanging_indent", "최종 서식 기준 내어쓰기"),
    ("page_group", "관련 문단 페이지 배치"),
)
SPACING_STAGES = (
    ("reset_spacing", "문서 전체 자간 초기화"),
    ("body_spacing", "본문 자간 조정"),
    ("short_line", "짧은 마지막 줄 병합"),
    ("control_spacing", "표·컨트롤 자간 조정"),
    ("control_short_line", "표·컨트롤 줄 병합"),
    ("word_check", "단어 분리 최종 검사"),
    ("control_word_check", "표·컨트롤 단어 검사"),
)

STAGE_EXAMPLES = {
    "pre_format": "예: 문서 제목, 개요, 붙임 표시를 먼저 찾아 각 영역의 서식을 정리합니다.",
    "precise_table": "예: 예시 서식의 표 셀 글꼴·테두리·너비를 대응하는 표에 복사합니다.",
    "normalize_space": "예: 문장 안에 불규칙하게 들어간 여러 공백을 정리합니다.",
    "punctuation_space": "예: 쉼표·마침표 뒤에 빠진 공백을 문맥에 맞게 보정합니다.",
    "standard_format": "예: 여백·글꼴·문두기호·문단 간격을 선택한 서식 기준에 맞춥니다.",
    "parenthesis": "예: 문두의 '(개요)' 같은 라벨 크기·굵기를 설정값에 맞춥니다.",
    "supplement_indent": "예: '* 참고'를 바로 위 항목의 글 시작 위치에 맞춥니다.",
    "table_format": "예: 표 첫 행은 머리글, 나머지 행은 본문 서식으로 맞춥니다.",
    "single_cell_spacing": "예: 한 칸짜리 개요 표에서 줄 끝에 걸린 단어를 자간으로 조정합니다.",
    "hanging_indent": "예: 'ㅇ 추진 계획'이 두 줄이면 둘째 줄을 '추진' 시작점에 맞춥니다.",
    "page_group": "예: 3단계 항목과 이어지는 4단계·부연설명이 쪽 사이에 갈라지지 않도록 조정합니다.",
    "reset_spacing": "예: 이전 편집에서 남은 자간 값을 0%로 되돌린 뒤 정리합니다.",
    "body_spacing": "예: 본문 줄 끝에서 단어가 갈라지면 글자 사이 간격을 조정합니다.",
    "short_line": "예: 마지막 줄에 짧게 남은 글자를 앞줄에 모으도록 시도합니다.",
    "control_spacing": "예: 표 셀·글상자 안에서 갈라진 단어를 자간으로 조정합니다.",
    "control_short_line": "예: 표 셀·글상자의 짧은 마지막 줄을 앞줄에 모으도록 시도합니다.",
    "word_check": "예: 1차 조정 뒤 본문에 남은 단어 분리를 다시 검사합니다.",
    "control_word_check": "예: 1차 조정 뒤 표 셀·글상자에 남은 단어 분리를 다시 검사합니다.",
}


def stages_for_mode(mode):
    if mode == "format":
        return FORMAT_STAGES
    if mode == "spacing":
        return SPACING_STAGES
    if mode == "all":
        return FORMAT_STAGES[:2] + SPACING_STAGES[:1] + FORMAT_STAGES[2:8] + SPACING_STAGES[1:] + FORMAT_STAGES[9:]
    raise ValueError("지원하지 않는 작업 모드입니다.")


def enabled(selection, key):
    return selection is None or selection.get(key, True)
