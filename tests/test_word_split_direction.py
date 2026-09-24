"""Split words move toward the longer half; equal halves or a short last line pull up."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class WordSplitDirectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_direction_rule(self):
        pull = self.ns['어절분리_앞줄당김인가']
        self.assertTrue(pull(2, 2))           # 전기|버스
        self.assertTrue(pull(3, 1))           # 수행하|는
        self.assertFalse(pull(1, 3))          # 실|질적인
        self.assertTrue(pull(1, 3, True))     # 마지막 줄 5자 미만이면 당김

    def _run(self, left, right, 마지막줄_짧음):
        fn = self.ns['단어중간_줄바꿈방지']
        start, boundary = (0, 0, 0), (0, 0, 10)
        word_start, word_end = (0, 0, 9), (0, 0, 13)
        infos = [(start, boundary, word_start, word_end, left, right)]
        saved = []

        class Doc:
            pos = start
            def GetPos(self):
                return self.pos
            def SetPos(self, *pos):
                self.pos = tuple(pos)

        def line_range(p):
            # 밀기가 적용되면 어절 전체가 다음 줄에 놓인 것으로 보고한다.
            if p == word_start:
                return word_start, (0, 0, 20)
            return start, (0, 0, 9)

        def keep(a, b):
            saved.append(b)
            return [(a, b, (0,) * 7)]

        with patch.dict(fn.__globals__, {
            'hwp': Doc(), 'hwp_run': lambda cmd: True,
            '중단_요청됨': lambda: False,
            '현재줄_끝_괄호내부_공백분리인가': lambda: False,
            '다음단어_당김_시도': lambda *a: False,
            '단어모드_줄범위': line_range,
            '단어모드_분리정보': lambda p: infos.pop() if infos else None,
            '단어모드_범위선택': lambda *a: None,
            '현재선택영역_텍스트': lambda: '실질적인',
            '단어모드_마지막줄_짧은잔여인가': lambda b: 마지막줄_짧음,
            '단어모드_자간보관': keep,
            '단어모드_자간적용': lambda *a: None,
            '단어_장평_추가축소_시도': lambda *a: False,
            '색상_적용_현재선택': lambda: None,
            '단어분리_통계': {'대상': 0, '성공': 0, '실패': 0},
            '진단로그': Mock(), '로그': Mock(), '검수_문제_기록': Mock(),
        }):
            self.assertTrue(fn(5))
        return saved, word_start, word_end

    def test_longer_tail_pushes_head_to_next_line_first(self):
        saved, word_start, _ = self._run(1, 3, False)
        self.assertEqual(saved, [word_start])

    def test_equal_halves_pull_first(self):
        saved, word_start, word_end = self._run(2, 2, False)
        self.assertEqual(saved, [word_end, word_start])

    def test_short_last_line_pulls_first(self):
        saved, word_start, word_end = self._run(1, 3, True)
        self.assertEqual(saved, [word_end, word_start])


if __name__ == '__main__':
    unittest.main()
