"""Run unittest discovery with native dialogs and actual COM activation forbidden.

The tests' own local mocks still take precedence. An accidental native operation
raises an error; it never creates a fake successful document or pagination result.
"""
from contextlib import ExitStack
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import tkinter.messagebox
    import tkinter.filedialog
    import win32com.client
    import win32com.client.dynamic
    with ExitStack() as stack:
        for target in ('tkinter.messagebox._show', 'tkinter.filedialog.Open.show',
                       'tkinter.filedialog.SaveAs.show', 'tkinter.filedialog.Directory.show',
                       'win32com.client.Dispatch', 'win32com.client.DispatchEx',
                       'win32com.client.GetActiveObject', 'win32com.client.dynamic.Dispatch'):
            stack.enter_context(patch(target, side_effect=RuntimeError('C23: native dialog/COM activation prohibited')))
        suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
