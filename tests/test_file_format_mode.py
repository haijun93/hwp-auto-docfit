"""파일포맷 변경 모드: 세부 작업이 없는 모드에서 KeyError 없이 동작하고 준비 안 된 형식은 시작하지 않는다."""
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from desktop_web_ui import DesktopWebBridge
from tests.gui_support import gui_root


class FileFormatModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {'APPDATA': self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        ns = runpy.run_path(str(Path(__file__).parents[1] / 'hwp-auto-docfit.py'), run_name='file_format_mode_test')
        self.root = gui_root(ns['TkinterDnD'].Tk, ns)
        self.addCleanup(self.root.destroy)
        self.root.withdraw()
        self.root.report_callback_exception = lambda *exc: self.errors.append(exc)
        self.errors = []
        self.app = ns['HwpAutoDocFitGUI'](self.root)
        self.bridge = DesktopWebBridge(self.app)
        self.bridge._tk = lambda callback, **kwargs: callback()
        self.bridge._conversion_prerequisites = lambda: {
            'kordoc': {'available': False, 'reason': 'kordoc 없음'}, 'pandoc': False, 'hwp_com': True}
        documents = []
        for name in ('보고서.hwpx', '취합.hwp'):
            path = Path(self.temp.name) / name
            path.write_bytes(b'not a real document')
            documents.append(str(path))
        self.app.files = documents

    def test_selecting_file_format_mode_has_no_stage_lookup_errors(self):
        self.bridge.set_mode('file_format')
        self.root.update()
        self.assertEqual(self.app.selected_mode.get(), 'file_format')
        self.assertIn('파일 형식', self.app.options_summary.cget('text'))
        # 세부 작업 명령은 이 모드에서 아무것도 하지 않는다.
        self.bridge.stage_config('all', {'enabled': False})
        self.bridge.reset_stages()
        self.bridge.set_stage_default(True)
        self.app._세부작업_열기('file_format')
        state = self.bridge.get_state()
        self.assertEqual(state['stages'], [])
        self.assertEqual(self.errors, [])

    def test_hwp_and_hwpx_offer_pdf_and_images_without_kordoc(self):
        self.bridge.set_mode('file_format')
        targets = {item['format']: item for item in self.bridge.get_state()['conversion_targets']}
        self.assertEqual(set(targets), {'hwpx', 'pdf', 'docx', 'epub', 'jpg', 'png'})
        self.assertTrue(targets['pdf']['enabled'])
        self.assertTrue(targets['jpg']['enabled'] and targets['png']['enabled'])
        self.assertFalse(targets['hwpx']['enabled'])

    def test_disabled_target_is_refused_before_conversion_starts(self):
        self.bridge.set_mode('file_format')
        self.bridge.set_conversion_target('hwpx')
        with patch.object(self.app, '파일포맷_변경_시작') as start:
            with self.assertRaisesRegex(ValueError, 'kordoc 없음'):
                self.bridge.start('file_format')
        start.assert_not_called()
        self.assertFalse(self.app.running)


if __name__ == '__main__':
    unittest.main()
