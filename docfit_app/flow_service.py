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

    def save(self, diagram_id, name, snapshot):
        if not isinstance(snapshot, dict) or snapshot.get("format") != "docfit-flow" or snapshot.get("version") != 1:
            raise ServiceError("INVALID_FLOW", "일반 흐름도 형식을 확인해 주세요.")
        if not isinstance(snapshot.get("nodes"), list) or not isinstance(snapshot.get("edges"), list):
            raise ServiceError("INVALID_FLOW", "도형과 연결선 목록을 확인해 주세요.")
        if len(snapshot["nodes"]) > 1000 or len(snapshot["edges"]) > 2000:
            raise ServiceError("FLOW_LIMIT", "도형 또는 연결선 수가 제한을 넘습니다.")
        return super().save(diagram_id, name, snapshot)


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
