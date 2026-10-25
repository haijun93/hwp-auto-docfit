from copy import deepcopy
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "format_fidelity_pc.py"))


class TableRenderToleranceTest(unittest.TestCase):
    def table(self, width="1000", height="2000", top="300", bottom="300", left="100"):
        attrs = lambda **kw: tuple(sorted(kw.items()))
        cell = (attrs(colAddr="0", rowAddr="0"), attrs(colSpan="1", rowSpan="1"),
                attrs(width="1000", height="2000"), attrs(top=top, bottom=bottom, left=left), ())
        return ("TBL", "1", "1", attrs(width=width, height=height), (), (), [cell])

    def compare(self, original, result):
        with patch.dict(MODULE["compare"].__globals__, load=lambda path: [original if path == "orig" else result]):
            return MODULE["compare"]("orig", "res")[0]

    def test_inclusive_limits_in_both_directions(self):
        original = self.table()
        for sign in (-1, 1):
            result = self.table(width=str(1000 + sign * 200), height=str(2000 + sign * 200),
                                top=str(300 + sign * 150), bottom=str(300 + sign * 150))
            unchanged = deepcopy(result)
            self.assertEqual(self.compare(original, result), 0)
            self.assertEqual(result, unchanged)

    def test_excess_and_other_fields_still_fail(self):
        for changes in ({"width": "1201"}, {"height": "1799"}, {"top": "451"},
                        {"bottom": "149"}, {"left": "101"}, {"width": "invalid"}):
            with self.subTest(changes=changes):
                self.assertEqual(self.compare(self.table(), self.table(**changes)), 1)

    def test_missing_attribute_and_cell_count_still_fail(self):
        original = self.table()
        result = list(self.table())
        result[3] = (("width", "1000"),)
        self.assertEqual(self.compare(original, tuple(result)), 1)
        result = list(self.table())
        result[6] = []
        self.assertEqual(self.compare(original, tuple(result)), 1)
