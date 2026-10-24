"""tests/test_v2_t04_t19.py

G31 2.0.0 3단계: T19 절약 완료 안내 + T04 서식 예시 편집 안내 Flutter 이관 단위 시험
- 사람 입력 없이 완료(실제 Tk 모달, messagebox, 한/글 창은 모두 patch로 차단)
- T04 Flutter 경로: 대기 상태(pending_dialog JSON), 답 전달(resolve_dialog), HWP 정리/분석 시작
- T04 Tk 경로: ui_tk_fallback=True 시 기존 Tk 창(Toplevel) 호출 확인 (patch로 검증)
- T19 Flutter 경로: Tk 창 대신 completion에 절약 문구·시간·캐릭터 그림 포함, Tk 창 미호출
- T19 Tk 경로: ui_tk_fallback=True 시 기존 Tk 절약 완료 창(Toplevel) 호출 확인 (patch로 검증)
"""

from pathlib import Path
import queue
import runpy
import unittest
from unittest.mock import MagicMock, patch

from desktop_web_ui import DesktopWebBridge
from test_desktop_browser_api import _FakeGui, _bridge

_ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))
HwpDocFitApp = _ns["HwpAutoDocFitGUI"]


class FakeTkRoot:
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


class TestV2T04T19(unittest.TestCase):
    def setUp(self):
        self.app = HwpDocFitApp.__new__(HwpDocFitApp)
        self.app.root = FakeTkRoot(hidden=True)
        self.app.running = False
        self.app._서식분석중 = False
        self.app.settings_toplevel = None
        self.app._예시편집_hwp = None
        self.app._예시편집_창 = None
        self.app._절약초 = 125.0
        self.app.ui_tk_fallback = False
        self.app.closing = False
        self.app.files = []
        self.app._결과목록 = []
        self.app._실패목록 = {}
        self.app.status_var = MagicMock(get=lambda: "처리 완료")
        self.app.developer_mode_var = MagicMock(get=lambda: False)
        self.app.stage_board = MagicMock()
        self.app._flutter_completion = {}
        self.app._flutter_format_review = {}

        self.bridge = DesktopWebBridge(self.app)
        self.bridge._tk = lambda callback, **kwargs: callback()
        ns = HwpDocFitApp._절약_완료창.__globals__
        # No Tcl interpreter, native window, message box or COM instance may be
        # created by these tests. Individual routing tests override only mocks.
        for name in ("Toplevel", "Tk"):
            self.enterContext(patch.object(ns["tk"], name, side_effect=AssertionError("Unexpected Tk window")))
        for name in ("StringVar", "PhotoImage", "Label"):
            self.enterContext(patch.object(ns["tk"], name))
        for name in ("Label", "Frame", "Button"):
            self.enterContext(patch.object(ns["ttk"], name))
        self.enterContext(patch.dict(ns, {"창_맨앞으로": MagicMock(),
                                         "한글_COM_인스턴스_생성": MagicMock(side_effect=AssertionError("Unexpected COM"))}))
        for name in ("showerror", "showinfo", "showwarning", "askokcancel", "askyesno"):
            self.enterContext(patch.object(ns["messagebox"], name, side_effect=AssertionError("Unexpected messagebox")))

    # =========================================================================
    # T04: 서식 예시 편집 안내 (외부 한/글 작성 후 분석 시작)
    # =========================================================================

    def test_t04_flutter_path_pending_dialog_json_and_cancel(self):
        """T04 Flutter 경로: 대기 상태 JSON 확인 및 취소 회신 시 한/글 종료 확인"""
        self.app.root._docfit_hidden_backend = True
        self.app.ui_tk_fallback = False

        mock_hwp = MagicMock()
        mock_window = MagicMock()
        mock_hwp.XHwpWindows.Item.return_value = mock_window
        mock_hwp.RegisterModule.return_value = True

        ns = HwpDocFitApp._서식_예시편집_시작.__globals__

        # Tk Toplevel이나 messagebox가 직접 뜨면 안 된다.
        with patch.object(ns["tk"], "Toplevel", side_effect=AssertionError("Unexpected Tk Toplevel")), \
             patch.object(ns["messagebox"], "showerror", side_effect=AssertionError("Unexpected showerror")), \
             patch.object(ns["messagebox"], "askokcancel", side_effect=AssertionError("Unexpected askokcancel")), \
             patch.object(ns.get("pythoncom", MagicMock()), "CoInitialize", return_value=None), \
             patch.dict(ns, {
                 "한글_COM_인스턴스_생성": MagicMock(return_value=mock_hwp),
                 "보안모듈_초기화": MagicMock(),
             }):

            done = MagicMock()

            def resolve_on_wait(variable):
                # wait_variable 진입 시 Flutter의 대기 다이얼로그 조회 및 응답 시뮬레이션
                pending = self.bridge.get_pending_dialog()
                self.assertIsNotNone(pending)
                self.assertEqual(pending.get("kind"), "format_example_edit")
                self.assertEqual(pending.get("title"), "서식 예시 문서 편집")
                self.assertEqual(pending.get("ok_label"), "분석 시작")
                self.assertEqual(pending.get("cancel_label"), "취소")
                self.assertTrue(pending.get("confirm"))
                self.assertIn("한/글 창에서 예시 문서를 작성하세요", pending.get("message", ""))

                # Flutter에서 취소 누름
                res = self.bridge.resolve_dialog(pending["id"], False)
                self.assertTrue(res.get("ok"))

            self.app.root.wait_variable = resolve_on_wait

            with patch.object(ns["tk"], "BooleanVar", return_value=done):
                self.app._서식_예시편집_시작()

            # 취소 시 HWP 종료 호출 확인
            mock_hwp.Clear.assert_called_with(1)
            mock_hwp.Quit.assert_called_once()
            self.assertIsNone(self.app._예시편집_hwp)

    def test_t04_flutter_path_approve_saves_and_starts_analysis(self):
        """T04 Flutter 경로: '분석 시작' 승인 시 HWPX 임시 저장 및 _서식_분석_시작 호출 검증"""
        self.app.root._docfit_hidden_backend = True
        self.app.ui_tk_fallback = False

        mock_hwp = MagicMock()
        mock_window = MagicMock()
        mock_hwp.XHwpWindows.Item.return_value = mock_window
        mock_hwp.RegisterModule.return_value = True
        mock_hwp.SaveAs.return_value = True

        mock_block = MagicMock()
        mock_block.type = "paragraph"
        mock_block.text = "□ 추진 배경 및 목적"
        mock_inspect = MagicMock(blocks=[mock_block])

        ns = HwpDocFitApp._서식_예시편집_시작.__globals__
        mock_분석_시작 = MagicMock()
        self.app._서식_분석_시작 = mock_분석_시작

        with patch.object(ns["tk"], "Toplevel", side_effect=AssertionError("Unexpected Tk Toplevel")), \
             patch.object(ns.get("pythoncom", MagicMock()), "CoInitialize", return_value=None), \
             patch.dict(ns, {
                 "한글_COM_인스턴스_생성": MagicMock(return_value=mock_hwp),
                 "보안모듈_초기화": MagicMock(),
                 "inspect_hwpx": MagicMock(return_value=mock_inspect),
             }):

            done = MagicMock()

            def resolve_on_wait(variable):
                pending = self.bridge.get_pending_dialog()
                self.assertEqual(pending.get("kind"), "format_example_edit")
                # Flutter에서 "분석 시작" 승인 회신
                self.bridge.resolve_dialog(pending["id"], True)

            self.app.root.wait_variable = resolve_on_wait

            with patch.object(ns["tk"], "BooleanVar", return_value=done):
                self.app._서식_예시편집_시작()

            # 임시 파일 저장 및 서식 분석 시작 호출 검증
            mock_hwp.SaveAs.assert_called()
            mock_분석_시작.assert_called_once()
            called_args, called_kwargs = mock_분석_시작.call_args
            self.assertIn("예시.hwpx", str(called_args[0]))
            self.assertEqual(called_kwargs.get("이름묻기"), False)
            self.assertEqual(called_kwargs.get("기본이름"), "추진 배경 및")
            mock_hwp.Quit.assert_called_once()

    def test_t04_tk_fallback_calls_legacy_toplevel(self):
        """T04 Tk fallback 경로: ui_tk_fallback=True 시 기존 Tk Toplevel 생성 확인"""
        self.app.root._docfit_hidden_backend = True
        self.app.ui_tk_fallback = True

        mock_hwp = MagicMock()
        mock_hwp.XHwpWindows.Item.return_value = MagicMock()
        mock_hwp.RegisterModule.return_value = True

        ns = HwpDocFitApp._서식_예시편집_시작.__globals__
        mock_toplevel_instance = MagicMock()

        with patch.object(ns["tk"], "Toplevel", return_value=mock_toplevel_instance) as mock_top, \
             patch.object(ns.get("pythoncom", MagicMock()), "CoInitialize", return_value=None), \
             patch.dict(ns, {
                 "한글_COM_인스턴스_생성": MagicMock(return_value=mock_hwp),
                 "보안모듈_초기화": MagicMock(),
             }):

            self.app._서식_예시편집_시작()

            # Tk 경로에서는 Toplevel 창이 열려야 함
            mock_top.assert_called_once_with(self.app.root)
            self.assertIs(self.app._예시편집_창, mock_toplevel_instance)

    def test_t04_invalid_document_reports_error_then_allows_cancel(self):
        ns = HwpDocFitApp._서식_예시편집_시작.__globals__
        for saved, expected_error in ((False, "저장"), (True, "항목기호")):
            # Save failures and missing markers both keep the editor open for
            # correction, then cancellation must close only the owned HWP.
            with self.subTest(saved=saved):
                hwp = MagicMock()
                hwp.RegisterModule.return_value = True
                hwp.SaveAs.return_value = saved
                analyze = MagicMock()
                self.app._서식_분석_시작 = analyze
                replies = []

                def reply(variable):
                    pending = self.bridge.get_pending_dialog()
                    replies.append(pending)
                    self.bridge.resolve_dialog(pending["id"], len(replies) == 1)

                self.app.root.wait_variable = reply
                with patch.dict(ns, {"한글_COM_인스턴스_생성": MagicMock(return_value=hwp),
                                     "보안모듈_초기화": MagicMock(),
                                     "inspect_hwpx": MagicMock(return_value=MagicMock(blocks=[]))}), \
                     patch.object(ns["tk"], "BooleanVar", return_value=MagicMock()), \
                     patch.object(ns["pythoncom"], "CoInitialize"):
                    self.app._서식_예시편집_시작()
                self.assertEqual(len(replies), 2)
                self.assertIn(expected_error, replies[1]["error"])
                hwp.Quit.assert_called_once()
                analyze.assert_not_called()

    # =========================================================================
    # T19: 작업 완료 시 절약 안내 화면 이관
    # =========================================================================

    def test_t19_flutter_path_populates_completion_without_tk(self):
        """T19 Flutter 경로: Tk Toplevel 창 없이 completion에 절약 문구·시간 반영 검증"""
        self.app.root._docfit_hidden_backend = True
        self.app.ui_tk_fallback = False
        self.app._절약초 = 150.0  # 2분 30초

        ns = HwpDocFitApp._절약_완료창.__globals__

        with patch.object(ns["tk"], "Toplevel", side_effect=AssertionError("Unexpected Tk Toplevel")):
            res = self.app._절약_완료창(성공=5, 실패=0)
            self.assertIsNone(res)

        # completion 데이터 확인
        comp = self.app._flutter_completion
        self.assertIn("당신의 소중한 시간 02분 30초가 절약되었습니다!", comp.get("savings_message", ""))
        self.assertEqual(comp.get("savings_seconds"), 150.0)
        self.assertEqual(comp.get("savings_time"), "02분 30초")

        # get_state() 브리지 전송 확인
        gui = _FakeGui()
        gui._flutter_completion = comp
        state = _bridge(gui).get_state()
        self.assertEqual(state["completion"]["savings_seconds"], 150.0)
        self.assertIn("02분 30초", state["completion"]["savings_message"])

    def test_t19_preserves_saved_seconds_after_counter_reset(self):
        self.app._절약초 = None
        self.app._절약_완료창(1, 0, savings_seconds=125.0)
        self.assertEqual(self.app._flutter_completion["savings_seconds"], 125.0)
        self.assertEqual(self.app._flutter_completion["savings_time"], "02분 05초")

    def test_t19_finished_event_carries_actual_savings_to_flutter(self):
        self.app._절약초 = 125.0
        self.app._안내키 = None
        self.app.root.after = MagicMock()
        for name in ("_안내_설정", "버튼_대기중", "_작업결과_표시", "로그표시"):
            setattr(self.app, name, MagicMock())
        events = queue.Queue()
        events.put(("finished", 1, 0))
        diagnostics = MagicMock()
        ns = HwpDocFitApp.queue_처리.__globals__
        with patch.dict(ns, {"gui_queue": events, "진단로그": diagnostics}):
            self.app.queue_처리()
        diagnostics.assert_not_called()
        self.assertTrue(events.empty())
        self.assertIsNone(self.app._절약초)
        self.assertEqual(self.app._flutter_completion["savings_seconds"], 125.0)
        self.assertEqual(self.app._flutter_completion["savings_time"], "02분 05초")

    def test_t19_flutter_path_handles_failures_message(self):
        """T19 Flutter 경로: 실패 문서가 있을 때의 안내 문구 검증"""
        self.app.root._docfit_hidden_backend = True
        self.app.ui_tk_fallback = False

        ns = HwpDocFitApp._절약_완료창.__globals__

        with patch.object(ns["tk"], "Toplevel", side_effect=AssertionError("Unexpected Tk Toplevel")):
            self.app._절약_완료창(성공=3, 실패=2)

        comp = self.app._flutter_completion
        self.assertIn("문서 2개를 처리하지 못했습니다", comp.get("savings_message", ""))
        self.assertIn("성공 3개", comp.get("savings_message", ""))

    def test_t19_tk_fallback_calls_legacy_toplevel(self):
        """T19 Tk fallback 경로: ui_tk_fallback=True 시 기존 Tk Toplevel 생성 확인"""
        self.app.root._docfit_hidden_backend = True
        self.app.ui_tk_fallback = True
        self.app._절약초 = 60.0

        ns = HwpDocFitApp._절약_완료창.__globals__
        mock_toplevel_instance = MagicMock()
        mock_toplevel_instance.winfo_screenwidth.return_value = 1920
        mock_toplevel_instance.winfo_screenheight.return_value = 1080
        mock_toplevel_instance.winfo_reqwidth.return_value = 600
        mock_toplevel_instance.winfo_reqheight.return_value = 300

        with patch.object(ns["tk"], "Toplevel", return_value=mock_toplevel_instance) as mock_top:
            win = self.app._절약_완료창(성공=1, 실패=0)

        mock_top.assert_called_once_with(self.app.root)
        self.assertIs(win, mock_toplevel_instance)


if __name__ == "__main__":
    unittest.main()
