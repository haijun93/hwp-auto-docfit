# 알파 리팩터링 진행 기록

## 적용 범위
- Phase 1 기반 보강 완료, Phase 2 기반 구현·Linux 검증 완료. Phase 3~5는 Alpha 8에서 소스 구현·Linux 검증 완료(Windows 실측 검증 별도).
- 기존 시각 편집기 미커밋 작업은 보존하며 별도 검증 대상으로 유지.
- 개발 지시와 단계별 게이트는 REFACTOR_SPEC.md에 기록.

## 구현 및 검증
- 계층 분석: 문단 원본 index 저장, 정렬 키에서 records.index 반복 호출 제거.
  전체 분석기가 O(N)이라는 의미는 아니며, 정렬 및 기존 문맥 분석은 별도임.
- style_inventory 요약 함수 3개에 축약 경고 명시.
- format_elements 원본 XML 복제에서 4가지 차이의 보존을 회귀 검사.
  대표값 API 자체의 완전 정밀 분석 전환을 의미하지 않음.
- fidelity: 연산 안의 바이트 치환은 역순 적용하고, 연산마다 소스맵 재구축.
  동일 문단의 연속 치환, 서로 다른 문단의 길이 변화, 엔티티 치환 검증.
- ZIP bit 3(Data Descriptor)는 명시적으로 거부. 스트리밍 ZIP 지원 확대가 아님.
- source_provenance를 지정한 HWP→HWPX 변환 후 패치는 별도 등급으로 보고.
  호출자의 변환 이력 전달이 필요하며 실제 COM 변환 실행 검증은 하지 않음.
- kordoc 신규 check_engine_contract/run_kordoc_result는 버전·Node 검증,
  반환 코드 2와 warnings/skipped를 구조화. 기존 Path API는 유지.
  기존 호출부의 신규 계약 API 전환은 후속 작업.
- 본체 CRLF 정규화, .gitattributes로 CRLF 지정, 로컬 venv 추적 제외.

## 검증 환경의 한계
- Linux Python은 저장소 .venv/bin/python, PYTHONIOENCODING=utf-8 사용.
- Windows 전용 모듈 대체 + 실제 Tk/Xvfb로 전체 회귀 검사 수행.
- 직접 unittest에서 본체를 불러오는 일부 시험은 winreg가 없어 실행 불가.
  Linux 시험 실행기로 해당 계층 시험 12개 통과.
- Windows .venv/Scripts/python.exe, 실제 한/글 COM 및 Windows Flutter 실행은 미검증.

## 첫 전체 검사 및 보완
- 1,027개 실행, 오류 1개, 건너뜀 3개. MIME 초기화가 가짜 winreg를 읽은 시험 환경 오류 수정.
- fidelity 13개, format_elements 16개, kordoc 16개, 계층 분석 12개 개별 통과.
- 재검사: 1,026개 실행, 실패·오류 0개, 건너뜀 3개. 기존 kordoc 계약 6개는 별도 재검사에 포함해 보존 확인.
- 현재 전체 시험 목록을 포함한 Phase 2 회귀 검사를 추가 수행 중.

## Phase 2 구현
- RunOptions와 AppState 도입, 옵션의 유효 모드·표 제외·단계 선택 순수 계산.
- GUI 기존 상태 속성은 AppState 호환 프로퍼티로 연결.
- 브리지 프로파일·분석 상태는 AppState로 접근, 외부 레거시 호스트 어댑터 유지.
- coverage 분석 객체 교체 시 재계산, 명시적 무효화 지원, 반환값 복사로 캐시 오염 방지.
- 설정 마이그레이션은 core로 이관, 기존 docfit_app 경로는 호환 파사드 유지.
- ConfigStore 저장은 기존 파일/프로세스 잠금·원자 저장 구현 재사용.
- 작업 시작 시 RunOptions 스냅샷을 만들고 resolve_stages로 파이프라인 단계 선택을 계산.
- 모든 Tk 설정 변수 자체의 제거는 Phase 4 이후에도 별도 검증이 필요함.

## 원격 알파 7 통합
- 작업 중 GitHub alpha가 6fd5c61로 진행되어 일반 푸시가 거부됨.
- 강제 푸시 없이 별도 작업 트리에서 원격 알파 7 위에 변경을 통합.
- 기존 변환 준비 상태 캐시와 신규 coverage 캐시를 모두 유지.
- 기존 작업 트리의 시각 편집기 변경은 별도로 보존.
- Phase 2 기존 작업 트리 전체 검사: 1,037개, 실패·오류 0개, 건너뜀 3개.
- 최종 실행 단계 옵션 연결을 포함한 알파 7 통합본 전체 검사: 1,050개, 통과 1,047개, 실패·오류 0개, 건너뜀 3개.
- 통합본 compile, Linux import_check, CRLF(26,097줄, 단독 LF 0개) 확인.
- Phase 3~5와 Windows 실제 COM·Flutter 검증은 미완료.

## Alpha 8 후속 완료

Phase 3~5 구현 및 최종 검증은 [완료 보고서](REFACTOR_PHASE3_5_ALPHA8.md)를 참고한다. 위 미완료·시험 수치는 이전 단계의 이력이다.
