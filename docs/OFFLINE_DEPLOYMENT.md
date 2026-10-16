# 폐쇄망 배포 — v1.76.2

Windows 배포 EXE에 Node.js 22.23.3 및 kordoc 4.21.30 런타임을 포함합니다.
사용자는 HWP_AutoDocFit_kordoc_runtime.zip을 따로 받지 않습니다.

## 첫 실행

1. HWP_AutoDocFit.exe를 실행합니다.
2. 내장 ZIP의 SHA256을 확인한 뒤 C:\HWP_AUTODOCFIT에 자동 저장합니다.
3. 같은 경로의 kordoc-runtime/4.21.30에 안전하게 압축을 풉니다.
4. 쓰기 권한이 없으면 %LOCALAPPDATA%\HwpAutoDocFit으로 대체합니다.
5. 설치된 엔진은 다음 실행부터 재사용하며, 첫 설치에도 온라인 접속은 필요하지 않습니다.

사용자 원본 문서는 설치 경로로 이동하지 않습니다. 변환 결과는 원본 옆에 새 이름으로 생성합니다.
기존의 실행 파일 옆 ZIP·설치 폴더 검색은 이전 배포 호환용으로 유지합니다.

## 지원과 별도 도구

- TXT·MD→HWPX는 내장 엔진, PDF·PNG·JPG는 내장 엔진과 설치된 한/글을 사용합니다.
- HWPX→TXT·MD는 내장 분석기를 사용합니다. 글꼴·쪽 배치·그림은 텍스트 결과에 포함되지 않습니다.
- HWP→HWPX 및 HWP·HWPX→PDF·그림은 설치된 한/글을 사용합니다.
- DOCX·EPUB 출력용 Pandoc은 별도 도구입니다.
- OCR 모델은 포함하지 않습니다. 그림·스캔 문서의 글자 인식은 준비 상태에 따라 제한됩니다.

## 개발·빌드

Windows의 build.bat과 CI가 scripts/build_kordoc_runtime.ps1을 먼저 실행해 resources에 꾸러미와 SHA256을 만듭니다.
공식 Node.js ZIP 체크섬과 npm 잠금 파일 무결성을 검증하고 PyInstaller가 꾸러미를 EXE에 포함합니다.
네트워크는 빌드 PC에서만 의존성을 준비할 때 사용합니다. 런타임 ZIP은 개발·빌드 증거로 남기며 사용자 릴리즈의 필수 별도 다운로드로 첨부하지 않습니다.
