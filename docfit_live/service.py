"""LiveLink 서비스(3.0-α1): 사용자 한/글 연결은 전용 STA 스레드 하나에서만 다룬다.

- 명령은 FIFO로 하나씩 실행한다(쓰기 겹침 없음).
- 앱이 띄운 숨은 한/글(표 복사용)은 창이 보이지 않으므로 고르지 않는다.
- 사용자 클립보드는 넣기 전에 보관하고 넣은 뒤 되돌린다(글·그림 형식).
"""
from __future__ import annotations

import ctypes
import json
import logging
import os
from pathlib import Path
import queue
import threading
from concurrent.futures import Future

from . import link


_REPO_ROOT = Path(__file__).resolve().parent.parent


def is_undo_gate_passed(evidence_path: str | os.PathLike | None = None) -> bool:
    """외부 프로세스/COM을 호출하지 않는 순수 파일 판독 게이트.
    기본 증거 위치: 저장소 루트 기준 reports/live-replace-gate.json.
    저장소 내부 경로만 통과하며 외부 경로 및 탈출 경로는 엄격히 차단한다.
    """
    try:
        raw_path = Path(evidence_path) if evidence_path is not None else (_REPO_ROOT / "reports" / "live-replace-gate.json")
        if not raw_path.is_absolute():
            raw_path = _REPO_ROOT / raw_path
        resolved_gate = raw_path.resolve()
        try:
            resolved_gate.relative_to(_REPO_ROOT)
        except ValueError:
            # 저장소 외부의 증거 파일 주입 차단
            return False
        if not resolved_gate.is_file():
            return False

        with open(resolved_gate, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return False
        if data.get("schema_version") != 1:
            return False
        if data.get("gate") != "live_replace":
            return False
        if data.get("status") != "PASS":
            return False
        if data.get("undo_steps") != 1:
            return False
        evidence_files = data.get("evidence_files")
        if not isinstance(evidence_files, (list, tuple)) or not evidence_files:
            return False
        for ef in evidence_files:
            if not isinstance(ef, str) or not ef.strip():
                return False
            ef_path = Path(ef)
            if not ef_path.is_absolute():
                resolved_ef = (_REPO_ROOT / ef_path).resolve()
            else:
                resolved_ef = ef_path.resolve()
            try:
                resolved_ef.relative_to(_REPO_ROOT)
            except ValueError:
                # 저장소 외부 이탈(심볼릭/상대경로 탈출 등) 차단
                return False
            if not resolved_ef.is_file():
                return False
        return True
    except Exception as exc:
        logging.getLogger(__name__).warning("Undo 게이트 증거 파일 판독 실패: %s", exc)
        return False


def _validate_expected_context(expected: object, *, require_selection: bool) -> tuple[dict | None, dict | None]:
    """expected 계약 검증 및 정규화.
    반환: (정규화된 expected dict, 오류 DTO dict) 중 하나는 None.
    """
    if not isinstance(expected, dict) or not expected:
        return None, {
            "ok": False,
            "code": "INVALID_ARGUMENT",
            "message": "expected 문맥이 필요합니다.",
        }

    path = expected.get("path")
    if not isinstance(path, str) or not path.strip():
        return None, {
            "ok": False,
            "code": "INVALID_ARGUMENT",
            "message": "expected.path가 필요합니다.",
        }

    doc_id = expected.get("document_id") or expected.get("DocumentID") or expected.get("doc_id")
    if not isinstance(doc_id, str) or not doc_id.strip():
        return None, {
            "ok": False,
            "code": "INVALID_ARGUMENT",
            "message": "expected.document_id가 필요합니다.",
        }

    for k in ("pos", "selected", "in_table"):
        if k not in expected:
            return None, {
                "ok": False,
                "code": "INVALID_ARGUMENT",
                "message": f"expected.{k}가 필요합니다.",
            }

    pos = expected["pos"]
    if not (isinstance(pos, (list, tuple)) and len(pos) == 3 and all(isinstance(x, int) and not isinstance(x, bool) for x in pos)):
        return None, {
            "ok": False,
            "code": "INVALID_ARGUMENT",
            "message": "expected.pos는 길이 3의 정수 배열/튜플이어야 합니다.",
        }

    selected = expected["selected"]
    if not isinstance(selected, bool):
        return None, {
            "ok": False,
            "code": "INVALID_ARGUMENT",
            "message": "expected.selected는 bool이어야 합니다.",
        }

    in_table = expected["in_table"]
    if not isinstance(in_table, bool):
        return None, {
            "ok": False,
            "code": "INVALID_ARGUMENT",
            "message": "expected.in_table은 bool이어야 합니다.",
        }

    normalized = {
        "path": path,
        "document_id": doc_id,
        "pos": list(pos),
        "selected": selected,
        "in_table": in_table,
    }

    if require_selection:
        if not selected:
            return None, {
                "ok": False,
                "code": "INVALID_ARGUMENT",
                "message": "선택 범위 자간 변환은 selected=True여야 합니다.",
            }
        if "selection_range" not in expected:
            return None, {
                "ok": False,
                "code": "INVALID_ARGUMENT",
                "message": "expected.selection_range가 필요합니다.",
            }
        sr = expected["selection_range"]
        if not (isinstance(sr, (list, tuple)) and len(sr) == 2 and
                all(isinstance(p, (list, tuple)) and len(p) == 3 and
                    all(isinstance(x, int) and not isinstance(x, bool) for x in p) for p in sr)):
            return None, {
                "ok": False,
                "code": "INVALID_ARGUMENT",
                "message": "expected.selection_range는 길이 2의 [list, para, pos] 정수 배열이어야 합니다.",
            }
        normalized["selection_range"] = [list(sr[0]), list(sr[1])]
    else:
        if not in_table or selected:
            return None, {
                "ok": False,
                "code": "INVALID_ARGUMENT",
                "message": "표 정보단위 변환은 in_table=True, selected=False여야 합니다.",
            }

    return normalized, None


def _context_matches(expected: dict, actual: dict) -> bool:
    """path, document_id, pos, selected, in_table, selection_range 일치 여부 검증."""
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return False

    exp_doc_id = expected.get("document_id") or expected.get("DocumentID") or expected.get("doc_id")
    act_doc_id = actual.get("document_id") or actual.get("DocumentID") or actual.get("doc_id")
    if not exp_doc_id or not act_doc_id or exp_doc_id != act_doc_id:
        return False

    if expected.get("path") != actual.get("path"):
        return False

    exp_pos = tuple(expected.get("pos") or ())
    act_pos = tuple(actual.get("pos") or ())
    if exp_pos != act_pos:
        return False

    if expected.get("selected") != actual.get("selected"):
        return False

    if expected.get("in_table") != actual.get("in_table"):
        return False

    if expected.get("selected"):
        exp_range = expected.get("selection_range")
        act_range = actual.get("selection_range")
        if not exp_range or not act_range:
            return False
        try:
            exp_t = tuple(tuple(int(x) for x in p) for p in exp_range)
            act_t = tuple(tuple(int(x) for x in p) for p in act_range)
            if exp_t != act_t:
                return False
        except Exception:
            return False

    return True


def _visible(app) -> bool:
    try:
        return bool(app.XHwpWindows.Active_XHwpWindow.Visible)
    except Exception:
        return True  # 알 수 없으면 후보에 둔다(choose가 애매하면 멈춘다).


def hangul_window_titles() -> list[str]:
    """보이는 한/글 창 제목을 앞에 있는 순서(Z 순서)로."""
    titles: list[str] = []
    try:
        user32 = ctypes.windll.user32
        proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def visit(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buffer, length + 1)
                    if " - 한글" in buffer.value:
                        titles.append(buffer.value)
            return True
        user32.EnumWindows(proc(visit), 0)
    except Exception:
        pass
    return titles


class LiveLinkService:
    def __init__(self, *, sessions=None, titles=None, com_init=True, gate_checker=None, window_enabled=None):
        self._sessions = sessions or link.running_sessions
        self._titles = titles or hangul_window_titles
        self._com_init = com_init
        self._gate_checker = gate_checker or is_undo_gate_passed
        self._window_enabled = window_enabled
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def _is_undo_gate_passed(self) -> bool:
        return bool(self._gate_checker())

    def _transform_table_block(self, block: bytes, delta: int) -> bytes:
        raise NotImplementedError("실측 필요: GetTextFile HWPML 표 블록 직렬화기 미구현")

    def _transform_selection_block(self, block: bytes) -> bytes:
        raise NotImplementedError("실측 필요: GetTextFile 선택 블록 내부 형식 및 자간 엔진 연결 규격 미실측")

    # ── 전용 스레드 ──
    def _run(self):
        if self._com_init:
            import pythoncom
            pythoncom.CoInitialize()
        try:
            while True:
                item = self._queue.get()
                if item is None:
                    return
                future, fn = item
                if future.set_running_or_notify_cancel():
                    try:
                        future.set_result(fn())
                    except BaseException as exc:
                        future.set_exception(exc)
        finally:
            if self._com_init:
                import pythoncom
                pythoncom.CoUninitialize()

    def call(self, fn, timeout=30.0):
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run, name="docfit-livelink", daemon=True)
                self._thread.start()
        future: Future = Future()
        self._queue.put((future, fn))
        return future.result(timeout)

    def close(self):
        if self._thread and self._thread.is_alive():
            self._queue.put(None)

    # ── 명령 ──
    def _pick(self, prefer_path=""):
        sessions = [s for s in self._sessions() if _visible(s.app)]
        titles = self._titles()
        return link.choose(sessions, prefer_path=prefer_path, window_title=titles[0] if titles else "")

    def status(self, prefer_path="") -> dict:
        def work():
            try:
                session = self._pick(prefer_path)
            except link.LiveLinkError as exc:
                return {"connected": False, "code": exc.code, "message": str(exc)}
            ctx = link.context(session.app)
            return {"connected": True, "title": session.title or "새 문서", "path": session.path, "context": ctx}
        return self.call(work)

    def paste(self, expected: dict | None = None, prefer_path="") -> dict:
        def work():
            session = self._pick(prefer_path or (expected or {}).get("path", ""))
            if expected:
                current = link.context(session.app)
                if current.get("path") != expected.get("path") or current.get("document_id") != expected.get("document_id"):
                    raise link.LiveLinkError("STALE_CONTEXT", "넣으려던 사이에 문서가 바뀌었어요. 다시 눌러 주세요.")
            return link.paste_at_cursor(
                session.app, expected=expected, window_enabled=self._window_enabled
            )
        return self.call(work)

    def resize_cursor_table(
        self, delta: int, *, expected: dict, prefer_path: str = "", enabled: bool = False
    ) -> dict:
        required_measurements = [
            "GetTextFile HWPML 표 블록 추출 인자 및 반환 인코딩",
            "HWPML 셀/행/열 반복 단위 경계 식별 및 복제 규칙",
            "SetTextFile 등 단일 표 교체 액션 및 인자",
            "교체 후 Ctrl+Z 1회 복구 동작",
        ]
        if not enabled:
            return {
                "ok": False,
                "code": "FEATURE_DISABLED",
                "message": "3.0-α3 기능이 비활성화되어 있습니다.",
                "required_measurements": required_measurements,
            }
        norm_expected, err = _validate_expected_context(expected, require_selection=False)
        if err is not None:
            return {**err, "required_measurements": required_measurements}

        if delta not in (-1, 1):
            return {
                "ok": False,
                "code": "INVALID_ARGUMENT",
                "message": f"delta는 -1 또는 +1이어야 합니다 (입력값: {delta}).",
                "required_measurements": required_measurements,
            }

        if not self._is_undo_gate_passed():
            return {
                "ok": False,
                "code": "UNDO_GATE_CLOSED",
                "message": "단일 Undo 실측 증거가 없어 교체할 수 없습니다.",
                "required_measurements": required_measurements,
            }

        def work():
            try:
                session = self._pick(prefer_path or norm_expected.get("path", ""))
            except link.LiveLinkError as exc:
                return {
                    "ok": False,
                    "code": exc.code,
                    "message": str(exc),
                    "required_measurements": required_measurements,
                }

            # 1. 작업 시작 시 문맥 확인 (경로·DocumentID·위치·선택·표안)
            now = link.context(session.app)
            if not _context_matches(norm_expected, now):
                return {
                    "ok": False,
                    "code": "STALE_CONTEXT",
                    "message": "넣으려던 사이에 커서나 문서가 바뀌었어요. 다시 눌러 주세요.",
                    "required_measurements": required_measurements,
                }

            if not now.get("in_table"):
                return {
                    "ok": False,
                    "code": "NOT_IN_TABLE",
                    "message": "커서가 표 안에 있지 않아요.",
                    "required_measurements": required_measurements,
                }

            # 2. 표 블록 추출 (실측 미비 시 NotImplementedError)
            try:
                block = link.export_table_block(session.app)
            except link.LiveLinkError as exc:
                return {
                    "ok": False,
                    "code": exc.code,
                    "message": str(exc),
                    "required_measurements": required_measurements,
                }
            except NotImplementedError as exc:
                return {
                    "ok": False,
                    "code": "UNSUPPORTED_FORMAT",
                    "message": str(exc) or "표 정보단위 추출 형식이 실측되지 않았습니다.",
                    "required_measurements": required_measurements,
                }

            # 3. 파싱, 순수 변환 및 직렬화
            try:
                new_block = self._transform_table_block(block, delta)
            except ValueError as exc:
                return {
                    "ok": False,
                    "code": "INVALID_STRUCTURE",
                    "message": str(exc),
                    "required_measurements": required_measurements,
                }
            except NotImplementedError as exc:
                return {
                    "ok": False,
                    "code": "UNSUPPORTED_FORMAT",
                    "message": str(exc) or "표 정보단위 변환/직렬화 엔진이 실측되지 않았습니다.",
                    "required_measurements": required_measurements,
                }

            # 4. 교체 직전 문맥 재확인 (경로·DocumentID·위치·선택·표안) 및 교체
            pre_replace = link.context(session.app)
            if not _context_matches(norm_expected, pre_replace):
                return {
                    "ok": False,
                    "code": "STALE_CONTEXT",
                    "message": "교체 직전에 커서나 문서가 바뀌었어요.",
                    "required_measurements": required_measurements,
                }

            try:
                return link.replace_table_block(session.app, new_block, expected=norm_expected)
            except link.LiveLinkError as exc:
                return {
                    "ok": False,
                    "code": exc.code,
                    "message": str(exc),
                    "required_measurements": required_measurements,
                }
            except NotImplementedError as exc:
                return {
                    "ok": False,
                    "code": "UNSUPPORTED_FORMAT",
                    "message": str(exc) or "표 교체 액션이 실측되지 않았습니다.",
                    "required_measurements": required_measurements,
                }

        return self.call(work)

    def normalize_selection_spacing(
        self, *, expected: dict, prefer_path: str = "", enabled: bool = False
    ) -> dict:
        required_measurements = [
            "GetTextFile 선택 범위 추출 인자 및 인코딩",
            "선택 범위 자간 엔진 API 및 입력 파라미터 연결 규격",
            "SetTextFile 등 선택 범위 교체 액션 및 단일 Undo 검증",
        ]
        if not enabled:
            return {
                "ok": False,
                "code": "FEATURE_DISABLED",
                "message": "3.0-α3 기능이 비활성화되어 있습니다.",
                "required_measurements": required_measurements,
            }
        norm_expected, err = _validate_expected_context(expected, require_selection=True)
        if err is not None:
            return {**err, "required_measurements": required_measurements}

        if not self._is_undo_gate_passed():
            return {
                "ok": False,
                "code": "UNDO_GATE_CLOSED",
                "message": "단일 Undo 실측 증거가 없어 교체할 수 없습니다.",
                "required_measurements": required_measurements,
            }

        def work():
            try:
                session = self._pick(prefer_path or norm_expected.get("path", ""))
            except link.LiveLinkError as exc:
                return {
                    "ok": False,
                    "code": exc.code,
                    "message": str(exc),
                    "required_measurements": required_measurements,
                }

            # 1. 작업 시작 시 문맥 확인 (경로·DocumentID·위치·선택·표안)
            now = link.context(session.app)
            if not _context_matches(norm_expected, now):
                return {
                    "ok": False,
                    "code": "STALE_CONTEXT",
                    "message": "넣으려던 사이에 커서나 문서가 바뀌었어요. 다시 눌러 주세요.",
                    "required_measurements": required_measurements,
                }

            if not now.get("selected"):
                return {
                    "ok": False,
                    "code": "NO_SELECTION",
                    "message": "선택된 범위가 없어요.",
                    "required_measurements": required_measurements,
                }

            # 2. 선택 블록 추출 (실측 미비 시 NotImplementedError)
            try:
                block = link.export_selection_block(session.app)
            except link.LiveLinkError as exc:
                return {
                    "ok": False,
                    "code": exc.code,
                    "message": str(exc),
                    "required_measurements": required_measurements,
                }
            except NotImplementedError as exc:
                return {
                    "ok": False,
                    "code": "UNSUPPORTED_FORMAT",
                    "message": str(exc) or "선택 범위 블록 추출 인자가 실측되지 않았습니다.",
                    "required_measurements": required_measurements,
                }

            # 3. 선택 블록 자간 변환
            try:
                new_block = self._transform_selection_block(block)
            except ValueError as exc:
                return {
                    "ok": False,
                    "code": "INVALID_STRUCTURE",
                    "message": str(exc),
                    "required_measurements": required_measurements,
                }
            except NotImplementedError as exc:
                return {
                    "ok": False,
                    "code": "UNSUPPORTED_FORMAT",
                    "message": str(exc) or "선택 범위 자간 엔진 연결 규격이 실측되지 않았습니다.",
                    "required_measurements": required_measurements,
                }

            # 4. 교체 직전 문맥 재확인 (경로·DocumentID·위치·선택·표안)
            pre_replace = link.context(session.app)
            if not _context_matches(norm_expected, pre_replace):
                return {
                    "ok": False,
                    "code": "STALE_CONTEXT",
                    "message": "교체 직전에 커서나 문서가 바뀌었어요.",
                    "required_measurements": required_measurements,
                }

            # 5. 교체
            try:
                return link.replace_selection_block(session.app, new_block, expected=norm_expected)
            except link.LiveLinkError as exc:
                return {
                    "ok": False,
                    "code": exc.code,
                    "message": str(exc),
                    "required_measurements": required_measurements,
                }
            except NotImplementedError as exc:
                return {
                    "ok": False,
                    "code": "UNSUPPORTED_FORMAT",
                    "message": str(exc) or "선택 범위 교체 액션이 실측되지 않았습니다.",
                    "required_measurements": required_measurements,
                }

        return self.call(work)



# ── 클립보드 보관·복원 ──
def save_clipboard() -> dict:
    """사용자 클립보드의 글·그림을 보관하고 원래 비었는지 기록한다."""
    saved: dict = {"_empty": False, "_restorable": False}
    try:
        import win32clipboard as cb
        cb.OpenClipboard()
        try:
            for fmt in (cb.CF_UNICODETEXT, cb.CF_DIB):
                if cb.IsClipboardFormatAvailable(fmt):
                    saved[fmt] = cb.GetClipboardData(fmt)
                    saved["_restorable"] = True
            if not saved["_restorable"]:
                saved["_empty"] = cb.CountClipboardFormats() == 0
        finally:
            cb.CloseClipboard()
    except Exception as exc:
        raise link.LiveLinkError("CLIPBOARD_SAVE_FAILED", "클립보드를 보관하지 못해 넣기를 취소했어요.") from exc
    return saved


def restore_clipboard(saved: dict) -> bool:
    try:
        import win32clipboard as cb
        if not saved.get("_restorable") and not saved.get("_empty"):
            return False
        cb.OpenClipboard()
        try:
            cb.EmptyClipboard()
            for fmt, data in saved.items():
                if isinstance(fmt, str):
                    continue
                cb.SetClipboardData(fmt, data)
        finally:
            cb.CloseClipboard()
        return True
    except Exception:
        return False
