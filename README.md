# HWP Auto DocFit (한/글 자동 자간 맞춤 도구)

한글(HWP, HWPX) 문서의 줄바꿈 단어 및 공문서 문장부호/번호 항목의 자간을 자동으로 조정하여, 문서의 줄 수를 최적화하고 문서 가독성을 높여주는 Windows 자동화 프로그램입니다.  
고수준 한글 자동화 래퍼 라이브러리인 [`pyhwpx`](https://martiniifun.github.io/pyhwpx/)를 기반으로 구축되었습니다.

---

## 🚀 주요 기능

1. **자동 줄바꿈 자간 조정 (LineFit)**
   - 줄 끝에서 단어가 걸쳐 잘리는 경우 앞/뒤 길이를 분석하여 자동으로 자간 축소(`-1%`) 또는 확대(`+1%`) 수행
   - 최대 15회 조정 후에도 해결되지 않으면 원상 복구(Undo)하여 서식 깨짐 방지
2. **공문서 문장부호/개조식 번호 2줄 축소 알고리즘**
   - 항목 기호(`-`, `○`, `□`, `■`, `▶` 등) 및 가나다 순 번호(`1.`, `가.`, `①`, `㉠` 등)로 시작하는 문장 인식
   - 같은 문단 내 자동 줄바꿈으로 인해 2번째 줄이 5자 이하로 넘어간 경우, 1줄로 맞추어질 때까지 자간 자동 축소
3. **`pyhwpx.ctrl_list` 기반 표 / 글상자 완벽 순회**
   - 표 및 텍스트 박스 내부의 모든 텍스트 영역을 누락 없이 순회 처리
4. **GUI 드래그 앤 드롭 및 다중 처리**
   - HWP/HWPX 파일 및 폴더를 마우스 드래그 앤 드롭으로 간편하게 추가
   - 작업 진행률 표시바 및 실시간 상세 로그 제공
   - 원본 파일은 보존하며 `파일명(자간조정).hwp[x]` 형태로 안전하게 자동 저장
5. **보안 승인 모듈 자동 설정**
   - 한글 OLE Automation의 접근 허용 팝업을 차단하는 보안 모듈(`FilePathCheckerModuleExample.dll`) 자동 설치 및 레지스트리 자동 등록

---

## 💻 실행 환경 및 요구 사항

* **운영체제**: Windows 10 / 11
* **한글 버전**: 한글 2020 이상
* **Python**: Python 3.10 이상 (64-bit 권장)

### 의존성 패키지 설치
```bash
pip install -r requirements.txt
# 또는
pip install pyhwpx pywin32 tkinterdnd2
```

---

## 📂 파일 구조

```
hwp-auto-docfit/
├── hwp_auto_docfit.py                 # HWP Auto DocFit GUI 메인 프로그램 (pyhwpx 기반)
├── hwp auto letter spacing.py         # LineFit CLI 스크립트 (초기 버전)
├── FilePathCheckerModuleExample.dll   # 한글 보안 승인 DLL
├── requirements.txt                   # 프로젝트 의존성 목록
├── .github/
│   └── workflows/
│       └── build-windows-exe.yml      # PyInstaller Windows 실행 파일 CI 빌드 워크플로우
└── docs/
    └── reference/                     # 한글 Automation 공식 레퍼런스 문서
```

---

## 🛠️ 실행 방법

### 1. Python 스크립트로 실행
```bash
python hwp_auto_docfit.py
```

### 2. Windows 단일 실행 파일(`.exe`) 빌드
PyInstaller를 통해 독립 실행 파일로 빌드할 수 있습니다:
```bash
pip install pyinstaller pywin32 tkinterdnd2 pyhwpx
pyinstaller --onefile --windowed --collect-all tkinterdnd2 --collect-all pyhwpx --name "HWP_Auto_DocFit_v4.1" "hwp_auto_docfit.py"
```
빌드 완료 후 생성된 `dist\HWP_Auto_DocFit_v4.1.exe`와 같은 폴더에 `FilePathCheckerModuleExample.dll`을 함께 배치하여 사용합니다.