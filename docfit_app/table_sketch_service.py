"""표그림판 저장소 및 호출 스레드에서 실행하는 한/글 표 복사."""
from __future__ import annotations

import json
import re
import tempfile
import threading
from pathlib import Path

from docfit_core import table_sketch, table_import
from .table_units_service import TableUnitsService, HWP_CLIPBOARD_FORMAT

COM_LOCK = threading.Lock()


def validate_name(name):
    if (not isinstance(name, str) or not name.strip() or len(name) > 60 or name != name.strip() or
            re.search(r'[<>:"/\\|?*\x00-\x1f]', name) or name.endswith(".") or
            name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1,10)), *(f"LPT{i}" for i in range(1,10))}):
        raise ValueError("이름은 경로 문자 없이 60자 이내로 입력해 주세요.")
    return name


class TableSketchService:
    def __init__(self, settings_root, hwp_factory=None, *, clipboard_formats=None, activator=None):
        self.folder = Path(settings_root) / "table_sketches"
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

    def import_table(self, source_type, data, table_index=0):
        if source_type == "html":
            res = table_import.import_table_from_html(data)
        elif source_type in ("hwpx", "file"):
            res = table_import.import_table_from_hwpx(data, table_index=table_index)
        elif source_type == "xml":
            res = table_import.import_table_from_xml(data)
        else:
            raise ValueError(f"지원하지 않는 가져오기 형식입니다: {source_type}")
        if not res.get('lines'):
            raise ValueError('가져올 표를 찾지 못했습니다. HWPX 파일이나 표를 확인해 주세요.')
        return dict(ok=True, **res)

    def command(self, action, payload=None):
        try:
            if action == "preview": return table_sketch.preview(payload)
            if action == "copy": return self.copy(payload)
            if action == "list": return self.list()
            if action == "save" and isinstance(payload, dict):
                return self.save(payload.get("name"), payload.get("sketch"))
            if action == "load": return self.load(payload)
            if action == "delete": return self.delete(payload)
            if action in ("import", "import_table"):
                src = payload.get("source_type", "html") if isinstance(payload, dict) else "html"
                d = payload.get("data", payload) if isinstance(payload, dict) else payload
                idx = payload.get("table_index", 0) if isinstance(payload, dict) else 0
                return self.import_table(src, d, table_index=idx)
            if action == "import_hwpx":
                p = payload.get("path", payload) if isinstance(payload, dict) else payload
                idx = payload.get("table_index", 0) if isinstance(payload, dict) else 0
                return self.import_table("hwpx", p, table_index=idx)
            raise ValueError("표그림판 작업을 확인해 주세요.")
        except (OSError, ValueError, TypeError) as exc:
            return dict(ok=False, message=str(exc))
