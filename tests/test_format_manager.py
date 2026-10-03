"""서식 관리: 예시 보고서로 복제한 서식의 이름 바꾸기·삭제·세부 수정을 확인 없이 부르는 본체와 웹 화면 모드 동작."""
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch


class FormatManagerTest(unittest.TestCase):
    def test_rename_delete_and_web_mode_analysis(self):
        source = Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"
        with tempfile.TemporaryDirectory(prefix="hwp-docfit-formats-") as folder:
            with patch.dict(os.environ, {"APPDATA": folder}):
                ns = runpy.run_path(str(source), run_name="format_manager_test")
                root = ns["TkinterDnD"].Tk()
                root.withdraw()                      # 웹 화면 모드처럼 Tk 기본 창을 숨긴다
                try:
                    app = ns["HwpAutoDocFitGUI"](root)
                    root.withdraw()
                    self.assertTrue(app._웹화면_모드())
                    # 예시 보고서로 복제한 서식 둘을 만든다.
                    for identifier, name in (("p1", "보고서A"), ("p2", "보고서B")):
                        profile = ns["기본_서식프로파일"]()
                        profile["name"] = name
                        profile["source"] = {"filename": f"{name}.hwpx"}
                        app._서식_파일_저장(identifier, profile)
                        app._프로파일들[identifier] = profile
                    app._프로파일_목록갱신()
                    formats = ns["서식프로파일_폴더"]()

                    # 이름 바꾸기: 기본 서식·빈 이름·겹치는 이름은 이유를 돌려주고, 되면 파일에도 저장한다.
                    self.assertIn("기본 문서 서식", app._서식_이름_저장("", "새 이름"))
                    self.assertIn("비어 있지 않은", app._서식_이름_저장("p1", "  "))
                    self.assertIn("이미 사용 중", app._서식_이름_저장("p1", "보고서B"))
                    self.assertIsNone(app._서식_이름_저장("p1", "마포 보고서", "마포구"))
                    saved = json.loads((formats / "p1.json").read_text(encoding="utf-8"))
                    self.assertEqual((saved["name"], saved["organization"]), ("마포 보고서", "마포구"))
                    self.assertIsNone(app._서식_이름_저장("p1", "마포 보고서", ""))
                    self.assertNotIn("organization", json.loads((formats / "p1.json").read_text(encoding="utf-8")))

                    # 삭제: 기본 서식은 안 되고, 쓰던 서식을 지우면 기본 서식으로 돌아간다.
                    self.assertIn("기본 문서 서식", app._서식_삭제(""))
                    app._활성_서식_프로파일 = "p2"
                    self.assertIsNone(app._서식_삭제("p2"))
                    self.assertFalse((formats / "p2.json").exists())
                    self.assertNotIn("p2", app._프로파일들)
                    self.assertEqual(app._활성_서식_프로파일, "")
                    app.running = True
                    self.assertIn("작업 중", app._서식_삭제("p1"))
                    app.running = False

                    # 웹 화면에서 분석을 시작하고, 실패는 숨은 Tk 창의 안내 상자 대신 상태 문구로 알린다.
                    with patch.dict(app._서식_분석_시작.__globals__,
                                    {"한글파일_서식_분석": lambda path: (_ for _ in ()).throw(RuntimeError("분석 실패"))}):
                        app._서식_분석_시작(str(Path(folder) / "예시.hwpx"))
                        self.assertTrue(app._서식분석중)
                        self.assertEqual(app._서식분석_파일, "예시.hwpx")
                    with patch.object(ns["messagebox"], "showerror",
                                      side_effect=AssertionError("웹 화면에서 숨은 안내 상자를 띄움")):
                        app._서식_복사완료(error="분석 실패")
                    self.assertFalse(app._서식분석중)
                    self.assertIn("분석 실패", app.status_var.get())
                    # 없는 서식은 세부 수정하지 않는다.
                    app._서식_수정하기("없는서식")
                finally:
                    root.destroy()


if __name__ == "__main__":
    unittest.main()
