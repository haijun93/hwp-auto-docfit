# v1.74 Beta 1 리뷰 및 Alpha 3 안정화

기준 코드: Beta 1 `016b6be`, 작업 시작 Alpha 2 `4e1c391`. 기존 alpha 이력을 보존했다. 1.75.1/1.75.2 및 백업 브랜치를 병합하지 않았다. 사용자 확인에 따라 Flutter 제거와 MCP 기능 확대·기본 활성화는 제외했다.

| 우선순위 | 발견 사항 | 영향·확인 | Alpha 3 조치 |
|---|---|---|---|
| P1 | `_tk` timeout에서 Future를 취소하지 않음 | 실패 안내 후 대기 callback이 실행됨을 Python 큐로 재현 | pending 요청 취소, 실행 시작 원자 표시, 실행 중 timeout은 별도 안내 |
| P1 | Tk 종료와 대기 Future가 연결되지 않음 | `timeout=None` 호출자가 종료 후에도 대기 | request registry, 종료 오류 해제, 늦은 callback 완료 안전 처리, 종료 취소 시 bridge 유지 |
| P2 | `rangeLoaded` 때문에 범위를 최초 한 번만 반영 | 새 문서/새 작업에서도 5–7쪽을 다음 start에 전송, 위젯 회귀 실패로 확인 | 문서·backend 범위 변경과 새 작업에 동기화, 입력 draft 보존 |
| P2 | poll과 명령 응답에 순서 방어 없음 | 늦은 spacing snapshot이 새 unify 명령 결과를 덮음, 위젯 회귀 실패로 확인 | 명령 generation 증가, 이전 poll 성공/실패 적용 금지 |
| P1 | `build.bat`이 Flutter 빌드 실패 후 EXE 패키징 계속 | Flutter 없는 패키지를 만들 수 있는 명시적 경로 | Flutter analyze/test/build·오프라인 자산 검증 필수, 실패 시 패키징 중단 |
| P2 | `normalize`의 format value가 list/dict이면 membership TypeError | 손상된 준말 값 때문에 정상 등록표 조회도 실패 가능 | 문자열 타입 검사, 정상 항목 조회·잘못된 raw 값 보존 회귀 시험 |

패키징 경로는 확인된 위험이며, 회수된 1.75의 구체 실행 원인을 추정한 것은 아니다. 새 준말 기능의 오류·작업 중 제약·데이터 보존은 별도 서비스/위젯 시험으로 확인한다. 이전 표 서식과 다른 설정은 그대로 유지한다.

## 구조 리뷰

현재 `DesktopWebBridge`는 Tk 변수와 GUI 메서드에 직접 의존한다. 주요 화면에 Flutter가 있어도 전체 설정·서식 요소 편집·문서 검토·승인·보조 도구는 Tk 화면을 연다. 단일 `main.dart`와 약 26,000줄 Python 앱의 상태/엔진/UI 결합이 전체 전환의 핵심 부담이다.

이번 변경은 `docfit_app`의 UI 독립 준말/설정 서비스와 Flutter `core/api`, `core/models`, `features/abbreviations`를 도입한 첫 단계다. Tk 비상 경로를 삭제하지 않고 같은 서비스에 연결했다. 전체 설정 저장기·작업/파일/프로필 상태·진행 이벤트는 아직 이전하지 않았다. 기존 COM 처리 알고리즘을 재작성하거나 MCP·외부 IPC를 붙이지 않았다.

최종 합격은 Linux 단위 테스트만으로 판단할 수 없다. Windows+한/글 2020에서 실제 문서 사본·설정·준말/프로필·중단/종료·Flutter 자산/EXE를 검증해야 한다. 실제 결과와 미실시 항목은 [시험 보고서](FLUTTER_TEST_REPORT.md), 기능별 다음 작업은 [조사표](FLUTTER_MIGRATION_AUDIT.md)와 [전환 계획](FLUTTER_MIGRATION_PLAN.md)에 기록한다.
