# Alpha 9 — 리뷰 R1~R5 및 실행 상태·콜백 수정

작성일: 2026-10-14. 기준: 7497338(통합 코드), 287aa0d(검토 보고서).

## 수정 내용

| 항목 | 구현 | 재현 회귀 검증 |
|---|---|---|
| R1 / P1 | 로컬·CI가 HWP_AutoDocFit.spec을 공유. core/engine/app/ui 전수 수집. --self-test는 분리 모듈 및 실제 본체 부트스트랩 심볼 검사 후 JSON/종료 코드 반환 | 동적 모듈 누락·부트스트랩 심볼 누락 시 실패, 전체 소스 부트스트랩 성공. CI는 동결 EXE를 별도로 실행 |
| R2 / P1 | 일반 흐름도와 개발자 tldraw 양쪽에서 편집 세대·저장 세대·진행 중 요청을 분리. 저장 ACK는 해당 snapshot까지만 확정 | 지연 저장 중 추가 입력, 오래된 clean 이벤트, 닫기 차단 위젯 시험 및 빌드된 Flutter 브라우저 재현 |
| R3 / P1 | 아웃라이너 변경 요청 직렬화, 텍스트 revision 비교, 오래된 응답 폐기. 대기 중 자동 저장 연기 및 닫기 차단 | 지연 toggle 중 추가 타이핑과 2초 debounce 경과, 연속 toggle 순차 실행·최신 snapshot 사용 |
| R4 / P2 | 잠금 안에서 UTF-8 바이트 원자 저장 및 실제 바이트 SHA-256 revision 확정. 응답을 위해 잠금 밖에서 재조회하지 않음 | 두 서비스·스레드의 잠금 해제/응답 교차 후 A는 A revision만 반환하며 B 저장에 대한 후속 덮어쓰기 거부 |
| R5 / P2 | 화면·SVG/PNG가 동일한 글자 측정, 한글 줄바꿈, 자동 크기를 사용. 좌우 16px·상하 12px, 도형별 내접 안전 영역 및 외곽 20px 적용 | 한글 400자, 여러 줄, 마름모·타원·텍스트·긴 분기 설명. 실제 DOM 경계 및 PNG 생성 확인 |

일반 편집기와 tldraw 번들을 각각 다시 빌드했다. Flutter 웹 생성물도 갱신하고 자산 검사를 수행한다.
원본 문서 처리·XML 안전 파서·개발자 전용 tldraw 조건과 기존 저장 경로는 유지한다.

## 실행 상태와 콜백

- `docfit_engine/context.py`: RunContext가 RunOptions 사본, 프로필, 컨테이너/XML 캐시, COM 세션 상태, 취소 포트, PipelineCallbacks를 보유한다.
- GUI worker는 명시적으로 context/callbacks를 전달한다. ContextVar는 중첩 호출 동안 같은 실행 상태를 선택하며 종료·오류 시 복원한다.
- runtime은 실제 엔진 함수를 작업별 상태 사전에 바인딩한다. 실행 중 엔진의 전역 조회·쓰기는 본체 사전이 아닌 이 사전에서 발생한다. 두 작업의 캐시·프로필·중단 상태가 섞이지 않는 시험을 추가했다.
- 실제 작업/문서 실행 경로의 로그·상태·진행 및 stage 진입·종료·오류를 주입된 콜백으로 보고한다. 오류는 보고 후 다시 전달한다.
- 기존 루트 함수 호출과 monkeypatch를 위한 호환 어댑터는 의도적으로 남긴다. 이 경계는 명시적 컨텍스트가 없는 구형 호출에서만 상태를 동기화한다. GUI의 명시적 실행 경로는 본체 상태로 결과를 역전파하지 않는다.
- COM 객체·모듈·동기화 객체 등 외부 포트는 깊은 복제 대상이 아니다. 순수 상태 객체로 모든 엔진 함수를 재작성한 것과 구분한다. 다중 COM 작업의 Windows 안전성은 별도 실측 대상이다.

## 최종 검증

- AST/compile: 본체·브리지·패키지 및 spec 86개 검사 통과. 본체 CRLF 3,320줄 유지.
- import_check 및 전체 소스 부트스트랩 --self-test: 통과. Windows 전용 임포트 대체, 80개 패키지/모듈과 부트스트랩 심볼 6개 확인.
- Python 전체: 1,085개 실행, 1,082개 통과, 조건부 제외 3개, 실패/오류 0. 제외는 선택형 MCP SDK 미설치와 실제 Windows PowerShell·절전 API 시험이다. 실제 Tk 시험은 제외하지 않았다.
- 마지막 set 복제 보완 후 RunContext 집중 시험 5개 재실행 통과.
- Flutter 전체: 44개 통과. Flutter analyze: 지적 사항 0개.
- 일반 흐름도 모델: 6개 통과.
- 실제 Chromium 편집기: 예시 10종·왕복 저장·실행 취소/다시 실행·한글 400자 내부 경계·PNG(594×780) 통과. 외부 요청 0건, 페이지 오류 0건.
- Flutter release 웹 빌드와 entrypoint/로컬 CanvasKit/글꼴/사용권 검사 통과. 일반 편집기 5개·tldraw 73개 배포 파일이 원본 번들과 바이트 단위 일치.
- 최종 Flutter 웹 + 실제 Python 저장소 통합: 저장·PNG 출력·재열기·삭제 통과. 일반 모드에서 tldraw 저장소가 생성되지 않음, 페이지 오류 0건.
- 저장 응답을 이벤트로 보류한 상태에서 추가 편집 후 응답 재개: 이전 snapshot만 디스크 저장, 추가 입력은 화면에 보존, 닫기 시 미저장 확인 표시, 계속 편집 후 입력 유지. 페이지 오류 0건.
- 재현 명령: `scripts/verify_flow_editor.py`, `scripts/verify_flutter_flow.py`, `scripts/verify_flow_save_race.py`(Playwright·Chromium 및 최종 웹 번들 필요, 임시 설정/저장소만 사용).

## 남은 환경 검증

- Linux 시험은 실제 Tk/Xvfb를 사용하고 Windows COM/winreg 임포트만 대체한다. 한/글 조판 결과를 검증한 것으로 해석하지 않는다.
- Windows 한/글 COM, WebView2 및 PyInstaller EXE 실행은 이 환경에서 수행하지 못했다. CI에는 동결 EXE 검사와 JSON 결과 검사를 추가했으며 실제 CI 성공을 확인하기 전에는 성공으로 단정하지 않는다.
- EXE smoke timeout은 최초 onefile 압축 해제를 고려한 30초다. 시작 3초 보장이나 성능 개선률은 주장하지 않는다.
- 웹 빌드에는 미사용 CupertinoIcons 글꼴 탐색 경고가 남는다(앱 코드 참조 없음). 필요한 MaterialIcons와 한글 글꼴·로컬 CanvasKit 검사는 통과했다.
- 네이티브 엔진 시제품의 engine_ready=false, tldraw 사용권/배포 정책, MCP 전용 오메가 과제는 이번 수정 완료 범위와 별도다.
