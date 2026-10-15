# Flutter 네이티브 전환 현황 (2026-10-13)

현재 공개 main은 1.74 Beta 1, 개발 alpha는 안정화 코드와 네이티브 시제품을 병행한다. 최종 목표는 Flutter Windows 기본 UI와 별도 Python 처리 백엔드다.

| 영역 | 현재 코드 | 상태 |
|---|---|---|
| Windows 실행 기반 | flutter_ui/windows | runner·CMake·DPI·최소 크기 추가, Windows 미빌드 |
| 백엔드 수명·통신 | docfit_app/backend_main.py, ipc_server.py | Tk/WebView2 없이 시작, 인증·종료·중복 실행 방지 구현 |
| 전체 설정 | configuration_service.py, settings_schema.py, settings_migrations.py | 79개 기본 설정에서 사용자 편집 90개 필드 구성, Flutter 화면 추가 |
| 준말 관리 | abbreviation_service.py | 네이티브·웹 공통 서비스 |
| 문서 입력 | application_service.py, bridge_native.dart | 기본 파일·폴더 선택 및 목록 관리 |
| 문서 분석 | docfit_core/hwpx.py | 기존 안전 분석 연결, 원본 읽기 전용 |
| 실제 서식 처리 | hwp-auto-docfit.py | 기존 COM 파이프라인 유지, 네이티브 연결 미구현 |
| 프로필 상세·문서 검토 | 기존 Tk 경로 | 네이티브 전환 미완료 |
| 진행 이벤트·취소 | 기존 웹 bridge | 네이티브 작업 큐·이벤트 미구현 |

일괄 파일 분할은 하지 않았다. 설정·앱 상태·통신·저장 잠금부터 독립시키고 docfit_core 알고리즘은 유지한다. C++ runner와 Windows 잠금·패키징은 Linux 시험만으로 완료 판정하지 않는다.
