"""실행 중인 한/글 연결·문맥 읽기·커서 위치에 넣기(3.0-α1).

- 연결은 ROT(실행 중 개체 표)에서만 찾는다. GetActiveObject·Dispatch로 대신하지 않는다(새 한/글이 생김, PoC C28).
- 쓰기는 '한 번의 붙여넣기'로만 한다 — 한/글에서 Ctrl+Z 한 번으로 되돌아간다(PoC: 블록 삽입 1회 Undo 확인).
- 사용자 문서를 저장하지 않고, 사용자 한/글을 종료하지 않는다.
COM 호출은 이 모듈을 쓰는 한 스레드(STA)에서만 한다. 시험은 가짜 객체(rot·dispatch 주입)로 한다.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass, field
from pathlib import Path


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
        return str(doc.FullName or ""), str(Path(str(doc.FullName or "")).name)
    except Exception:
        try:
            path = str(app.Path or "")
            return path, Path(path).name
        except Exception:
            return "", ""


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
    """커서 문맥: 위치·선택 여부·표 안 여부·쪽 표시·문서."""
    path, title = _document(app)
    try:
        pos = tuple(app.GetPos())
    except Exception as exc:
        raise LiveLinkError("DOCUMENT_BUSY", "한/글이 응답하지 않아요. 열린 대화상자를 닫고 다시 시도해 주세요.") from exc
    try:
        selected = bool(app.SelectionMode)
    except Exception:
        selected = False
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
    return {"path": path, "title": title, "pos": list(pos), "selected": selected, "in_table": in_table, "page": page}


def paste_at_cursor(app, *, expected: dict | None = None) -> dict:
    """클립보드 내용을 커서 위치에 한 번 붙여 넣는다(Ctrl+Z 한 번으로 되돌림). expected 문맥이 다르면 멈춘다."""
    now = context(app)
    if expected and (expected.get("path") != now["path"] or expected.get("pos") != now["pos"]):
        raise LiveLinkError("STALE_CONTEXT", "넣으려던 사이에 커서나 문서가 바뀌었어요. 다시 눌러 주세요.")
    if not app.HAction.Run("Paste"):
        raise LiveLinkError("PASTE_FAILED", "한/글에 붙여 넣지 못했어요.")
    return {"inserted": True, "context": now, "undo_steps": 1}
