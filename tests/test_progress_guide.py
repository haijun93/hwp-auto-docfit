"""진행 화면 단계 안내 문장 연결 검사."""
import unittest

from docfit_core.progress_guide import GUIDE_ITEMS, MODE_GUIDES, guide_key, guide_state


class ProgressGuideTests(unittest.TestCase):
    def test_stage_names_map_to_friendly_guides(self):
        self.assertEqual(guide_key('열기'), 'open')
        self.assertEqual(guide_key('본문 자간·단어 분리 조정 (2차)'), 'body_spacing')
        self.assertEqual(guide_key('자간 조정 후 내어쓰기'), 'indent')
        self.assertEqual(guide_key('서식통일 적용'), 'unify_apply')
        self.assertEqual(guide_key('서식통일'), 'unify_survey')
        self.assertEqual(guide_key('후속 작업 후 서식통일 재검증'), 'unify_recheck')
        self.assertIsNone(guide_key('알 수 없는 단계'))

    def test_each_mode_has_about_ten_sentences_or_fewer(self):
        keys = {key for key, _, _ in GUIDE_ITEMS}
        for mode, steps in MODE_GUIDES.items():
            self.assertLessEqual(len(steps), 13, mode)
            self.assertTrue(set(steps) <= keys, mode)
            self.assertEqual(steps[-1], 'done')

    def test_state_marks_current_and_done_steps(self):
        state = guide_state('unify', 'unify_apply', {'open', 'unify_survey'})
        self.assertEqual(state['current'], 2)
        self.assertEqual(state['done'], [0, 1])
        self.assertIn('표준과 다른 문장', state['message'])


class UnifyStageTests(unittest.TestCase):
    def test_unify_uses_document_majority_only_with_optional_page_fit(self):
        from docfit_core.stage_selection import default_choice, stages_for_mode
        self.assertEqual([key for key, _ in stages_for_mode('unify')],
                         ['table_style', 'style_unify', 'table_unify', 'page_fit'])
        self.assertTrue(default_choice('style_unify', 'unify'))
        self.assertFalse(default_choice('page_fit', 'unify'))
        self.assertFalse(default_choice('standard_format', 'unify'))


if __name__ == '__main__':
    unittest.main()
