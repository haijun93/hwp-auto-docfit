"""실제 엑셀이 만든 클립보드(HTML Format)로 표 모델과 HWPX를 검사한다."""
import tempfile
import unittest
from unittest import mock
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from docfit_core.excel_table import parse_clipboard
from docfit_core.excel_table_hwpx import BODY_WIDTH_MM, _column_widths, to_hwpx
from docfit_app.excel_table_service import ExcelTableService

FIXTURE = Path(__file__).parent / "fixtures" / "excel_clipboard.cf_html"
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def cell(model, row, col):
    return next(c for r in model["rows"] for c in r if (c["row"], c["col"]) == (row, col))


class ExcelClipboardTests(unittest.TestCase):
    def setUp(self):
        self.model = parse_clipboard(FIXTURE.read_bytes())

    def test_real_excel_fragment_without_table_tag(self):
        self.assertEqual((self.model["row_count"], self.model["col_count"]), (5, 5))

    def test_text_is_cleaned_and_display_format_kept(self):
        self.assertEqual(cell(self.model, 1, 1)["text"], "마포 축제 지원")
        self.assertEqual(cell(self.model, 1, 2)["text"], "1,234,567")
        self.assertEqual(cell(self.model, 1, 3)["text"], "87.5%")
        self.assertEqual(cell(self.model, 2, 4)["text"], "줄1\n줄2")

    def test_classes_outside_fragment_give_format(self):
        self.assertTrue(cell(self.model, 0, 0)["bold"])
        self.assertEqual(cell(self.model, 0, 0)["fill"], "#C0D5E6")
        self.assertEqual(cell(self.model, 1, 1)["fill"], "#FFFF00")
        self.assertEqual(cell(self.model, 1, 2)["align"], "right")

    def test_character_color_from_excel_fixture(self):
        self.assertEqual(cell(self.model, 0, 0)["color"], "#000000")

    def test_merges_are_placed_on_the_grid(self):
        self.assertEqual(cell(self.model, 1, 0)["rowspan"], 2)
        self.assertEqual(cell(self.model, 2, 1)["text"], "도서관 운영")
        self.assertEqual(cell(self.model, 4, 0)["colspan"], 2)
        self.assertEqual(cell(self.model, 4, 2)["text"], "1,337,567")

    def test_hwpx_fits_body_width_with_merges(self):
        with tempfile.TemporaryDirectory() as folder:
            path = to_hwpx(self.model, Path(folder) / "t.hwpx")
            with zipfile.ZipFile(path) as package:
                root = ET.fromstring(package.read("Contents/section0.xml"))
        table = root.find(f".//{HP}tbl")
        self.assertAlmostEqual(int(table.find(f"{HP}sz").get("width")) / 283.465, 170, delta=1)
        self.assertEqual(len(list(table.iter(f"{HP}tc"))), 23)


class FallbackAndCleanupTests(unittest.TestCase):
    def test_service_keeps_background_by_default_and_can_remove_it(self):
        captured = []
        original = __import__('docfit_app.excel_table_service', fromlist=['to_hwpx']).to_hwpx

        def capture(model, path):
            captured.append((model['row_count'], model['col_count'],
                             [c['text'] for row in model['rows'] for c in row],
                             [c['fill'] for row in model['rows'] for c in row]))
            return original(model, path)

        def copier(path):
            return {'ok': True}

        service = ExcelTableService(clipboard=lambda: (FIXTURE.read_bytes(), None), copier=copier)
        with mock.patch('docfit_app.excel_table_service.to_hwpx', side_effect=capture):
            self.assertTrue(service.command('convert')['ok'])
        self.assertIn('#C0D5E6', captured[-1][3])
        with mock.patch('docfit_app.excel_table_service.to_hwpx', side_effect=capture):
            result = service.command('paste_clean')
        self.assertTrue(result['ok'])
        self.assertEqual(captured[-1][:3], captured[0][:3])
        self.assertTrue(all(not fill for fill in captured[-1][3]))

    def test_tsv_keeps_quoted_line_break_in_one_cell(self):
        model = parse_clipboard(None, 'a\t"줄1\n줄2"\nb\tc')
        self.assertEqual((model["row_count"], model["col_count"]), (2, 2))
        self.assertEqual(cell(model, 0, 1)["text"], "줄1\n줄2")

    def test_control_text_quote_and_trailing_empty_are_removed(self):
        html = "<tr><td>'앞_x000D_\u00a0 뒤\u200b</td><td></td></tr><tr><td></td><td></td></tr>"
        model = parse_clipboard(html)
        self.assertEqual((model["row_count"], model["col_count"]), (1, 1))
        self.assertEqual(cell(model, 0, 0)["text"], "앞 뒤")
        self.assertGreaterEqual(model["cleaned"]["symbols"], 2)

    def test_span_highlight_is_dropped_but_counted(self):
        model = parse_clipboard('<tr><td><span style="background:yellow">글</span></td></tr>')
        self.assertEqual(cell(model, 0, 0)["fill"], "")
        self.assertEqual(model["cleaned"]["background"], 1)

    def test_empty_input_raises(self):
        with self.assertRaises(ValueError):
            parse_clipboard(None, None)

    def test_merges_reaching_last_row_and_column_keep_full_extent(self):
        model = parse_clipboard('<tr><td rowspan="2" colspan="2">a</td></tr><tr></tr>')
        self.assertEqual((model["row_count"], model["col_count"]), (2, 2))
        self.assertEqual((cell(model, 0, 0)["rowspan"], cell(model, 0, 0)["colspan"]), (2, 2))

    def test_empty_first_row_and_column_preserve_offsets(self):
        model = parse_clipboard('<tr><td></td><td></td></tr><tr><td></td><td>x</td></tr>')
        self.assertEqual((model["row_count"], model["col_count"]), (2, 2))
        self.assertEqual((cell(model, 1, 1)["row"], cell(model, 1, 1)["col"]), (1, 1))

    def test_text_line_breaks_and_special_spaces_are_cleaned(self):
        model = parse_clipboard('<tr><td>첫 줄<br>둘\u202f 줄</td></tr>')
        self.assertEqual(cell(model, 0, 0)["text"], "첫 줄\n둘 줄")

    def test_signed_parenthesized_and_currency_numbers_align_right(self):
        model = parse_clipboard('<tr><td>-12</td><td>(1,234.50)</td><td>₩ -500</td><td>$12.00</td></tr>')
        self.assertTrue(all(cell(model, 0, col)["numeric"] for col in range(4)))
        self.assertTrue(all(cell(model, 0, col)["align"] == "right" for col in range(4)))

    def test_column_widths_without_data_and_minimum_overflow(self):
        widths = _column_widths({"col_count": 4, "widths": []})
        self.assertAlmostEqual(sum(widths), BODY_WIDTH_MM)
        widths = _column_widths({"col_count": 30, "widths": [0] * 30})
        self.assertAlmostEqual(sum(widths), BODY_WIDTH_MM)

    def test_200_by_200_is_allowed_but_201_is_rejected(self):
        from docfit_core.excel_table_hwpx import _sketch
        self.assertEqual(_sketch({"rows": [], "row_count": 200, "col_count": 200})["grid"]["cols"], 200)
        with tempfile.TemporaryDirectory() as folder:
            for dimensions in ((201, 1), (1, 201)):
                with self.subTest(dimensions=dimensions), self.assertRaises(ValueError):
                    to_hwpx({"row_count": dimensions[1], "col_count": dimensions[0], "rows": [], "widths": []}, Path(folder) / "x.hwpx")


if __name__ == "__main__":
    unittest.main()
