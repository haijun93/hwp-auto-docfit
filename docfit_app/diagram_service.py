"""Opt-in local diagram snapshot storage for the native developer prototype."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile

from docfit_app.api_contract import ServiceError
from docfit_app.settings_migrations import migrate


_ID = re.compile(r"^[a-f0-9]{32}$")
_MAX_SNAPSHOT_BYTES = 700 * 1024


class DiagramService:
    def __init__(self, app_folder, settings_store):
        self.app_folder = Path(app_folder).resolve()
        self.root = self.app_folder / "diagrams"
        self.settings_store = settings_store

    def enabled(self):
        settings = migrate(self.settings_store.read())
        return settings.get("developer_mode") is True and settings.get("diagram_editor_enabled") is True

    def require_enabled(self):
        if not self.enabled():
            raise ServiceError("DIAGRAMS_DISABLED", "개발자 모드와 tldraw 도형 편집기를 모두 켜야 사용할 수 있습니다.")

    def _document_path(self, diagram_id):
        if not isinstance(diagram_id, str) or not _ID.fullmatch(diagram_id):
            raise ServiceError("INVALID_DIAGRAM_ID", "도형 문서 식별자를 확인해 주세요.")
        if self.root.is_symlink():
            raise ServiceError("DIAGRAM_PATH_INVALID", "도형 저장 폴더 경로가 올바르지 않습니다.")
        path = self.root / (diagram_id + ".json")
        if path.parent.resolve() != self.root.resolve():
            raise ServiceError("INVALID_DIAGRAM_ID", "도형 문서 경로를 확인해 주세요.")
        return path

    def list(self):
        self.require_enabled()
        if self.root.is_symlink():
            raise ServiceError("DIAGRAM_PATH_INVALID", "도형 저장 폴더 경로가 올바르지 않습니다.")
        self.root.mkdir(parents=True, exist_ok=True)
        result = []
        for path in self.root.glob("*.json"):
            if not _ID.fullmatch(path.stem) or path.is_symlink():
                continue
            try:
                if path.stat().st_size > _MAX_SNAPSHOT_BYTES + 16_384:
                    continue
                item = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(item, dict) and isinstance(item.get("name"), str):
                    result.append({"id": path.stem, "name": item["name"],
                                   "updated_at": item.get("updated_at", "")})
            except (OSError, ValueError):
                continue
        return sorted(result, key=lambda item: item["updated_at"], reverse=True)

    def load(self, diagram_id):
        self.require_enabled()
        path = self._document_path(diagram_id)
        try:
            if path.is_symlink() or path.stat().st_size > _MAX_SNAPSHOT_BYTES + 16_384:
                raise ServiceError("DIAGRAM_INVALID", "도형 파일 크기나 경로가 올바르지 않습니다.")
            item = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ServiceError("DIAGRAM_NOT_FOUND", "저장된 도형 문서를 찾지 못했습니다.") from exc
        except (OSError, ValueError) as exc:
            raise ServiceError("DIAGRAM_READ_FAILED", "도형 문서를 읽지 못했습니다.") from exc
        if not isinstance(item, dict) or not isinstance(item.get("snapshot"), dict):
            raise ServiceError("DIAGRAM_INVALID", "도형 문서 형식이 올바르지 않습니다.")
        return item

    def save(self, diagram_id, name, snapshot):
        self.require_enabled()
        path = self._document_path(diagram_id)
        if self.root.is_symlink():
            raise ServiceError("DIAGRAM_PATH_INVALID", "도형 저장 폴더 경로가 올바르지 않습니다.")
        if not isinstance(name, str) or not name.strip() or len(name) > 120 or "\x00" in name:
            raise ServiceError("INVALID_DIAGRAM_NAME", "도형 문서 이름은 1~120자여야 합니다.")
        if not isinstance(snapshot, dict):
            raise ServiceError("INVALID_DIAGRAM", "도형 문서 데이터가 올바르지 않습니다.")
        try:
            encoded = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ServiceError("INVALID_DIAGRAM", "도형 문서에 저장할 수 없는 값이 있습니다.") from exc
        if len(encoded) > _MAX_SNAPSHOT_BYTES:
            raise ServiceError("DIAGRAM_TOO_LARGE", "도형 데이터가 너무 큽니다. 포함된 이미지나 도형 수를 줄여 주세요.")
        self.root.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            raise ServiceError("DIAGRAM_INVALID", "도형 저장 경로가 올바르지 않습니다.")
        old = {}
        if path.exists():
            try:
                old = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                old = {}
        item = {"version": 1, "id": diagram_id, "name": name.strip(),
                "updated_at": datetime.now(timezone.utc).isoformat(), "snapshot": snapshot,
                "png_sha256": old.get("png_sha256", "") if isinstance(old, dict) else ""}
        temporary = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.root,
                                             prefix=diagram_id + ".", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(item, stream, ensure_ascii=False, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except (OSError, ValueError, TypeError) as exc:
            raise ServiceError("DIAGRAM_WRITE_FAILED", "도형 문서를 저장하지 못했습니다.") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
        return {"id": diagram_id, "name": item["name"], "updated_at": item["updated_at"]}

    def delete(self, diagram_id):
        self.require_enabled()
        path = self._document_path(diagram_id)
        try:
            if path.is_symlink():
                raise ServiceError("DIAGRAM_INVALID", "도형 저장 경로가 올바르지 않습니다.")
            path.unlink()
        except FileNotFoundError as exc:
            raise ServiceError("DIAGRAM_NOT_FOUND", "저장된 도형 문서를 찾지 못했습니다.") from exc
        except OSError as exc:
            raise ServiceError("DIAGRAM_DELETE_FAILED", "도형 문서를 삭제하지 못했습니다.") from exc
        return {"deleted": True}
