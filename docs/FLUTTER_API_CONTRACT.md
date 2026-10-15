# Flutter ↔ Python API 계약

## 신규 준말 API v1

호출: 기존 `docfitCall(method, JSON.stringify(args))`/pywebview 로컬 bridge. HTTP API·MCP가 아니다. `_BrowserApi`에 아래 명령만 추가한다.

| 명령 | 위치 인자 | 성공 data |
|---|---|---|
| `get_abbreviations` | 없음 | snapshot |
| `save_abbreviation` | key:string, type:`text`/`format`, value:string, original_key:string(기본 `""`) | 저장 후 snapshot |
| `delete_abbreviation` | key:string | 삭제 후 snapshot |
| `set_abbreviation_defaults` | enabled:boolean | 저장 후 snapshot |

응답: `{"api_version":1,"ok":true,"data":{...},"error":null}`. 실패는 `ok:false,data:null,error:{code,message,recoverable}`. snapshot은 `entries:[{key,type,value,label,builtin,style?}],format_kinds:{종류:설명},use_defaults:boolean,running:boolean`이다. `style`은 기존 학습 결과이며 Flutter는 덮어쓰지 않는다. 일반 `get_state`에 준말 목록이나 문서 내용을 추가하지 않는다.

| 코드 | 의미 / 사용자 동작 |
|---|---|
| `INVALID_INPUT` | 길이/콜론/종류/본말/중제목 번호 오류, 입력 수정 |
| `DUPLICATE_KEY` | 다른 등록의 키를 덮을 수 없음, 해당 항목 편집 |
| `NOT_FOUND` | 삭제/수정 대상이 없어짐 또는 내장 항목 삭제 시도, 재조회 |
| `JOB_RUNNING` | 작업 중 변경 금지, 완료/중단 뒤 재시도 |
| `INVALID_REGISTRY` | 저장된 준말 등록표 형식 오류, 기존 데이터 확인 |
| `SETTINGS_READ_FAILED` | 읽기/JSON 실패, 파일은 보존 |
| `SETTINGS_WRITE_FAILED` | 파일 교체 실패, 기존 설정은 보존, 재시도 |

현재 서비스 오류는 복구 가능 여부 `true`로 보낸다. Flutter는 API 버전 불일치를 `API_VERSION` 오류로 다룬다. 새 등록의 `original_key`는 빈 문자열이다. 사용자 항목 편집/이름 변경은 기존 키를 보낸다. 기본 항목 편집은 사용자 override로 저장하며, override 삭제 시 기본 준말이 다시 적용될 수 있다. 문서 적용 규칙(첫 어절+콜론, 붙임 부수 제외)은 기존 엔진 그대로다.

## 기존 API 및 종료

기존 상태/옵션/프로필 명령의 bare Map/bool 반환을 바꾸지 않는다. 기존 전체 API의 버전 관리·structured error 전환은 후속이다. `get_state`는 파일/모드/범위/단계/프로필/결과/guide 등의 전체 snapshot이다. 진행 이벤트와 변경 revision은 아직 없다.

`_tk` dispatch 시간 초과는 미실행 요청을 취소한다. 실행이 이미 시작됐으면 취소했다고 주장하지 않고 중복 실행을 피하도록 안내한다. 종료는 진행 중 callback을 강제 중단하는 것이 아니라 기다리는 bridge 요청을 오류로 완료한다. 작업 중단은 기존 worker의 `중단_event` 경로를 사용한다. 종료 확인 취소 시 bridge는 열린 상태를 유지한다.

서비스/브리지 오류에 문서 본문·준말 값·민감한 파일 내용을 로그로 남기지 않는다. 전체 상태의 파일 경로는 기존 UI 표시/로컬 처리 목적이며 외부 전송 기능을 추가하지 않는다.
