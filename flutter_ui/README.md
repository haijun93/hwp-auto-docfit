# Flutter 알파 UI

Material 3 기반 Flutter Web 화면을 기존 WebView2 창에 포함합니다.
Python/한글 COM 처리부는 `DesktopWebBridge`를 통해 연결합니다.
파일·폴더 선택, 텍스트 입력, 작업 방식, 쪽 범위, 진행 상태, 결과,
중단, 다음 작업을 지원합니다. 설정 화면에서 작업로그·무결성검사·최종검수 파일 저장,
서식통일 결과 창, 항상 위 표시를 포함한 자주 쓰는 설정을 바꿀 수 있습니다.
전체 설정과 일부 서식 분석·검토 대화상자는 아직 Tk 창을 사용하며, 단계적으로 이관합니다.

저장소 루트에서 `powershell -File build_flutter.ps1`로 빌드합니다.
SDK는 PATH, `FLUTTER_SDK`, 또는 `%LOCALAPPDATA%\DocFitTools\flutter`에서 찾습니다.
결과는 `desktop_web/flutter`이며 기존 exe 패키징에 함께 포함됩니다.
빌드가 있으면 Flutter 화면을 사용하고, 없으면 기존 WebView 화면을 사용합니다.
앱 실행은 기존 `.venv\Scripts\pythonw.exe hwp-auto-docfit.py` 명령을 사용합니다.

검사: `flutter analyze`, `flutter test` (`flutter_ui` 폴더에서 실행).
Noto Sans KR 폰트는 OFL 라이선스로 번들합니다(`assets/OFL.txt`).
CanvasKit과 글꼴을 로컬에 포함하므로 화면 실행에 CDN 연결이 필요하지 않습니다.
