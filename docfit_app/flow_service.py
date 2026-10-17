"""General-mode flow storage, separate from opt-in tldraw snapshots."""
from docfit_app.diagram_service import DiagramService
from docfit_app.api_contract import ServiceError


class FlowService(DiagramService):
    def __init__(self, app_folder, settings_store):
        super().__init__(app_folder, settings_store)
        self.root = self.app_folder / "flows"

    def enabled(self):
        return True

    def require_enabled(self):
        # This editor uses React Flow (MIT); tldraw gates remain in DiagramService.
        pass

    def save(self, diagram_id, name, snapshot, expected_revision=None):
        if not isinstance(snapshot, dict) or snapshot.get("format") != "docfit-flow" or snapshot.get("version") != 1:
            raise ServiceError("INVALID_FLOW", "일반 흐름도 형식을 확인해 주세요.")
        if not isinstance(snapshot.get("nodes"), list) or not isinstance(snapshot.get("edges"), list):
            raise ServiceError("INVALID_FLOW", "도형과 연결선 목록을 확인해 주세요.")
        if len(snapshot["nodes"]) > 1000 or len(snapshot["edges"]) > 2000:
            raise ServiceError("FLOW_LIMIT", "도형 또는 연결선 수가 제한을 넘습니다.")
        return super().save(diagram_id, name, snapshot, expected_revision)


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

    def export_catalog(self, template_id, *, cell_edits=None, structure_edits=None):
        """Save a native table copy with requested text and row/column edits."""
        import uuid
        from docfit_core.table_catalog import export_template
        folder = self._catalog_export_folder()
        path = folder / (uuid.uuid4().hex + ".hwpx")
        try:
            export_template(template_id, path, cell_edits=cell_edits, structure_edits=structure_edits)
        except (ValueError, OSError) as exc:
            path.unlink(missing_ok=True)
            raise ServiceError("CATALOG_EXPORT_FAILED", "표 서식을 HWPX로 내보내지 못했습니다.") from exc
        return {"path": str(path)}

    def copy_catalog(self, template_id, *, cell_edits=None, structure_edits=None):
        """Publish a selected template through Hancom's native clipboard format."""
        import tempfile
        from docfit_core.table_catalog import export_template
        folder = self._catalog_export_folder()
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=folder, suffix=".hwpx", delete=False) as stream:
                temporary = __import__("pathlib").Path(stream.name)
            export_template(template_id, temporary, cell_edits=cell_edits, structure_edits=structure_edits)
            from docfit_app.native_table_clipboard import copy_hwpx_document
            return copy_hwpx_document(temporary)
        except ServiceError:
            raise
        except (ValueError, OSError) as exc:
            raise ServiceError("CATALOG_COPY_FAILED", "선택한 표 서식을 복사하지 못했습니다.") from exc
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

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
