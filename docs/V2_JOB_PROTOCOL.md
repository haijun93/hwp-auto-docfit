# 2.0 작업 통신 규약 (C10)

Python 구현: `docfit_app/jobs.py`. Flutter 수신 구현은 다음 카드에서 한다.
기존 `get_state`, `start`, `stop`, `table_units('copy', …)` 응답은 유지한다.

## 작업과 호출

`start_job(kind, params={}) → job_id`는 UUID 문자열을 반환한다. 종류는
`format`, `spacing`, `unify`, `all`, `file_format`, `table_copy`이다.
C19에서 1.80.9의 문서 도구 삭제 결정에 따라 C16의 `public_language`,
`public_language_apply` 작업과 전용 API를 삭제했다. 아래 공통 jobs 규약은 유지한다.
`file_format`의 params는 `target`(기본 hwpx), 네이티브에서는 `files`, `output_dir`도 받는다.
데스크톱의 PDF 합치기(`target=pdfm`)는 `file_order`로 현재 목록과 같은 파일 집합의 순서만 지정할 수 있다.
데스크톱의 입력 파일은 기존 화면 목록을 쓴다. 문서 작업의 params는
`range_enabled`, `start`, `end`, 표 복사는 기존 `table_units.copy` payload를 그대로 쓴다.
네이티브 시제품은 file_format과 table_copy만 실행하고 나머지는 NOT_AVAILABLE이다.
표 복사는 네이티브에서도 한/글이 설치되어 있어야 하며 미설치 오류는 failed로 전달한다.

작업 상태: `queued → running → done | failed | cancelled`. 취소 요청은 별도
`cancel_requested=true`이며, 요청만으로 cancelled로 바꾸지 않는다.
`status(job_id)`는 JobManager 내부 조회 API이며, `get_state().job`에는
`id`, `job_id`, `kind`, `state`, `progress`, `cancel_requested`가 포함된다(작업 없으면 null).
파일별 실패를 포함한 일괄 처리는 끝까지 실행하면 done이다. `done.data.failed`로 실패 수를 보고,
개별 오류는 item_failed로 보고한다. 작업 자체의 치명적 오류만 failed이다.

## 사건과 조회

```json
{"seq": 31, "job_id": "ed92a599-670b-4223-9b97-368402537164", "type": "progress", "at": "2026-10-23T01:02:03.000000+00:00", "data": {"file": 2, "total": 5, "stage": "save", "percent": 35}}
```

type은 `started | progress | item_done | item_failed | log | dialog | done | failed | cancelled`.
seq는 한 관리자·프로세스 수명에서 모든 작업에 걸쳐 1부터 엄격히 증가한다.
at은 시간대가 포함된 UTC ISO 8601이다. JSON으로 전송할 값만 data에 담으며
COM 객체·콜백·threading.Event는 담지 않는다. 반환 스냅샷 수정은 관리자 상태를 바꾸지 않는다.

`get_events(after_seq, max=200)`은 긴 폴링 없이 즉시 배치를 반환한다.
IPC dispatch의 args는 `[after_seq]`, 직접 Python·WebView API는 max도 지정 가능하다.

```json
{"events": [], "next_seq": 31, "latest_seq": 31, "oldest_seq": 1, "gap": false}
```

소비자는 events를 seq 순서대로 처리한 뒤 next_seq를 다음 after_seq로 보낸다.
max는 1~200, after_seq는 0 이상의 정수이며 bool은 허용하지 않는다.
최근 2,000건만 보관하므로 `after_seq < oldest_seq-1`이면 gap=true다.
이때 get_state로 요약을 다시 읽고 남아 있는 배치를 순서대로 처리한다.
빈 배치의 next_seq는 요청 커서를 유지한다. 재시작·재연결 시 커서를 0으로 초기화한다.
한 사건을 여러 번 받으면 seq로 중복을 제거한다. 네트워크 재전송에 대한 start의 멱등성은
보장하지 않으며 IPC request_id의 기존 중복 차단을 사용한다.

## 진행과 대화상자

progress: `file`은 현재 파일 번호(처리 전 0, 처리 중 1~N), `total`은 N,
`stage`는 단계 이름, `percent`는 전체 파일 처리 비율(0~100)이다.
파일 시작은 `(n-1)/N*100`, 파일 내부 progress(p)는 `(n-1+p/100)/N*100`,
item_done/item_failed 뒤에는 `n/N*100`, done은 100이다. 단계별 소요시간 가중치는 쓰지 않는다.
전체 비율은 단계 재시도·재개 시 되돌아갈 수 있으며 시간 예상치가 아니다.
표 복사는 세부 백분율 없이 started/item_done/done을 보낸다.
saved는 item_done(source, output), document_error는 item_failed(source, message),
status/step/guide는 progress(stage), log는 log(message)로 바꾼다.
GUI가 대기로 복귀했고 worker도 종료됐는데 종료 튜플이 없으면 다음 시작 전에
이전 작업을 JOB_INTERRUPTED 실패로 회수한다. 살아 있는 worker의 슬롯은 회수하지 않는다.
legacy의 서식통일 검토 튜플은 dialog(kind) 알림으로 바꾸고 실제 대화상자 내용과 응답은
기존 get_pending_dialog/resolve_dialog를 쓴다. 다른 UI 대화상자는 기존 API를 계속 사용한다.

## 취소·동시 실행·종료

`cancel_job(job_id)`는 즉시 취소 요청 상태를 반환한다. 중복 요청과 종료된 작업 취소는 무해하다.
runner(report, cancelled)는 파일 사이·저장 전 등 원본 안전성이 보장되는 지점에서 cancelled()를
확인하고 돌아온다. 파일 변환은 기존 stop_event 확인 지점을 유지하고, 표 복사는 시작 전에 확인한다.
진행 중 COM 호출은 Python 스레드를 강제 중단할 수 없으므로 호출 복귀·정리까지 기다린다.
취소 요청 뒤 성공 반환도 cancelled로 처리한다.

10초가 지나도 끝나지 않으면 `docfit_core.hwp_process.kill_owned()`만 호출하고
CANCEL_TIMEOUT 로그를 낸다. 사용자의 한/글 전체 종료나 이미지 이름을 이용한 taskkill은 금지한다.
강제 정리 뒤에도 worker가 살아 있으면 작업 슬롯을 계속 보유한다. 정리 실패는 CLEANUP_FAILED 로그다.
기존 Tk의 중단 유예 점검도 호환을 위해 유지된다(소유 PID 정리는 자체적으로 직렬화됨).

문서 처리·변환·표 복사는 한 관리자에서 한 개만 실행한다. 대기열에 쌓지 않고 JOB_RUNNING으로 거부한다.
가벼운 종류 `inspect`, `preview`, `catalog`는 JobManager에서 병행 가능하다.
WebView의 기존 표 복사 호출도 같은 슬롯을 사용하며, 기존 표 COM 잠금도 유지한다.
관리자는 공유 스레드 잠금으로 상태·seq·배치를 보호한다. 서로 다른 앱 프로세스의 슬롯은 별개이며
네이티브 실행기의 기존 프로세스 잠금은 유지한다.

shutdown은 새 작업을 막고 취소를 요청하며 제한 시간 동안 worker를 기다린 뒤 소유 한/글만 정리한다.
네이티브 shutdown RPC·부모 파이프 단절, WebView/Tk 종료 경로에 연결한다.
활성 작업 ID·종류만 앱 설정 폴더의 desktop-jobs.json/native-jobs.json에 원자적으로 기록한다.
재시작 시 남은 작업은 ORPHANED_JOB failed 사건과 상태로 회수하고 활성 목록을 비운다.
문서 자동 재처리는 하지 않는다. 이전 프로세스의 PID 숫자만으로는 소유권을 증명할 수 없으므로
재시작 후 임의의 한/글을 종료하지 않는다. 사건 전체·완료 이력은 메모리 수명 동안만 유지한다.

## 오류 코드

| 코드 | 뜻·소비자 처리 |
|---|---|
| INVALID_INPUT | 종류·입력·커서·배치 크기 오류, 입력 수정 |
| JOB_NOT_FOUND | 알 수 없는 ID, 상태 다시 조회 |
| JOB_RUNNING | 문서 슬롯 사용 중, 현재 작업 종료 대기 |
| JOB_NOT_STARTED | 파일 없음·설정 검증에서 시작되지 않음 |
| BACKEND_CLOSING | 종료 중, 재시작 후 재연결 |
| NOT_AVAILABLE | 해당 실행기에 문서 엔진 없음 |
| JOB_FAILED | 작업 자체 오류, message 표시 |
| JOB_INTERRUPTED | 기존 worker가 종료 사건 없이 끝남, 실패로 회수 |
| HWP_FAILED / CLIPBOARD_FAILED | 기존 표 복사 서비스 오류 유지 |
| CANCEL_REQUESTED | 취소 접수 log, 종료 사건 대기 |
| CANCEL_TIMEOUT | 유예 초과 log, 소유 COM 정리 시도 |
| CLEANUP_FAILED | 정리 호출 실패 log, 종료 대기 |
| ORPHANED_JOB | 이전 실행이 비정상 종료된 작업, 사용자 재시작 필요 |

신규 호출의 즉시 검증 오류는 기존 ServiceError/IPC 오류 봉투를 사용한다.
시작된 작업의 오류는 failed 사건 data의 code/message에 담는다. 기존 API 봉투는 바꾸지 않는다.
