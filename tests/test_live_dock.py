"""3.0-α2 도우미 패널 배치·추적(가짜 값으로 시험)."""
import threading
import unittest

from docfit_live.dock import DockTracker, panel_rect

WORK = (0, 0, 1920, 1040)


class PanelRectTest(unittest.TestCase):
    def test_right_outside_first(self):
        self.assertEqual(panel_rect((100, 50, 1200, 900), WORK), (1200, 50, 360, 850))

    def test_left_outside_when_right_has_no_room(self):
        self.assertEqual(panel_rect((500, 0, 1800, 1000), WORK), (140, 0, 360, 1000))

    def test_inside_when_both_outsides_fail_and_never_off_screen(self):
        self.assertEqual(panel_rect((0, 0, 1920, 1040), WORK), (1560, 0, 360, 1040))
        # 한/글 창이 화면 오른쪽 밖으로 걸쳐 있어도 패널은 작업 영역 안에 둔다.
        x, _, w, _ = panel_rect((200, 0, 2300, 1040), WORK)
        self.assertTrue(0 <= x and x + w <= 1920, x)

    def test_left_preference_is_symmetric(self):
        self.assertEqual(panel_rect((400, 0, 1200, 800), WORK, side="left"), (40, 0, 360, 800))
        self.assertEqual(panel_rect((100, 0, 1200, 800), WORK, side="left"), (1200, 0, 360, 800))

    def test_height_is_clipped_to_work_area_and_minimized_is_none(self):
        self.assertEqual(panel_rect((100, -30, 1000, 1200), WORK), (1000, 0, 360, 1040))
        self.assertIsNone(panel_rect(None, WORK))

    def test_second_monitor_with_negative_coordinates(self):
        left_monitor = (-1920, 0, 0, 1040)
        self.assertEqual(panel_rect((-1800, 100, -600, 900), left_monitor), (-600, 100, 360, 800))

    def test_bad_arguments(self):
        for kwargs in ({"width": 0}, {"side": "top"}):
            with self.assertRaises(ValueError):
                panel_rect((0, 0, 100, 100), WORK, **kwargs)
        with self.assertRaises(ValueError):
            panel_rect((0, 0, 100, 100), (0, 0, 300, 100))


class DockTrackerTest(unittest.TestCase):
    def test_moves_only_when_position_changes(self):
        frames = [((100, 0, 1200, 900), WORK)] * 3 + [((300, 0, 1400, 900), WORK)] * 3 + [None] * 3
        moves, done = [], threading.Event()

        def get_rect():
            if not frames:
                done.set()
                return None
            return frames.pop(0)
        tracker = DockTracker(get_rect, moves.append, interval=0.01)
        tracker.start()
        self.assertTrue(done.wait(5))
        tracker.stop()
        self.assertEqual(moves, [(1200, 0, 360, 900), (1400, 0, 360, 900), None])

    def test_errors_do_not_stop_tracking(self):
        calls, done = [], threading.Event()

        def get_rect():
            calls.append(1)
            if len(calls) == 1:
                raise OSError("x")
            done.set()
            return ((0, 0, 800, 600), WORK)
        moves = []
        tracker = DockTracker(get_rect, moves.append, interval=0.01)
        tracker.start()
        self.assertTrue(done.wait(5))
        tracker.stop()
        self.assertEqual(moves[0], (800, 0, 360, 600))


if __name__ == "__main__":
    unittest.main()
