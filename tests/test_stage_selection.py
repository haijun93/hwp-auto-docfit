import unittest

from docfit_core.stage_selection import (CARD_OPTION_STAGES, STAGE_EXAMPLES, TABLE_STAGE_KEYS, card_option_from_stages,
                                         card_option_keys, card_option_off_keys, card_option_stage_values,
                                         default_choice, enabled, stages_for_mode, without_page_fit, without_tables)


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

    def test_every_card_option_links_to_stages_of_its_card(self):
        # 카드 옵션 9개(자간 정리 2·서식 통일 4·한 번에 적용 3)는 모두 그 카드 세부 작업 목록의 작업과 연동한다.
        self.assertEqual(len(CARD_OPTION_STAGES), 9)
        self.assertEqual(card_option_keys("unify_keep_layout", "unify"), ("page_layout_keep",))
        for option, (modes, _, _) in CARD_OPTION_STAGES.items():
            self.assertTrue(card_option_keys(option, modes[0]), option)
        self.assertEqual(card_option_keys("spacing_exclude_tables", "spacing"),
                         ("control_spacing", "control_short_line", "control_word_check"))
        self.assertEqual(card_option_keys("unify_exclude_tables", "unify"), ("table_style", "table_unify"))
        self.assertEqual(card_option_keys("unify_exclude_spacing", "unify"), ("unify_spacing",))
        self.assertEqual(card_option_keys("unify_exclude_pagefit", "unify"), ("page_fit",))
        self.assertEqual(card_option_keys("all_exclude_tables", "format"),
                         ("text_table_convert", "table_style", "table_width", "precise_table", "table_format"))
        self.assertEqual(len(card_option_keys("all_include_spacing", "all")), 7)
        self.assertEqual(card_option_keys("all_include_spacing", "format"), ())   # 자간 조정 제외 구성에는 자간 작업이 없다
        self.assertEqual(card_option_keys("unify_exclude_tables", "all"), ())     # 다른 카드의 작업은 건드리지 않는다

    def test_option_turns_linked_stages_on_and_off(self):
        # '제외' 옵션을 켜면 관련 작업을 모두 끄고, 끄면 모두 켠다. '포함' 옵션은 반대로 따른다.
        self.assertEqual(card_option_stage_values("unify_exclude_tables", True, {}, "unify"),
                         {"table_style": False, "table_unify": False})
        self.assertEqual(card_option_stage_values("unify_exclude_tables", False, {}, "unify"),
                         {"table_style": True, "table_unify": True})
        self.assertEqual(card_option_stage_values("spacing_reset_existing", False, {}, "spacing"), {"reset_spacing": False})
        # '표 제외'를 켠 채 '자간 조정 포함'을 켜면 표·컨트롤 자간 작업은 꺼 둔다.
        values = card_option_stage_values("all_include_spacing", True, {"all_exclude_tables": True}, "all")
        self.assertTrue(values["body_spacing"] and values["reset_spacing"] and values["word_check"])
        self.assertFalse(values["control_spacing"] or values["control_short_line"] or values["control_word_check"])
        # '자간 조정 포함'을 끈 채 '표 제외'를 끄면 all 구성의 표·컨트롤 자간 작업은 꺼 둔다.
        values = card_option_stage_values("all_exclude_tables", False, {"all_include_spacing": False}, "all")
        self.assertTrue(values["table_style"])
        self.assertFalse(values["control_spacing"])

    def test_option_follows_stages(self):
        # '제외' 옵션은 관련 작업이 모두 꺼졌을 때만 켜지고, '포함' 옵션은 하나라도 켜져 있으면 켜진다.
        unify = {key: default_choice(key, "unify") for key, _ in stages_for_mode("unify")}
        self.assertFalse(card_option_from_stages("unify_exclude_tables", unify, "unify"))
        self.assertFalse(card_option_from_stages("unify_exclude_spacing", unify, "unify"))
        self.assertTrue(card_option_from_stages("unify_exclude_pagefit", unify, "unify"))   # 쪽 맞춤 기본 꺼짐
        unify["table_style"] = False
        self.assertFalse(card_option_from_stages("unify_exclude_tables", unify, "unify"))   # 표 서식통일은 켜져 있다
        unify["table_unify"] = False
        self.assertTrue(card_option_from_stages("unify_exclude_tables", unify, "unify"))
        spacing_off = {key: False for key, _ in stages_for_mode("all") if key in card_option_keys("all_include_spacing", "all")}
        self.assertFalse(card_option_from_stages("all_include_spacing", spacing_off, "all"))
        self.assertTrue(card_option_from_stages("all_include_spacing", dict(spacing_off, short_line=True), "all"))
        self.assertIsNone(card_option_from_stages("all_include_spacing", {}, "format"))
        # 카드 요약이 이미 알리는 작업(켜진 제외 옵션·꺼진 포함 옵션이 끈 작업)
        self.assertEqual(card_option_off_keys({"unify_exclude_pagefit": True, "unify_exclude_tables": False}, "unify"),
                         {"page_fit"})
        self.assertEqual(card_option_off_keys({"spacing_reset_existing": False}, "spacing"), {"reset_spacing"})


if __name__ == "__main__":
    unittest.main()
