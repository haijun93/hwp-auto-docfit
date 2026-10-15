# Flutter·Python 아키텍처 — 점진적 전환

## 현재 실행 구조

Flutter Web(Material 3, Noto Sans KR/CanvasKit 로컬 자산) → `docfitCall` → pywebview `_BrowserApi` → `DesktopWebBridge` → Tk 루프 어댑터/독립 서비스 → Python 작업 worker → HWP COM.

`_BrowserApi`는 허용 명령만 공개한다. GUI·WebView·서비스 객체 자체는 JavaScript에 노출하지 않는다. WebView2를 유지하며 Python/Tk는 대응 기능 검증 전 비상 복구 경로로 남긴다. native IPC 서버나 외부 포트는 이번 변경에서 만들지 않는다.

## 이번 서비스 경계

- `docfit_app/settings_service.py`: 기존 JSON의 읽기/부분 변경/임시 파일+원자 교체. 다른 설정 키 보존, 손상된 파일 덮어쓰기 금지. 기존 앱의 설정 마이그레이션을 재작성하지 않는다.
- `docfit_app/abbreviation_service.py`: 기본/사용자 준말, 검증·CRUD·이름 변경·학습된 표 style 보존·작업 중 변경 금지. Tk 모듈에 의존하지 않는다.
- `docfit_app/api_contract.py`: 신규 API v1 응답·오류 코드/메시지/복구 가능 여부. 기존 API 응답은 호환성을 위해 그대로다.
- `HwpAutoDocFitGUI._준말_서비스()`: 설정 경로를 주입하고 서비스 하나를 재사용한다. Flutter 브리지와 Tk 준말 창은 동일 서비스에 연결한다. 브리지의 Tk 루프 직렬화는 기존 설정 trace 저장과 경합하지 않도록 유지한다.
- `docfit_core/abbreviations.py`와 문서 알고리즘은 재사용한다. 서비스에서 COM 객체를 만들거나 전달하지 않는다.

## Flutter 모듈

`core/api/abbreviation_api.dart`는 타입 있는 API 호출/오류를, `core/models/abbreviation.dart`는 JSON 모델을, `features/abbreviations/`는 조회/검색/편집/삭제 UI를 담당한다. `main.dart`에는 기능 진입점만 추가한다. 다른 기존 화면을 한꺼번에 분리하지 않는다.

상태 관리는 이 독립 기능에서 `StatefulWidget`과 immutable snapshot으로 시작한다. 기존 단일 화면과 잘 맞고 추가 패키지가 필요 없기 때문이다. Riverpod은 공유 서비스·다중 화면 상태가 늘 때 도입 비용/이득을 다시 평가한다. 기존 주 화면 `ValueNotifier` 및 API 주입 테스트를 유지한다.

## 요청 수명과 상태 순서

- Python: 요청 Future를 private registry에 등록한다. 실행 시작을 원자적으로 표시하며, 시간 초과된 미실행 요청은 취소한다. 실행 중인 callback은 강제로 중단하지 않고 별도 오류를 보낸다. Tk 종료는 모든 호출자를 종료 오류로 해제하고 늦은 callback의 결과 덮어쓰기를 막는다.
- Flutter: 명령 시작 시 generation을 증가시킨다. 이전 generation의 poll 성공/실패를 적용하지 않으며 명령 대기 중 새 poll을 시작하지 않는다.
- 범위 입력: 기존 backend 범위가 같으면 입력 draft를 유지한다. 문서 목록·backend 범위·새 작업이 바뀌면 authoritative 값을 반영한다.
- 신규 기능: 저장 실패 시 편집 입력을 유지하며, dispose 이후 비동기 응답으로 위젯 상태를 바꾸지 않는다. 작업 중 변경은 UI와 서비스 양쪽에서 막는다.

## 남은 분리

Tk 변수 기반 앱 상태, 프로필·파일·작업·로그/진행 이벤트는 아직 어댑터에 남아 있다. 이후 서비스 객체로 옮기되 COM은 기존 초기화/해제 절차를 갖춘 Python worker에 남긴다. 새 API 버전과 오류 형식을 기존 명령 전체에 적용할 때는 호환 어댑터와 계약 테스트를 먼저 마련한다. 문서 본문·설정 값·시크릿을 진단 로그에 추가하지 않는다.
