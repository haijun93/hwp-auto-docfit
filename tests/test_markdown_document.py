"""Explicit Markdown files use semantic headings, independent of AI guessing."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch
from docfit_core.ai_answer import looks_like_ai_answer, ai_answer_to_labeled_text, parse_ai_answer
from docfit_core.labeled_text import parse_labeled_text

SAMPLE = '''# 시설 정비 계획(안)

2026. 10. / 담당부서 시설팀

시설 7개소를 정비하고자 함.

## 추진개요
### 공사개요
- 예산: 2,970,000원
| 구분 | 금액 |
| --- | --- |
| 절사 | -9,000 |

※ [확인 필요] 항목은 검토 후 확정한다.

## 행정사항
- 기간은 별도 확정

붙임 1. 검토자료 1부. 끝.
'''


class MarkdownDocumentTests(unittest.TestCase):
    def test_notes_do_not_disable_explicit_file_headings(self):
        self.assertFalse(looks_like_ai_answer(SAMPLE))
        self.assertTrue(looks_like_ai_answer(SAMPLE, markdown_document=True))
        out = ai_answer_to_labeled_text(SAMPLE, markdown_document=True)
        self.assertIn('제목: 시설 정비 계획(안)', out)
        self.assertIn('네모: 추진개요', out)
        self.assertIn('원: 공사개요', out)
        self.assertIn('당구: [확인 필요] 항목은 검토 후 확정한다.', out)
        for value in ('2026. 10. / 담당부서 시설팀', '2,970,000', '-9,000', '붙임 1.'):
            self.assertIn(value, out)
        tables = [b for b in parse_labeled_text(out) if b['kind'] == 'table']
        self.assertEqual(tables[0]['rows'], [['구분', '금액'], ['절사', '-9,000']])

    def test_single_title_and_spaced_hashes(self):
        self.assertEqual(parse_ai_answer('# 제목', markdown_document=True)[0], {'kind': 'title1', 'text': '제목'})
        out = ai_answer_to_labeled_text('# 제목\n# # 장 제목\n# ## 절 제목\n- 내용', markdown_document=True)
        self.assertIn('네모: 장 제목', out)
        self.assertIn('원: 절 제목', out)
        self.assertNotIn('#', out)

    def test_heading_ranks_do_not_depend_on_encounter_order(self):
        blocks = parse_ai_answer('### 하위\n## 상위\n### 하위2', markdown_document=True)
        paragraphs = {b['text']: b['marker'] for b in blocks if b['kind'] == 'para'}
        self.assertEqual(paragraphs, {'하위': 'ㅇ', '상위': '□', '하위2': 'ㅇ'})

    def test_hashes_inside_code_do_not_trigger_heading_route(self):
        self.assertFalse(looks_like_ai_answer('```\n# # example\n```', markdown_document=True))


class MarkdownAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_md_without_engine_reaches_semantic_renderer_even_if_ai_toggle_off(self):
        fn = self.ns['외부문서_hwpx로_변환']
        captured, engine = [], Mock(side_effect=AssertionError('engine must not be used'))
        with patch.dict(fn.__globals__, {'텍스트파일_읽기': lambda p: SAMPLE,
             '텍스트_hwpx로_변환': lambda text, target: captured.append(text),
             'generate_hwpx': engine, '로그': Mock(), '알파_AI답변변환_사용': False}):
            fn('draft.md', '.md', 'work.hwpx')
        engine.assert_not_called()
        self.assertIn('네모: 추진개요', captured[0])
        self.assertIn('표: 절사 | -9,000', captured[0])

    def test_explicit_beomgov_md_bypasses_generic_markdown_engine(self):
        fn = self.ns['외부문서_hwpx로_변환']
        text = '#!범정부오피스\n소제목: 개요\n표: 항목 : 값'
        renderer, engine = Mock(), Mock(side_effect=AssertionError('호환 입력을 일반 엔진에 넘기면 안 됨'))
        with patch.dict(fn.__globals__, {'텍스트파일_읽기': lambda p: text,
             '텍스트_hwpx로_변환': renderer, 'generate_hwpx': engine}):
            fn('draft.md', '.md', 'work.hwpx')
        renderer.assert_called_once_with(text, 'work.hwpx')
        engine.assert_not_called()

    def test_semantic_blocks_are_inserted_as_real_tables_then_post_processed(self):
        fn = self.ns['텍스트_hwpx로_변환']
        doc, insert, post = Mock(), Mock(), Mock()
        events = []
        doc.SaveAs.side_effect = lambda *a: events.append('save') or True
        doc.Clear.side_effect = lambda *a: events.append('release') or True
        post.side_effect = lambda *a: events.append('style')
        with patch.dict(fn.__globals__, {'hwp': doc, '라벨블록_한글삽입': insert,
                                        '라벨_서식표_적용': post, '텍스트_삽입': Mock(side_effect=AssertionError('literal labels leaked'))}):
            opened = fn(ai_answer_to_labeled_text(SAMPLE, markdown_document=True), 'work.hwpx')
        self.assertFalse(opened)  # 라벨 후처리를 위해 COM 문서를 닫았으므로 pipeline이 다시 열어야 함
        self.assertEqual(events, ['save', 'release', 'style'])
        blocks = insert.call_args.args[1]
        self.assertTrue(any(b['kind'] == 'table' for b in blocks))
        self.assertTrue(any(b['kind'] == 'title1' for b in blocks))

    def test_failed_save_never_releases_or_patches(self):
        fn = self.ns['텍스트_hwpx로_변환']
        doc, post = Mock(), Mock()
        doc.SaveAs.return_value = False
        with patch.dict(fn.__globals__, {'hwp': doc, '라벨블록_한글삽입': Mock(), '라벨_서식표_적용': post}):
            with self.assertRaises(RuntimeError):
                fn('제목: 제목\n네모: 내용', 'work.hwpx')
        doc.Clear.assert_not_called()
        post.assert_not_called()

    def test_mixed_labeled_report_keeps_the_saved_document_open(self):
        fn = self.ns['텍스트_hwpx로_변환']
        doc, inserted = Mock(), []
        doc.Run.return_value = True
        doc.SaveAs.return_value = True
        with patch.dict(fn.__globals__, {
            'hwp': doc,
            '텍스트_삽입': lambda line: inserted.append(line),
            'hwp_run': lambda *_: True,
        }):
            opened = fn('제목 : 계획 보고\n\n개요 : 추진 개요\n\n□ 추진 배경', 'work.hwpx')
        self.assertTrue(opened)
        self.assertEqual(inserted[0], '제목 : 계획 보고')
        doc.Clear.assert_not_called()

    def test_labels_mixed_with_report_lines_are_inserted_line_by_line(self):
        # v1.76 회귀: 제목:/개요: 라벨에 □ ㅇ - * 줄이 섞인 TXT를 라벨 해석기로 넘겨 항목이 한 문단으로 합쳐졌다.
        fn = self.ns['텍스트_hwpx로_변환']
        doc, insert, written = Mock(), Mock(), []
        doc.SaveAs.return_value = True
        text = ('제목 : 계획(안) 보고\n\n개요 : 보고드림.\n\n□ 추진 배경\n  ㅇ (상황) 환경 반복\n'
                '    - 항세기*가 교차\n    * 항세기: 안정된 시기\n  ┌──┬──┐\n  │ 구분 │ 내용 │')
        with patch.dict(fn.__globals__, {'hwp': doc, '라벨블록_한글삽입': insert, '라벨_서식표_적용': Mock(),
                                        '텍스트_삽입': written.append, 'hwp_run': Mock()}):
            fn(text, 'work.hwpx')
        insert.assert_not_called()
        self.assertIn('    * 항세기: 안정된 시기', written)
        self.assertIn('  ㅇ (상황) 환경 반복', written)
