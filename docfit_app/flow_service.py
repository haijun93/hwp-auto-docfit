"""Local React Flow snapshot storage."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from hashlib import sha256
from docfit_infra.storage.process_lock import ProcessLock

from docfit_app.api_contract import ServiceError


_ID = re.compile(r"^[a-f0-9]{32}$")
_MAX_SNAPSHOT_BYTES = 700 * 1024


class FlowService:
    def __init__(self, app_folder, settings_store):
        self.app_folder = Path(app_folder).resolve()
        self.root = self.app_folder / "flows"
        self.settings_store = settings_store

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
        path = self._document_path(diagram_id)
        try:
            if path.is_symlink() or path.stat().st_size > _MAX_SNAPSHOT_BYTES + 16_384:
                raise ServiceError("DIAGRAM_INVALID", "도형 파일 크기나 경로가 올바르지 않습니다.")
            raw = path.read_bytes()
            item = json.loads(raw.decode("utf-8"))
        except FileNotFoundError as exc:
            raise ServiceError("DIAGRAM_NOT_FOUND", "저장된 도형 문서를 찾지 못했습니다.") from exc
        except (OSError, ValueError) as exc:
            raise ServiceError("DIAGRAM_READ_FAILED", "도형 문서를 읽지 못했습니다.") from exc
        if not isinstance(item, dict) or not isinstance(item.get("snapshot"), dict):
            raise ServiceError("DIAGRAM_INVALID", "도형 문서 형식이 올바르지 않습니다.")
        item["revision"] = sha256(raw).hexdigest()
        return item

    def _save_snapshot(self, diagram_id, name, snapshot, expected_revision=None):
        path = self._document_path(diagram_id)
        with ProcessLock(path.with_suffix(".lock")):
            current = self.load(diagram_id) if path.exists() else None
            if ((current is None and expected_revision is not None)
                    or (current is not None and expected_revision != current["revision"])):
                raise ServiceError("DIAGRAM_CONFLICT", "다른 편집자가 문서를 변경했습니다. 새 문서로 저장하거나 다시 열어 주세요.")
            result = self._save_locked(diagram_id, name, snapshot)
            result["revision"] = self.load(diagram_id)["revision"]
            return result

    def _save_locked(self, diagram_id, name, snapshot):
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
        path = self._document_path(diagram_id)
        with ProcessLock(path.with_suffix(".lock")):
            return self._delete_locked(path)

    def _delete_locked(self, path):
        try:
            if path.is_symlink():
                raise ServiceError("DIAGRAM_INVALID", "도형 저장 경로가 올바르지 않습니다.")
            path.unlink()
        except FileNotFoundError as exc:
            raise ServiceError("DIAGRAM_NOT_FOUND", "저장된 도형 문서를 찾지 못했습니다.") from exc
        except OSError as exc:
            raise ServiceError("DIAGRAM_DELETE_FAILED", "도형 문서를 삭제하지 못했습니다.") from exc
        return {"deleted": True}

    def save(self, diagram_id, name, snapshot, expected_revision=None):
        if not isinstance(snapshot, dict) or snapshot.get("format") != "docfit-flow" or snapshot.get("version") != 1:
            raise ServiceError("INVALID_FLOW", "일반 흐름도 형식을 확인해 주세요.")
        if not isinstance(snapshot.get("nodes"), list) or not isinstance(snapshot.get("edges"), list):
            raise ServiceError("INVALID_FLOW", "도형과 연결선 목록을 확인해 주세요.")
        if len(snapshot["nodes"]) > 1000 or len(snapshot["edges"]) > 2000:
            raise ServiceError("FLOW_LIMIT", "도형 또는 연결선 수가 제한을 넘습니다.")
        return self._save_snapshot(diagram_id, name, snapshot, expected_revision)


    @staticmethod
    def png_bytes(encoded):
        import base64
        import binascii
        import struct
        if not isinstance(encoded, str) or len(encoded) > 28 * 1024 * 1024:
            raise ServiceError("INVALID_PNG", "PNG 크기가 제한을 넘습니다.")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ServiceError("INVALID_PNG", "PNG 데이터가 올바르지 않습니다.") from exc
        if len(data) < 33 or len(data) > 20 * 1024 * 1024 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
            raise ServiceError("INVALID_PNG", "PNG 형식이 올바르지 않습니다.")
        width, height = struct.unpack(">II", data[16:24])
        if not width or not height or width * height > 30_000_000:
            raise ServiceError("INVALID_PNG", "PNG 이미지 크기가 제한을 넘습니다.")
        return data

    def export_hwpx(self, spec, base_path, basic_style=None):
        """표/다이어그램 편집기의 흐름표·기본 표를 HWPX로 만들어 내보내기 폴더에 둔다(docfit_core.table_builder)."""
        import uuid
        from docfit_core.table_builder import TableSpecError, build_table_hwpx
        if not isinstance(spec, dict) or spec.get("kind") not in {"flow", "grid"}:
            raise ServiceError("TABLE_KIND_DISABLED", "알파 버전에서는 흐름표와 기본 표만 만들 수 있습니다.")
        folder = self.root / "exports"
        if self.root.is_symlink() or folder.is_symlink():
            raise ServiceError("DIAGRAM_PATH_INVALID", "표 저장 폴더 경로가 올바르지 않습니다.")
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (uuid.uuid4().hex + ".hwpx")
        try:
            build_table_hwpx(spec, base_path, path, basic_style=basic_style)
        except TableSpecError as exc:
            path.unlink(missing_ok=True)
            raise ServiceError("INVALID_TABLE", str(exc)) from exc
        return {"path": str(path)}

    def _catalog_export_folder(self):
        folder = self.root / "exports"
        if self.root.is_symlink() or folder.is_symlink():
            raise ServiceError("DIAGRAM_PATH_INVALID", "표 저장 폴더 경로가 올바르지 않습니다.")
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def export_catalog(self, template_id, *, cell_edits=None, structure_edits=None, style_edits=None):
        """Save a native table copy with requested text, row/column, and style/border edits."""
        raise ServiceError("FEATURE_DISABLED", "표 서식 모음은 현재 알파 버전에서 비활성화되어 있습니다.")

    def copy_catalog(self, template_id, *, cell_edits=None, structure_edits=None, style_edits=None):
        """Publish a selected template through Hancom's native clipboard format."""
        raise ServiceError("FEATURE_DISABLED", "표 서식 모음은 현재 알파 버전에서 비활성화되어 있습니다.")

    def export_shapes_hwpx(self, snapshot):
        """다이어그램 스냅샷을 한/글 도형 HWPX 문서로 생성해 내보낸다."""
        import uuid
        from docfit_core.diagram_shapes import diagram_to_hwpx
        folder = self.root / "exports"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (uuid.uuid4().hex + ".hwpx")
        try:
            diagram_to_hwpx(snapshot, path)
        except Exception as exc:
            path.unlink(missing_ok=True)
            raise ServiceError("INVALID_DIAGRAM_SHAPES", str(exc)) from exc
        return {"path": str(path)}

    def export_png(self, encoded):
        import uuid
        data = self.png_bytes(encoded)
        folder = self.root / "exports"
        if self.root.is_symlink() or folder.is_symlink():
            raise ServiceError("DIAGRAM_PATH_INVALID", "그림 저장 폴더 경로가 올바르지 않습니다.")
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (uuid.uuid4().hex + ".png")
        with path.open("xb") as stream:
            stream.write(data)
        return {"path": str(path)}
