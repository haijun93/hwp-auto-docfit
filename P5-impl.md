# P5 구현 결과 보고서 (P5-impl.md)

- 작성 일시: 2026-10-28
- 작성자: 코더 (Antigravity)
- 기준 브랜치: `feature/2.0.1-file-conversion` (main=v2.0.0 기준, HEAD ea84ccfebbe35ead55b24b844cb737e6654a7b22)
- 참조 설계서: `~/work/hwp/P5-design.md` (`docs/P5-design.md`)

---

## 1. 개요 및 작업 요약

선임(Codex)의 설계서 `P5-design.md`의 모든 요구사항을 **그대로** 구현 완료하였습니다.
- 6번째 탭 '파일변환'에 잘못 연결되어 있던 `DocumentToolsWorkspace`를 제거하고, 전용 화면인 `FileConversionWorkspace`로 교체하였습니다.
- 기존 변환 실행 백엔드 사슬(`DesktopWebBridge.start_job('file_format', ...)`, `gui.파일포맷_변경_시작`, `conversion_runner`) 및 UI 컴포넌트(`FloatingFormatPicker`, `MergeOrderDialog`)를 100% 재사용하였으며 새로운 변환 엔진이나 하위 프로세스를 생성하지 않았습니다.
- 변환 전용 파일 선택 purpose(`add_conversion_files`) 및 브리지 메서드(`get_file_conversion_state`, `add_conversion_files`)를 신설하여 기존 문서편집 정책에 영향을 주지 않고 PPTX, HTML 등 `CONVERSION_INPUTS` 형식을 안전하게 지원하도록 하였습니다.
- `_IntegratedAppWorkspace` 호스트 및 `Workspace.isActive` 가드를 구현하여 숨은 탭의 팝업/배지 좌표 보고/드롭 대상 오작동을 차단하였습니다.
- 사용자 지시("명령 실행 불가: 시험은 작성만, 커밋 금지")에 따라 자동 시험 파일(Python 4종, Flutter 2종)을 모두 작성하였으며 쉘 명령 실행이나 커밋은 수행하지 않았습니다.

---

## 2. 작업 파일 목록 및 상세 구현 내역

### 2.1 백엔드 및 서비스 레이어

1. **`docfit_app/native_file_dialog_service.py`** (수정)
   - `docfit_core.file_conversion.CONVERSION_INPUTS` import.
   - `PURPOSES['add_conversion_files'] = ('open', CONVERSION_INPUTS)` 추가.
   - `_policy` 메서드의 다중 선택 허용 조건을 `purpose not in {'add_files', 'add_conversion_files'}`로 확장.
   - `register_selection`의 다중 경로 허용 집합에 `'add_conversion_files'` 추가. 기존 300초 TTL, 일회용 소비, 보안 검증 유지.

2. **`docfit_ui/legacy.py`** (수정)
   - `파일추가(self, file_path, *, file_conversion=False)` 시그니처 확장.
   - `file_conversion=True`일 때만 함수 내부에서 `CONVERSION_INPUTS`를 import하여 검사하고, 기본값 `False`에서는 기존 `지원_확장자` 검사 및 모든 동작을 그대로 보존.

3. **`desktop_web_ui.py`** (수정)
   - `get_file_conversion_state(self)`: Tk snapshot 밖에서 `_conversion_targets`를 조회하고 복사본에 `conversion_targets`, `conversion_target`, `can_start`를 채워 반환 (mode가 file_format이면 중복 조회 방지).
   - `add_conversion_files(self, selection_id)`: 일회용 토큰 해석 후 `add_paths(..., file_conversion=True)` 전달 및 변환 상태 반환.
   - `add_paths(self, paths, *, from_drop=False, file_conversion=False)`:
     - `file_conversion=True` 시 `add_conversion_files` purpose 등록 및 `gui.파일추가(path, file_conversion=True)` 호출.
     - 폴더가 들어올 경우 목록에 추가하지 않고 상태 문구로 `'파일을 끌어 놓아 주세요'` 안내.
     - `file_conversion=False`인 기존 분기 및 동작 100% 보존.
   - `set_drop_target(target)`: 허용 값에 `'file_conversion'` 추가.
   - `receive_drop`: `drop_target == 'file_conversion'` 분기를 최우선으로 배치하여 배지 좌표나 기존 분기보다 먼저 처리되도록 보장.
   - `_BrowserApi`: 공개 목록에 `get_file_conversion_state`, `add_conversion_files`, `select_files`, `selection_status` 추가.

### 2.2 Flutter 프런트엔드

4. **`flutter_ui/lib/main.dart`** (수정)
   - `FileConversionWorkspace` import 추가.
   - `DocFitApp`: `useIntegratedShell` 분기에서 `_IntegratedAppWorkspace`를 마운트 (`useIntegratedShell=False`인 단독 `Workspace` 경로는 유지).
   - `_IntegratedAppWorkspace` (신규 State):
     - `selectedIndex` (기본 0), 탭 0일 때 `Workspace(isActive: true)`, 탭 5일 때 `FileConversionWorkspace(isActive: true)`.
     - `_routeDropTarget`: 세대 번호를 통한 async 직렬 큐로 탭 5면 `'file_conversion'`, 그 외는 `'documents'`로 드롭 대상 동기화.
   - `Workspace`:
     - `final bool isActive` (기본 `true`) 파라미터 추가.
     - `reportProfileBounds`: `!widget.isActive` 시 조기 반환.
     - `didUpdateWidget`: 비활성화(`true -> false`) 시 `lastProfileBounds = null` 및 `set_profile_drop_bounds([0,0,0,0])` 호출, 활성화 시 다음 프레임에 재보고.
     - `apply`: post-frame callback에서 `widget.isActive`일 때만 팝업/탭 전환/포맷 선택창(`openConversionPicker`) 호출. 백그라운드 상태 적용 및 대화상자 처리는 유지.
     - `openConversionPicker`: `!widget.isActive` 가드 추가.
     - `setDropTarget`: `!widget.isActive` 가드 추가.
     - 텍스트 입력 진입점(`openTools('convert')`) 및 기존 문서편집 동작 보존.

5. **`flutter_ui/lib/features/conversion/file_conversion_workspace.dart`** (신규 전체)
   - `FileConversionWorkspace` 구현 (main.dart 미참조, 순수 컴포넌트 재사용).
   - 상태 관리: `snapshot`, `jobItems`, `trackedJob`, `busy`, `polling`, `pickerOpen`, `cancelPending`, `revision`, `nextSeq`.
   - UI 레이아웃:
     - 좁은 창(폭 420) 및 넓은 창(1280) 대응 가능한 반응형 스크롤 레이아웃.
     - 헤더 '파일변환' 및 안내 텍스트('문서편집과 파일 목록을 함께 사용합니다').
     - 파일 추가/전체 비우기, 파일 목록 리스트뷰 (파일명, 확장자 뱃지, 전체 경로 툴팁, 개별 삭제 버튼).
     - 대상 형식 선택 버튼 (`FloatingFormatPicker` 다이얼로그 호출), 선택 불가 사유 안내.
     - 'pdfm' 선택 시 `MergeOrderDialog`를 통한 파일 순서 재정렬 지원 및 다이얼로그 도중 목록 변경 방어.
     - 진행 막대(`LinearProgressIndicator`), 처리 건수, 작업 취소 버튼.
     - 변환 완료/실패 요약 및 결과 폴더 열기(`show_result`) 버튼.
   - 모든 필수 Key 배치: `fileConversionWorkspace`, `conversionAddFiles`, `conversionClearFiles`, `conversionFileList`, `conversionRemove_<index>`, `conversionChooseFormat`, `conversionProgress`, `conversionCancelJob`, `conversionOpenResults`, `conversionError`.

### 2.3 무인 자동 시험 (테스트 코드)

6. **`tests/test_v2_file_dialog_service.py`** (확장)
   - `test_conversion_selection_accepts_supported_formats`: CONVERSION_INPUTS 전체 확장자 지원 및 PPTX 복수 선택 토큰 검증.
   - `test_conversion_purpose_does_not_expand_document_policy`: PPTX가 `add_conversion_files`에서는 성공하고 기존 `add_files`에서는 `UNSUPPORTED_FORMAT`으로 거부됨을 확인.
   - `test_conversion_token_is_bound_single_use_and_expires`: 일회용 소비, TTL 만료, purpose 바인딩, 메타데이터 경로 은닉 검증.
   - `test_conversion_selection_cancel_and_request_dedup`: 취소 및 동시 중복 요청 1회 실행(dedup) 검증.

7. **`tests/test_desktop_file_drop.py`** (확장)
   - `test_conversion_drop_precedes_profile_badge`: `file_conversion` 타깃일 때 배지 영역 안 좌표에서도 서식 복제가 아닌 `add_paths(..., file_conversion=True)`가 호출됨을 검증.
   - `test_existing_drop_targets_keep_routing`: `documents`, `manual_documents`, `format`, `quick_format` 기존 라우팅 보존 검증.
   - `test_conversion_drop_rejects_folders_and_missing_native_paths`: 폴더 드롭 거부 문구('파일을 끌어 놓아 주세요') 및 경로 없는 드롭 거부 검증.

8. **`tests/test_p5_file_conversion_bridge.py`** (신규 전체)
   - `test_conversion_snapshot_keeps_editor_mode_and_uses_targets`: 에디터 모드 불변 및 변환 대상/가능 여부 확인.
   - `test_conversion_snapshot_does_not_duplicate_ready_probe`: mode=file_format 시 targets 중복 조회 방지 검증.
   - `test_selected_pptx_uses_conversion_policy`: 선택 토큰을 통한 PPTX 등록 및 gui 위임 검증.
   - `test_running_job_rejects_conversion_list_mutation`: 실행 중 목록 변형(추가/삭제/비우기) 차단 검증.
   - `test_file_format_start_delegates_existing_worker`: 기존 `gui.파일포맷_변경_시작` 위임, subprocess/COM 차단 검증.
   - `test_job_cancellation_uses_exact_id`: 정확한 Job ID 취소 위임 확인.
   - `test_show_result_reveals_folder_without_opening_document`: 문서 실행 없이 폴더만 열기 검증.
   - `test_browser_api_exposes_only_required_conversion_methods`: API 화이트리스트 노출 검증.
   - `test_registration_preserves_source_bytes`: 등록 전후 원본 파일 바이트 SHA-256 불변 검증.

9. **`tests/test_p5_legacy_file_registration.py`** (신규 전체)
   - `ast`를 사용하여 `docfit_ui/legacy.py`의 `파일추가` 원본 AST 노드를 추출·컴파일하여 시험 환경에 바인딩.
   - `test_default_file_registration_keeps_extensions`: 기본 호출 시 기존 지원_확장자만 허용, HTML 거부 검증.
   - `test_conversion_file_registration_accepts_html_and_pptx`: `file_conversion=True` 시 HTML, PPTX 정상 등록 및 UI/카운터 갱신 검증.
   - `test_conversion_file_registration_rejects_invalid_and_duplicate`: exe/미존재 파일/중복 등록 거부 검증.

10. **`flutter_ui/test/file_conversion_workspace_test.dart`** (신규 전체)
    - 설계서 7장에 명시된 15개 항목 단독 위젯 시험 구현 완료:
      1. `file conversion shows files without text tools`
      2. `adds selected pptx through scoped selection token`
      3. `cancelled selection leaves file list unchanged`
      4. `file addition and drop refresh never start conversion`
      5. `format choice starts existing file_format job once`
      6. `unavailable target cannot start`
      7. `picker cancellation preserves target and files`
      8. `merge confirmation preserves chosen order`
      9. `merge cancellation and changed files do not start`
      10. `progress and cancellation follow tracked job`
      11. `event gap restores snapshot and partial failures`
      12. `stale refresh cannot restore removed files`
      13. `opens result folder only on explicit click`
      14. `inactive widget and disposal stop side effects`
      15. `layout supports narrow and wide windows`

11. **`flutter_ui/test/file_conversion_integration_test.dart`** (신규 전체)
    - 설계서 7장에 명시된 5개 항목 통합 시험 구현 완료:
      1. `sixth tab mounts FileConversionWorkspace`
      2. `hidden editor cannot open picker on conversion update`
      3. `switching tabs preserves conversion job and routes drops`
      4. `text input keeps original entrypoint`
      5. `standalone Workspace retains existing behavior`

---

## 3. 설계(P5-design.md) 대비 차이점

- **차이점 없음 (설계 100% 완전 준수)**:
  - 설계서에 지정된 시그니처, 파일 위치, 위젯 Key, API 계약, 예외 처리, 비활성 가드, 중복 조회 방지 등을 일점일획 빠짐없이 그대로 구현하였습니다.
  - 임의의 편법(return/pass/if True/if False/주석 처리)이나 불필요한 기능 확장, 신규 패키지 추가를 일절 배제하였습니다.
  - 모든 파일의 CRLF 줄바꿈 형식을 유지하였습니다.

---

## 4. 검수자(실행 담당자) 확인 및 실행 요청 사항

코더 역할 지침에 따라 테스트 실행 명령 및 Git 커밋은 일절 수행하지 않았습니다. 검수 담당자께서는 아래 절차로 검증을 진행해 주시기 바랍니다.

1. **Python 테스트 검증**:
   ```powershell
   .\.venv\Scripts\python.exe -m unittest tests/test_p5_file_conversion_bridge.py tests/test_p5_legacy_file_registration.py tests/test_v2_file_dialog_service.py tests/test_desktop_file_drop.py
   .\.venv\Scripts\python.exe -m unittest discover -s tests
   ```
2. **Flutter 테스트 및 정적 분석**:
   ```bash
   cd flutter_ui
   flutter analyze
   flutter test test/file_conversion_workspace_test.dart test/file_conversion_integration_test.dart
   flutter test
   ```
3. **Web 빌드 재생성 (필요 시)**:
   ```powershell
   .\build_flutter.ps1
   ```
4. **Git 작업 마무리**:
   - `feature/2.0.1-file-conversion` 브랜치에 변경 사항 커밋.
   - 푸시: `github` 원격 저장소 먼저 푸시 후, `origin`(GitLab 백업) 푸시.

---

## 5. 질문 사항

- 현재 설계서 1장 형식 계약에 명시된 바와 같이, `HWP` 및 `PPTX`는 **입력 형식**이며 현재 변환 **출력 대상**이 아닙니다. 이 제약 사항과 `_conversion_targets`의 `enabled`/`reason` 노출 정책이 UI와 단위 테스트에 정확히 반영되었습니다. 향후 HWP/PPTX 출력이 엔진 차원에서 지원되기 전까지 현재와 같이 비활성화 안내 문구로 유지하면 되는지 확인 부탁드립니다.
