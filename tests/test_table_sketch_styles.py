"""표그림판 선 굵기(한/글 mm 목록)·선 색·칸별 배경색·묶음이 HWPX(한/글 복사)에 반영되는지 시험한다."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from docfit_core import table_sketch as ts


def line(x1, y1, x2, y2, **kw):
    return dict(x1=x1, y1=y1, x2=x2, y2=y2, **kw)


def box(x1, y1, x2, y2, **kw):
    return [line(x1, y1, x2, y1, **kw), line(x1, y2, x2, y2, **kw),
            line(x1, y1, x1, y2, **kw), line(x2, y1, x2, y2, **kw)]


def drawing(lines, **extra):
    return dict(grid=dict(cols=36, rows=50, cell_mm=5.0), lines=lines, texts=[], **extra)


def cell_fills(sketch):
    """(행, 열) → 칸의 borderFill 노드."""
    with tempfile.TemporaryDirectory() as folder:
        path = ts.to_hwpx(sketch, Path(folder) / "out.hwpx")
        with zipfile.ZipFile(path) as archive:
            header = ET.fromstring(archive.read("Contents/header.xml"))
            section = ET.fromstring(archive.read("Contents/section0.xml"))
    fills = {n.get("id"): n for n in header.iter(ts.HH + "borderFill")}
    cells = {}
    for tc in section.iter(ts.HP + "tc"):
        addr = tc.find(ts.HP + "cellAddr")
        cells[(int(addr.get("rowAddr")), int(addr.get("colAddr")))] = fills[tc.get("borderFillIDRef")]
    return cells, section


class LineWidthAndColorTests(unittest.TestCase):
    def test_mm_width_and_color_reach_hwpx_borders(self):
        sketch = drawing(box(0, 0, 4, 2, width="1.5 mm", color="#DC2626") +
                         [line(2, 0, 2, 2, width="0.25 mm", color="#1D4ED8")])
        cells, _ = cell_fills(sketch)
        left, right = cells[(0, 0)], cells[(0, 1)]
        top = left.find(ts.HH + "topBorder")
        self.assertEqual((top.get("type"), top.get("width"), top.get("color")), ("SOLID", "1.5 mm", "#DC2626"))
        inner = left.find(ts.HH + "rightBorder")
        self.assertEqual((inner.get("width"), inner.get("color")), ("0.25 mm", "#1D4ED8"))
        self.assertEqual(right.find(ts.HH + "leftBorder").get("width"), "0.25 mm")

    def test_every_hangul_width_is_accepted(self):
        for width in ts.BORDER_WIDTHS:
            result = ts.preview(drawing(box(0, 0, 2, 2, width=width)))
            self.assertEqual(result["warnings"], [], width)
            self.assertEqual(set(result["cells"][0]["borders"].values()), {width})

    def test_old_names_still_map_to_same_hwpx_widths(self):
        cells, _ = cell_fills(drawing(box(0, 0, 2, 2, width="thick")))
        self.assertEqual(cells[(0, 0)].find(ts.HH + "topBorder").get("width"), "0.4 mm")

    def test_unknown_width_is_excluded_with_warning(self):
        result = ts.preview(drawing(box(0, 0, 2, 2) + [line(1, 0, 1, 2, width="9 mm")]))
        self.assertTrue(any("선 5" in w for w in result["warnings"]))
        self.assertEqual(result["cols"], 1)

    def test_overlapping_lines_keep_thicker_mm_width(self):
        result = ts.preview(drawing(box(0, 0, 2, 2, width="0.2 mm") + [line(0, 0, 2, 0, width="0.7 mm")]))
        self.assertEqual(result["cells"][0]["borders"]["top"], "0.7 mm")
        self.assertEqual(result["cells"][0]["borders"]["bottom"], "0.2 mm")

    def test_arrow_mm_width_becomes_line_shape_width(self):
        sketch = drawing(box(0, 0, 6, 2), arrows=[dict(x1=1, y1=1, x2=5, y2=1, width="1.0 mm", color="#16A34A")])
        _, section = cell_fills(sketch)
        shape = next(section.iter(ts.HP + "lineShape"))
        self.assertEqual((shape.get("width"), shape.get("color")), (str(round(1.0 * ts.UNIT_MM)), "#16A34A"))

    def test_group_ids_are_ignored_by_table_conversion(self):
        sketch = drawing([dict(l, group="g1") for l in box(0, 0, 2, 2)])
        self.assertEqual(ts.preview(sketch)["warnings"], [])


class RegionFillTests(unittest.TestCase):
    def test_rectangle_split_by_line_gets_separate_cell_colors(self):
        # 사각형을 가로 직선 하나로 이등분하면 2칸: 칸마다 다른 배경(격자 칸 단위 채움).
        fills = [dict(x1=x, y1=y, x2=x + 1, y2=y + 1, color="#FEF9C3") for x in range(4) for y in range(2)]
        fills += [dict(x1=x, y1=y, x2=x + 1, y2=y + 1, color="#DBEAFE") for x in range(4) for y in range(2, 4)]
        sketch = drawing(box(0, 0, 4, 4) + [line(0, 2, 4, 2)], fills=fills)
        cells, _ = cell_fills(sketch)
        self.assertEqual(sorted(cells), [(0, 0), (1, 0)])
        colors = {k: v.find(ts.HC + "fillBrush/" + ts.HC + "winBrush").get("faceColor") for k, v in cells.items()}
        self.assertEqual(colors, {(0, 0): "#FEF9C3", (1, 0): "#DBEAFE"})
        # 테두리·분할선은 그대로 남는다.
        self.assertEqual(cells[(0, 0)].find(ts.HH + "bottomBorder").get("type"), "SOLID")

    def test_uncolored_cell_has_no_fill(self):
        fills = [dict(x1=0, y1=0, x2=2, y2=2, color="#FEE2E2")]
        cells, _ = cell_fills(drawing(box(0, 0, 4, 2) + [line(2, 0, 2, 2)], fills=fills))
        self.assertIsNotNone(cells[(0, 0)].find(ts.HC + "fillBrush"))
        self.assertIsNone(cells[(0, 1)].find(ts.HC + "fillBrush"))


class CanvasBuilderWidthTests(unittest.TestCase):
    def test_canvas_border_builder_accepts_mm_widths(self):
        from docfit_core.hwpx.canvas_hwpx_builder import build_table_sketch_border_fills_xml
        sketch = drawing(box(0, 0, 2, 2, width="2.0 mm"))
        try:
            nodes = build_table_sketch_border_fills_xml(sketch)
        except (KeyError, TypeError) as error:  # pragma: no cover - 실패 내용 표시
            self.fail(error)
        self.assertEqual(nodes[0].find(ts.HH + "topBorder").get("width"), "2.0 mm")


if __name__ == "__main__":
    unittest.main()
