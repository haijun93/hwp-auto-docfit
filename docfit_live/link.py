"""실행 중인 한/글 연결·문맥 읽기·커서 위치에 넣기(3.0-α1).

- 연결은 ROT(실행 중 개체 표)에서만 찾는다. GetActiveObject·Dispatch로 대신하지 않는다(새 한/글이 생김, PoC C28).
- 쓰기는 '한 번의 붙여넣기'로만 한다 — 한/글에서 Ctrl+Z 한 번으로 되돌아간다(PoC: 블록 삽입 1회 Undo 확인).
- 사용자 문서를 저장하지 않고, 사용자 한/글을 종료하지 않는다.
COM 호출은 이 모듈을 쓰는 한 스레드(STA)에서만 한다. 시험은 가짜 객체(rot·dispatch 주입)로 한다.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath


class LiveLinkError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class Session:
    moniker: str
    app: object = field(repr=False)
    path: str = ""          # 지금 문서 경로(저장 안 한 새 문서면 빈 값)
    title: str = ""         # 문서 이름(창 제목과 맞춰 볼 때 씀)


def _document(app):
    try:
        doc = app.XHwpDocuments.Active_XHwpDocument
        full = str(doc.FullName or "")
        return full, PureWindowsPath(full).name if full else ""
    except Exception:
        try:
            path = str(app.Path or "")
            return path, PureWindowsPath(path).name if path else ""
        except Exception:
            return "", ""


def _document_id(app) -> str:
    try:
        doc = app.XHwpDocuments.Active_XHwpDocument
        if hasattr(doc, "DocumentID"):
            return str(doc.DocumentID or "")
    except Exception:
        pass
    try:
        if hasattr(app, "DocumentID"):
            return str(app.DocumentID or "")
    except Exception:
        pass
    try:
        doc = getattr(app, "ActiveDocument", None)
        if doc and hasattr(doc, "DocumentID"):
            return str(doc.DocumentID or "")
    except Exception:
        pass
    return ""


def running_sessions(*, rot=None, bind_ctx=None, dispatch=None) -> list[Session]:
    """ROT에 등록된 한/글 연결 목록."""
    if rot is None:
        import pythoncom
        rot, bind_ctx = pythoncom.GetRunningObjectTable(), pythoncom.CreateBindCtx(0)
        import win32com.client
        dispatch = lambda unknown: win32com.client.Dispatch(unknown.QueryInterface(pythoncom.IID_IDispatch))
    sessions = []
    for moniker in rot.EnumRunning():
        try:
            name = moniker.GetDisplayName(bind_ctx, None)
        except Exception:
            continue
        if "HwpObject" not in name:
            continue
        try:
            app = dispatch(rot.GetObject(moniker))
        except Exception:
            continue
        path, title = _document(app)
        sessions.append(Session(name, app, path, title))
    return sessions


def foreground_title() -> str:
    """앞에 있는 창 제목(한/글 창이면 '문서이름 - 한글' 꼴)."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value
    except Exception:
        return ""


def choose(sessions: list[Session], *, prefer_path: str = "", window_title: str = "") -> Session:
    """연결할 한/글: 고른 문서 경로 → 앞 창 제목에 이름이 든 문서 → 하나뿐이면 그것. 애매하면 오류(엉뚱한 문서에 쓰지 않음)."""
    if not sessions:
        raise LiveLinkError("NO_HANGUL", "실행 중인 한/글을 찾지 못했어요. 한/글에서 문서를 연 뒤 다시 눌러 주세요.")
    if prefer_path:
        same = [s for s in sessions if s.path and Path(s.path) == Path(prefer_path)]
        if len(same) == 1:
            return same[0]
    if window_title:
        named = [s for s in sessions if s.title and s.title in window_title]
        if len(named) == 1:
            return named[0]
        if not named and "[" not in window_title:
            # 저장 안 한 새 문서('빈 문서 1 - 한글')는 문서 이름이 비어 있다(10-31 실측). 그런 문서가 하나뿐일 때만 고른다.
            blank = [s for s in sessions if not s.path]
            if len(blank) == 1:
                return blank[0]
    if len(sessions) == 1:
        return sessions[0]
    raise LiveLinkError("AMBIGUOUS", "한/글 창이 여러 개 있어요. 넣을 문서 창을 한 번 누른 뒤 다시 시도해 주세요.")


def context(app) -> dict:
    """커서 문맥: 위치·선택 여부·표 안 여부·쪽 표시·문서·선택 범위."""
    path, title = _document(app)
    doc_id = _document_id(app)
    try:
        pos = tuple(app.GetPos())
    except Exception as exc:
        raise LiveLinkError("DOCUMENT_BUSY", "한/글이 응답하지 않아요. 열린 대화상자를 닫고 다시 시도해 주세요.") from exc
    try:
        selected = bool(app.SelectionMode)
    except Exception:
        selected = False

    selection_range = None
    if selected:
        try:
            if hasattr(app, "GetSelectedPos") and callable(app.GetSelectedPos):
                res = app.GetSelectedPos()
                if isinstance(res, (tuple, list)) and len(res) == 2:
                    selection_range = [list(res[0]), list(res[1])]
                elif hasattr(res, "spara") and hasattr(res, "epara"):
                    s_list = getattr(res, "slist", 0)
                    e_list = getattr(res, "elist", 0)
                    selection_range = [[int(s_list), int(res.spara), int(res.spos)], [int(e_list), int(res.epara), int(res.epos)]]
                elif isinstance(res, dict) and "start" in res and "end" in res:
                    selection_range = [list(res["start"]), list(res["end"])]
            elif hasattr(app, "GetSelectedPosBySet") and callable(app.GetSelectedPosBySet):
                sset = app.CreateSet("ListParaPos")
                eset = app.CreateSet("ListParaPos")
                if app.GetSelectedPosBySet(sset, eset):
                    selection_range = [
                        [int(sset.Item("List")), int(sset.Item("Para")), int(sset.Item("Pos"))],
                        [int(eset.Item("List")), int(eset.Item("Para")), int(eset.Item("Pos"))],
                    ]
            elif hasattr(app, "selection_range") and app.selection_range is not None:
                sr = app.selection_range
                if isinstance(sr, (list, tuple)) and len(sr) == 2:
                    selection_range = [list(sr[0]), list(sr[1])]
        except Exception:
            selection_range = None
        if selection_range is None:
            selection_range = [list(pos), list(pos)]

    try:
        parent = app.ParentCtrl
        in_table = bool(parent is not None and parent.CtrlID == "tbl")
    except Exception:
        in_table = False
    try:
        indicator = app.KeyIndicator()
        page = int(indicator[3]) if isinstance(indicator, (tuple, list)) and len(indicator) > 3 else None
    except Exception:
        page = None
    try:
        window = app.XHwpWindows.Active_XHwpWindow
        visible = bool(window.Visible)
        hwnd = int(getattr(window, "Hwnd", getattr(window, "HWND", 0)) or 0)
    except Exception as exc:
        if hasattr(app, "XHwpWindows"):
            raise LiveLinkError("DOCUMENT_BUSY", "한/글 문서 창을 확인할 수 없어요. 대화상자나 다른 창을 닫고 다시 시도해 주세요.") from exc
        visible, hwnd = True, 0
    return {"path": path, "title": title, "document_id": doc_id, "hwnd": hwnd, "visible": visible, "pos": list(pos), "selected": selected, "in_table": in_table, "page": page, "selection_range": selection_range}


def _window_enabled(hwnd: int) -> bool:
    """한/글 문서 창이 대화상자 등에 의해 비활성화됐는지 확인한다."""
    user32 = ctypes.windll.user32
    user32.IsWindowEnabled.argtypes = [ctypes.c_void_p]
    user32.IsWindowEnabled.restype = ctypes.c_bool
    return bool(user32.IsWindowEnabled(hwnd))


def paste_at_cursor(app, *, expected: dict | None = None, window_enabled=None) -> dict:
    """클립보드 내용을 커서 위치에 한 번 붙여 넣는다(Ctrl+Z 한 번으로 되돌림). expected 문맥이 다르면 멈춘다."""
    now = context(app)
    if not now.get("visible"):
        raise LiveLinkError("DOCUMENT_BUSY", "한/글 문서 창이 활성 상태가 아니에요. 문서 창을 앞에 두고 다시 시도해 주세요.")
    if now["hwnd"]:
        try:
            # 주입값은 실제 HWND 대화상자 검사를 대체하므로 명시적으로만 사용한다.
            checker = window_enabled if window_enabled is not None else _window_enabled
            enabled = checker(now["hwnd"])
        except Exception:
            enabled = True  # hwnd 상태를 확인할 수 없으면 문맥 재확인 결과에 맡긴다.
    else:
        enabled = True
    if not enabled:
        raise LiveLinkError("DOCUMENT_BUSY", "한/글 문서 창이 활성 상태가 아니에요. 대화상자나 다른 창을 닫고 다시 시도해 주세요.")
    if expected and any(expected.get(k) != now.get(k) for k in ("path", "document_id", "pos", "selected", "in_table", "page", "hwnd")):
        raise LiveLinkError("STALE_CONTEXT", "넣으려던 사이에 커서나 문서가 바뀌었어요. 다시 눌러 주세요.")
    if not _run_allowed(app, "Paste"):
        raise LiveLinkError("PASTE_FAILED", "한/글에 붙여 넣지 못했어요.")
    return {"inserted": True, "context": now, "undo_steps": 1}


_ALLOWED_ACTIONS = frozenset({"Paste"})


def _run_allowed(app, action: str) -> bool:
    if action not in _ALLOWED_ACTIONS:
        raise LiveLinkError("ACTION_NOT_ALLOWED", "이 한/글 작업은 허용되지 않습니다.")
    return bool(app.HAction.Run(action))


# ── 3.0-α3 표·선택 범위 GetTextFile 입출력 어댑터 경계 ──
def _validate_replace_context(app, expected: dict, *, require_selection: bool) -> dict:
    """현 문맥을 한 번 얻어 필수 path/document_id/pos/selected/in_table를 기대 문맥과 비교한다.
    불완전 expected는 INVALID_ARGUMENT, 불일치는 STALE_CONTEXT, 대상 밖은 NOT_IN_TABLE 또는 NO_SELECTION.
    """
    if not isinstance(expected, dict) or not expected:
        raise LiveLinkError("INVALID_ARGUMENT", "expected 문맥이 필요합니다.")

    exp_path = expected.get("path")
    if not isinstance(exp_path, str) or not exp_path.strip():
        raise LiveLinkError("INVALID_ARGUMENT", "expected.path가 필요합니다.")

    exp_doc_id = expected.get("document_id") or expected.get("DocumentID") or expected.get("doc_id")
    if not isinstance(exp_doc_id, str) or not exp_doc_id.strip():
        raise LiveLinkError("INVALID_ARGUMENT", "expected.document_id가 필요합니다.")

    for k in ("pos", "selected", "in_table"):
        if k not in expected:
            raise LiveLinkError("INVALID_ARGUMENT", f"expected.{k}가 필요합니다.")

    exp_pos = expected["pos"]
    if not (isinstance(exp_pos, (list, tuple)) and len(exp_pos) == 3 and all(isinstance(x, int) and not isinstance(x, bool) for x in exp_pos)):
        raise LiveLinkError("INVALID_ARGUMENT", "expected.pos가 올바르지 않습니다.")

    if not isinstance(expected["selected"], bool) or not isinstance(expected["in_table"], bool):
        raise LiveLinkError("INVALID_ARGUMENT", "expected 불리언 필드가 올바르지 않습니다.")

    now = context(app)
    now_doc_id = now.get("document_id") or now.get("DocumentID") or now.get("doc_id")
    if not now_doc_id or not isinstance(now_doc_id, str) or not now_doc_id.strip():
        # DocumentID를 가져올 수 없으면 빈 문자열을 허용해 비교를 통과시키지 않는다.
        raise LiveLinkError("STALE_CONTEXT", "문서 식별자를 확인할 수 없습니다.")

    if (
        exp_path != now.get("path")
        or exp_doc_id != now_doc_id
        or tuple(exp_pos) != tuple(now.get("pos") or ())
        or expected["selected"] != now.get("selected")
        or expected["in_table"] != now.get("in_table")
    ):
        raise LiveLinkError("STALE_CONTEXT", "넣으려던 사이에 커서나 문서가 바뀌었어요. 다시 눌러 주세요.")

    if require_selection:
        if not now.get("selected"):
            raise LiveLinkError("NO_SELECTION", "선택된 범위가 없어요.")
        if "selection_range" not in expected:
            raise LiveLinkError("INVALID_ARGUMENT", "expected.selection_range가 필요합니다.")
        exp_range = expected["selection_range"]
        if not (isinstance(exp_range, (list, tuple)) and len(exp_range) == 2 and
                all(isinstance(p, (list, tuple)) and len(p) == 3 and
                    all(isinstance(x, int) and not isinstance(x, bool) for x in p) for p in exp_range)):
            raise LiveLinkError("INVALID_ARGUMENT", "expected.selection_range가 올바르지 않습니다.")

        now_range = now.get("selection_range")
        if not (isinstance(now_range, (list, tuple)) and len(now_range) == 2):
            raise LiveLinkError("STALE_CONTEXT", "선택 범위를 확인할 수 없습니다.")
        if tuple(tuple(p) for p in exp_range) != tuple(tuple(p) for p in now_range):
            raise LiveLinkError("STALE_CONTEXT", "넣으려던 사이에 선택 범위가 바뀌었어요. 다시 눌러 주세요.")
    else:
        if not now.get("in_table"):
            raise LiveLinkError("NOT_IN_TABLE", "커서가 표 안에 있지 않아요.")

    return now


def export_table_block(app) -> bytes:
    """커서의 상위 tbl 컨트롤을 확인하고, 실측된 GetTextFile 인자로 표 블록을 얻는다."""
    now = context(app)
    if not now["in_table"]:
        raise LiveLinkError("NOT_IN_TABLE", "커서가 표 안에 있지 않아요.")
    raise NotImplementedError(
        '실측 결과: GetTextFile("HWPML", "") 및 GetTextFile("HWPML", "saveblock")는 None, '
        'GetTextFile("TEXT", "")는 문서 전체 텍스트를 반환해 표 블록 추출에 사용할 수 없습니다.'
    )


def replace_table_block(app, block: bytes, *, expected: dict) -> dict:
    """expected 문맥/대상 표를 재확인하고 실측된 한 번의 교체 명령으로 블록을 넣는다."""
    if not isinstance(block, bytes):
        raise TypeError("block은 bytes여야 합니다.")
    _validate_replace_context(app, expected, require_selection=False)
    raise NotImplementedError("실측 필요: GetTextFile이 표 블록을 반환하지 않아 SetTextFile 표 교체 계약을 확정할 수 없습니다.")


def export_selection_block(app) -> bytes:
    """현재 선택 범위를 실측된 GetTextFile 인자로 반환한다."""
    now = context(app)
    if not now["selected"]:
        raise LiveLinkError("NO_SELECTION", "선택된 범위가 없어요.")
    raise NotImplementedError(
        '실측 결과: 선택 중 GetTextFile("HWPML", "") 및 GetTextFile("HWPML", "saveblock")는 None, '
        'GetTextFile("TEXT", "")는 선택 범위가 아닌 문서 전체 텍스트를 반환합니다.'
    )


def replace_selection_block(app, block: bytes, *, expected: dict) -> dict:
    """선택 범위 문맥을 재확인하고 한 번의 교체로 반환한다."""
    if not isinstance(block, bytes):
        raise TypeError("block은 bytes여야 합니다.")
    _validate_replace_context(app, expected, require_selection=True)
    raise NotImplementedError("실측 필요: GetTextFile이 선택 블록을 반환하지 않아 SetTextFile 선택 교체 계약을 확정할 수 없습니다.")

