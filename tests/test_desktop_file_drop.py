from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from pathlib import Path
import tempfile

from desktop_web_ui import DesktopWebBridge, _bind_file_drop, _FILE_DROP_SCRIPT


class DropEvent:
    def __iadd__(self, handler):
        self.handler = handler
        return self


class FileDropTests(TestCase):
    def test_only_successful_document_drop_advances_navigation_revision(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'report.md'
            path.write_text('# title', encoding='utf-8')
            gui = Mock(running=False, files=[])
            gui.파일추가.return_value = True
            bridge = DesktopWebBridge(gui)
            bridge._tk = lambda callback: callback()
            bridge.get_state = Mock(return_value={})
            bridge.receive_drop([str(path)])
            self.assertEqual(bridge._document_drop_revision, 1)
            gui.파일추가.return_value = False
            bridge.receive_drop([str(path)])
            bridge.receive_drop([str(path.with_suffix('.missing'))])
            self.assertEqual(bridge._document_drop_revision, 1)
            gui.파일추가.return_value = True
            bridge.add_paths([str(path)])
            self.assertEqual(bridge._document_drop_revision, 1)
            gui.running = True
            bridge.receive_drop([str(path)])
            self.assertEqual(bridge._document_drop_revision, 1)

    def bind(self):
        event = DropEvent()
        window = SimpleNamespace(dom=SimpleNamespace(document=SimpleNamespace(
            events=SimpleNamespace(drop=event))), run_js=Mock())
        bridge = Mock()
        _bind_file_drop(window, bridge)
        window.run_js.assert_called_once_with(_FILE_DROP_SCRIPT)
        return event.handler, bridge

    def test_native_paths_delivered_including_korean_spaces_and_multiple_files(self):
        handler, bridge = self.bind()
        paths = [r'C:\문서 폴더\첫째.hwpx', r'C:\문서 폴더\둘째.hwp']
        handler.callback({'dataTransfer': {'files': [
            {'name': '첫째.hwpx', 'pywebviewFullPath': paths[0]},
            {'name': '둘째.hwp', 'pywebviewFullPath': paths[1]},
        ]}})
        # 끌어 놓은 경로는 놓기 대상(문서 목록·서식 복제)을 고르는 receive_drop으로 간다.
        bridge.receive_drop.assert_called_once_with(paths)
        self.assertTrue(handler.prevent_default)

    def test_drop_goes_to_format_cloning_while_format_manager_is_open(self):
        bridge = DesktopWebBridge(Mock())
        bridge.add_paths, bridge.add_format_paths = Mock(), Mock()
        bridge.receive_drop([r'C:\예시.hwpx'])
        bridge.add_paths.assert_called_once_with([r'C:\예시.hwpx'], from_drop=True)
        bridge.drop_target = 'format'
        bridge.receive_drop([r'C:\예시.hwpx'])
        bridge.add_format_paths.assert_called_once_with([r'C:\예시.hwpx'])

    def test_missing_native_path_never_guesses_from_filename(self):
        handler, bridge = self.bind()
        with self.assertLogs('desktop_web_ui', level='WARNING'):
            handler.callback({'dataTransfer': {'files': [{'name': 'test.hwpx'}]}})
        bridge.receive_drop.assert_not_called()
        bridge._tk.assert_called_once()

    def test_non_file_drop_does_not_add_documents(self):
        handler, bridge = self.bind()
        handler.callback({'dataTransfer': {'files': []}})
        bridge.receive_drop.assert_not_called()

    def test_running_job_rejects_document_list_changes(self):
        gui = Mock(running=True)
        bridge = DesktopWebBridge(gui)
        bridge._tk = lambda callback: callback()
        bridge.get_state = Mock(return_value={})
        bridge.add_paths([r'C:\문서.hwpx'])
        gui.파일추가.assert_not_called()
        gui.폴더추가.assert_not_called()

    def test_conversion_drop_precedes_profile_badge(self):
        bridge = DesktopWebBridge(Mock())
        bridge.add_paths = Mock(return_value={})
        bridge.quick_register_and_activate_profile = Mock()
        bridge.add_format_paths = Mock()
        bridge.set_drop_target('file_conversion')
        bridge.set_profile_drop_bounds([10, 10, 100, 100])
        paths = [r'C:\보고서.pptx']
        bridge.receive_drop(paths, client_x=50, client_y=50)
        bridge.add_paths.assert_called_once_with(paths, from_drop=True, file_conversion=True)
        bridge.quick_register_and_activate_profile.assert_not_called()
        bridge.add_format_paths.assert_not_called()

    def test_existing_drop_targets_keep_routing(self):
        bridge = DesktopWebBridge(Mock())
        bridge.add_paths = Mock(return_value={})
        bridge.add_format_paths = Mock(return_value={})
        bridge.quick_register_and_activate_profile = Mock(return_value={})

        paths = [r'C:\문서.hwpx']
        bridge.set_drop_target('documents')
        bridge.receive_drop(paths)
        bridge.add_paths.assert_called_with(paths, from_drop=True)

        bridge.set_drop_target('manual_documents')
        bridge.receive_drop(paths)
        bridge.add_paths.assert_called_with(paths, from_drop=False)

        bridge.set_drop_target('format')
        bridge.receive_drop(paths)
        bridge.add_format_paths.assert_called_with(paths)

        bridge.set_drop_target('quick_format')
        bridge.receive_drop(paths)
        bridge.quick_register_and_activate_profile.assert_called_with(paths[0])

    def test_conversion_drop_rejects_folders_and_missing_native_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            subfolder = Path(folder) / 'sub'
            subfolder.mkdir()
            gui = Mock(running=False, files=[])
            gui.status_var = Mock()
            gui.파일추가 = Mock(return_value=False)
            gui.폴더추가 = Mock(return_value=0)
            bridge = DesktopWebBridge(gui)
            bridge._tk = lambda callback: callback()
            bridge.get_file_conversion_state = Mock(return_value={})
            bridge.set_drop_target('file_conversion')

            bridge.receive_drop([str(subfolder)])
            gui.status_var.set.assert_called_with('파일을 끌어 놓아 주세요')
            gui.파일추가.assert_not_called()
            gui.폴더추가.assert_not_called()

            handler, mock_bridge = self.bind()
            with self.assertLogs('desktop_web_ui', level='WARNING'):
                handler.callback({'dataTransfer': {'files': [{'name': 'unknown.pptx'}]}})
            mock_bridge.receive_drop.assert_not_called()
