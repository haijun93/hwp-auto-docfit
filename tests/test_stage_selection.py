import unittest

from docfit_core.stage_selection import STAGE_EXAMPLES, enabled, stages_for_mode


class StageSelectionTest(unittest.TestCase):
    def test_mode_lists_have_unique_stages_in_execution_order(self):
        for mode in ("spacing", "format", "all"):
            keys = [key for key, _ in stages_for_mode(mode)]
            self.assertEqual(len(keys), len(set(keys)))
            self.assertTrue(all(STAGE_EXAMPLES.get(key, "").startswith("예:") for key in keys))
        all_keys = [key for key, _ in stages_for_mode("all")]
        # 자간 초기화는 선행 서식·정밀 표 복제보다 먼저 실행된다(복사한 자간 보존).
        self.assertEqual(all_keys[0], "reset_spacing")
        self.assertLess(all_keys.index("reset_spacing"), all_keys.index("pre_format"))
        # 쪽 수 맞춤 뒤에 문단 페이지 배치를 한다.
        for mode in ("format", "all"):
            keys = [key for key, _ in stages_for_mode(mode)]
            self.assertLess(keys.index("page_fit"), keys.index("page_group"))
        self.assertLess(all_keys.index("body_spacing"), all_keys.index("hanging_indent"))
        self.assertNotIn("single_cell_spacing", all_keys)

    def test_omitted_selection_keeps_previous_behavior(self):
        self.assertTrue(enabled(None, "body_spacing"))
        self.assertTrue(enabled({}, "body_spacing"))
        self.assertFalse(enabled({"body_spacing": False}, "body_spacing"))


if __name__ == "__main__":
    unittest.main()
