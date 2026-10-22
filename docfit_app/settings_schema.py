"""Shared settings defaults; storage keys and legacy adapter bindings are preserved."""
DEFAULTS = {
    'shell_menu': False,
    "prevent_word_split": True,
    # 장평 줄이기(가로 비율 축소)는 기본으로 끈다(2026-10-10 사용자 규칙). 끄면 자간 줄이기·늘리기만으로 조정한다.
    "ratio_shrink": False,
    "punctuation": True,
    "punctuation_threshold": "5",
    "keep_punctuation_set_together": True,
    "color_mark_on": False,
    "color": "blue",
    "autoclose": False,
    "stdformat": True,
    "verify": False,
    # 기록 탭의 보고서 파일 생성 옵션. 상세 진단 자체는 verify가 제어한다.
    "integrity_report_file": False,
    "final_review_file": False,
    # 작업로그·무결성검사 JSON·최종검수 JSON은 사용자가 켜기 전까지 꺼 둔다(판 2부터).
    "report_files_rev": 2,
    "two_pass_processing": False,
    "retry_body": "15",
    "retry_table": "5",
    "linespacing_min": "140",
    "linespacing_max": "200",
    # 문두 라벨 굵게에서 뺄 기호(False). 별표(*, **)는 2026-10-03부터 기본으로 뺀다.
    "label_symbols": {"□": False, "※": False, "*": False, "**": False},
    # 설정 파일 판: 2 = 별표(*, **) 라벨 굵게 기본값 끔을 반영한 설정(예전 파일은 불러올 때 한 번 끈다)
    "label_symbols_rev": 2,
    "paren_shrink": True,
    "paren_label_bold": True,
    "std_margin": True,
    "std_ratio": True,
    "std_linespacing": True,
    "std_title": True,
    "std_title_auto": True,
    "std_attachment_auto": True,
    "std_midtitle_auto": True,
    "std_midtitle_bold": True,
    "abbreviations": {},
    "abbreviation_defaults": True,
    # 준말 출처: "document"=준말 관리 HWPX 문서(C:\HWP_AUTODOCFIT\준말관리), "settings"=앱 설정(1.80.2까지)
    "abbreviation_source": "document",
    "std_title_bold": True,
    "std_dateinfo": True,
    "std_dateinfo_bold": True,
    "std_symbols": True,
    "std_hanging_indent": True,
    "std_supplement_indent": True,
    "std_symbol_box_bold": False,
    "std_symbol_o_bold": True,
    "std_symbol_dash_bold": False,
    "std_symbol_note_bold": False,
    # 같은 항목기호의 라벨이 굵게 되면 다른 문단의 머리말도 굵게 맞춤
    "std_marker_bold_consistency": True,
    "std_parspace": True,
    # 항목기호 문장 사이에 빈 줄로 띄운 간격 삭제(문단 위 여백으로 대신함)
    "std_remove_blank_lines": True,
    "std_parspace_chapter": "15",
    "std_parspace_midtitle": "15",
    "std_parspace_box": "15",
    "std_parspace_circle": "8",
    "std_parspace_dash": "4",
    "std_parspace_note": "0",
    # 설정 파일 판: 2 = 문단 위 여백 기본값 15/15/15/8/4/0pt(예전 기본값 20/15/15/10/3을 그대로 쓰던 파일은 새 값으로)
    "std_parspace_rev": 2,
    "std_supplement_rev": 2,
    "std_parspace_return_percent": "150",
    # 제목 서식 부제(제목 글의 첫 쉼표 앞 글) 글자 크기 pt
    "std_title_subtitle_pt": "15",
    # 새로 만드는 제목 서식 표의 담당자 칸(2×2 표 B2, 2행1열 표 A2) 글. 비우면 기준 표의 글을 그대로 둔다.
    "title_owner_text": "",
    "std_table_header": True,
    "active_format_profile": "",
    "review_document_kind": "보고서",
    "review_reading_purpose": "상세 설명용",
    "symbol_fonts": {
        "□": {"font": "HY견고딕", "size": "17"},
        "ㅇ": {"font": "한컴돋움", "size": "15"},
        "-": {"font": "휴먼명조", "size": "14"},
        "※": {"font": "한컴돋움", "size": "13"},
        # *(대표 기호, **는 *로 합침)의 기본값은 ※와 동일하다.
        "*": {"font": "한컴돋움", "size": "13"},
        "•": {"font": "한컴돋움", "size": "13"},
    },
    # 표 머리글(첫 행)·본문(나머지 행) 글꼴·크기. 문장기호별 글꼴처럼 서식
    # 프로파일보다 우선하는 개인 설정이다.
    "table_fonts": {
        "header": {"font": "한컴돋움", "size": "13"},
        "body": {"font": "휴먼명조", "size": "12"},
    },
    "hwp_font_folder": "",
    "paste_add_folder": "",
    "always_on_top": True,
    "check_updates_on_start": True,
    # 폐쇄망(인터넷이 안 되는 PC) 모드. 켜면 업데이트 확인·kordoc 모델 내려받기 등 외부 접속을 하지 않는다.
    "offline_mode": True,
    "table_spacing": True,
    "log_file": False,
    # 개발자 모드: 켜야 문서 도구(문서 구조 검토·맞춤법·작성 도우미·Markdown·고급 문서 도구 등) 메뉴가 보인다.
    "developer_mode": False,
    # tldraw 기능은 개발자 모드와 함께 사용자가 별도 활성화해야 한다.
    "diagram_editor_enabled": False,
    # '한 번에 적용' 카드의 '자간 조정 포함'. 끄면 기존 자간을 두고 서식만 입히는 서식 적용(format)으로 실행한다.
    "all_include_spacing": True,
    # 한 번에 적용의 '표 제외': 켜면 표 관련 세부 작업을 모두 빼고 표 칸 안 문장도 자간 작업에서 뺀다.
    "all_exclude_tables": False,
    # 한 번에 적용의 '페이지 맞춤 제외': 켜면 문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 뺀다.
    "all_exclude_pagefit": False,
    "all_linespacing": True,
    # 서식 통일 카드의 '표 제외'·'자간 정리 제외'·'페이지 맞춤 제외'. 세부 작업과 연동되며, 서식 통일의 쪽 맞춤은
    # 세부 작업 기본값이 꺼짐이라 '페이지 맞춤 제외'만 기본 켜짐이다.
    "unify_exclude_tables": False,
    "unify_exclude_spacing": False,
    "unify_exclude_pagefit": True,
    # 서식 통일 카드의 '원본 쪽 구성 유지'(세부 작업 page_layout_keep과 연동, 기본 켬).
    "unify_keep_layout": True,
    # 서식 통일 카드의 '전체 서식 맞추기'(세부 작업 unify_full_format과 연동, 기본 끔 = 글꼴·크기만 맞춤).
    "unify_full_format": False,
    # 서식통일 뒤 '작업 결과 확인' 창(서식통일 5/5)을 띄울지. 기본 꺼짐(2026-10-04 사용자 요청).
    "unify_result_window": False,
    # '자간 정리' 카드의 '기존 자간 초기화'(세부 작업 01과 같은 값). None이면 저장된 세부 작업 구성을 따른다.
    "spacing_reset_existing": None,
    "spacing_enabled": True,
    "spacing_page_fit": False,
}

VARIABLE_BINDINGS = {'prevent_word_split': 'prevent_word_split_var',
 'spacing_enabled': 'spacing_enabled_var',
 'spacing_page_fit': 'spacing_page_fit_var',
 'ratio_shrink': 'ratio_shrink_var',
 'punctuation': 'punctuation_var',
 'punctuation_threshold': 'punctuation_threshold_var',
 'keep_punctuation_set_together': 'keep_punctuation_set_var',
 'color_mark_on': 'color_mark_on_var',
 'color': 'color_var',
 'autoclose': 'autoclose_var',
 'unify_result_window': 'unify_result_window_var',
 'stdformat': 'stdformat_var',
 'verify': 'verify_var',
 'integrity_report_file': 'integrity_report_file_var',
 'final_review_file': 'final_review_file_var',
 'two_pass_processing': 'two_pass_var',
 'table_spacing': 'table_spacing_var',
 'log_file': 'log_file_var',
 'check_updates_on_start': 'check_updates_on_start_var',
 'developer_mode': 'developer_mode_var',
 'retry_body': 'retry_body_var',
 'retry_table': 'retry_table_var',
 'linespacing_min': 'linespacing_min_var',
 'linespacing_max': 'linespacing_max_var',
 'hwp_font_folder': 'font_folder_var',
 'paste_add_folder': 'paste_add_folder_var',
 'paren_shrink': 'paren_shrink_var',
 'paren_label_bold': 'paren_label_bold_var',
 'always_on_top': 'always_on_top_var',
 'all_include_spacing': 'include_spacing_var',
 'all_exclude_tables': 'exclude_tables_var',
 'title_owner_text': 'title_owner_var',
 'all_exclude_pagefit': 'all_exclude_pagefit_var',
 'all_linespacing': 'all_linespacing_var',
 'unify_exclude_tables': 'unify_exclude_tables_var',
 'unify_exclude_spacing': 'unify_exclude_spacing_var',
 'unify_exclude_pagefit': 'unify_exclude_pagefit_var',
 'unify_keep_layout': 'unify_keep_layout_var',
 'unify_full_format': 'unify_full_format_var'}
