# Alpha 10 갱신 코드 리뷰 — 6ac66ef

**후속 상태: R1~R5 해결 완료(소스·Linux 회귀 검증 기준).**
[수정·검증 보고서](REVIEW_FIXES_6ac66ef.md)를 확인한다. 아래는 수정 전 발견 기록이며 Windows 실기기 검증 완료를 의미하지 않는다.

검토일: 2026-10-14. 기준: a5938d1 이후 9개 커밋, 최신 6ac66ef.
범위: 74개 변경 파일의 구조·차이, 실행 컨텍스트, 표 처리, 변환·폐쇄망 배포, Flutter UI와 빌드 경로.
정적 검토와 아래 재현·회귀 시험을 수행했다. 모든 줄의 정확성이나 취약점 부재를 증명하는 감사는 아니다.

**수정 전 판정: P1 2건·P2 3건. 최초 리뷰에서는 기능 코드를 수정하지 않았다. 후속 수정 상태는 위 링크를 따른다.**

## R1 / P1 — 누락된 미리보기 자료가 CI 빌드를 차단

- 위치: flutter_ui/tool/settings_preview.dart:7, flutter_ui/tool/profile_preview.dart:7, build_flutter.ps1:17.
- 두 추적된 진입점이 settings_preview_data.dart를 import하지만 해당 파일은 추적되지 않고 .gitignore로 제외된다.
  scripts/preview_settings.py를 수동 실행한 PC에서만 생기며 CI에는 생성 단계가 없다.
- 깨끗한 최신 작업 트리의 flutter analyze --no-pub 및 CI와 같은 dart analyze --fatal-infos:
  URI 누락 2개·previewSettingsJson 미정의 2개로 실패.
- 영향: build_flutter.ps1이 분석 실패 직후 예외를 던져 웹 빌드·EXE 패키징·꾸러미 업로드를 진행하지 못한다.
  Windows CI 자체 실행 결과를 조회한 것은 아니며 필수 게이트의 실패를 로컬에서 확인했다.
- 수정: 개인정보 없는 기본 미리보기 자료를 추적하거나 모든 분석/빌드 전에 결정적으로 생성한다.
  분석을 느슨하게 하는 대신 새 clone의 자료 생성·분석을 검증한다.

## R2 / P1 — 병합 칸과 빈 열이 있는 표의 글 칸 너비가 0이 됨

- 위치: docfit_core/table_width.py:217, :225.
- _plan_with_empty_columns의 original 배열은 colSpan=1 칸의 폭만 수집한다.
  모든 행에서 병합된 열은 폭이 0으로 남는다. sum(original)을 전체 폭으로 사용해
  빈 열이 표 전체 폭을 예약하고 글 있는 열에는 0이 배분된다.
- 재현: 2행 3열, 각 행 앞 두 열 병합(폭 2000, 제목/본문 있음), 마지막 열은 빈 칸(폭 1000).
  fit_table(table, 10000, HeaderIndex(HEADER))의 실제 결과:

~~~text
is_target=True, is_design_table=False
before = [[2000, 1000], [2000, 1000]]
column_ratios = [0.5, 0.5, 0.0]
changed=True
after = [[0, 9434], [0, 9434]]
~~~

- 영향: 텍스트 보존 검사로는 걸러지지 않는 조판 파손. 결과 문서의 글 칸이 사라질 수 있다.
- 수정: 병합 폭을 포함한 일관된 물리 열 폭을 복원하고 빈 열 비율을 계산한다.
  복원 불가 시 원래 폭 유지/안전 폴백과 로그를 사용한다. 양수 폭·전체 폭 합·병합 폭 합을 검증한다.
- 필수 회귀: 모든 행에서 두 열 병합 + 빈 비고 열, 병합/단일 칸 혼합, 다단 헤더와 모든 열 양수 폭.

## R3 / P2 — 프로필 요소 이동 시 편집한 텍스트가 원래 값으로 표시됨

- 위치: flutter_ui/lib/features/formats/profile_editor.dart:219.
- 새 선택 화면은 선택한 요소의 필드만 생성한다. 다른 요소로 갔다 돌아오면 TextFormField가 재생성된다.
  initialValue는 edits를 반영하는 _current 결과가 아니라 최초 서버 field.value를 사용한다.
- 실제 위젯 재현: 쪽 왼쪽 여백 20mm → 25mm 입력 → 본문 요소 선택 → 쪽 요소 재선택.
  기대 25mm, 실제 20mm. edits에는 25mm가 남으므로 표시 값과 저장 요청 값이 달라진다.
- 원래 화면에도 초기값만 쓰던 코드가 있었으나 이번 선택식 UI는 요소 전환마다 필드가 사라져 일상적인 경로에서 재현된다.
- 수정: initialValue에 _current(node, field)를 사용하거나 컨트롤러를 요소/필드별로 유지한다.
  텍스트 변경→요소 왕복→표시·미리보기·저장 payload 일치 시험을 추가한다.

## R4 / P2 — 캡션 표가 날짜 칸 선행 서식에서 변경됨

- 위치: docfit_engine/formatter.py:1805, docfit_engine/pipeline.py:317.
- 새 보호 규칙은 캡션 표를 보호하지만 표_날짜칸_한줄은 is_design_table만 확인한다.
  캡션만 달린 일반 데이터 표는 통과하고 날짜 셀의 lineWrap을 SQUEEZE로 바꾼다.
- 실제 함수 재현: 캡션 달린 2×2 표의 본문 두 칸 날짜 → 변경 수 2,
  두 subList의 lineWrap이 미지정에서 SQUEEZE로 변경됨. COM 보호 영역 조사보다 먼저 실행된다.
- 영향: 사용자가 꾸민 표의 줄바꿈·글자 폭 조판이 바뀐다. 최신 ‘모든 서식 작업에서 보호’ 계약을 충족하지 못한다.
- 수정: 장식/캡션 판정을 공유하고 날짜 처리에도 적용한다. 바깥 표에서 안쪽 칸을 순회하며 보호를 우회하지 않도록
  표 경계에서 재귀 판정한다. 캡션 표 날짜 칸 XML 유지 시험을 추가한다.

## R5 / P2 — 일반 표 안의 장식 표는 COM 보호 목록에서 빠짐

- 위치: docfit_engine/page_fit.py:4266.
- subList 번호는 root.iter로 전수 수집하지만 표는 section 바로 아래 p/run/tbl만 수집한다.
  일반 표 셀 안의 장식 표·캡션 표는 판정 대상에 도달하지 못한다.
- 실제 메타데이터 재현: 일반 2×2 표 첫 칸 안에 기존 BAR 장식 표(2행·빈 점선 칸)를 넣은 HWPX.
  서식표_영역_목록(path, 장식만=True) 결과는 빈 목록이다.
- 영향: XML 자간 초기화는 중첩 표를 보호해도 COM 자간·문장부호·표 헤더 처리용 디자인표_보호영역에는 해당 칸이 없다.
  Windows COM 결과물 변경은 미검증이며 보호 메타데이터 누락은 재현했다.
- 수정: 중첩 표도 전수 수집하고 보호하는 바깥 표의 하위 영역 포함 규칙을 정한다.
  중첩 장식/캡션 표와 일반 안쪽 표의 구분 시험, Windows 셀 목록 번호 실측 시험을 추가한다.

## 검증 결과

- Python AST/compile 87개, import_check 통과(Windows 전용 임포트 대체). 본체 CRLF 3,323줄 유지.
- Python 전체 1,120개: 통과 1,117개, 조건부 제외 3개, 실패/오류 0개.
  실제 Tk/Xvfb 사용. 제외는 선택형 MCP SDK와 실제 Windows PowerShell·절전 API 시험이다.
- Flutter 전체 48개, 일반 흐름도 모델 6개 통과.
- Flutter/dart 분석은 R1의 오류 4개로 실패. 기존 단위 시험 통과는 빌드 가능성이나 새 경계 조건의 정확성을 뜻하지 않는다.
- 추가 위젯 재현은 R3의 기대 25mm/실제 20mm로 실패함을 확인했다. 임시 파일은 기존 시험 스위트에 남기지 않았다.
- R2/R4/R5는 실제 Python 함수와 최소 XML/HWPX 입력으로 재현했다. 원본 사용자 문서는 사용하지 않았다.
- 로그: /tmp/docfit-review-6ac66ef-python.log, /tmp/docfit-review-6ac66ef-flutter.log,
  /tmp/docfit-review-6ac66ef-dart-analyze.log, /tmp/docfit-review-merged-width.log,
  /tmp/docfit-review-profile-switch.log, /tmp/docfit-review-table-protection.log.
  임시 로그의 장기 보존을 전제로 하지 않으며 입력·출력·위치를 본문에 기록했다.

## 구조·보안·최적화 평가

- 실행 컨텍스트 비교 창 핸들 전달, 레거시 전역 재동기화 범위 축소, 아웃라이너 초기 로딩 입력 보호,
  변환 사본·임시 폴더 정리는 개선이다. 관련 전체 회귀 시험은 통과했다.
- 폐쇄망 기본값, npx 다운로드 제한, 로컬 꾸러미, 고정 npm lock 및 빌드 시 Node SHA-256 확인은 배포 예측성을 개선한다.
  공식 kordoc 4.21.30 공개 패키지의 KORDOC_OFFLINE/KORDOC_MODEL_CACHE 지원도 소스로 확인했다.
- ZIP 경로·총 크기 제한, 원자 이미지 출력, defusedxml/원본 보존 경로를 검토했다.
  확정한 신규 원격 코드 실행 취약점은 없다. 침투시험·전체 의존성 보안 감사 완료를 의미하지 않는다.
- 추가 보강 후보: 런타임 설치 프로세스 간 잠금, 설치 시 배포 해시 검증 자동화, manifest 개별 크기 제한,
  폐쇄망 모드 실제 외부 요청 차단 계측. 이번 재현 결함 5건과 구분한다.
- 표 보호의 모듈별 독립 판정을 공유 정책으로 합치는 것이 우선이다. 전수 순회와 예외/중첩 처리도 같은 계약으로 검증한다.
- Windows 한/글 COM·WebView2·동결 EXE와 실제 폐쇄망 PC 설치는 미실행. 성능 개선률은 실측 근거가 없어 주장하지 않는다.
