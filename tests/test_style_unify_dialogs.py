"""tests/test_style_unify_dialogs.py

G29 서식통일 마법사 검토 대화상자(T20, T21, T22) 브리지 및 검토창 단위 시험
- 가짜 GUI 환경에서 선택 대기 → 답 → 마법사가 받은 값이 Tk와 동일한지 검증
- 취소 시 마법사 중단 및 안전 복귀 검증
- ui_tk_fallback이 꺼져 있을 때 브리지 모달 경로 검증
"""

from pathlib import Path
import runpy
import threading
import unittest
from unittest.mock import MagicMock, patch

from desktop_web_ui import DesktopWebBridge

_ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))
HwpDocFitApp = _ns["HwpAutoDocFitGUI"]


class FakeTkRoot:
    def __init__(self):
        self._docfit_hidden_backend = True
        self._ui_tk_fallback = False

    def cget(self, key):
        return None


class FakeGuiForStyleUnify:
    """_서식통일 검토창 로직 검증용 가짜 GUI"""
    def __init__(self, fallback=False):
        self.root = FakeTkRoot()
        self.root._ui_tk_fallback = fallback
        self._flutter_values = {}
        self._flutter_selection = []
        self._flutter_format_review = {}
        self.files = ["C:\\test\\doc1.hwp"]
        self._last_alert_kwargs = {}

    def _is_tk_fallback(self):
        return getattr(self.root, "_ui_tk_fallback", False)

    def _알림(self, func, title, message, **kwargs):
        self._last_alert_kwargs = kwargs
        if func is _ns["messagebox"].showerror:
            raise AssertionError(message)
        # 가짜 알림 응답: approve_next_alert 플래그에 따라 승인 또는 취소 반환
        return getattr(self, "_approve_next_alert", True)


class TestStyleUnifyDialogs(unittest.TestCase):
    def setUp(self):
        self.gui = FakeGuiForStyleUnify(fallback=False)
        # 잘못된 경로는 팝업이나 재시도 대기 대신 즉시 실패한다.
        namespace = HwpDocFitApp._서식통일_대표서식_검토창.__globals__
        for module, attr in ((namespace["tk"], "Toplevel"),
                             (namespace["messagebox"], "showerror"),
                             (namespace["messagebox"], "askyesno")):
            guard = patch.object(module, attr, side_effect=AssertionError("unexpected Tk modal"))
            guard.start()
            self.addCleanup(guard.stop)

    def test_t20_pick_style_dialog_approve(self):
        """T20 대표 서식 검토: 승인 시 대표프로필 업데이트 반영 검증 (Tk 동등성)"""
        대표프로필 = {
            ("1.", "개조식", 1): {
                "font": ("맑은 고딕", 10),
                "size": (1500, 10),
                "marker_bold": (True, 10),
                "label_bold": (False, 10),
                "hanging_indent": (True, 10),
            }
        }
        그룹별_표본 = {("1.", "개조식", 1): [{"text": "1. 샘플"}]}
        req = {
            "payload": 그룹별_표본,
            "profile": 대표프로필,
            "approved": False,
            "done": threading.Event(),
        }

        # 사용자가 Flutter에서 폰트 및 크기 수정한 시나리오
        self.gui._approve_next_alert = True
        self.gui._flutter_values = {
            "0:font": "나눔고딕",
            "0:size": "16.0",
            "0:marker_bold": "False",
            "0:label_bold": "True",
            "0:hanging_indent": "False",
        }

        # 검토창 호출
        HwpDocFitApp._서식통일_대표서식_검토창(self.gui, req)

        self.assertTrue(req["approved"])
        self.assertTrue(req["done"].is_set())

        # 대표프로필에 pt * 100 값 및 글꼴 등이 정상 반영되었는지 확인
        prof = 대표프로필[("1.", "개조식", 1)]
        self.assertEqual(prof["font"][0], "나눔고딕")
        self.assertEqual(prof["size"][0], 1600)  # 16.0 pt -> 1600
        self.assertFalse(prof["marker_bold"][0])
        self.assertTrue(prof["label_bold"][0])
        self.assertFalse(prof["hanging_indent"][0])

        # 전달된 kind 및 flutter_styles 확인
        self.assertEqual(self.gui._last_alert_kwargs.get("kind"), "style_unify_profile")
        styles = self.gui._last_alert_kwargs.get("flutter_styles", [])
        self.assertEqual(len(styles), 1)
        self.assertEqual(styles[0]["marker"], "1.")

    def test_t20_pick_style_dialog_cancel(self):
        """T20 대표 서식 검토: 취소 시 approved=False 및 마법사 중단 검증"""
        대표프로필 = {
            ("1.", "개조식", 1): {
                "font": ("맑은 고딕", 10),
                "size": (1500, 10),
            }
        }
        req = {
            "payload": {("1.", "개조식", 1): []},
            "profile": 대표프로필,
            "approved": True,
            "done": threading.Event(),
        }

        self.gui._approve_next_alert = False  # 취소
        HwpDocFitApp._서식통일_대표서식_검토창(self.gui, req)

        self.assertFalse(req["approved"])
        self.assertTrue(req["done"].is_set())
        # 대표프로필은 변경되지 않아야 함
        self.assertEqual(대표프로필[("1.", "개조식", 1)]["font"][0], "맑은 고딕")

    def test_t21_area_dialog_approve(self):
        """T21 적용 영역 검토: 승인 시 선택된 인덱스 목록 전달 검증"""
        계획 = [
            {"mismatch": True, "marker": "1.", "role": "개조식", "text": "1. 본문 첫번째"},
            {"mismatch": False, "marker": "2.", "role": "개조식", "text": "2. 일치 문장"},
            {"mismatch": True, "marker": "가.", "role": "본문", "text": "가. 두번째"},
        ]
        req = {
            "payload": 계획,
            "approved": False,
            "selected": [],
            "done": threading.Event(),
        }

        self.gui._approve_next_alert = True
        self.gui._flutter_selection = [0]  # 첫 번째 불일치 문장만 선택

        HwpDocFitApp._서식통일_적용영역_검토창(self.gui, req)

        self.assertTrue(req["approved"])
        self.assertEqual(req["selected"], [0])
        self.assertTrue(req["done"].is_set())
        self.assertEqual(self.gui._last_alert_kwargs.get("kind"), "style_unify_regions")
        areas = self.gui._last_alert_kwargs.get("flutter_areas", [])
        self.assertEqual(len(areas), 2)  # mismatch인 항목 2개 전달

    def test_t21_area_dialog_cancel(self):
        """T21 적용 영역 검토: 취소 시 selected 빈 목록 검증"""
        계획 = [{"mismatch": True, "marker": "1.", "role": "개조식", "text": "1. 내용"}]
        req = {
            "payload": 계획,
            "approved": True,
            "selected": [0],
            "done": threading.Event(),
        }

        self.gui._approve_next_alert = False
        self.gui._flutter_selection = [0]

        HwpDocFitApp._서식통일_적용영역_검토창(self.gui, req)

        self.assertFalse(req["approved"])
        self.assertEqual(req["selected"], [])
        self.assertTrue(req["done"].is_set())

    def test_t22_result_dialog(self):
        """T22 결과 확인: 결과 payload 전달 및 승인 완료 검증"""
        result_payload = {
            "status": "passed",
            "checked": 30,
            "issues": [],
            "not_checkable": [],
            "unresolved": [],
            "file": "보고서.hwp",
        }
        req = {
            "payload": result_payload,
            "approved": False,
            "done": threading.Event(),
        }

        HwpDocFitApp._서식통일_결과_확인창(self.gui, req)

        self.assertTrue(req["approved"])
        self.assertTrue(req["done"].is_set())
        self.assertEqual(self.gui._flutter_format_review["status"], "passed")
        self.assertEqual(self.gui._last_alert_kwargs.get("kind"), "style_unify_result")
        res_data = self.gui._last_alert_kwargs.get("flutter_result", {})
        self.assertEqual(res_data.get("status_text"), "검수 통과")

    def test_desktop_web_ui_bridge_pending_and_resolve(self):
        """desktop_web_ui.py의 브리지 get_pending_dialog 및 resolve_dialog 검증"""
        bridge = DesktopWebBridge(self.gui)
        bridge._tk = lambda callback, **kwargs: callback()
        done = MagicMock()
        self.gui._flutter_dialog = {
            "id": "profile-1", "title": "대표 서식 확인", "message": "대표값을 확인하세요.",
            "confirm": True, "kind": "style_unify_profile",
            "styles": [{"index": 0, "marker": "1."}],
            "fields": [{"id": "0:font", "value": "맑은 고딕"}],
            "choices": [{"id": 0, "label": "1."}], "done": done,
        }
        pending = bridge.get_pending_dialog()
        self.assertEqual(pending["kind"], "style_unify_profile")
        self.assertEqual(pending["styles"][0]["marker"], "1.")
        self.assertNotIn("done", pending)
        bridge.resolve_dialog(pending["id"], True, [0], {"0:font": "나눔스퀘어"})
        self.assertTrue(self.gui._flutter_dialog["answer"])
        self.assertEqual(self.gui._flutter_dialog["values"], {"0:font": "나눔스퀘어"})
        self.assertEqual(self.gui._flutter_dialog["selection"], [0])
        done.set.assert_called_once_with(True)

    def test_bridge_rejects_unknown_fields_and_choices_even_when_empty(self):
        bridge = DesktopWebBridge(self.gui)
        bridge._tk = lambda callback, **kwargs: callback()
        self.gui._flutter_dialog = {"id": "empty", "choices": [], "fields": [], "done": MagicMock()}
        with self.assertRaises(ValueError):
            bridge.resolve_dialog("empty", True, [99], {})
        with self.assertRaises(ValueError):
            bridge.resolve_dialog("empty", True, [], {"unknown": "True"})
        self.gui._flutter_dialog["done"].set.assert_not_called()

    def test_tk_routes_reach_original_window_without_opening_modal(self):
        methods = (
            (HwpDocFitApp._서식통일_대표서식_검토창, {"profile": {}, "payload": {}}),
            (HwpDocFitApp._서식통일_적용영역_검토창, {"payload": []}),
            (HwpDocFitApp._서식통일_결과_확인창, {"payload": {}}),
        )
        namespace = methods[0][0].__globals__
        for hidden, fallback in ((False, False), (False, True), (True, True)):
            self.gui.root._docfit_hidden_backend = hidden
            self.gui.root._ui_tk_fallback = fallback
            for method, request in methods:
                with self.subTest(hidden=hidden, fallback=fallback, method=method.__name__):
                    with patch.object(namespace['tk'], 'Toplevel', side_effect=RuntimeError('Tk route')) as window:
                        with self.assertRaisesRegex(RuntimeError, 'Tk route'):
                            method(self.gui, request)
                        window.assert_called_once_with(self.gui.root)

    def test_alert_roundtrip_uses_only_hidden_backend_variable(self):
        app = HwpDocFitApp.__new__(HwpDocFitApp)
        app.root = FakeTkRoot()
        app.ui_tk_fallback = False
        bridge = DesktopWebBridge(app)
        bridge._tk = lambda callback, **kwargs: callback()
        done = MagicMock()
        def resolve(variable):
            self.assertIs(variable, done)
            pending = bridge.get_pending_dialog()
            self.assertEqual(pending['styles'], [{'index': 0}])
            bridge.resolve_dialog(pending['id'], True, [0], {'0:font': '나눔고딕'})
        app.root.wait_variable = resolve
        namespace = HwpDocFitApp._알림.__globals__
        with patch.object(namespace['tk'], 'BooleanVar', return_value=done):
            accepted = app._알림(namespace['messagebox'].askyesno, '대표 서식', '확인',
                               kind='style_unify_profile', flutter_styles=[{'index': 0}],
                               flutter_choices=[{'id': 0}], flutter_fields=[{'id': '0:font'}])
        self.assertTrue(accepted)
        self.assertEqual(app._flutter_values, {'0:font': '나눔고딕'})
        self.assertEqual(app._flutter_selection, [0])
        self.assertIsNone(app._flutter_dialog)



if __name__ == "__main__":
    unittest.main()
