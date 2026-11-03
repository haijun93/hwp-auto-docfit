# 스프린트 01 — 타임머신 연관 검색·작성 기준일 품질 보강

- 기간: 2026-11-03 / 브랜치: `alpha` / PM: 오케스트레이터 에이전트
- 근거: `TODO.md` 타임머신 추가 요구 중 "작성 기준일 기반 정렬", "연관도 근거와 수정"

## 1. 목표

PM 사전 조사에서 확인한 결함을 고치고, 기준일을 어디서 얻었는지(근거)를 사용자에게 보여 준다.

| # | 확인된 문제 | 위치 |
|---|---|---|
| P1 | Windows 경로(`C:\a\b.hwpx`)에서 선택 문서 이름을 `path.rsplit("/")`로 구해 **폴더 경로 전체가 이름으로 쓰임** → 폴더명 단어가 연관 점수에 섞임 | `docfit_core/timemachine/related.py` |
| P2 | 연관 근거(`reasons`)가 사전 목록인데 화면이 `join`으로 그대로 이어 붙여 `{type: terms, …}`가 노출됨 | `flutter_ui/lib/features/timemachine/timemachine_screen.dart` |
| P3 | 기준일 추출 패턴 중복(분기 패턴 2번, 3요소 분기 2번), 상반기·하반기 미지원, 패턴 순서대로만 찾아 본문 앞쪽의 실제 기준일보다 뒤쪽 분기 표기가 이길 수 있음 | `docfit_core/timemachine/content_search.py` |
| P5 | (아키텍트 발견) 서비스가 연관 항목의 `path`를 응답에서 지워 화면의 "연관 아님" 버튼이 아무 동작도 하지 않음. 위젯 시험의 가짜 응답에는 path가 있어 잡히지 않음 | `docfit_app/timemachine_service.py:438-440`, 화면 |
| P4 | 기준일의 출처(명시된 `기준일` / 분기·반기 추정)를 구분하지 않아 화면에서 근거를 알 수 없음 | 코어·서비스·화면 |

## 2. 수락 기준

- [x] 백슬래시·슬래시 경로 모두에서 선택 문서 이름이 파일명만으로 계산된다(시험).
- [x] 기준일 추출: 명시 기준일 > 분기 > 반기 우선, 같은 종류면 본문에서 먼저 나온 것, 잘못된 날짜는 건너뜀(시험).
- [x] 연관 결과 항목과 선택 문서에 기준일 출처가 함께 나온다(기존 키 유지 — 하위 호환).
- [x] 화면에 근거가 사람이 읽는 문장(예: `공통 업무·사업 단서: 예산, 집행`)으로 표시되고, 기준일 출처가 보인다.
- [x] 전체 시험 통과(리눅스에서 가능한 범위), 기존 타임머신 시험 71개 회귀 없음.

## 3. 설계 (아키텍트)

- **기준일 출처**: `extract_reference_date_info(text) -> {date, source(explicit|quarter|half|None), text}` 신설, 기존 `extract_reference_date`는 래퍼로 유지. 패턴 3종(명시 기준일·분기·반기)으로 정리, 종류 우선 → 같은 종류는 먼저 나온 것, 잘못된 날짜는 건너뜀. 반기는 상반기 6/1·하반기 12/1(분기 규칙 `date(y, q*3, 1)`과 일관). 연도만 있는 표기는 미지원(오탐 위험).
- **DB 스키마 불변**: 연관 검색 때 본문에서 다시 추출(후보 본문을 이미 읽으므로 비용 작음, 마이그레이션 없음).
- **후보 기준일**: `"기준일" not in body` 글자 검사 → `source == "explicit"`로 교체. 정렬은 명시 기준일만 사용, 추정값은 `estimated_reference_date`로 따로 표시.
- **경로 이름(P1)**: 색인에 저장된 `name` 사용, 없으면 `ntpath.basename`.
- **응답 계약(하위 호환)**: 기존 `reference_date`·`reference_date_found` 유지 + `reference_date_source`·`reference_date_text`(최상위·항목), `estimated_reference_date`(항목), 각 reason에 서버가 만든 `text` 문장.
- **PM 결정(P5)**: 경로를 노출하지 않는 원래 의도를 지키기 위해 서비스가 항목마다 불투명 `related_id`를 발급(서비스 인스턴스 안 대응표)하고 `related_exclude`가 `related_id`를 받는다. 기존 `related_path` 입력도 계속 받는다.
- 반기 거리 계산(`_PERIOD`)은 반기를 분기 2·4로 환산해 같은 축에서 비교.

## 4. 작업 목록

| ID | 내용 | 담당 | 파일 소유 | 상태 |
|---|---|---|---|---|
| S01-T1 | 기준일 추출 정리·출처 반환, 연관 검색 경로 버그(P1·P3·P4) | 개발자(코어) | `docfit_core/timemachine/content_search.py`, `related.py`, `tests/test_timemachine_related.py`, `tests/test_timemachine_content_search.py` | 완료 |
| S01-T1b | `related_id` 발급·제외 요청 수정(P5) | 개발자(코어) | `docfit_app/timemachine_service.py`, `tests/test_timemachine_service.py` | 완료 |
| S01-T2 | 연관 근거·기준일 출처 표시 | 개발자(화면) | `flutter_ui/lib/features/timemachine/*`, `flutter_ui/test/timemachine_screen_test.dart` | 완료 |
| S01-T3 | 검토·시험 | 리뷰어 | (읽기 전용) | 완료(조건부 통과 → 반려 1회 → 수정) |

## 5. 검토 결과

1차 판정: **조건부 통과**. 반려 1회 뒤 수정 완료, PM 재검증(타임머신 시험 117개 통과).

| 심각도 | 위치 | 문제 | 처리 |
|---|---|---|---|
| 중간 | `timemachine_screen.dart` 연관 아님 | `related_exclude`가 거절(`ok:false`)돼도 조용히 무시 — `related_id` 만료(서비스 재시작·1000개 초과) 시 무반응 | 수정: 대화상자 안에 오류 문구 표시 + 위젯 시험 |
| 낮음 | `content_search.py` 명시 기준일 | 원문 text의 끝 `.`·`월` 누락 | 수정 + 시험 |
| 낮음 | `content_search.py` 명시 기준일 | `9. 301`을 30일로 판정(숫자 경계 없음) | 수정(`(?!\d)`, 그 일치 무시) + 시험 |
| 낮음 | 기준일·기간 패턴 | `2026년 1/4분기` 표기 미인식(기존과 같음) | 다음 스프린트 후보 |
| 참고 | `tests/test_timemachine_service.py` | `test_scan_refreshes_only_existing_content_index_and_removes_deleted` 간헐 실패(HEAD에서도 재현, 약 1/20) | 별도 과제 |

규칙 점검: 표준 xml import 없음, 줄바꿈 형식 유지, 배정 밖 파일 수정 없음.

## 6. 실기 확인 필요(Windows)

- Flutter 위젯 시험(`flutter test test/timemachine_screen_test.dart`) — 이 컨테이너에 Flutter SDK 없음
- `flutter analyze`(이 환경에서 Dart 코드는 정적 검토만 함)
- 실제 Windows 경로 색인 후 연관 문서 대화상자 표시(파일명만 사용, 근거 문장·기준일 출처)
- 앱 재시작 후 기존 대화상자에서 "연관 아님" → 오류 문구 표시
- `release/2.2.11`과 합칠 때 `timemachine_service.py`·`timemachine_screen.dart` 충돌 확인
