import unittest

from docfit_core.stage_selection import (STAGE_EXAMPLES, TABLE_STAGE_KEYS, enabled, stages_for_mode, without_page_fit,
                                         without_tables)


class StageSelectionTest(unittest.TestCase):
    def test_mode_lists_have_unique_stages_in_execution_order(self):
        for mode in ("spacing", "unify", "format", "all"):
            keys = [key for key, _ in stages_for_mode(mode)]
            self.assertEqual(len(keys), len(set(keys)))
            self.assertTrue(all(STAGE_EXAMPLES.get(key, "").startswith("예:") for key in keys))
        # 서식 적용·한 번에 적용은 준말 → 본말 변환이 첫째, 보고서 표준서식이 둘째로 다른 모든 단계보다 먼저다.
        for mode in ("format", "all"):
            self.assertEqual([key for key, _ in stages_for_mode(mode)][:2], ["abbreviation", "standard_format"])
        # 자간 정리·서식 통일은 두 단계를 하지 않는다.
        for mode in ("spacing", "unify"):
            keys = [key for key, _ in stages_for_mode(mode)]
            self.assertNotIn("abbreviation", keys)
            self.assertNotIn("standard_format", keys)
        all_keys = [key for key, _ in stages_for_mode("all")]
        # 그다음 박스 그림 표 변환, 자간 초기화(선행 서식·정밀 표 복제보다 먼저, 복사한 자간 보존) 순서다.
        self.assertEqual(all_keys[2:4], ["text_table_convert", "reset_spacing"])
        self.assertLess(all_keys.index("reset_spacing"), all_keys.index("pre_format"))
        format_keys = [key for key, _ in stages_for_mode("format")]
        self.assertEqual(format_keys[2], "text_table_convert")
        for keys in (format_keys, all_keys):
            self.assertLess(keys.index("text_table_convert"), keys.index("pre_format"))
        # 쪽 수 맞춤 뒤에 문단 페이지 배치를 한다.
        for mode in ("format", "all"):
            keys = [key for key, _ in stages_for_mode(mode)]
            self.assertLess(keys.index("page_fit"), keys.index("page_group"))
        for keys in (format_keys, all_keys):
            self.assertLess(keys.index("table_format"), keys.index("hanging_indent"))
            self.assertLess(keys.index("hanging_indent"), keys.index("supplement_indent"))
        self.assertLess(all_keys.index("supplement_indent"), all_keys.index("body_spacing"))
        self.assertNotIn("single_cell_spacing", all_keys)

    def test_omitted_selection_keeps_previous_behavior(self):
        self.assertTrue(enabled(None, "body_spacing"))
        self.assertTrue(enabled({}, "body_spacing"))
        self.assertFalse(enabled({"body_spacing": False}, "body_spacing"))

    def test_without_tables_turns_off_every_table_stage(self):
        # 한 번에 적용의 '표 제외': 표 관련 작업만 끄고 다른 선택과 제목·개요 서식(pre_format)은 그대로 둔다.
        all_keys = [key for key, _ in stages_for_mode("all")]
        self.assertTrue(set(TABLE_STAGE_KEYS) - {"table_unify"} <= set(all_keys))
        chosen = without_tables({"body_spacing": False, "table_style": True})
        self.assertTrue(all(chosen[key] is False for key in TABLE_STAGE_KEYS))
        self.assertFalse(chosen["body_spacing"])
        self.assertTrue(enabled(chosen, "pre_format", "all"))
        self.assertTrue(enabled(chosen, "word_check", "all"))

    def test_without_page_fit_turns_off_both_page_stages(self):
        # '페이지 맞춤 제외': (1) 문단 아래 간격 페이지 맞춤 (2) 관련 문단 페이지 배치를 끈다.
        chosen = without_page_fit({"page_fit": True, "body_spacing": True})
        self.assertEqual((chosen["page_fit"], chosen["page_group"], chosen["body_spacing"]), (False, False, True))


if __name__ == "__main__":
    unittest.main()
