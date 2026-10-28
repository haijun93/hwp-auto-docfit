# Codex Task: Implement Canvas Package Adapter & Package Merging Tests

Branch: `dev/2.0.0`
Directory: `C:\HWP_AUTODOCFIT\v1803\v2`

## Background & Objective
Per the user mandate (Rule 2: Codex Idle Prevention & Parallel Coding):
Codex continuously implements core modules without waiting in an idle review state.

Refer to `docs/V2_REMAINING_DESIGN_SPEC.md` lines 152-179:
"HWPX exporter는 기존 패키지의 스타일·borderFill·개체 ID를 전역 할당하고 참조를 재매핑한다. serializer는 schema·참조·ZIP·내용 검증 후 새 출력에 원자 승격하고 원본은 쓰지 않는다."

## Required Files to Implement

1. `docfit_core/hwpx/canvas_package_adapter.py`:
   - `merge_canvas_block_into_hwpx(hwpx_bytes_or_path, block_data, output_path=None)`:
     - Safely parses existing HWPX ZIP structure via `defusedxml` and standard `zipfile`.
     - Inspects `Contents/header.xml` to find existing max IDs for borderFills, charProperties, paraProperties, and styles.
     - Calls `build_table_sketch_xml`, `build_table_sketch_border_fills_xml`, `build_diagram_shape_xml`, or `build_mindmap_xml` with mapped ID references.
     - Appends new borderFills / paraProperties into `header.xml` with updated itemCnt.
     - Inserts the generated elements into `Contents/section0.xml` at target paragraph/anchor location.
     - Atomic promotion: writes to temporary file and validates before replacing target (never modifies original in place).
     - Rejects invalid ZIP / corrupt archives with ValueError/DiffError.

2. `tests/test_v2_canvas_package_adapter.py`:
   - Unit tests creating minimal valid HWPX fixtures in memory.
   - Tests merging table sketch, diagram shape, and mindmap blocks into an existing HWPX.
   - Verifies header ID remapping, section insertion, and archive integrity.
   - All tests pass with `python -m pytest tests/test_v2_canvas_package_adapter.py`.

## Rules & Constraints
- CRLF line endings on Windows.
- Pure standard library + `defusedxml`.
- Ensure all existing tests pass: `python -m pytest tests/test_v2_session.py tests/test_v2_diff_host.py tests/test_v2_canvas_hwpx.py`.

