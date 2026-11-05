"""Window geometry helpers for the developer-only sidebar mode."""
from __future__ import annotations


def choose_side(window_center_x, work_left, work_right, remembered='right'):
    left_distance = abs(window_center_x - work_left)
    right_distance = abs(work_right - window_center_x)
    if left_distance == right_distance:
        return remembered if remembered in {'left', 'right'} else 'right'
    return 'left' if left_distance < right_distance else 'right'


class SidebarModeController:
    def __init__(self, api, window, developer_mode, saved_side='right'):
        self.api = api
        self.window = window
        self.developer_mode = developer_mode
        self.saved_side = saved_side if isinstance(saved_side, str) and saved_side in ('left', 'right') else 'right'
        self.side_explicitly_selected = False
        self.saved = None
        self.active = False

    def set_side(self, side: str) -> dict[str, object]:
        if not self.developer_mode:
            raise PermissionError('사이드메뉴 모드는 개발자 모드에서만 사용할 수 있습니다.')
        if side not in ('left', 'right'):
            raise ValueError("side must be exactly 'left' or 'right'")
        self.saved_side = side
        self.side_explicitly_selected = True
        if hasattr(self.window, 'save_side'):
            self.window.save_side(side)
        if self.active:
            left, top, right, bottom = self.api.work_area(self.window.handle())
            width = 190
            x = left if side == 'left' else right - width
            self.api.set_window_pos(self.window.handle(), x, top, width, bottom - top, True)
        return {'ok': True, 'active': self.active, 'side': side}

    def toggle(self, enabled):
        if not self.developer_mode:
            raise PermissionError('사이드메뉴 모드는 개발자 모드에서만 사용할 수 있습니다.')
        if bool(enabled) == self.active:
            return {'ok': True, 'active': self.active}
        if enabled:
            rect = self.window.geometry()
            self.saved = {'x': rect[0], 'y': rect[1], 'width': rect[2], 'height': rect[3],
                          'topmost': bool(self.window.topmost())}
            left, top, right, bottom = self.api.work_area(self.window.handle())
            side = (self.saved_side if self.side_explicitly_selected else
                    choose_side(rect[0] + rect[2] // 2, left, right, self.saved_side))
            self.saved_side = side
            if hasattr(self.window, 'save_side'):
                self.window.save_side(side)
            width = 190
            x = left if side == 'left' else right - width
            self.api.set_window_pos(self.window.handle(), x, top, width, bottom - top, True)
            self.window.set_sidebar_only(True)
            self.active = True
            return {'ok': True, 'active': True, 'side': side}
        self.window.set_sidebar_only(False)
        s = self.saved
        self.api.set_window_pos(self.window.handle(), s['x'], s['y'], s['width'], s['height'], s['topmost'])
        self.active = False
        return {'ok': True, 'active': False}

