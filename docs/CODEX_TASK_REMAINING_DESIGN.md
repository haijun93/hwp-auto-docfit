# Codex Task: HWP AutoDocFit 2.0.0 잔여 과제 상세 설계 완성 지시서

- **수신**: 수석 아키텍트 & 개발자 코덱스 (Codex)
- **발신**: 프로젝트 총괄 매니저 제미나이 1 (Windows 본 PC)
- **일자**: 2026-10-27
- **근거**: 사용자 직접 지시 ("코덱스 현재 유휴상태야. 지금 즉시 설계를 완성하라고 지시해")
- **작업 저장소**: `C:\HWP_AUTODOCFIT\v1803\v2` (브랜치: `dev/2.0.0`)

---

## 1. 지시 배경 및 목표

1. **v1.80.15 정식 릴리즈 완료**:
   - `내어쓰기 테스트.txt` 일괄 적용 자간 버그 수정, 53개 회귀 시험 통과, 실문서 조판 및 화면 검증(C1) 완료 후 GitHub 및 GitLab 배포가 완료되었습니다.
2. **2.0.0 단일 셸 워크스페이스 마운트 완료**:
   - 코덱스가 설계한 6-탭 단일 셸 계약(`TabNavigationShell`, `IntegratedWorkspace`)이 `flutter_ui/lib/main.dart`의 `DocFitApp` 최상위 진입점에 정식 연결되었으며, 위젯 통합 시험(`test/docfit_app_integrated_shell_test.dart`) 100% 통과 및 `dev/2.0.0` 원격 푸시(5종 보안 스캔 ALL PASS)가 완료되었습니다.
3. **현 시점 핵심 과제**:
   - 2.0.0 정식 릴리즈 전 남아 있는 **2대 핵심 미완료 영역(T17 비교 뷰어 격리 설계, 캔버스별 구체 Command 스키마 설계)**에 대해 수석 개발자 코덱스가 즉시 최종 기술 설계를 완성하고 명세서(`docs/V2_REMAINING_DESIGN_SPEC.md` 또는 `docs/V2_CORE_CONTRACTS.md` 확장)를 확정해야 합니다.

---

## 2. 코덱스가 완성해야 할 3대 상세 설계 요구사항

### [과제 1] T17 비교 뷰어(한/글 OLE 호스트 분리) IPC 및 수명 주기 설계
- **배경**: 코덱스 C26 결과 보고서에서 *"T17은 미완료: 별도 프로세스 분리, 한/글 OLE 호스트 분리, 새 뷰어 창 분리 아직 미실행"*으로 규정됨.
- **설계 요구사항**:
  1. **독립 OLE 호스트 프로세스 분리 규격**:
     - 메인 Flutter 프로세스/WebView2가 블로킹되지 않도록, 한/글 OLE 컨트롤을 독립 프로세스(`python -m docfit_engine.diff_host` 등)로 띄우는 아키텍처 정의.
  2. **프로세스 수명 주기 및 IPC 통신 프로토콜**:
     - 원본 파일과 결과 파일의 경로(읽기 전용 보호), 좌우 동기화 스크롤/페이지 이동 명령 전달 방식.
     - 사용자 뷰어 닫기 또는 메인 앱 종료 시 좀비 프로세스 방지(Process Guard / 자가 종료 타이머).
  3. **Flutter 측 UI 결합점**:
     - `IntegratedWorkspace` 내에서 T17 뷰어 요청 시 Flutter 다이얼로그 또는 탭 화면 연동 규격.

### [과제 2] 캔버스(표그림판·다이어그램·마인드맵) 전용 구체 Command 클래스 설계
- **배경**: `V2_CORE_CONTRACTS.md`에서 *"탭 3·4·5 모델 편집을 순수 Command로 감싼다"*는 원칙만 수립됨.
- **설계 요구사항**:
  1. `docfit_core/session/canvas_commands.py` (또는 동등 모듈) 내 구체적 Command 클래스 정의:
     - `InsertTableSketchCommand`: 표그림판 격자/선 JSON 데이터를 HWPX 표준 `<hp:tbl>` 객체로 변환하여 세션 draft에 삽입.
     - `InsertDiagramShapeCommand`: React Flow 형상/화살표 커넥터 데이터를 HWPX `<hp:lineseg>` 및 그래픽 객체로 변환하여 삽입.
     - `InsertMindmapTreeCommand`: 마인드맵 계층 구조 트리를 개요 번호/한 칸 표 요약 블록으로 변환하여 삽입.
  2. **`CommandBus` 트랜잭션 및 Undo/Redo 정규화**:
     - `draft` 딕셔너리 내 저장 위치, `before`/`after` 스냅샷 키 구조, `expected_revision` 원자성 보장 규격.

### [과제 3] Win32 Tk 파일 다이얼로그(B01~B14) 완전 대체 규격
- **배경**: `desktop_web_ui.py`에 남아 있는 `self._tk(..., front=True)` Win32 파일창 호출부 제거.
- **설계 요구사항**:
  - Flutter `file_picker` 및 백엔드 IPC 파일 수신 브리지 규격 확정.

---

## 3. 산출물 및 검증 기준

1. **설계 산출물 문서**:
   - `docs/V2_REMAINING_DESIGN_SPEC.md` 작성 또는 `docs/V2_CORE_CONTRACTS.md` 개정.
2. **코드 뼈대 및 단위 계약 시험**:
   - `docfit_core/session/canvas_commands.py` (또는 관련 모듈) 프로토타입.
   - `tests/test_v2_canvas_commands.py` 단위 시험.
3. **보고**:
   - `docs/CODEX_CLAUDE_SPACING_COORDINATION.md`에 설계 완료 보고 추가.
