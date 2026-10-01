"""User-selectable processing stages, in execution order."""

FORMAT_STAGES = (
    ("standard_format", "보고서 표준서식"),
    ("pre_format", "제목·개요·붙임 선행 서식"),
    ("precise_table", "일반 표 정밀 서식 복제"),
    ("normalize_space", "공백 정규화"),
    ("punctuation_space", "문장부호 뒤 공백 보정"),
    ("parenthesis", "문두 라벨·괄호 서식"),
    ("table_format", "표 머리글·본문 서식"),
    ("single_cell_spacing", "개요·한 칸 표 자간 조정"),
    ("hanging_indent", "최종 서식 기준 내어쓰기"),
    ("supplement_indent", "부연설명 들여쓰기"),
    # 실행 순서: 쪽 수 맞춤(문단 아래 간격)을 먼저 하고 문단 페이지 배치를 마지막에 한다.
    ("page_fit", "문단 아래 간격 페이지 맞춤"),
    ("page_group", "관련 문단 페이지 배치"),
)
# 서식통일: 고정된 기준 서식이 아니라 '이 문서 안에서 가장 많이 쓴 스타일'로
# 이질적인 스타일을 맞춘다. 기준이 달라지는 기능이라 기본값은 꺼져 있고(옵트인),
# 실행창의 '기본후처리'·'전문후처리' 프리셋이 켠다.
UNIFY_STAGE = ("style_unify", "서식통일 (문서 안 대표 스타일로 맞춤)")
# AI 채팅 답변을 붙여넣을 때 흔히 딸려오는 박스 그림 표(┌─┬─┐ …)를 실제
# 한/글 표로 바꾼다. 다른 모든 서식·자간 단계보다 먼저 실행해야 하므로
# FORMAT_STAGES 안에 넣지 않고 UNIFY_STAGE와 같은 방식으로 앞자리에 끼워 넣는다.
TEXT_TABLE_STAGE = ("text_table_convert", "텍스트 표(박스 그림)를 실제 표로 변환")
# 서식통일 작업에서 표를 본문과 따로, 같은 종류(같은 모양 칸·같은 기호 제목 상자)끼리 맞춘다.
TABLE_UNIFY_STAGE = ("table_unify", "표 서식통일 (같은 종류 표끼리 글꼴·크기 맞춤)")
# 준말(제목1: 등)을 서식 표·문구로 바꾼다. 서식 적용·한 번에 적용에서 실행하며, 등록한 준말이
# 없으면 아무 일도 하지 않는다. 문서 구조를 바꾸므로 다른 모든 단계보다 먼저(가장 처음에) 실행한다.
ABBREVIATION_STAGE = ("abbreviation", "준말 → 본말 변환")
# 문두기호 문장에서 단어 뒤에 붙은 * / **를 위첨자(Shift+Alt+P)로 만든다. 글자 모양만 바꾸며
# 서식 적용·한 번에 적용에서 실행한다.
ASTERISK_STAGE = ("asterisk_superscript", "별표(*, **) 위첨자 적용")
# '붙임 …'부터 '끝.'까지 묶음의 글꼴 종류·크기를 문두기호 ㅇ와 같게 한다(글자 모양만 바꿈).
ATTACH_FONT_STAGE = ("attachment_font", "붙임~끝. 묶음 글꼴·크기를 ㅇ와 동일하게")
# 준말 '표'의 본말(예시 표에서 배운 위치별 테두리·바탕색·글꼴)을 문서의 일반 표에 입힌다. 제목·개요·붙임
# 선행 서식 다음, 일반 표 정밀 복제 앞에서 실행하며 서식통일 작업에서도 실행한다.
TABLE_STYLE_STAGE = ("table_style", "기본 표 서식 (준말 '표'의 예시 표 서식 적용)")
DEFAULT_OFF = frozenset({"style_unify"})

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
    "style_unify": "예: 여러 사람이 쓴 문서를 합쳐 ㅇ 문단 대부분이 휴먼명조 15pt인데 몇 개만 굴림 13pt이면, 그 몇 개를 휴먼명조 15pt로 맞춥니다.",
    "pre_format": "예: 문서 제목, 개요, 중제목(Ⅰ·Ⅱ 번호 표), 붙임 표시를 먼저 찾아 각 영역의 서식을 정리합니다.",
    "precise_table": "예: 예시 서식의 표 셀 글꼴·테두리·너비를 대응하는 표에 복사합니다.",
    "normalize_space": "예: 문장 안에 불규칙하게 들어간 여러 공백을 정리합니다.",
    "punctuation_space": "예: 쉼표·마침표 뒤에 빠진 공백을 문맥에 맞게 보정합니다.",
    "standard_format": "예: 준말 변환 바로 다음, 다른 모든 단계보다 먼저 여백·글꼴·문두기호·문단 간격을 선택한 서식 기준에 맞춥니다.",
    "parenthesis": "예: 문두의 '(개요)' 같은 라벨 크기·굵기를 설정값에 맞춥니다.",
    "supplement_indent": "예: '* 참고'를 바로 위 항목의 글 시작 위치에 맞춥니다.",
    "table_format": "예: 표 첫 행은 머리글, 나머지 행은 본문 서식으로 맞춥니다.",
    "single_cell_spacing": "예: 한 칸짜리 개요 표에서 줄 끝에 걸린 단어를 자간으로 조정합니다.",
    "hanging_indent": "예: 'ㅇ 추진 계획'이 두 줄이면 둘째 줄을 '추진' 시작점에 맞춥니다.",
    "page_group": "예: ㅇ (운영방식)과 이어지는 - 항목들을 한 묶음으로 배치합니다. □ 제목은 첫 ㅇ 묶음과 연결합니다.",
    "page_fit": "예: 마지막 쪽에 2~3줄만 남았으면 문단 아래 간격을 줄여 앞쪽 쪽으로 당겨옵니다.",
    "reset_spacing": "예: 이전 편집에서 남은 자간 값을 0%로 되돌린 뒤 정리합니다.",
    "body_spacing": "예: 본문 줄 끝에서 단어가 갈라지면 글자 사이 간격을 조정합니다.",
    "short_line": "예: 마지막 줄에 짧게 남은 글자를 앞줄에 모으도록 시도합니다.",
    "control_spacing": "예: 표 셀·글상자 안에서 갈라진 단어를 자간으로 조정합니다.",
    "control_short_line": "예: 표 셀·글상자의 짧은 마지막 줄을 앞줄에 모으도록 시도합니다.",
    "word_check": "예: 1차 조정 뒤 본문에 남은 단어 분리를 다시 검사합니다.",
    "control_word_check": "예: 1차 조정 뒤 표 셀·글상자에 남은 단어 분리를 다시 검사합니다.",
    "abbreviation": "예: 줄 맨 앞(빈칸 제외) 어절이 준말인 '제목1: 지구 침공계획(안) 보고'·'로1 추진배경'·'붙임 자료명' 같은 줄을 가장 먼저 해당 서식 표로 바꾸고 준말 뒤 글을 표에 넣습니다(콜론은 있어도 없어도 됨).",
    "asterisk_superscript": "예: 'ㅇ (핵심 내용) 지자* 선행 투입 → 함대** 발진'에서 단어 뒤에 붙은 *와 **를 위첨자로 바꿉니다. 줄 맨 앞의 '* 설명'·'** 설명' 문두기호는 그대로 둡니다.",
    "attachment_font": "예: '붙임: 1. 지구 침공 세부 시행계획 1부.'부터 '끝.'까지 마침표로 끝나는 한 줄 문장들의 글꼴·크기를 ㅇ 문장과 같게 맞춥니다.",
    "text_table_convert": "예: '┌──┬──┐ / │ 구분 │ 내용 │ / └──┴──┘'처럼 박스 그림으로 그려 붙여넣은 표를 한/글의 실제 표로 바꿉니다.",
    "table_style": "예: 준말 '표'에 담긴 예시 표처럼 머리글 행은 바탕색·이중 밑줄·한컴돋움 13pt 굵게, 본문은 휴먼명조 12pt로 맞추고 칸 위치별 테두리를 입힙니다. 준말 창의 '표 서식 학습…'으로 예시 표를 바꿉니다.",
    "table_unify": "예: 같은 모양 표에서 한 칸만 굴림이면 한컴돋움으로, 󰊱 제목 상자 하나만 10pt면 다른 제목 상자처럼 15pt로 맞춥니다. 칸에 맞추려 줄인 글자와 표 안 글자색은 그대로 둡니다.",
}


_STAGE_BY_KEY = {stage[0]: stage for stage in FORMAT_STAGES + SPACING_STAGES + (
    UNIFY_STAGE, TEXT_TABLE_STAGE, TABLE_UNIFY_STAGE, ABBREVIATION_STAGE, ASTERISK_STAGE,
    ATTACH_FONT_STAGE, TABLE_STYLE_STAGE)}
# 서식 적용·한 번에 적용은 준말 → 본말 변환을 가장 먼저, 문두기호별 서식 등 보고서 표준서식을 두 번째로
# 다른 모든 단계보다 먼저 실행한다(서식 통일은 두 단계를 하지 않는다).
_FIRST_STAGES = ("abbreviation", "standard_format")
# 실제 실행 순서와 같게 보여 준다. 박스 그림 표 변환은 문단 구조를 바꾸므로 나머지 단계보다 먼저,
# 자간 초기화는 선행 서식·정밀 표 복제보다 먼저(복사한 자간 보존) 실행하고, 서식통일은 공백·문장부호
# 정리 뒤에 한다. 내어쓰기·부연설명을 먼저 맞추고 자간 변경 문단만 내어쓰기를 재조정한다.
_MODE_STAGES = {
    # 서식통일은 문서 자체의 대표 서식이 기준이다. 기본 표 서식(준말 '표')을 먼저 입힌 뒤 서식을 맞추고,
    # 쪽 맞춤은 사용자가 켤 때만 실행한다.
    "unify": ("table_style", "style_unify", "table_unify", "page_fit"),
    "format": _FIRST_STAGES + (
        "text_table_convert", "asterisk_superscript", "attachment_font", "pre_format", "table_style",
        "precise_table", "normalize_space", "punctuation_space", "style_unify", "parenthesis",
        "table_format", "single_cell_spacing", "hanging_indent", "supplement_indent", "page_fit", "page_group"),
    # 서식통일은 예외 문단별 서식→자간→내어쓰기 처리이며 전체 자간 단계는 돌리지 않는다.
    "spacing": ("reset_spacing", "style_unify", "body_spacing", "short_line", "control_spacing",
                "control_short_line", "word_check", "control_word_check"),
    # 개요·한 칸 표 자간 조정(single_cell_spacing)은 서식 전용이다.
    "all": _FIRST_STAGES + (
        "text_table_convert", "reset_spacing", "asterisk_superscript", "attachment_font", "pre_format",
        "table_style", "precise_table", "normalize_space", "punctuation_space", "style_unify", "parenthesis",
        "table_format", "hanging_indent", "supplement_indent", "body_spacing", "short_line", "control_spacing",
        "control_short_line", "word_check", "control_word_check", "page_fit", "page_group"),
}


def stages_for_mode(mode):
    if mode not in _MODE_STAGES:
        raise ValueError("지원하지 않는 작업 모드입니다.")
    return tuple(_STAGE_BY_KEY[key] for key in _MODE_STAGES[mode])


def default_choice(key, mode=None):
    """세부 작업의 기본 선택값(서식통일처럼 옵트인인 단계만 꺼짐).

    '서식 통일' 작업 유형에서는 서식통일이 곧 작업 자체라 켜져 있다.
    """
    if mode == "unify":
        return key in ("style_unify", "table_unify", "table_style")
    return key not in DEFAULT_OFF


def enabled(selection, key, mode=None):
    if selection is None:
        return default_choice(key, mode)
    return selection.get(key, default_choice(key, mode))
