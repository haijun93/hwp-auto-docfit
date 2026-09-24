"""Verify the Windows GUI can start without processing a document."""

import os
import base64
import io
from pathlib import Path
import runpy
import tempfile
import time
import unittest
import urllib.error
from unittest.mock import Mock, patch
from zipfile import ZIP_DEFLATED, ZipFile

from tests.test_style_profile import HEADER, SECTION


class StartupTest(unittest.TestCase):
    def test_page_group_collects_only_the_current_paragraph(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="page_group_unit_test")
        collect = namespace["보고서_본문묶음_수집"]

        class FakeHwp:
            def __init__(self):
                self.pos = (0, 10, 0)

            def GetPos(self):
                return self.pos

            def SetPos(self, *pos):
                self.pos = tuple(pos)

        fake = FakeHwp()
        actions = []

        def run(action):
            actions.append(action)
            if action == "MoveParaBegin":
                fake.pos = (0, 10, 0)
            elif action == "MoveParaEnd":
                fake.pos = (0, 10, 25)

        with patch.dict(collect.__globals__, {
            "hwp": fake,
            "hwp_run": run,
            "현재문단_텍스트": lambda: "ㅇ 본문",
            "보고서_문단역할": lambda text: "본문",
        }):
            self.assertEqual(
                collect((0, 10, 0)),
                [((0, 10, 0), (0, 10, 25), "본문")],
            )

        self.assertEqual(fake.GetPos(), (0, 10, 0))

    def test_final_save_clears_page_protection(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        text = source.read_text(encoding="utf-8")
        clear_call = text.index("if 보고서_페이지보호_전체해제() is False:",
                                text.index("# 선택한 처리 회차가 끝난 뒤"))
        save_call = text.index("저장결과 = hwp.SaveAs", clear_call)
        self.assertLess(clear_call, save_call)

    def test_title_connects_first_body_but_not_entire_section(self):
        namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))
        collect = namespace["보고서_본문묶음_수집"]
        class Document:
            pos = (0, 0, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = pos
            def run(self, action):
                _, para, _ = self.pos
                if action == 'MoveParaBegin':
                    self.pos = (0, para, 0)
                elif action == 'MoveParaEnd':
                    self.pos = (0, para, 20)
                elif action == 'MoveNextParaBegin':
                    self.pos = (0, min(para + 1, 3), 0)
        doc = Document()
        roles = ['소제목', '본문', '본문', '내용']
        with patch.dict(collect.__globals__, {
            'hwp': doc, 'hwp_run': doc.run,
            '현재문단_텍스트': lambda: roles[doc.pos[1]],
            '보고서_문단역할': lambda text: text,
        }):
            self.assertEqual([p[0][1] for p in collect((0, 0, 0))], [0, 1])
            self.assertEqual(doc.pos, (0, 0, 0))
            roles[1] = '소제목'
            self.assertEqual(len(collect((0, 0, 0))), 1)

    def test_body_group_includes_all_children_and_stops_at_next_body(self):
        namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))
        collect = namespace['보고서_본문묶음_수집']
        class Document:
            pos = (0, 0, 0)
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos)
            def run(self, action):
                _, para, _ = self.pos
                if action == 'MoveParaBegin':
                    self.pos = (0, para, 0)
                elif action == 'MoveParaEnd':
                    self.pos = (0, para, 20)
                elif action == 'MoveNextParaBegin':
                    self.pos = (0, min(para + 1, len(roles) - 1), 0)
        doc = Document()
        # □ 3안 / ㅇ 운영방식 / - 세 항목과 부연설명 / ㅇ 행정사항
        roles = ['소제목', '본문', '내용', '내용', '내용', '부연설명', '본문', '내용']
        with patch.dict(collect.__globals__, {
            'hwp': doc, 'hwp_run': doc.run,
            '현재문단_텍스트': lambda: roles[doc.pos[1]],
            '보고서_문단역할': lambda text: text,
            '중단_요청됨': lambda: False,
        }):
            self.assertEqual([p[0][1] for p in collect((0, 1, 0))], [1, 2, 3, 4, 5])
            self.assertEqual([p[0][1] for p in collect((0, 0, 0))], [0, 1, 2, 3, 4, 5])
            self.assertEqual([p[0][1] for p in collect((0, 4, 0))], [4, 5])
            roles[3] = None  # 빈 문단·무기호 문단을 넘어서 연결하지 않는다.
            self.assertEqual([p[0][1] for p in collect((0, 1, 0))], [1, 2])
        self.assertEqual(doc.GetPos(), (0, 0, 0))

    def test_hanging_indent_treats_attached_open_quote_as_body_boundary(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="hanging_indent_offset_test")
        offset = namespace["문단_내어쓰기_기준_오프셋"]

        self.assertEqual(offset(" ㅇ (개요) 본문"), 8)
        # 낫표로 시작하는 본문은 '「'이 아니라 바로 다음 글자 '공'이 기준이다.
        self.assertEqual(offset(" ㅇ (개요)「공유재산법 시행령」제75조"), 8)
        self.assertEqual(offset(" ㅇ (개요) 「공유재산법」에 따라"), 9)
        self.assertEqual(offset(" ㅇ 「공유재산법」에 따라"), 4)
        self.assertEqual(offset(" - 근거 : 『지방재정법』 제17조"), 9)
        # 다른 인용부호는 기존처럼 부호 위치가 기준이다.
        self.assertEqual(offset(" - (운영방식)“공용차량 조례”"), 9)
        # 연도 괄호가 지명에 붙은 형태는 문두 라벨로 오인하지 않는다.
        self.assertEqual(offset(" ㅇ (2026)서울"), 3)

    def test_output_filename_is_always_hwpx(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="output_filename_test")
        output_filename = namespace["저장파일명"]
        output_filename.__globals__["작업_모드"] = "spacing"
        output_filename.__globals__["쪽범위_실제"] = None

        self.assertEqual(Path(output_filename("보고서.hwp")).name, "보고서(자간조정).hwpx")
        self.assertEqual(Path(output_filename("보고서.hwpx")).name, "보고서(자간조정).hwpx")

    def test_release_version_and_exe_asset_selection(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="updater_test")
        version_tuple = namespace["_버전_튜플"]
        select_asset = namespace["_업데이트_자산_선택"]

        self.assertGreater(version_tuple("v1.67"), version_tuple("1.66"))
        preferred = {"name": "HWP_AutoDocFit.exe", "browser_download_url": "https://example.test/app.exe"}
        release = {"assets": [{"name": "notes.txt"}, preferred, {"name": "other.exe"}]}
        self.assertIs(select_asset(release), preferred)

    def test_gitlab_release_asset_is_normalized(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="gitlab_updater_test")
        select_asset = namespace["_업데이트_자산_선택"]

        release = {
            "assets": [{
                "name": "HWP_AutoDocFit.exe",
                "browser_download_url": "https://gitlab.example/releases/app.exe",
            }]
        }
        self.assertEqual(
            select_asset(release)["browser_download_url"],
            "https://gitlab.example/releases/app.exe",
        )

    def test_gitlab_without_releases_is_treated_as_up_to_date(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="no_release_updater_test")
        fetch_release = namespace["_최신_릴리스_조회"]
        not_found = urllib.error.HTTPError(
            namespace["UPDATE_API_URL"], 404, "Not Found", {}, None
        )
        self.addCleanup(not_found.close)

        with patch.object(namespace["urllib"].request, "urlopen", side_effect=not_found):
            self.assertIsNone(fetch_release())

    def test_pillow_is_available_and_embedded_cat_images_are_valid(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="pillow_test")

        image_module = namespace["Image"]
        self.assertIsNotNone(image_module)
        for variable_name in ("SETTINGS_CAT_BASE64", "MAIN_CAT_STATES_BASE64"):
            image_bytes = base64.b64decode(namespace[variable_name])
            with image_module.open(io.BytesIO(image_bytes)) as image:
                image.verify()

    def test_missing_pillow_triggers_install_and_retry(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="pillow_install_test")
        load_pillow = namespace["_load_pillow"]
        expected_modules = (object(), object(), object())
        import_pillow = Mock(side_effect=[ImportError("missing"), expected_modules])
        install_pillow = Mock()

        with patch.dict(load_pillow.__globals__, {
            "_import_pillow": import_pillow,
            "_install_pillow": install_pillow,
        }):
            self.assertEqual(load_pillow(), expected_modules)

        install_pillow.assert_called_once_with()
        self.assertEqual(import_pillow.call_count, 2)

    def test_frozen_app_never_runs_pip(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="frozen_dependency_test")
        install_pillow = namespace["_install_pillow"]
        run_command = Mock()

        with patch.object(namespace["sys"], "frozen", True, create=True), \
                patch.dict(install_pillow.__globals__, {"_run_dependency_command": run_command}):
            with self.assertRaisesRegex(RuntimeError, "PyInstaller"):
                install_pillow()

        run_command.assert_not_called()

    def test_partial_charshape_does_not_fill_unrequested_bold(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        namespace = runpy.run_path(str(source), run_name="charshape_test")

        class ParameterSet:
            def __init__(self):
                self.items = {}

            def SetItem(self, name, value):
                self.items[name] = value

        class Action:
            def __init__(self):
                self.parameters = ParameterSet()

            def CreateSet(self):
                return self.parameters

            def Execute(self, parameters):
                return True

        class FakeHwp:
            def __init__(self):
                self.action = Action()

            def CreateAction(self, name):
                self.action_name = name
                return self.action

        fake = FakeHwp()
        apply_charshape = namespace["문자모양_적용_현재선택"]
        apply_charshape.__globals__["hwp"] = fake
        apply_charshape(자간=0)
        self.assertEqual(fake.action_name, "CharShape")
        self.assertNotIn("Bold", fake.action.parameters.items)
        self.assertEqual(fake.action.parameters.items["SpacingHangul"], 0)

    def test_gui_initializes_without_callback_errors(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        with tempfile.TemporaryDirectory(prefix="hwp-docfit-test-") as settings_dir:
            with patch.dict(os.environ, {"APPDATA": settings_dir}):
                namespace = runpy.run_path(str(source), run_name="startup_test")
                self.assertEqual(namespace["APP_NAME"], "한글문서 후처리 도구")
                root = namespace["TkinterDnD"].Tk()
                root.withdraw()
                callback_errors = []
                root.report_callback_exception = lambda *args: callback_errors.append(args)
                try:
                    app = namespace["HwpAutoDocFitGUI"](root)
                    self.assertIn("한글문서 후처리 도구", root.title())
                    root.update()
                    self.assertTrue(root.winfo_children())
                    self.assertEqual(callback_errors, [])
                    self.assertIsNone(app.worker)
                    self.assertFalse(app.running)
                    self.assertTrue(app.check_updates_on_start_var.get())
                    self.assertEqual(app.main_profile_combo.get(), "기본 보고서 서식")
                    self.assertIn("HWP/HWPX", app.format_drop_label.cget("text"))
                    self.assertIn("문서 구조", app.document_review_button.cget("text"))
                finally:
                    root.destroy()

    def test_document_review_window_shows_read_only_result(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        with tempfile.TemporaryDirectory(prefix="hwp-docfit-review-") as folder:
            document = Path(folder) / "sample.hwpx"
            with ZipFile(document, "w", ZIP_DEFLATED) as archive:
                archive.writestr("Contents/header.xml", HEADER)
                archive.writestr("Contents/section0.xml", SECTION)
            before = document.read_bytes()
            with patch.dict(os.environ, {"APPDATA": folder}):
                namespace = runpy.run_path(str(source), run_name="document_review_ui_test")
                root = namespace["TkinterDnD"].Tk()
                root.withdraw()
                errors = []
                root.report_callback_exception = lambda *args: errors.append(args)
                try:
                    app = namespace["HwpAutoDocFitGUI"](root)
                    app.files = [str(document)]
                    app._문서검토_열기()
                    def trees(widget):
                        for child in widget.winfo_children():
                            if isinstance(child, namespace["ttk"].Treeview):
                                yield child
                            yield from trees(child)
                    deadline = time.monotonic() + 5
                    while time.monotonic() < deadline:
                        root.update()
                        if any(tree.get_children() for tree in trees(app._문서검토_창)):
                            break
                        time.sleep(.03)
                    self.assertFalse(errors)
                    self.assertEqual(document.read_bytes(), before)
                    self.assertTrue(app._문서검토_창.winfo_exists())
                    self.assertTrue(any(tree.get_children() for tree in trees(app._문서검토_창)))
                finally:
                    root.destroy()


if __name__ == "__main__":
    unittest.main()
