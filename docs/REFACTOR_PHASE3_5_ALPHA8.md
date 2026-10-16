# 1.74 Alpha 8 — Phase 3~5 구현·검증 보고

## 적용 결과

- Phase 3: 26,115줄 본체에서 618개 정의(함수 616개, GUI 클래스 2개)를 분리. 본체 3,310줄, CRLF 유지. 보안·COM·자간·서식·쪽 배치·파이프라인은 `docfit_engine`, Tk 폴백은 `docfit_ui`에 배치.
- 기존 함수 이름·시그니처는 본체 re-export로 유지. `runtime` 바인더는 호출 세션의 전역 딕셔너리를 공유하므로 기존 monkeypatch·runpy 사용을 보존함. 전역 의존성의 완전 제거 또는 모든 엔진 함수의 독립 실행 API화를 의미하지 않음.
- 기준 커밋 `41e5428` 대비 실행 함수 AST 614개 동일 확인. 독스트링을 제외하고 주입된 기본 인수 참조를 정규화해 비교함. 의도적 변경은 보안 모듈 초기화와 웹 모드 기본 창 숨김 2개임. 기존 실측 기반 조판 알고리즘은 재작성하지 않음.
- DLL 기본 경로 복사/등록 실패 시 LOCALAPPDATA modules 폴백. 등록 실패와 세션 분리 회귀 시험 추가.
- Phase 4: Flutter 프로필 계층·셀별 편집/복원, 세부 단계 전체 선택·기본값, 기존 표 템플릿·준말 관리 연결. 프로필 저장은 revision 충돌 검사 및 coverage 무효화 적용.
- 아웃라이너 단축키·자동 저장·충돌 방어, AI 붙여넣기/라벨/개조식 변환, 금액·날짜·표 계산·개인정보 가리기, 수치·공공언어 검토를 Flutter 도구 화면으로 통합.
- 공공언어 교정은 사용자가 선택한 규칙만 새 HWPX 사본에 적용. 검토 후 원문 변경 시 재검사 요구. 고급 변환·RAG·IR·표·양식·비교·패치·생성은 선택형 kordoc 버전 계약 확인 후 작업 사본에서 실행. 백그라운드 작업 ID/진행 조회로 RPC 차단 방지.
- 대표 서식·적용 영역·종료 확인을 Flutter 대화상자로 제공. 확인은 자동 승인하지 않음. 실행 중에도 별도 확인 조회를 유지.
- 실제 웹 모드 Tk 루트는 withdraw. 소유 스레드 큐 펌프로 Tk 작업 전달, 외부 RPC 스레드의 Tk 콜백 등록 방지. 파일 대화상자 때만 투명 소형 호스트와 임시 topmost 사용. Tk 폴백은 유지.
- Phase 5: build.bat의 engine/ui/core/app 하위 모듈 수집 및 Flutter 자산 검사 유지. 네이티브 빌드의 app/core 수집 보강. 인수인계·개발 문서와 실행 명세 동기화.

## 최종 검증

- 환경: Linux Python 3.12, 저장소 `.venv/bin/python`, UTF-8, 실제 Tk/Xvfb. Windows COM/winreg만 시험 대역 사용.
- Python 전체: **1,070개 실행, 1,067개 통과, 조건부 건너뜀 3개(Windows 절전 방지·PowerShell 및 미설치 선택형 MCP SDK), 실패·오류 0개**. GUI 필수 모드로 실행해 화면 부재로 인한 숨은 건너뜀 방지.
- 모듈 compile 및 Linux import_check 통과. 본체 CRLF 3,310개, 단독 LF 0개.
- Flutter 전체: **39개 통과**, native 계약 시험 포함. analyze: **No issues found**.
- Flutter 웹 Release 빌드 통과(98.9초). 로컬 자산·폰트 라이선스 포함 검증 통과. 생성 번들은 기존 배포 정책에 따라 Git 추적하지 않으며 Windows 빌드에서 다시 생성함.
- 새 회귀 검증: 엔진 세션 바인딩·보안 폴백, 프로필 revision/복원·JSON 계약, 실제 Tk 소유 스레드 확인 루프, 초안 충돌·교정 사본·고급 비동기 작업, 네이티브 설정 영속화, Flutter 도구·확인 화면.

## 보안·효과·남은 검증

- 사용자 원본 덮어쓰기 방지, XML 안전 파서 정책 유지. 브라우저 공개 면은 JSON 값과 메서드이며 Tk 위젯을 반환하지 않음.
- 동작 보존과 UI 경로 통합 효과는 회귀 시험으로 확인. Windows 실문서 처리 시간·메모리 개선률은 측정하지 않았으므로 성능 향상 수치를 제시하지 않음.
- 현재 운영 경로는 Flutter 웹/WebView2 + 숨긴 Tk/COM 백엔드임. 별도 Flutter Windows 네이티브 시제품은 `engine_ready=false`로 유지됨.
- Windows `.venv\Scripts\python.exe` 전체 시험, 한/글 COM 실측 조판, WebView2 포커스·파일 선택, PyInstaller EXE 실행은 이 Linux 환경에서 검증하지 못함. Windows 배포 전 해당 검증 필요.
- 고급 도구 실제 kordoc 실행은 선택형 엔진 설치 환경에서 추가 확인 필요. tldraw 시제품의 사용권·COM 삽입 잔여 과제는 이번 범위와 별도임.
