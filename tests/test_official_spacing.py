"""「2025 행정업무운영 편람」 띄어쓰기 규정: '끝.' 앞·'붙임' 뒤 2타, 날짜 '2021. 12. 12.'(0 생략)."""
from pathlib import Path
import runpy
import unittest

from docfit_core.document_rules import normalize_official_spacing as fix, official_double_space_spans


class OfficialSpacingTest(unittest.TestCase):
    def test_end_mark_has_two_spaces(self):
        self.assertEqual(fix('붙임: 세부 시행계획 1부. 끝.'), '붙임: 세부 시행계획 1부.  끝.')
        self.assertEqual(fix('협조하여 주시기 바랍니다.끝.'), '협조하여 주시기 바랍니다.  끝.')
        self.assertEqual(fix('바랍니다.    끝.'), '바랍니다.  끝.')
        self.assertEqual(fix('바랍니다.  끝.'), '바랍니다.  끝.')
        self.assertEqual(fix(' 끝.'), '  끝.')                      # 표 아래 '끝.'만 있는 줄
        self.assertEqual(fix('작업이 끝.'), '작업이 끝.')            # 마침표 뒤가 아니면 끝 표시가 아니다

    def test_attachment_label_has_two_spaces(self):
        self.assertEqual(fix('붙임 1. 서식승인 목록 1부.'), '붙임  1. 서식승인 목록 1부.')
        self.assertEqual(fix('붙임 계획서 1부. 끝.'), '붙임  계획서 1부.  끝.')
        self.assertEqual(fix('붙임 : 1. 계획서 1부.'), '붙임 : 1. 계획서 1부.')   # 쌍점 꼴은 그대로
        self.assertEqual(fix('붙임 자료를 참고하여 작성'), '붙임 자료를 참고하여 작성')  # 붙임 표시문이 아님

    def test_dates_use_dot_space_without_zero(self):
        self.assertEqual(fix('2021.12.12. 개최'), '2021. 12. 12. 개최')
        self.assertEqual(fix('1985. 09. 06.(금)'), '1985. 9. 6.(금)')
        self.assertEqual(fix('’26.3.5.~3.9.'), '’26. 3. 5.~3.9.')
        self.assertEqual(fix('버전 1.2.3.'), '버전 1.2.3.')
        self.assertEqual(fix('2026.13.40.'), '2026.13.40.')        # 날짜가 아닌 수

    def test_double_space_spots_are_kept_by_space_cleanup(self):
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        targets = ns['단어사이_연속공백_정리_대상']
        self.assertEqual(targets('붙임  계획서 1부.  끝.'), [])
        self.assertEqual(targets('바랍니다.  끝.'), [])
        self.assertEqual(targets('주민  편의를 위한 계획.  끝.'), [(2, 4)])   # 다른 연속 공백은 그대로 줄인다
        self.assertEqual(official_double_space_spans('붙임  계획서 1부.  끝.'), [(2, 4), (11, 13)])


if __name__ == '__main__':
    unittest.main()
