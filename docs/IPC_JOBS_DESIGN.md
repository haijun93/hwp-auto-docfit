# IPC 작업(job) 설계 — job_id·진행 이벤트·취소·오류 봉투

카드 IPCJOB. 기준: `release/2.2.30`(fd921bd). **설계 문서이며 코드는 바꾸지 않았다.**
TODO.md "소스코드 재구조화"의 "IPC 동기 호출에 job_id/취소/진행 이벤트를 설계…" 항목 중 **설계** 부분에 해당한다.
(같은 항목의 "Flutter 네이티브 UI에 실제 문서 처리 엔진을 연결한다"는 이 설계의 6단계이며 아직 하지 않았다.)

관련 기존 문서: `docs/V2_JOB_PROTOCOL.md`(JobManager 규약, 이 문서는 그 위에 얹는다),
`docs/FLUTTER_IPC_PROTOCOL.md`(전송 규약 v1), `docs/FLUTTER_API_CONTRACT.md`(서비스 응답 `api_version/ok/data/error`),
`docs/CODE_RESTRUCTURING_REVIEW_ALPHA6_2026-10-13.md`(P0: "native IPC는 요청을 `ApplicationService.lock` 안에서 동기 실행").

---

## 0. 결론 먼저

1. **작업 관리자는 이미 있다.** `docfit_app/jobs.py`의 `JobManager`가 job_id(UUID4)·상태(`queued→running→done|failed|cancelled`)·
   사건 스트림(`events(after_seq,max)`)·협력적 취소(`cancel`)·10초 뒤 소유 한/글 정리(`_timeout`→`kill_owned`)를 갖췄다.
   새 관리자를 만들지 않는다. **빠진 것은 ① 전송층이 긴 호출에 막히지 않게 하는 일 ② 느린 서비스 호출을 JobManager에 편입하는 일
   ③ Flutter(Dart)가 job을 소비하는 일**이다.
2. **오늘 실제로 막히는 지점**(코드로 확인, 4절): 네이티브 IPC가 `ApplicationService.lock` 안에서 `dispatch`를 실행하므로 한 동기 호출이 도는 동안
   `get_events`·`cancel_job`도 기다린다. 같은 연결은 요청을 한 줄씩 직렬 처리한다. Dart 클라이언트는 호출마다 20초 타임아웃이다.
   임시 스크립트로 측정: 3.0초짜리 가짜 동기 호출 중 다른 연결의 `get_events`가 **2.70초** 걸렸다(8절 "측정").
3. **기존 응답 봉투는 바꾸지 않는다.** 새 메서드(`job_status` 등)와 새 `kind`만 더하고, 기존 동기 메서드는 이관이 끝나도 한 릴리스 이상 병존시킨다.
4. **이관 순서(위험 낮은 것부터)**: P1 전송층 분리 → P2 Dart 소비자 → P3 이미 자체 start/poll인 기능을 JobManager에 편입 →
   P4 파일 IO만 하는 동기 호출 → P5 COM 쓰는 동기 호출 → P6 문서 처리 엔진. 5절.

---

## 1. 두 가지 백엔드 경로 (같은 JobManager, 다른 전송)

| 경로 | 진입 | 전송 | 비고 |
|---|---|---|---|
| 네이티브(독립 Python 백엔드) | `docfit_app/backend_main.py:main` → `IpcServer`(`docfit_app/ipc_server.py`) → `ApplicationService.dispatch`(`docfit_app/application_service.py`) | 127.0.0.1 임시 포트 TCP, 한 줄 JSON, 토큰, 최대 1 MiB(`MAX_MESSAGE`), 연결 8개(`BoundedSemaphore(8)`) | Dart `flutter_ui/lib/core/ipc/native_client.dart:NativeClient`. 문서 처리 엔진 미연결(`engine_ready=False`), `start_job`은 `file_format`·`table_copy`만 |
| WebView(데스크톱 앱) | `desktop_web_ui.py:_BrowserApi` → `DesktopWebBridge` 메서드 → `_tk(callback, timeout=120)`로 Tk 스레드에 위임 | pywebview `docfitCall`(`flutter_ui/lib/bridge_web.dart`) | 문서 처리는 Tk 레거시 worker(`docfit_ui/legacy.py:작업시작`·`파일포맷_변경_시작`)가 하며 `JobManager`에 `begin`/`attach`로 등록 |

`flutter_ui/lib/bridge.dart`가 조건부 export로 고른다(웹 빌드 `bridge_web.dart`=WebView, `dart:io` 빌드 `bridge_native.dart`=`NativeClient.call`).
**두 경로가 같은 이벤트 규약을 공유해야 한다**: `JobManager`가 공통이므로 규약 변경은 `jobs.py`와 두 어댑터(`application_service.py`의 `get_events`/`cancel_job`/`start_job`,
`desktop_web_ui.py`의 같은 이름 메서드)에서만 한다.

## 2. 이미 있는 작업 관리와의 관계

### 2.1 `docfit_app/jobs.py`의 `JobManager`

| 요소 | 위치 | 내용 |
|---|---|---|
| 작업 종류 | `LIGHT_KINDS = {'inspect','preview','catalog'}` | 그 밖의 종류는 문서 슬롯 1개를 공유 — 동시에 실행 중이면 `begin`이 `JOB_RUNNING`으로 거부(대기열 없음) |
| 발급 | `begin(kind, params, stop_event=None)` | `uuid.uuid4()` 문자열이 `id`이자 `job_id`. 상태 `queued` |
| 비동기 실행 | `start(kind, params, runner, job_id=None)` | 데몬 스레드에서 `runner(report, cancelled)` 실행, 정상 반환 `done`/취소 `cancelled`/예외 `failed`(`code=getattr(exc,'code','JOB_FAILED')`) |
| 동기 실행 | `run_inline(kind, params, runner)` | 호출자 스레드에서 실행하되 같은 슬롯·사건을 쓴다. **응답은 여전히 호출이 끝나야 돌아온다**(네이티브 `table_units copy`가 이 방식, `application_service.py` `run_inline('table_copy', …)`) |
| 레거시 편입 | `attach`, `prepare_legacy`, `legacy_event`, `manager_for` | Tk worker가 `gui_queue`에 넣는 튜플(`doc_begin`·`step`·`progress`·`saved`·`document_error`·`finished`·`stopped`·`fatal_error`·`log`·`style_unify_*_review`)을 사건으로 변환. 호출 지점: `docfit_ui/legacy.py`(4621~4643, 4686~4688, 5486~5488) |
| 사건 | `report(id,type,data)`, `events(after_seq,max)` | type: `started progress item_done item_failed log dialog done failed cancelled`. `seq`는 프로세스 수명 전체에서 증가, 링 버퍼 2,000건(`capacity`), `gap`/`oldest_seq`/`next_seq`/`latest_seq` |
| 취소 | `cancel(id)`, `cancelled(id)` | `cancel_requested=true`+`stop` Event. 종료는 runner가 안전 지점에서 확인하고 돌아올 때. `cancel_timeout=10`초 뒤 `_timeout`→`docfit_core.hwp_process.kill_owned`(앱이 띄운 한/글 PID만) |
| 종료 | `shutdown(timeout=10)` | 새 작업 거부(`BACKEND_CLOSING`), 전부 취소, worker 대기, 소유 한/글 정리 |
| 고아 복구 | `_recover`/`_persist` | `native-jobs.json`/`desktop-jobs.json`에 활성 작업 ID·종류만 기록, 재시작 시 `ORPHANED_JOB` failed로 회수 |

### 2.2 현재 노출 상태 (확인함)

- 네이티브 `ApplicationService.dispatch`의 허용 목록에 `start_job`(2인자)·`cancel_job`(1)·`get_events`(1)가 있고, `get_state().job`이 최근 작업 하나의 `id/job_id/kind/state/progress/cancel_requested`를 준다.
  **개별 작업 조회(`status(job_id)`)는 IPC로 노출돼 있지 않다**(`JobManager.status`는 내부용).
- WebView `_BrowserApi` 허용 목록(`desktop_web_ui.py`, "start_job","cancel_job","get_events")에도 같은 세 메서드가 있다. 기존 `start`/`stop`은 이 위의 얇은 래퍼(`start`→`start_job`, `stop`→`cancel_job`).
- **Dart는 이 세 메서드를 전혀 호출하지 않는다**(`flutter_ui/lib`에 `start_job`·`cancel_job`·`get_events` 문자열 없음). 화면은 `main.dart`의 1초 주기 `get_state` 폴링과 기존 `start`/`stop`을 쓴다.
  즉 job 규약은 Python 쪽에서만 구현·시험(`tests/test_jobs.py` 17건)돼 있고 소비자가 없다.

### 2.3 JobManager 밖에서 따로 만든 "시작·상태·취소" 패턴 (3가지 변종)

같은 문제를 기능마다 다시 풀었다. 이것들을 통합하는 것이 P3다.

| 기능 | 위치 | 시작/상태/취소 | 상태 모양 |
|---|---|---|---|
| HWP→HWPX 일괄 | `desktop_web_ui.py:hwp_bulk`(1827), `docfit_core/hwp_bulk.py:run_bulk`·`BulkState` | `start`/`status`/`stop`(별도 스레드 `hwp-bulk`, `threading.Event`) | `BulkState.as_dict()` |
| 자료함 폴더 스캔 | `docfit_app/library_scan.py:FolderScanService.handle`(`box_scan`/`box_scan_status`/`box_scan_cancel`) | klib 또는 Python 폴백 스레드 | `idle|scanning|done|cancelled|error` |
| 타임머신 스캔·본문 색인 | `docfit_app/timemachine_service.py:_start_scan`(397)·`_start_content_index`(146)·`cancel_content_index`(165) | `scan`/`content_index_start`/`content_index_status`/`content_index_cancel` | `_content_state` dict |

## 3. 오래 걸리는 호출 목록 (코드에서 확인)

분류: **J** = 이미 JobManager 사건 사용, **P** = 자체 start/poll(JobManager 밖), **S** = 응답이 끝나야 돌아오는 동기 호출(전송층을 점유).
"경로"는 N=네이티브 IPC, W=WebView. 소요 시간은 측정하지 않았다(아래 "길어지는 이유"는 코드상 근거).

| # | 호출 | 위치 | 길어지는 이유 | 경로 | 분류 | 취소 지점 |
|---|---|---|---|---|---|---|
| 1 | `start`/`start_job` `format\|spacing\|unify\|all\|pagefit` | `desktop_web_ui.py:_start_legacy`→`docfit_ui/legacy.py:작업시작` | 한/글 COM 문서 처리 | W | J | `중단_event`, 파일 사이·저장 전 |
| 2 | `start_job('file_format')`, `start_single_file_conversion` | `docfit_app/conversion_runner.py:start_conversion_job`/`run_conversion`, `desktop_web_ui.py:_start_single_conversion_snapshot` | COM PDF/그림/HWPX 변환, pandoc, OCR | N·W | J | `stop_event` 파일 단위 |
| 3 | `start_job('table_copy')` | W: `desktop_web_ui.py:_table_copy_job`, N: `TableUnitsService.start_copy_job` | 숨긴 한/글 Open→Copy→Quit | N·W | J | 시작 전만 |
| 4 | `table_units('copy', …)` (Dart `table_units_api.dart` `copy`가 이 경로를 호출) | `application_service.py` `run_inline('table_copy')` | 위와 같음, **응답을 기다림** | N | S(+J 사건) | 시작 전만 |
| 5 | `table_units('preview'\|'thumbnails')` | `docfit_app/table_units_service.py:command`·`thumbnails` | 한/글 PDF→표 부분 PNG 스냅샷 생성(캐시 미스 시) | N·W | S | 없음 |
| 6 | `hwp_bulk('start')` | 2.3 | 드라이브 전체 스캔+한/글 변환 | W | P | `stop` |
| 7 | 자료함 폴더 스캔 `box_scan` | 2.3 | 폴더 순회+색인 | W | P | `box_scan_cancel` |
| 8 | 자료함 `library('index')` | `docfit_app/library_service.py:command`(217)→`index`(63). `index`는 `cancel`·`progress` 인자를 받지만 `command`가 넘기지 않는다 | 등록 폴더 전체 순회·색인 | N | S | 인자는 있으나 미연결 |
| 9 | 타임머신 `scan`·`content_index_start` | 2.3 | `os.walk` 전체, 본문 추출 | N·W | P | `content_index_cancel`(스캔은 `restart`) |
| 10 | 타임머신 `thumbnails`/`thumbnail(id)` | `timemachine_service.py` `THUMBNAIL_TIME_LIMIT = 5.0` 후 `worker.join` | 별도 프로세스 썸네일, 최대 5초 대기 | N·W | S | 5초 한도 |
| 11 | 타임머신 `content_index`(1건)·`content_search` | `timemachine_service.py:_command` | 한 문서 추출 / SQLite 검색 | N·W | S | 없음 |
| 12 | `file_rename('preview'\|'apply'\|'undo')` | `docfit_app/file_rename_service.py:preview`(216)·`apply`(237)·`undo`(258) | 파일 수만큼 이름 변경 | N·W | S | 없음 |
| 13 | `file_rename('add_paths'\|'pick_folder', recursive)` | `file_rename_service.py`(`os.walk`, 138행 부근), `native_file_dialog_service.py`(161행 부근) | 폴더 재귀 순회(항목 수 상한 `MAX_ENTRIES = 10000`은 있음) | N·W | S | 없음 |
| 14 | `table_sketch('copy'\|'paste_hwp'\|'import_hwpx_table'\|'recognize'\|'import_image')` | `docfit_app/table_sketch_service.py:command`(258) | 숨긴 한/글, 클립보드 대기 루프(`time.sleep(0.05)`) | N·W | S | 없음 |
| 15 | `kclip('copy_no_shade')`, `excel_table('strip_shading')` | `kclip_service.py:command`(188), `excel_table_service.py` | 클립보드 변환·재기록(짧음) | N·W | S | 없음 |
| 16 | `flow_editor('catalog_copy'\|'copy_diagram_shapes'\|'export_png'\|'export_hwpx'\|'copy_result')` | `application_service.py:dispatch`→`FlowService`·`clipboard_service` | HWPX 생성·클립보드 | N·W | S | 없음 |
| 17 | `document_tool(...)` | `document_tools_service.py:command` | 문서 도구 | N·W | S | 없음 |
| 18 | `new_document('create'\|'blank')` | `desktop_web_ui.py:new_document`(1993) | 한/글 실행·문서 열기 | W | S | 없음 |
| 19 | `inspect_document(path)` | `application_service.py`→`docfit_core.hwpx.validate_and_inspect_hwpx` | ZIP/XML 검증(큰 문서) | N | S | 없음 |
| 20 | `check_update`/`start_update` | `desktop_web_ui.py`→`docfit_app/update_service.py` | 네트워크(`http_get` 타임아웃 규칙) | W | S/P | 없음 |
| 21 | `compare_result`/`open_diff` | `docfit_app/diff_host_service.py`(자체 스레드·프로세스) | 별도 뷰어 프로세스 | W | P | 서비스 자체 |

경량이라 이 설계의 대상이 아닌 것: `get_state`, 설정·준말 CRUD, `set_*`, `add_paths`(문서 목록 추가, 최대 1,000개), `handshake`.

**관찰**: S 분류 중 COM을 쓰는 것(4·5·14·18)은 한/글이 응답하지 않으면 무기한 걸릴 수 있으나 Dart는 20초에서 포기한다(4.3절). 파일 IO만 하는 것(8·12·13)은 대량 입력에서만 길어진다.

---

## 4. 현재 구조의 한계 (코드로 확인한 사실)

1. **전역 잠금 안의 동기 실행** — `docfit_app/ipc_server.py:IpcHandler.handle`(67행)이 `with self.server.app.lock:` 안에서 `dispatch`를 부른다.
   `ApplicationService.lock`은 `RLock` 하나이므로 어떤 연결의 동기 호출이든 도는 동안 다른 연결의 `get_events`·`cancel_job`·`get_state`도 대기한다. 작업을 취소하려는 요청이 취소 대상 호출 뒤에 줄을 선다.
2. **연결 하나는 직렬** — 같은 연결에서는 응답을 쓴 뒤에야 다음 줄을 읽는다. Dart는 소켓 하나(`NativeClient.socket`)만 쓴다.
3. **클라이언트 타임아웃은 요청 취소가 아니다** — `native_client.dart` 154행 `waiter.future.timeout(Duration(seconds: 20))`은 대기만 포기한다. 백엔드는 계속 실행하고 늦게 온 응답은 `pending`에 없어 버려진다.
   쓰기 작업이면 사용자는 결과를 모른 채 재시도할 수 있다("쓰기는 자동 재시도하지 않는다" 규칙은 있으나 화면은 오류만 본다).
4. **서버의 유휴 읽기 타임아웃 30초** — `IpcHandler.handle` 41행 `settimeout(30)`. 30초 동안 요청이 없으면 서버가 연결을 닫고, Dart `disconnected()`는 **백엔드 프로세스를 kill**한다. 화면이 1초 주기 `get_state`를 보내는 동안은 문제 없지만, job 폴링을 도입할 때도 "활성 job이 없어도 주기 호출이 있다"는 가정에 의존한다(유지하거나 `ping`을 명시).
5. **WebView 경로의 `_tk` 120초 한도** — `desktop_web_ui.py:_tk(callback, timeout=120)`. 시간 초과는 미실행 요청만 취소한다(`FLUTTER_API_CONTRACT.md`).
6. **오류 봉투가 세 겹이고 일부는 코드가 사라진다**
   - 전송 봉투(`ipc_server.py`): `{protocol_version, request_id, success, result | error{code,message,recoverable}}`
   - 서비스 봉투(`api_contract.py:response`): `{api_version, ok, data, error{code,message,recoverable}}` — 일부 서비스만
   - 임의 모양: `{'ok':False,'message':…}`(`application_service.py`의 `table_sketch`/`excel_table` 작업 중 거부, `excel_table_service.py`), `{"ok": False, "code": …, "message": …}`(`desktop_web_ui.py:library`)
   - `ServiceError`가 아닌 예외는 전송 봉투에서 `BACKEND_ERROR`(고정 메시지)로 뭉개진다. `ValueError/TypeError/IndexError/KeyError`는 `INVALID_INPUT`.
   - 사건의 `failed`는 `{code,message}`만 있고 `recoverable`이 없다(`jobs.py:start`·`run_inline`).
7. **메시지 1 MiB 한도** — 결과가 크면 `MESSAGE_LIMIT`. 사건의 `data`도 같은 한 줄에 실려 오므로 `done.data.result`에 큰 값을 싣는 설계는 쓸 수 없다.
8. **사건 보관은 메모리 2,000건** — 느린 소비자는 `gap=true`를 받고 `get_state`로 요약을 다시 읽어야 한다(`V2_JOB_PROTOCOL.md`). 완료 이력은 재시작 후 없다.
9. **`backend_version` 엄격 비교** — Dart가 `'1.74 Native Prototype 1'` 문자열을 정확히 비교한다(`native_client.dart` 54·88행). 이관 중 이 문자열을 바꾸면 연결이 거부되므로 **기능 감지는 `handshake.capabilities`로 하고 버전 문자열은 건드리지 않는다.**

---

## 5. 설계

### 5.1 원칙

- **JobManager 재사용·확장, 병렬 구현 금지.** 사건 `type` 집합과 `seq`/`gap` 규칙은 유지한다(필드는 추가만, 제거·의미 변경 금지).
- **기존 메서드·봉투 불변.** 새 기능은 새 메서드·새 `kind`·새 선택 필드로 더한다. 클라이언트는 `handshake.capabilities`에 `jobs.v1`이 있을 때만 새 경로를 쓰고, 없으면 기존 동기 호출로 돌아간다(기능 플래그 겸 롤백 경로).
- **폴링 유지, 푸시 도입 안 함.** IPC v1은 요청-응답 한 줄이다. 서버 푸시는 프로토콜 v2가 필요하고 Dart 수신부(`receive`가 `request_id`로만 분기) 재작성이 따른다. `V2_JOB_PROTOCOL.md`의 "긴 폴링 없이 즉시 배치"도 유지한다.
- **정확성 우선.** 취소·속도 때문에 원본 무결성 검사·최종 검수를 생략하지 않는다(`TODO.md` "피할 것" 항목과 동일).
- **COM은 job 하나가 한 스레드에서 소유**(`CoInitialize`/`CoUninitialize` 쌍은 `start_copy_job` 방식). 호출자 스레드(연결 핸들러)에서 COM을 쓰지 않는다.

### 5.2 job_id

- 발급은 기존 `JobManager.begin`의 `uuid.uuid4()`를 그대로 쓴다. `start_job`의 반환값이 job_id 문자열(기존과 동일).
- **`request_id`와 `job_id`는 다르다**: `request_id`(전송, 1~128자, 연결당 최근 4,096개 중복 거절)는 한 번의 왕복을 식별하고, `job_id`는 작업 수명을 식별한다. 재연결·재시작 후에는 `request_id` 기록이 사라진다.
- 재시작하면 job도 사라진다(`ORPHANED_JOB`). Dart는 연결이 끊기면 백엔드를 kill하므로(`disconnected`) 재연결 = 새 백엔드이며 이어받을 job이 없다. 따라서 `start_job` 멱등키(`client_request_id`)는 **지금은 도입하지 않는다**(열린 질문 3).
- 신규: **`job_status(job_id)`** — `JobManager.status`를 노출하고, 종료 상태이면 `result`(직렬화 256 KiB 이하일 때만, 아니면 `result_ref`)를 더한다. 사건 링 버퍼에서 종료 사건이 밀려나도 결과를 읽을 수 있게 하는 안전망이다.

### 5.3 호출 형태 (기존 호환)

```text
start_job(kind, params)  → job_id (문자열)              # 기존, 변경 없음. 즉시 반환
cancel_job(job_id)       → status 스냅샷                # 기존, 변경 없음. 즉시 반환
get_events(after_seq)    → {events,next_seq,latest_seq,oldest_seq,gap}   # 기존
job_status(job_id)       → status 스냅샷 + (종료 시) result   # 신규
```

`kind` 규칙: 기존 `format spacing unify all file_format table_copy pagefit inspect preview catalog`에 이관 단계별로 추가한다
(예: `file_rename_apply`, `library_index`, `table_sketch_copy`). 이름은 "기능_동작" 소문자 스네이크. `kind` 등록부(5.6)에 없으면 `NOT_AVAILABLE`.

### 5.4 진행 이벤트

사건 봉투는 기존 그대로(`V2_JOB_PROTOCOL.md`): `{seq, job_id, type, at, data}`. `data`의 **선택 필드만 추가**한다.

| type | 기존 data | 추가 선택 필드 |
|---|---|---|
| `progress` | `file`,`total`,`stage`,`percent`(0~100), 변환 시 `name` | `indeterminate: bool`(총량 미상 — 스캔 등, true면 `percent` 무시), `processed`,`discovered`(스캔 계열 개수), `detail`(짧은 사람이 읽는 문구, 문서 본문·경로 전체 금지) |
| `item_done` | `source`,`output` 등 | `index`(0부터 항목 번호) |
| `item_failed` | `source`,`message` | `code`(5.5의 코드), `recoverable` |
| `done` | `result`, 또는 `success`,`failed` 개수 | — |
| `failed` | `code`,`message` | `recoverable`(5.5) |
| `cancelled` | `{}` | `partial`: `{success,failed}`(취소 전까지 처리된 개수) |

규칙: ① 한 job의 `progress.percent`는 가능하면 단조 증가(`V2_JOB_PROTOCOL.md`는 재시도 시 되돌아갈 수 있다고 허용 — 유지). ② 보고 빈도 상한: runner는 초당 10건을 넘기지 않는다(링 버퍼 2,000건을 한 job이 채워 다른 job 사건을 밀어내는 일 방지; 합치기는 `JobManager.report`가 아닌 runner 어댑터에서). ③ 소비자는 `seq`로 중복 제거.

**소비 방식(Dart)**: 활성 job이 있으면 250~500 ms, 없으면 기존 1초 `get_state` 주기와 합친다. `gap=true`면 `get_state`/`job_status`로 재동기화. 폴링이 서버 유휴 타임아웃(4.4)도 해소한다.

### 5.5 오류 봉투

세 계층은 **유지**하고, 새로 생기는 곳(job 사건·`job_status`)만 한 가지 모양으로 통일한다.

**JobError** (JSON Schema, `failed.data`·`item_failed.data`·`job_status.error`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "docfit/job-error.v1",
  "type": "object",
  "required": ["code", "message"],
  "additionalProperties": true,
  "properties": {
    "code": {"type": "string", "pattern": "^[A-Z][A-Z0-9_]{1,47}$"},
    "message": {"type": "string", "maxLength": 500},
    "recoverable": {"type": "boolean", "default": true},
    "source": {"type": "string", "description": "항목 오류일 때 원본 파일 경로(item_failed)"}
  }
}
```

**매핑 규칙(어댑터 한 곳에서)**:

| 입력 | JobError |
|---|---|
| `ServiceError(code,msg,recoverable)` | 그대로 |
| 서비스 임의 모양 `{'ok':False,'message':m}` / `{ok:False,error:{code,message}}` | runner 안에서 `ServiceError`로 변환 후 위 규칙. 선례: `desktop_web_ui.py:_table_copy_job` |
| `ValueError` 등 입력 오류 | `INVALID_INPUT`, `recoverable=true` |
| 그 밖의 예외 | `JOB_FAILED`, 메시지는 `str(exc)`를 500자로 자르되 문서 본문·암호는 담지 않는다 |
| 취소 요청 뒤 어떤 결과든 | `cancelled`(오류 아님) |

코드표는 `V2_JOB_PROTOCOL.md`의 표를 그대로 쓰고 필요하면 추가만 한다(`JOB_RUNNING`, `JOB_NOT_FOUND`, `JOB_INTERRUPTED`, `ORPHANED_JOB`, `CANCEL_TIMEOUT`, `CLEANUP_FAILED`, `NOT_AVAILABLE`, `HWP_FAILED`, `CLIPBOARD_FAILED`, `INVALID_INPUT`, `BACKEND_CLOSING`). 신규 후보: `RESULT_TOO_LARGE`(5.7).
**시작 자체의 거절**(`start_job`에서 즉시 검증 실패)은 지금처럼 전송 봉투의 `error`로 돌려준다 — job이 만들어지지 않았기 때문이다. job이 만들어진 뒤의 오류는 사건·`job_status`로만 전달한다.

### 5.6 kind 등록부 (신규, `docfit_app/jobs.py` 안의 표)

지금은 `LIGHT_KINDS` 집합 하나다. 이관하려면 종류별 성질이 필요하다.

```text
KIND = {
  name:        str,
  exclusive:   bool,   # True면 문서 슬롯 1개를 공유(현 non-light 규칙)
  singleton:   bool,   # 같은 kind는 동시에 하나(스캔·색인용; exclusive=False여도 적용) → 위반 시 JOB_RUNNING
  com:         bool,   # 한/글 COM 사용 → runner 스레드가 CoInitialize/Quit 소유, 취소 시 kill_owned 대상
  cancel:      'cooperative' | 'none',   # none이면 cancel_job은 JOB_NOT_CANCELLABLE 로그 + 종료 대기
  result_max:  int,    # job_status.result 직렬화 한도(기본 262144)
}
```

`begin`의 충돌 판정이 `kind not in LIGHT_KINDS`에서 등록부 조회로 바뀐다. 기존 kind의 값은 현 동작과 같게 채운다(회귀 시험으로 고정).

### 5.7 큰 결과·취소 의미

- 결과가 `result_max`를 넘으면 runner는 파일로 쓰고(앱 설정 폴더 하위 staging) `result_ref`(경로 아님, 서버가 아는 토큰)만 `done`에 싣는다. 경로·이동 검증은 기존 파일 선택 서비스 규칙(`..`·UNC·심볼릭 링크 거부)을 재사용한다. P4 이후 필요해질 때 구현한다.
- **취소 의미**: 협력적. runner는 원본이 안전한 지점(파일 사이, 저장 직전, 순회 항목 사이)에서만 `cancelled()`를 확인한다. 취소 시 ① 원본 불변 ② 이미 완성돼 `item_done`으로 보고된 출력은 유지 ③ 미완성 임시 파일은 runner의 `finally`에서 삭제 ④ `cancelled.data.partial`로 개수 보고. COM 호출 중에는 강제 중단하지 않고 호출 복귀를 기다리며, 10초 초과 시 기존 `kill_owned`(소유 PID만)만 쓴다. 이미지 이름으로 `taskkill` 금지 규칙 유지.
- 동기 호출을 **그대로 두는 것**의 취소: 불가. 그래서 취소가 필요한 기능은 반드시 job으로 옮긴다(`cancel: 'none'`은 짧은 호출용 표식).

### 5.8 전송층 변경 (P1의 내용)

1. **제어 메서드는 `app.lock` 밖에서 처리한다.** `IpcHandler.handle`에서 `method in CONTROL = {'get_events','cancel_job','job_status','handshake'}`이면 잠금 없이 `dispatch`. 이 메서드들은 `JobManager`의 자체 `RLock`만 만진다(`application_service.py`의 `get_events`·`cancel_job`이 `self.jobs.*`만 호출함을 확인). `shutdown`·`get_state`는 상태를 읽고 쓰므로 잠금 유지.
2. **긴 호출을 job으로 바꾸면 2번(연결 직렬)은 자연히 해소**된다 — `start_job`이 즉시 반환하기 때문. 이관 전 과도기에 동기 호출 중 `cancel_job`이 필요하면 Dart에 제어용 두 번째 연결을 두는 안은 보류(열린 질문 1; 서버는 이미 연결 8개를 받는다).
3. `handshake.capabilities`에 `'jobs.v1'` 추가(문자열 추가만; Dart는 `protocol_version`·`backend_version`만 검사하므로 호환).
4. 처리 시간 계측: 핸들러가 `method`·소요 ms만 로그(입력·결과 본문 금지). 이관 전후 비교용 기준선.

---

## 6. 단계적 이관 순서 (위험 낮은 것부터)

각 단계는 독립 카드·독립 롤백이 가능해야 한다. "롤백" = 클라이언트가 `jobs.v1` 미탐지로 기존 호출 사용, 또는 서버의 해당 kind 등록 제거.

| 단계 | 내용 | 대상 호출(3절 #) | 위험 | 롤백 | 완료 조건 |
|---|---|---|---|---|---|
| P1 | 전송층: CONTROL 메서드 잠금 밖, `job_status`, `jobs.v1`, 소요 로그 | — | 낮음(JobManager 접근만 잠금 밖으로) | 한 줄 되돌림 | 느린 가짜 동기 호출 중 `get_events` 지연 100 ms 미만(현재 2.70 s) |
| P2 | Dart `JobClient`(시작·폴링·취소·`gap` 재동기화) + 이미 job인 `file_format`·`table_copy` 화면 연결 | 2, 3 | 낮음 — Python은 이미 구현·시험됨, UI만 신규 | 기능 플래그로 기존 `start`/`stop` | 네이티브에서 파일 변환 진행률·취소가 화면에 보임 |
| P2b | 네이티브 `table_units('copy')` 동기→`start_job('table_copy')` 호출로 전환(Dart `table_units_api.dart:copy`) | 4 | 낮음 — 20초 타임아웃 문제 해소 | 동기 호출 유지 | 20초 넘는 복사도 성공 표시 |
| P3 | 자체 start/poll 기능을 JobManager에 어댑터로 편입(내부 동작·기존 메서드 불변, 사건만 추가 발행). 타임머신 스캔/색인 → 자료함 스캔 → `hwp_bulk` | 6, 7, 9 | 낮음~중 — 이미 비동기이며 겉모양만 통일. `singleton`·`exclusive=False` 등록 | 어댑터 제거 | 기존 상태 API와 job 사건의 수치 일치 |
| P4 | 파일 IO만 하는 동기 호출: `library_index`(이미 있는 `cancel`/`progress` 인자 연결), `file_rename_apply`/`undo`, 재귀 `add_paths` | 8, 12, 13 | 중 — 되돌리기·원본 보존 시험 필요 | 기존 동기 경로 병존 | 취소 후 원본·이력 일관 |
| P5 | COM 쓰는 동기 호출: `table_sketch_*`, `table_units` preview/thumbnails, `new_document`, `flow_editor` 복사 | 5, 14, 16, 18 | 중~높음 — COM 스레드 소유·`kill_owned` 경로 | 기존 동기 경로 병존 | Windows 실기 COM 시험 통과 |
| P6 | 문서 처리 엔진(`format spacing unify all pagefit`)을 네이티브에 연결 — 현재 `application_service.py:start_job`은 `NOT_AVAILABLE` | 1 | 높음 — 엔진 분리(`hwp-auto-docfit.py`)와 같은 시기, COM 정확도 회귀 우선 | WebView 경로 유지 | 서식 충실도 기준(`scripts/format_fidelity_pc.py`) 불일치 0 |

비대상: 3절 #10·11·15·17·19·20은 짧거나 한도가 있어 job화 이득이 작다. 입력이 커지는 것이 확인되면(`inspect_document` 등) 그때 P4 방식으로 추가한다.

**WebView 경로**: #1·2·3은 이미 job이다. P2의 Dart `JobClient`는 `bridge.dart`를 통해 두 경로 모두에서 같은 코드로 동작하도록 만든다(WebView `start_job`/`get_events`/`cancel_job`은 이미 있음).

## 7. 시험 전략

원칙: **한/글·원본 문서 없이 돌 수 있는 시험을 먼저**, COM은 Windows 수동 시험으로 분리. 기존 시험의 기대값을 바꿔 통과시키지 않는다.

| 층 | 시험 | 기존 → 추가 |
|---|---|---|
| JobManager 단위 | 등록부 충돌 판정, `singleton`, `result_max`, 오류 매핑, 사건 스키마 | `tests/test_jobs.py`(17건) 확장. 기존 kind의 동작이 등록부 도입 전과 같음을 먼저 고정 |
| 전송 | 느린 가짜 `dispatch` 중 `get_events`/`cancel_job` 지연, 같은 연결 직렬, 취소→종료 사건, 연결 끊김→재시작 후 `ORPHANED_JOB`, `request_id` 재사용 거절 | `tests/test_native_ipc.py`(실제 서브프로세스) 확장 |
| 계약 | 발행되는 모든 사건을 5.4·5.5의 스키마로 검사(검증기는 새 의존성 없이 손으로 작성; `jsonschema`는 `requirements-mcp.txt`에만 있어 앱 필수 의존성이 아님). 대표 사건 골든 JSON | 신규 `tests/test_job_events_contract.py` |
| 호환 | 기존 동기 메서드(`table_units copy` 등)의 응답이 이관 전후 동일, `start`/`stop`/`get_state` 응답 형태 불변 | 이관 PR마다 스냅샷 |
| 소비자(Dart) | 가짜 소켓 서버로 `JobClient`: 폴링 주기, `gap` 재동기화, 중복 `seq`, 취소, 타임아웃이 job을 취소하지 않음 | `flutter_ui/test` 신규 |
| 성능 | 활성 job 중 `get_events` p95, 유휴 폴링 CPU, 사건 2,000건 초과 시 `gap` | 이관 전후 같은 PC 비교(추정 금지, 측정값만 기재) |
| Windows 실기 | 취소 시 소유 한/글만 종료되고 사용자 한/글 유지, 10초 `CANCEL_TIMEOUT`, 원본 SHA-256 불변 | `C:\HWP_AUTODOCFIT\.com-test.lock` 잠금 필수. 사용자 문서는 사본으로만 |

## 8. 측정 (이 문서 작성 중 실제로 돌린 것)

- 기존 시험: `python3 -m unittest tests.test_jobs tests.test_native_ipc tests.test_hwp_bulk_bridge` → **28건 통과**(macOS, Python 3.14.0, COM 없음).
- 4.1절 확인용 임시 스크립트(저장소에 넣지 않음; 실제 `IpcServer`+`ApplicationService`, `table_units('slow')`만 3초 `sleep`하도록 `dispatch`를 감쌈):
  - 느린 호출 전체 3.01초.
  - 느린 호출 진행 중 **다른 연결**의 `get_events`: **2.70초** 후 성공 응답(잠금 대기).
  - **같은 연결**에 느린 호출 직후 `get_events`를 이어 보내면 두 번째 응답이 **3.01초** 뒤에 도착(요청 순서대로 직렬).
  - `cancel_job`을 같은 방식으로 시험하려 했으나 느린 호출이 끝난 뒤에 실행돼 대기 시간이 0.00초로 나왔다 — **취소 지연은 측정하지 못했다**. `get_events`와 같은 잠금 경로이므로 같은 지연이 생긴다는 것은 코드(`ipc_server.py` 67행)에서 읽은 추론이다.
- 이 PC(macOS)에서는 한/글 COM·Flutter 빌드를 돌릴 수 없어 COM 호출의 실제 소요 시간, Dart 클라이언트 동작은 **확인하지 못했다**.

## 9. 열린 질문

1. 이관 전 과도기에 동기 COM 호출을 취소할 필요가 있나? 있다면 Dart 제어 전용 두 번째 연결을 둘 것인가(서버는 8연결 허용), 그 호출을 먼저 P5로 당길 것인가.
2. 폴링 vs 푸시. 이 설계는 폴링을 유지한다. 폴링 지연이 체감 문제로 확인되면 `get_events`에 선택 `wait_ms`(≤1000, 잠금 밖이라 가능)를 더하는 것이 푸시보다 먼저다.
3. `start_job` 멱등키(`client_request_id`)와 완료 이력 영속화: 지금은 재연결 = 새 백엔드라 필요성이 낮다. 백엔드를 살려 둔 채 재연결하는 구조(Dart `disconnected`가 kill하지 않는 방식)로 바꿀 때 함께 결정한다.
4. 자료함·타임머신 스캔처럼 오래 도는 `singleton` job을 문서 슬롯과 병행 허용해도 되는가(디스크 경쟁, 한/글과의 충돌 없음 여부는 Windows 실측 필요).
5. `hwp_bulk`의 암호 목록은 `passwords.clear()`로 버린다. job `params`는 `native-jobs.json`에는 기록되지 않지만(ID·종류만) 사건 링 버퍼·`status`에 `params`가 새지 않는지 P3에서 확인해야 한다(`JobManager.status`는 `params`를 반환하지 않음을 확인했으나, 어댑터가 `item_done` 등에 담는 값은 검토 필요).

## 10. 구현 현황 (카드 IPCJOB2, 1단계)

- 공용 모듈 `docfit_app/job_envelope.py`: `job_error`(5.5 매핑, `recoverable` 추가), `ProgressThrottle`(초당 10건 상한), `fit_result`(256 KiB 한도).
- `JobManager`: `job_status(id)`(종료 시 `result`/`error`), `SINGLETON_KINDS`(같은 kind 동시 1개, 위반 시 `JOB_RUNNING`), `failed.data`에 `recoverable` 추가, `cancelled.data.partial`.
- 첫 이관 대상 **`library_index`**(3절 #8, 파일 IO만·COM 없음): `start_job('library_index', {library_id})`. 기존 `library('index')` 동기 호출은 그대로.
- `handshake.capabilities`에 `jobs.v1` 추가. `job_status` 메서드 추가. 전송층 CONTROL 잠금 밖 처리(5.8)는 이번 카드에 포함하지 않음.
- 시험: `tests/test_ipc_job_library_index.py`(11건).
