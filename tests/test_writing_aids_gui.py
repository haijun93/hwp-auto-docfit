"""작성 도우미·AI 프롬프트 창과 기관 서식 표시(A3) GUI 스모크 테스트."""
from pathlib import Path
import os
import runpy
import tempfile
import unittest
from unittest.mock import patch


class WritingAidsGuiTest(unittest.TestCase):
    def test_windows_open_and_buttons_work(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        with tempfile.TemporaryDirectory(prefix="hwp-docfit-aids-") as folder:
            with patch.dict(os.environ, {"APPDATA": folder}):
                ns = runpy.run_path(str(source), run_name="aids_ui_test")
                root = ns["TkinterDnD"].Tk()
                root.withdraw()
                errors = []
                root.report_callback_exception = lambda *args: errors.append(args)
                try:
                    app = ns["HwpAutoDocFitGUI"](root)
                    app._작성도우미_열기()
                    root.update()
                    tabs = app._작성도우미_탭
                    names = [tabs.tab(t, "text") for t in tabs.tabs()]
                    self.assertEqual(names, ["금액·숫자", "날짜", "표 계산", "나이·주민번호", "번호", "회신공문", "기관 서식"])
                    src, dst, commands = app._작성도우미_입출력["금액·숫자"]
                    src.insert("1.0", "예산 1,500,000원")
                    commands["한글 금액 병기"]()
                    self.assertEqual(dst.get("1.0", "end-1c"), "예산 금1,500,000원(금일백오십만원)")
                    src, dst, commands = app._작성도우미_입출력["날짜"]
                    src.insert("1.0", "2025. 7. 1.")
                    commands["이번 달 금요일"]()
                    self.assertTrue(dst.get("1.0", "end-1c").startswith("2025. 7. 4.(금)"))
                    src, dst, commands = app._작성도우미_입출력["표 계산"]
                    src.insert("1.0", "구분\t값\n가\t1\n나\t2")
                    commands["열 합계"]()
                    self.assertTrue(dst.get("1.0", "end-1c").endswith("합계\t3"))
                    values, output, make = app._작성도우미_회신
                    values["title"].set("자료 제출 요청")
                    make()
                    self.assertIn("끝.", output.get("1.0", "end-1c"))

                    app._AI_프롬프트_열기(root)
                    root.update()

                    # 작업 카드 3장: 자간 정리(+ 기존 자간 초기화·표 내 자간 정리) / 서식 통일 / 한 번에 적용(+ 자간 조정 포함)
                    self.assertEqual([b.cget("text") for b in app.mode_buttons],
                                     ["자간 정리", "기존 자간 초기화", "표 내 자간 정리", "서식 통일", "한 번에 적용",
                                      "자간 조정 포함", "표 제외"])
                    # '표 제외'는 기본 꺼짐. 켜면 한 번에 적용 카드를 고르고 요약에 알리며 설정에 저장한다.
                    self.assertFalse(app.exclude_tables_var.get())
                    app.exclude_tables_var.set(True)
                    app._표제외_변경()
                    self.assertIn(app.selected_mode.get(), ("all", "format"))
                    self.assertIn("표 제외", app.options_summary.cget("text"))
                    self.assertTrue(ns["설정_불러오기"]()["all_exclude_tables"])
                    # 실행하면 표 관련 세부 작업을 모두 끄고 표 칸 안 문장도 자간 작업에서 뺀다.
                    import threading
                    captured = {}

                    class _Thread:
                        def __init__(self, target=None, args=(), daemon=None):
                            captured["args"] = args

                        def start(self):
                            pass

                    app.files = [str(Path(folder) / "문서.hwpx")]
                    with patch.object(threading, "Thread", _Thread):
                        app.작업시작(app.selected_mode.get())
                    args = captured["args"]
                    self.assertFalse(args[22])                       # 표자간조정
                    self.assertTrue(all(args[25][k] is False for k in ns["표작업_키목록"]))
                    app.running = False
                    app.exclude_tables_var.set(False)
                    self.assertNotIn("표 제외", app.options_summary.cget("text"))
                    # '표 내 자간 정리'는 설정 table_spacing(표 안 문장 자간조정)과 같은 값이고 기본은 켜짐이다.
                    self.assertTrue(app.table_spacing_var.get())
                    app._카드_클릭("all")
                    app.table_spacing_var.set(False)
                    app._자간초기화_변경()
                    self.assertEqual(app.selected_mode.get(), "spacing")
                    self.assertIn("표 안 문장 제외", app.options_summary.cget("text"))
                    self.assertFalse(ns["설정_불러오기"]()["table_spacing"])
                    app.table_spacing_var.set(True)
                    self.assertNotIn("표 안 문장 제외", app.options_summary.cget("text"))
                    self.assertTrue(ns["설정_불러오기"]()["table_spacing"])
                    # 설정창 '제목 부제 크기'는 기본 15pt이고, 바꾸면 바로 반영·저장된다.
                    부제 = app.std_parspace_vars["std_title_subtitle_pt"]
                    self.assertEqual(부제.get(), "15")
                    부제.set("18")
                    self.assertEqual(ns["제목_부제_크기_반영"].__globals__["제목_부제_크기_pt"], 18)
                    self.assertEqual(ns["설정_불러오기"]()["std_title_subtitle_pt"], "18")
                    부제.set("15")
                    # 설정창 '제목 표 담당자 칸(B2) 글'은 기본 빈 글이고, 바꾸면 바로 반영·저장된다.
                    self.assertEqual(app.title_owner_var.get(), "")
                    app.title_owner_var.set("기획예산과 홍길동(2345)")
                    self.assertEqual(ns["제목_담당자_글_반영"].__globals__["제목_담당자_글"], "기획예산과 홍길동(2345)")
                    self.assertEqual(ns["설정_불러오기"]()["title_owner_text"], "기획예산과 홍길동(2345)")
                    app.title_owner_var.set("")
                    # '기존 자간 초기화'는 자간 정리 세부 작업 01과 같은 값이고 설정 파일에 저장된다.
                    app._카드_클릭("all")
                    app.reset_spacing_var.set(False)
                    app._자간초기화_변경()
                    self.assertEqual(app.selected_mode.get(), "spacing")
                    self.assertFalse(app.stage_choices["spacing"]["reset_spacing"])
                    self.assertTrue(app.stage_choices["all"]["reset_spacing"])
                    self.assertFalse(ns["설정_불러오기"]()["spacing_reset_existing"])
                    self.assertIn("기존 자간을 초기화하지 않고", app.options_summary.cget("text"))
                    app.stage_choices["spacing"]["reset_spacing"] = True   # 세부 작업 창에서 다시 켬
                    app._요약갱신()
                    self.assertTrue(app.reset_spacing_var.get())
                    self.assertTrue(ns["설정_불러오기"]()["spacing_reset_existing"])
                    self.assertEqual(list(app.mode_cards), ["spacing", "unify", "all"])
                    app._카드_클릭("all")
                    self.assertEqual(app.selected_mode.get(), "all")
                    # 자간 조정을 빼면 같은 카드에서 서식 적용(format)으로 실행하고 기존 자간을 둔다.
                    app.include_spacing_var.set(False)
                    app._자간포함_변경()
                    self.assertEqual((app.selected_mode.get(), app.card_mode_var.get()), ("format", "all"))
                    self.assertIn("자간 조정 제외", app.options_summary.cget("text"))
                    app._카드_클릭("spacing")
                    app._카드_클릭("all")
                    self.assertEqual(app.selected_mode.get(), "format")   # 선택을 기억한다
                    self.assertFalse(ns["설정_불러오기"]()["all_include_spacing"])
                    app.include_spacing_var.set(True)
                    app._자간포함_변경()
                    self.assertEqual(app.selected_mode.get(), "all")
                    app._빠른설정("report")
                    app._카드_클릭("unify")  # 빠른 선택 해제가 서식 통일 모드 자체를 끄면 안 된다
                    self.assertEqual(app.selected_mode.get(), "unify")
                    self.assertTrue(app.stage_choices["unify"]["style_unify"])
                    self.assertFalse(app.stage_choices["spacing"]["style_unify"])
                    self.assertIn("문서에서 많이 쓰인", app.options_summary.cget("text"))

                    # 기관을 붙인 서식은 '[기관] 이름'으로 보이고 기관별로 묶인다.
                    base = app._프로파일들[""]
                    app._프로파일들["b"] = dict(base, name="보도자료", organization="마포구")
                    app._프로파일들["a"] = dict(base, name="개인 서식")
                    app._프로파일_목록갱신()
                    shown = list(app.main_profile_combo["values"])
                    self.assertEqual(shown[0], base["name"])
                    self.assertEqual(shown[1:], ["[마포구] 보도자료", "개인 서식"])
                    self.assertEqual(app._프로파일_ids, ["", "b", "a"])
                finally:
                    root.destroy()
                self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
