"""□ 묶음 쪽 맞춤: 논리단위 5개 이하면 묶음 전체를 단위 수가 많은 쪽(같으면 앞쪽)으로."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

ROLE = {'ㅁ': '소제목', 'ㅇ': '본문', '-': '내용', '*': '부연설명'}


def layout(pattern):
    """'ㅁㅇ-/--' → (역할 목록, 문단별 첫 줄 쪽). '/'는 쪽 경계."""
    roles, pages, page = [], [], 1
    for ch in pattern:
        if ch == '/':
            page += 1
            continue
        roles.append(ROLE[ch])
        pages.append(page)
    return roles, pages


class PageGroupUnitsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def decide(self, pattern):
        roles, pages = layout(pattern)
        units = self.ns['쪽맞춤_논리단위'](roles)
        unit_pages = [pages[unit[0]] for unit in units]
        push, _, _ = self.ns['쪽맞춤_뒤로밀기인가'](unit_pages, sorted(set(pages)))
        return len(units), '밈' if push else '당김'

    def test_user_examples(self):
        self.assertEqual(self.decide('ㅁ/ㅇ'), (2, '당김'))
        self.assertEqual(self.decide('ㅁㅇ/ㅇㅇ'), (4, '당김'))
        self.assertEqual(self.decide('ㅁㅇ/ㅇㅇㅇ'), (5, '밈'))
        self.assertEqual(self.decide('ㅁㅇ-/--'), (2, '당김'))
        self.assertEqual(self.decide('ㅁㅇ--/-ㅇㅇ'), (4, '당김'))

    def test_notes_and_items_attach_to_previous_unit(self):
        units = self.ns['쪽맞춤_논리단위'](layout('ㅁ*ㅇ-*ㅇ*')[0])
        self.assertEqual(units, [[0, 1], [2, 3, 4], [5, 6]])

    def _group_attempt(self, pattern, move_result='성공'):
        fn = self.ns['소제목묶음_같은쪽_시도']
        roles, pages = layout(pattern)
        group = [((0, i, 0), (0, i, 5), role) for i, role in enumerate(roles)]
        mover = Mock(return_value=move_result)
        stats = {'대상': 0, '성공': 0, '실패': 0}
        record = Mock()
        with patch.dict(fn.__globals__, {
            '보고서_소제목묶음_수집': lambda pos: group,
            '쪽범위_사용중': lambda: False,
            '보고서_묶음_쪽별줄수': lambda paragraphs: {p: 1 for p in pages},
            '문단_첫줄_쪽': lambda start: pages[start[1]],
            '_묶음_같은쪽_이동': mover, '세트문장_통계': stats,
            '검수_문제_기록': record, '진단로그': Mock(), '로그': Mock(),
            '현재_처리파일': 'x.hwpx',
        }):
            result = fn((0, 0, 0), 'ㅁ 제목')
        return result, mover, stats, record

    def test_small_group_moves_whole_group_in_decided_direction(self):
        result, mover, stats, _ = self._group_attempt('ㅁㅇ/ㅇㅇㅇ')
        self.assertEqual(result[0], '처리')
        self.assertIs(mover.call_args.args[3], True)  # 뒤쪽으로 밈
        self.assertEqual(stats['성공'], 1)
        result, mover, _, _ = self._group_attempt('ㅁㅇ--/-ㅇㅇ')
        self.assertIs(mover.call_args.args[3], False)  # 앞쪽으로 당김

    def test_six_or_more_units_left_to_unit_level(self):
        result, mover, stats, _ = self._group_attempt('ㅁㅇㅇ/ㅇㅇㅇ')
        self.assertEqual(result, ('단위별', []))
        mover.assert_not_called()
        self.assertEqual(stats['대상'], 0)

    def test_group_already_on_one_page_is_done(self):
        result, mover, _, _ = self._group_attempt('ㅁㅇ-ㅇ')
        self.assertEqual(result[0], '처리')
        mover.assert_not_called()

    def test_failed_group_move_falls_back_to_unit_level(self):
        result, _, stats, record = self._group_attempt('ㅁ/ㅇ', move_result='실패')
        self.assertEqual(result[0], '단위별')
        self.assertEqual(stats['실패'], 1)
        self.assertIn('소제목 묶음 쪽 분리', record.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
