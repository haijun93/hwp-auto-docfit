# Alpha 10 — 6ac66ef 리뷰 5건 수정

작성일: 2026-10-14. 기준: 6ac66ef 코드 및 f22bc22 검토 보고서.
범위: P1 2건·P2 3건 수정. 앱 판은 1.74 Alpha 10을 유지한다.

## 변경 내용

| 항목 | 변경 | 회귀 검증 |
|---|---|---|
| R1/P1 미리보기 import 누락 | 두 도구가 추적되는 preview_data.dart의 공개 기본 자료를 사용. 개별 설정/프로필 자료는 임시 JSON과 --dart-define-from-file로만 전달 | 새 작업 트리 상태에서 생성 파일 없이 dart 분석. 정상/실패 빌드의 임시 자료 정리와 사용자 프로필의 추적 소스 미기록 시험 |
| R2/P1 병합 칸 너비 0 | 빈 열의 비율 분모에 병합 칸을 포함한 완전한 행의 실제 폭 사용. 불확실한 구조, 0 이하 폭, 전체 폭 불일치는 원래 표 유지 | 2행 3열 앞 두 열 병합+빈 열, 병합 머리글/단일 본문 혼합, 불완전 구조 무변경 |
| R3/P2 요소 전환 표시값 | TextFormField 최초 값을 현재 edits와 서버 값을 합친 _current 결과로 설정 | 여백 20mm→25mm→다른 요소→복귀: 표시·미리보기·저장 요청 모두 25mm |
| R4/P2 캡션 날짜 칸 변경 | 공통 is_protected_table 및 보호 경계에서 멈추는 셀 순회 도입. XML 자간 초기화도 같은 판정 사용 | 캡션 표의 날짜 XML 무변경. 일반 바깥 표의 날짜는 처리하면서 안쪽 보호 표는 유지 |
| R5/P2 중첩 보호 누락 | 모든 깊이의 표를 조사. 보호 표 아래의 모든 subList(중첩 일반 표·캡션 글 포함)를 보호 | 중첩 장식/캡션 표, 보호 바깥 표의 하위 칸, 캡션 글 목록, 실제 자간 엔진 제외 판정 |

기존 두 열 병합 글 칸 폭 2000/빈 열 1000의 재현 입력은 본문 폭 10000 처리 후
글 칸 6290/빈 열 3144로 유지된다(바깥 여백 제외 총 9434).
일반 칸과 보호 칸을 함께 검사해 전체 작업을 건너뛰어 시험을 통과하지 않도록 했다.

## 호환성과 배포

- 본체 함수 re-export와 실행 컨텍스트 계약 유지. 본체 CRLF 유지.
- 예전 미리보기 생성 자료 파일은 개인 자료의 우발적 추적을 막기 위해 계속 ignore하지만 현재 빌드에서 필요하지 않다.
- preview_data.dart에는 기본 설정과 일반 예시만 포함한다. 실제 사용자 프로필을 이 파일에 쓰지 않는다.
- Flutter 운영 웹 번들을 다시 빌드하고 로컬 CanvasKit·글꼴·사용권과 엔트리포인트 검사를 수행한다.
- 새 XML 파싱은 defusedxml을 유지하며 사용자 원본 문서는 시험에 사용하지 않았다.

## 최종 검증

- AST/compile: 본체·브리지·도메인/엔진/UI/앱/인프라·시험·미리보기 빌드 스크립트 242개 통과.
- import_check 통과(Windows 전용 임포트만 대체), 본체 CRLF 3,323줄 유지.
- Python 전체 1,132개: 통과 1,129·조건부 제외 3·실패/오류 0. 실제 Tk/Xvfb 사용.
  제외는 선택형 MCP SDK 및 실제 Windows PowerShell·절전 API 시험이다.
- Flutter 전체 49개 통과. dart analyze --fatal-infos 및 flutter analyze --no-pub 지적 사항 0개.
- Flutter 운영 웹 release 빌드 및 entrypoint/한글 글꼴/사용권/로컬 CanvasKit 검사 통과.
- 흐름도 모델 시험 6개 통과.
- 최종 웹 번들 + 실제 Python 저장소: 일반 모드·Flutter iframe·저장·PNG 출력·재열기·삭제 통과.
  tldraw 저장소가 생성되지 않았고 페이지 오류 0건.
- 생성된 settings_preview_data.dart가 없는 상태에서 분석 게이트를 통과했다.
- 로그: /tmp/docfit-fix-6ac66ef-python-release.log, /tmp/docfit-fix-6ac66ef-dart-analyze.log,
  /tmp/docfit-fix-6ac66ef-flutter.log, /tmp/docfit-fix-6ac66ef-build.log,
  /tmp/docfit-fix-6ac66ef-browser.log. 임시 로그의 장기 보존에 의존하지 않는다.

Windows 한/글 COM·WebView2·동결 EXE 및 실제 폐쇄망 PC 실행은 이 Linux 환경에서 검증하지 못했다.
COM 보호 영역의 수집과 자간 제외 판단은 실제 엔진 함수·최소 HWPX 및 COM 포트 대체 객체로 검사했다.
웹 빌드의 미사용 CupertinoIcons 글꼴 탐색 경고는 기존부터 존재하며 필수 MaterialIcons/한글 글꼴 검사는 별도로 확인한다.
