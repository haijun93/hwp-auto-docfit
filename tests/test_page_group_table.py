"""표 묶음(제목 문장 + 표 + 주석) 쪽 배치 판단."""
from pathlib import Path
import runpy
import tempfile
import unittest
import zipfile
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


class PageBreakTableTests(unittest.TestCase):
    """쪽 나눔(Ctrl+Enter)으로 새 쪽을 시작하는 표는 앞 문장과 표 묶음이 아니다.

    실측(10월 확대간부회의 자료): 각 과 자료의 마지막 'ㅇ 동주민센터: …'와 쪽 나눔 뒤 다음 자료의
    제목 표를 한 묶음으로 보아 저장 결과 검수가 '[표 묶음 쪽 분리]' 5건을 실패로 냈다.
    """

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def write_hwpx(self, folder):
        hp = 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
        table = '<hp:tbl rowCnt="2" colCnt="1"/>'
        section = (f'<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" {hp}>'
                   '<hp:p pageBreak="0"><hp:run><hp:t>ㅇ 동주민센터: 홍보</hp:t></hp:run></hp:p>'
                   f'<hp:p pageBreak="1"><hp:run>{table}</hp:run></hp:p>'
                   f'<hp:p pageBreak="0"><hp:run>{table}</hp:run></hp:p></hs:sec>')
        path = Path(folder) / 'doc.hwpx'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('Contents/section0.xml', section)
        return path

    def remember(self, tables):
        fn = self.ns['본문_쪽나눔_기억']
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_hwpx(folder)
            with patch.dict(fn.__globals__, {'_서식통일_현재_HWPX': lambda: path, '진단로그': Mock()}):
                fn(tables)
        return set(fn.__globals__['_쪽나눔문단'])

    def test_page_break_paragraphs_are_read_from_hwpx(self):
        self.assertEqual(self.remember({1: (0, 1, 0), 2: (0, 2, 0)}), {1})

    def test_mismatched_table_positions_are_not_trusted(self):
        # 저장 뒤 문단이 바뀌어 표 위치가 다르면 다른 문단을 쪽 나눔으로 볼 수 있으므로 쓰지 않는다.
        self.assertEqual(self.remember({2: (0, 2, 0), 3: (0, 3, 0)}), set())

    def collect(self, page_breaks, midtitle=False):
        fn = self.ns['보고서_표묶음_수집']
        cursor = [(0, 65, 0)]
        hwp = Mock()
        hwp.SetPos.side_effect = lambda *pos: cursor.__setitem__(0, tuple(pos))
        hwp.GetPos.side_effect = lambda: cursor[0]
        with patch.dict(fn.__globals__, {'hwp': hwp, '보고서_본문묶음_수집': lambda pos: LEAD,
                                         '현재문단_텍스트': lambda: '', 'hwp_run': Mock(),
                                         '중단_요청됨': lambda: False, '_쪽나눔문단': page_breaks,
                                         '로마자_중제목_표인가': lambda key: midtitle}):
            return fn((0, 65, 0), {66: KEY})

    def test_table_after_page_break_is_not_a_bundle(self):
        self.assertEqual(self.collect(set())[3], KEY)   # 쪽 나눔이 없으면 표 묶음
        self.assertIsNone(self.collect({66}))

    def test_roman_midtitle_table_is_not_a_bundle(self):
        # 'Ⅱ | 추진 계획' 중제목 표는 앞 문장의 표가 아니라 다음 □ 묶음의 머리다.
        self.assertIsNone(self.collect(set(), midtitle=True))


class MidtitlePageTests(unittest.TestCase):
    """로마자 중제목이 앞쪽 끝에 홀로 남으면 중제목 앞에서 쪽을 나눈다(소제목과 같은 규칙)."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_roman_number_pattern(self):
        pattern = self.ns['_로마자_중제목_번호']
        for text in ('Ⅰ', 'Ⅱ.', 'Ⅻ', 'IV'):
            self.assertTrue(pattern.match(text), text)
        for text in ('1', '가.', '추진 배경', 'Ⅱ 추진'):
            self.assertFalse(pattern.match(text), text)

    def test_bundle_is_midtitle_heading_and_first_circle_unit(self):
        # Ⅱ 추진 계획 + □ 단계별 추진 일정 + ㅇ (1단계) + - 입자가속기 … 은 쪼갤 수 없는 하나의 묶음이다.
        fn = self.ns['중제목_묶음_문단']
        group = [((0, i, 0), (0, i, 9), role) for i, role in
                 enumerate(['소제목', '본문', '내용', '본문', '내용'], start=11)]
        with patch.dict(fn.__globals__, {'보고서_소제목묶음_수집': lambda pos: group}):
            self.assertEqual(fn((0, 11, 0)), group[:3])
        only = group[:1] + [((0, 12, 0), (0, 12, 9), '부연설명')]
        with patch.dict(fn.__globals__, {'보고서_소제목묶음_수집': lambda pos: only}):
            self.assertEqual(fn((0, 11, 0)), only)

    def fix(self, measures, move='실패', page_break=False, next_break=False):
        fn = self.ns['중제목_외톨이_정리']
        measures = list(measures)
        breaks = []
        stats = {'대상': 0, '성공': 0, '실패': 0}
        hwp = Mock()
        hwp.GetPos.return_value = (0, 1, 0)
        mover = Mock(return_value=move)
        breaker = Mock(return_value=page_break)
        with patch.dict(fn.__globals__, {
            'hwp': hwp, 'hwp_run': Mock(), '로그': Mock(), '검수_문제_기록': Mock(), '현재_처리파일': '',
            '쪽범위_사용중': lambda: False, '세트문장_통계': stats,
            '중제목_묶음_문단': lambda pos: [((0, 11, 0), (0, 11, 9), '소제목')],
            '중제목_묶음_쪽': lambda mid, paras: measures.pop(0) if len(measures) > 1 else measures[0],
            '_묶음_같은쪽_이동': mover, '_묶음_쪽나눔_이동': breaker,
            '쪽나눔_켜짐': lambda pos: next_break,
            '쪽나눔_설정': lambda pos, on: breaks.append((pos, on)),
        }):
            moved = fn({'위치': (0, 10, 0), '표키': (0, 10, 0), '다음': (0, 11, 0), '요약': '□ 추진 계획'})
        return moved, mover, breaker, breaks, stats

    def test_bundle_on_one_page_is_left_alone(self):
        moved, mover, breaker, breaks, stats = self.fix([({2: 4}, (2, 2))])
        self.assertFalse(moved)
        mover.assert_not_called()
        self.assertEqual((breaks, stats['대상']), ([], 0))

    def test_midtitle_alone_at_page_end_is_pushed(self):
        moved, mover, _, _, stats = self.fix([({2: 4}, (1, 1))], move='성공')
        self.assertTrue(moved)
        self.assertTrue(mover.call_args.args[3])            # 뒤쪽 줄이 많으면 민다(줄간격 확대)
        self.assertEqual(mover.call_args.kwargs['표키'], (0, 10, 0))
        self.assertEqual(stats['성공'], 1)

    def test_only_last_dash_line_spilling_is_pulled_back(self):
        # 중제목·□·ㅇ는 앞쪽, '- 입자가속기 …'만 뒤쪽이면 당긴다(줄간격 축소).
        moved, mover, _, _, _ = self.fix([({1: 3, 2: 1}, (1, 1))], move='성공')
        self.assertTrue(moved)
        self.assertFalse(mover.call_args.args[3])

    def test_page_break_when_line_spacing_fails(self):
        moved, _, breaker, _, _ = self.fix([({2: 4}, (1, 1))], page_break=True)
        self.assertTrue(moved)
        self.assertEqual(breaker.call_args.args[0], (0, 10, 0))   # 중제목 앞에서 쪽 나눔

    def test_page_break_of_following_heading_is_released_first(self):
        # □가 이미 쪽 나눔으로 다음 쪽에 갔으면 그 쪽 나눔을 풀어 본다(둘 다 켜면 □가 한 쪽 더 밀림).
        moved, mover, _, breaks, _ = self.fix([({2: 4}, (1, 1)), ({1: 4}, (1, 1))], next_break=True)
        self.assertTrue(moved)
        self.assertEqual(breaks, [((0, 11, 0), False)])
        mover.assert_not_called()

    def test_failed_move_restores_page_break(self):
        moved, _, _, breaks, stats = self.fix([({2: 4}, (1, 1))], next_break=True)
        self.assertFalse(moved)
        self.assertEqual(breaks, [((0, 11, 0), False), ((0, 11, 0), True)])
        self.assertEqual(stats['실패'], 1)

if __name__ == '__main__':
    unittest.main()
