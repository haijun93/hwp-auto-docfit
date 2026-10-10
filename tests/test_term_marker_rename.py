"""용어 변경(문두기호 → 항목기호, 2026-10-10): 예전 서식 프로필의 '문두기호_역할' 키도 읽는다."""
from pathlib import Path
import runpy
import unittest


class MarkerTermRenameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_old_profile_key_is_still_read(self):
        g = self.ns['항목기호_역할표'].__globals__
        원래 = g['표준서식_설정']
        try:
            g['표준서식_설정'] = {"문두기호_역할": {"□": "소제목"}}
            self.assertEqual(self.ns['항목기호_역할표'](), {"□": "소제목"})
            g['표준서식_설정'] = {"항목기호_역할": {"□": "본문"}, "문두기호_역할": {"□": "소제목"}}
            self.assertEqual(self.ns['항목기호_역할표'](), {"□": "본문"})
        finally:
            g['표준서식_설정'] = 원래


if __name__ == '__main__':
    unittest.main()
