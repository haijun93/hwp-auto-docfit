# Codex Task: Implement T17 Diff Host & Diff Host Service

Branch: `dev/2.0.0`
Directory: `C:\HWP_AUTODOCFIT\v1803\v2`

## Background & Objective
Per the user mandate:
"제미나이 워커들의 작업량이 많으면 코덱스는 검수 대기 상태를 풀고 제미나이 워커들의 작업량의 일부를 받아서 작업해"
Codex is no longer waiting in an idle review state. Codex takes over the implementation of the T17 comparison viewer backend.

Refer to `docs/V2_REMAINING_DESIGN_SPEC.md` Section 1 ("1. T17 프로세스 경계", "1.1 파일 보호와 세션 식별", "1.2 IPC wire v1", "1.3 수명 주기와 Process Guard").

## Required Files to Implement

1. `docfit_engine/diff_host.py`:
   - Standalone CLI/module entrypoint: runnable as `python -m docfit_engine.diff_host`.
   - STA COM initialization: `pythoncom.CoInitialize()` in dedicated thread/main loop.
   - IPC Wire v1 over stdin/stdout (newline-delimited UTF-8 JSON, max 64 KiB/line, depth <= 16, whitelist validation for method/type, reject NaN/Infinity/duplicate keys).
   - Bootstrap protocol: receive `{v:1, id, viewer_id, method: "bootstrap", params: {nonce, viewer_id, parent_pid, left: {path, sha256}, right: {path, sha256}, protocol: 1}}`. Validate 256-bit nonce and parent_pid.
   - Methods: `bootstrap`, `navigate`, `scroll`, `set_sync`, `focus`, `heartbeat`, `close`.
   - Process self-termination if:
     - parent process exits / pipe reaches EOF
     - heartbeat is missing for 10 seconds
     - close command received
   - HwpCtrl instantiation / dual-pane Win32 UI (or headless mock / testable fallback when HwpCtrl ActiveX is not registered, e.g. in CI or test mode).
   - Ensure stdout is reserved exclusively for protocol messages; stderr for limited logs.

2. `docfit_app/diff_host_service.py`:
   - `DiffHostService` managing child `docfit_engine.diff_host` processes.
   - Life cycle: `preparing -> starting -> opening -> ready -> closing -> closed`.
   - Win32 Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` (or fallback if Windows Job Objects permissions unavailable in test).
   - File isolation: copies left and right documents to `%LOCALAPPDATA%/HwpAutoDocFit/diff/<viewer_id>/left.hwp[x]` and `right.hwp[x]`, verifying SHA-256 before/after. Sets read-only mode.
   - Generates 256-bit random nonce for bootstrap.
   - Heartbeat loop sending heartbeat every 2 seconds.
   - Response caching: caches last 256 completed responses per id.
   - API endpoints to hook into backend/bridge:
     - `open_diff(document_id, result_id, expected_revision, request_id)`
     - `diff_status(viewer_id, after_seq)`
     - `diff_navigate(viewer_id, side, page, sync)`
     - `diff_close(viewer_id, reason)`

3. `tests/test_v2_diff_host.py`:
   - Unit tests covering:
     - IPC wire v1 protocol framing, max line limit (64 KiB), depth limit, NaN rejection, duplicate key rejection.
     - Nonce validation failure handling.
     - Heartbeat timeout handling.
     - Process guard / clean teardown.
     - File isolation & hash comparison.
   - All tests must pass cleanly with `pytest tests/test_v2_diff_host.py`.

## Rules & Constraints
- CRLF line endings on Windows.
- Pure standard library + existing project dependencies (`pythoncom`, `win32gui`, etc. where available, with graceful test fallbacks).
- Do not break existing tests (ensure `pytest tests/test_v2_canvas_commands.py` and other tests still pass).

