"""파일변환 화면(2.0.7): 올린 파일 크기, 원본 열기·폴더에서 보기, 결과의 원본 열기."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from desktop_web_ui import DesktopWebBridge, _BrowserApi


class ConversionFileActionsTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.source = Path(self.folder.name) / "보고서.hwp"
        self.source.write_bytes(b"x" * 2048)
        self.gui = Mock(files=[str(self.source)])
        self.gui._결과목록 = [{"원본": str(self.source), "결과": str(self.source.with_suffix(".pdf"))}]
        self.bridge = DesktopWebBridge(self.gui)
        self.bridge._tk = Mock(side_effect=lambda callback, **kwargs: callback())
        self.bridge.get_state = Mock(return_value={})

    def tearDown(self):
        self.folder.cleanup()

    def test_open_and_reveal_source_files(self):
        self.bridge.open_source_file(0)
        self.gui._경로_열기.assert_called_once_with(str(self.source))
        with patch("desktop_web_ui.subprocess.Popen") as popen, patch("desktop_web_ui.os.name", "nt"):
            self.bridge.show_source_file(0)
        self.assertEqual(popen.call_args.args[0][:2], ["explorer", "/select,"])
        self.bridge.open_source_file(5)
        self.gui.status_var.set.assert_called_with("파일을 찾을 수 없습니다.")

    def test_open_result_source(self):
        self.gui._경로_열기.reset_mock()
        self.bridge.open_result_source(0)
        self.gui._경로_열기.assert_called_once_with(str(self.source))

    def test_browser_exposes_new_commands(self):
        api = _BrowserApi(self.bridge)
        for name in ("open_source_file", "show_source_file", "open_result_source",
                     "start_single_file_conversion"):
            self.assertTrue(callable(getattr(api, name)))

    def test_single_conversion_passes_one_file_snapshot_and_preserves_ui_target(self):
        self.source.with_suffix('.docx').write_bytes(b'existing result')
        self.source.with_suffix('.hwpx').write_bytes(b'existing result')
        other = Path(self.folder.name) / 'other.pdf'
        other.write_bytes(b'other')
        self.gui.files = [str(self.source), str(other)]
        self.gui.running = False
        self.gui._job_id = None
        self.gui.selected_mode = Mock()
        self.gui._결과_초기화 = Mock()
        self.gui._안내_설정 = Mock()
        self.gui.버튼_작업중 = Mock()
        self.gui.로그표시 = Mock()
        self.gui.status_var = Mock()
        self.gui.worker = None
        self.gui._docfit_runtime_namespace = {
            '중단_event': __import__('threading').Event(),
            'gui_queue': __import__('queue').Queue(),
        }
        self.gui._flutter_completion = {}
        self.gui._flutter_format_review = {}
        self.gui._결과_초기화 = Mock()
        self.gui._안내_설정 = Mock()
        self.gui.버튼_작업중 = Mock()
        self.gui.로그표시 = Mock()
        self.gui.status_var = Mock()
        self.gui.selected_mode = Mock()
        self.gui.running = False
        self.gui.closing = False
        self.gui._안내키 = None
        self.gui._안내지남 = set()
        self.gui._진행문서 = self.gui._진행_세부작업 = None
        self.gui._실패목록 = {}
        self.gui._작업종료시각 = None
        self.gui._작업시작시각 = None
        self.gui._job_managed_conversion = None
        self.bridge.conversion_target = 'hwpx'
        targets = [
            {'format': 'hwpx', 'label': 'HWPX', 'enabled': True, 'reason': 'ok'},
            {'format': 'pdf', 'label': 'PDF', 'enabled': True, 'reason': 'ok'},
        ]
        with patch.object(self.bridge, '_conversion_targets', return_value=targets), \
             patch('docfit_app.jobs.prepare_legacy') as prepare, \
             patch('docfit_app.jobs.manager_for') as manager_for, \
             patch('docfit_app.conversion_runner.start_conversion_job') as start_conversion:
            manager = manager_for.return_value
            manager.thread.return_value = Mock(name='worker')
            prepare.return_value.begin.return_value = 'job-1'
            result = self.bridge.start_single_file_conversion(0, 'pdf')
        self.assertEqual(result, 'job-1')
        self.assertEqual(start_conversion.call_args.args[1:3], ([str(self.source)], 'pdf'))
        self.assertEqual(self.gui.files, [str(self.source), str(other)])
        self.assertEqual(self.bridge.conversion_target, 'hwpx')

    def test_single_conversion_rejects_unavailable_target_without_starting(self):
        self.gui.running = False
        self.gui.files = [str(self.source)]
        with patch.object(self.bridge, '_conversion_targets', return_value=[
            {'format': 'hwpx', 'label': 'HWPX', 'enabled': False, 'reason': '한/글이 필요합니다'},
        ]), patch.object(self.bridge, '_start_single_conversion_snapshot') as start:
            with self.assertRaisesRegex(ValueError, '한/글이 필요합니다'):
                self.bridge.start_single_file_conversion(0, 'hwpx')
        start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
