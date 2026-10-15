"""표/다이어그램 편집기의 흐름표·기본 표를 한/글 HWPX로 만든다(docfit_core.table_builder, 2026-10-15)."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from defusedxml.ElementTree import fromstring

from docfit_core.hwpx import validate_hwpx
from docfit_core.table_builder import TableSpecError, build_table_hwpx, normalize
from docfit_core.table_style import default_style, is_flow_table, is_grid_table, is_user_designed_table

BASE = Path(__file__).resolve().parents[1] / "resources" / "서식예시" / "기본 서식.hwpx"


def tag(element):
    return element.tag.rsplit("}", 1)[-1]


def flow(n=4, **styles):
    return {"kind": "flow", "steps": [{"title": f"단계 {i + 1}", "date": f"{i + 1}월"} for i in range(n)],
            "styles": styles}


class TableBuilderTest(unittest.TestCase):
    def build(self, spec, style=None):
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: [p.unlink() for p in folder.iterdir()] and None)
        out = build_table_hwpx(spec, BASE, folder / "out.hwpx", basic_style=style)
        validate_hwpx(out)
        with zipfile.ZipFile(out) as z:
            header = fromstring(z.read("Contents/header.xml"))
            section = fromstring(z.read("Contents/section0.xml"))
        table = next(x for x in section.iter() if tag(x) == "tbl")
        return header, section, table

    def test_flow_table_follows_the_learned_layout_for_any_step_count(self):
        for n in (2, 3, 4, 5, 6, 9):
            _, section, table = self.build(flow(n))
            self.assertEqual((table.get("rowCnt"), table.get("colCnt")), ("2", str(2 * n - 1)))
            cells = [x for x in table.iter() if tag(x) == "tc"]
            arrows = [c for c in cells if "".join(t.text or "" for t in c.iter() if tag(t) == "t") == "➜"]
            self.assertEqual(len(arrows), n - 1)
            self.assertTrue(all(next(x for x in c if tag(x) == "cellSpan").get("rowSpan") == "2" for c in arrows))
            # 칸 폭 합이 표 폭(쪽 여백 사이)과 같다.
            first_row = [c for c in cells if next(x for x in c if tag(x) == "cellAddr").get("rowAddr") == "0"]
            widths = sum(int(next(x for x in c if tag(x) == "cellSz").get("width")) for c in first_row)
            self.assertEqual(widths, int(next(x for x in table if tag(x) == "sz").get("width")))
            # 만든 흐름표는 앱이 '사용자가 꾸민 표'로 보호한다.
            self.assertTrue(is_flow_table(table) and is_user_designed_table(table))
            self.assertEqual(len([p for p in section if tag(p) == "p"]), 2)   # 구역 설정 문단 + 표 문단

    def test_chosen_font_size_bold_and_color_reach_the_char_shape(self):
        header, _, table = self.build(flow(3, step={"font": "맑은 고딕", "size": 14, "bold": True, "color": "#1D4ED8"}))
        first = next(x for x in table.iter() if tag(x) == "run")
        char = next(x for x in header.iter() if tag(x) == "charPr" and x.get("id") == first.get("charPrIDRef"))
        self.assertEqual((char.get("height"), char.get("textColor")), ("1400", "#1D4ED8"))
        self.assertIsNotNone(next((x for x in char if tag(x) == "bold"), None))
        font_id = next(x for x in char if tag(x) == "fontRef").get("hangul")
        hangul = next(x for x in header.iter() if tag(x) == "fontface" and x.get("lang") == "HANGUL")
        self.assertEqual(next(f for f in hangul if f.get("id") == font_id).get("face"), "맑은 고딕")

    def test_grid_table_takes_basic_style_and_user_header_override(self):
        spec = {"kind": "grid", "header_rows": 1, "rows": [["구 분", "계획"], ["상반기", "10"], ["하반기", "12"]],
                "styles": {"head": {"font": "HY견고딕", "size": 13, "bold": True, "color": "#FFFFFF", "fill": "#1F4E79"}}}
        header, _, table = self.build(spec, default_style())
        self.assertTrue(is_grid_table(table))
        self.assertFalse(is_user_designed_table(table))
        cells = [x for x in table.iter() if tag(x) == "tc"]
        head = cells[0]
        fill = next(x for x in header.iter() if tag(x) == "borderFill" and x.get("id") == head.get("borderFillIDRef"))
        self.assertEqual(next(x for x in fill.iter() if tag(x) == "winBrush").get("faceColor"), "#1F4E79")
        body_char = next(x for x in cells[2].iter() if tag(x) == "run").get("charPrIDRef")
        self.assertNotEqual(body_char, next(x for x in head.iter() if tag(x) == "run").get("charPrIDRef"))

    def border_of(self, header, cell):
        fill = next(x for x in header.iter() if tag(x) == "borderFill" and x.get("id") == cell.get("borderFillIDRef"))
        return {side: (next(x for x in fill if tag(x) == side + "Border").get("type"))
                for side in ("left", "right", "top", "bottom")}

    def test_flow_grows_downward_and_can_run_vertically(self):
        steps = [{"title": f"단계 {i}", "details": [f"{i}월", "담당"]} for i in range(3)]
        _, _, table = self.build({"kind": "flow", "rows": 2, "steps": steps})
        self.assertEqual((table.get("rowCnt"), table.get("colCnt")), ("3", "5"))      # 단계 + 세부 2줄
        arrows = [c for c in table.iter() if tag(c) == "tc" and "".join(t.text or "" for t in c.iter() if tag(t) == "t") == "➜"]
        self.assertTrue(all(next(x for x in c if tag(x) == "cellSpan").get("rowSpan") == "3" for c in arrows))
        header, _, table = self.build({"kind": "flow", "direction": "vertical", "rows": 2, "steps": steps, "arrow": "▼"})
        self.assertEqual((table.get("rowCnt"), table.get("colCnt")), ("5", "3"))      # 단계 3행 + 화살표 2행
        down = [c for c in table.iter() if tag(c) == "tc" and "▼" in "".join(t.text or "" for t in c.iter() if tag(t) == "t")]
        self.assertEqual(len(down), 2)
        with self.assertRaises(TableSpecError):
            normalize({"kind": "flow", "direction": "vertical", "steps": steps, "arrow": "➜"})   # 세로는 아래 화살표만

    def test_border_types_follow_hangul(self):
        spec = {"kind": "grid", "rows": [["가", "나"], ["다", "라"]], "header_rows": 1,
                "borders": {"outer": {"type": "DOUBLE_SLIM", "width": "0.5 mm", "color": "#000000"},
                            "inner": {"type": "NONE", "width": "0.1 mm", "color": "#000000"}}}
        header, _, table = self.build(spec, default_style())
        cells = [x for x in table.iter() if tag(x) == "tc"]
        first = self.border_of(header, cells[0])
        self.assertEqual((first["left"], first["top"], first["right"], first["bottom"]),
                         ("DOUBLE_SLIM", "DOUBLE_SLIM", "NONE", "NONE"))               # 바깥 이중선, 안쪽 투명선
        with self.assertRaises(TableSpecError):
            normalize({**spec, "borders": {"outer": {"type": "WAVY"}}})

    def test_org_chart_draws_links_with_cell_borders(self):
        spec = {"kind": "org", "root": "문화경제국",
                "units": [{"title": "관광정책과", "detail": "관광정책팀"}, {"title": "지역경제과"}, {"title": "문화예술과"}]}
        header, _, table = self.build(spec)
        self.assertEqual((table.get("rowCnt"), table.get("colCnt")), ("5", "12"))
        cells = [x for x in table.iter() if tag(x) == "tc"]
        texts = ["".join(t.text or "" for t in c.iter() if tag(t) == "t") for c in cells]
        self.assertIn("문화경제국", texts)
        root = cells[texts.index("문화경제국")]
        self.assertEqual(next(x for x in root if tag(x) == "cellAddr").get("colAddr"), "5")   # 가운데 부서 위
        self.assertTrue(is_user_designed_table(table))                                        # 조직표로 보호
        widths = {int(next(x for x in c if tag(x) == "cellSz").get("width")) for c in cells}
        self.assertTrue(all(w > 0 for w in widths))

    def test_bar_table_matches_learned_layout(self):
        header, _, table = self.build({"kind": "bar", "title": "2026 추진실적", "note": "( 8. 31. 현재 )"})
        self.assertEqual((table.get("rowCnt"), table.get("colCnt")), ("2", "5"))
        self.assertTrue(is_user_designed_table(table))
        middle = [c for c in table.iter() if tag(c) == "tc" and next(x for x in c if tag(x) == "cellAddr").get("colAddr") == "2"]
        self.assertEqual(self.border_of(header, middle[0])["bottom"], "DASH")

    def test_invalid_specs_are_rejected(self):
        for bad in ({"kind": "flow", "steps": [{"title": "하나"}]},
                    flow(13),
                    flow(3, step={"font": "없는 글꼴"}),
                    flow(3, step={"size": 80}),
                    flow(3, step={"color": "red"}),
                    {"kind": "grid", "rows": [["가"] * 13]},
                    {"kind": "grid", "rows": [["가\x00"]]},
                    {"kind": "chart"}):
            with self.assertRaises(TableSpecError):
                normalize(bad)


if __name__ == "__main__":
    unittest.main()
