"""클립보드 엑셀 표를 HWPX 한/글 표로 복사한다."""
from __future__ import annotations
import tempfile
from pathlib import Path
from docfit_core.excel_table import parse_clipboard
from docfit_core.excel_table_hwpx import to_hwpx
from .native_table_clipboard import copy_hwpx_document

class ExcelTableService:
    def __init__(self, clipboard=None, copier=None):
        self.clipboard = clipboard or _clipboard
        self.copier = copier or copy_hwpx_document

    def command(self, action, payload=None):
        if action not in ('convert', 'paste_clean'): return {'ok':False,'message':'엑셀 표 변환 명령을 확인해 주세요.'}
        try:
            html_data, tsv = self.clipboard()
            model = parse_clipboard(html_data, tsv, clean=not (isinstance(payload,dict) and payload.get('clean') is False))
            # 몽땅클립보드 전용 경로는 셀 음영만 제거하고 표/내용/병합 구조는 그대로 둔다.
            keep_fill = action != 'paste_clean' and not (isinstance(payload,dict) and payload.get('keep_cell_background') is False)
            if not keep_fill:
                for row in model['rows']:
                    for cell in row: cell['fill']=''
            with tempfile.TemporaryDirectory(prefix='docfit_excel_') as d:
                path=to_hwpx(model,Path(d)/'excel-table.hwpx')
                result=self.copier(path)
            return {'ok':True,'rows':model['row_count'],'cols':model['col_count'],'cleaned':model['cleaned'],
                    'message':'한/글에서 Ctrl+V로 붙여넣으세요.'}
        except (ValueError, OSError) as exc: return {'ok':False,'message':str(exc)}

def _clipboard():
    try:
        import win32clipboard
        html_fmt=win32clipboard.RegisterClipboardFormat('HTML Format')
        win32clipboard.OpenClipboard()
        try:
            html_data=win32clipboard.GetClipboardData(html_fmt) if win32clipboard.IsClipboardFormatAvailable(html_fmt) else None
            tsv=win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT) if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT) else None
            return html_data,tsv
        finally: win32clipboard.CloseClipboard()
    except Exception: return None,None
