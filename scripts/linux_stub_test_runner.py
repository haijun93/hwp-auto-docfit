"""Linux·클라우드 세션용 시험 실행기: Windows·Tk 전용 모듈을 가짜로 대체해 앱 본체를 임포트한다.

Windows 개발 PC에서는 필요 없다(정식 시험은 `python -m unittest discover -s tests`).
Windows 전용 모듈만 대체한다. Tk/TkDND·pywebview·XML은 실제 의존성을 사용한다.
GUI 시험은 실제 디스플레이 또는 Xvfb가 필요하다. 한/글 COM 동작은 검증하지 못한다.

사용법(저장소 루트에서):
    python3 scripts/linux_stub_test_runner.py discover -s tests
    python3 scripts/linux_stub_test_runner.py tests.test_stage_timing
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

for name in ('winreg', 'pythoncom', 'win32com', 'win32com.client', 'win32gui', 'win32con',
             'win32api', 'win32process', 'win32clipboard', 'pywintypes'):
    sys.modules.setdefault(name, MagicMock())
# Linux has no registry: report missing keys instead of returning untyped mocks.
# Tests that need registry data replace these functions explicitly.
sys.modules['winreg'].OpenKey.side_effect = FileNotFoundError("Windows registry unavailable")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
require_gui = '--require-gui' in sys.argv
if require_gui:
    sys.argv.remove('--require-gui')


class GuiRequiredResult(unittest.TextTestResult):
    def addSkip(self, test, reason):
        if require_gui and any(term in reason.lower() for term in ('display', 'gui', 'tkinter', '화면')):
            error = AssertionError(f"GUI execution required; unexpected skip: {reason}")
            self.addFailure(test, (AssertionError, error, None))
        else:
            super().addSkip(test, reason)


runner = unittest.TextTestRunner(resultclass=GuiRequiredResult)
unittest.main(module=None, argv=['x'] + sys.argv[1:], testRunner=runner)
