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


# 2.0.5 오류 재현용: 실제 화면 클래스의 메서드가 담긴 모듈 전역에서 한/글 생성 함수를 찾는다.
REGISTER_MODULE_NAME, REGISTER_MODULE_VALUE = "FilePathCheckDLL", "Test"


class _App:
    def RegisterModule(self, name, value):
        return True

    class XHwpWindows:
        @staticmethod
        def Item(index):
            return SimpleNamespace(Visible=True)


def 한글_COM_인스턴스_생성(독립=False):
    return _App()


class _FakeGui:
    running = False

    def 파일포맷_변경_시작(self):
        pass


class PendingGuiBridgeTest(unittest.TestCase):
    def test_hangul_factory_works_while_gui_is_a_pending_proxy(self):
        from desktop_web_ui import DesktopWebBridge
        ready, holder = threading.Event(), {"gui": _FakeGui()}
        ready.set()
        bridge = DesktopWebBridge(PendingGui(ready, holder))
        self.assertIsInstance(bridge._table_units_hwp(), _App)
