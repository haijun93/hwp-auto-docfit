"""표 템플릿: 스냅샷으로 고르고 정보단위 개수를 바꿔 한/글에 붙여넣을 수 있게 복사한다(2026-10-22).

- 템플릿 원본은 사용자가 고칠 수 있는 `C:\\HWP_AUTODOCFIT\\표서식모음\\표 서식모음.hwpx`를 먼저 쓰고, 없으면 앱 내장본을 쓴다.
- 정보단위 분석·조절은 docfit_core.table_units(한/글 없이 HWPX XML만 다룸).
- 스냅샷 그림은 한/글로 PDF를 만든 뒤 표 부분만 잘라 PNG로 저장하고, 원본 파일 해시별로 캐시한다.
- 복사는 조절한 HWPX를 숨긴 한/글로 열어 복사한다. 한/글을 닫아도 클립보드의 'Hwp Native' 형식이 남아
  사용자가 한/글에서 Ctrl+V 하면 서식 그대로 붙는다(2026-10-22 실측).
"""
from __future__ import annotations

import base64
import hashlib
import shutil
import tempfile
from pathlib import Path

from docfit_core import table_units
from docfit_core.table_catalog import default_catalog_path

from .api_contract import ServiceError

USER_CATALOG = Path(r"C:\HWP_AUTODOCFIT") / "표서식모음" / "표 서식모음.hwpx"
SNAPSHOT_FOLDER = ".스냅샷"
SNAPSHOT_REVISION = b"C13-shapes-v1"
HWP_CLIPBOARD_FORMAT = "Hwp Native"


def catalog_path(user_catalog: Path = USER_CATALOG) -> Path:
    return user_catalog if user_catalog.is_file() else default_catalog_path()


def _digest(path: Path) -> str:
    return hashlib.sha256(SNAPSHOT_REVISION + path.read_bytes()).hexdigest()[:16]


def _safe_name(template_id: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in str(template_id))


def crop_to_content(image, margin: int = 6):
    """흰 여백을 잘라 표 부분만 남긴다."""
    from PIL import ImageChops, Image
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, (255, 255, 255))
    box = ImageChops.difference(rgb, background).getbbox()
    if not box:
        return rgb
    left, top, right, bottom = box
    return rgb.crop((max(0, left - margin), max(0, top - margin),
                     min(rgb.width, right + margin), min(rgb.height, bottom + margin)))


class TableUnitsService:
    def __init__(self, hwp_factory=None, *, source: Path | None = None, snapshot_root: Path | None = None,
                 clipboard_formats=None, settings=None, activator=None):
        # hwp_factory: 독립 한/글 COM 객체를 만들어 돌려주는 함수(보안 모듈 등록·숨김 포함). 시험에서는 가짜.
        self._hwp_factory = hwp_factory
        self._source = source
        self._snapshot_root = snapshot_root
        self._content_cache: dict[str, dict[str, str]] = {}
        self._clipboard_formats = clipboard_formats or _clipboard_formats
        self._settings = settings
        self._memory = {}
        self._activator = activator or _activate_visible_hwp

    def _preferences(self):
        return self._settings.read() if self._settings else self._memory

    def _update_preferences(self, change):
        if self._settings:
            self._settings.update(change)
        else:
            change(self._memory)

    def favorite(self, template_id, on):
        if not isinstance(template_id, str) or type(on) is not bool or template_id not in {t["id"] for t in self._units()}:
            raise ServiceError("INVALID_INPUT", "즐겨찾기 표와 선택 값을 확인해 주세요.")
        def update(data):
            favorites = _id_list(data.get("table_template_favorites"))
            data["table_template_favorites"] = [v for v in favorites if v != template_id]
            if on:
                data["table_template_favorites"].append(template_id)
        self._update_preferences(update)
        return self.list()

    @property
    def source(self) -> Path:
        return Path(self._source) if self._source else catalog_path()

    def _snapshot_dir(self) -> Path:
        root = Path(self._snapshot_root) if self._snapshot_root else USER_CATALOG.parent / SNAPSHOT_FOLDER
        return root / _digest(self.source)

    def _content_keys(self) -> dict[str, str]:
        """템플릿마다 표 XML 내용 지문(그림 판 표식 포함). 서식모음 파일을 한 번만 열어 모두 계산하고 파일 지문별로 기억한다.

        그림을 파일 전체 지문 폴더에 두면 서식모음에 표 하나만 더해도 모든 그림이 사라졌다(2026-10-23 사용자 실측) —
        표 내용 지문으로 두면 바뀌지 않은 표의 그림은 그대로 쓴다."""
        from defusedxml import ElementTree as ET
        from docfit_core import table_catalog as catalog
        digest = _digest(self.source)
        cached = self._content_cache.get(digest)
        if cached is not None:
            return cached
        keys: dict[str, str] = {}
        try:
            records = catalog._scan(self.source)
            sections = {}
            with catalog._safe_archive(self.source) as archive:
                for record in records:
                    name = record["section"]
                    if name not in sections:
                        sections[name] = ET.fromstring(archive.read(name))
                    paragraph = sections[name].findall(table_units.HP + "p")[record["paragraph_index"]]
                    table = catalog._top_tables(paragraph)[record["table_index"]]
                    keys[str(record["id"])] = hashlib.sha256(SNAPSHOT_REVISION + ET.tostring(table)).hexdigest()[:20]
        except Exception:
            keys = {}
        self._content_cache = {digest: keys}
        return keys

    def _snapshot_path(self, template_id: str) -> Path:
        key = self._content_keys().get(str(template_id))
        if key:
            root = Path(self._snapshot_root) if self._snapshot_root else USER_CATALOG.parent / SNAPSHOT_FOLDER
            return root / "tables" / f"{key}.png"
        return self._snapshot_dir() / f"{_safe_name(template_id)}.png"

    def _snapshot_url(self, template_id: str) -> str | None:
        path = self._snapshot_path(template_id)
        if not path.is_file():
            legacy = self._snapshot_dir() / f"{_safe_name(template_id)}.png"
            if not legacy.is_file():
                return None
            path = legacy
        return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")

    def _units(self):
        try:
            return table_units.describe_units(self.source)
        except (OSError, ValueError) as exc:
            raise ServiceError("CATALOG_UNAVAILABLE", f"표 서식 모음을 읽지 못했습니다: {exc}") from exc

    def list(self) -> dict:
        preferences = self._preferences()
        favorites = _id_list(preferences.get("table_template_favorites"))
        templates = []
        for item in self._units():
            templates.append({**item, "thumbnail": self._snapshot_url(item["id"]),
                              "favorite": item["id"] in favorites})
        ids = {t["id"] for t in templates}
        return {"source": str(self.source), "templates": templates,
                "recent": [v for v in _id_list(preferences.get("table_template_recent")) if v in ids][:8],
                "thumbnails_ready": bool(templates) and all(item["thumbnail"] for item in templates)}

    def preview(self, template_id, row_count=None, col_count=None, *, fill="increment", cell_texts=None) -> dict:
        try:
            return table_units.preview(str(template_id), self.source, row_count=row_count, col_count=col_count,
                                       fill=fill, cell_texts=cell_texts)
        except (KeyError, ValueError) as exc:
            raise ServiceError("INVALID_INPUT", str(exc).strip("'\"")) from exc

    def _export(self, folder: Path, template_id, row_count=None, col_count=None, *, fill="increment", cell_texts=None) -> Path:
        target = folder / f"{_safe_name(template_id)}.hwpx"
        try:
            return table_units.export_resized(str(template_id), target, self.source,
                                              row_count=row_count, col_count=col_count, fill=fill, cell_texts=cell_texts)
        except (KeyError, ValueError) as exc:
            raise ServiceError("INVALID_INPUT", str(exc).strip("'\"")) from exc

    def _hwp(self):
        if self._hwp_factory is None:
            raise ServiceError("HWP_UNAVAILABLE", "한/글을 사용할 수 없어 이 작업을 할 수 없습니다.")
        return self._hwp_factory()

    @staticmethod
    def _close(app) -> None:
        for call in (lambda: app.Clear(1), app.Quit):
            try:
                call()
            except Exception:
                pass

    def copy(self, template_id, row_count=None, col_count=None, *, fill="increment", cell_texts=None) -> dict:
        folder = Path(tempfile.mkdtemp(prefix="docfit_table_copy_"))
        try:
            document = self._export(folder, template_id, row_count, col_count, fill=fill, cell_texts=cell_texts)
            app = self._hwp()
            try:
                if app.Open(str(document), "HWPX", "forceopen:true") is False:
                    raise ServiceError("HWP_FAILED", "한/글이 표 문서를 열지 못했습니다.")
                control = app.HeadCtrl
                while control is not None and control.CtrlID != "tbl":
                    control = control.Next
                if control is None:
                    raise ServiceError("HWP_FAILED", "복사할 표를 찾지 못했습니다.")
                if app.SetPosBySet(control.GetAnchorPos(0)) is False or app.FindCtrl() is False:
                    raise ServiceError("HWP_FAILED", "복사할 표를 선택하지 못했습니다.")
                if app.Run("Copy") is False:
                    raise ServiceError("CLIPBOARD_FAILED", "표를 복사하지 못했습니다.")
            finally:
                self._close(app)
            if HWP_CLIPBOARD_FORMAT not in self._clipboard_formats():
                raise ServiceError("CLIPBOARD_FAILED", "클립보드에 한/글 표를 넣지 못했습니다. 다시 시도해 주세요.")
            def update(data):
                recent = _id_list(data.get("table_template_recent"))
                data["table_template_recent"] = [str(template_id)] + [v for v in recent if v != str(template_id)][:7]
            self._update_preferences(update)
            try:
                activated = bool(self._activator())
            except Exception:
                activated = False
            return {"copied": True, "activated": activated,
                    "message": "표를 복사했어요. 한/글 문서에서 붙여넣을 곳을 누르고 Ctrl+V 하세요."}
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def thumbnails(self) -> dict:
        """모든 템플릿의 실제 모양 그림을 한/글로 만든다(이미 있는 그림은 다시 만들지 않음)."""
        import pypdfium2 as pdfium

        from docfit_core.file_conversion import convert_hwpx_to_pdf

        items = self._units()
        missing = [item for item in items if not self._snapshot_path(item["id"]).is_file()]
        if missing:
            folder = Path(tempfile.mkdtemp(prefix="docfit_table_snap_"))
            app = None
            try:
                app = self._hwp()
                for item in missing:
                    document = self._export(folder, item["id"])
                    pdf = folder / f"{_safe_name(item['id'])}.pdf"
                    convert_hwpx_to_pdf(app, document, pdf)
                    try:
                        app.Clear(1)
                    except Exception:
                        pass
                    rendered = pdfium.PdfDocument(str(pdf))
                    try:
                        image = rendered[0].render(scale=110 / 72).to_pil()
                    finally:
                        rendered.close()
                    picture = crop_to_content(image)
                    picture.thumbnail((640, 640))
                    target = self._snapshot_path(item["id"])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    temporary = target.with_name(target.name + ".tmp")
                    picture.save(temporary, format="PNG", optimize=True)
                    temporary.replace(target)
            finally:
                if app is not None:
                    self._close(app)
                shutil.rmtree(folder, ignore_errors=True)
            # 예전 파일 지문 폴더(표 내용 지문 저장 전 방식)는 지운다.
            self._remove_old_snapshots(self._snapshot_dir())
        return self.list()

    @staticmethod
    def _remove_old_snapshots(current: Path) -> None:
        """템플릿 파일이 바뀌어 새 해시 폴더를 만들었으면 예전 해시 폴더의 그림은 지운다."""
        for folder in current.parent.iterdir():
            if folder.is_dir() and folder != current and len(folder.name) == len(current.name):
                shutil.rmtree(folder, ignore_errors=True)

    def command(self, action, payload=None):
        if payload is not None and not isinstance(payload, dict):
            raise ServiceError("INVALID_INPUT", "표 템플릿 입력 형식을 확인해 주세요.")
        payload = payload or {}
        counts = {key: payload.get(key) for key in ("row_count", "col_count")}
        for key, value in counts.items():
            if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
                raise ServiceError("INVALID_INPUT", "정보단위 개수를 확인해 주세요.")
        if action == "list":
            return self.list()
        if action == "thumbnails":
            return self.thumbnails()
        if action == "favorite":
            return self.favorite(payload.get("id"), payload.get("on"))
        if action in ("preview", "copy"):
            template_id = payload.get("id")
            if not isinstance(template_id, str) or not template_id:
                raise ServiceError("INVALID_INPUT", "표 템플릿을 골라 주세요.")
            method = self.preview if action == "preview" else self.copy
            try:
                table_units.validate_input(payload.get("fill", "increment"), payload.get("cell_texts"))
            except ValueError as exc:
                raise ServiceError("INVALID_INPUT", str(exc)) from exc
            return method(template_id, **counts, fill=payload.get("fill", "increment"), cell_texts=payload.get("cell_texts"))
        raise ServiceError("INVALID_INPUT", "표 템플릿 작업을 확인해 주세요.")


def _id_list(value):
    return list(dict.fromkeys(v for v in value if isinstance(v, str))) if isinstance(value, list) else []


def _activate_visible_hwp():
    import win32gui
    import win32con

    windows = []
    def collect(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        cls, title = win32gui.GetClassName(hwnd), win32gui.GetWindowText(hwnd)
        if cls.startswith("HwndWrapper[Hwp") or cls.startswith("Hwp") or (cls == "HNC_FRAME" and ("한글" in title or "한/글" in title)):
            windows.append(hwnd)
    win32gui.EnumWindows(collect, None)
    for hwnd in windows:
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return win32gui.GetForegroundWindow() == hwnd
        except Exception:
            continue
    return False


def _clipboard_formats() -> list[str]:
    import win32clipboard

    win32clipboard.OpenClipboard()
    try:
        names, fmt = [], 0
        while True:
            fmt = win32clipboard.EnumClipboardFormats(fmt)
            if not fmt:
                return names
            try:
                names.append(win32clipboard.GetClipboardFormatName(fmt))
            except Exception:
                names.append(str(fmt))
    finally:
        win32clipboard.CloseClipboard()
