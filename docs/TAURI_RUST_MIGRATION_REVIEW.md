# Tauri + Rust 전환 타당성 검토 (2026-11-05)

## 1. 결론
- **전면 전환은 비권장.** 전환 대상은 "UI 껍데기"가 아니라 23,341줄 단일 파일(`hwp-auto-docfit.py`)에 든 한/글 COM 제어 로직이며, 이 부분은 Rust로 옮겨도 얻는 것이 거의 없고 비용·위험이 크다.
- **부분 전환은 권장(단계적):** ① K에이전트(클립보드·타임머신) = Rust, ② UI 셸 = Tauri(WebView2 재사용), ③ 한/글 COM·문서 변환 엔진 = Python 사이드카 유지.

## 2. 현황 (실측, 2026-11-05 기준)
| 영역 | 규모 | 비고 |
|---|---|---|
| `hwp-auto-docfit.py` | 23,341줄, 함수 887개 | 한/글 COM(win32com) 호출 다수, tkinter GUI(`HwpAutoDocFitGUI`, `LiveStageBoard`) 포함 |
| `docfit_core/` | 약 9,300줄 | 대부분 순수 로직(HWPX XML, 서식 복제, 표 폭, 개조식 변환 등) |
| `desktop_web_ui.py` + `desktop_web/` | 851줄 + HTML/JS | pywebview(WebView2) UI |
| `flutter_ui/` | Dart 약 2,200줄 | Flutter 웹 UI, 전면 이식 진행 중 |
| `tests/` | 약 13,700줄 | unittest, 서식 재현·회귀 기준 자산 |
| 외부 의존 | pywin32, Pillow, defusedxml, pywebview, tkinterdnd2 | 한/글 보안 DLL(`MapoHwpAutoDocFitSecurity.dll`) 레지스트리 등록 |

## 3. 전환 가능성 항목별 평가
| 항목 | Rust 전환 | 판단 |
|---|---|---|
| 한/글 COM 자동화 (HWPFrame.HwpObject, HAction/HParameterSet) | `windows` crate의 `IDispatch`로 가능하나 late-binding 호출을 전부 수작업 작성. win32com의 이름→DISPID 자동 해결·variant 변환·예외 처리를 직접 구현해야 함 | **어려움.** 18개 지점이 COM이고 파라미터셋 접근이 수백 곳. 이득 없음(병목은 한/글 자체) |
| HWPX 처리(zip+XML) | `zip`, `quick-xml` 로 쉬움, 속도 이득 | 가능. 단 defusedxml 수준의 XXE 방어는 quick-xml 설정으로 재확인 필요 |
| 서식 충실도(fidelity) 엔진 | 가능하나 `format_fidelity_pc.py`의 "불일치 0" 기준을 그대로 통과해야 함 | 가능하나 **재검증 비용 큼** |
| tkinter GUI | Tauri 프런트(Web)로 대체 | 이미 Flutter/WebView2 이식 중이므로 방향 일치 |
| 문서 변환 등 외부 도구(kordoc 등) 호출 | `Command` 사이드카 | 쉬움 |
| 보안 DLL 등록(winreg) | `winreg` crate | 쉬움 |
| 배포(PyInstaller exe → Tauri 번들) | MSI/NSIS, 용량 대폭 감소 가능 | 이득. 단 코드서명·SmartScreen 평판은 새로 쌓아야 함 |

## 4. 장단점
**이득**
- 시작 속도·메모리·exe 용량 개선(Python 런타임 제거), 상주 에이전트에 특히 유리.
- 타입 안정성(현재 단일 거대 파일의 회귀 위험 감소).
- 정적 바이너리라 백신 오탐·의존성 설치 문제 감소 가능.

**비용·위험**
- 한/글 COM 호출부 재작성(핵심 자산이자 가장 위험한 부분), 동작 동등성은 한/글 실기로만 검증 가능(Linux CI 불가).
- 테스트 약 13,700줄(unittest)과 회귀 스크립트 재작성 필요. 기존 "재연 100%/불일치 0" 기준을 이전 버전과 교차 비교(`compare_versions_pc.py`)해야 함.
- Tauri 2는 WebView2를 쓰므로 **현재 pywebview/Flutter 웹 UI와 렌더링 계층은 동일**, UI 성능 이득은 제한적. Flutter 웹을 그대로 올리거나 JS로 재작성해야 하며 Dart↔Rust 브리지는 IPC 신규 설계.
- 개발 인력: 현재 AI 에이전트 협업 체계(Codex/Claude 등)는 Python 중심으로 검증되어 있음. Rust 빌드는 MSVC 툴체인·시간이 추가됨.
- 공공기관 PC 환경: Tauri 번들 설치(MSI)가 정책상 막힐 수 있음(현 portable exe와 비교 필요).

## 5. 추천 로드맵
1. **P0 (지금)**: Flutter UI 이식 완료 + `docfit_core`를 순수 함수/CLI(JSON in-out)로 경계 정리. 이 경계가 이후 어떤 전환에도 필요.
2. **P1**: K에이전트를 Rust 독립 exe로 개발(`docs/KAGENT_DESIGN.md`). 전환 역량 검증 겸 첫 Rust 자산.
3. **P2**: Tauri 셸 PoC — Flutter 웹(또는 `desktop_web`)을 올리고 Python 엔진은 **사이드카(PyInstaller exe, stdin/stdout JSON-RPC)** 로 호출. 평가: 시작시간, 메모리, 용량, 설치 정책 통과 여부.
4. **P3 (선택)**: HWPX 순수 처리 모듈(`hwpx`, `table_width`, `fidelity/*`)만 Rust crate로 이식 — 동등성 테스트(동일 입력 → 동일 XML) 통과 시.
5. **COM 제어부는 마지막까지 Python 유지**, 이식하더라도 한/글 실기 회귀를 통과한 뒤에만.

## 6. 예상 공수 (대략, 단일 개발자 기준 추정치 — 실측 아님)
- 전면 전환: 6~12개월 + 기능 동결 필요 → 비현실적.
- P1 K에이전트: 4~6주. P2 PoC: 2~3주. P3 HWPX 코어: 2~3개월.

## 7. 사용자 결정이 필요한 사항
1. 목표가 용량/속도/백신 오탐/유지보수 중 무엇인가? (목표에 따라 P2 필요성이 달라짐)
2. 배포 대상 PC에서 MSI/NSIS 설치가 허용되는가, portable exe만 가능한가?
3. P1(K에이전트 Rust) 먼저 착수 승인 여부.
