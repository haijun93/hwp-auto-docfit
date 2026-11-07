# Tauri + Rust 전환 타당성 검토 (2026-11-07, `main` 기준 개정)

> 개정 사유: 첫 판(2026-11-05)은 로컬 작업 브랜치를 읽고 쓴 것이라 `main`과 달랐다. ① 코드 규모 수치가 `main`과 맞지 않았고(예: "23,341줄 단일 파일") ② K에이전트가 **이미 Rust로 구현**되어 있는데 "새로 개발(4~6주)"로 적었다. 이 판은 `origin/main`(v2.2.31 계열)을 직접 읽어 다시 썼다. 수치는 줄 수 세기·파일 읽기로 확인한 값이며, **빌드·실행·성능 측정은 하지 않았다**(Linux 환경).

## 1. 결론
- **전면 전환은 비권장.** 한/글 COM 제어(약 20개 파일에 분산)를 Rust로 옮겨도 얻는 것이 적고, 동작 동등성은 한/글 실기에서만 검증할 수 있다.
- **부분 전환은 이미 진행 중이며 계속 권장.** Rust 자산이 `main`에 약 9,800줄 있다(K에이전트 약 4,960줄, 자료함·노트북 엔진 klib 약 4,810줄). 다음 후보는 **UI 셸(Tauri) PoC**와 **HWPX 순수 처리 모듈**이다.
- **한/글 COM·문서 변환 엔진은 Python 유지**(필요 시 사이드카 호출).

## 2. 현황 (`origin/main` 실측)
| 영역 | 규모 | 비고 |
|---|---|---|
| `hwp-auto-docfit.py` | 3,500줄 | 진입점·호환 래퍼(분리됨) |
| `docfit_engine/` | 18개 파일, 약 20,200줄 | 한/글 COM 서식 엔진(`com_driver`, `formatter_*`, `pipeline`, `spacing`, `page_fit` 등) |
| `docfit_ui/legacy.py` | 5,802줄 | tkinter GUI(레거시) |
| `desktop_web_ui.py` | 3,435줄 | pywebview 브리지 |
| `docfit_core/` | 약 32,800줄 | 대부분 순수 로직(HWPX XML, 서식 복제, 표, 개조식, 타임머신 등) |
| `docfit_app/` | 약 8,300줄 | 서비스 계층(파일변환·클립보드·K에이전트 연결 등) |
| Flutter UI(`flutter_ui/lib`) | 약 37,000줄 | 전체 화면 이식 진행 중 |
| **Rust** | **약 9,770줄** | `kagent/` 4,957줄 + `klib/` 4,813줄 |
| 테스트(Python) | 약 42,600줄 | unittest, 회귀·서식 재연 기준 자산 |
| COM 직접 사용 파일 | 약 22개(`docfit_engine/*`, `docfit_app/*`, `docfit_ui/legacy.py` 등) | `HAction`·`HParameterSet`·`XHwp` 호출 약 96곳(`docfit_engine`·`docfit_core`·진입점·`docfit_ui` 기준) |

## 3. 이미 구현된 Rust 자산
- **K에이전트 `kagent/`**(몽땅클립보드·타임머신 감시): `main.rs`, `clip.rs`, `popup.rs`, `store.rs`, `timeline.rs`, `watch.rs`, `pipe.rs`, `crypt.rs`, `sqlite.rs`, `json.rs`, `open_item.rs`, `util.rs`. 이벤트 구동 클립보드 감시, DPAPI 암호화, 사용자 전용 파이프 IPC, 네이티브 빠른 목록 팝업, 스크린샷 폴더 감시, 타임머신 색인. 의존 크레이트는 `windows-sys`·`png`뿐, SQLite는 Windows 내장. CI(`build-windows-exe.yml`)가 `cargo test`·`cargo build` 후 `resources/kagent.exe`와 SHA-256을 만든다. 앱 연결: `docfit_app/kagent_client.py`·`kclip_service.py`, Flutter 관리창 `features/kclip/`. 검토: `docs/KAGENT_REVIEW_K1.md`.
- **자료함·노트북 엔진 `klib/`**: 폴더 증분 스캔, 본문 검색, 노트북 변환(`scan.rs`, `search.rs`, `content.rs`, `nb_transform.rs`, `notebook.rs`, `db.rs`, `pipe.rs`).
- TODO 기록상 K에이전트 실측: exe 0.65MB, 유휴 CPU 0%, 개인 메모리 1.8MB, Rust 단위 시험 10건(**이번에 재측정하지 않음**).
- **남은 일(K에이전트)**: 코드 서명(기관 인증서), 누수 장시간 시험(K1), 빠른 목록 개편(상단 메뉴·분류·설정 메뉴), 엑셀 표 변환 연동, "빠른 목록이 비어 보이는" 문제의 Windows 실기 확인, 자동 실행 실기 확인, 기관 PC 허용 목록.

## 4. 전환 가능성 항목별 평가
| 항목 | Rust 전환 | 판단 |
|---|---|---|
| 한/글 COM 자동화 | `windows` crate `IDispatch`로 가능하나 late-binding 호출·파라미터셋 접근을 직접 구현(win32com의 이름→DISPID 해결·variant 변환·예외 처리 대체) | **어려움, 이득 없음.** 병목은 한/글 자체이며 검증은 실기에서만 가능 |
| HWPX 처리(zip+XML) | `zip`·`quick-xml`로 쉬움, 속도 이득 | 가능. XML 외부 개체(XXE) 방어는 defusedxml 수준으로 재확인 필요. 서식 재연 "불일치 0" 기준 재통과 필요 |
| 상주 감시·빠른 목록 | **이미 Rust(`kagent`)** | 완료 영역. 개선만 남음 |
| 폴더 스캔·검색 엔진 | **이미 Rust(`klib`)** | 완료 영역 |
| tkinter GUI(`legacy.py`) | Tauri/Flutter 프런트로 대체 | Flutter 이식과 같은 방향 |
| 배포 | MSI/NSIS, 용량 감소 | 코드서명·SmartScreen 평판·기관 설치 정책 확인 필요(현 portable exe와 비교) |

Tauri 2도 WebView2를 쓰므로 현재 pywebview/Flutter 웹 UI와 렌더링 계층은 같다. UI 성능 이득은 제한적이고, Dart↔Rust 브리지(IPC)를 새로 설계해야 한다.

## 5. 장단점
**이득**: 시작 속도·메모리·용량 개선 가능, 타입 안정성, Python 런타임 제거 시 백신 오탐·의존성 문제 감소, **이미 쌓인 Rust 빌드·CI·서명 파이프라인 재사용**.
**비용·위험**: COM 호출부 재작성(핵심 자산이자 가장 위험), 한/글 실기 검증 필수, 테스트 약 42,600줄과 회귀 스크립트의 재작성·교차 비교(`compare_versions_pc.py`), Python 중심 AI 협업 검증 체계, 기관 PC에서 설치형(MSI) 차단 가능성.

## 6. 추천 로드맵 (개정)
1. **P0 — 진행 중**: Flutter 이식 마무리, `docfit_core`·`docfit_engine`을 입력→출력(JSON) 경계로 정리. 이미 `docfit_engine/` 분리가 되어 있어 경계 설정은 첫 판 가정보다 앞서 있다.
2. **P1 — 구현 완료, 잔여 작업만 진행**: K에이전트(Rust). 위 §3 "남은 일"을 진행한다. (첫 판의 "신규 개발 4~6주"는 삭제)
3. **P2 — 다음 후보**: **Tauri 셸 PoC** — Flutter 웹(또는 `desktop_web`)을 올리고 Python 엔진은 **사이드카**(stdin/stdout JSON-RPC)로 호출. 평가: 시작 시간, 메모리, 용량, 설치 정책 통과 여부, 이미 Rust인 `kagent`·`klib`과의 연동 방식(기존 파이프 IPC 재사용).
4. **P3 — 선택**: HWPX 순수 처리 모듈(`hwpx`, `table_width`, `fidelity/*`)만 Rust crate로 이식. 동일 입력→동일 XML 통과 시.
5. **COM 제어부는 마지막까지 Python 유지**, 이식하더라도 한/글 실기 회귀 통과 후에만.

## 7. 예상 공수 (추정치, 실측 아님)
- 전면 전환: 6~12개월 + 기능 동결 → 비현실적.
- P1 잔여 작업: 개별 TODO 기준(빠른 목록 개편 5~8주 추정 등 별도 문서 참고).
- P2 PoC: 2~3주. P3 HWPX 코어: 2~3개월.

## 8. 사용자 결정이 필요한 사항
1. 목표가 용량/속도/백신 오탐/유지보수 중 무엇인가? (P2 필요성에 영향)
2. 배포 대상 PC에서 MSI/NSIS 설치가 허용되는가, portable exe만 가능한가?
3. P2(Tauri PoC) 착수 여부. (첫 판의 "P1 착수 승인" 항목은 P1이 이미 구현되어 삭제)
