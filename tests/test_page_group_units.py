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

    def _group_attempt(self, pattern, move_result='성공', head=None, head_pages=None):
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
            '쪽보다_긴_묶음인가': lambda paragraphs, counts: False,
            '_묶음_쪽나눔_이동': lambda *args, **kwargs: False,
            '표_쪽범위': lambda key: head_pages,
        }):
            result = fn((0, 0, 0), 'ㅁ 제목', head)
        return result, mover, stats, record

    def test_small_group_moves_whole_group_in_decided_direction(self):
        result, mover, stats, _ = self._group_attempt('ㅁㅇ/ㅇㅇㅇ')
        self.assertEqual(result[0], '처리')
        self.assertIs(mover.call_args.args[3], True)  # 뒤쪽으로 밈
        self.assertEqual(stats['성공'], 1)
        result, mover, _, _ = self._group_attempt('ㅁㅇ--/-ㅇㅇ')
        self.assertIs(mover.call_args.args[3], False)  # 앞쪽으로 당김

    def test_midtitle_head_moves_with_group(self):
        # 'Ⅱ 추진 계획' 중제목이 앞쪽 끝, □ 묶음이 뒤쪽이면 중제목부터 함께 민다(□ 앞 쪽 나눔 금지).
        head = {'위치': (0, 9, 0), '표키': (0, 9, 0)}
        result, mover, _, _ = self._group_attempt('/ㅁㅇ-', head=head, head_pages=(1, 1))
        self.assertEqual(result[0], '처리')
        self.assertEqual(mover.call_args.args[0], (0, 9, 0))
        self.assertEqual(mover.call_args.kwargs['표키'], (0, 9, 0))
        self.assertIs(mover.call_args.args[3], True)

    def test_failed_pull_does_not_push_whole_group(self):
        # 실측(서식 예시 'Ⅱ 추진 계획'): □ㅇㅇ/ㅇ는 앞쪽 단위가 많아 당기는데, 줄간격이 이미 최소라 못 당겨도
        # 묶음 전체를 2쪽으로 밀지 않고 ㅇ 단위 경계에서 나눈다(단위별 배치).
        result, mover, stats, record = self._group_attempt('ㅁㅇ-ㅇ/ㅇ', move_result='실패')
        self.assertEqual(result[0], '단위별')
        self.assertIs(mover.call_args.args[3], False)            # 당김만
        self.assertIs(mover.call_args.kwargs['한방향'], True)     # 반대(밀기)로 보완하지 않음
        record.assert_not_called()
        self.assertEqual((stats['대상'], stats['실패']), (0, 0))

    def test_failed_push_still_tries_page_break(self):
        result, mover, stats, record = self._group_attempt('ㅁ/ㅇㅇㅇ', move_result='실패')
        self.assertIs(mover.call_args.kwargs['한방향'], False)
        self.assertEqual(stats['실패'], 1)                         # 쪽 나눔도 못 하면(이 시험에서는 False) 미해결
        record.assert_called_once()

    def test_unit_boundary_split_with_front_majority_is_exempt(self):
        fn = self.ns['소제목묶음_단위경계_앞쪽우선']
        group = [((0, i, 0), (0, i, 5), role) for i, role in enumerate(['소제목', '본문', '내용', '본문', '본문'])]
        units = [[0], [1, 2], [3], [4]]
        pages = {0: 1, 1: 1, 2: 1, 3: 1, 4: 2}
        def counts(paragraphs):
            return {pages[p[0][1]]: 1 for p in paragraphs} if len({pages[p[0][1]] for p in paragraphs}) == 1                 else {1: 1, 2: 1}
        with patch.dict(fn.__globals__, {'보고서_묶음_쪽별줄수': counts}):
            self.assertTrue(fn(group, units))
            pages[2] = 2                                          # ㅇ 단위 안(- 줄)에서 나뉘면 예외 아님
            self.assertFalse(fn(group, units))
            pages.update({2: 1, 3: 2})                            # 뒤쪽 단위가 더 많으면 예외 아님
            pages[1] = 2; pages[2] = 2
            self.assertFalse(fn(group, units))

    def test_group_ending_with_table_is_left_to_unit_and_table_bundles(self):
        # 'ㅇ (3단계)' 뒤 표가 오면 그 ㅇ는 표의 제목 문장 — □ 묶음 전체 규칙 대신 단위·표 묶음 배치에 맡긴다.
        fn = self.ns['소제목묶음_뒤_표인가']
        group = [((0, i, 0), (0, i, 5), role) for i, role in enumerate(['소제목', '본문', '본문'], start=15)]
        g = fn.__globals__
        with patch.dict(g, {'로마자_중제목_표인가': lambda key: False}):
            self.assertTrue(fn(group, {18: (0, 18, 0)}))
            self.assertFalse(fn(group, {30: (0, 30, 0)}))
            self.assertFalse(fn(group, None))
        with patch.dict(g, {'로마자_중제목_표인가': lambda key: True}):
            self.assertFalse(fn(group, {18: (0, 18, 0)}))       # 다음 중제목 표는 이 묶음의 표가 아니다

    def test_paragraph_space_pull_restores_when_it_fails(self):
        fn = self.ns['_묶음_위간격_축소_당김']
        written = []
        cursor = [(0, 0, 0)]
        hwp = Mock()
        hwp.SetPos.side_effect = lambda *pos: cursor.__setitem__(0, pos)
        backup = [((0, i, 0), 1, 160) for i in range(3)]
        stats = {'축소횟수': 0}
        with patch.dict(fn.__globals__, {
            'hwp': hwp, 'hwp_run': Mock(), '중단_요청됨': lambda: False, '세트문장_통계': stats,
            '문단_위간격_pt_현재문단': lambda: 10.0,
            '문단_위간격_적용_현재선택': lambda pt: written.append((cursor[0], pt)),
            '보고서_묶음_쪽별줄수': lambda paragraphs: {1: 2, 2: 1},
            '표_쪽범위': lambda key: None, '로그': Mock(), '진단로그': Mock(),
        }):
            self.assertFalse(fn(backup, [], 1, None, '□ 단계별 추진 일정'))
        self.assertEqual([pt for _, pt in written[:3]], [9.0, 9.0, 9.0])     # 10%씩
        self.assertIn(5.0, [pt for _, pt in written])                         # 최대 50%까지
        self.assertEqual([pt for _, pt in written[-3:]], [10.0, 10.0, 10.0])  # 못 당기면 복원

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
