"""Shared settings changes reach the real Tk fallback without opening a settings window."""
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
from desktop_web_ui import DesktopWebBridge
from tests.gui_support import gui_root

class FlutterSettingsGuiTests(unittest.TestCase):
    def test_service_save_updates_real_gui_and_preserves_other_fields(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'APPDATA':folder}):
            ns=runpy.run_path(str(Path(__file__).parents[1]/'hwp-auto-docfit.py'),run_name='settings_gui_test')
            root=gui_root(ns['TkinterDnD'].Tk,ns)
            root.withdraw()
            try:
                app=ns['HwpAutoDocFitGUI'](root)
                bridge=DesktopWebBridge(app)
                bridge._tk=lambda callback, **kwargs:callback()
                initial=bridge.get_settings()['data']
                with patch.object(app,'설정창_열기',side_effect=AssertionError('No legacy dialog')):
                    result=bridge.save_settings({'retry_body':'9','symbol_fonts.□.size':'18'},initial['revision'])
                self.assertTrue(result['ok'],result)
                self.assertEqual(app.retry_body_var.get(),'9')
                self.assertEqual(app.symbol_font_vars['□']['size'].get(),'18')
                self.assertEqual(ns['설정_불러오기']()['retry_body'],'9')
                self.assertNotEqual(result['data']['revision'],initial['revision'])
            finally:
                root.destroy()
