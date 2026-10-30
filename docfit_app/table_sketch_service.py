"""표그림판 저장소 및 호출 스레드에서 실행하는 한/글 표 복사."""
from __future__ import annotations

import json
import re
import tempfile
import threading
from pathlib import Path

from docfit_core import table_sketch
from docfit_core.hwp_table_import import sketch_from_html
from .table_units_service import TableUnitsService, HWP_CLIPBOARD_FORMAT

COM_LOCK = threading.Lock()


def validate_name(name):
    if (not isinstance(name, str) or not name.strip() or len(name) > 60 or name != name.strip() or
            re.search(r'[<>:"/\\|?*\x00-\x1f]', name) or name.endswith(".") or
            name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1,10)), *(f"LPT{i}" for i in range(1,10))}):
        raise ValueError("이름은 경로 문자 없이 60자 이내로 입력해 주세요.")
    return name


class TableSketchService:
    def __init__(self, settings_root, hwp_factory=None, *, clipboard_formats=None, activator=None, clipboard_html=None,
                 clipboard_seq=None):
        self.folder = Path(settings_root) / "table_sketches"
        self._clipboard_html = clipboard_html or _clipboard_html
        self._clipboard_seq = clipboard_seq or _clipboard_seq
        self.hwp = TableUnitsService(hwp_factory, clipboard_formats=clipboard_formats, activator=activator)

    def _path(self, name):
        path = self.folder / (validate_name(name) + ".json")
        if path.resolve().parent != self.folder.resolve():
            raise ValueError("그림 저장 경로를 확인해 주세요.")
        return path

    def save(self, name, sketch):
        path = self._path(name)
        table_sketch.normalize(sketch)
        self.folder.mkdir(parents=True, exist_ok=True)
        # 원본 선 끝점도 보존: 겹친 선 정규화는 변환 시 수행한다.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".tmp", dir=self.folder, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                json.dump(sketch, stream, ensure_ascii=False, allow_nan=False)
            except Exception:
                stream.close()
                temporary.unlink(missing_ok=True)
                raise
        try:
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return dict(ok=True, name=name)

    def list(self):
        return dict(ok=True, sketches=sorted(p.stem for p in self.folder.glob("*.json") if p.is_file() and not p.is_symlink()))

    def load(self, name):
        path = self._path(name)
        if path.stat().st_size > 8_000_000:
            raise ValueError("그림 파일이 너무 큽니다.")
        sketch = json.loads(path.read_text(encoding="utf-8"))
        table_sketch.normalize(sketch)
        return dict(ok=True, name=name, sketch=sketch)

    def delete(self, name):
        self._path(name).unlink()
        return dict(ok=True, name=name)

    def copy(self, sketch):
        if not COM_LOCK.acquire(blocking=False):
            return dict(ok=False, message="표 복사 작업이 진행 중입니다. 잠시 후 다시 눌러 주세요.")
        try:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                with tempfile.TemporaryDirectory(prefix="docfit_sketch_") as directory:
                    document = table_sketch.to_hwpx(sketch, Path(directory)/"sketch.hwpx")
                    app = self.hwp._hwp()
                    try:
                        if app.Open(str(document), "HWPX", "forceopen:true") is False:
                            raise ValueError("한/글이 표 문서를 열지 못했습니다.")
                        ctrl = app.HeadCtrl
                        while ctrl is not None and ctrl.CtrlID != "tbl": ctrl = ctrl.Next
                        if ctrl is None or app.SetPosBySet(ctrl.GetAnchorPos(0)) is False or app.FindCtrl() is False:
                            raise ValueError("복사할 표를 선택하지 못했습니다.")
                        if app.Run("Copy") is False:
                            raise ValueError("표를 복사하지 못했습니다.")
                    finally:
                        self.hwp._close(app)
                    if HWP_CLIPBOARD_FORMAT not in self.hwp._clipboard_formats():
                        raise ValueError("클립보드에 한/글 표를 넣지 못했습니다.")
                    try: self.hwp._activator()
                    except Exception: pass
                    return dict(ok=True, message="한/글에서 Ctrl+V로 붙여넣으세요.")
            finally:
                pythoncom.CoUninitialize()
        except Exception as exc:
            return dict(ok=False, message=str(exc))
        finally:
            COM_LOCK.release()

    def paste_hwp(self, payload=None):
        """한/글에서 복사한 표(클립보드 HTML)를 표그림판 그림으로. 칸 간격은 지금 그림판 값을 따른다."""
        payload = payload if isinstance(payload, dict) else {}
        # Ctrl+V(2.0.6): 표그림판 안에서 복사한 뒤 클립보드가 그대로면 한/글 표가 아니라 그림판 안 붙여넣기를 한다.
        seq = self._clipboard_seq()
        after = payload.get("after_seq")
        if type(after) is int and seq is not None and seq == after:
            return dict(ok=False, code="UNCHANGED", seq=seq, message="")
        cell_mm = payload.get("cell_mm", 5.0)
        if isinstance(cell_mm, bool) or not isinstance(cell_mm, (int, float)) or not 0.5 <= cell_mm <= 50:
            cell_mm = 5.0
        html = self._clipboard_html()
        if not html:
            raise ValueError("클립보드에 한/글 표가 없습니다. 한/글에서 표를 선택해 복사(Ctrl+C)한 뒤 다시 눌러 주세요.")
        sketch = sketch_from_html(html, float(cell_mm))
        source = sketch.pop("source")
        return dict(ok=True, sketch=sketch, rows=source["rows"], cols=source["cols"], seq=seq,
                    message=f"한/글 표({source['rows']}행 × {source['cols']}열)를 가져왔어요. 선·글을 고친 뒤 다시 복사할 수 있어요.")

    def command(self, action, payload=None):
        try:
            if action == "preview": return table_sketch.preview(payload)
            if action == "copy": return self.copy(payload)
            if action == "list": return self.list()
            if action == "save" and isinstance(payload, dict):
                return self.save(payload.get("name"), payload.get("sketch"))
            if action == "load": return self.load(payload)
            if action == "delete": return self.delete(payload)
            if action == "paste_hwp": return self.paste_hwp(payload)
            if action == "clipboard_seq": return dict(ok=True, seq=self._clipboard_seq())
            raise ValueError("표그림판 작업을 확인해 주세요.")
        except (OSError, ValueError, TypeError) as exc:
            return dict(ok=False, message=str(exc))


def _clipboard_html():
    """Windows 클립보드의 'HTML Format'(한/글이 표를 복사할 때 함께 넣음). 없으면 None."""
    try:
        import win32clipboard
    except ImportError:
        return None
    fmt = win32clipboard.RegisterClipboardFormat("HTML Format")
    for _ in range(5):
        try:
            win32clipboard.OpenClipboard()
            break
        except Exception:
            import time
            time.sleep(0.05)
    else:
        return None
    try:
        if not win32clipboard.IsClipboardFormatAvailable(fmt):
            return None
        data = win32clipboard.GetClipboardData(fmt)
        return data if isinstance(data, (bytes, str)) else None
    finally:
        win32clipboard.CloseClipboard()


def _clipboard_seq():
    """Windows 클립보드 바뀜 번호(복사할 때마다 늘어난다). 알 수 없으면 None."""
    try:
        import win32clipboard
        return int(win32clipboard.GetClipboardSequenceNumber())
    except Exception:
        return None
