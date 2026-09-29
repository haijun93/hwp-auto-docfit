"""표 묶음(제목 문장 + 표 + 주석) 쪽 배치 판단."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

LEAD = [((0, 65, 0), (0, 65, 12), '본문')]
TABLE = ((0, 66, 0), (0, 66, 1), '표')
NOTES = [((0, 67, 0), (0, 67, 40), '부연설명'), ((0, 68, 0), (0, 68, 40), '부연설명')]
KEY = (0, 66, 0)


class TableBundlePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def run_case(self, lead_pages, table_pages, note_pages, move_result='실패', break_result=True):
        fn = self.ns['표묶음_같은쪽_시도']
        g = fn.__globals__

        def counts(paragraphs):
            if paragraphs == LEAD:
                return dict(lead_pages)
            return dict(note_pages)

        move = Mock(return_value=move_result)
        page_break = Mock(return_value=break_result)
        stats = {'대상': 0, '성공': 0, '실패': 0}
        with patch.dict(g, {
            '보고서_표묶음_수집': lambda pos, tables: (LEAD, TABLE, NOTES, KEY),
            '보고서_묶음_쪽별줄수': counts,
            '표_쪽범위': lambda key: table_pages,
            '_묶음_같은쪽_이동': move, '_묶음_쪽나눔_이동': page_break,
            '쪽범위_사용중': lambda: False, '세트문장_통계': stats,
            '검수_문제_기록': Mock(), '로그': Mock(), '진단로그': Mock(), '현재_처리파일': '',
        }):
            end = fn((0, 65, 0), 'ㅇ (세부 추진일정)', {66: KEY})
        return end, move, page_break, stats

    def test_bundle_on_one_page_is_left_alone(self):
        end, move, page_break, stats = self.run_case({4: 1}, (4, 4), {4: 2})
        self.assertEqual(end, NOTES[-1][0])
        move.assert_not_called()
        page_break.assert_not_called()
        self.assertEqual(stats['대상'], 0)

    def test_heading_alone_at_page_end_is_pushed_with_table(self):
        # 실측 사례: 제목 3쪽 끝, 표·주석 4쪽 → 줄간격으로 밀고, 안 되면 제목 앞 쪽 나눔.
        end, move, page_break, stats = self.run_case({3: 1}, (4, 4), {4: 2})
        self.assertTrue(move.call_args.args[3])            # 먼저 확대(뒤로 밈)
        self.assertEqual(move.call_args.kwargs['표키'], KEY)
        page_break.assert_called_once()
        self.assertEqual(page_break.call_args.kwargs['표키'], KEY)
        self.assertEqual(stats['성공'], 1)

    def test_only_notes_spilling_are_pulled_back(self):
        _, move, page_break, _ = self.run_case({3: 1}, (3, 3), {4: 1}, move_result='성공')
        self.assertFalse(move.call_args.args[3])           # 먼저 축소(앞으로 당김)
        self.assertFalse(move.call_args.kwargs['한방향'])   # 안 되면 통째로 미는 것도 시도
        page_break.assert_not_called()

    def test_table_starting_on_front_page_is_never_page_broken(self):
        # 표가 앞쪽에서 시작해 쪽을 넘으면 앞쪽을 크게 비우는 쪽 나눔은 하지 않는다.
        _, move, page_break, stats = self.run_case({3: 1}, (3, 4), {4: 1})
        self.assertTrue(move.call_args.kwargs['한방향'])
        page_break.assert_not_called()
        self.assertEqual(stats['실패'], 1)

    def test_table_longer_than_page_only_keeps_heading_with_table_start(self):
        _, move, page_break, stats = self.run_case({3: 1}, (4, 6), {6: 1})
        move.assert_not_called()
        self.assertTrue(page_break.call_args.kwargs['표까지만'])
        self.assertEqual(stats['성공'], 1)


if __name__ == '__main__':
    unittest.main()
