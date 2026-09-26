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

                    # 작업 유형 4가지: 자간 정리 / 서식 통일 / 서식 적용 / 한 번에 적용
                    self.assertEqual([b.cget("text") for b in app.mode_buttons],
                                     ["자간 정리", "서식 통일", "서식 적용", "한 번에 적용"])
                    app._프리셋_선택("basic")
                    app._카드_클릭("unify")  # 빠른 선택 해제가 서식 통일 모드 자체를 끄면 안 된다
                    self.assertEqual(app.selected_mode.get(), "unify")
                    self.assertTrue(app.stage_choices["unify"]["style_unify"])
                    self.assertFalse(app.stage_choices["spacing"]["style_unify"])
                    self.assertIn("가장 많이 쓴", app.options_summary.cget("text"))

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
