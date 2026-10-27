# Codex Task: Implement Native File Dialog Service & B01~B14 File Picker Modernization

Branch: `dev/2.0.0`
Directory: `C:\HWP_AUTODOCFIT\v1803\v2`

## Background & Objective
Per the user mandate:
"코덱스 현재 사용가능해. 코덱스 작업개시해"
"제미나이 워커들의 작업량이 많으면 코덱스는 검수 대기 상태를 풀고 제미나이 워커들의 작업량의 일부를 받아서 작업해"

Codex takes over the implementation of the file selection modernization and backend API connections according to `docs/V2_REMAINING_DESIGN_SPEC.md` Section 3.

## Required Implementation

1. `docfit_app/native_file_dialog_service.py`:
   - `NativeFileDialogService`:
     - Runs file dialog in dedicated STA thread so WebView2 / GUI loop never hangs.
     - Supports `select_files(request_id, purpose, mode="open"|"save"|"directory", multiple=False)`:
       - Uses Windows native dialog (IFileOpenDialog / IFileSaveDialog via ctypes / win32 or tkinter-free fallback).
       - Returns selection token: `{ok: true, cancelled: false, selection_id: uuid, files: [{name, size}]}` or `{ok: true, cancelled: true}`.
       - Token expires after 5 minutes and is single-use per purpose.
       - Canonical path resolution, verifies file existence, extension whitelist, max 1000 files for folders, rejects ADS/reparse point bypasses.
     - `resolve_selection(selection_id, purpose)`: retrieves actual Windows paths stored securely in host memory, then invalidates token.
     - `register_selection(purpose, paths)`: registers paths from Flutter native file_picker and returns a selection_id token.

2. Update `desktop_web_ui.py`:
   - Replace legacy Tkinter file dialog calls in `add_files`, `add_folder`, and related methods:
     - Remove `self._tk(self.gui.파일선택, timeout=None, front=True)`
     - Remove `self._tk(self.gui._폴더선택, timeout=None, front=True)`
     - Add explicit APIs:
       - `add_paths(paths)`
       - `add_directory(selection_id, recursive=False)`
       - `select_files(payload)`
       - `register_selection(payload)`
     - Ensure `front=True` is completely eliminated from file dialog paths.

3. `tests/test_v2_file_dialog_service.py`:
   - Unit tests covering:
     - Token generation, expiry (5 min), and single-use consumption.
     - Purpose whitelist enforcement.
     - Path canonicalization, non-existent file rejection, directory bounds check.
     - Cancellation handling (cancelled=True does not error).
     - Concurrent requests and request_id deduplication.
   - All tests pass with `python -m pytest tests/test_v2_file_dialog_service.py`.

## Rules & Constraints
- CRLF line endings on Windows.
- Pure Python standard library + existing project dependencies.
- Ensure all existing test suites continue to pass: `python -m pytest tests/test_v2_session.py tests/test_v2_diff_host.py tests/test_v2_canvas_hwpx.py tests/test_v2_canvas_package_adapter.py`.
