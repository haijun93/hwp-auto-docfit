"""서식 보관 한 번 읽기와, 페이지 수 맞춤의 문단 위 간격 보완·실패 시 복원."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class FormatSaveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_single_pass_reads_spacing_and_ratio_without_text(self):
        fn = self.ns['단어모드_서식보관']
        spacing = [0, 0, -3, -3, 0]
        ratio = [100, 95, 95, 100, 100]

        class CharShape:
            HSet = None

            def __getattr__(self, name):
                i = doc.selection
                if name.startswith('Spacing'):
                    return spacing[i]
                if name.startswith('Ratio'):
                    return ratio[i]
                raise AttributeError(name)

        class Doc:
            pos = (0, 0, 0)
            selection = None
            HParameterSet = type('P', (), {'HCharShape': type('H', (), {'HSet': None})()})()
            HAction = type('A', (), {'GetDefault': lambda self, *a: None})()
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos)
            def SelectText(self, sp, spos, ep, epos):
                self.selection = spos
                return True

        doc = Doc()
        doc.HParameterSet.HCharShape = CharShape()

        def run(cmd):
            if cmd == 'MoveNextChar':
                doc.pos = (0, 0, min(5, doc.pos[2] + 1))

        forbidden = Mock(side_effect=AssertionError('글자 내용을 읽으면 안 됨'))
        with patch.dict(fn.__globals__, {
            'hwp': doc, 'hwp_run': run, '중단_요청됨': lambda: False,
            '자간조정_본문범위': lambda a, b: (a, b),
            '단어모드_한글자': forbidden, '현재선택영역_텍스트': forbidden,
        }):
            spacing_runs, ratio_runs = fn((0, 0, 0), (0, 0, 5))
        self.assertEqual([(a[2], b[2], v[0]) for a, b, v in spacing_runs],
                         [(0, 2, 0), (2, 4, -3), (4, 5, 0)])
        self.assertEqual([(a[2], b[2], v[0]) for a, b, v in ratio_runs],
                         [(0, 1, 100), (1, 3, 95), (3, 5, 100)])

    def test_ratio_step_reuses_values_read_by_caller(self):
        fn = self.ns['단어_장평_추가축소_시도']
        reader = Mock(side_effect=AssertionError('다시 읽으면 안 됨'))
        runs = ([((0, 0, 0), (0, 0, 3), (0,) * 7)], [((0, 0, 0), (0, 0, 3), (100,) * 7)])
        with patch.dict(fn.__globals__, {
            '단어모드_서식보관': reader, '단어모드_자간적용': lambda *a: None,
            '단어모드_장평적용': lambda *a: None, '최소_성공단계_탐색': lambda *a, **k: 3,
            '진단로그': Mock(),
        }):
            self.assertTrue(fn((0, 0, 0), (0, 0, 3), (0, 0, 0), (0, 0, 9), 5, 보관=runs))
        reader.assert_not_called()


class PageFitFallbackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def _fit(self, below_changes, above_pages, splits=()):
        """splits: 목표 쪽 수에 닿았을 때마다 돌려줄 '묶음 걸림' 여부."""
        fn = self.ns['보고서_페이지수_맞춤_시도']
        g = fn.__globals__
        calls, restored = [], []
        below = iter(below_changes)
        pages = iter(above_pages)
        split_iter = iter(splits)

        def adjust(delta, 최소쪽=None, 위간격=False, 원래값=None):
            calls.append('위' if 위간격 else '아래')
            count = 3 if 위간격 else next(below, 0)
            if count and 원래값 is not None:
                원래값.setdefault((0, len(calls)), 10.0)
            return count

        with patch.dict(g, {
            'hwp': object(), '중단_요청됨': lambda: False, '로그': Mock(),
            '구조문단_간격_일괄조정': adjust,
            '마지막쪽_화면줄수': lambda: (next(pages, 4), 1),
            '쪽맞춤_묶음분리_있음': lambda 최소쪽=None: calls.append(f'묶음검사:{최소쪽}') or next(split_iter, False),
            '구조문단_간격_복원': lambda values, 위간격=False: restored.append((위간격, len(values))) or len(values),
            '페이지맞춤_최대_pt': 3.0, '페이지맞춤_스텝_pt': 1.0, '페이지맞춤_뒤쪽범위_쪽수': 2,
            '페이지맞춤_묶음확인_추가단계': 4, '쪽맞춤_묶음_확인됨': False, '쪽맞춤_묶음이동_결정': False,
        }):
            result = fn(3)
            confirmed = g['쪽맞춤_묶음_확인됨']
            self.move_decided = g['쪽맞춤_묶음이동_결정']
        # 묶음 검사는 간격을 바꾸는 쪽(최소쪽 = 목표 3 - 뒤쪽범위 2 = 1)부터만 본다.
        checks = [c for c in calls if c.startswith('묶음검사')]
        self.assertTrue(all(c == '묶음검사:1' for c in checks), checks)
        calls = [c for c in calls if not c.startswith('묶음검사')]
        return result, calls, restored, confirmed

    def test_uses_paragraph_top_spacing_when_bottom_spacing_is_zero(self):
        result, calls, restored, confirmed = self._fit([0], [4, 3])
        self.assertTrue(result)
        self.assertTrue(confirmed)                      # 묶음도 온전
        self.assertEqual(calls, ['아래', '위', '위'])
        self.assertEqual(restored, [])

    def test_keeps_shrinking_until_groups_are_intact(self):
        result, calls, restored, confirmed = self._fit([0], [3, 3], splits=[True, False])
        self.assertTrue(result)
        self.assertTrue(confirmed)
        self.assertEqual(calls, ['아래', '위', '위'])
        self.assertEqual(restored, [])

    def test_falls_back_to_first_step_that_reached_target(self):
        # 1단계에서 3쪽에 닿았지만 끝까지 묶음이 걸림 → 되돌린 뒤 1단계만 다시 적용.
        result, calls, restored, confirmed = self._fit([0], [3, 3, 3], splits=[True, True, True])
        self.assertTrue(result)
        self.assertFalse(confirmed)                     # 쪽 배치가 묶음을 옮겨야 함
        self.assertTrue(self.move_decided)              # 재확인에서 다시 줄이지 않음
        self.assertEqual(calls, ['아래', '위', '위', '위', '위'])
        self.assertEqual(restored, [(True, 3), (False, 0)])

    def test_failure_restores_all_changed_spacing(self):
        result, calls, restored, confirmed = self._fit([2, 2, 2], [4, 4, 4, 4, 4, 4])
        self.assertFalse(result)
        self.assertFalse(confirmed)
        self.assertFalse(self.move_decided)
        self.assertEqual(calls, ['아래'] * 3 + ['위'] * 3)
        self.assertEqual(restored, [(True, 3), (False, 3)])


    def test_whole_pass_clears_previous_document_decision(self):
        fn = self.ns['보고서_페이지수_맞춤_전체_적용']
        g = fn.__globals__
        with patch.dict(g, {
            '쪽맞춤_묶음_확인됨': True, '쪽맞춤_묶음이동_결정': True,
            '페이지맞춤_문단간격_사용': True, '중단_요청됨': lambda: False,
            '마지막쪽_화면줄수': lambda: (3, 25), '페이지맞춤_최대남은줄수': 3,
        }):
            self.assertTrue(fn())
            self.assertFalse(g['쪽맞춤_묶음_확인됨'])
            self.assertFalse(g['쪽맞춤_묶음이동_결정'])


class PageFitTimingTest(unittest.TestCase):
    """쪽 수 맞춤 소요 시간 계측: 동작은 그대로, 단계마다 한 줄과 끝에 합계 한 줄만 로그로 남는다."""

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_helpers_only_record_while_active_and_report_differences(self):
        g = self.ns
        add, start, end = g['쪽맞춤_계측_더하기'], g['쪽맞춤_계측_시작'], g['쪽맞춤_계측_끝']
        add('쪽측정', 5.0, 1)                       # 시작 전에는 기록하지 않는다.
        start()
        add('쪽측정', 1.5, 1)
        before = g['쪽맞춤_계측_복사']()
        add('쪽측정', 2.0, 1)
        add('표스캔', 4.0)
        diff = g['쪽맞춤_계측_차이'](before)
        self.assertEqual(diff['쪽측정'], (2.0, 1))
        self.assertEqual(diff['표스캔'], (4.0, 0))
        self.assertEqual(end()['쪽측정'], [3.5, 2])
        self.assertEqual(g['쪽맞춤_계측_끝'](), {})  # 끝낸 뒤에는 비어 있고 더 쌓지 않는다.
        add('쪽측정', 9.0, 1)
        self.assertEqual(g['쪽맞춤_계측값'], None)

    def test_fit_logs_one_line_per_step_and_a_summary(self):
        fn = self.ns['보고서_페이지수_맞춤_시도']
        g = fn.__globals__
        logs = []
        pages = iter([4, 4, 4, 4, 4, 4])

        def adjust(delta, 최소쪽=None, 위간격=False, 원래값=None):
            g['쪽맞춤_계측_더하기']('문단순회', 0.5, 7)
            g['쪽맞춤_계측_더하기']('문단쓰기', 0.25, 2)
            return 2

        with patch.dict(g, {
            'hwp': object(), '중단_요청됨': lambda: False, '로그': logs.append,
            '구조문단_간격_일괄조정': adjust, '구조문단_간격_복원': lambda values, 위간격=False: 0,
            '마지막쪽_화면줄수': lambda: (next(pages, 4), 1),
            '쪽맞춤_묶음분리_있음': lambda 최소쪽=None: False,
            '페이지맞춤_최대_pt': 2.0, '페이지맞춤_스텝_pt': 1.0, '페이지맞춤_뒤쪽범위_쪽수': 2,
            '페이지맞춤_묶음확인_추가단계': 4, '쪽맞춤_묶음_확인됨': False, '쪽맞춤_묶음이동_결정': False,
        }):
            self.assertFalse(fn(3))
        steps = [m for m in logs if m.startswith('[쪽 수 맞춤 계측]')]
        summary = [m for m in logs if m.startswith('[쪽 수 맞춤 계측 합계]')]
        self.assertEqual(len(steps), 4)                 # 아래 간격 2단계 + 위 간격 2단계
        self.assertIn('문단 간격', steps[0])
        self.assertIn('순회 0.5', steps[0])
        self.assertIn('훑은 문단 7개·바꾼 2곳', steps[0])
        self.assertEqual(len(summary), 1)
        self.assertIn('실패/원복', summary[0])
        self.assertIn('쪽 측정 4회', summary[0])
        self.assertIsNone(g['쪽맞춤_계측값'])           # 끝나면 계측이 꺼진다.

    def test_table_margin_pass_records_scan_read_and_write(self):
        fn = self.ns['표_셀_세로여백_일괄조정']
        g = fn.__globals__

        class Doc:
            HParameterSet = object()
            pos = (0, 0, 0)

            def GetPos(self):
                return self.pos

            def SetPos(self, *pos):
                self.pos = tuple(pos)

        written = []
        g['쪽맞춤_계측_시작']()
        try:
            with patch.dict(g, {
                'hwp': Doc(), '중단_요청됨': lambda: False, '로그': Mock(),
                '페이지맞춤_표셀세로여백_사용': True, '페이지맞춤_최대_pt': 10.0, '페이지맞춤_스텝_pt': 1.0,
                '페이지맞춤_표셀세로여백_최소_pt': 0.0,
                '한칸표_영역_목록': lambda: [],
                '표칸_묶음_키별': lambda: {('k',): [(2, 'A1', 0), (3, 'B1', 0)]},
                '현재_페이지번호': lambda: 5,
                '셀_세로여백_읽기': lambda: (1, 500, 500),
                '셀_세로여백_현재선택': lambda **kw: written.append(kw) or True,
            }):
                changed = fn(5, 최소쪽=1, 원래값={})
            값 = g['쪽맞춤_계측값']
        finally:
            g['쪽맞춤_계측_끝']()
        self.assertEqual(changed, 2)
        self.assertEqual(len(written), 2)
        self.assertEqual(값['표셀읽기'][1], 2)
        self.assertEqual(값['표셀쓰기'][1], 2)
        self.assertIn('표스캔', 값)


if __name__ == '__main__':
    unittest.main()
