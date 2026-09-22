import unittest

from docfit_core.stage_selection import STAGE_EXAMPLES, enabled, stages_for_mode


class StageSelectionTest(unittest.TestCase):
    def test_mode_lists_have_unique_stages_in_execution_order(self):
        for mode in ("spacing", "format", "all"):
            keys = [key for key, _ in stages_for_mode(mode)]
            self.assertEqual(len(keys), len(set(keys)))
            self.assertTrue(all(STAGE_EXAMPLES.get(key, "").startswith("예:") for key in keys))
        all_keys = [key for key, _ in stages_for_mode("all")]
        self.assertLess(all_keys.index("pre_format"), all_keys.index("reset_spacing"))
        self.assertLess(all_keys.index("reset_spacing"), all_keys.index("normalize_space"))
        self.assertLess(all_keys.index("body_spacing"), all_keys.index("hanging_indent"))
        self.assertNotIn("single_cell_spacing", all_keys)

    def test_omitted_selection_keeps_previous_behavior(self):
        self.assertTrue(enabled(None, "body_spacing"))
        self.assertTrue(enabled({}, "body_spacing"))
        self.assertFalse(enabled({"body_spacing": False}, "body_spacing"))


if __name__ == "__main__":
    unittest.main()
