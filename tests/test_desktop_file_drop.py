from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from desktop_web_ui import DesktopWebBridge, _bind_file_drop, _FILE_DROP_SCRIPT


class DropEvent:
    def __iadd__(self, handler):
        self.handler = handler
        return self


class FileDropTests(TestCase):
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
        bridge.add_paths.assert_called_once_with([r'C:\예시.hwpx'])
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
