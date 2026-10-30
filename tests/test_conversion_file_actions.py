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
        for name in ("open_source_file", "show_source_file", "open_result_source"):
            self.assertTrue(callable(getattr(api, name)))


if __name__ == "__main__":
    unittest.main()
