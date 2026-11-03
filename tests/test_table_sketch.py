"""표그림판: 기하 구조·HWPX·저장·브리지 계약 회귀 시험."""
import copy
import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from defusedxml import ElementTree as ET
from docfit_core import table_sketch as ts
from docfit_app.table_sketch_service import TableSketchService, COM_LOCK, validate_name


def line(x1,y1,x2,y2,**kw):
    return dict(x1=x1,y1=y1,x2=x2,y2=y2,**kw)


def box(x1,y1,x2,y2):
    return [line(x1,y1,x2,y1),line(x1,y2,x2,y2),line(x1,y1,x1,y2),line(x2,y1,x2,y2)]


def drawing(lines=None,texts=None):
    return dict(grid=dict(cols=36,rows=50,cell_mm=5.0),lines=lines or [],texts=texts or [])


def organization():
    return drawing(box(4,0,8,2)+box(0,6,3,8)+box(4,6,8,8)+box(9,6,12,8)+
                   [line(6,2,6,4),line(1,4,10,4),line(1,4,1,6),line(6,4,6,6),line(10,4,10,6)],
                   [dict(x=5,y=1,text="총괄팀",bold=True),dict(x=0,y=6,text="1팀"),
                    dict(x=5,y=6,text="2팀"),dict(x=10,y=6,text="3팀")])


class GeometryTests(unittest.TestCase):
    def test_rectangle(self):
        result=ts.preview(drawing(box(2,3,10,8)))
        self.assertEqual((result['rows'],result['cols'],len(result['cells'])),(1,1,1))
        self.assertEqual((result['width_mm'],result['height_mm']),(40,25))
        self.assertEqual(set(result['cells'][0]['borders'].values()),{'thin'})

    def test_two_by_two(self):
        result=ts.preview(drawing(box(0,0,4,4)+[line(2,0,2,4),line(0,2,4,2)]))
        self.assertEqual((result['rows'],result['cols'],len(result['cells'])),(2,2,4))
        self.assertTrue(all(c['rowspan']==c['colspan']==1 for c in result['cells']))

    def test_organization(self):
        result=ts.preview(organization())
        self.assertEqual((result['rows'],result['cols']),(4,8))
        self.assertEqual(len(result['cells']),28)
        filled=[c for c in result['cells'] if c['text']]
        self.assertEqual(len(filled),4)
        self.assertTrue(any(c['colspan']>1 for c in filled))
        self.assertTrue(any(set(c['borders'].values())=={'none'} for c in result['cells']))
        self.assertEqual(sum(c['rowspan']*c['colspan'] for c in result['cells']),32)

    def test_partial_boundary_and_dangling_edge(self):
        result=ts.preview(drawing(box(0,0,4,4)+[line(0,2,2,2)]))
        self.assertEqual(result['x_coords'],[0,2,4])
        self.assertEqual(result['y_coords'],[0,2,4])
        self.assertEqual(len(result['cells']),4)
        cells={(c['row'],c['col']):c for c in result['cells']}
        self.assertEqual(cells[0,0]['borders']['bottom'],'thin')
        self.assertEqual(cells[0,1]['borders']['bottom'],'none')

    def test_rectangular_region_merges_vertically(self):
        # 오른쪽만 가로로 나눈 표: 왼쪽은 2행 병합.
        result=ts.preview(drawing(box(0,0,4,4)+[line(2,0,2,4),line(2,2,4,2)]))
        self.assertEqual(len(result['cells']),3)
        self.assertEqual((result['cells'][0]['rowspan'],result['cells'][0]['colspan']),(2,1))

    def test_mixed_boundary_styles_remain_separate(self):
        result=ts.preview(drawing(box(0,0,4,4)+[line(0,0,2,0,width='thick',style='dash')]))
        self.assertEqual(len(result['cells']),2)
        self.assertEqual(result['cells'][0]['borders']['top'],'thick')
        self.assertEqual(result['cells'][0]['border_styles']['top'],'dash')
        self.assertEqual(result['cells'][1]['borders']['top'],'thin')

    def test_diagonal_corners_and_cross(self):
        for lines,expected in (([line(0,0,4,4)],'backslash'),([line(0,4,4,0)],'slash'),
                               ([line(0,0,4,4),line(0,4,4,0)],'cross')):
            result=ts.preview(drawing(box(0,0,4,4)+lines))
            self.assertEqual(len(result['cells']),1)
            self.assertEqual(result['cells'][0]['diagonal'],expected)

    def test_partial_diagonal_splits_into_paper_units(self):
        result=ts.preview(drawing(box(0,0,5,4)+[line(1,0,4,3)]))
        diag=[c for c in result['cells'] if c['diagonal']!='none']
        self.assertEqual(len(diag),3)
        self.assertTrue(all(c['colspan']==c['rowspan']==1 for c in diag))
        self.assertTrue(all(c['diagonal']=='backslash' for c in diag))

    def test_second_diagonal_does_not_erase_original_corner_diagonal(self):
        result=ts.preview(drawing(box(0,0,4,4)+[line(0,0,4,4),line(1,0,4,3)]))
        xs,ys=result['x_coords'],result['y_coords']
        diagonal_cells=[c for c in result['cells'] if c['diagonal']=='backslash']
        length=sum(xs[c['col']+c['colspan']]-xs[c['col']] for c in diagonal_cells)
        self.assertEqual(length,7)

    def test_overlapping_and_joining(self):
        clean,warnings=ts.normalize(drawing([line(5,0,2,0),line(0,0,3,0),line(5,0,7,0)]))
        self.assertEqual(clean['lines'],[line(0,0,7,0,width='thin',style='solid')])
        self.assertFalse(warnings)
        result=ts.preview(drawing(box(0,0,4,4)+[line(0,0,4,4,width='double'),line(0,0,4,4,width='thin')]))
        self.assertEqual(result['cells'][0]['diagonal_styles']['backslash'],('double','solid'))

    def test_bad_lines_and_texts_warn(self):
        invalid=[line(1,1,1,1),line(-1,0,2,0),line(0,0,3,2),line(0.5,0,1,0),None,line(0,0,1,0,style='bad')]
        result=ts.preview(drawing(box(0,0,2,2)+invalid,[dict(x=100,y=0,text='bad')]))
        self.assertEqual(len(result['warnings']),7)
        self.assertEqual(len(result['cells']),1)

    def test_text_maps_to_merged_cell_and_input_is_unchanged(self):
        sketch=drawing(box(2,3,10,8),[dict(x=3,y=4,text='총괄팀',bold=True,align='right'),dict(x=6,y=5,text='지원')])
        before=copy.deepcopy(sketch)
        result=ts.preview(sketch)
        self.assertEqual(result['cells'][0]['text'],'총괄팀\n지원')
        self.assertEqual(sketch,before)

    def test_empty_and_invalid_grid(self):
        self.assertEqual(ts.preview(drawing())['rows'],0)
        for mm in (0,float('inf'),True):
            value=drawing(); value['grid']['cell_mm']=mm
            with self.assertRaises(ValueError): ts.preview(value)


class TestPrecisionEraserTableLayout(unittest.TestCase):
    """실제 Dart 모델의 삭제 결과를 Python 레이아웃에 연결한다."""

    @classmethod
    def setUpClass(cls):
        dart = shutil.which('dart')
        if not dart:
            raise unittest.SkipTest('정밀 지우개 모델 시험에는 Dart SDK가 필요합니다.')
        # Flutter의 dart.bat 대신 SDK 실행 파일을 직접 호출한다.
        sdk = Path(dart).parent / 'cache/dart-sdk/bin/dart.exe'
        cls.dart = str(sdk) if sdk.exists() else dart

    def erase(self, lines, segment):
        model = (Path(__file__).resolve().parents[1] /
                 'flutter_ui/lib/features/table_sketch/table_sketch_models.dart')
        source = f"""import 'dart:convert';
import '{model.as_uri()}';
void main(List<String> args) {{
  final doc = TableSketchDoc.fromJson(jsonDecode(args[0]));
  final s = (jsonDecode(args[1]) as List).cast<int>();
  final changed = doc.eraseUnitSegment(s[0], s[1], s[2], s[3]);
  print(jsonEncode({{'changed': changed, 'doc': doc.toJson(forTable: true)}}));
}}
"""
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / 'erase.dart'
            script.write_text(source, encoding='utf-8')
            result = subprocess.run(
                [self.dart, str(script), json.dumps(drawing(lines)), json.dumps(segment)],
                capture_output=True, text=True, encoding='utf-8', timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        erased = json.loads(result.stdout)
        self.assertTrue(erased['changed'])
        return erased['doc']

    def test_split_middle_segment_creates_two_lines(self):
        result = self.erase([line(0,0,3,0,width='thick',style='dash')], [1,0,2,0])
        self.assertEqual(result['lines'], [
            line(0,0,1,0,width='thick',style='dash'),
            line(2,0,3,0,width='thick',style='dash')])

    def test_erase_inner_h_segment_merges_cells(self):
        result = ts._layout(self.erase(
            box(0,0,2,2)+[line(0,1,2,1),line(1,0,1,2)], [0,1,1,1]))
        cells = {(c['row'],c['col']):(c['rowspan'],c['colspan']) for c in result['cells']}
        self.assertEqual(cells, {(0,0):(2,1), (0,1):(1,1), (1,1):(1,1)})

    def test_erase_inner_v_segment_merges_cells(self):
        result = ts._layout(self.erase(
            box(0,0,2,2)+[line(0,1,2,1),line(1,0,1,2)], [1,0,1,1]))
        cells = {(c['row'],c['col']):(c['rowspan'],c['colspan']) for c in result['cells']}
        self.assertEqual(cells, {(0,0):(1,2), (1,0):(1,1), (1,1):(1,1)})

    def test_erase_diagonal_segment(self):
        result = self.erase([line(0,0,3,3)], [1,1,2,2])
        self.assertEqual(result['lines'], [
            line(0,0,1,1,width='thin',style='solid'),
            line(2,2,3,3,width='thin',style='solid')])


class ExportTests(unittest.TestCase):
    def test_hwpx_structure_dimensions_borders_and_text(self):
        sketch=organization()
        sketch['lines'][0].update(width='double',style='dash')
        sketch['lines'][1].update(width='thick',style='dot')
        expected=ts.preview(sketch)
        with tempfile.TemporaryDirectory() as folder:
            path=ts.to_hwpx(sketch,Path(folder)/'out.hwpx')
            with zipfile.ZipFile(path) as archive:
                roots={name:ET.fromstring(archive.read(name)) for name in archive.namelist() if name.endswith('.xml')}
            tables=[t for name,root in roots.items() if name.startswith('Contents/section') for t in root.iter(ts.HP+'tbl')]
            self.assertEqual(len(tables),1)
            table=tables[0]
            self.assertEqual((int(table.get('rowCnt')),int(table.get('colCnt'))),(expected['rows'],expected['cols']))
            actual=table.findall(ts.HP+'tr/'+ts.HP+'tc')
            self.assertEqual(len(actual),len(expected['cells']))
            fills={n.get('id'):n for n in roots['Contents/header.xml'].iter(ts.HH+'borderFill')}
            for cell,meta in zip(actual,expected['cells']):
                span=cell.find(ts.HP+'cellSpan')
                self.assertEqual((int(span.get('rowSpan')),int(span.get('colSpan'))),(meta['rowspan'],meta['colspan']))
                fill=fills[cell.get('borderFillIDRef')]
                for side,width in meta['borders'].items():
                    edge=fill.find(ts.HH+side+'Border')
                    self.assertEqual(edge.get('type')=='NONE',width=='none')
                    if width=='double': self.assertEqual((edge.get('type'),edge.get('width')),('DOUBLE_SLIM','0.5 mm'))
                    if width=='thick': self.assertEqual((edge.get('type'),edge.get('width')),('DOT','0.4 mm'))
                self.assertEqual(cell.find(ts.HP+'cellMargin').get('left'),'142')
            self.assertEqual(int(table.find(ts.HP+'sz').get('width')),round(expected['width_mm']*ts.UNIT_MM))
            self.assertIn('총괄팀',''.join(t.text or '' for t in table.iter(ts.HP+'t')))

    def test_diagonal_border_fill(self):
        with tempfile.TemporaryDirectory() as folder:
            path=ts.to_hwpx(drawing(box(0,0,4,4)+[line(0,4,4,0),line(0,0,4,4)]),Path(folder)/'diag.hwpx')
            with zipfile.ZipFile(path) as archive:
                head=ET.fromstring(archive.read('Contents/header.xml'))
            self.assertTrue(any(n.find(ts.HH+'slash').get('type')=='CENTER' and n.find(ts.HH+'backSlash').get('type')=='CENTER' for n in head.iter(ts.HH+'borderFill')))

    def test_vertical_merge_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path=ts.to_hwpx(drawing(box(0,0,4,4)+[line(2,0,2,4),line(2,2,4,2)]),Path(folder)/'span.hwpx')
            with zipfile.ZipFile(path) as archive:
                root=ET.fromstring(archive.read('Contents/section0.xml'))
            spans=list(root.iter(ts.HP+'cellSpan'))
            self.assertEqual([(n.get('rowSpan'),n.get('colSpan')) for n in spans],[('2','1'),('1','1'),('1','1')])


class ServiceTests(unittest.TestCase):
    def test_names_and_storage(self):
        with tempfile.TemporaryDirectory() as folder:
            service=TableSketchService(folder)
            for name in ('','../escape','a/b','a\\b','a:b','CON','aux.json','x'*61,'a.',' x','x\x00'):
                with self.assertRaises(ValueError): validate_name(name)
                self.assertFalse(service.command('load',name)['ok'])
            sketch=organization()
            self.assertTrue(service.command('save',dict(name='조직도',sketch=sketch))['ok'])
            self.assertEqual(service.command('list')['sketches'],['조직도'])
            self.assertEqual(service.command('load','조직도')['sketch'],sketch)
            self.assertTrue(service.command('delete','조직도')['ok'])
            self.assertFalse(service.command('load','조직도')['ok'])

    def test_copy_selection_cleanup_and_clipboard_failure(self):
        log=[]
        class App:
            HeadCtrl=SimpleNamespace(CtrlID='tbl',Next=None,GetAnchorPos=lambda n:'anchor')
            def Open(self,path,*args): self.path=Path(path); return self.path.exists()
            def SetPosBySet(self,pos): log.append(pos)
            def FindCtrl(self): log.append('select')
            def Run(self,action): log.append(action)
            def Clear(self,n): log.append('clear')
            def Quit(self): log.append('quit')
        app=App()
        with tempfile.TemporaryDirectory() as folder:
            service=TableSketchService(folder,lambda:app,clipboard_formats=lambda:['Hwp Native'],activator=lambda:log.append('activate'))
            self.assertTrue(service.copy(drawing(box(0,0,4,4)))['ok'])
            self.assertEqual(log,['anchor','select','Copy','clear','quit','activate'])
            self.assertFalse(app.path.exists())
            service.hwp._clipboard_formats=lambda:[]
            self.assertFalse(service.copy(drawing(box(0,0,4,4)))['ok'])
            COM_LOCK.acquire()
            try: self.assertFalse(service.copy(drawing(box(0,0,4,4)))['ok'])
            finally: COM_LOCK.release()

    def test_bridge_exposes_direct_contract_and_rejects_busy_copy(self):
        from desktop_web_ui import DesktopWebBridge, _BrowserApi
        with tempfile.TemporaryDirectory() as folder:
            gui=SimpleNamespace(running=False)
            setattr(gui,'_준말_서비스',lambda:SimpleNamespace(settings=SimpleNamespace(_path=Path(folder)/'settings.json')))
            bridge=object.__new__(DesktopWebBridge)
            bridge.gui=gui
            bridge._tk=lambda action,**kw:action()
            self.assertTrue(bridge.table_sketch('preview',drawing(box(0,0,4,4)))['ok'])
            gui.running=True
            self.assertFalse(bridge.table_sketch('copy',drawing(box(0,0,4,4)))['ok'])

    def test_native_dispatch_optional_payload_and_unavailable_com(self):
        from docfit_app.application_service import ApplicationService
        with tempfile.TemporaryDirectory() as folder:
            app=ApplicationService(Path(folder)/'settings.json')
            self.assertEqual(app.dispatch('table_sketch',['list']),dict(ok=True,sketches=[]))
            self.assertTrue(app.dispatch('table_sketch',['preview',organization()])['ok'])
            self.assertFalse(app.dispatch('table_sketch',['copy',organization()])['ok'])


if __name__=='__main__': unittest.main()


class SketchColorTests(unittest.TestCase):
    """2.0.7: 선 색·사각형 배경색이 한/글 표 테두리 색·칸 배경색으로."""

    def test_line_color_and_fill_reach_hwpx(self):
        import tempfile, zipfile
        from pathlib import Path
        from docfit_core import table_sketch
        sketch = {"grid": {"cols": 20, "rows": 20, "cell_mm": 5.0}, "lines": [
            {"x1": 1, "y1": 1, "x2": 9, "y2": 1, "color": "#dc2626"}, {"x1": 1, "y1": 4, "x2": 9, "y2": 4},
            {"x1": 1, "y1": 1, "x2": 1, "y2": 4}, {"x1": 9, "y1": 1, "x2": 9, "y2": 4}],
            "texts": [], "fills": [{"x1": 1, "y1": 1, "x2": 9, "y2": 4, "color": "#DBEAFE"}]}
        view = table_sketch.preview(sketch)
        cell = view["cells"][0]
        self.assertEqual(cell["border_colors"]["top"], "#DC2626")
        self.assertEqual(cell["border_colors"]["bottom"], "#000000")
        self.assertEqual(cell["fill"], "#DBEAFE")
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "t.hwpx"
            table_sketch.to_hwpx(sketch, out)
            with zipfile.ZipFile(out) as archive:
                header = archive.read("Contents/header.xml").decode("utf-8")
        self.assertIn('color="#DC2626"', header)
        self.assertIn('faceColor="#DBEAFE"', header)

    def test_bad_colors_are_rejected_or_dropped(self):
        from docfit_core import table_sketch
        clean, warnings = table_sketch.normalize({"grid": {"cols": 5, "rows": 5}, "lines": [
            {"x1": 0, "y1": 0, "x2": 3, "y2": 0, "color": "red"}], "texts": [],
            "fills": [{"x1": 0, "y1": 0, "x2": 9, "y2": 1, "color": "#FFFFFF"}]})
        self.assertEqual(clean["lines"], [])
        self.assertEqual(clean["fills"], [])
        self.assertEqual(len(warnings), 2)


class ArrowExportTests(unittest.TestCase):
    def test_arrows_are_single_floating_connect_line_objects(self):
        sketch=drawing(box(0,0,8,4))
        sketch['arrows']=[dict(x1=1,y1=2,x2=6,y2=2,width='thick',style='dash',color='#DC2626')]
        result=ts.preview(sketch)
        self.assertFalse(any(t.get('arrow') for c in result['cells'] for t in c['texts']))
        with tempfile.TemporaryDirectory() as folder:
            path=ts.to_hwpx(sketch,Path(folder)/'arrow.hwpx')
            with zipfile.ZipFile(path) as archive:
                root=ET.fromstring(archive.read('Contents/section0.xml'))
            arrows=list(root.iter(ts.HP+'connectLine'))
            self.assertEqual(len(arrows),1)
            self.assertEqual(arrows[0].find(ts.HP+'lineShape').get('color'),'#DC2626')
            self.assertEqual(arrows[0].find(ts.HP+'lineShape').get('tailStyle'),'ARROW')
            self.assertEqual(len(list(root.iter(ts.HP+'lineShape'))),1)
            self.assertFalse(any(n.get('id','').startswith('300000') for n in root.iter(ts.HP+'lineShape')))
            self.assertEqual(arrows[0].find(ts.HP+'pos').get('vertRelTo'),'PARA')
            self.assertEqual(arrows[0].find(ts.HP+'pos').get('horzRelTo'),'PARA')

    def _export_xml(self, sketch):
        with tempfile.TemporaryDirectory() as folder:
            path = ts.to_hwpx(sketch, Path(folder) / 'test.hwpx')
            with zipfile.ZipFile(path) as archive:
                return ET.fromstring(archive.read('Contents/section0.xml'))

    def test_arrow_uses_first_empty_cell_and_preserves_text_cell_alignment(self):
        # 2열 표: 첫 칸에 텍스트, 둘째 칸은 빈 칸, 화살표는 둘째 칸에 위치
        sketch = drawing(box(0, 0, 8, 4) + [line(4, 0, 4, 4)],
                         texts=[dict(x=1, y=2, text="첫 칸 글")])
        sketch['arrows'] = [dict(x1=5, y1=2, x2=7, y2=2)]
        root = self._export_xml(sketch)
        tbl = root.find('.//' + ts.HP + 'tbl')
        cells = tbl.findall(ts.HP + 'tr/' + ts.HP + 'tc')
        self.assertEqual(len(cells), 2)

        # 첫 칸: CENTER 정렬 및 텍스트 원문 유지, 화살표 없음
        sub0 = cells[0].find(ts.HP + 'subList')
        self.assertEqual(sub0.get('vertAlign'), 'CENTER')
        t0 = cells[0].find('.//' + ts.HP + 't')
        self.assertEqual(t0.text, "첫 칸 글")
        self.assertEqual(len(cells[0].findall('.//' + ts.HP + 'connectLine')), 0)

        # 둘째 칸(빈 칸): 화살표 고정 칸이 되어 TOP 정렬, 화살표가 첫 문단 run 안에 위치
        sub1 = cells[1].find(ts.HP + 'subList')
        self.assertEqual(sub1.get('vertAlign'), 'TOP')
        t1 = cells[1].find('.//' + ts.HP + 't')
        self.assertEqual(t1.text or "", "")
        p1 = sub1.find(ts.HP + 'p')
        arrow_run = p1.find(ts.HP + 'run')
        self.assertIsNotNone(arrow_run.find(ts.HP + 'connectLine'))
        self.assertEqual(len(cells[1].findall('.//' + ts.HP + 'connectLine')), 1)

        # 둘째 칸 시작 좌표 ux[1] > 0 검증
        preview = ts.preview(sketch)
        xs = preview['x_coords']
        mm = sketch['grid']['cell_mm']
        ux = [round((x - xs[0]) * mm * ts.UNIT_MM) for x in xs]
        self.assertGreater(ux[1], 0)

    def test_arrow_anchor_offsets_subtract_anchor_cell_origin(self):
        # 첫 칸에 텍스트가 있고 둘째 칸(빈 칸)에 화살표가 고정되는 2열 표
        sketch = drawing(box(0, 0, 4, 4) + [line(2, 0, 2, 4)],
                         texts=[dict(x=1, y=2, text="칸1")])
        sketch['arrows'] = [dict(x1=3, y1=1, x2=5, y2=1)]
        preview = ts.preview(sketch)
        xs, ys = preview["x_coords"], preview["y_coords"]
        cell_mm = sketch["grid"]["cell_mm"]
        ux = [round((x - xs[0]) * cell_mm * ts.UNIT_MM) for x in xs]
        uy = [round((y - ys[0]) * cell_mm * ts.UNIT_MM) for y in ys]
        margin = round(0.5 * ts.UNIT_MM)
        anchor_col = 1
        anchor_row = 0

        root = self._export_xml(sketch)
        arrow = root.find('.//' + ts.HP + 'connectLine')
        pos = arrow.find(ts.HP + 'pos')

        expected_horz = round((3 - xs[0]) * cell_mm * ts.UNIT_MM) - margin - ux[anchor_col]
        expected_vert = round((1 - ys[0]) * cell_mm * ts.UNIT_MM) - margin - uy[anchor_row]
        self.assertEqual(int(pos.get("horzOffset")), expected_horz)
        self.assertEqual(int(pos.get("vertOffset")), expected_vert)
        self.assertGreater(ux[anchor_col], 0)

        # 원래 표 원점 기준 좌표로 환산 복원 검증
        restored_horz = int(pos.get("horzOffset")) + margin + ux[anchor_col]
        restored_vert = int(pos.get("vertOffset")) + margin + uy[anchor_row]
        orig_horz = round((3 - xs[0]) * cell_mm * ts.UNIT_MM)
        orig_vert = round((1 - ys[0]) * cell_mm * ts.UNIT_MM)
        self.assertEqual(restored_horz, orig_horz)
        self.assertEqual(restored_vert, orig_vert)

    def test_arrow_falls_back_to_first_cell_when_all_cells_have_text(self):
        # 2열의 모든 칸에 텍스트가 있을 때 화살표는 첫 칸으로 fallback
        sketch = drawing(box(0, 0, 8, 4) + [line(4, 0, 4, 4)],
                         texts=[dict(x=1, y=2, text="칸1"), dict(x=5, y=2, text="칸2")])
        sketch['arrows'] = [dict(x1=2, y1=2, x2=6, y2=2)]
        preview = ts.preview(sketch)
        xs, ys = preview["x_coords"], preview["y_coords"]
        cell_mm = sketch["grid"]["cell_mm"]
        margin = round(0.5 * ts.UNIT_MM)

        root = self._export_xml(sketch)
        tbl = root.find('.//' + ts.HP + 'tbl')
        cells = tbl.findall(ts.HP + 'tr/' + ts.HP + 'tc')
        self.assertEqual(len(cells), 2)

        # 첫 셀 subList가 TOP, 화살표가 첫 셀 첫 문단에 위치
        sub0 = cells[0].find(ts.HP + 'subList')
        self.assertEqual(sub0.get('vertAlign'), 'TOP')
        p0 = sub0.find(ts.HP + 'p')
        arrow_run = p0.find(ts.HP + 'run')
        self.assertIsNotNone(arrow_run.find(ts.HP + 'connectLine'))
        self.assertEqual(len(cells[0].findall('.//' + ts.HP + 'connectLine')), 1)

        # 둘째 셀은 CENTER 유지, 화살표 없음
        sub1 = cells[1].find(ts.HP + 'subList')
        self.assertEqual(sub1.get('vertAlign'), 'CENTER')
        self.assertEqual(len(cells[1].findall('.//' + ts.HP + 'connectLine')), 0)

        # 첫 셀 고정 fallback에서 기존 오프셋(원래 표 기준 값 - margin) 유지 검증
        arrow = root.find('.//' + ts.HP + 'connectLine')
        pos = arrow.find(ts.HP + 'pos')
        expected_horz = round((2 - xs[0]) * cell_mm * ts.UNIT_MM) - margin
        expected_vert = round((2 - ys[0]) * cell_mm * ts.UNIT_MM) - margin
        self.assertEqual(int(pos.get("horzOffset")), expected_horz)
        self.assertEqual(int(pos.get("vertOffset")), expected_vert)
