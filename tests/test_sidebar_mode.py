import unittest
from unittest.mock import Mock

from docfit_app.sidebar_mode import (
    DEFAULT_FRAME_WIDTH, SIDEBAR_RAIL_WIDTH, SidebarModeController, choose_side, sidebar_window_width,
)

# 배율·테두리를 알 수 없을 때(가짜 API): 56 + 16 = 72
BASE_WIDTH = SIDEBAR_RAIL_WIDTH + DEFAULT_FRAME_WIDTH


class FakeApi:
    def __init__(self, area=(100, 40, 1100, 840)):
        self.area, self.positions = area, []
    def work_area(self, hwnd): return self.area
    def set_window_pos(self, hwnd, x, y, width, height, topmost):
        self.positions.append((hwnd, x, y, width, height, topmost))


class ScaledApi(FakeApi):
    """배율 150%, 테두리 24px, 실제 창 위치는 물리 픽셀."""
    def __init__(self, area=(0, 0, 2880, 1680), scale=1.5, frame=24, rect=(900, 150, 1200, 900)):
        super().__init__(area)
        self.scale, self.frame, self.rect, self.fail = scale, frame, rect, False
    def dpi_scale(self, hwnd): return self.scale
    def frame_width(self, hwnd): return self.frame
    def window_rect(self, hwnd): return self.rect
    def set_window_pos(self, hwnd, x, y, width, height, topmost):
        if self.fail:
            raise OSError('앱 창 위치를 바꾸지 못했습니다.')
        super().set_window_pos(hwnd, x, y, width, height, topmost)


class FakeWindow:
    def __init__(self, rect=(600, 100, 800, 600), topmost=False):
        self.rect, self.on_top, self.only = rect, topmost, None
        self.saved_sides = []
    def handle(self): return 42
    def geometry(self): return self.rect
    def topmost(self): return self.on_top
    def set_sidebar_only(self, value): self.only = value
    def save_side(self, side): self.saved_sides.append(side)


class MinSizeWindow(FakeWindow):
    def __init__(self, *args, minimum=(390, 270), log=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.minimum, self.log = minimum, log if log is not None else []
    def min_size(self): return self.minimum
    def set_min_size(self, width, height):
        self.minimum = (width, height)
        self.log.append(('min', width, height))


class SidebarWidthTests(unittest.TestCase):
    def test_width_is_rail_times_scale_plus_frame(self):
        self.assertEqual(sidebar_window_width(1.0, 16), 72)
        self.assertEqual(sidebar_window_width(1.25, 20), 90)
        self.assertEqual(sidebar_window_width(1.5, 24), 108)
        self.assertEqual(sidebar_window_width(1.75, 0), 98)

    def test_width_defaults_when_metrics_unknown_or_invalid(self):
        self.assertEqual(sidebar_window_width(), BASE_WIDTH)
        self.assertEqual(sidebar_window_width(1.5, None), 84 + 24)
        for bad in (None, 0, -1, 'x', float('nan'), float('inf')):
            self.assertEqual(sidebar_window_width(bad, 16), 72, bad)
        self.assertEqual(sidebar_window_width(1.0, -5), 72)

    def test_width_is_narrower_than_old_fixed_190_and_pywebview_minimum(self):
        # 사용자 보고(2026-11-07): 창 폭 약 260px 중 아이콘 줄은 약 64px → 남는 폭이 흰 화면.
        for scale in (1.0, 1.25, 1.5):
            self.assertLess(sidebar_window_width(scale, round(16 * scale)), 260 * scale)
            self.assertLess(sidebar_window_width(scale, round(16 * scale)), 190 * scale)


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
        self.assertEqual(result['width'], BASE_WIDTH)
        self.assertEqual(api.positions[-1], (42, 1100 - BASE_WIDTH, 40, BASE_WIDTH, 800, True))
        self.assertTrue(window.only)
        controller.toggle(False)
        self.assertEqual(api.positions[-1], (42, 600, 100, 800, 600, True))
        self.assertFalse(window.only)

    def test_saved_side_has_priority_and_switch_persists_and_moves(self):
        api, window = FakeApi(area=(-1200, 30, -200, 830)), FakeWindow(rect=(900, 100, 800, 600))
        controller = SidebarModeController(api, window, True, saved_side='left')
        enabled = controller.toggle(True)
        self.assertEqual(enabled['side'], 'left')
        self.assertEqual(api.positions[-1], (42, -1200, 30, BASE_WIDTH, 800, True))
        switched = controller.switch_side()
        self.assertEqual(switched['side'], 'right')
        self.assertEqual(api.positions[-1], (42, -200 - BASE_WIDTH, 30, BASE_WIDTH, 800, True))
        self.assertEqual(window.saved_sides, ['left', 'right'])
        controller.toggle(False)
        next_controller = SidebarModeController(api, window, True, saved_side=controller.saved_side)
        self.assertEqual(next_controller.toggle(True)['side'], 'right')

    def test_scaled_monitor_uses_dpi_frame_and_physical_restore_rect(self):
        api, window = ScaledApi(), FakeWindow(rect=(600, 100, 800, 600))
        controller = SidebarModeController(api, window, True)
        result = controller.toggle(True)
        self.assertEqual(result['width'], 108)  # 56×1.5 + 24
        self.assertEqual(api.positions[-1], (42, 2880 - 108, 0, 108, 1680, True))
        controller.toggle(False)
        # 논리 픽셀 geometry(600,100,800,600)가 아니라 실제 창(물리 픽셀)으로 돌아간다.
        self.assertEqual(api.positions[-1], (42, 900, 150, 1200, 900, False))

    def test_min_size_released_only_while_active_and_restored_after_resize(self):
        log = []
        api = ScaledApi()
        original_set = api.set_window_pos
        api.set_window_pos = lambda *a: (log.append(('pos',) + a[1:5]), original_set(*a))
        window = MinSizeWindow(log=log)
        controller = SidebarModeController(api, window, True, saved_side='left')
        controller.toggle(True)
        self.assertEqual(window.minimum, (108, 270))
        self.assertEqual(log[:2], [('min', 108, 270), ('pos', 0, 0, 108, 1680)])
        controller.switch_side()
        self.assertEqual(window.minimum, (108, 270))
        log.clear()
        controller.toggle(False)
        self.assertEqual(window.minimum, (390, 270))
        # 원래 크기로 먼저 돌리고 나서 최소 크기를 되돌린다.
        self.assertEqual(log, [('pos', 900, 150, 1200, 900), ('min', 390, 270)])
        self.assertIsNone(controller.saved_min_size)
        # 다시 켜고 끄도 원래 최소 크기가 유지된다(사이드메뉴 폭을 원래 값으로 착각하지 않음).
        controller.toggle(True)
        controller.toggle(False)
        self.assertEqual(window.minimum, (390, 270))

    def test_failed_move_restores_min_size_and_stays_inactive(self):
        api, window = ScaledApi(), MinSizeWindow()
        api.fail = True
        controller = SidebarModeController(api, window, True)
        with self.assertRaises(OSError):
            controller.toggle(True)
        self.assertEqual(window.minimum, (390, 270))
        self.assertFalse(controller.active)
        self.assertIsNone(window.only)

    def test_metric_errors_fall_back_to_defaults(self):
        class BrokenApi(FakeApi):
            def dpi_scale(self, hwnd): raise OSError('dpi')
            def frame_width(self, hwnd): raise OSError('frame')
            def window_rect(self, hwnd): raise OSError('rect')
        api, window = BrokenApi(), FakeWindow()
        controller = SidebarModeController(api, window, True)
        self.assertEqual(controller.toggle(True)['width'], BASE_WIDTH)
        controller.toggle(False)
        self.assertEqual(api.positions[-1], (42, 600, 100, 800, 600, False))

    def test_missing_saved_side_uses_nearest_edge(self):
        controller = SidebarModeController(FakeApi(), FakeWindow(rect=(100, 100, 800, 600)), True, saved_side=None)
        self.assertEqual(controller.toggle(True)['side'], 'left')

    def test_switch_requires_active_developer_mode(self):
        controller = SidebarModeController(FakeApi(), FakeWindow(), True)
        self.assertFalse(controller.switch_side()['ok'])
        controller.developer_mode = False
        with self.assertRaises(PermissionError):
            controller.switch_side()

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

    def test_win32_window_metrics(self):
        from desktop_web_ui import _Win32WindowApi
        class User32:
            def GetWindowRect(self, hwnd, rect):
                rect._obj.left, rect._obj.top, rect._obj.right, rect._obj.bottom = -7, 0, 1033, 800
                return 1
            def GetClientRect(self, hwnd, rect):
                rect._obj.left, rect._obj.top, rect._obj.right, rect._obj.bottom = 0, 0, 1024, 769
                return 1
            def GetDpiForWindow(self, hwnd): return 120
        api = _Win32WindowApi(User32())
        self.assertEqual(api.window_rect(5), (-7, 0, 1040, 800))
        self.assertEqual(api.frame_width(5), 16)
        self.assertEqual(api.dpi_scale(5), 1.25)

        class NoDpi:
            def GetWindowRect(self, hwnd, rect): return 0
        api = _Win32WindowApi(NoDpi())
        self.assertEqual(api.dpi_scale(5), 1.0)
        with self.assertRaises(OSError):
            api.window_rect(5)

    def test_pywebview_window_min_size_and_no_fixed_resize(self):
        from desktop_web_ui import _PyWebViewWindow
        native = Mock()
        native.MinimumSize.Width, native.MinimumSize.Height = 325, 225
        window = Mock(native=native)
        wrapper = _PyWebViewWindow(window, None, lambda: {'x': 0, 'y': 0, 'width': 1040, 'height': 800, 'topmost': False})
        self.assertEqual(wrapper.min_size(), (325, 225))
        wrapper.set_sidebar_only(True)
        wrapper.set_sidebar_only(False)
        window.resize.assert_not_called()


if __name__ == '__main__':
    unittest.main()
