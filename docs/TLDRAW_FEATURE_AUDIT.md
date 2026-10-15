# tldraw 편집기 기술·라이선스 감사

검토일: 2026-10-13 · 대상: `alpha` `8b83fc8` 기반 시제품

## 현재 구조와 결정

- 저장소는 1.74 Alpha 6에서 Flutter Windows runner, 토큰 인증 loopback IPC, Python 서비스 계층의 시제품을 추가했다. 문서 처리 엔진 연결은 아직 `engine_ready=false`이며 COM 처리는 기존 Python 앱에 남아 있다.
- tldraw는 React SDK이므로 Flutter Windows 안의 WebView2에서 실행한다. 편집기 정적 파일은 Vite로 빌드해 Flutter asset에 포함하고, 앱이 loopback HTTP 서버로 필요한 asset만 제공한다. 외부 CDN과 런타임 다운로드는 사용하지 않는다.
- WebView 메시지는 JSON으로 교환한다. Flutter 메뉴는 개발자 모드와 `diagram_editor_enabled`가 모두 켜졌을 때만 표시하고, Python `DiagramService`도 모든 저장·열기·삭제 명령에서 두 설정을 다시 확인한다.
- 저장은 `%APPDATA%\HwpAutoDocFit\diagrams\<32자리-hex-id>.json`에 원자적으로 기록한다. JSON 700 KiB 한도, 이름·ID 검증, 임시 파일 후 `os.replace`, 심볼릭 링크 차단을 적용한다. 사용자가 만든 PNG는 시스템 저장 대화상자로 별도 경로에 저장한다.

## 라이선스·외부 통신

tldraw SDK는 MIT가 아니라 자체 tldraw 라이선스다. 기본 조건은 개발 전용이며, 제품 배포·운영에는 평가 trial, 비상업 hobby 또는 상업 commercial license가 필요하다. 오픈소스 저장소에 포함할 수 있지만 SDK 자체 라이선스와 각 사용자의 라이선스 의무는 유지된다. 따라서 이 구현은 **로컬 개발·기술 검증 시제품**이고, 일반 사용자 공개·정식/베타 배포를 승인하지 않는다. 실제 공공기관 배포 성격과 사용 목적을 확정하고 적절한 사용 허가를 받은 뒤에만 배포 빌드에서 편집기를 활성화한다.

- SDK 라이선스: <https://tldraw.dev/community/license>
- SDK license key / 데이터 처리: <https://tldraw.dev/sdk-features/license-key>
- SDK는 Vite 빌드 시 번들된다. trial key를 넣지 않아 trial 분석 ping을 발생시키지 않는다.
- WebView는 loopback 정적 asset 서버만 사용하고 CSP에서 외부 연결(`connect-src 'none'`)을 차단한다. WebView2 Runtime/SDK 자체의 OS 통신은 별도 문제이며 이 정책으로 차단했다고 주장하지 않는다.
- 배포할 때 tldraw 고지와 라이선스 조건을 별도로 포함해야 한다. 재배포물은 라이선스 승인 전 생성하거나 게시하지 않는다.

## 기술 선택 및 제한

- tldraw 5.5.2와 `@tldraw/assets` 5.5.2를 고정했다. 공식 설치·저장·PNG API 문서를 따르며 저장 snapshot에는 SDK migration에 필요한 document/session을 둔다.
- Flutter `webview_windows` 0.4.0은 Dart 3에서 SDK constraint가 맞지 않아 선택하지 않았다. WebView2 통합은 Dart 3.12/Flutter 3.44 이상을 요구하는 BSD-3-Clause `webview_flutter_windows` 1.2.0으로 고정했다. 프로젝트 Flutter lockfile도 이 최소 SDK 범위다.
- Node 빌드 최소 버전은 22.12.0. 이 환경은 Node 20.13.1이므로 번들 빌드는 성공했지만 엔진 버전 경고가 발생했다. Node 22와 Windows/Flutter/WebView2에서의 빌드는 아직 별도 확인이 필요하다.
- 편집 PNG를 HWP 문서에 삽입하거나 기존 삽입 그림을 찾아 교체하는 기능은 구현하지 않았다. COM 개체 안정 식별, 삽입 위치, 원본 무결성은 한/글 실기기 시험 뒤 결정한다.

## 구현 범위

완료한 첫 수직 slice: 개발자 모드 전용 메뉴, 독립 OFF 플래그, 로컬 WebView2 tldraw 캔버스, 10개 예시 흐름, 조건분기 예시, local JSON 저장·열기·삭제, PNG 내보내기. 아직 미완료: 사용 템플릿 즐겨찾기·검색·미리보기, 편집기 자체 단위/E2E 시험, WebView2 실기기 입력/내보내기 점검, HWP 삽입·재편집, Windows 네이티브 전체 앱의 정식 전환.
