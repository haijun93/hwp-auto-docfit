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

    def _세부작업_옵션_맞춤(self, mode):
        self.linked = getattr(self, "linked", []) + [mode]

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
        self.assertEqual(len(public), 36)
        self.assertTrue(all(callable(value) for value in public.values()))
        self.assertNotIn('gui', public)
        self.assertNotIn('window', public)
        self.assertNotIn('request_close', public)
        self.assertEqual(api.get_state, bridge.get_state)

    def test_show_format_example_calls_app(self):
        # '서식 예시 확인': 지금 고른 서식을 입힌 예시 보고서를 앱이 만들어 연다.
        gui = _FakeGui()
        called = []
        gui._서식예시_확인 = lambda: called.append(True)
        _bridge(gui).show_format_example()
        self.assertEqual(called, [True])

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
        # 세부 작업을 바꿀 때마다 그 카드 옵션(표 제외 등)을 세부 작업에 맞춘다.
        self.assertEqual(gui.linked, ["spacing", "spacing"])

    def test_reset_stages_restores_mode_defaults(self):
        gui = _FakeGui()
        bridge = _bridge(gui)
        bridge.set_stage("body_spacing", False)
        bridge.reset_stages()
        self.assertTrue(gui.stage_choices["spacing"]["body_spacing"])
        self.assertFalse(gui.stage_choices["spacing"]["style_unify"])
        self.assertEqual(gui.linked, ["spacing", "spacing"])

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
        self.assertEqual([(p["id"], p["name"]) for p in bridge._profiles()],
                         [("", "기본 서식"), ("abc", "[마포구] 보고서")])

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

    def test_spacing_card_toggles_existing_spacing_reset(self):
        # '자간 정리' 카드의 '기존 자간 초기화'는 세부 작업 01(reset_spacing)과 같은 값이다.
        gui = _FakeGui()
        gui.selected_mode.set("all")
        bridge = _bridge(gui)
        self.assertTrue(bridge.get_state()["reset_spacing"])
        state = bridge.set_reset_spacing(False)
        self.assertEqual((state["mode"], state["reset_spacing"]), ("spacing", False))
        self.assertFalse(gui.stage_choices["spacing"]["reset_spacing"])
        self.assertFalse(next(s["on"] for s in state["stages"] if s["key"] == "reset_spacing"))
        self.assertTrue(gui.stage_choices["all"]["reset_spacing"])   # 한 번에 적용은 따로 둔다
        # 세부 작업에서 켜도 카드 값이 같이 바뀐다.
        self.assertTrue(bridge.set_stage("reset_spacing", True)["reset_spacing"])
        # 변경 감시 변수가 있으면 그 변수로 바꾼다(앱이 세부 작업 값과 설정 파일을 함께 바꿈).
        gui.reset_spacing_var = _Var(True)
        bridge.set_reset_spacing(False)
        self.assertFalse(gui.reset_spacing_var.get())
        gui.running = True
        bridge.set_reset_spacing(True)
        self.assertFalse(gui.reset_spacing_var.get())

    def test_spacing_card_toggles_table_spacing(self):
        # '자간 정리' 카드의 '표 내 자간 정리'는 설정 table_spacing(표 안 문장 자간조정)과 같은 값이다.
        gui = _FakeGui()
        gui.selected_mode.set("all")
        bridge = _bridge(gui)
        self.assertTrue(bridge.get_state()["table_spacing"])   # 변수가 없으면 기본값 켜짐
        gui.table_spacing_var = _Var(True)
        state = bridge.set_table_spacing(False)
        self.assertEqual((state["mode"], state["table_spacing"]), ("spacing", False))
        self.assertFalse(gui.table_spacing_var.get())
        gui.running = True
        self.assertFalse(bridge.set_table_spacing(True)["table_spacing"])   # 작업 중에는 바꾸지 않는다

    def test_all_card_toggles_exclude_tables(self):
        # '한 번에 적용'의 '표 제외'(설정 all_exclude_tables)는 기본 꺼짐이고, 바꾸면 그 카드를 고른다.
        gui = _FakeGui()
        gui.selected_mode.set("spacing")
        bridge = _bridge(gui)
        self.assertFalse(bridge.get_state()["exclude_tables"])   # 변수가 없으면 기본값 꺼짐
        gui.exclude_tables_var = _Var(False)
        state = bridge.set_exclude_tables(True)
        self.assertEqual((state["mode"], state["exclude_tables"]), ("all", True))
        gui.include_spacing_var.set(False)
        self.assertEqual(bridge.set_exclude_tables(True)["mode"], "format")   # 자간 조정을 뺀 한 번에 적용
        gui.running = True
        self.assertTrue(bridge.set_exclude_tables(False)["exclude_tables"])   # 작업 중에는 바꾸지 않는다

    def test_card_options_toggle_and_select_card(self):
        # 서식 통일 '표 제외'·'자간 정리 제외'·'페이지 맞춤 제외', 한 번에 적용 '페이지 맞춤 제외'(모두 기본 꺼짐)
        gui = _FakeGui()
        gui.selected_mode.set("spacing")
        bridge = _bridge(gui)
        self.assertEqual(bridge.get_state()["card_options"],
                         {"all_exclude_pagefit": False, "unify_exclude_tables": False,
                          "unify_exclude_spacing": False, "unify_exclude_pagefit": False})
        for name in ("all_exclude_pagefit_var", "unify_exclude_tables_var", "unify_exclude_spacing_var",
                     "unify_exclude_pagefit_var"):
            setattr(gui, name, _Var(False))
        state = bridge.set_card_option("unify_exclude_spacing", True)
        self.assertEqual((state["mode"], state["card_options"]["unify_exclude_spacing"]), ("unify", True))
        state = bridge.set_card_option("all_exclude_pagefit", True)
        self.assertEqual((state["mode"], state["card_options"]["all_exclude_pagefit"]), ("all", True))
        with self.assertRaises(ValueError):
            bridge.set_card_option("unknown", True)
        gui.running = True
        self.assertTrue(bridge.set_card_option("all_exclude_pagefit", False)["card_options"]["all_exclude_pagefit"])

    def test_format_manager_profiles_drop_routing_and_edits(self):
        # 서식 목록은 이름·기관·기본 서식 여부·예시 파일·사용 중 여부를 함께 준다.
        gui = _FakeGui()
        gui._프로파일들["abc"]["source"] = {"filename": "예시.hwpx"}
        bridge = _bridge(gui)
        state = bridge.get_state()
        self.assertEqual(state["profiles"][1], {"id": "abc", "name": "[마포구] 보고서", "title": "보고서",
                                                "organization": "마포구", "builtin": False, "source": "예시.hwpx",
                                                "active": False, "coverage": None})
        self.assertTrue(state["profiles"][0]["builtin"] and state["profiles"][0]["active"])
        self.assertEqual((state["drop_target"], state["format_task"]), ("documents", {"busy": False, "file": ""}))
        # '서식 관리' 창이 열리면 끌어 놓은 예시 보고서는 서식 복제로, 닫히면 문서 목록으로 간다.
        started, added = [], []
        gui._서식_분석_시작 = lambda path, 이름묻기=False: started.append((path, 이름묻기))
        gui.파일추가 = lambda path: added.append(path) or True
        gui.로그표시 = lambda *_: None
        with self.assertRaises(ValueError):
            bridge.set_drop_target("somewhere")
        self.assertEqual(bridge.set_drop_target("format")["drop_target"], "format")
        bridge.receive_drop([r"C:\a\메모.txt", r"C:\a\예시.hwpx", r"C:\a\둘째.hwp"])
        self.assertEqual(started, [(r"C:\a\예시.hwpx", False)])
        self.assertEqual(added, [])
        bridge.receive_drop([r"C:\a\메모.txt"])
        self.assertIn("HWP 또는 HWPX", gui.status_var.get())
        bridge.set_drop_target("documents")
        bridge.receive_drop([r"C:\a\보고서.hwpx"])
        self.assertEqual(added, [r"C:\a\보고서.hwpx"])
        self.assertEqual(len(started), 1)
        # 이름 바꾸기·삭제가 안 되면 notice에 이유를 담는다.
        gui._서식_이름_저장 = lambda identifier, name, organization: "이미 사용 중인 서식 이름입니다." if name == "중복" else None
        gui._서식_삭제 = lambda identifier: None
        self.assertEqual(bridge.rename_profile("abc", "중복", "")["notice"], "이미 사용 중인 서식 이름입니다.")
        self.assertNotIn("notice", bridge.rename_profile("abc", "새 이름", "마포구"))
        self.assertNotIn("notice", bridge.delete_profile("abc"))
        edited = []
        gui._서식_수정하기 = lambda identifier=None: edited.append(identifier)
        bridge.edit_profile("abc")
        self.assertEqual(edited, ["abc"])

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
