"""지연 생성 및 파괴된 설정 위젯의 버튼 상태 회귀 시험 (COM 미사용)."""
from pathlib import Path
import runpy
from types import SimpleNamespace
import tkinter as tk
import unittest
from unittest.mock import Mock


class Widget:
    def __init__(self, destroyed=False):
        self.states = []
        self.destroyed = destroyed

    def config(self, *, state):
        if self.destroyed:
            raise tk.TclError("destroyed")
        self.states.append(state)


class ButtonStateGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))
        cls.gui = ns["HwpAutoDocFitGUI"]

    def app(self):
        app = SimpleNamespace(files=["sample.hwpx"], main_profile_combo=Widget(), stop_button=Widget())
        for name in ("_작업방식_버튼상태", "_설정탭_상태_갱신", "_실행버튼_상태", "_요약갱신",
                     "_범위_상태_갱신", "_색상표시_상태_갱신", "_표준서식_하위옵션_상태_갱신"):
            setattr(app, name, Mock())
        return app

    def cycle(self, app):
        self.gui.버튼_작업중(app)
        self.gui.버튼_대기중(app)
        self.assertEqual(app.main_profile_combo.states, ["disabled", "readonly"])
        self.assertEqual(app.stop_button.states, ["normal", "disabled"])

    def test_missing_settings_widgets(self):
        self.cycle(self.app())

    def test_all_widgets_and_popup(self):
        app = self.app()
        names = "profile_combo copy_format_button settings_button keep_punctuation_set_check clear_button document_review_button prevent_word_split_check punctuation_check punctuation_threshold_spin table_spacing_check log_file_check page_range_toggle range_all_radio range_pages_radio range_start_spin range_end_spin retry_body_spin retry_table_spin two_pass_check color_mark_check autoclose_check stdformat_check paren_shrink_check paren_label_bold_check verify_check integrity_report_file_check final_review_file_check _팝업_profile_combo".split()
        for name in names:
            setattr(app, name, Widget())
        for name in ("color_radios", "std_detail_checks", "std_parspace_spins", "label_symbol_checks"):
            setattr(app, name, [Widget()])
        for name in ("range_mode_var", "color_mark_on_var", "stdformat_var", "paren_label_bold_var"):
            setattr(app, name, Mock())
        app._프로파일_콤보_이름목록 = ["profile_combo", "main_profile_combo", "_팝업_profile_combo"]
        self.cycle(app)
        self.assertEqual(app.profile_combo.states, ["disabled", "readonly"])
        self.assertEqual(app._팝업_profile_combo.states, ["disabled", "readonly"])
        self.assertEqual(app.copy_format_button.states, ["disabled", "normal"])
        app._범위_상태_갱신.assert_called_once_with()
        app._표준서식_하위옵션_상태_갱신.assert_called_once_with()

    def test_destroyed_widgets_and_missing_lists(self):
        app = self.app()
        app.profile_combo = Widget(destroyed=True)
        app.color_radios = [Widget(destroyed=True), Widget()]
        app.std_detail_checks = None
        self.cycle(app)
        self.assertEqual(app.color_radios[1].states, ["disabled"])


if __name__ == "__main__":
    unittest.main()
