# C28 — LiveLink 0단계 실측 및 1단계 계약

2026-10-29 · `feature/livelink` · v2.0.1 기반. **부분 가능, 승인 설계 전체는 아직 통과하지 못했다.**
실행 중인 시험용 한/글에 ROT로 연결하고, 문맥을 읽고, 표를 직접 삽입·교체하고,
선택 글자의 자간을 바꾸는 경로는 확인했다. **여러 편집을 Ctrl+Z 한 번으로 복원하는 요구는 미충족**이다.
설치된 제품은 한/글 2020이 아닌 **한컴오피스 NEO, COM Version `9, 6, 1, 10778`**이다.
2020 및 다른 빌드에서 같은 결과를 보장하지 않는다. 현재 앱 처리 엔진·사용자 UI는 변경하지 않았다.

## 실행·증거·안전 경계

```powershell
& 'C:/Users/haiju/OneDrive/바탕 화면/HWP_AutoDocFit/mapo-agent-1/.venv/Scripts/python.exe' scripts/livelink_poc.py --out C:/HWP_AUTODOCFIT/v1803/reports/C28-new-run
```

- Windows, pywin32, defusedxml, psutil 및 이미 등록된 `HwpAutoDocFitSecurity` DLL이 필요하다.
  `--out`은 존재하지 않는 새 폴더여야 한다. `--lock-wait` 기본 600초, `--phase-timeout` 기본 30초.
- `C:\HWP_AUTODOCFIT\.com-test.lock`을 원자적으로 생성한다. 기존 잠금을 가로채거나 자동 삭제하지 않는다.
  이번 시작 시 남아 있던 C27 잠금은 관련 시험·한/글 프로세스가 없음을 확인하고
  `reports/C28-stale-C27-lock-20261029.txt`로 보관했다.
- 이 NEO에서는 `XHwpWindow.WindowHandle`이 없다. **기존 Hwp.exe가 하나라도 있으면 시험을 중단한다.**
  DispatchEx 전후 신규 PID가 정확히 하나인 경우만 소유자로 기록한다. 새 창 생성 자체가 목적이 아니라,
  재연결 대상이 될 안전한 시험 인스턴스를 먼저 만드는 절차다. 재연결 때는 새 창을 만들지 않는다.
- `테스트예시/기본 서식.hwpx`를 결과 폴더의 `scratch/sample.hwpx`로 복사한다.
  ROT를 읽기 전에 기존 소유 COM 프록시로 사본 경로를 확인한다. PID를 이름에서 확인할 수 없는
  NEO ROT 항목은 실행 중인 모든 한/글 PID가 소유 집합과 같을 때만 연결한다. 연결 후 사본 경로를 다시 확인한다.
  사용자 창과 함께 실행하는 시나리오는 의도적으로 시험하지 않는다.
- 문서에는 Save/SaveAs를 호출하지 않는다. 표 변환용 보조 탭에는 scratch의 생성 파일만 연다.
  종료 때 `Clear(1) → Quit`, 필요하면 `docfit_core.hwp_process`의 소유 PID 정리를 사용한다.
  감시 프로세스가 venv launcher를 포함한 자기 Python 트리를 종료하고 소유 한/글만 정리한다.
  DispatchEx 자체가 반환하기 전에 멈추면 소유 PID 확정이 불가능할 수 있으므로, 알 수 없는 신규 PID를 강제 종료하지 않는다.
- 최종 기능 실측: `C:\HWP_AUTODOCFIT\v1803\reports\C28-final2/`의 `result.json`, `dialog.json`,
  `replace-trace.json`, `supervisor.json`. 문서 본문을 뺀 요약은 [LIVELINK_POC_RESULTS.json](LIVELINK_POC_RESULTS.json).
  앞선 run1~7/final/verify에는 실패 경로도 보존했다. 원본 SHA-256은
  `49a6b7f6601e0aa63ddd157d6f1dfb0ec852abc45eccae28e7a135533824e899`이며 실측 후 동일하다.
  final2 종료 시 잔여 한/글 PID 0개. 시간은 단일 실행의 진단값이며 동시 단위 시험 부하가 있었다.

## 항목별 결과

아래 시간은 모두 NEO `9.6.1.10778`에서 측정했다. 성공은 해당 좁은 시험의 성공을 뜻한다.

| 항목 | 판정 | API / 관측 | 소요 시간·제약 |
|---|---|---|---|
| 1 실행 중 인스턴스 연결 | 조건부 가능 | `GetRunningObjectTable → EnumRunning → GetObject → IDispatch`, `!HwpObject.96.1` | 0.055초. ROT 이름은 PID가 아니다. 소유 단독 세션에서 경로 대조 성공 |
| 1 다른 연결 경로 | 실패 | `GetActiveObject` HRESULT `0x800401E3`, `GetObject(display name)` `0x800401E4` | 각각 0.024/0.025초. 무조건 Dispatch로 대체하면 새 인스턴스가 생기므로 폴백 금지 |
| 1 보안 모듈 | 신규 객체 성공·ROT 재등록 실패 | 신규 프록시 `RegisterModule(FilePathCheckDLL,HwpAutoDocFitSecurity)=True`; ROT 프록시는 False | 최초 0.009초. False를 등록 성공으로 해석하지 않음. ROT 편집·파일 접근 보안 권한의 독립 검증 필요 |
| 2 커서·선택 | 가능 | `GetPos`, `CreateSet(ListParaPos)`, `GetSelectedPosBySet` | 0.014초. 선택 없음(False)은 커서 두 끝점으로 표현. 인자 없는 `GetSelectedPos()`는 필수 인자 오류 |
| 2 현재 문단 | 가능 | `MoveParaBegin`, `MoveSelParaEnd`, 블록 `GetTextFile` | 0.157초. 위치를 복원하나 기존 선택 방향·스크롤의 완전 복원은 별도 계약 필요 |
| 2 현재 쪽 | 제한적 가능 | `KeyIndicator`, `MovePageBegin/MovePageEnd`, `GetPos` | 0.017초. 화면 이동 끝점 확인. 표·다단·각주를 포함한 쪽의 전체 논리 범위로 단정할 수 없음 |
| 2 표 안 여부·표 위치 | 가능 | `ParentCtrl.CtrlID == tbl`, `HeadCtrl/Next`, `GetAnchorPos(0)` | 0.081초. 본문 anchor `(0,0,16)` → 표 내부 `(2,0,0)` 확인. 중첩 표는 별도 검증 |
| 3 복수 동작 Undo 묶음 | 미충족 | `BeginTransaction` 미노출. `InsertText → Bold → InsertText → Undo` | 없는 API 확인 0.029초, 반례 0.398초. 첫 삽입이 남아 1회 원복 실패 |
| 3 단일 삽입 Undo | 가능 | `SetTextFile(HWPML2X,insertfile) → Undo` | 아래 삽입 측정에 포함. 표 수뿐 아니라 전후 문서 HML 문자열 일치 확인 |
| 4 커서에 표 삽입 | 가능 | `FindCtrl → GetTextFile(HWPML2X,saveblock:true) → SetTextFile` | 1.975초(추출·삽입·Undo·검사 포함). 표 8→9→8, 클립보드 사용 없음 |
| 4 정보단위 증감 후 교체 | 조건부 가능 | 기존 `table_units.export_resized`, 보조 탭 HML 변환, `DeleteCtrl → SetTextFile` | 9.262초(내보내기·3개 보조 탭·증가/감소·검사 전체). 표(가로) 모양1 6→7→5행, 대상 DocumentID 유지 |
| 5 선택 자간 | 저수준 가능 | 기존 `단어모드_자간적용`, `SelectText`, `CharShape.Spacing*` | 1.753초(앱 모듈 로드 포함). 3글자 7종 자간 0→-1, 범위 밖 관측점은 불변. 전체 탐색 엔진 동일성 미검증 |
| 6 모달 중 COM | 이번 대화상자는 응답 | `HAction.Run(CharShape)`, STA 마샬링 후 다른 스레드 `GetPos`, `CharShapeBold` | 대화상자 총 4.072초. 열린 상태를 Win32로 확인한 뒤 읽기·편집 호출 모두 응답. 개별 값은 요약 JSON 참조 |

표 교체는 **알려진 템플릿에서 방금 삽입한 표**를 커서로 식별한 실측이다. 임의 사용자 표의 정보단위 판정,
기존 셀 내용 이관, 그림·수식·병합·참조 ID·페이지 배치 충실도, 표 교체 Undo 1회는 검증하지 않았다.
단순 `Insert(path,HWPX,'')`는 False였고, 보조 탭을 즉시 Clear/Close하는 구현은 서버 예외·대기를 보였다.
최종 스크립트는 보조 탭을 세션 끝까지 유지한다. 중간 실패를 무조건 재시도하지 않는다.

## 권장 구조와 1단계 구현 설계

**서비스·읽기 문맥과 단일 표 삽입부터 구현하되, 전체 쓰기 기능 출시는 Undo 게이트 통과 전까지 보류한다.**
단축키와 패널이 같은 명령 API를 호출하고, 문서 처리용 기존 배치 파이프라인을 그대로 호출하지 않는다.
배치에는 저장·재열기·문서 전체 초기화·순회가 포함되기 때문이다.

### LiveLink 서비스와 명령 큐

- `LiveLinkService`는 UI와 분리한 프로세스, COM 객체는 전용 STA 한 곳에서 소유한다.
  인증된 로컬 named pipe로 연결하고, 단일 FIFO writer 큐와 최대 길이 16을 둔다. COM 프록시는 UI에 넘기지 않는다.
- 세션 키는 `session_id + generation + DocumentID`이며 내부적으로 PID 생성 시각·창·ROT moniker도 보관한다.
  NEO의 moniker 숫자를 PID로 가정하지 않는다. 실제 사용자 세션의 창/COM/문서 대응은 **다음 구현의 선행 게이트**다.
  이 시험 스크립트의 “기존 한/글이 있으면 중단” 정책을 제품 서비스의 접속 방식으로 복사하지 않는다.
- 명령: `get_context`, `insert_template`, `resize_table_units`, `spacing_selection`, `cancel`, `get_command_status`.
  요청은 `{request_id, session_id, generation, document_id, expected_context, command, payload}`.
  `expected_context`는 선택 끝점과 대상 블록 지문. 큐에 들어갈 때와 실제 쓰기 직전에 재검증한다.
  문서 닫힘·다른 탭·커서 이동·블록 변경이면 `STALE_CONTEXT`로 중단하며 자동으로 다른 문서에 적용하지 않는다.
- 응답: `{request_id, status, changed, context, undo_steps, error_code}`.
  상태는 queued/running/succeeded/failed/cancelled/indeterminate.
  완료는 반환값뿐 아니라 대상 구조·범위 밖 보존 검사까지 통과한 경우다. request_id는 중복 실행하지 않는다.
- 모달은 HNC_DIALOG/#32770의 소유 관계·표시 여부를 확인해 `DOCUMENT_BUSY`로 큐 진입을 막는다.
  이번 모달에서 COM이 응답했어도 다른 파일·인쇄·보안 창은 응답하지 않을 수 있다.
  UI 응답 대기 제한과 COM 호출 종료는 다르다. Python 스레드 취소는 막힌 COM을 끊지 못한다.
- 읽기 2초/쓰기 10초를 초기 IPC 제한으로 두고 실측으로 조정한다. 제한 초과는 indeterminate와 재연결 필요를 반환한다.
  늦게 완료된 명령을 재실행하지 않는다. 실제 서비스는 **사용자의 Hwp.exe를 강제 종료하지 않는다**.
  PoC의 강제 종료는 소유 시험 인스턴스만을 위한 별도 정책이다.

### 되돌리기 계약

- `undo_steps=1`은 실제 지원 빌드에서 문서 내용·서식·개체·주변부까지 원복을 검증한 명령에만 준다.
  `BeginTransaction/EndTransaction`을 있다고 가정하거나 Python 호출 묶음을 Undo 묶음으로 취급하지 않는다.
- 확인된 후보는 **한 번의 블록 삽입**이다. 표 교체의 DeleteCtrl+삽입, 여러 run의 자간 변경에는 적용할 수 없다.
  보조 문서에서 변경된 블록을 만들고 한 번의 선택 블록 교체로 커밋하는 방식을 다음 실험으로 검증한다.
  해당 교체의 단일 Undo·서식 충실도가 실패하면 한컴 공식 SDK/확장 기능에서 지원 방법을 확인해야 한다.
- 일반 Undo를 여러 번 실행하는 자체 복원 버튼은 Ctrl+Z 1회 요구의 대체가 아니다.
  사용자가 이어서 입력한 작업을 되돌릴 위험이 있으므로 자동 Undo 반복을 금지한다.
  오류 시 복구용 메모리 블록과 문맥을 보관할 수 있으나, 보존 범위가 증명되지 않으면 쓰기를 시작하지 않는다.

### 선택 범위와 기존 자간 엔진

- 범위는 `(list, para, pos)` 끝점과 선택 지문으로 고정한다. 첫 버전은 동일 list의 완전한 본문 문단만 허용한다.
  표의 여러 셀·중첩 컨트롤·필드·보호 영역·어절 중간 경계는 지원 범위 밖으로 반환한다.
- `RunContext`에 `scope`를 넣고 `_자간자동조정_본체`, 줄 순회, 자간 초기화, 단어 탐색, 성공/실패 복원의
  모든 쓰기 지점을 동일한 범위 검사기로 제한한다. 주변 줄 조판은 읽되 범위 밖으로 선택을 확장하지 않는다.
  기존 `단어모드_자간적용`과 혼합 자간 보관·최소 성공 탐색 알고리즘을 재사용한다.
- scope=None은 기존 결과를 그대로 유지해야 한다. 같은 사본 두 개에서 기존 경로와 범위 경로를 비교해
  선택한 완전 문단의 자간·장평·줄 경계·미해결 목록 일치, 원문 글자와 범위 밖 run/표/문단 속성 불변을 검사한다.
  부분 선택은 전체 문서 실행과 목표가 달라질 수 있으므로 전체 문서 결과 동일성을 주장하지 않는다.
  아직 이 회귀 묶음이나 범위 인자를 구현한 것은 아니다.

### 단축키·도킹 패널 계약

- UI 프로세스의 `RegisterHotKey`로 사용자 지정 키를 등록한다. 충돌은 안내하고 다른 키를 선택하게 한다.
  키 이벤트는 foreground 문서 문맥을 캡처해 같은 명령 큐로 보내며 키 입력 자체로 편집하지 않는다.
- 1차 패널은 외부 보조 창으로 한/글 옆에 배치한다. WinEventHook으로 이동·크기·최소화·모달을 따라간다.
  진짜 한/글 내부 도킹은 미검증이며 별도 SDK/애드인 검토가 필요하다. 외부 패널을 내부 도킹으로 표시하지 않는다.
- 패널 버튼은 “선택 자간 정리”, “표 넣기”, “표 정보단위 증감”. 현재 범위, 실행 중 상태, 완료·실패만 표시한다.
  요청 전 커서를 캡처하고 패널 포커스로 인해 대상을 바꾸지 않는다. 문맥이 바뀌면 새 선택을 요구한다.

## 검증 및 다음 게이트

- 보호 경계 시험: `python -m unittest discover -s tests -p test_livelink_poc.py -v` — 5개 통과.
  타 문서 경로 거부, 죽은 PID의 COM 접근 금지, 기존 잠금 보존, 예외 시 자기 잠금만 해제,
  venv launcher 아래 작업 프로세스까지 종료하는 감시 경계를 검증한다.
- 전체 `python -m unittest discover -s tests` 결과는 아래 최종 검증 기록에 적는다.
- 필요 게이트: 실제 한/글 2020 재실측, 사용자 창 공존 시 문서 식별, ROT 보안 모듈 권한,
  범위 탐색 결과 동일성, 단일 블록 교체의 Undo·서식 보존, 임의 표의 내용 이관, 다른 모달·실제 timeout 주입,
  다단·각주·중첩 표 범위, 단축키와 외부 패널의 Windows 통합 시험.

한컴 공식 개발자 포럼의 [ROT 연결 예](https://forum.developer.hancom.com/t/rot/653)와
[실행 중 객체 연결 논의](https://forum.developer.hancom.com/t/c-rot/736)를 참고했다.
제품별 API를 혼동하지 않기 위해 판정은 이 PC 실측과 설치된 COM type library를 기준으로 했다.
웹한글 API의 Undo 제어를 데스크톱 COM의 트랜잭션 지원 근거로 사용하지 않았다.
