from pathlib import Path
import runpy
import unittest


class RegressionToolTest(unittest.TestCase):
    """회귀 도구(R3, 2026-10-10): 화면과 같은 설정 규칙, 검사별 판정(요구한 검사의 not_run은 실패)."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts' / 'regression_pc.py'),
                                run_name='regression_pc_test')

    def test_mode_follows_app_setting_key_and_saved_stage_choices(self):
        설정 = self.ns['작업_설정']
        모드, 세부작업, _, 표제외 = 설정({'all_include_spacing': False}, None, False)
        self.assertEqual((모드, 표제외), ('format', False))
        모드, 세부작업, _, _ = 설정({'stage_choices': {'all': {'page_group': False, '없는키': True}}}, None, False)
        self.assertEqual(모드, 'all')
        self.assertFalse(세부작업['page_group'])
        self.assertNotIn('없는키', 세부작업)

    def test_card_options_like_gui(self):
        설정 = self.ns['작업_설정']
        _, 세부작업, _, 표제외 = 설정({'all_exclude_tables': True, 'all_exclude_pagefit': True}, 'all', False)
        self.assertTrue(표제외)
        self.assertFalse(세부작업['page_fit'])
        _, 세부작업, 세부, _ = 설정({'unify_exclude_pagefit': True, 'unify_keep_layout': True,
                                 'unify_exclude_spacing': True}, 'unify', False)
        self.assertTrue(세부작업['page_layout_keep'])
        self.assertTrue(세부['unify_exclude_spacing'])

    def test_required_check_not_run_fails(self):
        판정 = self.ns['판정']
        요구 = {'min_score': 100, 'same_layout': True}
        검사, 합격 = 판정({'output_created': True, 'score': None, 'layout_same': None}, 요구)
        self.assertEqual((검사['score'], 검사['layout'], 합격), ('not_run', 'not_run', False))
        검사, 합격 = 판정({'output_created': True, 'score': 100.0, 'layout_same': True}, 요구)
        self.assertTrue(합격)
        검사, 합격 = 판정({'output_created': True, 'score': 99.6}, {'min_score': 100, 'same_layout': False})
        self.assertEqual((검사['score'], 검사['layout'], 합격), ('fail', 'not_applicable', False))

    def test_title_label_is_an_independent_release_gate(self):
        판정 = self.ns['판정']
        항목 = {'output_created': True, 'score': 100.0, 'title_check_required': True,
              'title_content_preserved': False}
        검사, 합격 = 판정(항목, {'min_score': 100, 'same_layout': False})
        self.assertEqual((검사['score'], 검사['title_content'], 합격), ('pass', 'fail', False))

    def test_title_result_probe_handles_subtitle_split_and_whitespace(self):
        from unittest.mock import patch
        검사 = self.ns['제목_결과검사']
        with patch.dict(검사.__globals__, {
            'detect_header': lambda _: {'title': {'text': '지구 이주·점령 계획(안) 보고'}}
        }):
            self.assertTrue(검사('삼체 문명 존속을 위한, 지구 이주·점령 계획(안) 보고', 'result.hwpx'))
        with patch.dict(검사.__globals__, {
            'detect_header': lambda _: {'title': None}
        }):
            self.assertFalse(검사('삼체 문명 존속을 위한, 지구 이주·점령 계획(안) 보고', 'result.hwpx'))


if __name__ == '__main__':
    unittest.main()
