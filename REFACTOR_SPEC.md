# 알파 리팩터링 실행 명세

사용자 지시: Phase 1~5를 순서대로 구현하고 각 단계의 검증 게이트를 통과한다.
기존 시각 편집기 개발 변경을 보존하며 alpha 브랜치에서 진행한다.

## 공통 준수 사항
- HANDOVER.md, AGENTS.md, GEMINI.md, docs/DEVELOPMENT.md,
  STYLE_FIDELITY_DESIGN.md, FORMAT_COPY_DESIGN.md, UI_DESIGN.md 준수.
- 저장소 .venv Python 및 PYTHONIOENCODING=utf-8 사용. Linux 검사는 Windows COM 검증과 구분.
- hwp-auto-docfit.py CRLF 유지, 기존 심볼 re-export, 원본 문서 덮어쓰기 금지.
- XML 파싱은 defusedxml, 브리지는 JSON 값과 명령만 공개.
- 한/글 실측, 여백 15/15/15/8/4/0pt 및 기존 조판 규칙 보존.

## Phase 1: 도메인 및 fidelity
- 계층 분석 원본 index 저장, 정렬 키 반복 검색 제거.
- 요약 분석기 경고, 영문 자간/밑줄색/그러데이션 각도/흰색 음영 회귀 검사.
- 다중 패치 오프셋 방어, ZIP bit 3 안전 처리 또는 명시적 거부.
- HWP 변환 후 패치 등급 분리, kordoc 버전·Node 호환성과 구조화 결과.
- 게이트: py_compile 및 전체 unittest.

## Phase 2: 상태 및 설정
- RunOptions, AppState, config_store 순수 설정 마이그레이션.
- 프로파일 coverage 캐싱, gui.state 접근과 기존 GUI 호환 property.
- 게이트: py_compile, import_check, 전체 unittest.

## Phase 3: 엔진 및 UI 분리
- 말단부터 security(LOCALAPPDATA 폴백), com_driver, spacing, formatter,
  page_fit, pipeline(PipelineCallbacks), docfit_ui 분리.
- 본체는 부트스트랩/호환 파사드, Tk 의존성은 엔진에 반입 금지.
- 게이트: 모든 모듈 compile, runpy import, 전체 unittest.

## Phase 4: Flutter Material 3 UI 일원화
- 프로파일/계층·셀 스타일, stage/환경 설정, 준말/표 학습 브리지.
- 아웃라이너 저장·이동·완료·메모·검색·내보내기 및 단축키.
- AI 붙여넣기/개조식 변환, 작성 도우미/수치·공공언어 검토.
- 메인 문서/작업 카드/진행 보드, 서식·설정·도구 화면 통합.
- Tk 보조 팝업 제거, 숨김 메시지 펌프 및 파일 선택 포커스 처리.
- 게이트: Flutter 빌드, 브리지 계약/스레드 검사, 가능한 화면 검사.

## Phase 5: 패키징 및 통합 검증
- build.bat 신규 모듈/Flutter 리소스 포함, gitignore 점검.
- HANDOVER.md와 docs/DEVELOPMENT.md 코드 구조 갱신.
- compile, import, 전체 unittest, 본체 CRLF 확인.
- 단계별 변경과 통과·실패·건너뜀 및 Windows 미검증을 구분하여 보고.

## 진행 기록
- Phase 1 진행 중. Phase 2~5 미완료.
- 계층 정렬 검색 제거, 요약 경고, 동일 문단 순차 패치 소스맵 재구축 구현.
- ZIP Data Descriptor는 명시적으로 거부하는 정책 채택.
