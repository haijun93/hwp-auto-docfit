import tempfile
import unittest
from pathlib import Path
from docfit_app.document_tools_service import DocumentToolsService
from docfit_app.api_contract import ServiceError

class DocumentToolsTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.service=DocumentToolsService(self.temp.name)

    def test_outline_saves_with_conflict_protection(self):
        original=self.service.command('outline.load',{})
        saved=self.service.command('outline.save',{'text':'# 첫 항목\n- 둘째','revision':original['revision']})
        self.assertEqual(self.service.command('outline.load',{})['text'],saved['text'])
        with self.assertRaises(ServiceError):
            self.service.command('outline.save',{'text':'stale','revision':original['revision']})
        self.assertEqual(Path(self.temp.name,'outliner_draft.md').read_text(),saved['text'])

    def test_outline_move_toggle_note_and_export_preserve_content(self):
        text='# 첫 항목\n# 둘째 항목'
        moved=self.service.command('outline.move',{'text':text,'index':1,'up':True})
        self.assertEqual(moved['text'],'# 둘째 항목\n# 첫 항목')
        done=self.service.command('outline.toggle',{'text':moved['text'],'index':0})
        self.assertIn('[x]',done['text'])
        memo=self.service.command('outline.note',{'text':done['text'],'index':0,'note':'메모'})
        self.assertIn('메모',self.service.command('outline.export',{'text':memo['text']})['text'])

    def test_paste_and_writing_tools_use_domain_functions(self):
        output=self.service.command('outline',{'text':'&gt; **안녕하세요.**[1]'})['text']
        self.assertNotIn('**',output)
        self.assertNotIn('[1]',output)
        self.assertNotIn('&gt;',output)
        self.assertIn('금',self.service.command('amount',{'text':'1000원'})['text'])
        self.assertNotIn('1234567',self.service.command('mask_rrn',{'text':'900101-1234567'})['text'])

    def test_invalid_input_and_unknown_commands_are_structured(self):
        with self.assertRaises(ServiceError):self.service.command('outline.move',{'text':'a','index':9})
        with self.assertRaises(ServiceError):self.service.command('unknown',{})
        with self.assertRaises(ServiceError):self.service.command('clean',{'text':'가'*400000})

    def test_proofread_requires_selection_preserves_original_and_rejects_changed_source(self):
        from tests.test_fidelity import make_hwpx, SECTION
        from docfit_core.hwpx import inspect_hwpx, to_markdown
        source=Path(self.temp.name)/'source.hwpx'
        make_hwpx(source,SECTION.replace('첫째 문단 9월 계획','금일 안내'))
        before=source.read_bytes()
        review=self.service.command('proofread',{'path':str(source)})
        self.assertTrue(any(item['rule_id']=='public.geumil' for item in review['issues']))
        payload={'path':str(source),'source_sha256':review['source_sha256'],'approved':['public.geumil']}
        applied=self.service.command('proofread_apply',payload)
        self.assertEqual(source.read_bytes(),before)
        self.assertIn('오늘',to_markdown(inspect_hwpx(applied['path'])))
        with self.assertRaises(ServiceError):
            self.service.command('proofread_apply',{**payload,'approved':[]})
        make_hwpx(source,SECTION.replace('첫째 문단 9월 계획','금일 다른 안내'))
        with self.assertRaises(ServiceError) as failure:
            self.service.command('proofread_apply',payload)
        self.assertEqual(failure.exception.code,'DOCUMENT_CHANGED')


class NativeSettingsContractTest(unittest.TestCase):
    def test_native_stage_defaults_and_card_options_survive_restart(self):
        from docfit_app.application_service import ApplicationService
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'settings.json';app=ApplicationService(path)
            app.dispatch('set_stage',['reset_spacing',False])
            app.dispatch('set_stage_default',[True])
            restarted=ApplicationService(path)
            selected={item['key']:item['enabled'] for item in restarted.state()['stages']}
            self.assertFalse(selected['reset_spacing'])
            restarted.dispatch('set_stage',['reset_spacing',True])
            selected={item['key']:item['enabled'] for item in ApplicationService(path).state()['stages']}
            self.assertTrue(selected['reset_spacing'])
            state=restarted.dispatch('set_card_option',['all_include_spacing',False])
            self.assertEqual(state['mode'],'format')
            self.assertFalse(state['include_spacing'])


class AdvancedJobsTest(unittest.TestCase):
    def test_advanced_jobs_are_pollable_scoped_and_do_not_block_rpc(self):
        import threading
        from unittest.mock import patch
        ready=threading.Event();release=threading.Event()
        def work(*args):
            ready.set();release.wait(2)
            return {'path':'result.md','status':'partial'}
        with tempfile.TemporaryDirectory() as folder,patch.object(DocumentToolsService,'advanced',side_effect=work):
            service=DocumentToolsService(folder)
            job=service.command('advanced.start',{'action':'markdown','path':'source.hwpx'})
            self.assertTrue(ready.wait(1))
            self.assertEqual(service.command('advanced.poll',{'id':job['id']})['status'],'running')
            self.assertEqual(service.command('advanced.start',{'action':'markdown','path':'source.hwpx'})['id'],job['id'])
            with self.assertRaises(ServiceError):service.command('advanced.start',{'action':'tables','path':'other.hwpx'})
            release.set()
            import time
            deadline=time.monotonic()+2
            while time.monotonic()<deadline:
                result=service.command('advanced.poll',{'id':job['id']})
                if result['status']!='running':break
                release.wait(.01)
            self.assertEqual(result['status'],'complete')
            self.assertEqual(result['result']['status'],'partial')
