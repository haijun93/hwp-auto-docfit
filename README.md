# 한글문서 후처리 도구

한글 2020의 HWP/HWPX 문서를 편집하는 Windows용 Python 프로그램입니다.
바이너리 HWP 입력은 원본을 변경하지 않고 작업용 HWPX로 변환하며, 모든 처리 결과는 HWPX로 저장합니다.
실행 파일은 `hwp-auto-docfit.py`이며, 프로그램 버전은 `1.67 Beta`입니다.
기존 사용자 설정과 자동 업데이트 호환성을 위해 실행 파일명 `HWP_AutoDocFit.exe`,
설정 폴더명 `HwpAutoDocFit`, 보안 모듈 등록명은 유지합니다.

서식 예시 문서를 드래그하거나 **서식 복사하기**를 누르면 문단의 들여쓰기, 글꼴,
글자 크기, 문두기호를 중심으로 제목·중제목·소제목·본문·내용·부연설명을 분석합니다.
문단 위 여백은 동일 역할에서도 달라질 수 있으므로 보조 정보로 표시합니다.
분석된 5대 시각 요소와 논리적 구조는 스크롤 가능한 확인 창에서 검토한 뒤
승인해야 서식 프로필로 저장·적용됩니다. 관련 소제목·본문·내용·부연설명 묶음이
둘 이상의 쪽으로 갈라지면 줄간격 재배치를 시도하고, 해결되지 않은 경우 검수
문제로 기록합니다. 한 쪽에 물리적으로 들어가지 않는 긴 묶음은 자동으로 보장할
수 없으므로 결과 문서를 확인해야 합니다.

이 프로젝트의 기준 저장소는 다음 GitLab 저장소입니다.

- `https://gitlab.aigov.go.kr/haijun93/hwp_autodocfit.git`

```powershell
git clone https://gitlab.aigov.go.kr/haijun93/hwp_autodocfit.git
cd hwp_autodocfit
```

## 프로젝트 웹사이트

앱 소개, 기능별 안내, 사용법과 최신 Windows 릴리스 다운로드 페이지는 `website/`에 있습니다.
`main` 브랜치가 갱신되면 GitLab Pages 작업이 정적 사이트를 배포합니다.

## 주요 기능

- 파일·폴더 드래그 앤 드롭과 여러 문서 일괄 처리
- 줄 끝 단어 분리를 줄이기 위한 자간 조정
- 공문서 항목 인식, 문장 줄 병합, 세트 문장의 같은 페이지 유지
- 보고서 표준서식, 표·셀 서식, 괄호·공백 정리
- HWPX ZIP bomb·경로 조작·CRC·필수 구조 사전 검사
- 처리 전후 본문·표·이미지·섹션 무결성 비교와 JSON 보고서
- HWP/HWPX 문단과 표를 UTF-8 Markdown으로 내보내기
- 예시 문서 드래그 앤 드롭 서식 분석과 사용자 서식 프로필 저장·재사용
- 일반 표의 셀별 글꼴·문단·테두리·음영·여백·크기·병합 구조 정밀 복제
- 선택형 kordoc v4 엔진을 이용한 공통 문서 IR, 중첩 표 Markdown, 표 분류와 블록·셀 신구대조
- 누름틀·양식 필드 분석 및 서식 보존 채우기·텍스트 패치, 공문서 표기법 검수
- 페이지별 Markdown, RAG 구조 청크 및 보고서·계획서·기안문 HWPX 생성
- 글자색 표시, 결과 검수, 진행률과 작업 로그
- 설정 저장 및 작업 중단

## 실행 환경

- Windows
- Python 3.14 및 Tkinter
- 한글 2020 설치 및 `HwpFrame.HwpObject` COM 자동화 사용 가능 환경
- `MapoHwpAutoDocFitSecurity.dll`: `hwp-auto-docfit.py`와 같은 폴더에 배치

문서 처리 시 프로그램은 프로젝트 전용 이름의 보안 모듈 DLL을 `C:\HwpAutomation`에 복사하고,
현재 사용자의 `Software\HNC\HwpAutomation\Modules` 아래에
`MapoHwpAutoDocFitSecurity`라는 고유한 값 이름으로 등록합니다.

현재 DLL은 한컴 예제 바이너리를 프로젝트 전용 파일명으로 변경한 것입니다. 상업용 배포나 사내 주요
시스템에서는 한컴이 제공하는 보안 모듈 소스를 검토하고 동일한 고유 명칭으로 직접 컴파일한 DLL로
교체하는 것을 권장합니다.

## 설치 및 실행

프로젝트 폴더에서 PowerShell로 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe hwp-auto-docfit.py
```

창에서 HWP/HWPX 파일을 선택하거나 끌어다 놓고, 설정을 조정한 다음 **실행**을 누릅니다.

목록에서 문서를 선택하고 **Markdown 내보내기**를 누르면 원본 폴더에 같은 이름의
`.md` 파일이 생성됩니다. HWPX는 직접 안전하게 분석하며, 바이너리 HWP는 한글 COM으로
임시 HWPX 스냅샷을 만든 뒤 변환합니다. 표는 Markdown 표로, 번호형 제목은 가능한 범위에서
제목 문법으로 변환됩니다.

세부 설정의 **상세 진단 및 문서 무결성 검사**가 켜져 있으면 편집 결과 옆에
`(무결성검사).json` 보고서가 만들어집니다. 본문 일치도와 문단·표·이미지·섹션 개수 변화를
기록하며, 경고가 있어도 결과를 삭제하지 않으므로 보고서를 확인해 최종 판단할 수 있습니다.

### 문서 서식 분석과 복제

실행창의 **적용 서식**에서 기본 서식 또는 저장해 둔 사용자 서식을 선택할 수 있습니다.
새 서식을 바로 사용하려면 오른쪽 드롭 영역에 예시 HWP/HWPX 문서를 놓습니다. 앱이 페이지
여백, 대표 본문·제목·기호 문단의 글꼴/크기/굵기, 장평·자간·줄간격·문단 모양을 분석합니다.
또한 문서의 모든 일반 표에서 셀별 문자·문단 서식, 테두리·색·음영, 셀 여백과 크기,
행·열 및 병합 좌표를 분석해 사용자 프로필로 저장한 뒤 `서식 정리` 작업에 바로 선택합니다.
적용할 때는 표의 행·열·셀 수, 순번, 첫 셀과 첫 행 텍스트를 조합해 대응 표를 찾으며,
대상 표 내용은 유지한 상태로 서식만 복제합니다.
일반 본문이 전혀 없는 표 전용 문서는 표 본문 셀의 대표 문자 서식(없으면 머리글 셀)을
본문 서식 대체값으로 사용하므로 표만 있는 양식도 프로필로 저장할 수 있습니다.
세부 설정의 **서식 복사하기**를 이용하면 저장 이름을 직접 지정할 수 있습니다.

서식 프로필은 `%APPDATA%\HwpAutoDocFit\formats`에 JSON으로 저장됩니다. Markdown은 HWP의
정밀 서식 속성과 병합 셀을 표현할 표준 문법이 없어 프로필 저장 형식으로 사용하지 않습니다. JSON은
숫자 단위, HWP 전용 참조 속성 및 셀 구조를 손실 없이 저장하면서 이전 버전 프로필과도 호환됩니다.

## EXE 빌드와 자동 업데이트

`build.bat`을 실행하면 `dist\HWP_AutoDocFit.exe`가 생성됩니다. Pillow와 tkinterdnd2도 EXE에 포함됩니다.

자동 업데이트를 배포하려면 현재 GitLab 프로젝트에 Release를 만들고 다음 규칙을 지킵니다.

- 태그: 현재 앱 버전보다 높은 버전(예: `v1.68`)
- Release 자산 링크 이름: `HWP_AutoDocFit.exe`
- 자산 링크 대상: 빌드한 `HWP_AutoDocFit.exe`를 내려받을 수 있는 URL
- 자동 업데이트를 사용하는 배포 환경에서는 Release API와 자산 링크를 인증 없이 읽고 내려받을 수 있어야 함

배포된 EXE는 시작 후 백그라운드에서 현재 GitLab 프로젝트의 최신 Release를 확인합니다. 새 버전이 있으면 사용자 확인 후 EXE를 다운로드하고 현재 실행 파일을 교체한 뒤 다시 실행합니다. 네트워크 오류나 Release가 없는 경우 앱 실행에는 영향을 주지 않습니다.
결과는 입력 형식과 관계없이 원본과 같은 폴더에 `원본파일명(자간조정).hwpx`로 저장됩니다.
HWP 입력은 임시 작업 공간에서 HWPX로 변환되므로 원본 HWP 파일은 그대로 유지됩니다.

### 고급 문서 도구

실행창의 **고급 문서 도구**에서는 kordoc v4 문서 엔진을 선택적으로 사용합니다.

- 고급·페이지별 Markdown, 공통 문서 IR(JSON), RAG 구조 청크
- 표 추출·데이터표/레이아웃표 분류, 페이지 이미지 미리보기
- 블록·셀 단위 신구대조, 누름틀·양식 필드 분석과 자동 채우기
- 원본 서식 보존 텍스트 패치, 날짜·금액·붙임 등 공문서 표기법 검수
- Markdown을 보고서·계획서·기안문 프리셋 HWPX로 생성

이 기능에는 [Node.js 18 이상](https://nodejs.org/ko/download)이 필요합니다. 고급 문서 도구 창의
**Node.js LTS 받기** 버튼에서 설치 페이지를 열 수 있으며, 설치 후 앱을 다시 실행해야 합니다.
앱은 `npx -y kordoc@^4`로 MIT 라이선스의
kordoc 엔진을 실행하며, Node가 없어도 기존 HWP/HWPX 편집 기능은 그대로 사용할 수 있습니다.
폐쇄망 배포 환경은 사전에 kordoc npm 패키지를 내부 저장소나 오프라인 캐시에 준비해야 합니다.
설정은 `%APPDATA%\HwpAutoDocFit\settings.json`에 저장됩니다.
보고서 표준서식은 `□`, `ㅇ`, `-`, `※` 등 문장부호로 시작하는 문단에만
적용됩니다. 각 작업의 전체 로그는 원본 문서 폴더에
`원본파일명(작업로그-YYYYMMDD-HHMMSS).log`로 저장됩니다.

## 기본 검증

```powershell
.\.venv\Scripts\python.exe -m py_compile hwp-auto-docfit.py docfit_core\__init__.py docfit_core\hwpx.py
.\.venv\Scripts\python.exe -c "import runpy; runpy.run_path('hwp-auto-docfit.py', run_name='import_check')"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

GitLab CI는 연결된 Linux `security-deploy` Runner에서 공통 소스와 HWPX 코어를 검사합니다.
Windows EXE는 Windows에서 전체 테스트 후 빌드한 `release-assets/HWP_AutoDocFit.exe`를 태그
파이프라인이 공식 Release 자산으로 게시합니다.
실제 문서 편집 검증에는 한글과 보안 모듈 DLL이 필요합니다.
