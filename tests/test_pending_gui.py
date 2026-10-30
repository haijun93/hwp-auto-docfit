"""웹 창을 Tk 화면보다 먼저 띄우는 대리 객체(2.0.5 시작 속도)."""
import threading
import unittest
from types import SimpleNamespace

from desktop_web_ui import PendingGui


class PendingGuiTest(unittest.TestCase):
    def test_calls_wait_for_the_real_gui_then_delegate(self):
        ready, holder = threading.Event(), {}
        pending = PendingGui(ready, holder, timeout=5)
        result = []
        worker = threading.Thread(target=lambda: result.append(pending.status))
        worker.start()
        self.assertTrue(worker.is_alive())  # Tk 준비 전에는 기다린다
        holder["gui"] = SimpleNamespace(status="준비됨")
        ready.set()
        worker.join(5)
        self.assertEqual(result, ["준비됨"])
        pending.status = "바뀜"
        self.assertEqual(holder["gui"].status, "바뀜")

    def test_tk_failure_becomes_the_same_start_error(self):
        ready, holder = threading.Event(), {"오류": OSError("Tk")}
        ready.set()
        with self.assertRaisesRegex(RuntimeError, "앱 인터페이스를 시작하지 못했습니다"):
            PendingGui(ready, holder).root
        with self.assertRaises(RuntimeError):
            PendingGui(threading.Event(), {}, timeout=0.01).root


if __name__ == "__main__":
    unittest.main()
