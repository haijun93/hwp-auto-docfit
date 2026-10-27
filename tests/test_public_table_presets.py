"""공공기관·비즈니스 6대 표준 표 템플릿 프리셋 단위 시험."""

import unittest
from docfit_core.public_table_presets import (
    PUBLIC_TABLE_PRESETS,
    get_public_preset_descriptors,
    is_public_preset,
    get_public_preset,
    build_public_preset_preview,
)


class PublicTablePresetsTest(unittest.TestCase):
    def test_descriptors_has_six_presets(self):
        descriptors = get_public_preset_descriptors()
        self.assertEqual(len(descriptors), 6)
        ids = {d["id"] for d in descriptors}
        expected_ids = {
            "pub_summary_headline",
            "pub_two_col_definition",
            "pub_multi_col_comparison",
            "pub_gantt_timeline",
            "pub_budget_breakdown",
            "pub_qa_checklist",
        }
        self.assertEqual(ids, expected_ids)
        for d in descriptors:
            self.assertEqual(d["category"], "공공 표준")
            self.assertTrue(d["name"].startswith(("①", "②", "③", "④", "⑤", "⑥")))
            self.assertIn("guideline", d)

    def test_is_public_preset(self):
        self.assertTrue(is_public_preset("pub_summary_headline"))
        self.assertFalse(is_public_preset("unknown_preset"))

    def test_preview_generation_all_presets(self):
        for pid in PUBLIC_TABLE_PRESETS:
            preview = build_public_preset_preview(pid)
            self.assertIn("rows", preview)
            self.assertIn("cols", preview)
            self.assertIn("cell_meta", preview)
            meta = preview["cell_meta"]
            self.assertEqual(len(meta), preview["rows"])
            self.assertEqual(len(meta[0]), preview["cols"])

            # 각 셀의 구조 검증
            for r, row in enumerate(meta):
                for c, cell in enumerate(row):
                    self.assertEqual(cell["row"], r)
                    self.assertEqual(cell["col"], c)
                    self.assertIn("width", cell)
                    self.assertIn("height", cell)
                    self.assertIn("text", cell)
                    self.assertIn("align", cell)
                    self.assertIn("style", cell)
                    self.assertIn("borders", cell)
                    self.assertIn("top", cell["borders"])
                    self.assertIn("bottom", cell["borders"])

    def test_headline_box_properties(self):
        preview = build_public_preset_preview("pub_summary_headline")
        self.assertEqual(preview["rows"], 1)
        self.assertEqual(preview["cols"], 1)
        cell = preview["cell_meta"][0][0]
        self.assertEqual(cell["style"]["fill"], "#EBF3FA")
        self.assertEqual(cell["borders"]["top"]["color"], "#1A365D")
        self.assertEqual(cell["borders"]["left"]["type"], "NONE")
        self.assertEqual(cell["borders"]["right"]["type"], "NONE")

    def test_two_col_definition_properties(self):
        preview = build_public_preset_preview("pub_two_col_definition")
        self.assertEqual(preview["rows"], 4)
        self.assertEqual(preview["cols"], 2)
        # 1열은 항목명(회색 음영, Bold)
        col0 = preview["cell_meta"][0][0]
        self.assertEqual(col0["style"]["fill"], "#F2F4F7")
        self.assertTrue(col0["style"]["bold"])
        self.assertEqual(col0["align"], "CENTER")
        # 2열은 본문(흰색, Regular)
        col1 = preview["cell_meta"][0][1]
        self.assertEqual(col1["style"]["fill"], "#FFFFFF")
        self.assertFalse(col1["style"]["bold"])
        self.assertEqual(col1["align"], "LEFT")

    def test_custom_row_col_resizing(self):
        # 2열 정의 표를 6행으로 확장
        preview = build_public_preset_preview("pub_two_col_definition", target_rows=6)
        self.assertEqual(preview["rows"], 6)
        self.assertEqual(len(preview["cell_meta"]), 6)


if __name__ == "__main__":
    unittest.main()
