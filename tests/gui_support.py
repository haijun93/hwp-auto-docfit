"""Real Tk roots for GUI tests; unavailable displays are reported as skips."""
import os
from pathlib import Path
import tkinter as tk
from unittest import SkipTest


def gui_root(factory, namespace):
    # GUI constructors create examples/idioms: keep them in each test's APPDATA.
    globals_ = namespace['HwpAutoDocFitGUI'].__init__.__globals__
    base = Path(os.environ['APPDATA']) / 'automation'
    globals_['HWP_AUTOMATION_DIR'] = base
    globals_['DLL_DIR'] = base / 'dll'
    globals_['TARGET_DLL'] = base / 'dll' / 'HwpAutoDocFitSecurity.dll'
    try:
        root = factory()
    except tk.TclError as exc:
        raise SkipTest(f"GUI display/TkDND unavailable: {exc}") from exc
    destroy = root.destroy

    def cleanup():
        # Tests destroy roots directly rather than using the app's close handler.
        for timer in root.tk.call('after', 'info'):
            root.tk.call('after', 'cancel', timer)
        destroy()

    root.destroy = cleanup
    return root
