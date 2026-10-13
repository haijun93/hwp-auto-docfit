# tldraw 편집기 시험 보고서

시험일: 2026-10-13 · 브랜치 기반: `alpha` `8b83fc8` · 상태: 첫 구현

## 현재 실행 결과

| 시험 | 결과 |
|---|---|
| npm 의존성 설치 | 성공 (`npm install --ignore-scripts`; lock 생성) |
| Vite release bundle | 성공, 947 모듈 / 약 5.0 MB static asset 생성 |
| Node 지원 버전 | 미충족: 로컬 Node 20.13.1, SDK는 Node ≥22.12.0 요구. 빌드는 성공했지만 `EBADENGINE` 경고가 있어 지원 버전 시험은 미완료 |
| Python 다이어그램 저장소 시험 | 이번 구현에서 추가, 아래 회귀시험 실행 대상 |
| Flutter analyze / widget test / Windows build | 미실행: 현재 Windows 개발 셸에서 Flutter/Dart SDK 실행 파일을 찾지 못함 |
| WebView2 실기기·오프라인 실행 | 미실행 |
| 한/글 COM 삽입·원본 보존 | 미실행·미구현 |

## 제한과 후속

- 앱의 Python IPC가 메시지당 1 MiB여서 JSON snapshot은 700 KiB로 제한한다. 이미지 업로드 기능은 기본 제공하지 않는다.
- 번들 크기 때문에 tldraw UI는 첫 로딩이 무거울 수 있다. Windows WebView2에서 시작 시간·유휴 메모리·PNG export·한국어 글꼴을 측정해야 한다.
- editor SDK는 비허용 MIT SDK가 아니다. 개발용 시제품 외 배포는 사용 허가 전까지 금지한다.
- 다음 필수 검증은 Node 22.12+, Flutter 3.47.5, Windows 10 1809+/WebView2 Runtime, 실제 사용자 상호작용, PNG 저장 재열기다.
