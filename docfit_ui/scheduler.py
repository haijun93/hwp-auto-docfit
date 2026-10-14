"""Owner-thread event pump for bridge commands, including nested Tcl waits.

Install on the Tk owner thread during GUI construction. RPC threads enqueue
Python callables only; they never register a Tcl callback from a foreign thread.
The next tick is scheduled before dispatch so a Flutter confirmation may use a
nested Tcl wait while later RPC replies continue to be serviced.
"""
from queue import Empty, Queue
import time


def install_scheduler(gui):
    if hasattr(gui, '_bridge_callbacks'):
        return
    gui._bridge_callbacks = Queue()
    gui._bridge_scheduler_closed = False

    def pump():
        if gui._bridge_scheduler_closed:
            return
        try:
            gui.root.after(10, pump)
        except Exception:
            gui._bridge_scheduler_closed = True
            return
        deadline = time.monotonic() + 0.01
        for _ in range(32):
            try:
                callback = gui._bridge_callbacks.get_nowait()
            except Empty:
                break
            callback()
            if time.monotonic() >= deadline:
                break

    gui.root.after(0, pump)
