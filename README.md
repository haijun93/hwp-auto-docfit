# HWP Auto DocFit — hwp 자동 편집기

한글 2020의 HWP/HWPX 문서를 편집하는 Windows용 Python 프로그램입니다.
실행 파일은 `hwp-auto-docfit.py`이며, 프로그램 버전은 `1.64`입니다.

## 주요 기능

- 파일·폴더 드래그 앤 드롭과 여러 문서 일괄 처리
- 줄 끝 단어 분리를 줄이기 위한 자간 조정
- 공문서 항목 인식, 문장 줄 병합, 세트 문장의 같은 페이지 유지
- 보고서 표준서식, 표·셀 서식, 괄호·공백 정리
- 글자색 표시, 결과 검수, 진행률과 작업 로그
- 설정 저장 및 작업 중단

## 실행 환경

- Windows
- Python 3.14 및 Tkinter
- 한글 2020 설치 및 `HwpFrame.HwpObject` COM 자동화 사용 가능 환경
- `FilePathCheckerModuleExample.dll`: `hwp-auto-docfit.py`와 같은 폴더에 배치

보안 모듈 DLL은 저장소에 포함되어 있지 않습니다. 문서 처리 시 프로그램이 이 DLL을
`C:\HwpAutomation`에 복사하고 현재 사용자 레지스트리에 등록합니다.

## 설치 및 실행

프로젝트 폴더에서 PowerShell로 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe hwp-auto-docfit.py
```

창에서 HWP/HWPX 파일을 선택하거나 끌어다 놓고, 설정을 조정한 다음 **실행**을 누릅니다.

## EXE 빌드와 자동 업데이트

`build.bat`을 실행하면 `dist\HWP_AutoDocFit.exe`가 생성됩니다. Pillow와 tkinterdnd2도 EXE에 포함됩니다.

자동 업데이트를 배포하려면 GitHub에 draft/prerelease가 아닌 정식 Release를 만들고 다음 규칙을 지킵니다.

- 태그: 현재 앱 버전보다 높은 버전(예: `v1.65`)
- 첨부 자산: `HWP_AutoDocFit.exe`

배포된 EXE는 시작 후 백그라운드에서 최신 정식 Release를 확인합니다. 새 버전이 있으면 사용자 확인 후 EXE를 다운로드하고, 가능한 경우 GitHub 자산의 SHA-256 digest를 검증한 뒤 현재 실행 파일을 교체하고 다시 실행합니다. 네트워크 오류나 Release가 없는 경우 앱 실행에는 영향을 주지 않습니다.
결과는 원본과 같은 폴더에 `원본파일명(자간조정).hwp` 또는
`원본파일명(자간조정).hwpx`로 저장됩니다.
설정은 `%APPDATA%\HwpAutoDocFit\settings.json`에 저장됩니다.
보고서 표준서식은 `□`, `ㅇ`, `-`, `※` 등 문장부호로 시작하는 문단에만
적용됩니다. 각 작업의 전체 로그는 원본 문서 폴더에
`원본파일명(작업로그-YYYYMMDD-HHMMSS).log`로 저장됩니다.

## 기본 검증

```powershell
.\.venv\Scripts\python.exe -m py_compile hwp-auto-docfit.py
.\.venv\Scripts\python.exe -c "import runpy; runpy.run_path('hwp-auto-docfit.py', run_name='import_check')"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

GitHub Actions도 Windows에서 문법, 모듈 로딩, GUI 초기화를 확인합니다.
실제 문서 편집 검증에는 한글과 보안 모듈 DLL이 필요합니다.
