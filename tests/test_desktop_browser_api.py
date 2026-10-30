import unittest
import tempfile
from pathlib import Path
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


class _LogText:
    def __init__(self, value=""):
        self.value = value

    def get(self, start, end):
        return self.value

    def delete(self, start, end):
        self.value = ""


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
        self.unify_result_window_var = _Var(False)
        self.verify_var = _Var(False)
        self.integrity_report_file_var = _Var(False)
        self.final_review_file_var = _Var(False)
        self.log_file_var = _Var(False)
        self.check_updates_on_start_var = _Var(True)
        self.developer_mode_var = _Var(False)
        self.always_on_top_var = _Var(True)
        self.include_spacing_var = _Var(True)
        self._결과목록 = [{"원본": str(Path("test-documents") / "문서.hwp"), "결과": str(Path("test-documents") / "문서(자간조정).hwpx"), "쪽수": 3}]
        self.opened = []
        self.stage_board = object()
        self.log_text = _LogText()

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
        self.assertGreaterEqual(len(public), 57)
        self.assertTrue({'cancel_zero_click', 'start_zero_click', 'quick_register_and_activate_profile'} <= public.keys())
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

    def test_format_gallery_gives_still_cut_and_name_per_format(self):
        # 키오스크식 서식 고르기: 서식마다 예시 첫 쪽 그림(data URI)과 이름을 돌려준다. 그림이 없으면 None.
        gui = _FakeGui()
        gui._서식_스틸컷 = lambda identifier, width, fmt: b'jpg' if identifier == '' else None
        items = _bridge(gui).format_gallery()
        self.assertTrue(items)
        self.assertEqual(items[0]['image'], 'data:image/jpeg;base64,anBn')
        self.assertTrue(all('name' in item and 'id' in item for item in items))
        self.assertTrue(all(item['image'] is None for item in items[1:]))

    def test_state_lists_stages_profiles_and_options(self):
        state = _bridge(_FakeGui()).get_state()
        self.assertEqual([item["key"] for item in state["stages"]],
                         [key for key, _ in stages_for_mode("spacing")])
        self.assertFalse(state["default_saved"])
        self.assertEqual(state["options"], {
            "autoclose": True, "unify_result_window": False, "verify": False,
            "integrity_report_file": False, "final_review_file": False, "log_file": False,
            "check_updates": True, "developer_mode": False, "always_on_top": True,
        })
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

    def test_removed_tools_rejected_even_in_developer_mode(self):
        gui = _FakeGui()
        gui._텍스트로_문서추가_열기 = lambda: None
        gui.developer_mode_var = _Var(True)
        bridge = _bridge(gui)
        for name in ("review", "proofread", "outline", "writing", "markdown", "advanced", "polish"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "지원하지 않는"):
                bridge.run_tool(name)

    def test_text_input_fallback_remains_available_without_developer_mode(self):
        gui = _FakeGui()
        called = []
        gui._텍스트로_문서추가_열기 = lambda: called.append(True)
        gui.developer_mode_var = _Var(False)
        gui.ui_tk_fallback_var = _Var(True)
        self.assertTrue(_bridge(gui).run_tool("paste"))
        self.assertEqual(called, [True])

    def test_document_tool_bridge_rejects_deleted_commands_and_keeps_conversion(self):
        from types import SimpleNamespace
        from docfit_app.settings_service import SettingsService
        with tempfile.TemporaryDirectory() as folder:
            gui = _FakeGui()
            gui._준말_서비스 = lambda: SimpleNamespace(settings=SettingsService(Path(folder)/"settings.json"))
            bridge = _bridge(gui)
            for name in ("review", "proofread", "proofread_apply", "numbers", "markdown", "prompt", "prompts",
                         "outline", "outline.load", "outline.save", "outline.export", "outline.filter",
                         "outline.move", "outline.toggle", "outline.note", "outline.indent", "outline.outdent",
                         "advanced", "advanced.start", "advanced.poll", "writing"):
                with self.subTest(name=name):
                    result = bridge.document_tool(name, {})
                    self.assertFalse(result["ok"])
                    self.assertEqual(result["error"]["code"], "INVALID_TOOL")
                    self.assertIn("지원하지 않는", result["error"]["message"])
            result = bridge.document_tool("convert", {"text": "# 제목\n- 항목"})
            self.assertTrue(result["ok"])
            self.assertIn("제목", result["data"]["text"])
            self.assertNotIn("#", result["data"]["text"])

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

    def test_log_is_read_on_demand_and_clear_is_blocked_during_job(self):
        gui = _FakeGui()
        bridge = _bridge(gui)
        gui.log_text.value = "첫 줄\n둘째 줄"
        self.assertEqual(bridge.get_log(), "첫 줄\n둘째 줄")
        self.assertEqual(bridge.clear_log(), "")
        gui.log_text.value = "진행 중 기록"
        gui.running = True
        self.assertEqual(bridge.clear_log(), "진행 중 기록")

    def test_flutter_record_settings_update_saved_variables_and_lock_while_running(self):
        gui = _FakeGui()
        bridge = _bridge(gui)
        for option in ("log_file", "integrity_report_file", "final_review_file"):
            state = bridge.set_option(option, True)
            self.assertTrue(state["options"][option])
        self.assertTrue(gui.log_file_var.get())
        self.assertTrue(gui.integrity_report_file_var.get())
        self.assertTrue(gui.final_review_file_var.get())
        gui.running = True
        bridge.set_option("log_file", False)
        self.assertTrue(gui.log_file_var.get())

    def test_page_fit_card_runs_page_fit_only_and_keeps_spacing_card_options(self):
        gui = _FakeGui()
        gui.spacing_enabled_var, gui.spacing_page_fit_var = _Var(True), _Var(False)
        gui.page_range_var = _Var(False)
        gui._범위_상태_갱신 = lambda: None
        seen = []
        gui.작업시작 = lambda mode: seen.append((mode, gui.spacing_enabled_var.get(), gui.spacing_page_fit_var.get()))
        bridge = _bridge(gui)
        bridge.get_state = lambda: {'mode': 'pagefit' if bridge._page_fit_card and gui.selected_mode.get() == 'spacing' else gui.selected_mode.get()}
        self.assertEqual(bridge.set_mode('pagefit')['mode'], 'pagefit')
        self.assertEqual(gui.selected_mode.get(), 'spacing')
        bridge._start_legacy('pagefit')
        # 실행할 때만 '자간 끔·쪽 맞춤 켬'이고, 자간 정리 카드 설정은 그대로 돌아온다.
        self.assertEqual(seen, [('spacing', False, True)])
        self.assertEqual((gui.spacing_enabled_var.get(), gui.spacing_page_fit_var.get()), (True, False))
        self.assertEqual(bridge.set_mode('spacing')['mode'], 'spacing')
        with self.assertRaises(ValueError):
            bridge.set_mode('page_fit')

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

    def test_file_format_mode_supports_kordoc_inputs_and_pdf_output(self):
        gui = _FakeGui()
        bridge = _bridge(gui)
        bridge._conversion_prerequisites = lambda: {
            "kordoc": {"available": True, "reason": "kordoc 4.24.9 설치 확인"},
            "pandoc": True,
            "hwp_com": True,
        }
        gui.files = [str(Path("report.xlsx"))]
        state = bridge.set_mode("file_format")
        self.assertEqual(state["mode"], "file_format")
        self.assertEqual(state["stages"], [])
        self.assertTrue(state["can_start"])
        self.assertEqual(state["conversion_target"], "hwpx")
        self.assertTrue(bridge.set_conversion_target("pdf")["can_start"])
        gui.files = [str(Path("report.hwpx"))]
        self.assertTrue(bridge.get_state()["can_start"])
        called = []
        gui.파일포맷_변경_시작 = lambda target: called.append(target)
        bridge.start("file_format")
        self.assertEqual(called, ["pdf"])

    def test_html_can_be_selected_as_input_and_output_format(self):
        gui = _FakeGui()
        gui.files = [str(Path("report.html"))]
        bridge = _bridge(gui)
        bridge._conversion_prerequisites = lambda: {
            "kordoc": {"available": True, "reason": "kordoc ready"},
            "pandoc": True,
            "hwp_com": True,
            "ocr": True,
        }
        bridge.set_mode("file_format")
        targets = {item["format"]: item for item in bridge.get_state()["conversion_targets"]}
        self.assertFalse(targets["html"]["enabled"])
        self.assertIn("같은 형식", targets["html"]["reason"])
        self.assertTrue(targets["docx"]["enabled"])
        self.assertTrue(targets["epub"]["enabled"])
        gui.files.append(str(Path("report.md")))
        targets = {item["format"]: item for item in bridge.get_state()["conversion_targets"]}
        self.assertTrue(targets["html"]["enabled"])
        self.assertTrue(bridge.set_conversion_target("html")["can_start"])

    def test_file_format_rejects_unsupported_target_and_normal_mode_input(self):
        gui = _FakeGui()
        bridge = _bridge(gui)
        bridge._conversion_prerequisites = lambda: {
            "kordoc": {"available": True, "reason": "kordoc 4.24.9 설치 확인"},
            "pandoc": False,
            "hwp_com": True,
        }
        gui.files = [str(Path("archive.zip"))]
        bridge.set_mode("file_format")
        self.assertFalse(bridge.get_state()["can_start"])
        with self.assertRaises(ValueError):
            bridge.set_conversion_target("mp3")
        bridge.set_mode("spacing")
        self.assertFalse(bridge.get_state()["can_start"])

    def test_file_conversion_preflight_disables_missing_dependencies_with_reason(self):
        gui = _FakeGui()
        gui.files = [str(Path("report.xlsx"))]
        bridge = _bridge(gui)
        bridge._conversion_prerequisites = lambda: {
            "kordoc": {"available": False, "reason": "kordoc 4.24.9 설치 필요 (Node.js 20+)"},
            "pandoc": False,
            "hwp_com": True,
        }
        state = bridge.set_mode("file_format")
        self.assertFalse(state["can_start"])
        targets = {target["format"]: target for target in state["conversion_targets"]}
        self.assertFalse(targets["hwpx"]["enabled"])
        self.assertIn("kordoc 4.24.9 설치 필요", targets["hwpx"]["reason"])
        self.assertFalse(targets["pdf"]["enabled"])
        self.assertIn("kordoc 4.24.9 설치 필요", targets["pdf"]["reason"])
        self.assertFalse(targets["docx"]["enabled"])

    def test_hwpx_pdf_needs_no_kordoc_node_or_pandoc(self):
        gui = _FakeGui()
        gui.files = ["report.hwpx", "second.HWPX"]
        bridge = _bridge(gui)
        bridge._conversion_prerequisites = lambda: {
            "kordoc": {"available": False, "reason": "Node.js 설치 필요"},
            "pandoc": False,
            "hwp_com": True,
        }
        bridge.set_mode("file_format")
        state = bridge.set_conversion_target("pdf")
        self.assertTrue(state["can_start"])
        pdf = next(item for item in state["conversion_targets"] if item["format"] == "pdf")
        self.assertIn("추가 변환기 설치 없음", pdf["reason"])
        gui.files.append("sheet.xlsx")
        self.assertFalse(bridge.get_state()["can_start"])
        gui.files = ["report.hwpx"]
        bridge._conversion_prerequisites = lambda: {
            "kordoc": {"available": False, "reason": "Node.js 설치 필요"},
            "pandoc": False,
            "hwp_com": False,
        }
        self.assertFalse(bridge.get_state()["can_start"])

    def test_conversion_preflight_runs_outside_tk_callback(self):
        gui = _FakeGui()
        gui.files = ["report.hwpx"]
        gui.selected_mode.set("file_format")
        bridge = _bridge(gui)
        in_tk = [False]

        def tk(callback):
            in_tk[0] = True
            try:
                return callback()
            finally:
                in_tk[0] = False

        def prerequisites():
            self.assertFalse(in_tk[0])
            return {"kordoc": {"available": False}, "pandoc": False, "hwp_com": True}

        bridge._tk = tk
        bridge._conversion_prerequisites = prerequisites
        self.assertTrue(bridge.set_conversion_target("pdf")["can_start"])

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
        gui.unify_quick_mode_var = _Var(True)
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
        gui.unify_quick_mode_var = _Var(True)
        bridge = _bridge(gui)
        self.assertEqual(bridge.get_state()["card_options"],
                         {"spacing_enabled": True, "spacing_page_fit": False,
                          "all_exclude_pagefit": False, "all_linespacing": True, "unify_exclude_tables": False,
                          "unify_exclude_spacing": False, "unify_exclude_pagefit": False,
                          "unify_keep_layout": False, "unify_quick_mode": True})
        gui.all_linespacing_var = _Var(True)
        state = bridge.set_card_option("all_linespacing", False)
        self.assertEqual((state["mode"], state["card_options"]["all_linespacing"]), ("all", False))
        for name in ("all_exclude_pagefit_var", "unify_exclude_tables_var", "unify_exclude_spacing_var",
                     "unify_exclude_pagefit_var"):
            setattr(gui, name, _Var(False))
        state = bridge.set_card_option("unify_quick_mode", False)
        self.assertEqual((state["mode"], state["card_options"]["unify_quick_mode"]), ("unify", False))
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
        import tempfile
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        sample_0 = str(Path(temporary.name) / "sample_0.txt")
        Path(sample_0).write_bytes(b"sample")
        sample_1 = str(Path(temporary.name) / "sample_1.hwpx")
        Path(sample_1).write_bytes(b"sample")
        sample_2 = str(Path(temporary.name) / "sample_2.hwp")
        Path(sample_2).write_bytes(b"sample")
        sample_3 = str(Path(temporary.name) / "sample_3.hwpx")
        Path(sample_3).write_bytes(b"sample")
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
        bridge.receive_drop([sample_0, sample_1, sample_2])
        self.assertEqual(started, [(sample_1, False)])
        self.assertEqual(added, [])
        bridge.receive_drop([sample_0])
        self.assertIn("HWP 또는 HWPX", gui.status_var.get())
        bridge.set_drop_target("documents")
        bridge.receive_drop([sample_3])
        self.assertEqual(added, [sample_3])
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
        self.assertEqual(gui.opened, [str(Path("test-documents") / "문서(자간조정).hwpx")])
        bridge.open_result(5)
        self.assertIn("찾을 수 없습니다", gui.status_var.get())
        with mock.patch("desktop_web_ui.os.path.isfile", return_value=True), \
                mock.patch("desktop_web_ui.os.name", "nt"), \
                mock.patch("desktop_web_ui.subprocess.Popen") as popen:
            bridge.show_result(0)
        self.assertEqual(popen.call_args.args[0][:2], ["explorer", "/select,"])


    def test_open_settings_stages_log_return_flutter_only_by_default(self):
        gui = _FakeGui()
        gui.설정창_열기 = mock.Mock()
        gui._세부작업_열기 = mock.Mock()
        gui.log_window = mock.Mock()
        gui.log_window.deiconify = mock.Mock()
        gui.log_window.lift = mock.Mock()

        bridge = _bridge(gui)

        res_settings = bridge.open_settings()
        self.assertEqual(res_settings, {"ok": False, "error": "FLUTTER_ONLY"})
        gui.설정창_열기.assert_not_called()

        res_stages = bridge.open_stages()
        self.assertEqual(res_stages, {"ok": False, "error": "FLUTTER_ONLY"})
        gui._세부작업_열기.assert_not_called()

        res_log = bridge.open_log()
        self.assertEqual(res_log, {"ok": False, "error": "FLUTTER_ONLY"})
        gui.log_window.deiconify.assert_not_called()
        gui.log_window.lift.assert_not_called()

    def test_open_settings_stages_log_with_ui_tk_fallback_enabled(self):
        gui = _FakeGui()
        gui.설정창_열기 = mock.Mock()
        gui._세부작업_열기 = mock.Mock()
        gui.log_window = mock.Mock()
        gui.log_window.deiconify = mock.Mock()
        gui.log_window.lift = mock.Mock()
        gui.ui_tk_fallback_var = _Var(True)

        bridge = _bridge(gui)

        res_settings = bridge.open_settings()
        self.assertTrue(res_settings)
        gui.설정창_열기.assert_called_once()

        res_stages = bridge.open_stages()
        self.assertTrue(res_stages)
        gui._세부작업_열기.assert_called_once()

        res_log = bridge.open_log()
        self.assertTrue(res_log)
        gui.log_window.deiconify.assert_called_once()
        gui.log_window.lift.assert_called_once()


if __name__ == '__main__':
    unittest.main()
