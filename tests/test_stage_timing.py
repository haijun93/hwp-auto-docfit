"""문서 처리 단계별 소요 시간 계측(알파 계획 W7-0): 동작은 그대로, 단계가 바뀔 때마다 시간을 모아 요약 로그만 남긴다."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def perf_counter(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class StageTimingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        cls.g = cls.ns['단계시간_시작'].__globals__      # 함수가 실제로 보는 전역(run_path 결과는 사본)

    def setUp(self):
        self.clock = FakeClock()
        self.patch = patch.dict(self.g, {'time': self.clock})
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.addCleanup(lambda: self.ns['단계시간_끝']())

    def test_marks_are_ignored_when_not_measuring(self):
        self.ns['단계시간_구간']('서식통일')          # 계측 중이 아니면 아무 일도 없다.
        self.assertIsNone(self.ns['단계시간_끝']())

    def test_each_stage_gets_the_time_until_the_next_mark(self):
        self.ns['단계시간_시작']()
        self.clock.advance(2)
        self.ns['단계시간_구간']('서식통일')
        self.clock.advance(30)
        self.ns['단계시간_구간']('최종 서식 기준 내어쓰기')
        self.clock.advance(8)
        self.ns['단계시간_구간']('서식통일')          # 같은 이름은 합산하고 횟수를 센다.
        self.clock.advance(10)
        표 = self.ns['단계시간_끝']()
        self.assertAlmostEqual(표['전체'], 50.0)
        self.assertEqual(표['합']['준비'], [2.0, 1])
        self.assertEqual(표['합']['서식통일'], [40.0, 2])
        self.assertEqual(표['합']['최종 서식 기준 내어쓰기'], [8.0, 1])
        self.assertEqual(표['순서'], ['준비', '서식통일', '최종 서식 기준 내어쓰기'])

    def test_stage_display_marks_the_stage(self):
        self.ns['단계시간_시작']()
        self.ns['단계표시']('본문 자간·단어 분리 조정')   # 진행 화면 호출이 곧 구간 표시다.
        self.clock.advance(5)
        표 = self.ns['단계시간_끝']()
        self.assertEqual(표['합']['본문 자간·단어 분리 조정'], [5.0, 1])

    def test_classification_groups_stages(self):
        분류 = self.ns['단계시간_분류']
        self.assertEqual(분류('열기'), '열기·변환')
        self.assertEqual(분류('문단 아래 간격 페이지 맞춤 (재확인)'), '쪽 맞춤·배치')
        self.assertEqual(분류('개별 문단 페이지 배치'), '쪽 맞춤·배치')
        self.assertEqual(분류('자간 조정 후 내어쓰기 2회차'), '내어쓰기 계열')   # 자간보다 내어쓰기가 먼저 걸린다.
        self.assertEqual(분류('최종 서식 기준 내어쓰기'), '내어쓰기 계열')
        self.assertEqual(분류('본문 자간·단어 분리 조정'), '자간·줄 끝')
        self.assertEqual(분류('표/컨트롤 줄 병합'), '자간·줄 끝')
        self.assertEqual(분류('저장 후 규칙 검수'), '저장·검수')
        self.assertEqual(분류('서식통일'), '서식·기타')
        self.assertEqual(분류('표 서식'), '서식·기타')

    def test_summary_lines_report_total_groups_and_top_stages(self):
        표 = {'전체': 100.0, '순서': ['서식통일', '개별 문단 페이지 배치', '저장'],
              '합': {'서식통일': [40.0, 1], '개별 문단 페이지 배치': [50.0, 2], '저장': [10.0, 1]}}
        줄 = self.ns['단계시간_요약줄'](표, '보고서.hwp')
        self.assertEqual(len(줄), 3)
        self.assertIn('보고서.hwp: 전체 100.0초 (단계 3종)', 줄[0])
        self.assertTrue(줄[1].startswith('[처리 시간 계측] 분류별: 쪽 맞춤·배치 50.0초(50%)'))
        self.assertIn('서식·기타 40.0초(40%)', 줄[1])
        self.assertIn('개별 문단 페이지 배치 50.0초(50%, 2회)', 줄[2])
        self.assertLess(줄[2].index('개별 문단 페이지 배치'), 줄[2].index('서식통일'))   # 오래 걸린 순

    def test_wrapper_logs_the_summary_and_turns_measuring_off(self):
        g = self.g
        logs = []

        def body(파일, index, total, 문장부호기능=True):
            g['단계표시']('서식통일')
            self.clock.advance(7)
            g['단계표시']('저장')
            self.clock.advance(3)
            return True

        with patch.dict(g, {'_문서_처리_본체': body, '로그': logs.append}):
            self.assertTrue(g['문서_처리']('C:/문서/보고서.hwp', 1, 1))
        self.assertEqual(len(logs), 3)
        self.assertIn('보고서.hwp: 전체 10.0초', logs[0])
        self.assertIsNone(g['_단계시간표'])

    def test_wrapper_logs_the_summary_even_when_the_body_fails(self):
        g = self.g
        logs = []

        def body(파일, index, total, 문장부호기능=True):
            g['단계표시']('서식통일')
            self.clock.advance(4)
            raise RuntimeError('중단')

        with patch.dict(g, {'_문서_처리_본체': body, '로그': logs.append}):
            with self.assertRaises(RuntimeError):
                g['문서_처리']('보고서.hwp', 1, 1)
        self.assertEqual(len(logs), 3)
        self.assertIsNone(g['_단계시간표'])


if __name__ == '__main__':
    unittest.main()
