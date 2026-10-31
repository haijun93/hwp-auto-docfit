# K1 검토 보고서 — K에이전트 결함 수정 및 누수 스트레스 검토

이 문서는 과제 K1에 따른 K에이전트(`kagent.exe`, Rust) 코드 검토 결과, 결함 수정 내역, 보류(유지) 항목 근거 및 누수 스트레스 측정 명세를 정리한 보고서입니다. 선임 프로그래머의 1·2·3차 검수 지적 사항을 전수 반영하여 보강되었습니다.

---

## 1. 검토 및 수정 내역 요약 표

| 영역 | 발견(근거 / 재현) | 수정 내용 | 남긴 항목과 이유 (보류/유지) | 시험 근거 |
|---|---|---|---|---|
| **Rust 2024 / coroutines 예약 키워드 충돌** | `kagent/src/main.rs:250, 278`<br>식별자 `gen` 사용으로 인해 최신 stable Rust 툴체인에서 예약어 컴파일 에러 발생. | 식별자 `gen`을 비예약어 `generation`으로 변경하여 컴파일 정상화. | 세대 번호 기반 stale 방지 아키텍처 및 동작 유지. | `main.rs::tests::timeline_generation_stale_detection` |
| **워처 thread spawn 실패 시 E0382 및 리소스 누수** | `kagent/src/watch.rs:117-184`<br>1. `dirs`가 move 클로저로 이동된 후 spawn 실패 분기에서 다시 borrow되어 E0382 컴파일 에러 발생.<br>2. 이벤트 지속 발생 시 `pending`/`overflow`가 상한 없이 커질 수 있음. | 1. `Dir`에 `Drop` 트레이트를 구현하여 스레드 정상/비정상 종료 및 실패 시 열려 있는 디렉터리 핸들이 자동 닫히도록 개선. 스레드 spawn 실패 분기에서는 `dirs` 접근 없이 `port`만 명시적으로 닫아 E0382 해결.<br>2. `MAX_PENDING_CHANGES = 1000` 상한 도입 및 도달 시 즉시 flush. 버퍼 overflow 시 해당 폴더의 세부 변경을 `pending`에서 압축 제거하여 메모리 점유 방지. | 정상 감시 루프의 IOCP 기반 이벤트 대기 및 디바운스 동작 유지. | `watch.rs::tests::restart_empty_roots_cleans_up` |
| **미사용 변수 경고** | `kagent/src/clip.rs:480`<br>`total_pixels` 변수가 선언된 후 사용되지 않아 컴파일 경고 발생. | `match w.checked_mul(h)` 결과의 범위 검증만 수행하도록 수정하여 경고 제거. | 최대 DIB 픽셀 상한 검증 유지. | `clip.rs::tests::png_to_dib_checked_size` |
| **타임라인 잠금 장기 보유 및 워커 직렬화** | `kagent/src/main.rs:146-207`, `266-278`<br>색인 스레드가 `timeline` Mutex를 잡고 장시간 `scan_root()`를 수행하면 워처 스레드(`apply`) 및 창 스레드(`write_status`)의 timeline lock 접근이 차단되어 메시지 루프 지연 발생. 또한 빈 루트 설정 시 stale 스캔이 새로운 상태를 덮어쓸 위험 존재. | 1. 전용 `kagent-timeline` 백그라운드 워커 스레드 도입하여 모든 DB I/O(Reconfigure, ScanRoot, Apply)를 단일 큐로 직렬화.<br>2. 세대 번호(`timeline_generation: AtomicU64`)를 발급하여 설정 변경 전 세대의 stale 작업 즉시 폐기.<br>3. `write_status()`의 동기 DB `count()` 조회를 제거하고 `timeline_files: AtomicI64` 원자 스냅샷으로 O(1) 조회. | 개별 파일 감시 이벤트의 DB 저장은 전용 워커에서 배치/순차 처리되므로 SQLite 동시성 충돌 없음. | `main.rs::tests::timeline_scan_pending_deduplicates_root`<br>`main.rs::tests::timeline_generation_stale_detection` |
| **팝업 이중 잠금 및 Stale 결과 방지** | `kagent/src/popup.rs:40-70`, `104-160`<br>`show()`/`refresh()`의 STATE 및 recent 중첩 잠금 해소 후에도, 비동기 검색 도중 사용자 입력 변경 시 이전 검색어가 최신 결과를 덮어쓸 수 있는 stale 덮어쓰기 위험 존재. | 1. `State` 구조체에 `seq: u64` 순서 번호 추가.<br>2. `refilter()` 및 `show()` 시작 시 `seq`를 증가시키고, DB 검색 후 `seq`와 `needle` 일치 여부를 검증하여 stale 결과를 조용히 폐기. | 검색 limit 50, 빈 검색 최근 목록, IME 조합 문자 처리는 정상 동작하므로 유지. | `popup.rs` 순서 번호 검증 코드 검토. |
| **GDI 리소스 누수 방지** | `kagent/src/popup.rs:227-301`<br>`paint()` 내에서 GDI 객체 생성 실패 시 일부 리소스 해제 누락 위험 존재. | RAII `PaintGuard` 도입. DC/비트맵/폰트 생성 실패 검증 및 스코프 종료(`Drop`) 시 `SelectObject` 복원, `DeleteObject`, `DeleteDC`, `EndPaint`를 확정 일괄 해제. | 정상 화면 폰트, 색상, 12줄 페이징 레이아웃 유지. | 스트레스 스크립트의 `GetGuiResources(GDI)` 누수 검증. |
| **DIB 산술 경계, 픽셀 상한 및 알파 선형화** | `kagent/src/clip.rs:130-141`, `338-430`<br>1. HDROP 10,000개 초과 시 조용히 잘려 복원되는 문제.<br>2. 20,000² 치수 시 수 GB 할당 및 DoS 위험, 32bpp 순회 2회 반복으로 인한 비효율. | 1. `MAX_HDROP_FILES = 10,000` 초과 시 전체 캡처를 명시적 거부(`None`).<br>2. `MAX_DIB_PIXELS = 16M`(4096×4096) 상한 도입하여 거대 메모리 할당 차단.<br>3. `dib_to_png`에서 픽셀 메모리를 단 1회 선형 순회(Single-pass)하며 알파 검사와 변환을 동시 수행. | 24비트 stride 패딩 및 bottom-up/top-down, 32비트 BGRA 변환 호환성 유지. | `clip.rs::tests::dib_layout_rejects_overflow_and_bad_dimensions`<br>`clip.rs::tests::png_to_dib_checked_size` |
| **서식 묶음 부분 파싱** | `kagent/src/clip.rs:206-237`<br>`unpack_formats`가 중간 항목 손상 시 이미 파싱된 앞부분만 반환하여 복원 시 부분 서식만 조용히 적용되는 문제. | `checked_add`와 `data.get()` 슬라이스 경계 검사 적용. count > 16 거부 및 잔여 바이트 소진 불일치 시 빈 `Vec` 반환. | `pack_formats` 레이아웃 및 HTML/RTF 묶음 호환성 유지. | `clip.rs::tests::unpack_formats_rejects_truncated_and_trailing_data` |
| **타임라인 경로 탐색 및 Win32 Alias 차단** | `kagent/src/timeline.rs:221-269`, `319-345`<br>상대 경로 인자가 `..\\outside.pdf`, 절대 경로, UNC 외에도 Win32 정규화 alias(장치명 `CON`, `NUL`, 끝 마침표/공백, ADS `:`)를 통해 루트 밖을 가리킬 위험. | `safe_relative_path`에 DOS 예약 장치명(`CON`, `PRN`, `AUX`, `NUL`, `COM1..9`, `LPT1..9`), 세그먼트 끝 마침표/공백, `?` 와일드카드 및 ADS 거부 로직 추가. | 정상 단일 파일명 및 하위 상대 경로(`sub\\file.pdf`) 허용 유지. | `timeline.rs::tests::apply_rejects_absolute_and_traversal_paths` |
| **단일 실행 뮤텍스 수명** | `kagent/src/main.rs:665-688`<br>`CreateMutexW` 반환 핸들을 지역 변수로 보관하지 않고 버려 명명된 뮤텍스 객체가 조기 파괴될 수 있는 문제. | `instance_mutex` 핸들을 보관하고 중복 인스턴스 경로에서는 새 핸들을 명시적으로 `CloseHandle` 후 기존 프로세스에 알림 전달. 메시지 루프 종료 시 `CloseHandle` 호출. | 단일 인스턴스 명칭(`Local\\HwpAutoDocFit.kagent`) 및 중복 감지 유지. | 단일 인스턴스 격리 검증. |
| **파이프 보안 및 DACL** | `kagent/src/pipe.rs:67-85, 113-131` | (수정 불필요) 현재 사용자 SID 및 Local System만 허용하는 DACL SDDL, `PIPE_REJECT_REMOTE_CLIENTS`, 64KB 초과 요청 즉시 거부 로직이 이미 견고히 구현됨. | 기존 안전한 구현 유지. | 기 작성된 IPC 보안 계약. |
| **JSON 파서 깊이 제한** | `kagent/src/json.rs:134-166, 278-293` | (수정 불필요) 최대 중첩 깊이 64 제한 및 초과 시 파싱 오류 처리가 기 구현되어 있음. | 기존 안전한 구현 유지. | `json.rs::tests::depth_limit` |
| **previews 캐시 수명** | `kagent/src/store.rs:160-164, 262-287` | (수정 불필요) `recent()` 호출 시 DB에 남아있는 ID 집합을 기준으로 `retain()`하여 삭제된 항목의 preview 캐시를 즉시 해제함. | 기존 안전한 메모리 해제 유지. | `store.rs` 테스트. |
| **restore 자기 쓰기 무시** | `kagent/src/main.rs:565-580` | (수정 불필요) `GetClipboardSequenceNumber`를 `self_seq`에 원자적으로 기록하여 자기 자신이 클립보드에 쓴 이벤트를 안전하게 무시함. | 기존 동작 유지. | `benchmark_pc.py`의 `restore_not_recorded_again`. |

---

## 2. 누수 스트레스 측정 스크립트 명세 (`scripts/kagent_stress_pc.py`)

- **단일 인스턴스 격리 및 안전 중단**:
  - 측정 전 `check_existing_instance()`로 기존 `Local\HwpAutoDocFit.kagent` 뮤텍스 및 윈도우 창 존재를 확인.
  - 기존 인스턴스 발견 시 사용자 데이터 격리 및 원래 설정 보호를 위해 프로세스 실행 및 IPC(`settings_set`/`quit` 등)를 일체 수행하지 않고 즉시 예외로 안전 중단.
- **주기별 부하 생성**:
  - 80ms 간격: 텍스트(한글 50자 반복), 32×32 DIB 비트맵, 임시 파일 경로(`CF_HDROP`)를 번갈아 클립보드에 복사.
  - 30초 간격: 보조 프로세스를 실행하여 팝업 표시를 트리거하고, 팝업 윈도우 핸들(`HwpAutoDocFit.KAgentPopup`)의 가시성을 검증한 뒤 `SendInput(Esc)` 전송 및 닫힘을 확인(시간 초과 시 오류 기록).
  - 30초(quick)/60초(일반) 간격: `settings_get`으로 읽은 설정 객체를 `settings_set(settings=...)`로 다시 전달하여 디렉터리 감시 재시작.
  - 30초(quick)/60초(일반) 간격: 타임라인 감시 대상 임시 fixture 폴더에 파일 생성 및 삭제 반복.
- **자원 추적 및 API 오류 엄격 검증**:
  - WorkingSetSize (작업 집합)
  - PrivateUsage (개인 메모리 바이트)
  - GetProcessHandleCount (핸들 수)
  - GetGuiResources (GDI 오브젝트, USER 오브젝트): 호출 전 `SetLastError(0)` 후 반환값 0 및 에러 발생 시 `valid=False` 처리.
- **판정 기준 (과제 원문 및 설계서 §3 일치)**:
  - quick 모드(`--quick`): 과제 지시서 원문에 따른 1분(60초) 측정. 초기 0초 표본을 기준(baseline)으로 삼고 60초 종료 표본(end)과 비교 (`quick_baseline: "initial"` 기록).
  - 일반 모드(`--minutes 10`): 처음 1분(60초) 시점 이후 첫 표본을 baseline으로 삼고 마지막 종료 표본(end)과 비교.
  - 최소 표본 요건: 표본 부족 또는 기준 표본 이후 종료 표본이 없을 시 FAIL.
  - 표본 수집 주기 편차 검증: 인접 표본 간격이 15~45초를 벗어날 경우 FAIL.
  - 필수 스트레스 단계 요건: 클립보드 복사, 팝업, 설정 재시작, 타임라인 파일 변경 최소 수행 횟수 미달 또는 예외 발생 시 FAIL.
  - PASS 조건: PrivateUsage 증가량 < 1 MiB (1,048,576 바이트), HandleCount 증가량 < 20, GDI 오브젝트 증가량 < 20.
- **원 설정 복원 및 정리**:
  - 스트레스 측정 종료 시(정상/예외 불문), 원래의 `timeline_roots` 설정을 `settings_set`으로 복원하고 감시 재시작을 확인한 뒤 프로세스를 종료하고 임시 폴더 삭제.

---

## 3. 검수 단계 실행 및 실측 결과 (검수자 기록 영역)

> **[검수 안내]**: 코더 역할 지침에 따라 실제 명령 실행은 수행하지 않았으며, 아래 검수 명령을 검수자(Windows PC 환경)가 실행한 뒤 결과를 이 영역에 기록합니다.

### 3.1 실행 명령
```powershell
# 1. Rust release 단위 시험 (총 22건)
%USERPROFILE%\.cargo\bin\cargo.exe test --release --manifest-path kagent/Cargo.toml

# 2. Python 단위 시험
python -m unittest discover -s tests

# 3. K에이전트 퀵 스트레스 누수 측정
python scripts/kagent_stress_pc.py kagent/target/release/kagent.exe --quick
```

### 3.2 검수 결과 기록

#### Cargo 및 unittest 실행 결과:
```
[검수 단계에서 실행 후 출력 로그를 여기에 붙입니다]
```

#### Stress quick 측정 결과 JSON (`reports/kagent-stress-*.json`):
```json
[검수 단계에서 생성된 스트레스 측정 결과 JSON 전체를 여기에 붙입니다]
```
