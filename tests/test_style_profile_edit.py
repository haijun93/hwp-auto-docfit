import copy
from pathlib import Path
import runpy
import unittest

from docfit_core.style_hierarchy import analyze_hierarchy
from docfit_core.style_profile_edit import apply_reviewed_styles


class StyleProfileEditTest(unittest.TestCase):
    def test_repeated_and_one_off_variants_are_visible(self):
        records = [
            {"text": text, "left": left, "indent": -20, "font": "명조",
             "size_pt": 14, "prev_spacing": 100}
            for text, left in (("□ 하나", 100), ("□ 둘", 100), ("□ 셋", 200))]
        variants = analyze_hierarchy(records)["variants"]
        self.assertEqual([(item["count"], item["kind"]) for item in variants],
                         [(2, "반복"), (1, "비반복")])

    def test_review_changes_copy_rules_and_field_selection(self):
        hierarchy = analyze_hierarchy([{"text": "□ 소제목", "left": 100,
                                        "font": "명조", "size_pt": 14,
                                        "prev_spacing": 200}])
        profile = {"format": {"기호_규칙": [("□", 0, "명조", 14, False, False)],
                              "복사_문단모양": {}, "제목_문단": {}},
                   "options": {"symbol_fonts": {"□": {"font": "명조", "size": "14"}}},
                   "style_hierarchy": hierarchy}
        original = copy.deepcopy(profile)
        rows = copy.deepcopy(hierarchy["variants"])
        rows[0].update(font="고딕", size_pt=16, left_hwpunit=300,
                       first_line_hwpunit=-50, prev_spacing_hwpunit=500,
                       apply={"font": False, "size": True, "indent": True, "spacing": False})
        edited = apply_reviewed_styles(profile, rows)
        self.assertEqual(profile, original)
        self.assertEqual(edited["format"]["기호_규칙"][0][2:4], ["고딕", 16.0])
        self.assertEqual(edited["format"]["복사_문단모양"]["□"]["PrevSpacing"], 500)
        self.assertFalse(edited["format"]["스타일_속성선택"]["□"]["font"])
        self.assertFalse(edited["format"]["스타일_속성선택"]["□"]["spacing"])
        self.assertEqual(edited["format"]["문두기호_역할"]["□"], "소제목")
        self.assertEqual(edited["options"]["symbol_fonts"]["□"]["font"], "고딕")

    def test_unselected_paragraph_fields_are_not_applied(self):
        namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "hwp-auto-docfit.py"),
                                   run_name="style_field_selection_test")
        apply_shape = namespace["복사_문단모양_적용"]
        globals_ = apply_shape.__globals__
        class Parameters:
            def __init__(self): self.values = {}
            def SetItem(self, key, value): self.values[key] = value
        class Action:
            def __init__(self): self.params = Parameters()
            def CreateSet(self): return self.params
            def Execute(self, params): return True
        class Hwp:
            def __init__(self): self.action = Action()
            def CreateAction(self, name): return self.action
        app = Hwp()
        globals_["hwp"] = app
        globals_["표준서식_설정"] = {
            "복사_문단모양": {"□": {"LeftMargin": 300, "Indentation": -50, "PrevSpacing": 500}},
            "스타일_속성선택": {"□": {"indent": False, "spacing": True}}}
        globals_["표준서식_문단위간격_사용"] = True
        apply_shape("□")
        self.assertEqual(app.action.params.values, {"PrevSpacing": 500})


if __name__ == "__main__":
    unittest.main()
