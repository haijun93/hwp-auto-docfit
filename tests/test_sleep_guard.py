"""처리 중 절전 방지는 켜고 끌 때 올바른 플래그를 넘긴다."""
from pathlib import Path
import ctypes
import runpy
import sys
import unittest
from unittest.mock import patch


@unittest.skipUnless(sys.platform == 'win32', 'Windows 전용')
class SleepGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_flags(self):
        fn = self.ns['절전_방지']
        with patch.object(ctypes.windll.kernel32, 'SetThreadExecutionState') as call:
            fn(True)
            fn(False)
        self.assertEqual([c.args[0] for c in call.call_args_list], [0x80000001, 0x80000000])


if __name__ == '__main__':
    unittest.main()
