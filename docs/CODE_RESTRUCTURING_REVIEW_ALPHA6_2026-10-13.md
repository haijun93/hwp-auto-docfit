# Alpha 6 기준 소스코드 재구조화 검토

검토 기준 커밋: GitHub `alpha` 8b83fc8 및 tldraw 첫 구현 변경분. 이 보고서는 구조·의존 방향의 검토이며 전체 실행 프로파일링 보고서가 아니다.

## 요약

기능별로 `docfit_app`(설정·서비스·IPC), `docfit_core`(문서 규칙), `docfit_infra`(파일 잠금), `flutter_ui/lib/features`(UI 기능)가 생겨 재구조화가 시작됐다. 기존 `hwp-auto-docfit.py` 문서 엔진과 Tk COM 파이프라인을 유지하는 점은 안전한 점진 분리다. tldraw도 독립 React 자산과 Flutter route로 분리하여 core 서식 처리와 분리했다.

단, “Flutter 네이티브 앱 + 독립 Python 서비스”는 시제품 상태다. Alpha 6 감사에서 `engine_ready=false`, 실제 COM 파이프라인 미연결, 설정·분석 위주 명령만 연결된 사실이 확인된다. `main.dart`는 현재도 대형 단일 파일이며 Python 엔트리포인트 `hwp-auto-docfit.py`에도 작업/GUI 코드가 남아 있다. 따라서 재구조화가 완료됐거나 기존 앱을 대체했다고 말할 수 없다.

## 확인된 우선 개선점

| 우선순위 | 관찰 | 영향 | 권장 조치 |
|---|---|---|---|
| P0 | native 앱이 아직 실제 문서 처리 엔진을 실행하지 않음 | 입력·설정 시제품과 제품의 처리 결과가 다름 | 엔진 worker/COM STA, job 상태·취소·재연결 계약 후 단일 작업 vertical slice 검증 |
| P0 | native IPC는 요청을 `ApplicationService.lock` 안에서 동기 실행하고 종료까지 기다림 | 큰 HWPX 분석·저장이 UI 요청을 막을 수 있음 | job_id와 bounded worker queue/progress event 도입 전 문서 분석 응답 지연 측정 |
| P1 | Python dispatcher와 Flutter `main.dart`가 점차 커지는 집중점 | 테스트·UI 수정의 영향 범위 증가 | 화면을 documents/settings/diagrams/results feature로 옮기고 API contract 타입을 고정 |
| P1 | IPC는 loopback token 인증이지만 단일 사용자 OS 경계가 아님 | 같은 PC의 다른 프로세스가 연결 슬롯을 점유할 가능성 | Windows ACL Named Pipe 또는 짧은 인증 전 timeout·연결 정책 실측 검토 |
| P1 | IPC 한도 1 MiB와 결과 JSON 메모리 확장 | 대형 입력 결과를 반환할 때 크기 제한 오류 | 대형 문서/다이어그램을 파일 핸들·staging 경로 방식으로 전송, 파일 경계 검증 |
| P1 | tldraw 라이선스 및 5 MB 자산 증가 | 승인 없는 제품 배포 위험, 초기 로딩 부담 | 개발 전용 차단 유지, 법적 사용 허가·Windows 로딩 메트릭 후 결정 |
| P2 | Python monolith 분리와 성능 최적화가 한 계획에 섞일 수 있음 | 분할 자체를 성능 효과로 오인 | 경계 추출은 동작 보존 회귀 시험, 최적화는 별도 기준선·COM 호출 계측으로 평가 |

## 성능 비교 방법

동일 문서 사본·같은 PC·같은 한/글 버전·동일 설정에서 시작·열기·분석·변환·저장·검수 구간을 각각 계측한다. COM 호출과 문서 열기/저장 횟수, peak RSS, UI 첫 상호작용 시간, 실패/재시도, output 구조 비교, 원본 SHA-256을 수집한다. 기준선이 확보되기 전에는 처리속도 개선 주장을 하지 않는다. Flutter/IPC만 바뀌었을 때는 문서 엔진 시간을 분리해 비교한다.

## 권장 다음 순서

1. native IPC/Flutter API 명세 및 오류·버전·메시지 크기 검증을 자동화한다.
2. HWPX 읽기 전용 분석처럼 COM 없는 기능 하나를 native UI에 끝까지 연결한다.
3. 작은 문서에서 실제 HWP COM STA 작업 큐와 취소/진행 이벤트를 별도 구현한다.
4. Beta1과 같은 실문서 사본으로 결과·원본 무결성 대조, 최소 5회 교차 측정한다.
5. `hwp-auto-docfit.py`, `main.dart`는 테스트 가능한 경계를 한 단위씩 분리한다. 이동마다 전체 회귀 시험을 거친다.
6. Flutter/Node/WebView2/한글 COM의 버전·라이선스·빌드 아티팩트가 고정된 Windows 재현 빌드가 확립될 때까지 정식 전환/배포를 보류한다.
