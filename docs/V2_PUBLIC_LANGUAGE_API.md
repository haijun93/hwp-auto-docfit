# 공공언어 검토·교정 제외어 API (C16, T11·T12)

Python 백엔드 완료, Flutter 화면은 다음 카드에서 구현한다. WebView의
`window.pywebview.api` / `DesktopWebBridge` / `_BrowserApi`에 아래 메서드가 노출된다.
네이티브 시제품 `ApplicationService.dispatch`에는 이 카드에서 추가하지 않았다.
기존 `document_tool('proofread', ...)`는 종전 API다. 새 화면은 아래 API를 사용한다.

## 1. 검토 시작

`public_language('start', payload)` → 서비스 봉투 안의 `job_id`.
`sources` 생략 시 현재 앱에 추가된 파일 목록을 사용한다.

```json
{"action":"start","payload":{"sources":["C:\\문서\\보고서.hwp"]}}
```

```json
{"api_version":1,"ok":true,"data":{"job_id":"job-uuid"},"error":null}
```

같은 동작의 저수준 호출은 `start_job('public_language', {"sources":[...]})`이며
반환값은 봉투 없는 작업 ID 문자열이다. 파일은 HWP/HWPX만 허용한다.
검사·HWP 변환은 임시 사본만 사용하며 원본을 변경하지 않는다.
문서 작업 슬롯을 기존 jobs와 공유하고 사용 중이면 `JOB_RUNNING`으로 거부한다.

## 2. 진행·완료·실패·취소

기존 `get_events(after_seq, max=200)`를 호출하고 **모든 작업**의 사건을 순서대로
소비한 뒤 `next_seq`를 저장한다. 화면은 해당 `job_id`로 사건을 분류한다.
`started → progress* → done/failed/cancelled` 규칙과 gap 처리는
[V2_JOB_PROTOCOL.md](V2_JOB_PROTOCOL.md)를 따른다. `item_done/item_failed`도 발생한다.

```json
{"seq":10,"job_id":"job-uuid","type":"progress","at":"2026-10-23T00:00:00+00:00","data":{"file":1,"total":1,"stage":"scan","percent":0,"source":"C:\\문서\\보고서.hwp"}}
```

완료 사건의 `data.result`:

```json
{
  "review_id":"review-uuid",
  "issues":[{
    "id":"issue-uuid",
    "source_path":"C:\\문서\\보고서.hwp",
    "rule_id":"public.geumbeon",
    "category":"공공언어",
    "source":"금번",
    "suggestion":"이번",
    "reason":"쉬운 표현 제안",
    "count":2,
    "examples":["금번 계획은 몇일 내에 확정합니다.","금번 일정은 금일에 공지합니다."],
    "locations":[
      {"section":"Contents/section0.xml","paragraph":1,"page":null},
      {"section":"Contents/section0.xml","paragraph":2,"page":null}
    ]
  }],
  "errors":[]
}
```

- `id`는 **검토별·문서별·규칙별 표현 묶음**의 불투명 ID다. 같은 표현이 문서에 여러 번
  있으면 한 항목으로 묶이고 `count`와 전체 `locations`가 제공된다. Tk와 같은 단위다.
- `source`=검출 원문 표현, `suggestion`=제안, `category`=규칙 종류,
  `reason`=설명. `examples`는 Tk와 같은 최대 3개 문맥이다.
- `paragraph`는 section 안 XML 문단의 1부터 시작하는 순번이며 빈 문단·표 내부 문단도 센다.
  COM 문단 좌표나 쪽 번호가 아니다. 조판을 측정하지 않으므로 `page`는 `null`이다.
  화면에는 ‘구역/문단’ 위치를 표시하고 쪽 번호를 추정하지 않는다.
- 규칙·매칭·순서·횟수·교정 제안은 Tk의 `scan_hwpx`와 동일하다.
- 일부 문서 실패는 `errors:[{"source":"...","message":"..."}]`와 함께 `done`.
  전부 실패하면 `failed`, `data`에 `code/message`가 온다. 검출 0건은 정상 완료다.

`cancel_job('job-uuid')`는 기존 규약대로 즉시 취소 요청 상태를 반환한다.
COM 호출 반환, 문단 검사, 파일 저장 직전에 취소를 확인한다. `cancelled`를 받을 때까지
완료로 간주하지 않는다. 중간 취소의 전체 목록은 제공하지 않는다.

## 3. 선택 항목만 새 사본에 적용

`public_language('apply', payload)` → 위와 같은 봉투의 새 `job_id`.

```json
{"action":"apply","payload":{"review_id":"review-uuid","ids":["issue-uuid"]}}
```

저수준 호출은 `start_job('public_language_apply', payload)`.
`ids`는 동일 검토에서 반환된 ID의 비어 있지 않은 목록이어야 한다.
임의 규칙 ID나 다른 검토의 항목은 거부한다. 선택한 표현 묶음의 모든 출현을 교정한다.
검토 때 고정한 임시 HWPX에 적용하므로 검사 후 원본이 바뀌어도 검사한 내용만 사용한다.
적용 시점의 공유 제외어 목록을 다시 읽으며, 제외한 표현은 교정하지 않는다.

완료 사건의 `data.result`:

```json
{"results":[{"source":"C:\\문서\\보고서.hwp","path":"C:\\문서\\보고서_공공언어교정.hwpx","changes":2}],"errors":[]}
```

이미 결과가 있으면 `_공공언어교정 (2).hwpx`부터 빈 이름을 찾는다. 기존 파일은 덮어쓰지
않는다. 여러 파일 적용 중 취소하면 이미 완성한 사본은 남고 `item_done`에서 경로를 알 수
있다. 이후 파일은 저장하지 않는다. 적용 진행 `stage`는 `apply`다.
검토 ID·임시 사본은 앱 실행 동안만 유효하며 재시작 후에는 다시 검사한다.

## 4. 제외어 조회·추가·삭제 (T12)

`proofreading_exclusions(action='list', payload={})`는 동일 서비스 봉투를 반환한다.

```json
{"action":"list","payload":{}}
```

```json
{"action":"add","payload":{"expressions":["금번","금일"]}}
```

```json
{"action":"delete","payload":{"expressions":["금일"]}}
```

```json
{"api_version":1,"ok":true,"data":{"expressions":["금번"]},"error":null}
```

Tk의 `설정_폴더()/proofreading_exclusions.json`을 그대로 공유한다. 파일 형식도 기존의
UTF-8 JSON 문자열 배열이며 `load_exclusions/save_exclusions`로 읽고 쓴다.
변경은 매 호출마다 디스크 최신 목록을 읽어 반영한다. 목록은 정렬·중복 제거된다.
추가·삭제 목록은 비어 있지 않은 문자열 배열이어야 한다. 현재 검토 표시는 화면에서
`source`로 필터링하고, 복원한 단어는 다시 검사하면 검출된다.

## 5. 오류·Tk 폴백

즉시 오류 봉투 예:

```json
{"api_version":1,"ok":false,"data":null,"error":{"code":"INVALID_APPROVAL","message":"이 검토에서 적용할 항목 ID를 선택해 주세요.","recoverable":true}}
```

`INVALID_INPUT`: 파일·명령·제외어 입력 오류, `REVIEW_NOT_FOUND`: 재검토 필요,
`INVALID_APPROVAL`: 선택 ID 오류, `EXCLUSIONS_FAILED`: 제외어 파일 읽기/쓰기 오류.
작업 슬롯·시작 후 오류는 기존 jobs 규약을 따른다.

Tk `_공공언어_검토`·`_교정_제외관리` 경로는 유지한다.
`ui_tk_fallback=false`일 때 `run_tool('proofread')`는 새 검토 시작 봉투를 반환한다.
`true`이면 종전 Tk 창을 연다. 새 화면은 `public_language`를 직접 호출한다.
