# 2.0.0 잔여 상세 설계 — 확정 계약 v1

작성: Codex, 2026-10-27. 대상 브랜치: `dev/2.0.0`.
근거: `V2_CORE_CONTRACTS.md`, `V2_PARITY_TABLE.md`의 C26, 현재
`desktop_web_ui.py`, `workspace_adapters.dart`, `docfit_core/session` 구현.
본 문서는 후속 구현의 규범이다. 설계 확정과 운영 기능 구현 완료를 구분한다.
T17 실행 백엔드·Flutter 파일 선택 교체·HWPX 직렬화는 이 변경에서 구현하지 않는다.

## 1. T17 프로세스 경계

운영 Flutter는 현재 WebView2 안의 웹 빌드다. Flutter가 Python이나 OLE를 직접 생성하지 않는다.
`IntegratedWorkspace.api` → `DesktopWebBridge` → 새 `DiffHostService` → 독립
`docfit_engine.diff_host` 프로세스 → 좌우 HwpCtrl ActiveX 두 개 순서로 연결한다.
기존 Tk 비교창은 사용하지 않는다. OLE HWND를 WebView2에 SetParent하지 않는다.
뷰어는 독립 최상위 Win32 창이며 Flutter 다이얼로그는 연결 상태와 제어만 표시한다.

호스트는 Win32 메시지 루프와 STA COM 초기화를 소유한다. OLE 활성화·열기·이동·해제는
모두 해당 STA 큐에서만 수행한다. IPC 읽기 스레드는 JSON 검증과 큐 전달만 한다.
두 컨트롤은 각각 문서 하나를 소유하며 사용자 실행 중인 HwpObject에 연결하지 않는다.
런타임은 설치된 HwpCtrl의 비트수와 일치해야 한다. 사전 검사 실패 시
`OLE_NOT_AVAILABLE`/`OLE_BITNESS_MISMATCH`로 끝내며 자동 설치나 Tk 폴백은 없다.
개발 실행은 `[venv_python, '-m', 'docfit_engine.diff_host']`, 동결판은 전용 서명된
`docfit-diff-host.exe` 진입점을 패키징한다. 셸 문자열 실행은 금지한다.

### 1.1 파일 보호와 세션 식별

Flutter 요청은 `{document_id, result_id, expected_revision, request_id}`다.
기존 index 기반 `open_diff`/`compare_result`/`launch_external_hwp_diff`는 선택 순간
문서·결과 ID로 고정한 뒤 같은 서비스로 전달하는 호환 어댑터로 남긴다.
결과 인덱스를 비동기 완료 시 다시 조회하지 않는다. 백엔드는 결과 레지스트리에서만
원본·결과 경로를 찾고 임의 JS 경로를 T17 입력으로 받지 않는다.
미저장 draft는 자동 저장하지 않는다. 저장된 결과 revision과 현재 revision이 다르면
`UNSAVED_REVISION`을 반환하고 Flutter가 저장된 결과 비교임을 표시한다.

서비스는 원본과 결과를 읽어 전용 `%LOCALAPPDATA%/HwpAutoDocFit/diff/<viewer_id>/`
안에 배타 생성한 `left.hwp[x]`, `right.hwp[x]` 사본으로 복사한다. 원본과 결과 해시,
파일 ID·크기·수정 시각을 복사 전후 대조하며 바뀌면 `SOURCE_CHANGED`로 실패한다.
사용자 경로의 파일 속성·ACL은 변경하지 않는다. 호스트에는 사본 경로만 전달한다.
사본을 읽기 전용 속성 및 HwpCtrl 읽기 전용 모드로 열고 편집·저장·인쇄·외부 링크
실행 UI와 단축키를 차단한다. 읽기 전용 모드 설정/검증 실패 시 창을 열지 않는다.
암호·보안 확인 등 대화형 열기가 필요한 문서는 `DOCUMENT_OPEN_FAILED`로 중단한다.
닫을 때 저장하지 않고 사본 해시를 재검사한다. 변경 감지는 오류로 기록한다.

### 1.2 IPC wire v1

백엔드가 만든 상속 전용 stdin/stdout 파이프를 사용한다. 공개 TCP 포트는 열지 않는다.
UTF-8 JSON 한 줄당 한 메시지, 최대 64 KiB(개행 제외), stdout은 프로토콜 전용,
stderr는 크기 제한 로그다. 서비스가 양쪽 출력을 계속 소비하여 파이프 정체를 막는다.
줄 길이·깊이(16)·타입·메서드 허용목록을 검사한다. NaN/Infinity·중복 JSON 키는 거부한다.
난수 256비트 nonce는 첫 bootstrap 프레임으로 전달하고 명령행·로그에 남기지 않는다.
v/nonce/viewer_id 불일치는 즉시 연결 종료한다. 파이프 EOF도 종료 신호다.

```json
{"v":1,"id":"req-uuid","viewer_id":"viewer-uuid","method":"navigate","params":{"side":"left","page":3,"sync":true,"navigation_seq":12}}
```

| 방향/메서드 | params 또는 결과 | 규칙 |
|---|---|---|
| service→host bootstrap | nonce, viewer_id, parent_pid, left/right {path, sha256}, protocol=1 | 최초 1회; 복사 디렉터리 내부 실제 파일만 허용 |
| host→service ready | capabilities, left/right page_count, host_pid | 두 문서 읽기 전용 열기 성공 후만 발행 |
| service→host navigate | side=left/right, page(1부터), sync, navigation_seq | 페이지 범위 검사; STA 실행 뒤 실제 페이지 반환 |
| service→host scroll | side, page, fraction(0..1), sync, navigation_seq | 절대 위치; 상대 delta 누적 금지 |
| service→host set_sync | enabled(bool) | 기본 true |
| service→host focus | 빈 객체 | 기존 창 활성화; 새 호스트 생성 금지 |
| service→host heartbeat | 빈 객체 | 2초마다 전송; COM 큐 밖에서 응답 |
| service→host close | reason=user/main_exit/cancel | 멱등; 새 탐색 접수 중단 |
| host→service position | side, page, fraction, navigation_seq, origin=user/remote | 이벤트; remote 이벤트를 다시 전송하지 않음 |
| host→service closed | reason, copy_hashes_match | 정상 종료 알림 |

응답은 `{v,id,viewer_id,ok:true,result:{...}}` 또는
`{v,id,viewer_id,ok:false,error:{code,message,retryable}}`다. 이벤트는 id 없이
`{v,viewer_id,event,seq,data}`를 사용한다. seq는 호스트별 단조 증가한다.
서비스는 완료 응답을 id별 최근 256개 캐시하여 중복 요청의 부작용을 방지한다.
재사용 id의 본문이 다르면 `REQUEST_ID_REUSED`다. 재시작 호스트에 이전 요청을 재생하지 않는다.
정상 제어 응답 3초, 준비 20초, 문서 열기 15초 한도다. 타임아웃은 서비스 감시 스레드가
판정한다. COM이 멈춰도 메인 UI 호출은 즉시 접수 응답을 받고 상태를 비동기로 읽는다.

좌우 페이지 수가 다르면 같은 page를 상대편 마지막 page로 제한하고 `clamped:true`를
알린다. 스크롤은 동일 page 내 상대 비율로 맞춘다. 문단 의미 정렬을 보장하지 않는다.
입력 이벤트는 초당 최대 30회로 합치며 최신 navigation_seq만 적용한다. HwpCtrl에서
정밀 스크롤 조회/설정이 지원되지 않으면 ready의 `scroll_sync:false`로 알리고
페이지 동기화만 제공한다. 미지원 기능을 성공으로 응답하지 않는다.

### 1.3 수명 주기와 Process Guard

상태: `preparing → starting → opening → ready → closing → closed`.
어느 활성 상태에서든 오류면 `failed → closing → closed`다. 취소는 모든 단계에서 가능하다.
세션당 최대 1개, 앱 전체 최대 2개 뷰어를 허용하며 초과는 `VIEWER_LIMIT`이다.
같은 문서·결과·revision 재요청은 기존 창 focus로 처리한다.

서비스는 CREATE_SUSPENDED로 호스트를 생성하고 `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`
Job Object에 편입한 뒤 재개한다. 편입 실패 시 시작을 취소한다. job handle은
호스트에 상속하지 않는다. 앱 비정상 종료에도 job handle이 닫혀 자식이 종료된다.
별도 감시 스레드가 준비/명령 deadline을 감시한다. host는 부모 process handle 종료,
파이프 EOF, heartbeat 10초 누락 시 자가 종료한다. 부모 PID만 반복 조회하여
PID 재사용을 부모 생존으로 오인하지 않는다.

창 X/Alt+F4, Flutter 취소, 세션 닫기, 앱 종료는 모두 close 경로로 수렴한다.
호스트는 문서 close(저장 안 함) → OLE release → CoUninitialize → 프로세스 종료한다.
서비스는 정상 종료 최대 3초 후 전용 job을 종료하고 최대 2초 기다린 뒤 오류를 기록한다.
`taskkill /IM Hwp.exe`는 금지한다. OLE 서버가 job 밖에 생성되면 생성 시 확보한
전용 서버 handle/시작 시각·소유권 검증이 가능한 프로세스만 정리한다. 소유권을
입증할 수 없는 서버를 죽이지 않으며 해당 환경은 릴리즈 게이트 실패다.
사본 디렉터리는 프로세스 종료 확인 뒤에만 제거한다. 잠긴 파일은 다음 시작 시
해당 viewer_id의 실행 프로세스가 없음을 확인하고 재정리한다.

### 1.4 Flutter 결합

문서편집 탭의 결과 카드 → `DiffViewerController.open()` → `api('open_diff', payload)`.
즉시 `{ok:true,viewer_id,state:'preparing'}` 반환 후 상태 API
`diff_status(viewer_id,after_seq)`를 500ms 간격으로 조회한다(활성 다이얼로그만).
진행/실패/닫기/동기화 상태를 Flutter Dialog에 표시한다. OLE 화면은 독립 창에만 있다.
Dialog의 '뷰어 닫기'는 `diff_close`를 호출하고 closed 확인 뒤 dispose한다.
탭 전환은 뷰어를 닫지 않으며 컨트롤러는 셸 상위 문서 세션에 귀속된다.
문서 닫기·앱 종료는 컨트롤러의 비동기 closeAll을 시작하고 서비스가 최종 종료를 보장한다.
현재 `DIFF_BACKEND_NOT_READY`는 실제 호스트 게이트를 통과할 때까지 유지한다.

## 2. 캔버스 Command 스키마

공통 생성자: `(block_id, payload, *, after_id=None)`. 요청 브리지는
`{request_id,document_id,expected_revision,command_type,block_id,after_id,payload}`를 받는다.
command_type은 세 클래스 이름의 허용목록만 사용하며 동적 import는 금지한다.
after_id=null은 끝에 삽입, 문자열은 해당 블록 바로 뒤다. 없는/중복 anchor는 실패한다.
block_id는 문서 내 고유 1..128자 문자열이며 클라이언트가 UUID를 생성한다.
payload는 JSON, 최대 2 MiB, NaN/Infinity 금지다. 명령 생성 시 방어 복사한다.
파싱 오류는 브리지에서 `INVALID_COMMAND`로 정규화하며 예외 세부 경로는 UI에 노출하지 않는다.

```json
{"document":{"schema_version":1,"blocks":[{"id":"uuid","kind":"mindmap","source":{"root":{"id":"r","text":"제목"}},"content":{"target":"hp:p","mode":"outline","paragraphs":[{"id":"r","level":0,"number":"1","text":"제목"}]}}]}}
```

문서의 기존 다른 키와 미지원 블록은 보존한다. 캔버스 selection/zoom/scroll은 draft에 없다.
프로토타입 `canvas_commands.py`는 이 중간 표현(IR)까지 구현한다. `content.target`은
직렬화 대상 종류이며 유효한 완성 HWPX XML이라는 뜻이 아니다. XML·파일·COM 객체는
draft에 넣지 않는다. 패키지 저장 어댑터가 아래 규칙으로 실제 객체를 만든다.

| 클래스 | 입력 v1 | content 및 HWPX 변환 |
|---|---|---|
| InsertTableSketchCommand | 기존 grid {cols,rows,cell_mm}, lines, texts JSON | 기존 normalize/preview를 순수 호출; 손실 경고·빈 표 거부. layout의 row/col/span/borders/texts를 hp:tbl/tr/tc로 변환 |
| InsertDiagramShapeCommand | nodes [{id,type:rect/ellipse,position:{x,y},width,height,data:{label}}], edges [{id,source,target,label}] | shapes + connectors; hp:rect/ellipse, hp:connectLine. 최대 노드 1000·edge 2000, 중복 ID·없는 끝점 거부 |
| InsertMindmapTreeCommand | root {id,text,children:[]}, mode=outline/summary_table | 선행 순회 paragraphs {id,level,number,text}; outline은 hp:p, summary_table은 1행1열 hp:tbl 안에 모든 문단. 최대 1000노드·깊이 32 |

마인드맵은 입력 children 순서를 보존한다. 중복 ID/순환을 거부한다. outline v1은
`1`, `1.1`과 탭을 실제 텍스트로 기록하고 level별 문단 들여쓰기를 적용한다.
자동 번호 메타데이터가 아닌 고정 개요 번호다. summary_table은 같은 번호·글을 한 칸에 넣는다.
라벨은 최대 10000자이며 XML 금지 제어문자를 거부한다. escape는 serializer가 수행한다.
다이어그램 좌표는 96dpi CSS px, HWPUNIT 변환은 round(px * 7200 / 96)다.
정수/유한 실수 ±1000000, 크기는 양수다. connector는 source/target 중심을 잇는
직선 화살표로 내보내며 React Flow의 라우팅·곡선·사용자 CSS는 v1 미지원으로 명시한다.
지원하지 않는 node type은 오류로 거부하며 일반 사각형으로 조용히 바꾸지 않는다.

**hp:lineseg는 문단 조판 캐시이며 도형/화살표 저장용이 아니다.** 새 문단은 이 캐시를
만들지 않고 한/글 재열기 때 계산한다. HWPX exporter는 기존 패키지의 스타일·borderFill·
개체 ID를 전역 할당하고 참조를 재매핑한다. 표 변환은 `table_sketch.to_hwpx`의
셀 생성 로직을 순수 builder로 추출하여 재사용한다. 현재 to_hwpx는 파일을 쓰므로
Command 안에서 호출하면 안 된다. XML 파싱은 defusedxml만 사용한다.
표 셀 크기는 기존 grid 기반 HWPUNIT 계산을 그대로 사용하고 누적 좌표 차로 계산한다.
번호·그림 텍스트에는 기존 문서 스타일 참조를 복제해 사용한다.
serializer는 schema·참조·ZIP·내용 검증 후 새 출력에 원자 승격하고 원본은 쓰지 않는다.
도형/연결선의 정확한 필수 XML 속성은 한/글 2020 생성 fixture와 공식 스키마로 검증한
builder에서만 출력하며 IR target 문자열을 직접 태그로 이어 붙이지 않는다.

### 2.1 트랜잭션·이력

문서마다 기존 CommandBus 하나를 공유한다. 브리지가 document_id로 버스를 찾은 뒤
`execute(command,expected_revision=n)` 또는 `execute_batch`를 호출한다.
버스가 session RLock 안에서 revision을 검사하고 전체 사본을 만든다. 명령 실패 시
state/revision/dirty/undo/redo 모두 불변이다. batch는 한 이력으로 기록한다.
기존 `_Entry.before`와 `.after`는 각각 **전체 draft 딕셔너리**다. 별도의
`draft['before']`/`draft['after']` 키는 만들지 않는다. 경로는 양쪽 모두
`entry.before['document']['blocks']`, `entry.after['document']['blocks']`다.
첫 삽입 이전 document 키 부재도 Undo에서 정확히 복원한다.
실행·Undo·Redo마다 revision +1; Undo는 revision을 과거로 돌리지 않는다.
새 실행은 redo를 비우며 충돌은 `REVISION_CONFLICT`와 최신 revision을 돌려준다.
자동 재실행하지 않고 최신 문서와 anchor를 다시 확인한다. 입력 request_id 재전송은
브리지의 문서별 응답 캐시로 처리하며 command block_id 중복을 멱등 성공으로 취급하지 않는다.
한 번의 drag에서 미리보기는 로컬에 두고 확정 시에만 명령을 보낸다.
저장/내보내기는 snapshot의 revision을 사용하며 성공 뒤 동일 revision일 때만 mark_saved한다.

## 3. B01~B14 대체와 파일 수신 브리지

file_picker 선택은 Flutter Windows 네이티브 빌드에서는 OS 선택창을 직접 사용한다.
현재 Flutter web+WebView2 빌드에서는 file_picker 결과에 실제 Windows 경로가 없으므로
브라우저 File.name을 경로로 보내면 안 된다. 이 빌드는 Windows 호스트의 새
`NativeFileDialogService`(IFileOpenDialog/IFileSaveDialog, 별도 STA) 브리지를 사용한다.
Flutter `FileSelectionPort`가 두 빌드를 같은 API로 감싼다. 어떤 경로도 Tk 파일창을 호출하지 않는다.
file_picker 패키지 API는 고정한 pubspec 버전의 실제 Windows 구현을 확인하여 연결한다.
문서의 과거 `getSavePath()` 표기는 개념적 저장 위치 선택이며 실제 메서드명으로 간주하지 않는다.

| 항목 | Flutter/호스트 동작 | 백엔드의 명시적 입력 API |
|---|---|---|
| B01 add_files | 복수 문서 선택 | add_paths(paths) |
| B02 add_folder | 폴더 선택 | add_directory(selection_id, recursive=false) |
| B03 open_settings | SettingsDialog | get/save_settings |
| B04 text_input | Flutter 텍스트 입력 | 텍스트 변환 서비스, 원본 파일 선택 없음 |
| B05 open_stages | showStages | set_stage/reset_stages |
| B06 open_log | showLog/LiveProgress | 로그 조회/구독 |
| B07 flow PNG | 저장 위치 선택 | flow_export(format=png, output_selection_id) |
| B08 flow HWPX | 저장 위치 선택 | flow_export(format=hwpx, output_selection_id) |
| B09 idioms | 단일 상용구 파일 선택 | idioms(action=import, input_selection_id) |
| B10 table_template | 단일 학습 문서 선택 | table_template(action=learn, input_selection_id) |
| B11 add_format_file | 단일 예시 문서 선택 | add_format_paths(paths) |
| B12 write_format_example | Flutter 가이드 | write_format_example의 UI 독립 서비스 API |
| B13 edit_profile | ProfileEditor | format_profile(action,payload) |
| B14 run_tool(paste) | B04로 위임 | 삭제된 다른 tool은 UNKNOWN_TOOL |

B03~B06·B12~B14는 파일창이 아닌 화면 대체 항목이다. 모두 `front=True` UI 호출을
제거하지만 데이터 상태를 소유 스레드에서 읽는 `_tk` RPC 자체를 이 과제에서 없애지는 않는다.
파일/폴더 선택을 백엔드 데이터 작업과 분리한다. 경로가 없으면 선택창을 띄우던 기존
서비스 분기는 `FILE_SELECTION_REQUIRED`를 반환한다. Flutter 기본 경로의
ui_tk_fallback=true도 이 항목을 우회해 Tk 창을 띄우지 않도록 제거한다.

### 3.1 요청과 취소·오류

`select_files({request_id,purpose,mode:open/save/directory,multiple})`의 purpose는 위 표의
정적 허용목록이며 확장자 필터는 백엔드가 결정한다. 호스트는 즉시 selection job id를
반환하고 별도 STA에서 OS 창을 열어 메인 WebView2 루프를 막지 않는다.
완료는 `{ok:true,cancelled:false,selection_id,files:[{name,size}]}` 또는
`{ok:true,cancelled:true}`다. 취소는 문서·설정·이력을 바꾸지 않고 오류 알림도 만들지 않는다.
네이티브 file_picker 결과는 `register_selection({purpose,paths})`를 통해 같은 토큰을 받는다.
폴더/저장 결과도 토큰으로 통일한다. 토큰은 해당 앱 인스턴스·purpose에 묶고 5분 뒤
만료하며 한 작업에만 사용한다. 완료 응답 재전송은 request_id 캐시에서 반환한다.
경로는 호스트 메모리에 보관하며 임의 JavaScript file.name/URI를 파일 경로로 해석하지 않는다.

백엔드는 실제 파일 존재·확장자·형식·크기 한도·접근권한·canonical path와 파일 ID를 검사한다.
지원되지 않는 네트워크/장치 경로, ADS, 재분석 지점 우회는 거부한다. 폴더는 재귀 기본 끔,
파일 1000개 한도·중복 파일 ID 제거·안정 정렬 후 추가한다. 처리 중 취소와 부분 오류는
파일별 결과로 반환하며 자동 문서 실행은 하지 않는다. drop도 동일 검증 서비스로 통합한다.
저장 대상은 원본/열려 있는 세션 작업 사본과 동일 경로·hardlink ID이면 거부한다.
기존 출력 교체는 선택 UI의 명시적 overwrite 승인과 기존 파일 ID를 토큰에 기록하며,
승인 뒤 파일이 바뀌면 `OUTPUT_CHANGED`로 재선택한다. 임시 파일 검증 후 원자 교체한다.
실패 코드는 `INVALID_PATH`, `UNSUPPORTED_FORMAT`, `ACCESS_DENIED`, `SELECTION_EXPIRED`,
`SOURCE_CHANGED`, `OUTPUT_CHANGED`, `BUSY`이며 내부 경로를 포함하지 않는 한글 메시지를 준다.
input 파일은 사본/바이트 스냅샷을 서비스에 넘기고 사용자 원본을 수정하지 않는다.

## 4. 구현 순서·완료 판정

1. Gemini 3: 세 캔버스 JSON을 본 v1으로 변환, document_id/revision/anchor 연결.
   Codex의 순수 Command 프로토타입과 계약 시험을 기준으로 손실 입력을 명시적으로 거부한다.
2. Gemini 2: FileSelectionPort·Windows 호스트 선택 서비스·B01~B14 명시적 API 연결,
   DiffViewerController와 Flutter 상태/취소 UI 연결. 셸 State 보존 시험을 유지한다.
3. Codex 후속 구현: DiffHostService/STA OLE host/Process Guard 및 HWPX builder 검수.
   설계상 API 이름은 새 계약이며 현재 존재하는 메서드로 보고하지 않는다.
4. Gemini 1: COM 잠금 하에 사본으로 Windows 실측하고 Codex가 실패 로그를 검토한다.

필수 자동 시험: malformed/과대 IPC, nonce/version 불일치, 중복 요청, EOF, 준비·COM hang,
부모 강제 종료, 창 X/Alt+F4, 중복 close, 반복 열고 닫기 100회, PID 재사용 모의 시험;
좌우 페이지 수 차이·탐색 echo 방지·미지원 scroll; 파일 취소/한글 경로/폴더/권한/
확장자 위장/원본 alias/토큰 만료/overwrite 경쟁 및 Tk 창 호출 0회;
세 Command의 payload 방어복사·anchor·batch rollback·동일 revision 경합·Undo/Redo.
현재 신규 8개와 기존 세션 19개가 순수 모델 범위를 검증한다.

릴리즈 게이트: 한/글 2020에서 두 문서 읽기 전용, 실제 페이지 동기화, 원본·결과 hash 불변,
기존 사용자 Hwp 프로세스 유지, host/OLE 잔류 0, exporter 결과 재열기·글/표/도형 참조
보존 확인. COM 시험은 `C:\HWP_AUTODOCFIT\.com-test.lock`을 반드시 사용한다.
이 게이트 통과 전 T17/B 전환/serializer를 구현 완료나 2.0.0 배포 가능으로 표시하지 않는다.
