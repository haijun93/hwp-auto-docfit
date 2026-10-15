import json
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


class AppSettingsWriterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.write = staticmethod(runpy.run_path(str(Path(__file__).parents[1] / 'hwp-auto-docfit.py'))['설정_저장'])

    def test_writer_preserves_other_fields_and_failed_replace_preserves_bytes(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            path.write_text('{"abbreviations":{"a":{"type":"text","value":"b"}},"custom":42}', encoding='utf-8')
            with patch.dict(self.write.__globals__, {'설정_파일_경로': lambda: path}):
                self.assertTrue(self.write({'log_file': True}))
                self.assertEqual(json.loads(path.read_text())['custom'], 42)
                self.assertIn('a', json.loads(path.read_text())['abbreviations'])
                saved = path.read_bytes()
                with patch('docfit_app.settings_service.os.replace', side_effect=OSError('disk failure')):
                    self.assertFalse(self.write({'log_file': False}))
                self.assertEqual(path.read_bytes(), saved)
