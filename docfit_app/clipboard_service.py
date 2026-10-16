"""Publish eager Windows clipboard formats; no document or COM instance is changed."""
import io
import sys
import time
from docfit_app.api_contract import ServiceError
from docfit_core.table_clipboard import cf_html, table_html


def copy_result(payload):
    if sys.platform != "win32":
        raise ServiceError("CLIPBOARD_UNAVAILABLE", "한/글 붙여넣기 복사는 Windows에서 사용할 수 있습니다.")
    import win32clipboard as clipboard
    if payload.get("kind") == "table":
        html, text = table_html(payload.get("spec"))
        formats = [(clipboard.RegisterClipboardFormat("HTML Format"), cf_html(html)), (13, text)]
        result = "table"
    elif payload.get("kind") == "png":
        from PIL import Image
        from docfit_app.flow_service import FlowService
        data = FlowService.png_bytes(payload.get("base64"))
        with Image.open(io.BytesIO(data)) as source:
            if source.format != "PNG":
                raise ValueError("PNG 파일이 아닙니다.")
            source.load()
            image = Image.new("RGB", source.size, "white")
            rgba = source.convert("RGBA")
            image.paste(rgba, mask=rgba.getchannel("A"))
            stream = io.BytesIO()
            image.save(stream, format="BMP")
        formats = [(8, stream.getvalue()[14:]), (clipboard.RegisterClipboardFormat("PNG"), data)]
        result = "image"
    else:
        raise ServiceError("INVALID_INPUT", "복사할 표 또는 그림을 확인해 주세요.")
    for attempt in range(4):
        try:
            clipboard.OpenClipboard()
            break
        except Exception as exc:
            if attempt == 3:
                raise ServiceError("CLIPBOARD_BUSY", "클립보드를 사용할 수 없습니다. 잠시 후 다시 복사해 주세요.") from exc
            time.sleep(.025)
    try:
        clipboard.EmptyClipboard()
        for format_id, value in formats:
            clipboard.SetClipboardData(format_id, value)
    finally:
        clipboard.CloseClipboard()
    return {"copied": True, "format": result}
