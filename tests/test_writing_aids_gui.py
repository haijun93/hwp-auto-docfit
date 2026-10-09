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

                    # 작업 카드 3장: 자간 정리(+ 기존 자간 초기화·표 제외) / 서식 통일(+ 표 제외·자간 정리 제외·
                    # 페이지 맞춤 제외) / 한 번에 적용(+ 자간 조정 포함·표 제외·페이지 맞춤 제외)
                    self.assertEqual([b.cget("text") for b in app.mode_buttons],
                                     ["자간 정리", "기존 자간 초기화", "표 제외",
                                      "서식 통일", "표 제외", "자간 정리 제외", "페이지 맞춤 제외", "원본 쪽 구성 유지",
                                      "한 번에 적용", "자간 조정 포함", "표 제외", "페이지 맞춤 제외"])
                    for 이름 in ("all_exclude_pagefit_var", "unify_exclude_tables_var", "unify_exclude_spacing_var"):
                        self.assertFalse(getattr(app, 이름).get(), 이름)       # 기본 꺼짐
                    # 서식 통일의 쪽 맞춤은 세부 작업 기본값이 꺼짐이라 '페이지 맞춤 제외'가 켜져 보인다(세부 작업과 연동).
                    self.assertTrue(app.unify_exclude_pagefit_var.get())
                    self.assertFalse(app.stage_choices["unify"]["page_fit"])
                    # '표 제외'는 기본 꺼짐. 켜면 한 번에 적용 카드를 고르고 요약에 알리며 설정에 저장한다.
                    self.assertFalse(app.exclude_tables_var.get())
                    app.exclude_tables_var.set(True)
                    app._표제외_변경()
                    self.assertIn(app.selected_mode.get(), ("all", "format"))
                    self.assertIn("표 제외", app.options_summary.cget("text"))
                    self.assertNotIn("세부 작업", app.options_summary.cget("text"))   # 카드 옵션으로 끈 작업은 따로 세지 않는다
                    self.assertTrue(ns["설정_불러오기"]()["all_exclude_tables"])
                    # 세부 작업 연동: 두 구성(자간 조정 포함 all·제외 format)의 표 관련 작업이 바로 꺼진다.
                    for 유형 in ("all", "format"):
                        self.assertTrue(all(not 값 for 키, 값 in app.stage_choices[유형].items()
                                            if 키 in ns["표작업_키목록"]), 유형)
                    self.assertTrue(app.stage_choices["all"]["pre_format"])   # 제목·개요 서식 표는 그대로
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
                    self.assertIsNot(args[25].get("page_fit"), False)  # 페이지 맞춤 제외는 꺼져 있다
                    app.running = False
                    app.exclude_tables_var.set(False)
                    self.assertNotIn("표 제외", app.options_summary.cget("text"))
                    self.assertTrue(app.stage_choices["all"]["table_style"] and app.stage_choices["all"]["control_spacing"])
                    self.assertTrue(app.stage_choices["format"]["table_width"])
                    # 반대로 세부 작업에서 표 작업을 모두 끄면 '표 제외'가 켜지고 다른 구성의 표 작업도 끈다.
                    app._카드_클릭("all")
                    for 키 in ns["표작업_키목록"]:
                        if 키 in app.stage_choices["all"]:
                            app.stage_choices["all"][키] = False
                    app._세부작업_옵션_맞춤("all")
                    self.assertTrue(app.exclude_tables_var.get())
                    self.assertFalse(app.stage_choices["format"]["table_style"])
                    # 표 작업을 하나라도 켜면 '표 제외'가 꺼지고, 사용자가 끈 나머지 작업은 그대로 둔다.
                    app.stage_choices["all"]["table_width"] = True
                    app._세부작업_옵션_맞춤("all")
                    self.assertFalse(app.exclude_tables_var.get())
                    self.assertFalse(app.stage_choices["all"]["table_style"])
                    app.exclude_tables_var.set(True)
                    app.exclude_tables_var.set(False)                    # 표 작업을 모두 다시 켠다
                    self.assertTrue(app.stage_choices["all"]["table_style"])
                    # 한 번에 적용의 '페이지 맞춤 제외': 문단 아래 간격 페이지 맞춤·관련 문단 페이지 배치를 끈다.
                    app.all_exclude_pagefit_var.set(True)
                    app._표제외_변경()
                    self.assertIn("페이지 맞춤 제외", app.options_summary.cget("text"))
                    for 유형 in ("all", "format"):
                        self.assertEqual((app.stage_choices[유형]["page_fit"], app.stage_choices[유형]["page_group"]),
                                         (False, False), 유형)
                    with patch.object(threading, "Thread", _Thread):
                        app.작업시작(app.selected_mode.get())
                    args = captured["args"]
                    self.assertEqual((args[25]["page_fit"], args[25]["page_group"]), (False, False))
                    self.assertTrue(args[22])                        # 표는 그대로
                    app.running = False
                    app.all_exclude_pagefit_var.set(False)
                    self.assertTrue(app.stage_choices["all"]["page_group"])
                    self.assertTrue(ns["설정_불러오기"]()["unify_exclude_tables"] is False)
                    # 서식 통일 카드: 표 제외·자간 정리 제외·페이지 맞춤 제외
                    app.unify_exclude_tables_var.set(True)
                    app.unify_exclude_spacing_var.set(True)
                    app.unify_exclude_pagefit_var.set(True)
                    app._카드옵션_변경("unify")
                    self.assertEqual(app.selected_mode.get(), "unify")
                    summary = app.options_summary.cget("text")
                    for 문구 in ("표 제외", "자간 정리 제외", "페이지 맞춤 제외"):
                        self.assertIn(문구, summary)
                    self.assertTrue(ns["설정_불러오기"]()["unify_exclude_spacing"])
                    # 세부 작업 연동: 기본 표 서식·표 서식통일·서식통일 문장 자간 정리·쪽 맞춤이 꺼진다.
                    for 키 in ("table_style", "table_unify", "unify_spacing", "page_fit"):
                        self.assertFalse(app.stage_choices["unify"][키], 키)
                    self.assertTrue(app.stage_choices["unify"]["style_unify"])
                    with patch.object(threading, "Thread", _Thread):
                        app.작업시작("unify")
                    args = captured["args"]
                    self.assertEqual(args[18], "unify")
                    self.assertEqual((args[25]["table_style"], args[25]["table_unify"], args[25]["page_fit"]),
                                     (False, False, False))
                    self.assertTrue(args[25]["style_unify"])
                    self.assertTrue(args[13]["unify_exclude_spacing"])  # 서식통일 자간 조정 끔
                    app.running = False
                    app.버튼_대기중()                                   # 작업이 끝난 것처럼 카드 버튼을 다시 켠다
                    for 이름 in ("unify_exclude_tables_var", "unify_exclude_spacing_var", "unify_exclude_pagefit_var"):
                        getattr(app, 이름).set(False)
                    for 키 in ("table_style", "table_unify", "unify_spacing", "page_fit"):
                        self.assertTrue(app.stage_choices["unify"][키], 키)
                    # 세부 작업 '서식통일 문장 자간 정리'를 끄면 '자간 정리 제외'가 켜지고, 실행 때 자간 조정을 끈다.
                    app.stage_choices["unify"]["unify_spacing"] = False
                    app._세부작업_옵션_맞춤("unify")
                    self.assertTrue(app.unify_exclude_spacing_var.get())
                    self.assertFalse(app.unify_exclude_tables_var.get())
                    with patch.object(threading, "Thread", _Thread):
                        app.작업시작("unify")
                    self.assertTrue(captured["args"][13]["unify_exclude_spacing"])
                    app.running = False
                    app.버튼_대기중()
                    app.unify_exclude_spacing_var.set(False)
                    self.assertTrue(app.stage_choices["unify"]["unify_spacing"])
                    # 자간 정리의 '표 제외'는 설정 table_spacing(표 안 문장 자간조정)의 반대 값이고 기본은 꺼짐이다.
                    self.assertTrue(app.table_spacing_var.get())
                    self.assertEqual(app.table_spacing_card_check.cget("text"), "표 제외")
                    app._카드_클릭("all")
                    app.table_spacing_card_check.invoke()             # '표 제외' 켬
                    self.assertFalse(app.table_spacing_var.get())
                    self.assertEqual(app.selected_mode.get(), "spacing")
                    self.assertIn("표 제외", app.options_summary.cget("text"))
                    self.assertFalse(ns["설정_불러오기"]()["table_spacing"])
                    # 세부 작업 연동: 표·컨트롤 자간 조정·줄 병합·단어 검사가 꺼진다(한 번에 적용은 따로 둔다).
                    for 키 in ("control_spacing", "control_short_line", "control_word_check"):
                        self.assertFalse(app.stage_choices["spacing"][키], 키)
                    self.assertTrue(app.stage_choices["all"]["control_spacing"])
                    app.table_spacing_card_check.invoke()             # 다시 끔
                    self.assertTrue(app.table_spacing_var.get())
                    self.assertNotIn("표 제외", app.options_summary.cget("text"))
                    self.assertTrue(ns["설정_불러오기"]()["table_spacing"])
                    self.assertTrue(app.stage_choices["spacing"]["control_word_check"])
                    # 세부 작업에서 표·컨트롤 작업을 모두 끄면 '표 제외'가 켜진다.
                    for 키 in ("control_spacing", "control_short_line", "control_word_check"):
                        app.stage_choices["spacing"][키] = False
                    app._세부작업_옵션_맞춤("spacing")
                    self.assertFalse(app.table_spacing_var.get())
                    app.table_spacing_var.set(True)
                    self.assertTrue(app.stage_choices["spacing"]["control_spacing"])
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
                    # 서식통일 '작업 결과 확인' 창은 기본 꺼짐이고, 켜면 바로 반영·저장된다.
                    self.assertFalse(app.unify_result_window_var.get())
                    app.unify_result_window_var.set(True)
                    self.assertTrue(ns["설정_불러오기"]()["unify_result_window"])
                    app.unify_result_window_var.set(False)
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
                    self.assertFalse(app.stage_choices["all"]["body_spacing"])   # all 구성의 자간 작업도 끈다
                    app._카드_클릭("spacing")
                    app._카드_클릭("all")
                    self.assertEqual(app.selected_mode.get(), "format")   # 선택을 기억한다
                    self.assertFalse(ns["설정_불러오기"]()["all_include_spacing"])
                    app.include_spacing_var.set(True)
                    app._자간포함_변경()
                    self.assertEqual(app.selected_mode.get(), "all")
                    자간작업 = ns["카드옵션_세부작업"]["all_include_spacing"][1]
                    self.assertTrue(all(app.stage_choices["all"][키] for 키 in 자간작업))
                    # 한 번에 적용에서 자간 작업을 모두 끄면 '자간 조정 포함'이 꺼지고 서식 적용(format)으로 바뀐다.
                    for 키 in 자간작업:
                        app.stage_choices["all"][키] = False
                    app._세부작업_옵션_맞춤("all")
                    self.assertEqual((app.include_spacing_var.get(), app.selected_mode.get()), (False, "format"))
                    app.include_spacing_var.set(True)
                    app._자간포함_변경()
                    self.assertTrue(all(app.stage_choices["all"][키] for 키 in 자간작업))
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
