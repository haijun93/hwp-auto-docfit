# Codex Task: Implement Canvas HWPX Exporter Builder & Unit Tests

Branch: `dev/2.0.0`
Directory: `C:\HWP_AUTODOCFIT\v1803\v2`

## Background & Objective
Per the user mandate:
"제미나이 워커들의 작업량이 많으면 코덱스는 검수 대기 상태를 풀고 제미나이 워커들의 작업량의 일부를 받아서 작업해"
Codex continues actively implementing core 2.0.0 modules.

Refer to `docs/V2_REMAINING_DESIGN_SPEC.md` Section 2 ("2. 캔버스 Command 스키마", "2.1 트랜잭션·이력").

## Required Files to Implement

1. `docfit_core/hwpx/canvas_hwpx_builder.py`:
   - Pure XML element builders for Canvas commands (no direct file writes, purely returns XML structures or fragments).
   - Functions:
     - `build_table_sketch_xml(payload, refs=None)`:
       - Uses layout calculation from `docfit_core/table_sketch.py`
       - Builds `hp:tbl`, `hp:tr`, `hp:tc` elements with proper row/col/span/borders/texts
       - Pure function: does NOT write to disk.
     - `build_diagram_shape_xml(payload, refs=None)`:
       - Supports node types `rect`, `ellipse` -> `hp:rect`, `hp:ellipse`.
       - Coordinate conversion: 96 dpi CSS px to HWPUNIT: `round(px * 7200 / 96)`.
       - Connectors: `hp:connectLine` straight arrows connecting center of source to center of target.
       - Validates max 1000 nodes, 2000 edges, unique IDs, positive sizes. Rejects unsupported node types with ValueError/SchemaError.
     - `build_mindmap_xml(payload, refs=None)`:
       - Supports modes: `outline` and `summary_table`.
       - `outline`: preorder traversal paragraphs (`hp:p`) with fixed outline numbers (`1`, `1.1`), tab, and level indentation.
       - `summary_table`: 1x1 table (`hp:tbl`) containing all paragraphs.
       - Max 1000 nodes, max depth 32. Rejects duplicate IDs and cycles.
     - Security & Sanitization:
       - Labels up to 10,000 characters.
       - Rejects/escapes XML forbidden control characters (ASCII 0-31 except \t, \n, \r).
       - NaN / Infinity rejected.

2. `tests/test_v2_canvas_hwpx.py`:
   - Unit tests verifying:
     - Table sketch XML output structure (`hp:tbl`/`tr`/`tc`).
     - Diagram shape XML output and exact HWPUNIT coordinate conversion math.
     - Mindmap tree outline and summary_table modes.
     - Cycle detection and depth limit enforcement in mindmaps.
     - XML control character handling.
   - Run tests using `python -m pytest tests/test_v2_canvas_hwpx.py`.

## Rules & Constraints
- CRLF line endings on Windows.
- Pure Python standard library + existing project dependencies (`defusedxml` or `xml.etree.ElementTree`).
- Do not break existing tests (ensure `pytest tests/test_v2_canvas_commands.py tests/test_v2_diff_host.py` still pass).
