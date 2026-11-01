# V3A2 α2 부족분 점검

범위: `docs/V3_PLUGIN_DESIGN.md`의 3.0-α2 (도우미 패널, 단축키, 트레이). α3와 `docfit_live/service.py`는 수정하지 않았다.

| α2 항목 | 상태 | 코드 근거 / 비고 |
|---|---|---|
| 약 360px 도우미 패널 화면 | 구현 | `flutter_ui/lib/features/live/helper_panel_screen.dart`; 좌측 메뉴에서 열리는 다이얼로그. 기존 화면과 병존 |
| 한/글 문서 연결 상태 표시 | 구현 | 사이드 메뉴의 LiveLink 상태 표시와 도우미 화면 내 안내 |
| 전역 단축키 기본값·파싱·등록 서비스 | 구현 | `docfit_live/hotkeys.py`; 기본 panel/table_template/table_sketch, Win32 등록 전용 메시지 스레드 |
| 설정 저장 및 중복 조합 검증 | 구현 | `desktop_web_ui.py::live_hotkeys`, `SettingsService` 설정의 `hotkeys` 키; Flutter 도우미에서 조회·저장 |
| 다른 앱이 점유한 단축키의 충돌 표시 | 구현 | 서비스 `failed` 응답을 도우미 입력란 아래 표시. 실제 등록 충돌 여부는 Windows 확인 필요 |
| 패널 단축키가 실제 화면 열기·닫기 동작 | 구현 | 핫키 요청을 상태 응답에 한 번 얹어 Flutter가 도우미 패널을 토글. 이미 열린 패널은 중복 다이얼로그를 만들지 않음 |
| 표 템플릿·표그림판 단축키가 실제 기능 실행 | 구현 | 상태 응답의 핫키 요청을 기존 `tabRequest`로 전달해 표템플릿(1)·표그림판(2) 탭 선택 |
| 한/글 창 옆 위치 계산 및 창 이동 추적 | 구현 / 실제 Windows 확인 필요 | `docfit_live/dock.py::panel_rect`, `DockTracker`와 순수 계산 시험 존재. 실제 창 핸들·모니터 API를 앱 수명주기 및 Flutter 창 이동에 연결한 코드 없음 |
| 한/글 이동·최소화·복원에 따른 추적 | 실제 Windows 확인 필요 | Win32 열거/창 사각형/모니터 작업영역 API는 지연 호출 함수로 존재. Windows에서 창 상태별 동작 미실측 |
| 트레이 상주, 메뉴·복원·종료 | 미구현 | α2 전용 트레이 아이콘/메뉴/수명주기 구현을 찾지 못함 |
| macOS에서 Windows 전용 코드 로드 | 구현 | Win32 진입은 `_user32()` 및 `_Win32Api` 생성 시점으로 지연. Win32 서비스 실제 동작은 Windows 확인 필요 |

## 이번 보완

- Flutter에 좁은 도우미 패널 화면과 사이드 메뉴 진입점을 추가했다.
- `live_hotkeys` 조회·저장 API를 Flutter에 연결하고, 저장된 세 조합과 등록 실패 이유를 표시한다.
- 기존 순수 좌표 계산과 가짜 창 프레임 추적 시험은 유지했다.

## 시험

- Python: `~/work/cx/venv/bin/python -m unittest tests.test_live_dock tests.test_live_hotkeys` — 22개 통과.
- Flutter: `flutter analyze --no-pub lib test` — 문제 없음. 전체 `flutter test --no-pub --timeout 120s` — 243개 통과, 1개 건너뜀.
- Windows 한/글·트레이·전역 단축키 실측은 이 macOS 환경에서 수행하지 않았다.

## 전역 단축키 화면 연결

- Python 콜백은 마지막 키 기록과 별도로 FIFO 요청 대기열에 쌓고, `get_state`가 잠금 아래 한 번만 꺼내 `hotkey_requests`에 포함한다. Tk 화면 호출은 하지 않는다.
- Flutter는 패널 요청을 도우미 패널 열기·닫기에 연결하고, 표 템플릿·표그림판은 `tabRequest`로 각 탭을 선택한다. 열린 패널에 재차 요청이 와도 다이얼로그를 겹쳐 열지 않는다.
- 시험: Python `tests.test_live_hotkeys` 14개 통과. Flutter `analyze --no-pub lib test` 문제 없음, 전체 시험 244개 통과·1개 건너뜀(약 50초). 신규 라우팅 위젯 시험 포함.
- macOS에서는 OS 전역 키 입력 등록 자체를 실측하지 않았다. Windows 전역 단축키 동작과 트레이는 별도 확인 범위다.
