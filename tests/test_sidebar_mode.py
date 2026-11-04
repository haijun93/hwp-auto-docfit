import unittest
from docfit_app.sidebar_mode import SidebarModeController, choose_side


class FakeApi:
    def __init__(self, area=(100, 40, 1100, 840)):
        self.area, self.positions = area, []
    def work_area(self, hwnd): return self.area
    def set_window_pos(self, hwnd, x, y, width, height, topmost):
        self.positions.append((hwnd, x, y, width, height, topmost))


class FakeWindow:
    def __init__(self, rect=(600, 100, 800, 600), topmost=False):
        self.rect, self.on_top, self.only = rect, topmost, None
    def handle(self): return 42
    def geometry(self): return self.rect
    def topmost(self): return self.on_top
    def set_sidebar_only(self, value): self.only = value


class SidebarModeTests(unittest.TestCase):
    def test_side_choice_and_remembered_tie(self):
        self.assertEqual(choose_side(180, 100, 1100), 'left')
        self.assertEqual(choose_side(1020, 100, 1100), 'right')
        self.assertEqual(choose_side(600, 100, 1100, 'left'), 'left')

    def test_geometry_work_area_and_restore_state(self):
        api, window = FakeApi(), FakeWindow(topmost=True)
        controller = SidebarModeController(api, window, True)
        result = controller.toggle(True)
        self.assertEqual(result['side'], 'right')
        self.assertEqual(api.positions[-1], (42, 910, 40, 190, 800, True))
        self.assertTrue(window.only)
        controller.toggle(False)
        self.assertEqual(api.positions[-1], (42, 600, 100, 800, 600, True))
        self.assertFalse(window.only)

    def test_developer_mode_denied(self):
        controller = SidebarModeController(FakeApi(), FakeWindow(), False)
        with self.assertRaises(PermissionError):
            controller.toggle(True)

    def test_win32_calls_are_injectable(self):
        from desktop_web_ui import _Win32WindowApi
        class User32:
            def __init__(self): self.calls = []
            def SystemParametersInfoW(self, action, _, rect, flags):
                rect._obj.left, rect._obj.top, rect._obj.right, rect._obj.bottom = 10, 20, 1010, 720
                self.calls.append(('work', action))
                return 1
            def SetWindowPos(self, *args): self.calls.append(('position', args)); return 1
        fake = User32()
        api = _Win32WindowApi(fake)
        self.assertEqual(api.work_area(55), (10, 20, 1010, 720))
        api.set_window_pos(55, 10, 20, 190, 700, True)
        self.assertEqual(fake.calls[0], ('work', api.SPI_GETWORKAREA))
        self.assertEqual(fake.calls[1][0], 'position')


if __name__ == '__main__':
    unittest.main()
