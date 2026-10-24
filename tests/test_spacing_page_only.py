"""자간 정리 카드의 독립 페이지 맞춤과 자간 불변 계약."""
from pathlib import Path
import os
import runpy
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from docfit_core.app_state import RunOptions
from docfit_core.stage_selection import SPACING_STAGE_KEYS, default_choice, stages_for_mode


class SpacingPageOptionsTests(unittest.TestCase):
    def test_four_combinations_and_master_off_overrides_reset_and_style(self):
        choices = {"spacing": {key: True for key, _ in stages_for_mode("spacing")}}
        for spacing in (False, True):
            for page in (False, True):
                with self.subTest(spacing=spacing, page=page):
                    selected = RunOptions(mode="spacing", spacing_enabled=spacing,
                                          spacing_page_fit=page).resolve_stages(choices)
                    self.assertEqual([selected[k] for k in SPACING_STAGE_KEYS], [spacing] * 7)
                    self.assertEqual(selected["style_unify"], spacing)
                    self.assertEqual((selected["page_fit"], selected["page_group"]), (page, page))
        self.assertTrue(choices["spacing"]["reset_spacing"])

    def test_old_defaults_and_other_modes_do_not_gain_page_fit(self):
        selected = RunOptions(mode="spacing").resolve_stages({})
        self.assertTrue(selected["body_spacing"])
        self.assertFalse(selected["page_fit"])
        self.assertFalse(default_choice("page_group", "spacing"))
        # 새 옵션은 다른 카드의 페이지/자간 선택에는 영향을 주지 않는다.
        selected = RunOptions(mode="all", spacing_enabled=False).resolve_stages({})
        self.assertTrue(selected["body_spacing"])
        self.assertTrue(selected["page_fit"])

    def test_table_exclusion_and_advanced_page_selection_are_respected(self):
        selected = RunOptions(mode="spacing", spacing_page_fit=True, table_spacing=False).resolve_stages(
            {"spacing": {"page_fit": True, "page_group": False}})
        self.assertFalse(selected["control_spacing"])
        self.assertTrue(selected["page_fit"])
        self.assertFalse(selected["page_group"])


class SpacingPagePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
                               run_name="import_check")

    def test_page_only_dispatches_vertical_fit_and_group_without_spacing_or_format(self):
        fn = self.ns["_문서_처리_1회"]
        calls = []
        forbidden = Mock(side_effect=AssertionError("페이지 맞춤 전용에서 자간/서식 함수 실행"))
        names = ("본문_기존자간조정", "본문_문장부호_처리", "컨트롤_내부_자간조정",
                 "컨트롤_내부_문장부호_처리", "공문_띄어쓰기_전체_적용", "연결부호_전체_맞춤",
                 "서식통일_전체_적용", "문단_내어쓰기_전체_갱신", "문단세트2_배치_적용")
        for standard in (False, True):
            calls.clear()
            selection = RunOptions(mode="spacing", spacing_enabled=False,
                                   spacing_page_fit=True).resolve_stages({})
            with patch.dict(fn.__globals__, {
                **{name: forbidden for name in names},
                "작업_모드": "spacing", "표준서식_사용": standard, "선택_세부작업": selection,
                "세트문장_같은쪽_사용": True, "세트문장_통계": {},
                "문단세트_가능": lambda _: False, "중단_요청됨": lambda: False,
                "단계표시": Mock(), "상태": Mock(), "로그": Mock(),
                "hwp_run": Mock(), "순회_시작": Mock(), "문단글_캐시_구간": lambda action: action,
                "보고서_페이지수_맞춤_전체_적용": lambda: calls.append("page") or True,
                "세트문장_같은쪽_전체_적용": lambda: calls.append("group") or True,
            }):
                self.assertTrue(fn("원본.hwpx"))
            self.assertEqual(calls, ["page", "group"])
        forbidden.assert_not_called()

    def test_page_fit_off_never_dispatches_page_stages(self):
        fn = self.ns["_문서_처리_1회"]
        forbidden = Mock(side_effect=AssertionError("페이지 맞춤 OFF에서 실행"))
        with patch.dict(fn.__globals__, {
            "작업_모드": "spacing", "표준서식_사용": False,
            "선택_세부작업": RunOptions(mode="spacing", spacing_enabled=False).resolve_stages({}),
            "문단세트_가능": lambda _: False, "중단_요청됨": lambda: False,
            "단계표시": Mock(), "상태": Mock(), "로그": Mock(), "hwp_run": Mock(), "순회_시작": Mock(),
            "보고서_페이지수_맞춤_전체_적용": forbidden, "세트문장_같은쪽_전체_적용": forbidden,
        }):
            self.assertTrue(fn("원본.hwpx"))
        forbidden.assert_not_called()

    def test_page_fit_last_resort_cannot_pull_words_when_spacing_off(self):
        fn = self.ns["문단_줄수_원본맞춤"]
        forbidden = Mock(side_effect=AssertionError("페이지 전용에서 자간 축소"))
        with patch.dict(fn.__globals__, {
            "작업_모드": "spacing", "선택_세부작업": {key: False for key in SPACING_STAGE_KEYS},
            "다음단어_당김_시도": forbidden, "_문단_줄시작들": forbidden,
        }):
            self.assertFalse(fn(0, 1))
        forbidden.assert_not_called()


class SpacingPageBridgeTests(unittest.TestCase):
    def test_real_gui_persists_page_only_and_links_advanced_stages(self):
        from desktop_web_ui import DesktopWebBridge
        from tests.gui_support import gui_root
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"APPDATA": folder}):
            ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
                               run_name="import_check")
            for reopen in (False, True):
                root = gui_root(ns["TkinterDnD"].Tk, ns)
                root.withdraw()
                try:
                    app = ns["HwpAutoDocFitGUI"](root)
                    bridge = DesktopWebBridge(app)
                    bridge._tk = lambda callback, **kwargs: callback()
                    if not reopen:
                        self.assertTrue(app.spacing_enabled_var.get())
                        self.assertTrue(app.spacing_page_fit_var.get())
                        bridge.set_card_option("spacing_page_fit", True)
                        bridge.set_card_option("spacing_enabled", False)
                    self.assertFalse(app.spacing_enabled_var.get())
                    self.assertTrue(app.spacing_page_fit_var.get())
                    self.assertFalse(any(app.stage_choices["spacing"][key] for key in SPACING_STAGE_KEYS))
                    self.assertTrue(app.stage_choices["spacing"]["page_fit"])
                    saved = ns["설정_불러오기"]()
                    self.assertFalse(saved["spacing_enabled"])
                    self.assertTrue(saved["spacing_page_fit"])
                    # 세부 작업에서 자간 단계를 다시 고르면 마스터도 켜진다.
                    if reopen:
                        bridge.set_stage("body_spacing", True)
                        self.assertTrue(app.spacing_enabled_var.get())
                        self.assertTrue(app.spacing_page_fit_var.get())
                finally:
                    root.destroy()

    def test_switches_select_spacing_and_both_off_block_start(self):
        from desktop_web_ui import DesktopWebBridge
        enabled, page = Mock(), Mock()
        enabled.get.return_value = False
        page.get.return_value = False
        bridge = DesktopWebBridge.__new__(DesktopWebBridge)
        bridge.gui = SimpleNamespace(running=False, spacing_enabled_var=enabled,
                                     spacing_page_fit_var=page, selected_mode=Mock())
        bridge._tk = lambda callback: callback()
        bridge.get_state = lambda: {}
        bridge._mode_selected = Mock()
        self.assertFalse(bridge._can_start("spacing", ["원본.hwp"], False))
        with self.assertRaisesRegex(ValueError, "하나 이상"):
            bridge.start("spacing")
        page.get.return_value = True
        self.assertTrue(bridge._can_start("spacing", ["원본.hwp"], False))
        bridge.set_card_option("spacing_page_fit", True)
        page.set.assert_called_once_with(True)
        bridge.gui.selected_mode.set.assert_called_once_with("spacing")
        bridge.gui.running = True
        bridge.set_card_option("spacing_enabled", True)
        enabled.set.assert_not_called()
