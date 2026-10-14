# 개발자용 실행·테스트·배포 안내

[사용자용 README로 돌아가기](../README.md)

일반 사용자는 `HWP_AutoDocFit.exe`만 실행하면 됩니다.
이 문서는 소스 코드를 수정하거나 실행 파일을 직접 빌드하는 사람을 위한 안내입니다.
작업 전 [AGENTS.md](../AGENTS.md)와 [HANDOVER.md](../HANDOVER.md)를 읽으세요.

## 1. 개발 환경

- Windows와 편집 가능한 한컴오피스 한/글. 실제 문서 처리 검증 환경은 한/글 2020입니다.
- Python·Tkinter. 현재 개발 환경은 **Python 3.14**이며 저장소의 `.venv`를 사용합니다.
- `HwpFrame.HwpObject` COM 자동화가 사용 가능한 환경
- 저장소 루트의 `MapoHwpAutoDocFitSecurity.dll`
- 새 웹 화면은 WebView2를 사용하며 사용할 수 없으면 기존 Tk 화면으로 대체합니다.

실행 파일 사용자와 달리, 소스 실행 시에는 Python과 [requirements.txt](../requirements.txt)의 의존성 설치가 필요합니다.
Node.js는 선택형 kordoc 기능에만 필요합니다. [추가 엔진 안내](ADVANCED_USAGE.md#engine)를 참고하세요.

## 2. 소스 받기

GitHub를 원본, GitLab을 백업 원격으로 사용합니다.
두 저장소에서 공통 README와 문서를 읽을 수 있습니다.

```powershell
git clone --origin github https://github.com/haijun93/hwp-auto-docfit.git
cd hwp-auto-docfit
git remote add origin https://gitlab.aigov.go.kr/haijun93/hwp_autodocfit.git
```

이미 저장소가 있다면 다시 복제하거나 원격을 중복 추가하지 말고 `git remote -v`로 확인하세요.
`main`은 베타 배포선, `alpha`는 새 기능 개발선입니다.
브랜치를 바꾸기 전 기존 수정사항을 확인하고 보존하세요.

## 3. 가상환경 만들고 실행하기

저장소 루트에서 PowerShell을 엽니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe hwp-auto-docfit.py
```

이미 가상환경이 준비되어 있으면 실행 명령만 사용합니다.
앱은 시작할 때 코드를 읽으므로 수정 후에는 다시 실행해야 반영됩니다.
Flutter 화면 개발·빌드는 [flutter_ui/README.md](../flutter_ui/README.md)를 참고하세요.

### 한/글 자동화 보안 모듈

프로그램은 보안 모듈 DLL을 `C:\HWP_AUTODOCFIT\dll\HwpAutoDocFitSecurity.dll`로 복사하고 현재 사용자의
`Software\HNC\HwpAutomation\Modules` 아래에 `HwpAutoDocFitSecurity`라는 이름으로 등록합니다(알파, 2026-10-10).
v1.72 베타까지는 `C:\HwpAutomation\MapoHwpAutoDocFitSecurity.dll`·값 이름 `MapoHwpAutoDocFitSecurity`였고,
알파는 실행할 때 예전 DLL과 예전 레지스트리 값을 지웁니다(예전 베타를 다시 실행하면 그 판이 스스로 다시 만듭니다).
앱에 포함된 원본 DLL 파일 이름(`MapoHwpAutoDocFitSecurity.dll`)과 빌드 설정은 그대로입니다.

앱 폴더 `C:\HWP_AUTODOCFIT`의 하위 폴더:

| 폴더 | 내용 |
|---|---|
| `dll` | 한/글 자동화 보안 모듈 DLL |
| `서식예시` | 서식마다 예시 HWPX(기본 서식은 `기본 서식.hwpx`, 추가한 서식은 `<서식 이름>.hwpx`). 사용자가 한/글에서 고쳐 저장하면 '한 번에 적용'을 시작할 때 바뀐 서식 값만 서식 설정에 옮깁니다(`docfit_core/format_samples.py`). 비교 기준이 되는 원본 사본·해시는 `%APPDATA%\HwpAutoDocFit\format_examples`에 둡니다. 기본 서식 예시를 지우면 고친 기본 서식(`formats\_standard.json`)도 지워 처음 값으로 돌아갑니다 |
| `글자상용구` | 한/글 글자 상용구 파일 `HWP.IDO`(없으면 앱에 포함된 파일을 넣음) |
| `본문상용구` | 한/글 본문 상용구 파일(`IDIOM\*.HWP`). 설정 > 고급의 '상용구 파일저장'이 두 상용구 폴더의 파일을 한/글 전용 폴더(`%AppData%\HNC\User\Hwp\60`, `IDIOM`)로 복사합니다 |

`알파_서식예시폴더_사용 = False`로 끄면 예전 폴더·이름·보관 방식으로 돌아갑니다.
기관의 파일 쓰기·자동화·레지스트리 정책에 따라 차단될 수 있으므로 승인된 환경에서 실행하세요.

현재 DLL은 한컴 예제 바이너리를 프로젝트 전용 파일명으로 바꾼 것입니다.
기관 주요 시스템이나 상업용 배포에서는 보안 모듈 소스를 검토하고 직접 빌드한 모듈을 사용하는 방안을 검토하세요.
실행 파일 빌드에는 이 DLL이 포함됩니다. 사용자에게 출처 불명의 DLL을 별도로 받도록 안내하지 마세요.

## 4. 테스트와 실제 문서 확인

```powershell
.\.venv\Scripts\python.exe -m py_compile hwp-auto-docfit.py docfit_core\__init__.py docfit_core\hwpx.py
.\.venv\Scripts\python.exe -c "import runpy; runpy.run_path('hwp-auto-docfit.py', run_name='import_check')"
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

GUI 테스트는 창을 띄울 수 있으므로 Windows 데스크톱 세션에서 실행합니다.
단위 테스트 통과가 실제 한/글에서의 화면·조판 일치를 보장하지는 않습니다.
문서 편집 검증에는 한/글과 보안 모듈이 필요하며 **사용자 원본이 아닌 사본**을 사용하세요.

스타일 분석 보고서와 예시 서식은 다음처럼 생성합니다.

```powershell
.\.venv\Scripts\python.exe scripts\style_inventory.py "문서.hwp" --out "분석결과"
```

코퍼스 시험과 COM 검증 예시는 `scripts/`, 세부 절차는 [HANDOVER.md](../HANDOVER.md)에 있습니다.
XML 파싱은 `defusedxml`을 사용하고 `hwp-auto-docfit.py`의 CRLF 줄바꿈을 유지하세요.

## 5. 실행 파일 빌드

```powershell
.\build.bat
```

완료되면 `dist\HWP_AutoDocFit.exe`가 생성됩니다.
빌드에는 의존 패키지 설치가 포함되므로 최초 실행 시 네트워크가 필요할 수 있습니다.
Flutter SDK가 없거나 검사·테스트·웹 빌드·자산 검증이 실패하면 EXE 빌드를 중단합니다.
Flutter 화면이 누락된 패키지를 만들지 않으며, 런타임의 기존 WebView/Tk 비상 복구 경로는 유지합니다.
`desktop_web`·`resources`·자동화 DLL 등 필요한 리소스는 빌드 스크립트가 포함합니다.

코드·단위 테스트뿐 아니라 빌드된 EXE를 실제로 실행해 창 제목의 버전과 문서 처리 결과를 확인하세요.

## 6. 배포와 자동 업데이트

정확한 브랜치 병합·CI 빌드·태그 절차는 [인수인계서의 배포 절차](../HANDOVER.md)를 따릅니다.

- 사용자 요청이 있을 때만 커밋·푸시합니다.
- 원격 반영 순서는 **GitHub(`github`) → GitLab(`origin`)**입니다.
- Windows 실행 파일은 GitHub 빌드 작업을 거쳐 준비하며 GitLab 태그 파이프라인이 공식 릴리스 자산으로 게시합니다.
- GitLab의 Linux 검사만으로 Windows COM·GUI 동작까지 검증됐다고 보지 않습니다.

앱은 GitLab 최신 릴리스를 확인하고 사용자 확인 후 업데이트 파일을 받아 실행 파일을 교체합니다.
릴리스에는 현재 앱보다 높은 버전의 태그와 `HWP_AutoDocFit.exe` 이름의 다운로드 자산 링크가 필요합니다.
자동 업데이트 환경에서 릴리스 API와 자산 링크는 인증 없이 접근할 수 있어야 합니다.
네트워크 오류나 릴리스 부재는 기존 앱 실행을 막지 않습니다.

실행 파일명 `HWP_AutoDocFit.exe`, 설정 폴더 `HwpAutoDocFit`, 보안 모듈 등록명은 호환성을 위해 유지합니다.
사용자 문서·설정·서식 JSON·작업 로그에 민감한 자료가 포함될 수 있으므로 배포 자산에 섞지 마세요.

## 7. 관련 자료

- [세부 기능과 제한사항](ADVANCED_USAGE.md)
- [UI 설계](../UI_DESIGN.md)
- [서식 복사 설계·측정](../FORMAT_COPY_DESIGN.md)
- [원본 보존·재현 설계](../STYLE_FIDELITY_DESIGN.md)
- [릴리스 노트](../releases/)
- [프로젝트 소개 웹사이트 소스](../website/)

## 알파 리팩터링 상태

- `docfit_core/app_state.py`: GUI 위젯과 독립된 실행 옵션·상태.
- `docfit_core/config_store.py`: 순수 설정 마이그레이션과 기존 원자 JSON 저장 연결.
- `desktop_web_ui.py`: 프로파일 coverage 캐시, AppState 접근 및 레거시 호스트 호환.
- `hwp-auto-docfit.py`: 기존 속성 파사드 및 실행 시 옵션 스냅샷. CRLF 유지.
- `docfit_engine/`·`docfit_ui/` 전체 추출과 Flutter 도구 일원화는 후속 단계.
- Linux 회귀 검사는 Windows 모듈 대체/실제 Tk를 사용하며 실제 한/글 COM 검증을 대신하지 않는다.


## Alpha 8 코드 구조 및 검증

- `hwp-auto-docfit.py`: CRLF 부트스트랩과 기존 이름 re-export. 외부 스크립트의 import/runpy 계약 유지.
- `docfit_engine/`: 보안 등록·COM·자간·서식·쪽 배치·파이프라인. `context.py`의 RunContext가 옵션·프로필·캐시·COM 세션 상태를 작업별로 소유한다. `runtime.py`는 함수를 작업별 상태 사전에 바인딩하며 GUI는 context/callbacks를 명시적으로 전달한다. 루트 함수의 기존 monkeypatch 호환 경계는 유지한다.
- `docfit_ui/legacy.py`: Tk 폴백. `scheduler.py`: 소유 스레드 큐 펌프. 외부 RPC 스레드는 Tk 콜백을 직접 등록하지 않는다.
- `docfit_core/app_state.py`, `config_store.py`: 정형 상태·옵션과 설정 마이그레이션.
- `desktop_web_ui.py`: JSON 명령/값만 공개. 프로필 revision 검사, 단계 설정, Flutter 확인 요청을 중개한다.
- `docfit_app/document_tools_service.py`: 공통 작성 도구, CAS 초안 저장, 선택 교정 사본, 작업 사본 기반 고급 도구와 상태 조회.
- `flutter_ui/lib/features/`: 프로필·기본 데이터 표·문서 도구·확인 화면. 현재 운영은 Flutter 웹/WebView2이며 별도 네이티브 COM 이관 완료를 뜻하지 않는다.
- `HWP_AutoDocFit.spec`: 로컬 build.bat과 CI의 공통 패키징 정의. engine/ui/core/app 하위 모듈을 수집한다. Flutter 자산 검사 유지.
- `docfit_app/self_test.py`: `--self-test [--self-test-report PATH]` 모듈·실제 부트스트랩 심볼 검사. GUI/COM 생성 없이 종료하며 CI는 동결 EXE를 30초 제한으로 검사한다.
- `PipelineCallbacks`: log/status/progress 및 on_stage_enter/exit/error, event 포트. 실제 문서 단계에서 호출하며 UI 위젯을 엔진에 전달하지 않는다.
- 비동기 편집: 흐름도 snapshot 세대와 ACK 세대를 구분하고 아웃라이너 변경 RPC를 직렬화한다. 지연 응답은 최신 입력 revision을 덮어쓰지 않는다.
- 일반 흐름도: model.js의 공통 글자 측정·자동 크기·안전 여백·줄바꿈을 화면과 PNG 양쪽에서 사용한다.
- 상세 구현·검증: [Alpha 9](REVIEW_FIXES_ALPHA9.md).

기본 DLL 경로에 복사 또는 등록이 실패하면 `%LOCALAPPDATA%\HwpAutoDocFit\modules`에 폴백한다.
Windows에서는 저장소 루트 `.venv\Scripts\python.exe`, `PYTHONIOENCODING=utf-8`로 compile/import/unittest를 실행한다.
현재 Linux 클라우드에서는 `.venv/bin/python`과 실제 Tk/Xvfb를 사용하고 COM/winreg만 대체한다.
Linux 전체 검사는 `DISPLAY=:91 .venv/bin/python scripts/linux_stub_test_runner.py --require-gui discover -s tests`이다.
Windows 한/글 실측, WebView2 포커스와 EXE 패키징은 Windows 환경에서 별도 확인해야 한다.
결과는 [Phase 3~5 보고서](REFACTOR_PHASE3_5_ALPHA8.md)에 기록한다.


### 일반 흐름도와 개발자 tldraw

- 일반 편집기: `diagram_editor/` React Flow(MIT), `docfit_app/flow_service.py`, Flutter `features/flows/`.
- 일반 모드 버튼은 개발자 옵션과 독립. 저장 API는 `flow_editor(action,payload)`, 데이터는 `flows/`.
- tldraw는 기존 `tldraw_editor/`·`features/diagrams/`·`DiagramService`를 유지. 개발자 모드와 별도 옵션이 모두 필요하며 `diagrams/` 데이터를 사용한다.
- `scripts/build_flow_editor.ps1`이 고정 의존성 설치·모델 시험·번들·라이선스 고지를 생성하며 웹/네이티브 빌드에서 호출한다. Node 22.12+ 필요.
- 일반 편집기는 런타임 CDN·외부 서비스 없이 로컬 자산 사용. 기존 tldraw SDK 제품 사용권 과제는 그대로 유지한다.


### Alpha 11 저장·종료 보호 계약

- fidelity 출력은 기존 결과를 덮어쓰지 않는다. 하드링크를 지원하지 않는 파일시스템의 오류는 명시적으로 처리한다.
- FlowService/DiagramService 기존 문서 저장에는 load/save 응답의 revision이 필요하다.
  문서별 프로세스 잠금 안에서 비교·쓰기·응답을 확정하며 충돌은 사본 저장으로 복구한다.
- Flutter core/close_guards.dart의 CloseLease는 편집 화면 dispose까지 종료를 보류한다.
  DesktopWebBridge.enable_close_guard → app_close 폴링 → resolve_dialog 승인 순서이며,
  native closing 콜백에서 JavaScript를 동기 대기하지 않는다.
- kordoc 버전별 .install.lock 파일은 제거하지 않는다. 설치 완료를 잠금 안에서 재검사한다.
- 검증·Windows 실기기 한계: docs/FINAL_REVIEW_FIXES_ALPHA11.md.
