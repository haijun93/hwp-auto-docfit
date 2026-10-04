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

프로그램은 보안 모듈 DLL을 `C:\HwpAutomation`에 복사하고 현재 사용자의
`Software\HNC\HwpAutomation\Modules` 아래에 `MapoHwpAutoDocFitSecurity`라는 이름으로 등록합니다.
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
Flutter SDK가 없으면 새 Flutter 화면 빌드를 건너뛰고 기존 화면으로 빌드를 계속합니다.
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
