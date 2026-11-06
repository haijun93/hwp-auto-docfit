"""클립보드 엑셀 표를 HWPX 한/글 표로 복사한다."""
from __future__ import annotations
import tempfile
from pathlib import Path
from docfit_core.excel_table import parse_clipboard
from docfit_core.excel_table_hwpx import to_hwpx
from docfit_core.excel_html_shading import strip_cell_shading_report
from .native_table_clipboard import copy_hwpx_document

class ExcelTableService:
    def __init__(self, clipboard=None, copier=None, html_writer=None):
        self.clipboard = clipboard or _clipboard
        self.copier = copier or copy_hwpx_document
        self.html_writer = html_writer or _write_html

    def command(self, action, payload=None):
        if action == 'strip_shading': return self._strip_shading()
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

    def _strip_shading(self):
        """클립보드의 엑셀 HTML에서 셀 배경만 지워 같은 클립보드에 다시 넣는다. 바꿀 것이 없거나 실패하면 클립보드를 건드리지 않는다."""
        html_data, tsv = self.clipboard()
        if not html_data:
            return {'ok':False,'message':'클립보드에서 엑셀 표를 찾지 못했습니다. 엑셀에서 셀을 복사한 뒤 다시 눌러 주세요.'}
        html, report = strip_cell_shading_report(html_data)
        if not report['changed']:
            return {'ok':True,'removed':0,'message':'지울 셀 배경이 없어 클립보드를 그대로 두었습니다.' if not report['reason'] or report['reason']=='지울 음영 없음' else '표를 안전하게 바꿀 수 없어 클립보드를 그대로 두었습니다. ('+report['reason']+')'}
        try: self.html_writer(html, tsv)
        except Exception as exc: return {'ok':False,'message':'클립보드에 쓰지 못했습니다: '+str(exc)}
        return {'ok':True,'removed':report['removed'],'message':'셀 배경을 지웠습니다. 한/글에서 Ctrl+V로 붙여넣으세요.'}

def _write_html(html, tsv):
    import win32clipboard
    data = html if isinstance(html, bytes) else html.encode('utf-8')
    fmt = win32clipboard.RegisterClipboardFormat('HTML Format')
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(fmt, data)
        if tsv: win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, tsv)
    finally: win32clipboard.CloseClipboard()

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
