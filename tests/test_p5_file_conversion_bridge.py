import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from desktop_web_ui import DesktopWebBridge, _BrowserApi
from docfit_app.native_file_dialog_service import NativeFileDialogService


class TestP5FileConversionBridge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_bridge(self, running=False, mode="spacing", files=None):
        gui = Mock()
        gui.running = running
        gui.selected_mode = Mock()
        gui.selected_mode.get.return_value = mode
        gui.files = list(files or [])
        gui.status_var = Mock()
        gui._결과목록 = []
        gui._실패목록 = {}
        gui._flutter_completion = {}
        gui._flutter_format_review = {}
        gui.range_mode_var = Mock()
        gui.range_mode_var.get.return_value = "all"
        gui.range_start_var = Mock()
        gui.range_start_var.get.return_value = 1
        gui.range_end_var = Mock()
        gui.range_end_var.get.return_value = 1
        gui.stage_board = Mock(active=None, visited=set(), outcome=None, detail="")
        gui._세부작업_기본저장 = {}
        gui.목록지우기 = Mock(side_effect=lambda: gui.files.clear() if not gui.running else None)
        gui._선택삭제 = Mock()
        gui._업데이트_서비스 = Mock(return_value=Mock(state=Mock(return_value={})))
        bridge = DesktopWebBridge(gui)
        bridge._tk = lambda cb, *a, **kw: cb()
        return bridge, gui

    def test_conversion_snapshot_keeps_editor_mode_and_uses_targets(self):
        bridge, gui = self._make_bridge(mode="spacing")
        bridge._conversion_targets = Mock(return_value=[{"format": "hwpx", "enabled": True}])
        state = bridge.get_file_conversion_state()
        self.assertEqual(state["mode"], "spacing")
        self.assertEqual(state["conversion_targets"], [{"format": "hwpx", "enabled": True}])
        self.assertEqual(state["conversion_target"], bridge.conversion_target)
        bridge._conversion_targets.assert_called_once()

    def test_conversion_snapshot_does_not_duplicate_ready_probe(self):
        bridge, gui = self._make_bridge(mode="file_format")
        targets = [{"format": "hwpx", "enabled": True}]
        bridge._conversion_targets = Mock(return_value=targets)
        state = bridge.get_file_conversion_state()
        self.assertEqual(state["mode"], "file_format")
        bridge._conversion_targets.assert_called_once()

    def test_selected_pptx_uses_conversion_policy(self):
        pptx = self.folder / "report.pptx"
        pptx.write_bytes(b"PK\x03\x04fake_pptx")
        bridge, gui = self._make_bridge()
        service = NativeFileDialogService()
        bridge._file_dialogs = service
        gui.파일추가 = Mock(return_value=True)

        token = service.register_selection('add_conversion_files', [str(pptx)])['selection_id']
        bridge.add_conversion_files(token)

        gui.파일추가.assert_called_once_with(str(pptx.resolve()), file_conversion=True)

    def test_running_job_rejects_conversion_list_mutation(self):
        sample = self.folder / "test.pptx"
        sample.write_bytes(b"data")
        bridge, gui = self._make_bridge(running=True, files=[str(sample)])
        gui.파일추가 = Mock()
        gui._선택삭제 = Mock()

        bridge.add_paths([str(sample)], file_conversion=True)
        gui.파일추가.assert_not_called()

        bridge.remove_file(0)
        gui._선택삭제.assert_not_called()

        bridge.clear_files()
        self.assertEqual(len(gui.files), 1)

    def test_file_format_start_delegates_existing_worker(self):
        bridge, gui = self._make_bridge(mode="spacing", files=[str(self.folder / "sample.hwpx")])
        gui.파일포맷_변경_시작 = Mock(return_value="job-1234")
        bridge._conversion_targets = Mock(return_value=[{"format": "pdf", "enabled": True}])

        with patch("subprocess.Popen") as mock_popen, patch("win32com.client.Dispatch", create=True) as mock_com:
            mock_popen.side_effect = AssertionError("subprocess creation forbidden")
            mock_com.side_effect = AssertionError("COM creation forbidden")

            job_id = bridge.start_job("file_format", {"target": "pdf", "file_order": ["a", "b"]})
            self.assertEqual(job_id, "job-1234")
            gui.파일포맷_변경_시작.assert_called_once_with(target="pdf", file_order=["a", "b"])

            gui.running = True
            with self.assertRaises(Exception):
                bridge.start_job("file_format", {"target": "pdf"})

    def test_job_cancellation_uses_exact_id(self):
        bridge, gui = self._make_bridge()
        gui.작업중단 = Mock()
        mock_job = Mock(id="job-target", kind="file_format")
        bridge._jobs = Mock(return_value=Mock(
            get=Mock(side_effect=lambda jid: mock_job if jid == "job-target" else None),
            cancel=Mock(return_value=mock_job),
            snapshot=Mock(return_value={"id": "job-target", "state": "cancelled"})
        ))

        res = bridge.cancel_job("job-target")
        self.assertEqual(res.get("state"), "cancelled")
        bridge._jobs().cancel.assert_called_once_with("job-target")
        gui.작업중단.assert_called_once()

    def test_show_result_reveals_folder_without_opening_document(self):
        res_file = self.folder / "output.pdf"
        res_file.write_bytes(b"%PDF-1.4")
        bridge, gui = self._make_bridge()
        gui._결과목록 = [{"결과": str(res_file), "원본": "input.hwpx", "쪽수": 1}]
        gui._경로_열기 = Mock()
        gui._알림 = Mock()
        gui.open_result = Mock()
        gui.open_results = Mock()

        with patch("desktop_web_ui.os.startfile", create=True) as mock_startfile:
            bridge.show_result(0)
            gui._경로_열기.assert_called_once()
            called_path = gui._경로_열기.call_args[0][0]
            self.assertTrue(str(called_path).startswith(str(self.folder)))
            if mock_startfile:
                mock_startfile.assert_not_called()
            gui.open_result.assert_not_called()
            gui.open_results.assert_not_called()
            gui._알림.assert_not_called()

    def test_browser_api_exposes_only_required_conversion_methods(self):
        bridge, gui = self._make_bridge()
        api = _BrowserApi(bridge)
        self.assertTrue(hasattr(api, "get_file_conversion_state"))
        self.assertTrue(hasattr(api, "add_conversion_files"))
        self.assertTrue(hasattr(api, "select_files"))
        self.assertTrue(hasattr(api, "selection_status"))
        self.assertFalse(hasattr(api, "register_selection"))
        self.assertFalse(hasattr(api, "gui"))
        self.assertFalse(hasattr(api, "hwp"))

    def test_registration_preserves_source_bytes(self):
        pptx = self.folder / "pres.pptx"
        md = self.folder / "doc.md"
        pptx_bytes = b"PK\x03\x04powerpoint_test_bytes"
        md_bytes = "# Markdown Content\nText".encode("utf-8")
        pptx.write_bytes(pptx_bytes)
        md.write_bytes(md_bytes)

        hash_pptx_before = hashlib.sha256(pptx_bytes).hexdigest()
        hash_md_before = hashlib.sha256(md_bytes).hexdigest()

        bridge, gui = self._make_bridge()
        gui.파일추가 = Mock(return_value=True)

        bridge.add_paths([str(pptx), str(md)], file_conversion=True)

        self.assertEqual(hashlib.sha256(pptx.read_bytes()).hexdigest(), hash_pptx_before)
        self.assertEqual(hashlib.sha256(md.read_bytes()).hexdigest(), hash_md_before)


if __name__ == "__main__":
    unittest.main()
