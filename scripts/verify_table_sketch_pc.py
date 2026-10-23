"""C12: 조직도 복사 → 새 문서 붙여넣기 → 저장 결과를 preview와 대조."""
import json
from pathlib import Path
import runpy
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from defusedxml import ElementTree as ET
from docfit_core.save_guard import com_test_lock
from docfit_core import table_sketch
from docfit_app.table_sketch_service import TableSketchService
from tests.test_table_sketch import organization


def main():
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=True)
    sketch = organization()
    preview = table_sketch.preview(sketch)
    (root/'preview.json').write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding='utf-8')
    table_sketch.to_hwpx(sketch,root/'source.hwpx')
    with com_test_lock('Codex','C12'):
        ns=runpy.run_path(str(Path(__file__).resolve().parents[1]/'hwp-auto-docfit.py'),run_name='sketch_com_test')
        def factory():
            app=ns['한글_COM_인스턴스_생성'](독립=True)
            if not app.RegisterModule(ns['REGISTER_MODULE_NAME'],ns['REGISTER_MODULE_VALUE']):
                app.Quit()
                raise RuntimeError('한/글 보안 모듈 등록 실패')
            app.XHwpWindows.Item(0).Visible=False
            return app
        result=TableSketchService(root,factory).copy(sketch)
        print(json.dumps(result,ensure_ascii=False),flush=True)
        if not result['ok']: raise RuntimeError(result['message'])
        ns['pythoncom'].CoInitialize()
        app=None
        try:
            app=factory()
            if app.Run('Paste') is False: raise RuntimeError('붙여넣기 실패')
            target=root/'pasted.hwpx'
            if app.SaveAs(str(target),'HWPX','') is False: raise RuntimeError('저장 실패')
        finally:
            if app is not None:
                try: app.Clear(1)
                finally: app.Quit()
            ns['pythoncom'].CoUninitialize()
    with zipfile.ZipFile(target) as archive:
        tables=[t for name in archive.namelist() if name.startswith('Contents/section') and name.endswith('.xml')
                for t in ET.fromstring(archive.read(name)).iter(table_sketch.HP+'tbl')]
    assert len(tables)==1, len(tables)
    table=tables[0]
    actual=[]
    for tc in table.findall(table_sketch.HP+'tr/'+table_sketch.HP+'tc'):
        addr,span=tc.find(table_sketch.HP+'cellAddr'),tc.find(table_sketch.HP+'cellSpan')
        actual.append(dict(row=int(addr.get('rowAddr')),col=int(addr.get('colAddr')),
                           rowspan=int(span.get('rowSpan')),colspan=int(span.get('colSpan'))))
    expected=[{k:c[k] for k in ('row','col','rowspan','colspan')} for c in preview['cells']]
    report=dict(ok=actual==expected and int(table.get('rowCnt'))==preview['rows'] and int(table.get('colCnt'))==preview['cols'],
                rows=int(table.get('rowCnt')),cols=int(table.get('colCnt')),cells=len(actual),
                merged_cells=sum(c['rowspan']>1 or c['colspan']>1 for c in actual),output=str(target),actual=actual,expected=expected)
    (root/'com-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('actual','expected')},ensure_ascii=False))
    assert report['ok'], 'preview와 실제 저장 결과의 표 구조 불일치'


if __name__=='__main__': main()
