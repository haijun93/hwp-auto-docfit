# Flutter 알파 UI

Material 3 기반 Flutter Web 화면을 기존 WebView2 창에 포함합니다.
Python/한글 COM 처리부는 `DesktopWebBridge`를 통해 연결합니다.
파일·폴더 선택, 텍스트 입력, 작업 방식, 쪽 범위, 진행 상태, 결과,
중단, 다음 작업을 지원합니다. 설정 화면에서 작업로그·무결성검사·최종검수 파일 저장,
서식통일 결과 창, 항상 위 표시를 포함한 자주 쓰는 설정을 바꿀 수 있습니다.
전체 설정과 일부 서식 분석·검토 대화상자는 아직 Tk 창을 사용하며, 단계적으로 이관합니다.

1.74 Alpha 3은 설정 서랍의 `준말 등록·관리`에서 조회·검색·등록·수정·삭제,
기본 준말 사용 여부를 Flutter로 제공합니다. 학습된 표 서식을 보존하며 표 서식 학습은 기존 전체 설정에서 합니다.
새 기능은 `lib/features/abbreviations`, API·모델은 `lib/core`로 분리했습니다.
[전환 현황](../docs/FLUTTER_MIGRATION_AUDIT.md) · [API 계약](../docs/FLUTTER_API_CONTRACT.md).

저장소 루트에서 `powershell -File build_flutter.ps1`로 빌드합니다.
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
