# HWP AutoDocFit 프로젝트 총괄 매니저 인수인계서 (Handover Dossier)

**수신**: 프로젝트 총괄 매니저 & 수석 개발자 코덱스 (Codex)  
**발신**: 팀장 제미나이 1 (Windows 본 PC)  
**일자**: 2026-10-26 (사용자 확정 지침)  
**승인**: 사용자 확정 ("프로젝트 총괄 메니저를 코덱스로 변경할게. 코덱스가 모든 워커를 지휘하여 개발을 진행할거야. 코덱스에게 인수인계서 작성서 인계해")

---

## 1. 프로젝트 총괄 지휘 권한 이양 선언

2026년 10월 26일부로 **코덱스(Codex)가 HWP AutoDocFit 프로젝트의 총괄 매니저(Project General Manager) 겸 수석 개발자(Principal Architect)**로 공식 취임하며, 전체 워커(제미나이 1, 제미나이 2, 제미나이 3, 젬마 4)에 대한 기획·설계·업무 배분·코드 검수·릴리즈 승인의 전권을 행사합니다.

---

## 2. 개편된 5인 워커 조직 체계 및 지휘선

```
┌────────────────────────────────────────────────────────────────────────┐
│             [프로젝트 총괄 매니저 & 수석 개발자] 코덱스 (Codex)         │
│  - 전체 프로젝트 로드맵 기획 및 핵심 아키텍처 설계 수립                 │
│  - 전 워커 업무 지휘 및 작업 하달, 일정 총괄 관리                      │
│  - 전 워커 코딩 산출물 검수, 코드 결함 탐지 및 개선안 지시            │
│  - 기술적 충돌 최종 판정 및 공식 릴리즈 배포 승인                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 전권 지휘 및 업무 하달
┌───────────────────────────────────▼────────────────────────────────────┐
│              [팀장 & Windows 실기기 통합] 제미나이 1 (본 PC)            │
│  - 총괄 매니저 코덱스의 설계 및 지휘 하에 보조 코딩 및 업무 수행      │
│  - 실제 Windows 환경 한컴오피스 한/글(2020/2024) COM 실전 테스트 집중 │
│  - 전 워커(Mac, 클라우드) 산출물 병합 및 바이너리 빌드/배포 실무 실행 │
│  * 코덱스 일일 사용한도 소진 시 한시적 역할 대행(리셋 시 즉시 복귀)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        ▼                                                       ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐
│     [코드개발] 제미나이 2     │       │     [코드개발] 제미나이 3     │
│       (MacBook Air)           │       │         (Mac Studio)          │
│  - 코덱스 설계 기반 주 코딩   │       │  - 코덱스 설계 기반 주 코딩   │
│  - UI/UX, 크로스플랫폼 개발   │       │  - 그래픽 캔버스, 엔진 개발   │
└───────────────┬───────────────┘       └───────────────┬───────────────┘
                │ 일부 업무 분담                        │ 일부 업무 분담
                └───────────────────────┬───────────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │      [보조개발] 젬마 4        │
                        │      (Mac Studio Ollama)      │
                        │  - 제미나이 2, 3 서브모듈 분담│
                        │  - 경량 로컬 검증 및 보조 코딩│
                        └───────────────────────────────┘
```

---

## 3. 트랙별 개발 진행 현황 및 인수인계 항목

### [트랙 1] 1.80.x 안정화 유지보수 (`C:\HWP_AUTODOCFIT\v1803\sec`)
1. **v1.80.14 정식 배포 완료**:
   - 표 템플릿 상단 중복 메뉴 바 전면 삭제 (화면 수직 공간 극대화).
   - PPT 스타일 1줄 리본(Single-row Category Ribbon, 36px/28px) 및 전폭 검색창 적용.
   - 상세창 우측 상단 `[ 📋 한/글로 복사 (Ctrl+V) ]` 즉시 복사 버튼 탑재.
   - GitHub Releases 및 GitLab downloads 배포 완료 (보안 스캔 5종 ALL PASS).
2. **v1.80.15 긴급 버그 수정 (코덱스 직접 검수 완료)**:
   - **결함 내용**: `내어쓰기 테스트.txt` 일괄 적용(`all` 모드) 시 개요·요약 상자(한 칸 표)의 자간 조정 단계(`single_cell_spacing`)가 `format` 전용으로 제한되어 건너뛰어지던 문제.
   - **조치 사항**: `docfit_core/stage_selection.py` 및 `docfit_engine/pipeline.py` 수정 완료, `tests/test_pipeline_review.py` 12개 교차 회귀 시험 통과.
   - **현재 상태**: 코덱스 수석 검수([CODEX_REVIEW_18015_FIX.md](file:///C:/HWP_AUTODOCFIT/v1803/sec/docs/CODEX_REVIEW_18015_FIX.md)) 승인 하에 `build_dist.bat` 패키징 빌드 진행 중. 빌드 완료 즉시 GitHub & GitLab에 v1.80.15 게시 예정.

### [트랙 2] 2.0.0 차세대 단일 셸 워크스페이스 (`C:\HWP_AUTODOCFIT\v1803\v2`)
1. **코어 세션 엔진 구현 완료 (코덱스 설계)**:
   - `docfit_core/session/document_session.py`: 원본 해시 고정, 작업 사본 배타 생성, revision 관리.
   - `docfit_core/session/command_bus.py`: 원자적 트랜잭션, Undo/Redo 스택, 버전 충돌(`RevisionConflict`) 방지.
   - `docfit_core/session/style_resolver.py`: 6단계 계단식 서식 상속 및 우선순위 리졸버.
   - 검증: [`tests/test_v2_session.py`](file:///C:/HWP_AUTODOCFIT/v1803/v2/tests/test_v2_session.py) 19개 단위 시험 전수 통과.
2. **Flutter 6-탭 내비게이션 셸 및 어댑터 완성**:
   - `tab_navigation_shell.dart`: `IndexedStack` 기반 탭 전환 시 6개 캔버스 상태 영구 보존.
   - `workspace_adapters.dart`: 6개 작업 영역(문서편집, 표템플릿, 표그림판, 다이어그램, 마인드맵, 파일변환)을 연결하는 `IntegratedWorkspace` 완성.
   - 검증: `tab_navigation_shell_test.dart`, `workspace_adapters_test.dart` 전수 통과, `flutter analyze` 0 warnings.
   - GitLab 원격 동기화: 보안 스캐너 5종 ALL PASS 후 `dev/2.0.0` 푸시 완료.

---

## 4. 환경 사양 및 인프라 매뉴얼

- **주요 저장소 위치**:
  - 1.80.x 유지보수: `C:\HWP_AUTODOCFIT\v1803\sec` (브랜치: `main`)
  - 2.0.0 차세대: `C:\HWP_AUTODOCFIT\v1803\v2` (브랜치: `dev/2.0.0`)
- **원격 저장소 (Git Remotes)**:
  - `github`: `https://github.com/haijun93/hwp-auto-docfit.git`
  - `origin`: `https://gitlab.aigov.go.kr/haijun93/hwp_autodocfit.git`
  - *인증*: Git Credential Manager를 통해 GitHub Token 및 GitLab 보안 인증 자동 주입.
- **주요 빌드 명령어**:
  - Flutter 빌드: `powershell -File .\build_flutter.ps1`
  - Python 단위 시험: `python -m unittest discover tests`
  - 배포 패키징: `cmd /c "build_dist.bat"`
- **워치독 러너**:
  - 코덱스 실행 및 한도 소진 감지: `python scripts/run_codex_with_watchdog.py -f <prompt_file> -w <workdir>`

---

## 5. 총괄 매니저 코덱스 직할 후속 지휘 과제

1. **v1.80.15 배포 실무 지휘**:
   - 현재 진행 중인 빌드 산출물(`HWP_AutoDocFit_v1.80.15_Portable.exe`, `Setup.exe`) 해시 확인 및 GitHub Releases 등록, GitLab 태그 푸시 완료 감독.
2. **2.0.0 진입점 마운트 및 캔버스 연동 지휘**:
   - 제미나이 2, 3에게 `flutter_ui/lib/main.dart`의 `DocFitApp`을 신규 `IntegratedWorkspace`로 마운트하도록 지시.
   - 표그림판·다이어그램에서 생성된 HWPX 블록이 한/글 클립보드 및 COM 드라이버로 원활히 복사되도록 데이터 교환 버스 설계 하달.
3. **제미나이 1 한/글 실기기 테스트 결과 분석 및 피드백**:
   - Windows 실제 환경에서 한/글 COM 실전 테스트 로그를 전달받아 취약점을 분석하고 개선 코딩 명령 하달.

---

## 6. [정정] 총괄 지휘권 재이관 (2026-10-26 23:48 KST, 사용자 지시)

사용자 지시("지금 시간부로 다시 프로젝트 진행을 제미나이1이 맡도록 하겠어")에 따라 **프로젝트 총괄 진행은 제미나이 1이 다시 맡는다.** 위 §1~§5의 코덱스 총괄 체계는 이 시각부로 효력을 잃는다. 진행 현황과 미결 카드는 `docs/CODEX_SUPPORT_BRIEFING_2026-10-26.md`를 기준으로 이어간다.
