"""서식 보관 중 글자 위치를 확인하지 못해도 문서 처리를 멈추지 않는다(2026-10-11 실측: 표 칸 '다음 단어 당김')."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch


class FormatPreserveFailureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_position_failure_returns_none_instead_of_raising(self):
        fn = self.ns['단어모드_서식보관']
        run = Mock()
        with patch.dict(fn.__globals__, {'자간조정_본문범위': lambda a, b: (a, b), '_단어모드_다음위치': lambda pos: None,
                                         '중단_요청됨': lambda: False, 'hwp_run': run, '진단로그': Mock()}):
            self.assertIsNone(fn((4, 0, 33), (4, 0, 39)))
        run.assert_called_with('Cancel')


if __name__ == '__main__':
    unittest.main()
