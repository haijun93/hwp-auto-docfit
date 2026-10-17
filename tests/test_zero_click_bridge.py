import json
import copy
import os
import runpy
import time
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests.test_desktop_browser_api import _FakeGui, _Var, _bridge


class ZeroClickBridgeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name)/'초안.md'
        self.path.write_text('# 추진 계획\nㅇ 내용', encoding='utf-8')
        self.gui = _FakeGui()
        self.gui.로그표시 = Mock()
        self.gui.파일추가 = lambda p: self.gui.files.append(p) or True
        self.gui.목록지우기 = self.gui.files.clear
        self.gui.작업시작 = Mock(side_effect=lambda mode: setattr(self.gui, 'running', True))
        self.bridge = _bridge(self.gui)

    def drop(self):
        return self.bridge.add_paths([str(self.path)], from_drop=True)

    def test_route_manual_override_and_clear_reactivation(self):
        self.assertEqual(self.drop()['mode'], 'all')
        self.bridge.set_mode('spacing')
        self.bridge.add_paths([str(self.path)])
        self.assertEqual(self.gui.selected_mode.get(), 'spacing')
        self.assertTrue(self.bridge.get_state()['user_overrode_mode'])
        self.bridge.clear_files()
        self.assertFalse(self.bridge.get_state()['user_overrode_mode'])
        self.assertEqual(self.drop()['mode'], 'all')

    def test_file_drop_and_legacy_execution_token_never_start_work(self):
        state = self.drop()
        self.assertFalse(state['zero_click']['pending'])
        self.assertFalse(state['instant_run_on_drop'])
        self.bridge.start_zero_click('old-token')
        self.bridge.start_zero_click('legacy-token')
        self.gui.작업시작.assert_not_called()
        json.dumps(state)

    def test_manual_edits_and_repeated_drop_remain_manual(self):
        for edit in (lambda: self.bridge.cancel_zero_click(), lambda: self.bridge.set_mode('spacing'),
                     lambda: self.bridge.set_option('verify', True), lambda: self.bridge.add_paths([str(self.path)], from_drop=True)):
            self.gui.files.clear()
            self.assertFalse(self.drop()['zero_click']['pending'])
            edit()
            self.bridge.start_zero_click('legacy-token')
            self.gui.작업시작.assert_not_called()
        self.gui.files.clear()
        self.assertFalse(self.drop()['zero_click']['pending'])

    def test_multidrop_and_picker_add_are_manual(self):
        state = self.bridge.add_paths([str(self.path), str(self.path)], from_drop=True)
        self.assertFalse(state['zero_click']['pending'])
        self.gui.files.clear()
        self.assertFalse(self.bridge.add_paths([str(self.path)])['zero_click']['pending'])

    def test_legacy_token_or_active_profile_analysis_cannot_start(self):
        self.assertFalse(self.drop()['zero_click']['pending'])
        self.bridge.start_zero_click('legacy-token')
        self.gui.작업시작.assert_not_called()
        self.gui.files.clear()
        self.gui._서식분석중 = True
        self.assertFalse(self.drop()['zero_click']['pending'])
        self.gui._서식분석중 = False
        self.gui.files.clear()
        self.bridge.set_drop_target('manual_documents')
        self.assertFalse(self.bridge.receive_drop([str(self.path)])['zero_click']['pending'])

    def test_real_gui_async_profile_completion_activates_profile_without_overriding_manual_mode(self):
        from desktop_web_ui import DesktopWebBridge
        from tests.gui_support import gui_root
        with patch.dict(os.environ, {'APPDATA': self.folder.name}):
            ns = runpy.run_path(str(Path(__file__).resolve().parents[1]/'hwp-auto-docfit.py'), run_name='import_check')
            root = gui_root(ns['TkinterDnD'].Tk, ns)
            root.withdraw()
            try:
                app = ns['HwpAutoDocFitGUI'](root)
                bridge = DesktopWebBridge(app)
                bridge._tk = lambda callback, **kwargs: callback()
                bridge.set_mode('spacing')
                old_ids = set(app.state.profiles)
                profile = copy.deepcopy(app.state.profiles[''])
                sample = self.path.with_name('마포구_업무보고.hwpx')
                sample.write_bytes(b'mocked analysis fixture')
                namespace = app._서식_분석_시작.__globals__
                with patch.dict(namespace, {'한글파일_서식_분석': lambda *args: copy.deepcopy(profile),
                                            '알파_서식예시폴더_사용': False,
                                            '서식프로파일_폴더': lambda: Path(self.folder.name)/'profiles'}):
                    bridge.quick_register_and_activate_profile(str(sample))
                    deadline = time.monotonic() + 4
                    while app.state.analyzing_format and time.monotonic() < deadline:
                        root.update()
                        time.sleep(.01)
                self.assertFalse(app.state.analyzing_format)
                self.assertNotIn(app.state.active_profile_id, old_ids)
                self.assertEqual(app.state.profiles[app.state.active_profile_id]['name'], '마포구 업무보고')
                self.assertEqual(app.state.profiles[app.state.active_profile_id]['organization'], '마포구')
                self.assertEqual(app.selected_mode.get(), 'spacing')
                self.assertIn('등록하고 선택', bridge.get_state()['quick_notice']['message'])
            finally:
                root.destroy()

    def test_quick_profile_name_and_native_badge_routing(self):
        example = self.path.with_name('마포구_업무보고.hwpx')
        example.write_bytes(b'fixture')
        def copied(path, **kw):
            self.gui._프로파일들['new'] = {'name': kw['기본이름']}
            self.gui._활성_서식_프로파일 = 'new'
        self.gui._서식_분석_시작 = Mock(side_effect=copied)
        self.bridge.set_profile_drop_bounds([10, 10, 200, 50])
        state = self.bridge.receive_drop([str(example)], client_x=30, client_y=30)
        self.assertEqual(state['profile'], 'new')
        self.assertEqual(self.gui._프로파일들['new']['name'], '마포구 업무보고')
        self.assertEqual(self.gui._서식_분석_시작.call_args.kwargs['기관'], '마포구')
        self.assertEqual(self.gui.files, [])

    def test_completed_result_is_never_opened_automatically(self):
        for results in (([{'결과': 'done.hwpx'}]), []):
            self.gui._결과목록 = results
            with patch.object(self.bridge, 'open_result') as opened:
                state = self.bridge.get_state()
            self.assertFalse(state['auto_open_result'])
            opened.assert_not_called()
