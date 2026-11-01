# S8 임시 파일·폴더 분류 (2026-11-01)

범위: 제품 코드(`tests/` 및 개발용 `scripts/` 제외)의 `mkdtemp`, `mkstemp`, `NamedTemporaryFile` 호출 검색. 한 파일에 여러 호출이 있으면 각각 같은 행으로 묶었다. 판단은 호출 문맥과 파일 수명주기를 기준으로 했다.

| 위치 | 용도·분류 | 예외 경로 / 조치 |
|---|---|---|
| `desktop_web_ui.py:1458` | 사용자 선택 경로에 PNG 결과 원자적 교체용 파일 | 사용자에게 반환하는 결과. 기존 `finally` 삭제, 유지 |
| `desktop_web_ui.py:1493` | 사용자 선택 경로에 HWPX 결과 원자적 교체용 파일 | 사용자 결과. 기존 `finally` 삭제, 유지 |
| `docfit_engine/page_fit.py:4625` | 현재 한/글 문서 표 보호 스냅샷 폴더 | COM 문서 스냅샷/기존 정리 흐름, 유지 |
| `docfit_engine/formatter_unify.py:1145` | 현재 문서 HWPX 사전 단계 파일 | COM 처리 결과가 이어 읽음. 주변 제목 임시 폴더 수명주기 사용, 유지 |
| `docfit_engine/formatter_titles.py:1028,1047,1734,1811,1840` | 현재 문서 구조 조사·적용 스냅샷/단계 파일 | 한/글 COM이 파일을 열거나 다시 읽음. 호출부에서 `_제목_임시폴더_정리`로 정리, 유지 |
| `docfit_core/korean_proofread.py:159` | 승인 교정 HWPX 결과 후보 | 사용자 결과로 hard-link 게시. 전체 작업 `finally`에서 후보 삭제, 유지 |
| `docfit_core/file_conversion.py:108` | Pandoc 변환 결과 후보 | 사용자 결과 게시 전 검증용. 내부 `finally` 삭제, 유지 |
| `docfit_core/file_conversion.py:145,281` | 한/글 PDF/HWPX 저장 후보 | COM이 저장·닫기하는 파일. `finally`에서 문서 닫고 후보 삭제, 유지 |
| `docfit_core/file_conversion.py:354,417,445` | HWPX 생성/TXT 내보내기 후보 | 사용자 결과 게시용. `finally` 삭제, 유지 |
| `docfit_core/kordoc_bridge.py:360` | kordoc 변환의 HWPX 결과 후보 | 사용자 결과 게시용. `finally` 삭제, 유지 |
| `docfit_core/pdf_compress.py:176` | 압축 PDF 결과 후보 | 검증 후 사용자 결과로 게시. `finally` 삭제, 유지 |
| `docfit_core/pdf_merge.py:212` | 합친 PDF 결과 후보 | 검증 후 사용자 결과로 게시. `finally` 삭제, 유지 |
| `docfit_core/fidelity/package.py:231` | 패키지 교체 결과 후보 | 사용자 결과 게시, `_publish_new`의 `finally` 삭제, 유지 |
| `docfit_core/xml_hanging_indent.py:604,1021` | HWPX 교정 후보 | 검증 후 사용자 결과 경로로 교체. `finally` 삭제, 유지 |
| `docfit_core/batch_format.py:430` | HWPX 일괄 처리 후보 | 검증 후 사용자 결과 경로로 교체. `finally` 삭제, 유지 |
| `docfit_app/conversion_runner.py:145` | PDF 병합 중 한/글이 만든 임시 PDF 모음 | 예외·취소 후 사용하지 않는 내부 작업물. `TemporaryDirectory` 수명 관리로 변경, 종료 정리 시험 추가 |
| `docfit_core/kordoc_runtime.py:296` | 엔진 설치/업데이트 다운로드 파일 | 별도 설치 단계가 소비하는 파일. 해당 설치 수명주기 및 정리 로직 범위, 유지 |
| `docfit_app/flow_service.py:109` | 사용자 설정 저장 파일의 원자적 교체 후보 | 장기 설정 결과 게시. `finally` 정리, 유지 |
| `docfit_app/table_sketch_service.py:44` | 표 스케치의 서비스 저장 데이터 후보 | 이후 요청에서 읽는 서비스 상태 파일. 원자적 저장, 유지 |
| `docfit_app/table_units_service.py:323,367` | 표 복제/스냅샷 작업 폴더 | 편집 중 표의 재사용 자료. 호출 후속 코드의 명시적 정리 대상, 유지 |
| `docfit_app/settings_service.py:61` | 사용자 설정 파일 후보 | 장기 설정 결과 게시. 문맥 관리자·기존 교체 처리, 유지 |
| `docfit_app/timemachine_service.py:122` | 타임머신 설정 원자적 교체 후보 | 설정 저장 결과. 예외 정리 흐름, 유지 |
| `docfit_app/file_rename_service.py:315` | 파일명 변경 이력 DB 후보 | 장기 이력 데이터 원자적 교체, 유지 |
| `docfit_core/file_rename/history.py:98` | 이름 변경 이력 저장 후보 | 장기 이력 데이터 원자적 교체와 예외 정리, 유지 |
| `docfit_core/hwpx/canvas_package_adapter.py:197` | HWPX 패키지 쓰기 후보 | 검증 뒤 결과 게시. `finally` 삭제, 유지 |
| `docfit_core/timemachine/thumbs.py:252` | 타임머신 썸네일 후보 | 저장 후 서비스 캐시가 읽음. 예외 정리, 유지 |

`scripts/`의 smoke/벤치마크/시각 비교/게시 스크립트 임시 폴더는 제품 런타임 범위가 아니어서 수정하지 않았다. 결과물, 설정·이력, 다른 프로세스/후속 요청이 읽는 자료, 한/글 COM이 열어 두는 파일은 삭제 동작을 바꾸지 않았다.
