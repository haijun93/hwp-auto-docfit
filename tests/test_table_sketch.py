"""표그림판: 기하 구조·HWPX·저장·브리지 계약 회귀 시험."""
import copy
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
