import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from docfit_app.configuration_service import ConfigurationService, fields
from docfit_app.settings_service import SettingsService
from docfit_app.api_contract import ServiceError


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'settings.json'
        self.store=SettingsService(self.path);self.service=ConfigurationService(self.store)

    def test_all_visible_fields_are_labeled_and_roundtrip(self):
        snapshot=self.service.snapshot()
        self.assertGreater(len(fields()),70)
        self.assertTrue(all(field['label'] for field in fields()))
        result=self.service.save({'retry_body':'7','symbol_fonts.□.size':'18','developer_mode':True},snapshot['revision'])
        self.assertEqual(result['values']['retry_body'],'7')
        self.assertEqual(self.store.read()['symbol_fonts']['□']['size'],'18')
        self.assertEqual(result['values']['symbol_fonts.□.font'],'HY견고딕')
        self.assertFalse(snapshot['values']['diagram_editor_enabled'])
        self.service.save({'diagram_editor_enabled':True},self.service.snapshot()['revision'])
        self.assertTrue(self.service.snapshot()['values']['diagram_editor_enabled'])

    def test_other_settings_preserved_and_stale_draft_rejected(self):
        self.store.update(lambda data:data.update({'custom':42,'abbreviations':{'요약':{'type':'text','value':'문구'}}}))
        snapshot=self.service.snapshot()
        self.store.update(lambda data:data.update({'log_file':True}))
        with self.assertRaises(ServiceError): self.service.save({'retry_body':'9'},snapshot['revision'])
        self.service.save({'retry_body':'9'},self.service.snapshot()['revision'])
        self.assertEqual(self.store.read()['custom'],42)
        self.assertIn('요약',self.store.read()['abbreviations'])

    def test_validation_and_job_guard_do_not_write(self):
        snapshot=self.service.snapshot()
        for values in ({'retry_body':'NaN'},{'retry_body':'1.2'},{'linespacing_min':'300','linespacing_max':'200'},
                       {'developer_mode':'true'},{'arbitrary':True}):
            with self.subTest(values=values), self.assertRaises(ServiceError):
                self.service.save(values,snapshot['revision'])
        with self.assertRaises(ServiceError): self.service.save({'retry_body':'9'},snapshot['revision'],running=True)
        self.assertFalse(self.path.exists())

    def test_existing_migrations_preserve_explicit_new_choice(self):
        self.store.update(lambda data:data.update({'report_files_rev':1,'log_file':True,
                          'label_symbols_rev':1,'label_symbols':{'*':True},'custom':42}))
        snapshot=self.service.snapshot()
        self.assertFalse(snapshot['values']['log_file'])
        self.assertFalse(snapshot['values']['label_symbols.*'])
        self.service.save({'log_file':True},snapshot['revision'])
        self.assertEqual(self.store.read()['report_files_rev'],2)
        self.assertTrue(self.service.snapshot()['values']['log_file'])
        self.assertEqual(self.store.read()['custom'],42)
