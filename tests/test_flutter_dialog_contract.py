import copy
import json
import os
from pathlib import Path
import runpy
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from tests.gui_support import gui_root
from desktop_web_ui import DesktopWebBridge
from docfit_core.app_state import AppState


class FlutterProfileContractTest(unittest.TestCase):
    def test_profile_roundtrip_validates_units_conflicts_and_restore(self):
        state=AppState(profiles={'p':{'name':'보고서','element_analysis':{
            'paragraph_groups':[{'role':'본문','marker':'ㅇ','count':1,'elements':{'size':{'value':1500}}}]
        }}})
        saved=[]
        gui=SimpleNamespace(state=state,running=False,_서식_파일_저장=lambda key,value:saved.append(copy.deepcopy(value)),
                            _프로파일_목록갱신=lambda:None,_프로파일_선택=lambda:None)
        bridge=DesktopWebBridge(gui);bridge._tk=lambda callback,**kwargs:callback()
        original=bridge.format_profile('get',{'id':'p'})['data']
        payload={'id':'p','revision':original['revision'],'edits':[{'path':['group',0],'key':'size','value':'16pt'}]}
        edited=bridge.format_profile('save',payload)
        self.assertTrue(edited['ok'],edited)
        self.assertEqual(saved[-1]['element_analysis']['paragraph_groups'][0]['elements']['size']['value'],1600)
        self.assertEqual(bridge.format_profile('save',payload)['error']['code'],'PROFILE_CONFLICT')
        payload['revision']=edited['data']['revision']
        restored=bridge.format_profile('restore',payload)
        self.assertTrue(restored['ok'])
        self.assertEqual(saved[-1]['element_analysis']['paragraph_groups'][0]['elements']['size']['value'],1500)
        json.dumps(restored)


class FlutterDialogContractTest(unittest.TestCase):
    def test_confirmation_uses_hidden_tk_pump_and_json_without_messagebox(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        environment=patch.dict(os.environ,{'APPDATA':temporary.name})
        environment.start();self.addCleanup(environment.stop)
        ns=runpy.run_path(str(Path(__file__).parents[1]/'hwp-auto-docfit.py'),run_name='flutter_dialog_test')
        root=gui_root(ns['TkinterDnD'].Tk,ns);root.withdraw();root._docfit_hidden_backend=True
        app=ns['HwpAutoDocFitGUI'].__new__(ns['HwpAutoDocFitGUI']);app.root=root
        from docfit_ui.scheduler import install_scheduler
        install_scheduler(app)
        bridge=DesktopWebBridge(app);answers=[];errors=[];trace=[]
        def worker():
            try:
                trace.append('worker-start')
                data=bridge.get_pending_dialog()
                trace.append(('read',data))
                json.dumps(data)
                bridge.resolve_dialog(data['id'],True,[],{})
                trace.append('resolved')
            except Exception as exc:errors.append(exc)
        def show():
            try:answers.append(app._알림(ns['messagebox'].askyesno,'확인','계속하시겠습니까?'))
            finally:root.after(0,root.quit)
        def watchdog():
            errors.append(AssertionError('dialog timeout'))
            pending=getattr(app,'_flutter_dialog',None)
            if pending:pending['done'].set(True)
            root.quit()
        with patch.object(ns['messagebox'],'askyesno',side_effect=AssertionError('Tk popup')) as popup:
            root.after(0,show)
            root.after(30,lambda:threading.Thread(target=worker,daemon=True).start())
            timeout=root.after(3000,watchdog)
            try:
                root.mainloop()
                root.after_cancel(timeout)
                popup.assert_not_called()
                self.assertEqual(errors,[],trace)
                self.assertEqual(answers,[True])
            finally:root.destroy()
