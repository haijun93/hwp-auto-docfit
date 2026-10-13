# Flutter 전환·1.74 Alpha 3 안정화 시험 보고서

2026-10-13. Linux 클라우드, Python 3.12.14, Flutter 3.47.5, Dart 3.13.4. 시작 alpha는 `4e1c391`, 비교 베타는 `016b6be`다. 사용자 문서 원본은 처리하지 않았다. 테스트는 임시 설정 파일/합성 HWPX/모의 API를 사용한다.

## 실행 결과

| 검사 | 결과 | 해석 |
|---|---|---|
| `flutter pub get --enforce-lockfile` | 성공, lockfile 변경 없음 | 고정된 의존성과 패키지 해시 유지 |
| `flutter analyze --no-pub` | 성공, No issues found | 신규 모듈 포함 |
| `flutter test --no-pub` | **25개 통과** | 기존 12 + 안정화/진입점 5 + 준말 UI/API 8 |
| release Web build, `--no-web-resources-cdn --no-wasm-dry-run --no-pub` | 성공 | 로컬 font/CanvasKit 포함; 기존 CupertinoIcons 폰트 경고는 남음 |
| `python scripts/verify_flutter_bundle.py` | 성공 | entrypoint/bootstrap/main JS/Korean font/license/CanvasKit JS·WASM |
| loopback HTTP 자산 smoke | 성공 | Flutter entrypoint 선택, bridge 함수·신규 API 참조, bootstrap/폰트/renderer/license 응답 확인; 브라우저나 COM 실행 검증은 아님 |
| Python 집중 시험 | **66개 통과** | request lifecycle 8, abbreviation service 13, bundle 3, HWPX 12, fidelity 10, format elements 15, file drop 5 |
| 기존 준말 RegistryTest | **7개 통과** | 기존 변환 규칙 + 손상된 format value 방어; 앱 import를 위해 Linux 대체 실행기 사용 |
| Browser API 직접 실행 | 18개, 17 성공/1 실패 | Windows 경로 basename을 POSIX Path로 읽는 기존 테스트 차이 |
| `python -m py_compile` 변경 Python 파일 | 성공 | Python 본체 줄바꿈을 정규화하지 않고 변경 |
| `pip check`, `git diff --check` | 성공 | 의존성 충돌/patch 공백 오류 없음 |

새 기능/회귀는 Python 25개와 Flutter 13개를 추가했다. 기존 테스트를 삭제하거나 assertion을 완화하지 않았다. Browser API 노출 명령 수만 신규 명령 4개에 맞춰 갱신했다.

## 전체 Python 결과·기준선

| 실행 | 총수 | 성공 | 실패 | 오류 | 건너뜀 | exit |
|---|---:|---:|---:|---:|---:|---:|
| Beta 1 Linux 대체 실행(이전 리뷰) | 907 | 883 | 7 | 15 | 2 | 1 |
| Alpha 2 Linux 대체 실행(변경 전) | 956 | 931 | 7 | 15 | 3 | 1 |
| Alpha 3 Linux 대체 전체 실행 | **981** | **956** | **7** | **15** | **3** | **1** |
| Alpha 3 표준 `python -m unittest discover -s tests` | 518 | 378 | 2 | 128 | 10 | 1 |

대체 실행 명령: `python scripts/linux_stub_test_runner.py discover -s tests`. 변경 전후 FAIL/ERROR 항목 이름을 비교해 **동일한 7개 실패/15개 오류**임을 확인했다. Tk MagicMock 동작, Windows 경로 비교, 실행기가 mock한 `webview`의 `webview.dom` 부재 때문이다. file drop는 실제 pywebview 의존성을 쓰는 집중 실행에서 5개가 모두 통과한다. 전체 대체 실행이 성공했다고 표현하지 않는다.

표준 명령의 128개 오류는 `winreg` 127건·`pythoncom` 1건 모듈 부재다. 2개 실패는 Windows 경로를 POSIX Path로 비교하는 기존 테스트다. Linux에는 Windows COM 모듈을 설치할 수 없다. Tk 화면 및 optional MCP SDK 시험 일부는 건너뛰었다. **Windows 표준 전체 시험 통과를 주장하지 않는다.** MCP SDK를 새로 설치/활성화하거나 사용자 연결 기능을 추가하지 않았다.

로그: `/tmp/docfit-alpha-before.log`, `/tmp/docfit-final-python-tests.log`, `/tmp/docfit-native-python-tests.log`, `/tmp/docfit-final-focused.log`, `/tmp/docfit-final-browser-api.log`, `/tmp/docfit-final-flutter-tests.log`, `/tmp/docfit-final-analyze.log`, `/tmp/docfit-final-flutter-build.log` (현재 세션용, Git에는 넣지 않음).

## 수정 전 재현

- `_tk` timeout 후 큐를 실행하면 callback 부작용이 발생했다. 신규 시험은 callback 미실행, 종료 해제, 실행 중 timeout, callback 자체 TimeoutError, 종료 취소/성공을 검사한다.
- 새 문서/새 작업의 Flutter start가 이전 `true,5,7` 범위를 전송했다. 두 신규 위젯 시험이 수정 전 실패했고 수정 후 `false,1,1`을 확인했다.
- 오래된 poll이 새 unify 명령 상태를 spacing으로 덮었다. 신규 위젯 시험이 수정 전 실패하고 수정 후 최신 모드로 start하는 것을 확인했다.
- 준말 service는 임시 실제 JSON 파일로 다른 설정·학습된 표 style·rename 충돌·잘못된 입력·실행 중 제약·깨진 설정·저장 교체 실패 보존을 검사했다. Flutter 오류는 입력을 유지하고 재시도 가능하며, pending save 중 닫기/뒤로 가기로 작업이 숨지 않는다.

## Windows에서 남은 필수 검증

1. `.venv\Scripts\python.exe -m unittest discover -s tests`와 `powershell -File build_flutter.ps1`, `build.bat`. Linux에서는 PowerShell/배치 스크립트 자체를 실행하지 못했으며, 내부 Flutter 명령과 Python 자산 검사는 동등한 Linux 명령으로 수행했다.
2. 빌드된 EXE의 버전/Flutter 화면/오프라인 폰트·CanvasKit 로드, 실제 파일/폴더 선택·다중 드롭·한글/공백 경로·200% DPI/키보드 조작.
3. 기존 설정 파일 사본으로 Tk/Flutter 준말 CRUD 동등성·학습한 표 서식 보존·기본값 override 삭제, 표 서식 학습, 저장 실패/취소.
4. 동일 문서 사본·설정으로 Beta 1/Alpha 3 교차 처리: 결과 글/표/그림·쪽 구성·원본 SHA-256, 작업 중단·종료/취소/재시도·한/글 프로세스 정리.
5. 신규 native EXE/IPC·Web/native 성능 비교는 아직 없으며 [기술 검증 문서](FLUTTER_NATIVE_FEASIBILITY.md)에 미실시로 표시한다.

실제 COM 문서 처리 결과·성능·최종 EXE 안전성을 검증한 것으로 해석하면 안 된다. 전체 설정/프로필 상세/검토 화면까지 Flutter로 완전히 이전한 상태도 아니다.
