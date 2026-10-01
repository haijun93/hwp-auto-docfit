import unittest
from unittest import mock

from desktop_web_ui import DesktopWebBridge, _BrowserApi
from docfit_core.stage_selection import stages_for_mode


class _Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _Combo:
    def __init__(self):
        self.index = None

    def current(self, index):
        self.index = index


class _FakeGui:
    """Tk 없이 연결부 명령을 시험하기 위한 최소 앱 대역."""

    def __init__(self):
        self.running = False
        self.files = []
        self.selected_mode = _Var("spacing")
        self.status_var = _Var("")
        self.range_mode_var = _Var("all")
        self.range_start_var = _Var("1")
        self.range_end_var = _Var("1")
        self.stage_choices = {
            mode: {key: key != "style_unify" for key, _ in stages_for_mode(mode)}
            for mode in ("spacing", "unify", "format", "all")
        }
        self._세부작업_기본저장 = {mode: False for mode in self.stage_choices}
        self.saved = []
        self.summaries = 0
        self._프로파일들 = {"": {"name": "기본 서식"}, "abc": {"name": "보고서", "organization": "마포구"}}
        self._프로파일_ids = ["", "abc"]
        self._활성_서식_프로파일 = ""
        self.main_profile_combo = _Combo()
        self.selected_profiles = []
        self.autoclose_var = _Var(True)
        self.verify_var = _Var(False)
        self.check_updates_on_start_var = _Var(True)
        self.include_spacing_var = _Var(True)
        self._결과목록 = [{"원본": r"C:\a\문서.hwp", "결과": r"C:\a\문서(자간조정).hwpx", "쪽수": 3}]
        self.opened = []
        self.stage_board = object()

    def _세부작업_기본값_저장(self, mode, 저장=True):
        self._세부작업_기본저장[mode] = bool(저장)
        self.saved.append((mode, bool(저장), dict(self.stage_choices[mode])))

    def _요약갱신(self):
        self.summaries += 1

    def _프로파일_선택(self, event):
        self.selected_profiles.append(event.widget.index)
        self._활성_서식_프로파일 = self._프로파일_ids[event.widget.index]

    def _경로_열기(self, path):
        self.opened.append(path)


def _bridge(gui):
    bridge = DesktopWebBridge(gui)
    bridge._tk = lambda callback, timeout=120, front=False: callback()
    return bridge


class BrowserApiTests(unittest.TestCase):
    def test_only_commands_exposed_not_native_window_or_tk_graph(self):
        bridge = DesktopWebBridge(object())
        bridge.window = object()
        api = _BrowserApi(bridge)
        public = {name: getattr(api, name) for name in dir(api) if not name.startswith('_')}
        self.assertEqual(len(public), 25)
        self.assertTrue(all(callable(value) for value in public.values()))
        self.assertNotIn('gui', public)
        self.assertNotIn('window', public)
        self.assertNotIn('request_close', public)
        self.assertEqual(api.get_state, bridge.get_state)

    def test_state_lists_stages_profiles_and_options(self):
        state = _bridge(_FakeGui()).get_state()
        self.assertEqual([item["key"] for item in state["stages"]],
                         [key for key, _ in stages_for_mode("spacing")])
        self.assertFalse(state["default_saved"])
        self.assertEqual(state["options"], {"autoclose": True, "verify": False, "check_updates": True})
        self.assertEqual(state["results"][0]["source"], "문서.hwp")
        self.assertEqual(state["results"][0]["pages"], 3)

    def test_stage_toggle_saves_only_when_default_saving_is_on(self):
        gui = _FakeGui()
        bridge = _bridge(gui)
        bridge.set_stage("body_spacing", False)
        self.assertFalse(gui.stage_choices["spacing"]["body_spacing"])
        self.assertEqual(gui.saved, [])
        bridge.set_stage_default(True)
        bridge.set_stage("short_line", False)
        self.assertEqual(gui.saved[-1][0], "spacing")
        self.assertFalse(gui.saved[-1][2]["short_line"])
        # 모르는 단계 키는 무시한다.
        bridge.set_stage("없는단계", False)
        self.assertNotIn("없는단계", gui.stage_choices["spacing"])

    def test_reset_stages_restores_mode_defaults(self):
        gui = _FakeGui()
        bridge = _bridge(gui)
        bridge.set_stage("body_spacing", False)
        bridge.reset_stages()
        self.assertTrue(gui.stage_choices["spacing"]["body_spacing"])
        self.assertFalse(gui.stage_choices["spacing"]["style_unify"])

    def test_running_job_blocks_setting_changes(self):
        gui = _FakeGui()
        gui.running = True
        bridge = _bridge(gui)
        bridge.set_stage("body_spacing", False)
        bridge.set_option("verify", True)
        bridge.set_profile("abc")
        self.assertTrue(gui.stage_choices["spacing"]["body_spacing"])
        self.assertFalse(gui.verify_var.get())
        self.assertEqual(gui.selected_profiles, [])

    def test_profile_and_quick_option(self):
        gui = _FakeGui()
        bridge = _bridge(gui)
        bridge.set_profile("abc")
        self.assertEqual(gui.selected_profiles, [1])
        bridge.set_profile("없는서식")
        self.assertEqual(gui.selected_profiles, [1])
        bridge.set_option("verify", True)
        self.assertTrue(gui.verify_var.get())
        with self.assertRaises(ValueError):
            bridge.set_option("임의설정", True)
        self.assertEqual(bridge._profiles(), [
            {"id": "", "name": "기본 서식"},
            {"id": "abc", "name": "[마포구] 보고서"},
        ])

    def test_all_card_runs_format_when_spacing_is_excluded(self):
        gui = _FakeGui()
        bridge = _bridge(gui)
        state = bridge.set_mode("all")
        self.assertEqual((state["mode"], state["include_spacing"]), ("all", True))
        # '자간 조정 포함'을 끄면 같은 카드에서 서식 적용(format)으로 실행한다.
        state = bridge.set_include_spacing(False)
        self.assertEqual((state["mode"], state["include_spacing"]), ("format", False))
        bridge.set_mode("spacing")
        self.assertEqual(bridge.set_mode("all")["mode"], "format")   # 저장된 선택을 따른다
        state = bridge.set_include_spacing(True)
        self.assertEqual(state["mode"], "all")
        # 예전 화면이 보내는 format은 자간 조정을 끈 한 번에 적용이다.
        state = bridge.set_mode("format")
        self.assertEqual((state["mode"], state["include_spacing"]), ("format", False))
        gui.running = True
        self.assertEqual(bridge.set_include_spacing(True)["mode"], "format")

    def test_result_actions_use_selected_result(self):
        gui = _FakeGui()
        bridge = _bridge(gui)
        with mock.patch("desktop_web_ui.os.path.isfile", return_value=True):
            bridge.open_result(0)
        self.assertEqual(gui.opened, [r"C:\a\문서(자간조정).hwpx"])
        bridge.open_result(5)
        self.assertIn("찾을 수 없습니다", gui.status_var.get())
        with mock.patch("desktop_web_ui.os.path.isfile", return_value=True), \
                mock.patch("desktop_web_ui.os.name", "nt"), \
                mock.patch("desktop_web_ui.subprocess.Popen") as popen:
            bridge.show_result(0)
        self.assertEqual(popen.call_args.args[0][:2], ["explorer", "/select,"])


if __name__ == '__main__':
    unittest.main()
