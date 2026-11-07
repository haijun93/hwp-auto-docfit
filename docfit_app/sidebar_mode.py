"""Window geometry helpers for the developer-only sidebar mode."""
from __future__ import annotations

import math

# Flutter 접힌 사이드메뉴(아이콘 줄) 폭. flutter_ui/lib/features/workspace/tab_navigation_shell.dart의
# kSidebarCollapsedWidth와 같아야 한다(논리 픽셀).
SIDEBAR_RAIL_WIDTH = 56
# 창 테두리 폭을 Win32로 재지 못할 때 쓰는 값(Windows 10/11 좌우 크기 조절 테두리 합, 100% 배율 기준).
DEFAULT_FRAME_WIDTH = 16


def choose_side(window_center_x, work_left, work_right, remembered='right'):
    left_distance = abs(window_center_x - work_left)
    right_distance = abs(work_right - window_center_x)
    if left_distance == right_distance:
        return remembered if remembered in {'left', 'right'} else 'right'
    return 'left' if left_distance < right_distance else 'right'


def sidebar_window_width(scale=1.0, frame_width=None, rail_width=SIDEBAR_RAIL_WIDTH):
    """사이드메뉴 모드 창 폭(물리 픽셀): 아이콘 줄 폭 × 화면 배율 + 창 테두리.

    창 폭을 아이콘 줄에 딱 맞춰 오른쪽에 빈 화면이 남지 않게 한다(사용자 요청 2026-11-07).
    """
    try:
        scale = float(scale)
    except (TypeError, ValueError):
        scale = 1.0
    if not scale > 0 or math.isinf(scale):
        scale = 1.0
    if frame_width is None or frame_width < 0:
        frame_width = round(DEFAULT_FRAME_WIDTH * scale)
    return int(math.ceil(rail_width * scale)) + int(frame_width)


class SidebarModeController:
    def __init__(self, api, window, developer_mode, saved_side='right'):
        self.api = api
        self.window = window
        self.developer_mode = developer_mode
        self.saved_side = saved_side
        self.saved = None
        self.saved_min_size = None
        self.active = False

    def _sidebar_width(self, hwnd):
        scale, frame = 1.0, None
        try:
            if hasattr(self.api, 'dpi_scale'):
                scale = self.api.dpi_scale(hwnd)
        except Exception:
            scale = 1.0
        try:
            if hasattr(self.api, 'frame_width'):
                frame = self.api.frame_width(hwnd)
        except Exception:
            frame = None
        return sidebar_window_width(scale, frame)

    def _current_rect(self, hwnd):
        # SetWindowPos와 같은 물리 픽셀 좌표로 저장해야 화면 배율 125%·150%에서도 정확히 돌아온다.
        if hasattr(self.api, 'window_rect'):
            try:
                return tuple(self.api.window_rect(hwnd))
            except Exception:
                pass
        return tuple(self.window.geometry())

    def _release_min_size(self, width):
        """사이드메뉴 모드 동안만 창 최소 폭 제한(기본 260)을 아이콘 줄 폭으로 낮춘다."""
        if not (hasattr(self.window, 'min_size') and hasattr(self.window, 'set_min_size')):
            return
        if self.saved_min_size is None:
            self.saved_min_size = tuple(self.window.min_size())
        self.window.set_min_size(width, self.saved_min_size[1])

    def _restore_min_size(self):
        if self.saved_min_size is None or not hasattr(self.window, 'set_min_size'):
            return
        saved, self.saved_min_size = self.saved_min_size, None
        self.window.set_min_size(*saved)

    def _place(self, hwnd, side):
        left, top, right, bottom = self.api.work_area(hwnd)
        width = self._sidebar_width(hwnd)
        self._release_min_size(width)
        x = left if side == 'left' else right - width
        self.api.set_window_pos(hwnd, x, top, width, bottom - top, True)
        return width

    def toggle(self, enabled):
        if not self.developer_mode:
            raise PermissionError('사이드메뉴 모드는 개발자 모드에서만 사용할 수 있습니다.')
        if bool(enabled) == self.active:
            return {'ok': True, 'active': self.active}
        hwnd = self.window.handle()
        if enabled:
            rect = self._current_rect(hwnd)
            self.saved = {'x': rect[0], 'y': rect[1], 'width': rect[2], 'height': rect[3],
                          'topmost': bool(self.window.topmost())}
            left, top, right, bottom = self.api.work_area(hwnd)
            side = self.saved_side if self.saved_side in {'left', 'right'} else choose_side(
                rect[0] + rect[2] // 2, left, right, self.saved_side
            )
            self.saved_side = side
            if hasattr(self.window, 'save_side'):
                self.window.save_side(side)
            try:
                width = self._place(hwnd, side)
                self.window.set_sidebar_only(True)
            except Exception:
                self._restore_min_size()
                raise
            self.active = True
            return {'ok': True, 'active': True, 'side': side, 'width': width}
        self.window.set_sidebar_only(False)
        s = self.saved
        self.api.set_window_pos(hwnd, s['x'], s['y'], s['width'], s['height'], s['topmost'])
        # 원래 크기로 돌린 다음 최소 크기를 되돌려야 WinForms가 창을 다시 키우며 위치를 흔들지 않는다.
        self._restore_min_size()
        self.active = False
        return {'ok': True, 'active': False}

    def switch_side(self):
        """Move an active sidebar to the opposite edge of its current monitor."""
        if not self.developer_mode:
            raise PermissionError('사이드메뉴 모드는 개발자 모드에서만 사용할 수 있습니다.')
        if not self.active:
            return {'ok': False, 'message': '사이드메뉴 모드가 켜져 있지 않습니다.'}
        side = 'left' if self.saved_side == 'right' else 'right'
        width = self._place(self.window.handle(), side)
        self.saved_side = side
        if hasattr(self.window, 'save_side'):
            self.window.save_side(side)
        return {'ok': True, 'active': True, 'side': side, 'width': width}
