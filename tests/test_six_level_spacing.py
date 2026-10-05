"""계층별 문단 위 여백 기본값: 2~4단계(장·중제목·□) 15 · 5단계(ㅇ) 8 · 6단계(-) 4 · 그 밖 0(2026-10-05)."""
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from docfit_core.document_rules import ParagraphSpacingTracker, paragraph_level

BASE = {"chapter": 15, "midtitle": 15, "box": 15, "circle": 8, "dash": 4, "note": 0}


class SixLevelSpacingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"))

    def test_levels(self):
        for text, level in (("제1장 개요", "chapter"), ("2장 계획", "chapter"), ("Chapter 3 결론", "chapter"),
                            ("Ⅰ. 추진 배경", "midtitle"), ("Ⅱ 추진 계획", "midtitle"), ("□ 가", "box"),
                            ("ㅇ 나", "circle"), ("- 다", "dash"), ("※ 라", "note"), ("일반 문장", None)):
            self.assertEqual(paragraph_level(text), level, text)

    def test_heading_levels_keep_their_value_without_return_multiplier(self):
        t = ParagraphSpacingTracker()
        got = [t.spacing_for(s, BASE) for s in ("제1장 개요", "Ⅰ. 배경", "□ 가", "ㅇ 나", "- 다", "* 라",
                                                "ㅇ 마", "□ 바", "Ⅱ 계획", "제2장 x")]
        self.assertEqual(got, [15, 15, 15, 8, 4, 0, 12, 22, 15, 15])
        self.assertEqual(t.spacing_for_level("midtitle", BASE), 15)     # 표 첫 칸 로마자 중제목 표

    def test_app_defaults(self):
        defaults = self.ns["기본_설정"]
        keys = ("std_parspace_chapter", "std_parspace_midtitle", "std_parspace_box",
                "std_parspace_circle", "std_parspace_dash", "std_parspace_note")
        self.assertEqual([defaults[k] for k in keys], ["15", "15", "15", "8", "4", "0"])
        self.assertEqual(self.ns["_표준서식_문단위간격_표"](), BASE)

    def test_default_profile_review_rows_have_all_levels_and_spacing(self):
        rows = self.ns["기본_계층_스타일"](self.ns["표준서식_설정"])
        got = {row["marker"]: (row["role"], row["prev_spacing_hwpunit"]) for row in rows}
        self.assertEqual(got["(장)"], ("장", 1500))
        self.assertEqual(got["Ⅰ"], ("중제목", 1500))
        self.assertEqual(got["□"], ("소제목", 1500))
        self.assertEqual(got["ㅇ"], ("본문", 800))
        self.assertEqual(got["-"], ("내용", 400))
        self.assertEqual(got["※"], ("부연설명", 0))
        self.assertEqual([row["role"] for row in rows][:3], ["제목", "장", "중제목"])

    def _load(self, saved):
        with tempfile.TemporaryDirectory(prefix="docfit-parspace-") as folder:
            with patch.dict(os.environ, {"APPDATA": folder}):
                path = self.ns["설정_파일_경로"]()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(saved, ensure_ascii=False), encoding="utf-8")
                return self.ns["설정_불러오기"]()

    def test_old_default_values_move_to_new_defaults(self):
        old = {"std_parspace_chapter": "20", "std_parspace_midtitle": "15", "std_parspace_box": "15",
               "std_parspace_circle": "10", "std_parspace_note": "3"}
        loaded = self._load(old)
        self.assertEqual([loaded[k] for k in old], ["15", "15", "15", "8", "0"])
        self.assertEqual(loaded["std_parspace_dash"], "4")
        self.assertEqual(loaded["std_parspace_rev"], 2)

    def test_user_changed_values_are_kept(self):
        loaded = self._load({"std_parspace_box": "12", "std_parspace_circle": "10"})
        self.assertEqual((loaded["std_parspace_box"], loaded["std_parspace_circle"]), ("12", "10"))
        # 새 판으로 저장된 값은 예전 기본값과 같아도 사용자가 고른 값이다.
        again = self._load({"std_parspace_chapter": "20", "std_parspace_circle": "10", "std_parspace_note": "3",
                            "std_parspace_rev": 2})
        self.assertEqual((again["std_parspace_chapter"], again["std_parspace_circle"]), ("20", "10"))


if __name__ == "__main__":
    unittest.main()
