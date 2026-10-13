# Flutter 전환 기능 조사 — 1.74 Alpha 3

기준: 공개 베타 `016b6be`(1.74 Beta 1), 개발 시작 `4e1c391`(1.74 Alpha 2). 2026-10-13 사용자 지시를 적용한다. Flutter UI 제거와 잘못된 MCP 시험 구현으로 회수한 1.75.1/1.75.2 및 백업 브랜치는 가져오지 않는다. 현재 앱의 MCP 진입점은 없으며 이번 변경에도 추가하지 않는다.

분류: F=Flutter 화면 구현, P=부분 구현, T=Tk 전용, B=Flutter 명령이 Tk 화면/상태에 의존, E=독립 Python 엔진/서비스. F 표기도 실제 Windows/COM 검증 완료를 뜻하지 않는다. 난이도는 기존 데이터·취소·조판 영향에 따른 상대 평가다.

| 기능 | 분류 / 기존 경로·관련 파일 | 설정·데이터 | 시험 | 우선순위 / 난이도 |
|---|---|---|---|---|
| 문서 목록 추가·제거·폴더 | P/B, `main.dart` → `add_files/add_folder/add_paths` → `파일선택/_폴더선택/파일추가` | `gui.files`, 실제 경로, 허용 확장자 | `test_desktop_file_drop.py`, `workspace_test.dart` | P2 파일 서비스 / 중 |
| 드래그 앤 드롭 | F/B, `_bind_file_drop/receive_drop`, pywebview native full path | `drop_target`, 문서/서식 목적지 | `test_desktop_file_drop.py`, Windows `smoke_file_drop.py` | P2 서비스 / 중 |
| 텍스트 입력·붙여넣기 | B/T, `text_input/run_tool(paste,polish)` → `_텍스트로_문서추가_열기/_붙여넣기_정리_열기` | `paste_add_folder`, `pasted_text/labeled_text/ai_answer` | `test_pasted_text.py`, `test_ai_answer.py`, GUI startup | P1 / 중 |
| 작업 유형·세부 작업 | F/B, `set_mode/set_stage/reset_stages/set_stage_default/open_stages` | `stage_choices`, 내부 spacing/unify/format/all | `test_desktop_browser_api.py`, `test_stage_selection.py`, `workspace_test.dart` | P1 수치 편집, P2 상태 / 중 |
| 자간 초기화·표 제외·쪽 맞춤 등 카드 옵션 | F/B, `set_include_spacing/set_reset_spacing/set_table_spacing/set_exclude_tables/set_card_option` | `all_include_spacing`, `spacing_reset_existing`, `table_spacing`, `*_exclude_*`, `unify_full_format` | Browser API, stage selection, 카드 위젯 시험 | P2 제약 통합 / 중 |
| 쪽 범위·새 작업 | F/B, `set_range/start/next_job`, `_작업범위_초기화` | 화면 draft와 Tk 범위 값, 시작/끝·전체 | `workspace_test.dart` 신규 범위 회귀 시험 | P0 안정화 구현 / 중 |
| 프로필 목록·선택·이름·기관·삭제 | F/B, `set_profile/rename_profile/delete_profile`, `_서식_이름_저장/_서식_삭제` | `active_format_profile`, `formats/*.json`, 예시·썸네일 | `test_format_manager.py`, Browser API, 위젯 시험 | P2 프로필 서비스 / 중 |
| 프로필 등록·예시 분석 | P/B, `add_format_file/add_format_paths/write_format_example` | 예시 HWP/HWPX/PDF, `element_analysis`, `format_task` | `test_format_example.py`, `test_format_elements.py`, `test_format_samples.py` | P1 / 높음 |
| 서식 요소·복사 범위 편집 | B/T/E, `edit_profile` → `_서식_수정하기/_서식_세부사항_확인/_서식_구조_확인`, `format_elements/style_profile_edit` | 글자·문단·표 칸, `hanging_rule`, 복사 토글 | `test_format_detail_dialog.py`, `test_style_profile_edit.py`, `test_format_elements.py` | P1 / 높음 |
| 예시 확인·썸네일 | F/B, `format_gallery/show_format_example/open_format_samples` | HWPX 사본, JPEG data URI, 예시 해시 | Browser API, `test_format_samples.py`, Windows HWP | P2 / 중 |
| 준말 조회·검색·CRUD·기본값 | **F/E 신규**, `features/abbreviations` → API v1 → `docfit_app/abbreviation_service.py`; Tk `_준말_서비스` 동일 인스턴스 | 기존 `abbreviations`, `abbreviation_defaults`; 학습된 style 보존 | `test_abbreviation_service.py`, `abbreviation_manager_test.dart`, 기존 `test_abbreviations.py` | **P1 구현**, Tk 화면 실기기 확인 대기 / 낮음 |
| 준말의 표 서식 학습·내장값 복원 | T/E, `abbreviation_dialog.learn_table/reset_table`, `table_style` | `표`의 `style`, 예시 HWPX | `test_abbreviation_dialog.py`, `test_table_style.py` | P1 후속 / 중 |
| 문서 계층·구조·불일치 검토 | B/T/E, `run_tool(review)` → `_문서검토_열기`, `document_review/style_hierarchy` | 문서 종류·읽기 목적, 검토 payload | `test_document_review.py`, `test_style_hierarchy.py`, GUI startup | P1 읽기 전용 화면부터 / 중 |
| 공공언어·맞춤법·수치 검토 | B/T/E, `_공공언어_검토`, `korean_proofread/number_check` | 사용자 선택 제안, 문서 변경/검토 승인 | `test_korean_proofread_dialog.py`, `test_number_check.py` | P1 / 높음 |
| 아웃라이너·작성 도우미·AI 프롬프트 | B/T/E, `run_tool(outline,writing)`, `_AI_프롬프트_열기`, `outline_ops/writing_aids` | 초안 파일·상용구·문구, COM 없이 가능한 순수 함수 | `test_outline_ops.py`, `test_outliner_gui.py`, `test_writing_aids_gui.py` | P1 독립 도구부터 / 중 |
| Markdown·kordoc 고급 도구 | B/T/E, `run_tool(markdown,advanced)`, `kordoc_bridge` | 개발자 모드, 외부 Node 도구, 출력 사본 | `test_kordoc_bridge.py`, `test_kordoc_contract.py` | P1 / 높음, 선택 의존성 |
| 빠른 환경설정 | F/B, `QUICK_OPTIONS/set_option` | autoclose, verify, 기록 파일 3종, 업데이트, developer_mode, always_on_top, unify_result_window | Browser API·위젯·report defaults 시험 | P2 설정 서비스 / 중 |
| 전체 환경설정·복원·충돌 안내 | B/T, `open_settings` → `설정창_열기`, `_설정_초기화_클릭/_설정_변경됨` | 아래 79개 기본 키 + 동적 stage_choices/프로필 | `test_reset_app.py`, `test_report_files_default_off.py`, GUI 시험 | P1 / 높음; 모든 설정 이전은 미완료 |
| 진행·중단·재시도 | P/B/E, `get_state/start/stop`, worker와 `gui_queue/중단_event` | active/visited/outcome, retry_body/table, two_pass_processing | `test_stage_timing.py`, `test_progress_guide.py`, 위젯·Windows corpus | P0 요청 안정화 구현, P2 작업 서비스 / 높음 |
| 대표 서식 승인·적용 범위 승인 | T/E, `_서식통일_대표값_검토_요청/대표서식_검토창/적용영역_검토창` | worker Event 승인/취소, selected payload | style review dialog, unify regression | P1 / 높음; 작업 중 modal 동작 보존 필요 |
| 결과 목록·파일 열기·폴더 열기 | F/B, `open_result/show_result/open_results` | `_결과목록`, 원본명·쪽수·결과경로 | Browser API·workspace 결과 시험 | P2 결과 서비스 / 낮음 |
| 원본/결과 비교·최종 검수·시간절약 창 | T/E, `비교창_준비`, `_서식통일_결과_확인창/_절약_완료창`, `final_evaluation/fidelity` | 결과 검수, 비교 HWP 세션, 원본 불변 | `test_final_evaluation.py`, `test_fidelity.py`, saved_time_dialog, Windows integrity | P1 / 높음 |
| 작업 로그·복사·지우기 | F/B, `showLog/get_log/clear_log` | Tk log_text, 일반 폴링에는 로그 본문 제외 | Browser API·workspace 로그 시험 | P2 이벤트·일반 문자열 버퍼 / 중 |
| 오류·업데이트·종료 확인 | B/T/E, Flutter snackbar + `request_close/종료`, updater 알림 | 업데이트 호스트·해시·check_updates_on_start | `test_updater.py`, `test_updater_env.py`, 신규 request lifecycle | P0 종료 안정화 구현, P1 화면 / 높음 |
| HWP 문서 처리·COM | E(분리 대상), `작업_실행/문서_처리/_문서_처리_본체`, docfit_core | 문서 사본·파이프라인 플래그·COM thread | Python corpus·integrity, Windows smoke/regression | P2 UI 상태 분리, 알고리즘 재작성 제외 / 높음 |

## 보존·확인 기준

- Flutter 자산은 `desktop_web/flutter`에 빌드하고 WebView2에서 사용한다. Python/Tk 비상 경로를 삭제하지 않는다.
- 순수 서비스에는 Tk 위젯/변수가 없다. 기존 서비스 호출은 Tk 루프에서 직렬화하는 어댑터를 통해 기존 설정 저장과 충돌하지 않게 한다.
- 새 준말 API는 저장 실패/작업 중/잘못된 입력을 구조화해 보낸다. 기존 API 전체의 버전/오류 전환은 미완료다.
- 새 서비스는 다른 설정 키와 학습된 표 서식을 보존하며, 깨진 설정 파일은 덮어쓰지 않는다. 기존 전체 설정 저장기의 마이그레이션은 그대로 유지한다.
- 기능 동등성과 COM 처리 결과의 최종 합격은 Windows+한/글 2020 사용자 흐름 검증으로 판단한다.

설정 키 전수 목록과 Tk 보조 진입점은 아래 부록에 기록한다. 세부 작업의 실제 단계 키는 `docfit_core/stage_selection.py`가 원천이며 임의로 재정의하지 않는다.

## 기본 설정 키 79개 (AST 조사)

- `prevent_word_split`, `ratio_shrink`, `punctuation`, `punctuation_threshold`, `keep_punctuation_set_together`, `color_mark_on`, `color`, `autoclose`
- `stdformat`, `verify`, `integrity_report_file`, `final_review_file`, `report_files_rev`, `two_pass_processing`, `retry_body`, `retry_table`
- `linespacing_min`, `linespacing_max`, `label_symbols`, `label_symbols_rev`, `paren_shrink`, `paren_label_bold`, `std_margin`, `std_ratio`
- `std_linespacing`, `std_title`, `std_title_auto`, `std_attachment_auto`, `std_midtitle_auto`, `std_midtitle_bold`, `abbreviations`, `abbreviation_defaults`
- `std_title_bold`, `std_dateinfo`, `std_dateinfo_bold`, `std_symbols`, `std_hanging_indent`, `std_supplement_indent`, `std_symbol_box_bold`, `std_symbol_o_bold`
- `std_symbol_dash_bold`, `std_symbol_note_bold`, `std_marker_bold_consistency`, `std_parspace`, `std_remove_blank_lines`, `std_parspace_chapter`, `std_parspace_midtitle`, `std_parspace_box`
- `std_parspace_circle`, `std_parspace_dash`, `std_parspace_note`, `std_parspace_rev`, `std_supplement_rev`, `std_parspace_return_percent`, `std_title_subtitle_pt`, `title_owner_text`
- `std_table_header`, `active_format_profile`, `review_document_kind`, `review_reading_purpose`, `symbol_fonts`, `table_fonts`, `hwp_font_folder`, `paste_add_folder`
- `always_on_top`, `check_updates_on_start`, `table_spacing`, `log_file`, `developer_mode`, `all_include_spacing`, `all_exclude_tables`, `all_exclude_pagefit`
- `unify_exclude_tables`, `unify_exclude_spacing`, `unify_exclude_pagefit`, `unify_keep_layout`, `unify_full_format`, `unify_result_window`, `spacing_reset_existing`

추가 저장 영역: `stage_choices`, `formats/*.json`, `format_examples`, `outliner_draft.md`, `test_corpus.json`, 업데이트 상태/설치 보조 파일.

## Tk 보조 진입점 (이름 기준 조사)

- `_창_최소높이_보정` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_세부작업_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_경로_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_문서_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_원본폴더_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_결과파일_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_서식창_부모` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_서식_키오스크_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_서식예시_폴더_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_문서검토_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_아웃라이너_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_텍스트로_문서추가_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_붙여넣기_정리_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_AI_프롬프트_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_작성도우미_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_공공언어_검토` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_설정창_생성` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `설정창_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_앱폴더_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `고급문서도구_열기` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `비교창_준비` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_비교창_닫기시도` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_서식통일_대표값_검토_요청` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_절약_완료창` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_검토창_앞으로` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_서식통일_대표서식_검토창` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_서식통일_적용영역_검토창` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_서식통일_결과_확인창` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
- `_비교창_분리_후_보존` (`hwp-auto-docfit.py`): 위 기능 표에 따라 화면/승인/보조 도구를 점진적으로 이전.
