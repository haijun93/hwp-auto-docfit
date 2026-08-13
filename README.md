# HWP Auto DocFit (한/글 자동 자간 맞춤 도구)

한글(HWP, HWPX) 문서의 줄바꿈 단어 및 공문서 문장부호/번호 항목의 자간을 자동으로 조정하여, 문서의 줄 수를 최적화하고 문서 가독성을 높여주는 자동화 프로그램 및 AI 에이전트용 **MCP(Model Context Protocol) 서버**입니다.  
고수준 한글 자동화 래퍼 라이브러리인 [`pyhwpx`](https://martiniifun.github.io/pyhwpx/)를 기반으로 구축되었습니다.

---

## 🚀 주요 기능

1. **자동 줄바꿈 자간 조정 (LineFit)**
   - 줄 끝에서 단어가 걸쳐 잘리는 경우 앞/뒤 길이를 분석하여 자동으로 자간 축소(`-1%`) 또는 확대(`+1%`) 수행
   - 최대 15회 조정 후에도 해결되지 않으면 원상 복구(Undo)하여 서식 깨짐 방지
2. **공문서 문장부호/개조식 번호 2줄 축소 알고리즘**
   - 항목 기호(`-`, `○`, `□`, `■`, `▶` 등) 및 가나다 순 번호(`1.`, `가.`, `①`, `㉠` 등)로 시작하는 문장 인식
   - 같은 문단 내 자동 줄바꿈으로 인해 2번째 줄이 5자 이하로 넘어간 경우, 1줄로 맞추어질 때까지 자간 자동 축소
3. **항상 최신 HWPX 포맷으로 안전 저장**
   - HWP 및 HWPX 문서를 처리한 후 항상 `[파일명](자간조정).hwpx` 표준 포맷으로 저장
4. **`pyhwpx.ctrl_list` 기반 표 / 글상자 완벽 순회**
   - 표 및 텍스트 박스 내부의 모든 텍스트 영역을 누락 없이 순회 처리
5. **AI 에이전트용 MCP (Model Context Protocol) 서버 탑재**
   - Claude Desktop, Cursor, Antigravity 등의 AI가 한/글 문서를 직접 분석(`analyze_hwp_document`)하고 자간을 맞춤(`fit_hwp_document`)할 수 있는 표준 도구 제공
6. **GUI / CLI / MCP 다중 모드 지원**
   - 마우스 드래그 앤 드롭 GUI 창
   - 터미널 CLI 일괄 처리 (`python hwp_auto_docfit.py 문서.hwp`)
   - AI 에이전트 백엔드 (`python mcp_server.py`)

---

## 💻 실행 환경 및 요구 사항

* **운영체제**: Windows 10 / 11 (문서 수정/저장 시) / macOS & Linux (문서 분석 Dry-run 지원)
* **한글 버전**: 한글 2020 이상 (Windows 환경)
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
├── hwp_auto_docfit.py                 # GUI 메인 프로그램 & CLI 디스패처 (pyhwpx 기반)
├── mcp_server.py                      # AI 에이전트용 Model Context Protocol (MCP) 서버
├── hwp auto letter spacing.py         # LineFit CLI 스크립트 (초기 버전)
├── FilePathCheckerModuleExample.dll   # 한글 보안 승인 DLL
├── requirements.txt                   # 프로젝트 의존성 목록
├── tests/
│   └── test_hwp_docfit.py             # 단위 테스트 및 시뮬레이션 검증 스위트
├── .github/
│   └── workflows/
│       └── build-windows-exe.yml      # PyInstaller Windows 실행 파일 CI 빌드 워크플로우
└── docs/
    └── reference/                     # 한글 Automation 공식 레퍼런스 문서
```

---

## 🛠️ 실행 방법

### 1. GUI 모드로 실행
```bash
python hwp_auto_docfit.py
```

### 2. CLI 모드로 특정 문서 일괄 처리
```bash
python hwp_auto_docfit.py "C:\Users\username\Documents\보고서.hwp"
```

### 3. AI 에이전트 MCP 서버 연동 (Claude Desktop / Cursor)
`claude_desktop_config.json` 파일에 아래와 같이 추가합니다:
```json
{
  "mcpServers": {
    "hwp-auto-docfit": {
      "command": "python",
      "args": ["C:/path/to/hwp-auto-docfit/mcp_server.py"]
    }
  }
}
```
* **제공 MCP 도구**:
  * `analyze_hwp_document(file_path)`: 문서 문단 구조 및 2줄 압축 대상 지점 사전 분석
  * `fit_hwp_document(file_path)`: 문서 자간 맞춤 및 HWPX 결과 파일 생성
  * `batch_fit_documents(folder_path)`: 폴더 내 문서 일괄 자간 맞춤

### 4. Windows 단일 실행 파일(`.exe`) 빌드
```bash
pip install pyinstaller pywin32 tkinterdnd2 pyhwpx
pyinstaller --onefile --windowed --collect-all tkinterdnd2 --collect-all pyhwpx --name "HWP_Auto_DocFit_v4.1" "hwp_auto_docfit.py"
```
빌드 완료 후 생성된 `dist\HWP_Auto_DocFit_v4.1.exe`와 같은 폴더에 `FilePathCheckerModuleExample.dll`을 함께 배치하여 사용합니다.