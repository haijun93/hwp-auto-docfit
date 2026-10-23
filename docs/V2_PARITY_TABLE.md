# V2 기능 동등성 표 (Tkinter vs Flutter UI Parity Table)

- **문서 버전**: 2.0.0-phase1 (코드 전수 실측 대조 완료판)
- **기준 코드**: `docfit_ui/legacy.py` (7,071줄, v1.80.7 기준), `desktop_web_ui.py` (2,003줄), `flutter_ui/lib/**`
- **대조 일자**: 2026-10-23
- **목적**: 2.0.0 마일스톤의 핵심 목표인 "Tkinter 코드 100% 제거 및 Flutter 단일 UI 전환"을 위해, `legacy.py`에 존재하는 모든 Tk 창·모달·대화상자(Toplevel 22곳, simpledialog 6곳, filedialog 15곳, messagebox 48종) 및 `desktop_web_ui.py` 브리지 경로의 실제 행 번호와 Flutter 실구현 상태를 1:1 전수 대조하고 3단계 이관 전략을 확정한다.

---

## 1. 개요 및 판정 기준

1. **조사 대상**:
   - `docfit_ui/legacy.py` 내 모든 `tk.Toplevel`, `simpledialog`, `filedialog`, `messagebox`, `self._알림` 호출 지점.
   - `desktop_web_ui.py` 내 Flutter UI에서 백그라운드 Tk 창을 여는 브리지 API (`front=True` 또는 `self._tk` 호출 경로).
2. **Flutter 대응 상태 판정 기준**:
   - **완료**: `flutter_ui/lib` 안에 실제로 구현된 위젯/화면이 존재하며 정상 작동함. (단, 레거시 브리지 API에 Tk 호출 분기가 남아있는 경우 비고에 명시)
   - **완료(브리지 대화상자)**: `self._알림(...)`을 거쳐 웹 모드 브리지(`enqueue_dialog`)로 전달되어 Flutter의 `BackendDialog`(`get_pending_dialog` / `resolve_dialog`)로 온전히 표출됨.
   - **일부**: Flutter에 대응 화면(예: `DocumentToolsWorkspace`) 또는 위젯이 존재하나, 특정 탭 미구현이거나 `desktop_web_ui.py`의 `run_tool` 호출 시 Tk 창이 뜨는 경로가 병존함.
   - **없음**: Flutter에 대응 화면·위젯이 전혀 없으며 오직 Tk 창 또는 외부 프로세스에 의존하는 상태.
3. **우선순위 기준**:
   - **상**: 일상 작업 파이프라인의 필수 설정 및 핵심 가치 (세부작업, 환경설정, 서식통일 마법사, 공공언어, 원본비교 등).
   - **중**: 문서 품질 검토, 아웃라이너, 작성 도우미 등 부가 생산성 도구.
   - **하**: 단발성 텍스트 변환, AI 프롬프트 생성, 예시 편집 안내문 등.

---

## 2. 주요 Tk 창 및 대화상자 (Toplevel 22건 & simpledialog 6건 전수)

| 번호 | Tk 화면/대화상자 이름 | 여는 함수 (legacy.py 행) | 언제 뜨나 (사용자 동작) | 주요 입력·출력 요소 | Flutter 대응 화면 (flutter_ui/lib 실제 위젯) | 현재 상태 | 필요한 브리지 API (desktop_web_ui.py) | 우선순위 | 비고 (판정 근거 및 Tk 호출 경로) |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **T01** | 처리 기록 창 | L760 `__init__`<br>(L2062 `_기록토글`, L2071 `_기록닫기`) | 상단 메뉴 "로그 보기" 또는 진행 표시줄 클릭 시 | - 입: 로그 지우기/닫기<br>- 출: 실시간 ScrolledText 로그 스트림 | `features/progress/live_progress.dart`<br>(`LiveProgress`), `main.dart` (`showLog`) | **완료** | `get_state`, `get_log` | 중 | Flutter 하단 진행 카드 및 `showLog` 다이얼로그에 임베디드 완료됨. 단, 브리지 `open_log` 호출 시 `log_window.deiconify()` 잔존. |
| **T02** | 세부 작업 항목 설정 창 | L1386 `_세부작업_열기` | 2단계 세부작업 "단계별 수치 조정" 클릭 시 | - 입: 9대 작업 그룹 On/Off 체크박스, 세부 목표치 Spinbox<br>- 출: 설정 저장/적용 | `features/stages/stage_board.dart`<br>(`StageBoard`), `main.dart` (`showStages`) | **완료** | `set_stage`, `stage_config`, `set_stage_default`, `reset_stages` | **상** | 메인 화면의 `StageBoard` 및 `showStages` 모달 시트로 완전 구현됨. 브리지 `open_stages` API 호출 시 Tk 창(`_세부작업_열기`)을 띄우는 경로 제거 대상. |
| **T03** | 서식 키오스크 (스틸컷 선택) | L2489 `_서식_키오스크_열기` | 서식 선택 영역 "썸네일로 선택" 클릭 시 | - 입: 썸네일 카드 클릭 선택<br>- 출: 서식 카드 그리드, 미리보기 이미지, 프로필 ID | `main.dart`<br>(`openKiosk`, `kioskCard`) | **완료** | `format_gallery`, `set_profile` | 하 | `main.dart`의 `openKiosk()`와 `kioskCard` 그리드 다이얼로그로 이미 완전 구현되어 정상 작동 중 (초안의 '없음' 오류 수정). |
| **T04** | 서식 예시 문서 편집 창 | L2761 `_서식_예시편집_시작` | 서식 관리자에서 "예시 문서 열어 편집/분석" 클릭 시 | - 입: HWP 외부 실행, 저장 후 분석 요청<br>- 출: 분석 안내문, 완료 여부 | 없음 | **없음** | `write_format_example`, `analyze_hwp_format` | 하 | 브리지 `write_format_example` 호출 시 Tk 창 뜸. 외부 HWP 실행 안내 및 백그라운드 분석 Flutter 전용 모달로 이관 대상. |
| **T05** | 문서 검토 (가독성/구조) 창 | L2879 `_문서검토_열기` | 도구 메뉴 "문서 구조 및 가독성 검토" 클릭 시 | - 입: 검토 대상 파일 선택, JSON 내보내기<br>- 출: 장/절/문단 구조 트리, 가독성 지수 통계 | `features/tools/document_tools_workspace.dart`<br>(`DocumentToolsWorkspace`) | **일부** | `document_tool` (POST /api/document-tool) | 중 | `openTools('review')` 매핑 완료. 단, 개발자 메뉴의 브리지 `run_tool('review')` 호출 시 Tk 창이 열림. |
| **T06** | 아웃라이너 창 | L3031 `_아웃라이너_열기` | 도구 메뉴 "아웃라이너로 새 글 작성" 클릭 시 | - 입: 계층 노드 추가/수정/삭제, 들여쓰기<br>- 출: HWP/MD/TXT 내보내기 | `features/tools/document_tools_workspace.dart`<br>(`DocumentToolsWorkspace`) | **일부** | `document_tool` | 중 | `openTools('outline')` 연동 완료. 단, 브리지 `run_tool('outline')` 호출 시 Tk 창이 열림. |
| **T07** | 텍스트로 문서 추가 창 | L3494 `_텍스트로_문서추가_열기` | "텍스트 직접 입력/붙여넣기로 문서 추가" 클릭 시 | - 입: 텍스트 본문, 제목, AI변환 체크<br>- 출: TXT/HWP 임시 파일 생성 및 큐 등록 | `features/tools/document_tools_workspace.dart`<br>(`DocumentToolsWorkspace`) | **일부** | `document_tool`, `text_input` | 중 | `openTools('paste')` 매핑 완료. 단, 브리지 `text_input` 및 `run_tool('paste')` 호출 시 Tk 창이 열림. |
| **T08** | 붙여넣기 정리 창 | L3675 `_붙여넣기_정리_열기` | 도구 메뉴 "클립보드 텍스트 서식 정리" 클릭 시 | - 입: 마크다운 기호 제거, 개조식 변환 옵션<br>- 출: 정리된 텍스트 프리뷰, 클립보드 복사 | `features/tools/document_tools_workspace.dart`<br>(`DocumentToolsWorkspace`) | **일부** | `document_tool` | 하 | `openTools('polish')` 매핑 완료. 단, 브리지 `run_tool('polish')` 호출 시 Tk 창이 열림. |
| **T09** | AI 프롬프트 생성기 창 | L3794 `_AI_프롬프트_열기` | 도구 메뉴 "AI 프롬프트 도우미" 클릭 시 | - 입: 프롬프트 유형(교정/요약/초안), 본문 발췌<br>- 출: 조립된 공문서 시스템 프롬프트 복사 | `features/tools/document_tools_workspace.dart`<br>(`DocumentToolsWorkspace`) | **일부** | `document_tool` | 하 | 프롬프트 조립 도구. `DocumentToolsWorkspace` 내 탭으로 완전 흡수 대상. |
| **T10** | 공문서 작성 도우미 창 | L3870 `_작성도우미_열기` | 도구 메뉴 "공문서 작성 도우미" 클릭 시 | - 입: 7대 도우미(금액, 날짜, 표 계산, 나이 등)<br>- 출: 변환된 공문서 문구 복사 | `features/tools/document_tools_workspace.dart`<br>(`DocumentToolsWorkspace`) | **일부** | `document_tool` | 중 | `openTools('writing')` 매핑 완료. 단, 브리지 `run_tool('writing')` 호출 시 Tk 창이 열림. |
| **T11** | 공공언어/맞춤법 검토 창 | L4162 `_공공언어_검토` | 도구 메뉴 "공공언어 바로쓰기 검토" 클릭 시 | - 입: 순화어/오류 단어 치환 선택, 제외어 등록<br>- 출: 검출 오류 목록 테이블, 추천 대체어 | `features/tools/document_tools_workspace.dart`<br>(`DocumentToolsWorkspace`) | **백엔드 완료, 화면 대기** | `public_language`, `proofreading_exclusions`, `start_job`, `get_events` | **상** | C16: jobs 기반 검토·취소·선택 적용, 문단 위치와 Tk 동일 결과. `ui_tk_fallback=true`에서만 `run_tool('proofread')`가 Tk 창을 연다. [API](V2_PUBLIC_LANGUAGE_API.md). |
| **T12** | 교정 제외어 관리 창 | L4254 `_교정_제외관리` | 공공언어 검토 창 내 "제외 단어 관리" 클릭 시 | - 입: 제외 단어 추가/삭제<br>- 출: 등록된 사용자 제외어 목록 | 없음 | **백엔드 완료, 화면 대기** | `proofreading_exclusions` | 중 | C16: 제외어 조회·추가·삭제 및 Tk와 동일 JSON 파일 공유 완료. Flutter 관리 모달은 다음 카드. [API](V2_PUBLIC_LANGUAGE_API.md). |
| **T13** | 서식 세부사항 확인 창 | L4472 `_서식_세부사항_확인` | 서식 프로필 상세 "세부 수치 보기/수정" 클릭 시 | - 입: 글자크기, 자간, 장평, 줄간격, 표 여백 등<br>- 출: 프로필 JSON 저장 | `features/formats/profile_editor.dart`<br>(`ProfileEditor`) | **완료** | `format_profile` (GET/PUT) | **상** | Flutter `ProfileEditor`로 100% 구현 완료됨. 브리지 `edit_profile`에서 Tk `_서식_수정하기`를 호출하는 잔존 분기 제거 대상. |
| **T14** | 서식 계층 구조 확인 창 | L4674 `_서식_구조_확인` | 서식 프로필 상세 "계층 구조(스타일) 보기" 클릭 시 | - 입: 항목기호별 글꼴/크기/들여쓰기 규칙<br>- 출: 계층 스타일 맵 저장 | `features/formats/profile_editor.dart`<br>(`ProfileEditor`) | **완료** | `format_profile` | **상** | `ProfileEditor` 내부 계층 스타일 탭에 완전 통합됨. |
| **T15** | 전체 환경설정 창 | L4832 `_설정창_생성` | 상단 메뉴 "설정" -> "환경설정" 클릭 시 | - 입: 폰트 매핑, COM 타임아웃, 백업 등 6개 탭<br>- 출: settings.json 저장 | `features/settings/settings_dialog.dart`<br>(`SettingsDialog`) | **완료** | `get_settings`, `save_settings`, `open_settings` | **상** | Flutter `SettingsDialog`가 구현 완료됨. 브리지 `open_settings`가 레거시 Tk 창(`설정창_열기`)을 띄우는 경로 제거 대상. |
| **T16** | kordoc 고급 문서 도구 창 | L5663 `고급문서도구_열기` | 메뉴바 "고급 도구" -> "HWP 구조 분석" 클릭 시 | - 입: 문서 덤프, 바이너리 검사, 필드 추출, 패치<br>- 출: 진단 결과 리포트 및 패치 파일 | `features/tools/document_tools_workspace.dart`<br>(`DocumentToolsWorkspace`) | **일부** | `document_tool` | 중 | Workspace 내 도구로 흡수 중이나 브리지 `run_tool('advanced')` 호출 시 Tk 창이 열림. |
| **T17** | 원본-결과 HWP 좌우 비교 창 | L5917 `비교창_준비` | 작업 완료 후 결과 목록 "좌우 비교 보기" 클릭 시 | - 입: 동기 스크롤 토글, 닫기<br>- 출: 좌측(원본) - 우측(결과) HWP COM 뷰어 | 없음 | **없음** | `launch_external_hwp_diff` (신규 독립 프로세스 브리지) | **상** | Windows OLE COM 뷰어 특성상 Flutter 직접 임베딩 불가. 독립 C#/Win32 뷰어 프로세스 분리 연동 필요. |
| **T18** | 대화상자 부모 헬퍼 | L6274 `_대화상자_부모` | Tk 모달 대화상자 중앙 정렬 시 내부 호출 | - 입/출: 1x1 투명 오버레이 윈도우 | 없음 (불필요) | **완료 (Tk 전용)** | N/A | 하 | Tk GUI 전용 내부 유틸리티. Flutter의 BuildContext 기반 모달 체계로 자동 소멸. |
| **T19** | 절약 완료 안내 창 | L6291 `_절약_완료창` | 전체 문서 맞춤/변환 배치 완료 시 | - 입: 확인, 결과 폴더 열기<br>- 출: 검은 고양이 그림, "OO분 시간 절약!" | `features/execution/execution_result_dialog.dart`<br>& `main.dart` (`outcome`) | **일부** | `get_state` | 중 | Flutter 4단계 결과 화면(`outcome`)에 완료 안내 표시 중. 캐릭터 및 시간 절약 연출 이관 가능. |
| **T20** | 서식통일 2단계: 대표 서식 검토 창 | L6415 `_서식통일_대표서식_검토창` | 다중 문서 서식 통일 마법사 2단계 도달 시 | - 입: 추출된 서식 후보 중 대표 기준 서식 선택<br>- 출: 선택된 기준 프로필 ID 확정 | `features/style_unify/unify_pick_style_dialog.dart`<br>(`UnifyPickStyleDialog`) | **완료** | `get_pending_dialog`, `resolve_dialog` | **상** | G29: 브리지 모달 및 Flutter 화면 이관 완료. `ui_tk_fallback=true` 시 기존 Tk 창 유지. [API](V2_STYLE_UNIFY_DIALOGS_API.md). |
| **T21** | 서식통일 3단계: 적용 영역 검토 창 | L6564 `_서식통일_적용영역_검토창` | 서식 통일 마법사 3단계 도달 시 | - 입: 문서별 적용 섹션/본문/표/머리말 체크박스<br>- 출: 적용 영역 매핑 구조체 | `features/style_unify/unify_area_dialog.dart`<br>(`UnifyAreaDialog`) | **완료** | `get_pending_dialog`, `resolve_dialog` | **상** | G29: 불일치 문장 선별 체크박스 이관 완료. `ui_tk_fallback=true` 시 기존 Tk 창 유지. [API](V2_STYLE_UNIFY_DIALOGS_API.md). |
| **T22** | 서식통일 5단계: 결과 확인 창 | L6672 `_서식통일_결과_확인창` | 서식 통일 마법사 완료 시 | - 입: 완료 확인, 결과 폴더 열기<br>- 출: 변경 문서 목록 및 적용 스타일 요약 | `features/style_unify/unify_result_dialog.dart`<br>(`UnifyResultDialog`) | **완료** | `get_pending_dialog`, `resolve_dialog` | **상** | G29: 검수 통계 및 결과 폴더 열기 이관 완료. `ui_tk_fallback=true` 시 기존 Tk 창 유지. [API](V2_STYLE_UNIFY_DIALOGS_API.md). |
| **S01** | 서식 이름 바꾸기 | L2168 `simpledialog.askstring` | 서식 프로필 복제/이름바꾸기 버튼 클릭 시 | - 입: 새 서식 이름 텍스트 | `main.dart`<br>(`RenameFormatDialog`) | **완료** | `rename_profile` | 상 | `main.dart` L3427 `RenameFormatDialog`에서 자체 처리 및 브리지 `rename_profile` 호출. |
| **S02** | 서식 기관명 바꾸기 | L2178 `simpledialog.askstring` | 서식 복사/이름바꾸기 시 기관명 입력 | - 입: 대상 기관명 텍스트 | `main.dart`<br>(`RenameFormatDialog`) | **완료** | `rename_profile` | 상 | `RenameFormatDialog`에서 이름과 기관명을 한 폼에서 입력받아 자체 완결. |
| **S03** | 서식 신규 생성 이름 입력 | L4320 `simpledialog.askstring` | 새 서식 만들기 클릭 시 | - 입: 새 서식 이름 텍스트 | `features/formats/profile_editor.dart`<br>(`ProfileEditor`) | **완료** | `format_profile` | 상 | Flutter 프로필 생성/저장 폼에서 자체 처리. |
| **S04** | 서식 신규 생성 기관명 입력 | L4327 `simpledialog.askstring` | 새 서식 만들기 시 기관명 입력 | - 입: 기관명 텍스트 | `features/formats/profile_editor.dart`<br>(`ProfileEditor`) | **완료** | `format_profile` | 상 | Flutter 프로필 생성/저장 폼에서 자체 처리. |
| **S05** | kordoc 페이지 분할 범위 입력 | L5693 `simpledialog.askstring` | 문서 도구에서 "페이지별 Markdown" 실행 시 | - 입: 분할 페이지 번호/범위 (예: 1-3, 5) | `features/tools/document_tools_workspace.dart`<br>(`DocumentToolsWorkspace`) | **일부** | `document_tool` | 중 | Workspace 내부 탭의 인라인 입력 필드로 이관 필요. |
| **S06** | kordoc 양식 필드값 수정 입력 | L5699 `simpledialog.askstring` | 고급 도구 "양식 자동 채우기" 실행 시 | - 입: 필드명 및 치환할 값 문자열 | `features/tools/document_tools_workspace.dart`<br>(`DocumentToolsWorkspace`) | **일부** | `document_tool` | 중 | Workspace 내부 탭의 양식 채우기 폼으로 이관 필요. |

---

## 3. 메시지 / 확인 / 질문 대화상자 (`self._알림` 및 `messagebox`)

`legacy.py` 내에는 총 85개 지점에서 사용자 알림/확인 대화상자가 호출되며, 48개의 고유 기능으로 분류됩니다.

### 3.1 브리지 대화상자 연동 메커니즘
- 웹 모드(`self._web_mode == True`)에서 `self._알림(...)` 호출은 `desktop_web_ui.py`의 `enqueue_dialog`를 거쳐 Flutter의 `BackendDialog`(`get_pending_dialog` / `resolve_dialog`)로 전달되어 웹 화면 내 모달로 안전하게 표시됩니다.
- 지원 유형:
  1. `종류="info"`: 단일 "확인" 안내 팝업.
  2. `종류="warning"`: 단일 "확인" 경고 팝업.
  3. `종류="error"`: 오류 메시지 팝업.
  4. `종류="question"`: "확인 / 취소" 2버튼 선택 팝업.
  5. `선택지=[...]`: 커스텀 버튼 목록을 가진 다중 선택 팝업.
  6. `입력필드=[...]`: 텍스트 입력을 동반하는 프롬프트 팝업.

### 3.2 주요 메시지 대화상자 목록 (실측 행 번호)

| 번호 | 메시지 대화상자 명칭 | legacy.py 호출 위치 | 발생 상황 | 종류 및 버튼 구성 | 현재 상태 | 비고 및 Flutter 브리지 대응 |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **M01** | 빈 파일 목록 경고 | L636, L1418, L5425 | 파일 미선택 상태에서 변환 시작 시 | 경고 (확인) | 완료(브리지 대화상자) | Flutter UI 차원에서 시작 버튼 비활성화로 사전 차단 |
| **M02** | 변환 진행 중 중단 확인 | L1008, L5502 | 작업 수행 중 창 닫기/취소 클릭 | 질문 (예 / 아니오) | 완료(브리지 대화상자) | Flutter 작업 취소 다이얼로그와 연동 |
| **M03** | 변환 완료 안내 | L1285, L5460 | 전체 작업 정상 완료 시 | 정보 (확인, 폴더열기) | 완료(브리지 대화상자) | 커스텀 액션 버튼("결과 폴더 열기") 브리지 지원 |
| **M04** | 서식 프로필 저장 확인 | L2250, L4372 | 프로필 수정 후 저장 클릭 시 | 정보 (확인) | 완료(브리지 대화상자) | Flutter ProfileEditor 내부 스낵바/알림으로 대체 |
| **M05** | 서식 프로필 삭제 확인 | L2271, L4405 | 프로필 삭제 클릭 시 | 질문 (삭제 / 취소) | 완료(브리지 대화상자) | 삭제 확인 모달 연동 |
| **M06** | HWP COM 연결 실패 경고 | L2815, L5890 | 한/글 미설치 또는 COM 초기화 실패 | 오류 (확인) | 완료(브리지 대화상자) | 명확한 조치 가이드(한/글 재실행) 텍스트 제공 |
| **M07** | 서식 통일 대상 부족 경고 | L6480, L6510 | 서식 통일 시 문서가 2개 미만일 때 | 경고 (확인) | 완료(브리지 대화상자) | 마법사 진입 전 검증 |
| **M08** | 대표 서식 불일치 경고 | L6620 | 기준 서식과 문서 양식 차이가 클 때 | 질문 (계속 / 중단) | 완료(브리지 대화상자) | 위험도 경고 후 계속 진행 여부 선택 |
| **M09** | 폰트 설치 안내 | L5380 | 필수 글꼴 누락 감지 시 | 정보 (확인) | 완료(브리지 대화상자) | 누락된 폰트명 목록 브리지 표시 |
| **M10** | 임시 파일 정리 확인 | L5820 | 디스크 공간 확보를 위한 캐시 정리 | 질문 (삭제 / 유지) | 완료(브리지 대화상자) | 확인 대화상자 연동 |
| **M11** | messagebox 직접 호출 잔존 | L2310, L3815 등 (총 7곳) | 일부 예외 처리 및 서브루틴 | messagebox.* 직접 호출 | **없음 (Tk 모달)** | **주의**: `self._알림`을 거치지 않아 웹 모드에서도 Tk 모달이 뜸. `self._알림`으로 전면 교체 필요 |

---

## 4. 파일 및 폴더 선택 대화상자 (`filedialog` 15건 전수)

`docfit_ui/legacy.py` 내의 파일 및 폴더 열기/저장 대화상자는 총 15곳에 존재합니다.

| 번호 | 호출 함수 및 위치 | 대화상자 종류 | 선택 대상 및 용도 | 현재 상태 | Flutter 전환 시 권장 정책 |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **F01** | L2044 `_폴더선택` | `askdirectory` | 변환 대상 문서들이 포함된 폴더 선택 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F02** | L2735 `_서식_파일에서_추가` | `askopenfilename` | 서식 복제용 예시 HWP/HWPX 파일 선택 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F03** | L2907 `_문서검토_열기` (`export_result`) | `asksaveasfilename` | 문서 구조/가독성 분석 결과 JSON 저장 경로 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F04** | L3350 `_아웃라이너_열기` (`개조식으로추가`) | `asksaveasfilename` | 아웃라이너 작성 결과 .txt 파일 저장 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F05** | L3374 `_아웃라이너_열기` (`마크다운으로추가`) | `asksaveasfilename` | 아웃라이너 작성 결과 .md 파일 저장 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F06** | L3395 `_아웃라이너_열기` (`저장`) | `asksaveasfilename` | 아웃라이너 전용 구조 데이터 저장 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F07** | L3410 `_아웃라이너_열기` (`열기`) | `askopenfilename` | 기존 아웃라이너 데이터 파일 열기 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F08** | L3530 `_텍스트로_문서추가_열기` (`폴더_찾아보기`) | `askdirectory` | 텍스트 변환 HWP 자동 저장 대상 폴더 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F09** | L3624 `_텍스트로_문서추가_열기` (`문서로추가`) | `asksaveasfilename` | 변환 텍스트 수동 .txt 파일 저장 위치 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F10** | L4079 `_작성도우미_열기` (`문서고르기`) | `askopenfilename` | 공문서 도우미 기관 서식 템플릿 HWP 열기 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F11** | L4309 `_서식_복사하기` | `askopenfilename` | 서식 프로필 복제 원본 파일 선택 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F12** | L5343 `_폰트폴더_찾아보기` | `askdirectory` | 설정창 사용자 폰트 검색 폴더 선택 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F13** | L5582 `파일선택` | `askopenfilenames` | 메인 화면 변환 대상 다중 HWP/오피스 파일 선택 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F14** | L5696 `고급문서도구_열기` (`compare_tool`) | `askopenfilename` | 고급 문서 도구 비교 대상 HWP 파일 선택 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |
| **F15** | L5702, L5732 `고급문서도구_열기` (`patch_tool` 등) | `askopenfilename` | kordoc 패치 및 Markdown 생성 대상 파일 선택 | 없음 | **Windows 네이티브 대화상자 유지** (`file_picker`) |

### 4.1 파일/폴더 대화상자 정책 제안
> [!IMPORTANT]
> **Windows 네이티브 대화상자(IFileDialog / comdlg32) 유지 적극 권장**
> 공무원 실무 환경에서는 즐겨찾기, 네트워크 공유 드라이브(NAS), 최근 열어본 폴더, 파일 미리보기 기능이 필수적입니다. Flutter Desktop 환경에서는 검증된 `file_picker` 패키지를 통해 OS 네이티브 다이얼로그를 띄우고, 백엔드에는 선택된 절대 경로(Absolute Path) 문자열만 전달하는 표준 방식을 채택합니다.

---

## 5. `desktop_web_ui.py`의 Tk 창 호출 브리지 API 전수 ("Flutter에서 눌렀는데 Tk 창이 뜨는" 경로)

`desktop_web_ui.py`(2,003줄)의 공개 API 중 `self._tk(..., front=True)` 또는 Tk 창/대화상자를 직접 호출하는 경로는 다음과 같습니다. 이 경로들이 현재 **Flutter UI 상에서 버튼을 눌렀을 때 백그라운드 Tk 창이 뜨는 실제 통로**입니다.

| 번호 | 공개 API 메서드명 (행 번호) | 호출 대상 (legacy.py 함수 / Toplevel 번호) | Flutter 트리거 동작 (언제 뜨나) | 현재 동작 및 문제점 | 2.0.0 전환 방안 |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **B01** | `add_files` (L618) | `self.gui.파일선택` (F13) | 1단계 "문서 추가" 버튼 또는 Ctrl+O | `self._tk(..., front=True)`로 Win32 파일 선택창 호출 | Flutter `file_picker`로 파일 선택 후 경로만 백엔드 전송 |
| **B02** | `add_folder` (L623) | `self.gui._폴더선택` (F01) | 1단계 "폴더 추가" 버튼 클릭 시 | `self._tk(..., front=True)`로 Win32 폴더 선택창 호출 | Flutter `file_picker` `getDirectoryPath()`로 대체 |
| **B03** | `open_settings` (L935) | `self.gui.설정창_열기` (T15) | 설정 드로어 "전체 설정 열기" 클릭 시 | `self._tk(..., front=True)`로 레거시 Tk 환경설정 창 띄움 | Flutter `SettingsDialog`가 이미 존재하므로 브리지의 Tk 호출 제거 |
| **B04** | `text_input` (L939) | `self.gui._텍스트로_문서추가_열기` (T07) | 1단계 "텍스트 붙여넣기" 클릭 시 | `self._tk(..., front=True)`로 Tk 텍스트 입력 창 띄움 | Flutter `DocumentToolsWorkspace(initial: 'convert')` 모달로 대체 |
| **B05** | `open_stages` (L943) | `self.gui._세부작업_열기` (T02) | 2단계 세부작업 상세 조정 클릭 시 | `self._tk(..., front=True)`로 Tk 세부작업 팝업 띄움 | Flutter `showStages()` AlertDialog로 완전 일원화 |
| **B06** | `open_log` (L949) | `self.gui.log_window` (T01) | 로그 메뉴 또는 상태바 클릭 시 | `log_window.deiconify()`, `lift()`로 숨은 Tk 창 표시 | Flutter `LiveProgress` / `showLog()` 다이얼로그로 완전 대체 |
| **B07** | `flow_editor` (L1045) | `filedialog.asksaveasfilename` | 표 편집기 PNG 내보내기 시 | `self._tk(..., front=True)`로 Tk 파일 저장창 호출 | Flutter `file_picker` `getSavePath()`로 대체 |
| **B08** | `flow_editor` (L1083) | `filedialog.asksaveasfilename` | 표 편집기 HWPX 내보내기 시 | `self._tk(..., front=True)`로 Tk 파일 저장창 호출 | Flutter `file_picker` `getSavePath()`로 대체 |
| **B09** | `idioms` (L1321) | `filedialog.askopenfilename` | 본문 상용구 파일 등록 시 | `self._tk(..., front=True)`로 Tk 파일 열기창 호출 | Flutter `file_picker`로 대체 |
| **B10** | `table_template` (L1372) | `filedialog.askopenfilename` | 기본 표 서식 학습 파일 선택 시 | `self._tk(..., front=True)`로 Tk 파일 열기창 호출 | Flutter `file_picker`로 대체 |
| **B11** | `add_format_file` (L1628) | `self.gui._서식_파일에서_추가` (F02) | 서식 관리 "예시 파일에서 복제" 클릭 시 | `self._tk(..., front=True)`로 Tk 파일 열기창 호출 | Flutter `file_picker`로 대체 |
| **B12** | `write_format_example` (L1633) | `self.gui._서식_예시편집_시작` (T04) | 서식 관리 "예시 작성하여 복제" 클릭 시 | `self._tk(..., front=True)`로 Tk 예시편집 창 띄움 | Flutter 가이드 다이얼로그로 전환 |
| **B13** | `edit_profile` (L1652) | `self.gui._서식_수정하기` (T13/T14) | 서식 관리 "세부 수정" 버튼 클릭 시 | `self._tk(..., front=True)`로 Tk 서식세부창 띄움 | Flutter `ProfileEditor`가 이미 완비되어 있으므로 Tk 호출 분기 제거 |
| **B14** | `run_tool(name)` (L1715~1733) | `review` (T05)<br>`proofread` (T11)<br>`paste` (T07)<br>`polish` (T08)<br>`outline` (T06)<br>`writing` (T10)<br>`advanced` (T16) | 개발자 모드 도구 메뉴의 각 항목 클릭 시 | `self._tk(command, front=True)`로 각 레거시 Tk 도구 창 호출 | Flutter `DocumentToolsWorkspace` 탭 네비게이션으로 100% 흡수 |

---

## 6. 종합 요약 및 통계

### 6.1 전체 대화상자/화면 집계

| 분류 | 전체 개수 | 완료 (Flutter 완비) | 완료 (브리지 대화상자) | 일부 (Workspace 흡수 등) | 없음 (미구현/외부) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Toplevel 화면** | 22 | 9 | 0 | 9 | 4 (T18 헬퍼 포함) |
| **simpledialog** | 6 | 4 | 0 | 2 | 0 |
| **메시지/알림 대화상자** | 48 | 0 | 41 | 0 | 7 (messagebox 직호출) |
| **filedialog (파일/폴더)** | 15 | 0 | 0 | 0 | 15 (`file_picker` 대상) |
| **총합** | **91** | **13** | **41** | **11** | **26** |

- **실제 동등성 달성률**: 완전 전환(13) + 브리지 연동(41) = **59.3% (54/91)** 달성.
- **핵심 사실 정정**:
  - `T03` 서식 키오스크는 초안과 달리 `main.dart`의 `openKiosk()`와 `kioskCard`로 이미 완료됨.
  - `T02` 세부작업, `T13/T14` 서식수정, `T15` 환경설정은 Flutter 위젯이 이미 존재함에도 `desktop_web_ui.py`에 Tk 창 호출 경로(B03, B05, B13)가 잔존하여 이중 유지 중임.

---

## 7. 3단계 이관 순서 (제안)

사용자가 실무에서 실제로 자주 마주치는 Tk 창을 중심으로 실사용 빈도 순 Top 10을 선정하고, 2.0.0 단일 UI 전환을 위한 브리지 API 및 Flutter 파일 위치를 제안합니다.

| 순위 | 대상 창 (번호 및 여는 함수) | 실사용 빈도 및 선정 사유 | 필요한 브리지 API (desktop_web_ui.py) | 예상 Flutter 파일 위치 | 2.0.0 이관 방안 |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **[T02] 세부 작업 설정**<br>(L1386 `_세부작업_열기`) | **최상** (문서 맞춤 파이프라인의 필수 조절 창) | `set_stage`, `stage_config` (POST /api/stage-config) | `flutter_ui/lib/features/stages/stage_board.dart` | 이미 구현 완료된 `StageBoard` 및 `showStages` 모달로 전면 일원화하고 B05 브리지 제거 |
| **2** | **[T15] 전체 환경설정**<br>(L4832 `_설정창_생성`) | **최상** (폰트 매핑, 타임아웃 등 핵심 전역 설정) | `get_settings`, `save_settings` (GET/POST /api/settings) | `flutter_ui/lib/features/settings/settings_dialog.dart` | 이미 완비된 `SettingsDialog`를 기본 호출하고 B03 브리지의 레거시 Tk 창 생성 코드 제거 |
| **3** | **[T01] 처리 기록 창**<br>(L760 `__init__`, `_기록토글`) | **상** (오류 확인 및 실시간 처리 진행 감시) | `get_state`, `get_log` | `flutter_ui/lib/features/progress/live_progress.dart` | `LiveProgress` 및 `showLog` 다이얼로그로 완전 일원화하고 B06 브리지의 `log_window` 제거 |
| **4** | **[T20] 서식통일 2단계: 대표서식 검토**<br>(L6415 `_서식통일_대표서식_검토창`) | **상** (다중 문서 서식 통일 시 필수 기준 승인 단계) | `flow_wizard` 또는 `get_pending_dialog` / `resolve_dialog` | `flutter_ui/lib/features/wizard/unify_step2_baseline_dialog.dart` (신규) | 추출된 서식 후보와 대표값을 비교/선택하는 Flutter 5단계 마법사 Step 2 위젯 신설 |
| **5** | **[T21] 서식통일 3단계: 적용영역 검토**<br>(L6564 `_서식통일_적용영역_검토창`) | **상** (대표 서식 미적용 문단 선별 적용 단계) | `resolve_dialog` (selected indices 반환) | `flutter_ui/lib/features/wizard/unify_step3_scope_dialog.dart` (신규) | 문장별 변경 예정 속성 확인 및 체크박스 토글 리스트 위젯 신설 |
| **6** | **[T22] 서식통일 5단계: 결과 확인**<br>(L6672 `_서식통일_결과_확인창`) | **상** (서식 통일 완료 및 변경 내역 검수) | `get_state` (completion report) | `flutter_ui/lib/main.dart` (`outcome` 패널) | Flutter 4단계 결과 탭의 작업 메시지/검수 결과 카드에 서식 통일 완료 보고 통합 |
| **7** | **[T11] 공공언어/맞춤법 검토**<br>(L4162 `_공공언어_검토`) | **상** (공공기관 공문서 오류 교정 핵심 가치) | `document_tool` (action='proofread'), `idioms` | `flutter_ui/lib/features/tools/document_tools_workspace.dart` | Workspace 내 'proofread' 탭 고도화 및 B14의 `run_tool('proofread')` Tk 호출 제거 |
| **8** | **[T17] 원본-결과 HWP 좌우 비교**<br>(L5917 `비교창_준비`) | **상** (자간/서식 작업 전후 신구대조 시각 확인) | `launch_external_hwp_diff` (신규 독립 프로세스 브리지) | `flutter_ui/lib/features/execution/diff_launcher_button.dart` | OLE COM 종속 분리를 위해 가벼운 독립 실행 Win32 뷰어로 분리 호출 |
| **9** | **[T05] 문서 구조·가독성 검토**<br>(L2879 `_문서검토_열기`) | **중** (보고서 품질 진단 및 글자수 통계) | `document_tool` (action='review') | `flutter_ui/lib/features/tools/document_tools_workspace.dart` | Workspace 내 'review' 탭 고도화 및 B14의 `run_tool('review')` Tk 호출 제거 |
| **10** | **[T10] 공문서 작성 도우미**<br>(L3870 `_작성도우미_열기`) | **중** (금액 한글화, 날짜 요일, 만 나이, 공문 서식) | 순수 Dart 로직 또는 `document_tool` (action='writing') | `flutter_ui/lib/features/tools/document_tools_workspace.dart` | Workspace 내 'writing' 탭 완성 및 B14의 `run_tool('writing')` Tk 호출 제거 |
