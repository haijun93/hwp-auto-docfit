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

    def test_paste_and_writing_tools_use_domain_functions(self):
        output=self.service.command('convert',{'text':'&gt; **안녕하세요.**[1]'})['text']
        self.assertNotIn('**',output)
        self.assertNotIn('[1]',output)
        self.assertNotIn('&gt;',output)
        self.assertIn('금',self.service.command('amount',{'text':'1000원'})['text'])
        self.assertNotIn('1234567',self.service.command('mask_rrn',{'text':'900101-1234567'})['text'])

    def test_invalid_input_and_unknown_commands_are_structured(self):
        with self.assertRaises(ServiceError):self.service.command('unknown',{})
        with self.assertRaises(ServiceError):self.service.command('clean',{'text':'가'*400000})


    def test_native_bridge_rejects_removed_tools_and_keeps_text_input(self):
        from docfit_app.application_service import ApplicationService
        app=ApplicationService(Path(self.temp.name)/'settings.json')
        app.dispatch('set_option',['developer_mode',True])
        fields={field['key'] for field in app.configuration.snapshot()['fields']}
        self.assertNotIn('review_document_kind',fields)
        self.assertNotIn('review_reading_purpose',fields)
        self.assertIn('developer_mode',fields)
        for name in ('review','proofread','proofread_apply','numbers','markdown','prompt','prompts',
                     'outline','outline.load','outline.save','outline.export','outline.filter','outline.move',
                     'outline.toggle','outline.note','outline.indent','outline.outdent',
                     'advanced','advanced.start','advanced.poll','writing'):
            with self.subTest(name=name):
                result=app.dispatch('document_tool',[name,{}])
                self.assertFalse(result['ok'])
                self.assertEqual(result['error']['code'],'INVALID_TOOL')
                self.assertIn('지원하지 않는',result['error']['message'])
        converted=app.dispatch('document_tool',['convert',{'text':'# 제목\n- 항목'}])
        self.assertTrue(converted['ok'])
        self.assertNotIn('#',converted['data']['text'])
        added=app.dispatch('document_tool',['add_text',{'text':converted['data']['text']}])
        self.assertTrue(added['ok'])
        path=Path(added['data']['path'])
        self.assertEqual(path.read_text(encoding='utf-8'),converted['data']['text'])
        self.assertIn(str(path),app.data.files)

    def test_remaining_text_transforms(self):
        cases={'clean':'**안내**','labels':'# 제목','amount':'1000원','commas':'10000',
               'weekdays':'2026-10-23','date_diff':'2026-10-23\n2026-10-24',
               'age':'2000-01-01','mask_rrn':'900101-1234567','table_calc':'1\t2\n3\t4'}
        for name,text in cases.items():
            with self.subTest(name=name):
                self.assertIsInstance(self.service.command(name,{'text':text})['text'],str)


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
