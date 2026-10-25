"""tests/test_v2_filepick.py

P3 2.0.0 3단계: 네이티브 파일·폴더 선택 및 경로 API 분기 단위 시험
- 사람 입력 없이 완료(실제 Tk 모달, messagebox, filedialog, 한/글 COM은 patch/mock으로 완전 차단)
- B01(add_files), B02(add_folder), B11(add_format_file):
  ui_tk_fallback=False 시 Tk 차단(FLUTTER_ONLY), ui_tk_fallback=True 시 Tk 대화상자 호출 유지
- B09(idioms add_body), B10(table_template learn):
  path 미제공 시 ui_tk_fallback=False 면 PATH_REQUIRED 에러 응답, True 면 filedialog 호출
- B07, B08(flow_editor export_png, export_hwpx):
  filedialog.asksaveasfilename 유지 및 원자적 파일 치환 보존
- add_paths, add_format_paths:
  파일/디렉터리 경로 수신 시 백엔드 적정 처리 메서드로 정확히 라우팅
"""

import base64
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from desktop_web_ui import DesktopWebBridge
from docfit_app.api_contract import ServiceError
try:
    from tests.test_desktop_browser_api import _FakeGui, _Var
except ImportError:
    from test_desktop_browser_api import _FakeGui, _Var


class _FakeTkRoot:
    def __init__(self, hidden=True):
        self._docfit_hidden_backend = hidden
        self._docfit_min_size = (420, 400)

    def cget(self, key):
        return None

    def winfo_exists(self):
        return True

    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080

    def wait_variable(self, variable):
        pass


class _FilePickFakeApp(_FakeGui):
    def __init__(self):
        super().__init__()
        self.root = _FakeTkRoot(hidden=True)
        self.ui_tk_fallback = False
        self.closing = False
        self._실패목록 = {}
        self.quality_level_var = _Var("standard")
        self.hwpx_cleanup_var = _Var("keep")
        self.doc_type_var = _Var("auto")
        self._flutter_completion = {}
        self._flutter_format_review = {}
        self._서식분석중 = False
        self._준말_서비스_대역 = MagicMock()

        # Mocks for file selection callbacks
        self.파일선택 = MagicMock()
        self._폴더선택 = MagicMock()
        self._서식_파일에서_추가 = MagicMock()
        self._서식_분석_시작 = MagicMock()
        self.파일추가 = MagicMock()
        self.폴더추가 = MagicMock()

    def 로그표시(self, msg):
        pass

    def _준말_서비스(self):
        return self._준말_서비스_대역

    def 파일포맷_변경_시작(self):
        pass


class TestV2FilePick(unittest.TestCase):
    def setUp(self):
        self.app = _FilePickFakeApp()
        self.bridge = DesktopWebBridge(self.app)
        self.bridge._tk = lambda callback, **kwargs: callback()
        self.bridge._update_document_hints = MagicMock()

    # -------------------------------------------------------------------------
    # B01: add_files
    # -------------------------------------------------------------------------

    def test_b01_add_files_flutter_path_blocks_tk_dialog(self):
        """B01 Flutter 경로: ui_tk_fallback=False 일 때 Tk 창을 띄우지 않고 FLUTTER_ONLY 반환"""
        self.app.ui_tk_fallback = False
        result = self.bridge.add_files()
        self.assertEqual(result, {"ok": False, "error": "FLUTTER_ONLY"})
        self.app.파일선택.assert_not_called()

    def test_b01_add_files_tk_fallback_calls_gui_file_select(self):
        """B01 레거시 경로: ui_tk_fallback=True 일 때 기존 Tk gui.파일선택 호출 및 상태 반환"""
        self.app.ui_tk_fallback = True
        result = self.bridge.add_files()
        self.app.파일선택.assert_called_once()
        self.bridge._update_document_hints.assert_called_once()
        self.assertIsInstance(result, dict)
        self.assertIn("files", result)

    # -------------------------------------------------------------------------
    # B02: add_folder
    # -------------------------------------------------------------------------

    def test_b02_add_folder_flutter_path_blocks_tk_dialog(self):
        """B02 Flutter 경로: ui_tk_fallback=False 일 때 Tk 창을 띄우지 않고 FLUTTER_ONLY 반환"""
        self.app.ui_tk_fallback = False
        result = self.bridge.add_folder()
        self.assertEqual(result, {"ok": False, "error": "FLUTTER_ONLY"})
        self.app._폴더선택.assert_not_called()

    def test_b02_add_folder_tk_fallback_calls_gui_folder_select(self):
        """B02 레거시 경로: ui_tk_fallback=True 일 때 기존 Tk gui._폴더선택 호출 및 상태 반환"""
        self.app.ui_tk_fallback = True
        result = self.bridge.add_folder()
        self.app._폴더선택.assert_called_once()
        self.bridge._update_document_hints.assert_called_once()
        self.assertIsInstance(result, dict)
        self.assertIn("files", result)

    # -------------------------------------------------------------------------
    # B11: add_format_file
    # -------------------------------------------------------------------------

    def test_b11_add_format_file_flutter_path_blocks_tk_dialog(self):
        """B11 Flutter 경로: ui_tk_fallback=False 일 때 Tk 창을 띄우지 않고 FLUTTER_ONLY 반환"""
        self.app.ui_tk_fallback = False
        result = self.bridge.add_format_file()
        self.assertEqual(result, {"ok": False, "error": "FLUTTER_ONLY"})
        self.app._서식_파일에서_추가.assert_not_called()

    def test_b11_add_format_file_tk_fallback_calls_gui_format_file(self):
        """B11 레거시 경로: ui_tk_fallback=True 일 때 기존 Tk gui._서식_파일에서_추가 호출 및 상태 반환"""
        self.app.ui_tk_fallback = True
        result = self.bridge.add_format_file()
        self.app._서식_파일에서_추가.assert_called_once()
        self.assertIsInstance(result, dict)
        self.assertIn("files", result)

    # -------------------------------------------------------------------------
    # B09: idioms (add_body)
    # -------------------------------------------------------------------------

    @patch("docfit_app.idiom_service.IdiomService")
    def test_b09_idioms_add_body_without_path_raises_in_flutter_path(self, mock_service_cls):
        """B09 Flutter 경로: path 미지정 시 filedialog 없이 ServiceError(PATH_REQUIRED) 응답"""
        self.app.ui_tk_fallback = False
        with patch("tkinter.filedialog.askopenfilename") as mock_pick:
            res = self.bridge.idioms("add_body", {"key": "test_key"})
            self.assertFalse(res.get("ok"))
            self.assertEqual(res.get("error", {}).get("code"), "PATH_REQUIRED")
            mock_pick.assert_not_called()

    @patch("docfit_app.idiom_service.IdiomService")
    def test_b09_idioms_add_body_with_path_processes_directly(self, mock_service_cls):
        """B09 경로 제공 시: filedialog 미호출, service.command 직접 실행"""
        mock_service = MagicMock()
        mock_service.command.return_value = {"saved": True}
        mock_service_cls.return_value = mock_service

        with patch("tkinter.filedialog.askopenfilename") as mock_pick:
            res = self.bridge.idioms("add_body", {"key": "test_key", "path": "C:/dummy/test.hwp"})
            mock_pick.assert_not_called()
            mock_service.command.assert_called_once()
            self.assertTrue(res.get("ok"))
            self.assertEqual(res.get("data"), {"saved": True})

    @patch("docfit_app.idiom_service.IdiomService")
    def test_b09_idioms_add_body_tk_fallback_uses_filedialog(self, mock_service_cls):
        """B09 레거시 경로: ui_tk_fallback=True 일 때 path 미제공 시 Tk filedialog 호출 후 등록"""
        self.app.ui_tk_fallback = True
        mock_service = MagicMock()
        mock_service.command.return_value = {"saved": True}
        mock_service_cls.return_value = mock_service

        with patch("tkinter.filedialog.askopenfilename", return_value="C:/picked/doc.hwp") as mock_pick:
            res = self.bridge.idioms("add_body", {"key": "test_key"})
            mock_pick.assert_called_once()
            mock_service.command.assert_called_once_with("add_body", {"key": "test_key", "path": "C:/picked/doc.hwp"})
            self.assertTrue(res.get("ok"))
            self.assertEqual(res.get("data"), {"saved": True})

    # -------------------------------------------------------------------------
    # B10: table_template (learn)
    # -------------------------------------------------------------------------

    @patch("docfit_app.table_template_service.TableTemplateService")
    def test_b10_table_template_learn_without_path_raises_in_flutter_path(self, mock_service_cls):
        """B10 Flutter 경로: path 미지정 시 filedialog 없이 ServiceError(PATH_REQUIRED) 응답"""
        self.app.ui_tk_fallback = False
        with patch("tkinter.filedialog.askopenfilename") as mock_pick:
            res = self.bridge.table_template("learn", {})
            self.assertFalse(res.get("ok"))
            self.assertEqual(res.get("error", {}).get("code"), "PATH_REQUIRED")
            mock_pick.assert_not_called()

    @patch("docfit_app.table_template_service.TableTemplateService")
    def test_b10_table_template_learn_with_path_processes_directly(self, mock_service_cls):
        """B10 경로 제공 시: filedialog 미호출, TableTemplateService.command 직접 실행"""
        mock_service = MagicMock()
        mock_service.command.return_value = {"learned": True}
        mock_service_cls.return_value = mock_service

        with patch("tkinter.filedialog.askopenfilename") as mock_pick:
            res = self.bridge.table_template("learn", {"path": "C:/dummy/template.hwpx"})
            mock_pick.assert_not_called()
            mock_service.command.assert_called_once()
            self.assertTrue(res.get("ok"))
            self.assertEqual(res.get("data"), {"learned": True})

    @patch("docfit_app.table_template_service.TableTemplateService")
    def test_b10_table_template_learn_tk_fallback_uses_filedialog(self, mock_service_cls):
        """B10 레거시 경로: ui_tk_fallback=True 일 때 path 미제공 시 Tk filedialog 호출 후 학습"""
        self.app.ui_tk_fallback = True
        mock_service = MagicMock()
        mock_service.command.return_value = {"learned": True}
        mock_service_cls.return_value = mock_service

        with patch("tkinter.filedialog.askopenfilename", return_value="C:/picked/template.hwpx") as mock_pick:
            res = self.bridge.table_template("learn", {})
            mock_pick.assert_called_once()
            mock_service.command.assert_called_once_with("learn", {"path": "C:/picked/template.hwpx"}, running=False)
            self.assertTrue(res.get("ok"))
            self.assertEqual(res.get("data"), {"learned": True})

    # -------------------------------------------------------------------------
    # B07 / B08: flow_editor export_png, export_hwpx (유지 검증)
    # -------------------------------------------------------------------------

    @patch("docfit_app.flow_service.FlowService")
    def test_b07_flow_editor_png_export_preserves_filedialog(self, mock_service_cls):
        """B07 흐름도 PNG 저장: 플래그와 무관하게 기존 Tk filedialog 유지 및 원자적 파일 생성"""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_png = Path(tmpdir) / "output.png"
            mock_store = MagicMock()
            mock_store._path = Path(tmpdir) / "flow.json"
            self.app._준말_서비스_대역.settings = mock_store

            mock_service = MagicMock()
            mock_service.png_bytes.return_value = b"\x89PNG\r\n\x1a\nfake_png"
            mock_service_cls.return_value = mock_service

            with patch("tkinter.filedialog.asksaveasfilename", return_value=str(out_png)) as mock_ask:
                res = self.bridge.flow_editor("export_png", {"base64": "fake_b64", "name": "diagram"})
                mock_ask.assert_called_once()
                self.assertEqual(res, {"path": str(out_png)})
                self.assertTrue(out_png.is_file())
                self.assertEqual(out_png.read_bytes(), b"\x89PNG\r\n\x1a\nfake_png")

    @patch("docfit_app.flow_service.FlowService")
    @patch("docfit_core.table_builder.normalize")
    @patch("docfit_core.table_builder.build_table_hwpx")
    @patch("docfit_app.table_template_service.TableTemplateService")
    def test_b08_flow_editor_hwpx_export_preserves_filedialog(
        self, mock_tpl_cls, mock_build, mock_norm, mock_service_cls
    ):
        """B08 흐름도 HWPX 저장: 플래그와 무관하게 기존 Tk filedialog 유지 및 원자적 파일 생성"""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_hwpx = Path(tmpdir) / "output.hwpx"
            mock_store = MagicMock()
            mock_store._path = Path(tmpdir) / "flow.json"
            self.app._준말_서비스_대역.settings = mock_store

            mock_tpl = MagicMock()
            mock_tpl.snapshot.return_value = {"preview": {}}
            mock_tpl_cls.return_value = mock_tpl

            def fake_build(spec, base, target, basic_style=None):
                target.write_bytes(b"PK\x03\x04fake_hwpx")

            mock_build.side_effect = fake_build

            with patch("tkinter.filedialog.asksaveasfilename", return_value=str(out_hwpx)) as mock_ask:
                res = self.bridge.flow_editor("export_hwpx", {"spec": {"kind": "flow"}, "name": "table"})
                mock_ask.assert_called_once()
                self.assertEqual(res, {"path": str(out_hwpx)})
                self.assertTrue(out_hwpx.is_file())
                self.assertEqual(out_hwpx.read_bytes(), b"PK\x03\x04fake_hwpx")

    # -------------------------------------------------------------------------
    # add_paths & add_format_paths 라우팅 검증
    # -------------------------------------------------------------------------

    def test_add_paths_accepts_files_and_directories(self):
        """add_paths: 디렉터리는 gui.폴더추가, 일반 파일은 gui.파일추가로 분기하여 처리"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "doc.hwp"
            test_file.write_text("dummy", encoding="utf-8")
            test_dir = Path(tmpdir) / "subfolder"
            test_dir.mkdir()

            self.bridge.add_paths([str(test_file), str(test_dir)])
            self.app.파일추가.assert_called_once_with(str(test_file))
            self.app.폴더추가.assert_called_once_with(str(test_dir))

    def test_add_format_paths_accepts_hwp_and_hwpx(self):
        """add_format_paths: 유효한 HWP/HWPX 경로가 들어오면 gui._서식_분석_시작 트리거"""
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = Path(tmpdir) / "format.hwp"
            f1.write_text("f1", encoding="utf-8")
            f2 = Path(tmpdir) / "format2.hwpx"
            f2.write_text("f2", encoding="utf-8")

            res = self.bridge.add_format_paths([str(f1), str(f2)])
            self.app._서식_분석_시작.assert_called_once_with(str(f1), 이름묻기=False)
            self.assertIsInstance(res, dict)
            self.assertIn("files", res)


if __name__ == "__main__":
    unittest.main()
