# Flutter 알파 UI

Material 3 기반 Flutter Web 화면을 기존 WebView2 창에 포함합니다.
Python/한글 COM 처리부는 `DesktopWebBridge`를 통해 연결합니다.
파일·폴더 선택, 텍스트 입력, 작업 방식, 쪽 범위, 진행 상태, 결과,
중단, 다음 작업을 지원합니다. 설정 화면에서 작업로그·무결성검사·최종검수 파일 저장,
서식통일 결과 창, 항상 위 표시를 포함한 자주 쓰는 설정을 바꿀 수 있습니다.
전체 설정 대화상자도 Flutter에서 검색·수정·기본값 복원을 지원합니다. 서식 세부 분석·일부 문서 검토·승인 대화상자는 기존 Tk 창을 유지하고 있어, 앱 전체 UI의 100% Flutter 전환은 아직 완료되지 않았습니다.

알파에는 네 번째 **파일포맷 변경** 작업이 있습니다. 카드를 선택하거나 이 모드에서 파일을 추가하면 별도 플로팅 포맷 선택창이 열립니다. Filee를 참고한 도넛 메뉴에서 HWPX/PDF/DOCX/EPUB를 고르면 창이 닫히고 선택이 반영됩니다. 가운데 버튼·Esc·창 바깥 클릭은 기존 선택을 유지한 채 취소합니다. `변환 포맷 선택` 버튼으로 다시 열 수 있습니다. 앱 내부의 플로팅 창이며, Filee의 시스템 전체 드래그 감시·앱 바깥 최상위 창은 구현하지 않습니다.

**HWPX → PDF는 앱에 구현된 한/글 내장 PDF 저장을 직접 사용합니다.** 기존 필수 환경인 한/글 2020 COM 외에 Node.js·kordoc·Pandoc·PDF 프린터를 설치할 필요가 없습니다. 한/글 렌더러를 사용하며 결과는 별도 파일에 저장합니다.

나머지 변환의 입력은 kordoc 4.21.30이 지원하는 HWP/HWPX/HML/PDF/XLS/XLSX/DOCX/PPTX/PNG/JPG/JPEG/WebP입니다. Node.js 20 이상과 kordoc 설치가 필요합니다. 앱은 실행 중 패키지를 임의로 내려받지 않으며, 기본 설치 위치는 `%APPDATA%\HwpAutoDocFit\kordoc`입니다. 첫 실행 다운로드를 허용하려면 신뢰할 수 있는 환경에서만 `DOCFIT_ALLOW_NPX_DOWNLOAD=1`을 설정하세요. DOCX·EPUB 출력에는 Pandoc, HWPX 이외 입력의 PDF 출력에는 한/글 COM도 필요합니다. 이 경로는 Markdown 기반으로 내용을 재생성하므로 원본 페이지·서식 보존을 보장하지 않습니다. 도구가 없거나 지원되지 않는 입력이면 해당 원형 선택지를 비활성화하고 이유를 화면에 표시합니다. [Kordoc 사용 형식](https://github.com/chrisryugj/kordoc/blob/main/docs/usage.md)과 결과 문서를 확인하세요.

1.74 Alpha 3은 설정 서랍의 `준말 등록·관리`에서 조회·검색·등록·수정·삭제,
기본 준말 사용 여부를 Flutter로 제공합니다. 학습된 표 서식을 보존하며 표 서식 학습은 기존 전체 설정에서 합니다.
새 기능은 `lib/features/abbreviations`, API·모델은 `lib/core`로 분리했습니다.
[전환 현황](../docs/FLUTTER_MIGRATION_AUDIT.md) · [API 계약](../docs/FLUTTER_API_CONTRACT.md).

저장소 루트에서 `powershell -File build_flutter.ps1`로 빌드합니다. Flutter 소스를 변경한 뒤에는 생성된 `desktop_web/flutter` 자산을 다시 빌드해야 실행 화면에 반영됩니다. 이 폴더는 생성물이라 Git에 커밋하지 않습니다.
SDK는 PATH, `FLUTTER_SDK`, 또는 `%LOCALAPPDATA%\DocFitTools\flutter`에서 찾습니다.
결과는 `desktop_web/flutter`이며 기존 exe 패키징에 함께 포함됩니다.
빌드 스크립트는 lockfile 설치·analyze·test·웹 빌드·폰트/CanvasKit 자산 검증을 모두 통과해야 성공합니다.
빌드가 있으면 Flutter 화면을 사용하고, 없으면 기존 WebView 화면을 사용합니다.
앱 실행은 기존 `.venv\Scripts\pythonw.exe hwp-auto-docfit.py` 명령을 사용합니다.

검사: `flutter analyze`, `flutter test` (`flutter_ui` 폴더에서 실행).
Noto Sans KR 폰트는 OFL 라이선스로 번들합니다(`assets/OFL.txt`).
CanvasKit과 글꼴을 로컬에 포함하므로 화면 실행에 CDN 연결이 필요하지 않습니다.

Linux 클라우드에서도 Web 검증은 가능합니다. SDK는 Windows CI와 같은 3.47.5입니다.
캐시 경로가 쓰기 제한된 경우 `XDG_CONFIG_HOME`, `PUB_CACHE`,
`ANALYZER_STATE_LOCATION_OVERRIDE`를 쓰기 가능한 경로로 지정합니다.
`dart --suppress-analytics format lib test`로 분석 데이터 디렉터리 쓰기 없이 포맷할 수 있습니다.
Windows 네이티브 EXE·WebView2·HWP COM 동작은 Windows+한/글 2020에서 별도 검증합니다.

## tldraw 업무 흐름도 편집기 (alpha 개발 전용)

`developer_mode`와 `diagram_editor_enabled`를 모두 켠 네이티브 Flutter Windows 앱에서만 메뉴가 보입니다.
루트에서 `build_native.ps1`을 실행하면 Node.js 22.12+, npm lockfile의 React/tldraw 번들,
Flutter 3.47.5 및 Windows WebView2 runner를 함께 검사·빌드합니다. 편집기 JS/CSS/폰트는 로컬 Flutter asset에 포함됩니다.
10개 업무 예시를 편집하고 JSON을 `%APPDATA%\HwpAutoDocFit\diagrams`에 저장하거나 PNG를 내보낼 수 있습니다.

이것은 **기술 시제품**입니다. HWP/HWPX 삽입과 재편집은 아직 구현하지 않았습니다.
tldraw SDK는 MIT 라이선스가 아니며 정식/베타/일반 사용자 배포에는 별도 사용권이 필요합니다.
사용권 승인 및 Windows 실기기 검증 전에는 배포 빌드에서 이 기능을 활성화하지 않습니다.
[현재 구조·라이선스 감사](../docs/TLDRAW_FEATURE_AUDIT.md) · [HWP 삽입 후속 설계](../docs/TLDRAW_HWP_INSERTION.md)
