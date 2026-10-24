"""Copy a HWPX document through Hancom's native clipboard provider.

HTML clipboard is useful for ordinary tables, but cannot preserve every HWPX cell
property. Opening the generated single-table HWPX in an isolated hidden HWP COM
instance and invoking Copy publishes Hancom's native table format instead.
"""

from pathlib import Path
import sys
import time

from .api_contract import ServiceError


def read_clipboard_table():
    """사용자 문서와 분리된 세션에서 복사된 표를 HWPX 사본으로 읽는다."""
    import tempfile
    import pythoncom
    import win32com.client
    import win32clipboard
    from docfit_core import table_import
    native = win32clipboard.RegisterClipboardFormat('Hwp Native')
    if not win32clipboard.IsClipboardFormatAvailable(native):
        html_format = win32clipboard.RegisterClipboardFormat('HTML Format')
        win32clipboard.OpenClipboard()
        try:
            if not win32clipboard.IsClipboardFormatAvailable(html_format):
                raise ValueError('한/글에서 표를 먼저 복사해 주세요.')
            data = win32clipboard.GetClipboardData(html_format)
        finally:
            win32clipboard.CloseClipboard()
        return table_import.import_table_from_html(data.decode('utf8') if isinstance(data, bytes) else data)
    app = None
    pythoncom.CoInitialize()
    try:
        app = win32com.client.DispatchEx('HwpFrame.HwpObject')
        app.XHwpWindows.Item(0).Visible = False
        from docfit_core.format_samples import APP_HOME, REGISTRY_VALUE, LEGACY_REGISTRY_VALUE
        module = REGISTRY_VALUE if (APP_HOME / 'dll' / 'HwpAutoDocFitSecurity.dll').is_file() else LEGACY_REGISTRY_VALUE
        if not app.RegisterModule('FilePathCheckDLL', module):
            raise ValueError('한/글 보안 모듈을 등록하지 못했습니다.')
        with tempfile.TemporaryDirectory(prefix='docfit_paste_') as folder:
            path = Path(folder) / 'clipboard.hwpx'
            if app.HAction.Run('Paste') is False or app.SaveAs(str(path), 'HWPX', '') is False:
                raise ValueError('복사된 표를 읽지 못했습니다.')
            result = table_import.import_table_from_hwpx(path)
            app.Clear(1)
            return result
    finally:
        if app is not None:
            try:
                app.Clear(1)
                app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def copy_hwpx_document(path: str | Path) -> dict:
    source = Path(path)
    if sys.platform != "win32":
        raise ServiceError("CLIPBOARD_UNAVAILABLE", "한/글 표 복사는 Windows에서만 사용할 수 있습니다.")
    if source.suffix.lower() != ".hwpx" or not source.is_file():
        raise ServiceError("INVALID_PATH", "복사할 HWPX 표 문서를 찾을 수 없습니다.")

    import pythoncom
    import win32com.client
    import win32clipboard

    app = None
    initialized = False
    try:
        pythoncom.CoInitialize()
        initialized = True
        try:
            app = win32com.client.DispatchEx("HwpFrame.HwpObject")
        except Exception as exc:
            raise ServiceError("HWP_COM_UNAVAILABLE", "사용자 한/글 문서와 분리된 복사 세션을 시작하지 못했습니다.") from exc
        try:
            app.XHwpWindows.Item(0).Visible = False
        except Exception:
            pass
        try:
            from docfit_core.format_samples import LEGACY_REGISTRY_VALUE, REGISTRY_VALUE
            from docfit_core.format_samples import APP_HOME
            module_name = REGISTRY_VALUE if (APP_HOME / "dll" / "HwpAutoDocFitSecurity.dll").is_file() else LEGACY_REGISTRY_VALUE
            registered = app.RegisterModule("FilePathCheckDLL", module_name)
            if not registered:
                raise ServiceError("HWP_SECURITY_MODULE", "한/글 보안 모듈 등록에 실패하여 표를 복사하지 못했습니다.")
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError("HWP_SECURITY_MODULE", "한/글 보안 모듈을 확인해 주세요.") from exc

        try:
            opened = app.Open(str(source), "HWPX", "")
            if opened is False:
                raise RuntimeError("한/글이 표 문서를 열지 못했습니다.")
            clipboard_sequence = win32clipboard.GetClipboardSequenceNumber()
            app.HAction.Run("SelectAll")
            app.HAction.Run("Copy")
            # Hancom publishes some native clipboard formats lazily via OLE.
            # Flush while the isolated HWP instance is alive; otherwise a fast
            # Quit can leave stale clipboard text for complex templates.
            try:
                pythoncom.OleFlushClipboard()
            except Exception:
                # HWP may publish a native clipboard owner without OLE's
                # standard flush implementation; the format check below is
                # the authoritative success condition.
                pass
            native_format = win32clipboard.RegisterClipboardFormat("Hwp Native")
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                if (win32clipboard.GetClipboardSequenceNumber() != clipboard_sequence and
                        win32clipboard.IsClipboardFormatAvailable(native_format)):
                    break
                time.sleep(0.05)
            else:
                raise RuntimeError("Hancom native clipboard format was not published")
        except Exception as exc:
            raise ServiceError("HWP_COPY_FAILED", "한/글에서 표를 열거나 복사하지 못했습니다.") from exc
        return {"copied": True, "format": "hancom-native-table"}
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
        if initialized:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
