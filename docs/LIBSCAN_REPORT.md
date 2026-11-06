# LIBSCAN 구현 보고서 — 자료함(klib) 폴더 증분 스캔·진행률·취소

- 작성일자: 2026-11-07
- 브랜치: `feature/libscan` (기준 github `release/2.2.23`)

## 1. 전제 확인
카드는 "자료함 폴더 스캔을 증분으로"라고 적었으나, klib(Rust)에는 폴더를 훑는 코드가 없었다(`read_dir`은 내보내기 전용). 증분 스캔이 이미 있는 곳은 Python `docfit_app/library_service.py`(4.0-A, `workspace/library.db`)뿐이다. 그래서 klib에 **새로 구현**했다. 기존 Python 서비스는 건드리지 않았다.

## 2. 구현
- `klib/src/scan.rs`(신규, 의존성 추가 없음): `scan_file(box_id, root, path, size, mtime_ns, scanned_at)` 표. 폴더를 훑어 크기·수정 시각(ns)이 같은 파일은 기존 행을 그대로 쓰고(쓰기 없음), 다른 파일만 upsert, 사라진 파일 행은 삭제한다. 원본은 메타데이터만 읽고 열지 않는다.
- 안전: 링크·정션 폴더는 따라가지 않음. 폴더를 읽다 오류가 나면 "사라진 파일 정리"를 건너뜀(일시 오류로 행이 지워지는 것 방지). 같은 자료함의 다른 루트 행은 건드리지 않음. 취소하면 정리도 건너뜀.
- 명령(named pipe): `box_scan {box_id, path}`(백그라운드 스레드로 시작하고 즉시 응답, 동시에 1건), `box_scan_status`(state·phase·discovered·total·processed·added·updated·unchanged·removed·skipped_errors·elapsed_ms), `box_scan_cancel`. 진행률은 폴더 훑기가 끝나 total이 정해진 뒤 processed/total(1000개 배치마다 갱신).
- `main.rs`: 스캔 중에는 60초 유휴 종료 감시가 프로세스를 끝내지 않도록 활동 시각을 갱신.
- Python `library_bridge.ALLOWED_COMMANDS`에 `box_scan`, `box_scan_status`, `box_scan_cancel` 추가.

## 3. 측정 (합성 파일 10,000개)
조건: 임시 폴더, 하위 폴더 100개에 `문서N.hwpx`(0~1KB) 분산. macOS(APFS, 캐시 따뜻함), release 빌드(opt3·lto), 같은 조건 2회 실행. 값은 ms. 측정 도구는 저장소 밖 임시 크레이트(scan.rs를 그대로 포함).

| 구분 | 1회차 실행 | 2회차 실행 | 비고 |
|---|---|---|---|
| 첫 스캔 | 59.7 | 59.1 | 10,000행 추가 |
| 재스캔(변경 없음) 5회 범위 | 29.3~30.4 | 28.3~30.4 | 10,000행 재사용, 쓰기 0 |
| 전체 다시 쓰기(증분 끄기) 5회 범위 | 50.6~56.4 | 51.1~56.7 | 비교 기준선 |
| 1% 변경 + 1% 삭제 후 재스캔 | 38.7 | 38.6 | 갱신 100, 재사용 9,800, 삭제 100 |

- 재스캔은 첫 스캔의 약 51%(약 2.0배), 전체 다시 쓰기의 약 55%(약 1.8배) 시간.
- 시간의 대부분은 폴더 훑기·`stat`이라 증분이 줄이는 것은 DB 쓰기분이다.

한계: **Windows/NTFS 실측이 아니다**(개발 맥 환경). NTFS·백신·콜드 캐시에서는 절대값과 비율이 다를 수 있어, 배포 전 Windows 실기 재측정이 필요하다.

## 4. 시험
- 신규 `scan.rs` 단위 시험 6건(증분 재사용·삭제 정리, 같은 크기·다른 mtime, 취소 시 행 유지, idle 상태, 루트별 정리, 폴더 읽기 실패 시 행 보존)과 `test_klib.rs` pipe 시험 1건(시작·상태·재스캔·삭제·오류·취소 no-op) 모두 통과.
- Python `test_box_scan_commands_are_allowed` 추가.
- 맥에서는 `windows-sys` 링크 때문에 기본 `cargo test`가 링크되지 않아, `RUSTFLAGS="-C link-arg=-Wl,-undefined,dynamic_lookup"`로 시험했다. Windows 경로(`\\`)를 쓰는 기존 시험 12건은 변경 전(HEAD)에도 같은 12건이 실패한다. 전체/전후 비교는 최종 답변 참조.

## 5. 남은 일
- Windows 실기 `cargo test`·재측정.
- UI(Flutter) 연결, 본문 색인과의 연동(변경된 파일만 `index_file`), 한 명령으로 여러 루트 스캔.
- `--request-json` 1회 실행 방식에서는 백그라운드 스캔이 프로세스 종료와 함께 끝난다(앱 브리지는 pipe 사용이라 영향 없음).

## 6. LIBSCAN2 — 앱 연결 (2026-11-07)
- klib: `box_scan`에 `extensions`(선택) 추가, 새 명령 `box_scan_files {box_id, path?, offset?, limit?}`(경로순 결과 목록), `--request-json` 한 번 실행 모드에서 `box_scan`은 끝날 때까지 기다린 뒤 최종 상태를 출력(5절의 한계 해소). 한 번 실행 모드의 DB 경로를 `Path::join`으로 바꿈(Windows 결과 동일).
- Python `docfit_app/library_scan.py`(`FolderScanService`): klib 가능하면 `box_scan`을 쓰고 상태를 폴링, 연결 실패·klib 없음이면 기존 `LibraryService.index`(동작 불변, `progress` 선택 인자만 추가)로 폴백. 폴백 DB는 `%LOCALAPPDATA%\HwpAutoDocFit\library\scan_fallback.db`. klib가 폴더 오류·진행 중이라고 답하면 폴백하지 않고 그 답을 돌려준다.
- `desktop_web_ui.library()`가 `box_scan*` 명령을 이 서비스로 보낸다(개발자 모드 제한 그대로).
- Flutter 자료함 화면: `LibraryScanApi`(선택 인터페이스)·'폴더 스캔' 단추·진행 막대·취소 단추·완료 요약. 위젯 시험 4건 작성.
- 한계: 이 맥에는 Flutter SDK가 없어 Dart 시험·정적 분석을 실행하지 못했다. 폴백의 파일 개수·변경 수는 klib와 달리 추가/갱신을 나누지 못하고 `changed`로만 센다. 폴백은 klib의 box가 필요 없는 대신 자료함 번호를 이름(`box-N`)으로만 구분한다.
