# 스마트 캐싱 포터블 런처

## 구성

- PyInstaller는 설치형과 캐시형 포터블에서 함께 쓰는 `onedir` 앱 번들을 만든다.
- `scripts/build_smart_launcher.py`가 번들의 파일별 SHA-256 매니페스트와 ZIP 페이로드를 만들고, Windows 기본 .NET Framework C# 컴파일러로 작은 단일 EXE 런처를 만든다. ZIP은 런처의 데이터 리소스로 내장되므로 PyInstaller `onefile` 부트로더가 매번 앱 전체를 임시 폴더에 풀지 않는다.
- 첫 실행에서만 `%LOCALAPPDATA%\HWP_AutoDocFit\app_v{버전}_{페이로드해시12자리}`에 푼다. 임시 `.staging-*` 폴더에서 각 파일의 경로·크기·SHA-256을 검증한 다음 완료 표식을 쓰고 디렉터리 이름을 원자적으로 바꾼다.
- 이후 실행은 완료 표식, 실행 파일, 매니페스트의 파일 존재·크기를 확인하고 캐시 앱을 직접 실행한다. 실행할 때마다 모든 DLL의 SHA-256을 다시 계산하지는 않는다. 설치 후 파일 내용 무결성은 최초 추출 시 검사한다.
- 실행 인자는 공백·따옴표를 포함해 자식 앱으로 전달한다. 런처와 앱은 같은 Global/Local 이름의 뮤텍스를 공유하며, 시작 이벤트로 소유권을 넘긴다. self-test는 뮤텍스와 스플래시를 건너뛴다.
- 새 버전/페이로드 해시는 새 캐시 경로를 만들며, 앱 시작 인계가 끝난 뒤 이전 `app_v*` 캐시를 정리한다.

## 빌드 및 확인

통합 빌드:

```bat
build_dist.bat
```

캐시형 포터블 단독 빌드(먼저 `HWP_AutoDocFit.spec`로 `onedir` 번들을 빌드한 뒤):

```powershell
.\.venv\Scripts\python.exe scripts\build_smart_launcher.py --version ( .\.venv\Scripts\python.exe scripts\read_app_version.py )
```

Windows CI는 `scripts/smoke_smart_launcher.py`로 self-test 인자 전달, cold extraction, 캐시 재사용을 확인하고 캐시 상태에서 두 차례 실제 앱 창 표시 시간을 기록한다. 1.5초 목표는 측정치로 보고하며, 서식 재연 합격 기준의 대체 조건으로 사용하지 않는다.

## 실제 측정 결과 — 2026-10-18 로컬 Windows 11

기존 로컬 `dist` 산출물을 보존하기 위해 임시 빌드 폴더에서 시험했다. 실제 앱 번들을 사용한 결과:

| 항목 | 측정 |
|---|---:|
| 최종 단일 EXE 크기 | 206,014,464 bytes |
| 첫 실행 스플래시 표시 | 534.84 ms |
| 첫 실행 실제 앱 창 표시 (압축 해제 포함) | 21,381.43 ms |
| 캐시 상태 self-test 시작/종료 | 1,738.28 ms |
| 캐시 상태 self-test 재실행 | 1,590.50 ms |
| 캐시 상태 실제 앱 창 표시 — 1차 | 8,720.74 ms |
| 캐시 상태 실제 앱 창 표시 — 2차 | 8,496.58 ms |
| 매니페스트 완료 표식의 재실행 변경 여부 | 변경 없음 (캐시 재사용 확인) |

따라서 캐시 추출 생략과 인자 전달은 동작하지만, 이 PC에서 요청한 스플래시 0.1초 및 캐시 실행·실제 창 표시 1.5초 목표는 달성되지 않았다. 첫 실행은 압축 해제가 있어 오래 걸리고, 캐시 이후에도 앱 초기화/WebView2 창 표시가 지연된다. 이 결과로 목표 성능을 달성했다고 주장하지 않는다. 측정에는 테스트용 `DOCFIT_OFFLINE=1` 환경과 이 PC의 Defender·WebView2·디스크 상태가 반영되어 있으므로 다른 PC 결과와 구분한다.

릴리즈 후보의 최종 검수 판정은 [릴리즈 검수 절차](RELEASE_TEST_PROCEDURE.md)의 서식 원본·재연 결과물 일치 여부로만 한다.
