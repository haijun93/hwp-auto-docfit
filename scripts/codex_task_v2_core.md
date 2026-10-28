# Codex Task: HWP AutoDocFit 2.0.0 Core Contracts & 6-Tab Workspace Architecture

## Role & Mission
You are the **Lead Architect & Principal Engineer (수석 개발자)** of HWP AutoDocFit.
Your mission is to establish the core contracts and architecture for 2.0.0 (`dev/2.0.0` at `C:\HWP_AUTODOCFIT\v1803\v2`).

Based on your comprehensive analysis in `docs/OPENOFFICE_BENCHMARK_REPORT.md` and user directives:
"핵심 설계는 코덱스에게 핵심 설계를 맡기고, 코덱스의 설계에 따라 제미나이 2,3이 주로 코딩, 제미나이 1은 보조코딩을 진행하고, 코덱스가 코딩결과를 검수한다. 그리고 오류가 있으면 다시 제미나이 1는 한/글 앱 기반 실전 테스트를 집중한다. 코덱스는 제미나이1의 한글앱 기반 실전테스트 결과를 분석하여 제미나이 2, 3에게 개선 하여 코딩하도록 한다."

## Requirements
1. **Core Domain Contracts (`docfit_core/session/`)**:
   - `document_session.py`: Define `DocumentSession` managing `document_id`, `revision`, `original_hash`, `working_copy_path`, and `dirty` state.
   - `command_bus.py`: Define transactional `CommandBus` & `HistoryService` with atomic execution, undo/redo stacks, and conflict detection (`expected_revision`).
   - `style_resolver.py`: Define `StyleResolver` implementing the cascading precedence:
     `App Defaults < Agency Profile < Document Theme < Parent Style < Table Role Conditions < Direct Formatting`.
2. **6-Tab Integration Shell (`flutter_ui/lib/features/workspace/tab_navigation_shell.dart`)**:
   - Design the root 6-tab navigation bar:
     `[1. 문서편집 | 2. 표템플릿 | 3. 표그림판 | 4. 다이어그램 | 5. 마인드맵 | 6. 파일변환]`
   - Ensure `IndexedStack` or `PageView` with `AutomaticKeepAliveClientMixin` so tab switches preserve user canvas states without loss.
3. **Verification**:
   - Write comprehensive unit tests for `DocumentSession`, `CommandBus`, and `StyleResolver` in `tests/test_v2_session.py`.
   - Ensure all tests pass.

