"""Linux·클라우드 세션용 시험 실행기: Windows·Tk 전용 모듈을 가짜로 대체해 앱 본체를 임포트한다.

Windows 개발 PC에서는 필요 없다(정식 시험은 `python -m unittest discover -s tests`).
Linux에는 winreg·pywin32·tkinter가 없어 `hwp-auto-docfit.py`를 임포트할 수 없으므로, 이 실행기가
먼저 가짜 모듈을 끼워 넣은 뒤 unittest를 돌린다. 한/글 동작은 시험하지 못하며, Tk 화면 대화상자 시험
(실패 5·오류 14, 2026-10-09 기준)은 이 환경에서 원래 통과하지 못한다.

사용법(저장소 루트에서):
    python3 scripts/linux_stub_test_runner.py discover -s tests
    python3 scripts/linux_stub_test_runner.py tests.test_stage_timing
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

for name in ('winreg', 'pythoncom', 'win32com', 'win32com.client', 'win32gui', 'win32con', 'tkinterdnd2',
             'win32api', 'win32process', 'win32clipboard', 'pywintypes', 'webview', 'tkinter', 'tkinter.ttk',
             'tkinter.messagebox', 'tkinter.filedialog', 'tkinter.simpledialog', 'defusedxml.sax'):
    sys.modules.setdefault(name, MagicMock())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
unittest.main(module=None, argv=['x'] + sys.argv[1:])
