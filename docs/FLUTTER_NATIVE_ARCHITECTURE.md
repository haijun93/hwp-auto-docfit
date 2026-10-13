# 네이티브 구조

Flutter 화면 → NativeClient → 인증된 loopback JSON IPC → ApplicationService → 공통 설정·준말 서비스 / docfit_core.

Python 백엔드는 tkinter, tkinterdnd2, webview를 import하지 않는다. 기존 웹 UI는 DesktopWebBridge를 통해 같은 설정 서비스를 사용하며 기존 Tk 복구 경로를 보존한다.

설정 기본값·마이그레이션은 UI 밖으로 이동했다. SettingsService는 경로별 스레드 잠금과 운영체제 파일 잠금 아래 읽기·변경·원자 교체를 수행한다. revision으로 오래된 설정 초안 저장을 거절한다. 같은 설정 폴더의 네이티브 백엔드는 하나만 실행된다. 구형 프로그램의 쓰기까지 잠금을 강제할 수 없으며 두 UI를 동시에 운영하는 것은 권장 운영 방식이 아니다.

향후 COM은 전용 STA 작업 스레드에서 직렬 처리해야 한다. 작업 접수와 진행 이벤트, 취소, 원본 사본 생성·검증·최종 저장을 연결한 뒤 engine_ready를 활성화한다. 현재 명령 실행 잠금은 서비스 요청을 직렬화하며 긴 분석의 비동기 처리는 아직 구현하지 않았다.

성능 개선은 실제 문서 코퍼스의 분석·COM 호출·저장 시간을 측정한 뒤 진행한다. 현재 시험 통과는 COM 성능 향상을 입증하지 않는다.
