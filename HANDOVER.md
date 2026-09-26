# 인수인계서 — 한글문서 후처리 도구 (HWP AutoDocFit)

작성: 2026-09-26, Claude Code 세션에서 작성. 대상: 이 저장소 작업을 이어받는 AI 코딩 에이전트(ChatGPT Codex, Gemini CLI 등)와 담당자.
작업을 시작하기 전에 이 문서를 끝까지 읽고, 모르는 내용은 `README.md`와 `TODO.md`를 참고하세요.

---

## 1. 한눈에 보기

| 항목 | 현재 값 |
|---|---|
| 제품 | 한/글 2020 문서(HWP/HWPX)를 공문서 규칙에 맞게 자동 후처리하는 Windows 데스크톱 앱(Python·Tkinter) |
| 최신 배포 | **v1.68 Beta 2** (2026-09-26) — 작업 유형 4가지 분리 |
| 직전 배포 | v1.68 Beta 1 (2026-09-26) — 알파 1.68 Alpha 1~6 개선 전체 반영 |
| 브랜치 | `main` = 베타(배포선), `alpha` = 새 기능 시험판 |
| 원격 | `github` = 원본(https://github.com/haijun93/hwp-auto-docfit), `origin` = GitLab 백업(gitlab.aigov.go.kr/haijun93/hwp_autodocfit) |
| 사용자 업데이트 | 앱이 GitLab "최신 릴리스"를 조회해 새 exe를 알림 |
| 테스트 | `python -m unittest discover -s tests` → 286개 통과(2026-09-26 기준) |
| 사용자 | 마포구청 공무원(개발자이자 실사용자). 한국어로 소통, 결과는 개조식 공문서 문체를 선호 |

---

## 2. 개발 환경

- **Windows 전용**. 한/글 2020이 설치되어 있고 COM 객체 `HwpFrame.HwpObject`를 쓸 수 있어야 실제 문서 처리가 됩니다.
- **Python 3.14** 가상환경: `.venv\Scripts\python.exe` (의존성: `requirements.txt` — pywin32, tkinterdnd2, Pillow, defusedxml)
- 보안 모듈 `MapoHwpAutoDocFitSecurity.dll`이 `hwp-auto-docfit.py`와 같은 폴더에 있어야 합니다(한/글 자동화 보안 승인용, 앱이 최초 실행 시 등록).
- 저장소 경로에 **한글과 공백**이 있습니다(`C:\Users\haiju\OneDrive\바탕 화면\HWP_AutoDocFit\mapo-agent-1`). 셸 명령에서는 항상 따옴표로 감싸세요.
- 실행: `.venv\Scripts\python.exe hwp-auto-docfit.py`
- 모듈 임포트 시 `docfit_core`를 찾도록 저장소 루트에서 실행하거나 `PYTHONPATH=.`을 지정하세요.
- 콘솔 한글 깨짐 방지: `PYTHONIOENCODING=utf-8`

---

## 3. 코드 구조

| 경로 | 역할 |
|---|---|
| `hwp-auto-docfit.py` (약 15,000줄) | 앱 본체. COM 자동화 파이프라인, 서식 분석, GUI 전체. **CRLF 줄바꿈**, 식별자·주석 대부분 한국어 |
| `docfit_core/hwpx.py` | HWPX 안전 검사(ZIP bomb·경로 조작), 구조 파싱, Markdown 내보내기, 무결성 비교 |
| `docfit_core/stage_selection.py` | 작업 유형별 세부 작업(단계) 목록과 기본 선택값 |
| `docfit_core/style_hierarchy.py` | 문두기호(□·ㅇ·-·※ 등) 판별, 들여쓰기 기반 계층 분석 |
| `docfit_core/style_inventory.py` | **문서 스타일 전수 분석**(정의/사용, 스타일 유형, 위첨자·글자색·음영, 표 종류)과 **예시 서식 HWPX 생성** |
| `docfit_core/labeled_text.py` | 라벨 입력 모드(`제목:/상자:/네모:/원:/바:/당구:/주석:/참고:/표:`) 파서 |
| `docfit_core/ai_prompts.py` | 생성형 AI에게 라벨 형식으로 답하게 하는 공문서 프롬프트 모음 |
| `docfit_core/writing_aids.py` | 작성 도우미 순수 함수: 금액 한글화, 날짜·요일, 표 계산, 쉼표·천원, 만 나이·주민번호 가리기, 번호 매기기, 회신공문 |
| `docfit_core/final_evaluation.py` | 작업 목표 대비 최종검수 점수·판정 |
| `docfit_core/number_check.py` | 본문 수치와 인접 표 수치 대조(읽기 전용) |
| `docfit_core/pasted_text.py` | AI 채팅 답변 붙여넣기 정리, 개조식 변환 |
| `docfit_core/outline_ops.py`, `document_review.py`, `document_rules.py`, `korean_proofread.py`, `kordoc_bridge.py`, `style_profile_edit.py` | 아웃라이너, 문서 구조 검토, 공공언어 교정, kordoc(Node.js) 변환 연동, 서식 구조 검토 편집 |
| `scripts/` | 코퍼스 벤치마크, 결과 감사, `style_inventory.py`(명령줄 스타일 분석) 등 |
| `tests/` | unittest. GUI 테스트는 실제 Tk 창을 띄우므로 데스크톱 세션이 필요 |
| `releases/vX.Y-beta.N.md` | 릴리스 노트(GitLab 릴리스 본문으로 그대로 쓰임) |
| `release-assets/HWP_AutoDocFit.exe` | CI가 만든 배포용 exe |
| `.github/workflows/build-windows-exe.yml` | exe 빌드(빌드 브랜치 푸시 때만 실행) |
| `.gitlab-ci.yml` | 태그 푸시 시 GitLab 릴리스 자동 생성 |
| `.claude/skills/gongmunseo-report-writing/` | 공문서 작성 스킬(행정업무운영 편람 규정 포함). 다른 에이전트도 문체 기준으로 참고 가능 |
| `TODO.md` | 작업 예정·완료 기록(사용자가 "나중에 해"라고 한 항목의 원천) |

---

## 4. 핵심 동작 이해

### 작업 유형 (실행창 카드 4장, v1.68 Beta 2부터)
| 카드 | 내부 모드 | 결과 파일 접미사 |
|---|---|---|
| 자간 정리 | `spacing` | `(자간조정).hwpx` |
| 서식 통일 | `unify` | `(서식통일).hwpx` |
| 서식 적용 | `format` | `(서식적용).hwpx` |
| 한 번에 적용 | `all` | `(일괄적용).hwpx` |

- 빠른 선택: 기본후처리 = 자간 정리 + 서식통일, 전문후처리 = 한 번에 적용 + 서식통일.
- 원본은 절대 덮어쓰지 않습니다. HWP 입력도 결과는 항상 HWPX입니다.

### 처리 파이프라인
- 진입점: `작업_실행(...)` → 문서마다 `문서_처리_1회` → `_문서_처리_1회`(단계별 `stage(name, action)` 호출).
- 단계 켜고 끄기: `stage_enabled(선택_세부작업, key)`, 단계 목록은 `docfit_core/stage_selection.py`.
- 핵심 원칙: **계산보다 한/글 실측**. 자간·내어쓰기·쪽 배치는 한/글에게 실제 커서 위치를 물어 판단합니다.
- 저장 후 결과를 다시 열어 단어 분리·쪽 배치를 검사하고(`검수`), 무결성 비교와 최종검수 보고서(`(최종검수).json`)를 남깁니다.
- 테스트용 헤드리스 실행 예: `scripts/smoke_style_corpus.py` 참고. `ns["작업_실행"]([경로], 실행모드="format", 자동닫기=True, 표준서식=True, 검수=True, 세부작업_선택={...})` 후 `gui_queue`에서 `("saved", …)` 이벤트를 꺼내 결과 경로를 얻습니다.

### 서식 프로필
- 기본 서식 + 사용자 서식(`%APPDATA%\HwpAutoDocFit\` 아래 JSON). 예시 문서를 분석(`hwpx_서식_분석`)해 만듭니다.
- 프로필에 `organization`(기관)을 넣으면 목록에 `[기관] 이름`으로 묶여 보입니다.
- 문서 첫머리 1×1 표는 제목 표로 판정되어 제목 서식이 적용됩니다(`제목_유형판별`, `제목_대상찾기`).

---

## 5. 작업 규칙 (반드시 지킬 것)

1. **새 기능은 `alpha` 브랜치에서** 개발하고, 사용자가 "베타에 적용"이라고 하면 `main`으로 합쳐 배포합니다.
2. **푸시 순서**: `github` 먼저, 그다음 같은 ref를 `origin`(GitLab)에 미러링. GitLab 쪽에서 개발하거나 충돌을 풀지 마세요.
3. **GitLab 보안 검사(Semgrep 등)가 푸시를 거부할 수 있습니다.** 특히 새로 만들거나 바꾼 파일에서 표준 `xml` 모듈을 import하면 `use-defused-xml` 규칙에 걸립니다. XML 파싱은 `defusedxml`만 쓰고, 새 모듈에는 표준 `xml`을 넣지 마세요(검사 우회용 주석이 아니라 실제로 고칠 것). 옛 태그 `v1.64`는 이 문제로 GitHub에만 있습니다.
4. `hwp-auto-docfit.py`는 **CRLF**입니다. 파일 전체를 LF로 바꾸는 편집을 하지 마세요(diff가 수만 줄로 불어남). 바이트 단위로 읽고 쓰거나 줄바꿈을 보존하세요.
5. 코드 스타일: 주변 코드처럼 한국어 식별자·한국어 주석, 주석 밀도도 맞춥니다.
6. 커밋 메시지: 한국어로 "무엇을 왜" 요약, 본문은 `-` 개조식. 사용자가 요청할 때만 커밋·푸시합니다.
7. 사용자 문서(예: `111\테스트 문서`)는 **원본을 수정하지 말고** 임시 사본으로 시험하세요.
8. 외부 프로그램(범피스·범정부오피스 등)을 분석한 결과는 기능 아이디어로만 쓰고 코드는 옮기지 않습니다.

---

## 6. 배포 절차 (베타)

1. `alpha` → `main` 병합(보통 fast-forward). 충돌 시 `TODO.md`는 완료 기록이 더 많은 쪽 기준으로 정리.
2. 버전 올리기: `hwp-auto-docfit.py`의 `APP_VERSION`, `README.md` 5행, `website/index.html`(5곳), 새 릴리스 노트 `releases/vX.Y-beta.N.md`(SHA-256 자리는 `SHA256_PLACEHOLDER`).
   - 자동 업데이트는 버전 문자열의 숫자 3개로 비교합니다(`_버전_튜플`: "1.68 Beta 2" → (1, 68, 2)).
3. 전체 테스트 통과 확인 → 커밋 → `git push github main` → `git push origin main`.
4. **exe 빌드**: GitHub CI는 빌드 브랜치 `claude/affectionate-goldberg-ggln7c` 푸시 때만 돕니다.
   - 먼저 `git fetch github` 후 그 브랜치에만 있는 문서·스킬 변경(다른 세션이 남긴 `TODO.md` 등)이 있으면 `main`으로 가져옵니다(CI exe 커밋은 제외).
   - 강제 푸시 없이 `git commit-tree "main^{tree}" -p github/claude/affectionate-goldberg-ggln7c -m "…"`로 main과 같은 내용의 커밋을 얹어 푸시합니다.
   - CI가 `Update built HWP_AutoDocFit.exe from CI run …` 커밋을 올리면(보통 5~10분) 그 커밋을 `main`에 cherry-pick.
5. exe를 실제로 실행해 창 제목의 버전을 확인 → `sha256sum release-assets/HWP_AutoDocFit.exe` 값을 릴리스 노트에 대문자로 기록 → 커밋·푸시(두 원격).
6. **태그**: `git tag -a vX.Y-beta.N -m "…"` → `git push github <태그>` → `git push origin <태그>`. GitLab CI(`release-windows`)가 릴리스와 exe 첨부를 자동으로 만듭니다(토큰 불필요).
7. 확인: `https://gitlab.aigov.go.kr/api/v4/projects/haijun93%2Fhwp_autodocfit/releases/permalink/latest`가 새 태그를 가리키는지, 내려받은 exe 해시가 노트와 같은지.

---

## 7. 알려진 함정 (이번 세션에서 실제로 겪은 것)

- **한/글 COM `MovePos`는 인자 3개**(`MovePos(3, 0, 0)` = 문서 끝). 1개만 넘기면 예외가 납니다.
- **단독 한/글 세션을 닫기 전에 `Clear(1)`**. 저장 안 된 문서가 있으면 `Quit()`에서 "저장할까요?" 창이 떠 무한 대기합니다(이미 `텍스트_hwpx_단독변환`에 반영).
- 표 생성 `HTableCreation.WidthType`: `0` = 단 너비에 맞춤, `2` = 임의 너비(글자 폭만큼 좁아짐).
- **확장자만 .hwpx인 HWP 바이너리**가 실제로 있습니다(예: 수출입동향 문서). `zipfile.is_zipfile`로 확인 후 HWP로 변환하세요(`분석용_hwpx_준비`).
- HWPX 문단 모양의 `hp:switch` 안에는 `hp:case`(실제 hwpunit)와 `hp:default`(두 배 값)가 함께 있습니다. **case 값**을 쓰세요.
- 한/글이 취소선이 없는 글자에도 `strikeout shape="3D"`를 저장합니다. 취소선으로 보지 마세요.
- 시험 중 한/글 프로세스가 남으면 다음 COM 호출이 꼬입니다. 시험 뒤 `Get-Process Hwp`로 확인하고, **직접 띄운 것만** 정리하세요(사용자가 쓰는 한/글 창을 닫지 말 것).
- 셸 heredoc으로 파이썬 코드를 넘기면 `\n`, `\b` 같은 역슬래시가 깨질 수 있습니다. 긴 수정은 파일로 스크립트를 써서 실행하세요.
- PyInstaller 추출물 폴더 안에서 파이썬을 실행하면 추출된 `struct.pyc`가 표준 모듈을 가립니다(외부 exe 분석 시).

---

## 8. 최근 작업 이력 (2026-09-26 세션)

| 커밋 | 내용 |
|---|---|
| `ef93a1f` (alpha) | 문서 스타일 전수 분석·예시 서식, 라벨 입력·AI 프롬프트, 작성 도우미(금액·날짜·표 계산·나이·번호·회신공문·기관 서식) |
| `a768c29` | 알파 병합, **1.68 Beta 1** |
| `0bcb093`, `50fd06f` | 예시 서식 생성의 XML 파싱을 defusedxml로, 원본 XML 구간 잘라 붙이기(GitLab Semgrep 대응) |
| `a0d71ea` | 1.68 Beta 1 릴리스 노트 SHA-256, 태그 `v1.68-beta.1` |
| `bd0b83b` | 작업 유형 4가지 분리(서식 통일 독립) |
| `cf9464c` | **1.68 Beta 2** 버전 |

검증 데이터: `C:\Users\haiju\OneDrive\바탕 화면\111\테스트 문서`(25개 문서). 스타일 분석·예시 서식 생성 25/25, 한/글 열기 25/25, 예시 재분석 시 서식 일치 21/25(큰 문서 4개는 원본 안에서도 값이 갈려 요약 한계).

---

## 9. 다음에 할 일

1. **알파 버전 표기**: `main` 배포 뒤 `alpha`를 `main`에 맞추고 `APP_VERSION`을 `1.69 Alpha 1`로 올리기(사용자 확인 필요).
2. `TODO.md`의 설계 제안(착수 전, 사용자 확인 필요):
   - 앱 UI/UX 개선(원본 보존 문구 상시 노출, 첫 실행 안내, "세부 작업"/"세부 설정" 명칭)
   - 설정 변경 시 실시간 미리보기, 스킨(테마) 선택, 서식 종류 이미지 미리보기
   - 감마 트랙(COM 비의존, rhwp 기반) — 렌더링 없는 구조적 후처리부터
3. 벤치마킹 목록 C 묶음(표·편집 도구): 셀 크기 복사·맞춤, 표 스타일 프리셋, 셀 찾아바꾸기, 목차 생성, 메일머지, 표 대량 계산.
4. 알려진 한계: 큰 문서의 예시 서식은 원본과 대표값이 조금 다를 수 있음(줄간격·※ 서식) → 등록 시 "서식 구조 검토" 화면에서 확인하도록 안내 중.

---

## 10. 빠른 명령 모음 (PowerShell 기준)

```powershell
# 앱 실행
.\.venv\Scripts\python.exe hwp-auto-docfit.py
# 전체 테스트 (약 3~4분, GUI 창이 잠깐 뜸)
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe -m unittest discover -s tests
# 문서 스타일 분석 보고서 + 예시 서식 만들기
.\.venv\Scripts\python.exe scripts\style_inventory.py "문서.hwp" --out 결과폴더
# 원격 상태
git fetch github; git log --oneline -3 github/main; git log --oneline -3 github/alpha
```
