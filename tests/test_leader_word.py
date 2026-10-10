"""연결 부호 어절('------', '……', '.....')은 한 어절로 보고 필요하면 한도를 넘어 줄이거나 개수를 줄인다(2026-10-10)."""
from pathlib import Path
import runpy
import unittest


class LeaderWordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_leader_span_detection(self):
        구간 = self.ns['연결부호_구간']
        self.assertEqual(구간("------"), (0, 6))
        self.assertEqual(구간("추진배경.......3"), (4, 11))
        self.assertEqual(구간("가……나"), None)                 # '…' 두 개는 연결 부호로 보지 않는다(3개부터)
        self.assertEqual(구간("가………나"), (1, 4))
        self.assertEqual(구간("2026-10-10"), None)            # 날짜·전화의 '-' 하나는 아니다
        self.assertEqual(구간("A--B----C"), (4, 8))           # 가장 긴 구간
        self.assertIsNone(구간("보통 어절"))

    def test_connector_units_three_kinds(self):
        단위들 = self.ns['연결부호_단위들']
        def 단위(t):
            return [t[a:b] for a, _, _, b in 단위들(t)]
        self.assertEqual(단위("ㅇ 일정 추진------------결과 확인"), ["추진------------결과"])     # 선
        self.assertEqual(단위("세부내용..........3쪽"), ["세부내용..........3쪽"])               # 점
        self.assertEqual(단위("세부내용      3쪽"), ["세부내용      3쪽"])                       # 여러 칸 빈칸
        self.assertEqual(단위("가나 ----- 다라"), ["가나 ----- 다라"])                           # 부호 양옆 빈칸 1칸
        self.assertEqual(단위("두 칸  공백"), [])
        self.assertEqual(단위("2026-10-10"), [])

    def test_connector_tab_is_kept(self):
        # 여러 줄 연결 부호는 앞 단계에서 탭 하나로 바뀐다. 글 사이 탭 하나는 정렬용이라 남긴다.
        대상 = self.ns['단어사이_연속공백_정리_대상']
        self.assertEqual(대상("Ⅰ. 추진 배경	가쪽"), [])
        self.assertEqual(대상("가	나	다"), [(1, 2), (3, 4)])

    def test_minimum_kept(self):
        self.assertEqual(self.ns['연결부호_최소개수'], 2)


if __name__ == '__main__':
    unittest.main()
