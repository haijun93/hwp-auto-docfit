"""표그림판 저장소 및 호출 스레드에서 실행하는 한/글 표 복사."""
from __future__ import annotations

import json
import base64
import binascii
import re
import tempfile
import threading
from pathlib import Path

from docfit_core import table_sketch
from docfit_core.hwp_table_import import sketch_from_html
from docfit_core.table_import import import_hwpx_table, list_hwpx_tables
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

    def save_draft(self, sketch):
        """작업 중 그림을 별도 복구 파일에 원자적으로 저장한다."""
        table_sketch.normalize(sketch)
        folder = self.folder / "recovery"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "draft.json"
        encoded = json.dumps(sketch, ensure_ascii=False, allow_nan=False)
        if len(encoded.encode("utf-8")) > 8_000_000:
            raise ValueError("자동 복구 데이터가 너무 큽니다.")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".tmp", dir=folder, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(encoded)
                stream.flush()
                import os
                os.fsync(stream.fileno())
            temporary.replace(path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return dict(ok=True)

    def load_draft(self):
        path = self.folder / "recovery" / "draft.json"
        if not path.is_file():
            return dict(ok=True, exists=False)
        if path.stat().st_size > 8_000_000:
            return dict(ok=False, exists=False, message="자동 복구 데이터가 너무 큽니다.")
        try:
            sketch = json.loads(path.read_text(encoding="utf-8"))
            table_sketch.normalize(sketch)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return dict(ok=False, exists=False, message=f"자동 복구 데이터를 읽지 못했습니다: {exc}")
        return dict(ok=True, exists=True, sketch=sketch)

    def clear_draft(self):
        (self.folder / "recovery" / "draft.json").unlink(missing_ok=True)
        return dict(ok=True)

    def import_image(self, data):
        """스케치 표 이미지에서 주된 가로·세로 선을 찾아 편집 가능한 격자로 만든다."""
        if not isinstance(data, str):
            raise ValueError("표 스케치 이미지를 읽지 못했습니다.")
        encoded = data.split(",", 1)[-1] if data.startswith("data:") else data
        if len(encoded) > 12_000_000:
            raise ValueError("이미지가 너무 큽니다. 8MB 이하 파일을 사용해 주세요.")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("이미지 데이터가 올바르지 않습니다.") from exc
        from io import BytesIO
        from PIL import Image, ImageOps
        try:
            image = Image.open(BytesIO(raw))
            if image.width < 32 or image.height < 32 or image.width * image.height > 16_000_000:
                raise ValueError("표 스케치 이미지 크기를 확인해 주세요.")
            image.load()
            gray = ImageOps.grayscale(image)
            gray.thumbnail((1200, 1200))
        except (OSError, Image.DecompressionBombError) as exc:
            raise ValueError("지원하는 그림 파일을 읽지 못했습니다.") from exc
        width, height = gray.size
        pixels = gray.load()
        threshold = 170
        horizontal = []
        for y in range(height):
            count = sum(1 for x in range(width) if pixels[x, y] < threshold)
            if count >= width * 0.35:
                horizontal.append(y)
        vertical = []
        for x in range(width):
            count = sum(1 for y in range(height) if pixels[x, y] < threshold)
            if count >= height * 0.35:
                vertical.append(x)

        def groups(values, gap=5):
            result = []
            for value in values:
                if not result or value - result[-1][-1] > gap:
                    result.append([value])
                else:
                    result[-1].append(value)
            return [round(sum(group) / len(group)) for group in result]

        ys, xs = groups(horizontal), groups(vertical)
        if len(xs) < 2 or len(ys) < 2 or len(xs) > 101 or len(ys) > 101:
            raise ValueError("표의 가로·세로 선을 충분히 찾지 못했습니다. 선이 선명한 정면 이미지를 사용해 주세요.")
        lines = []
        for row, y in enumerate(ys):
            lines.append(dict(x1=0, y1=row, x2=len(xs)-1, y2=row))
        for col, x in enumerate(xs):
            lines.append(dict(x1=col, y1=0, x2=col, y2=len(ys)-1))
        sketch = dict(grid=dict(cols=len(xs)-1, rows=len(ys)-1, cell_mm=5.0), lines=lines, texts=[])
        table_sketch.normalize(sketch)
        return dict(ok=True, sketch=sketch, rows=len(ys)-1, cols=len(xs)-1)

    def recognize(self, data):
        """표 스케치 이미지(base64/data URL)의 선을 격자 sketch로 인식한다(화면 연결 전 1단계)."""
        if not isinstance(data, str):
            raise ValueError("표 스케치 이미지를 읽지 못했습니다.")
        encoded = data.split(",", 1)[-1] if data.startswith("data:") else data
        if len(encoded) > 12_000_000:
            raise ValueError("이미지가 너무 큽니다. 8MB 이하 파일을 사용해 주세요.")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("이미지 데이터가 올바르지 않습니다.") from exc
        from docfit_core import table_sketch_recognize
        found = table_sketch_recognize.recognize_image(raw)
        _, warnings = table_sketch.normalize(found["sketch"])
        return dict(ok=True, sketch=found["sketch"], rows=found["rows"], cols=found["cols"],
                    angle=found["angle"], warnings=found["warnings"] + warnings)

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

    @staticmethod
    def _hwpx_payload(payload):
        """{path, cell_mm} 확인 → (경로, 칸 간격). 칸 간격이 이상하면 5mm."""
        if not isinstance(payload, dict) or not isinstance(payload.get("path"), str) or not payload["path"]:
            raise ValueError("HWPX 파일 경로를 지정해 주세요.")
        path = Path(payload["path"])
        if path.suffix.lower() != ".hwpx" or not path.is_file():
            raise ValueError(".hwpx 파일을 찾지 못했습니다.")
        cell_mm = payload.get("cell_mm", 5.0)
        if isinstance(cell_mm, bool) or not isinstance(cell_mm, (int, float)) or not 0.5 <= cell_mm <= 50:
            cell_mm = 5.0
        return path, float(cell_mm)

    def list_hwpx(self, payload):
        """HWPX 파일 안 최상위 표 목록(번호·행×열·첫 칸 글·가져올 수 있는지). 화면의 표 고르기용."""
        path, cell_mm = self._hwpx_payload(payload)
        found = list_hwpx_tables(path, cell_mm)
        message = "" if found["tables"] else "이 문서에는 표가 없습니다."
        return dict(ok=True, tables=found["tables"], total=found["total"], message=message)

    def import_hwpx(self, payload):
        """HWPX 파일의 N번째 표(0부터)를 표그림판 그림으로. 원본은 읽기만 한다(클립보드·화면은 별도)."""
        path, cell_mm = self._hwpx_payload(payload)
        sketch, info = import_hwpx_table(path, payload.get("index", 0), cell_mm)
        sketch, normalize_warnings = table_sketch.normalize(sketch)
        warnings = info["warnings"] + normalize_warnings
        return dict(ok=True, sketch=sketch, rows=info["rows"], cols=info["cols"], tables=info["tables"], warnings=warnings,
                    message=f"HWPX 표({info['rows']}행 × {info['cols']}열)를 가져왔어요.")

    def command(self, action, payload=None):
        try:
            if action == "preview": return table_sketch.preview(payload)
            if action == "copy": return self.copy(payload)
            if action == "list": return self.list()
            if action == "save" and isinstance(payload, dict):
                return self.save(payload.get("name"), payload.get("sketch"))
            if action == "load": return self.load(payload)
            if action == "delete": return self.delete(payload)
            if action == "save_draft" and isinstance(payload, dict): return self.save_draft(payload.get("sketch"))
            if action == "load_draft": return self.load_draft()
            if action == "clear_draft": return self.clear_draft()
            if action == "import_image": return self.import_image(payload)
            if action == "recognize": return self.recognize(payload)
            if action == "paste_hwp": return self.paste_hwp(payload)
            if action == "import_hwpx_table": return self.import_hwpx(payload)
            if action == "list_hwpx_tables": return self.list_hwpx(payload)
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
