"""엑셀 클립보드 HTML에서 셀 배경 음영만 제거하는 함수 시험."""
import re
import unittest
from pathlib import Path
from unittest import mock

from docfit_core.excel_html_shading import strip_cell_shading, strip_cell_shading_report
from docfit_core.excel_table import parse_clipboard
from docfit_app.excel_table_service import ExcelTableService

FIX = Path(__file__).parent / "fixtures"
NAMES = ["xlshade_class_merged", "xlshade_inline_bgcolor", "xlshade_pattern_span", "xlshade_row_col"]
SHADING = re.compile(rb"bgcolor|background|mso-pattern|mso-background-source", re.I)


def load(name):
    return (FIX / f"{name}.cf_html").read_bytes()


def cells(model):
    return [(c["row"], c["col"], c["rowspan"], c["colspan"], c["text"], c["color"], c["bold"])
            for r in model["rows"] for c in r]


def header(data):
    return {k.decode(): int(v) for k, v in re.findall(rb"(StartHTML|EndHTML|StartFragment|EndFragment):(\d+)", data)}


class StripShadingTests(unittest.TestCase):
    def test_shading_removed_everywhere(self):
        for name in NAMES:
            with self.subTest(name):
                out, report = strip_cell_shading_report(load(name))
                self.assertTrue(report["changed"], name)
                self.assertGreater(report["removed"], 0)
                self.assertIsNone(SHADING.search(out), SHADING.search(out) and SHADING.search(out).group(0))

    def test_structure_text_and_colors_preserved(self):
        for name in NAMES:
            with self.subTest(name):
                src = load(name)
                before = parse_clipboard(src, clean=False)
                after = parse_clipboard(strip_cell_shading(src), clean=False)
                self.assertEqual(cells(before), cells(after))
                self.assertTrue(all(c["fill"] == "" for r in after["rows"] for c in r))
        self.assertTrue(any(c["fill"] for r in parse_clipboard(load(NAMES[0]))["rows"] for c in r))

    def test_merge_attributes_kept(self):
        out = strip_cell_shading(load("xlshade_class_merged"))
        self.assertEqual(len(re.findall(rb"colspan=3", out)), 1)
        self.assertEqual(len(re.findall(rb"rowspan=2", out)), 2)
        self.assertIn(b"white", out)          # 글자색(흰색)은 유지
        self.assertIn(b"#C00000", out)
        self.assertIn(b"border:.5pt solid windowtext", out)
        self.assertEqual(len(re.findall(rb"<tr", out)), len(re.findall(rb"<tr", load("xlshade_class_merged"))))

    def test_inline_text_colors_and_borders_kept(self):
        out = strip_cell_shading(load("xlshade_inline_bgcolor")).decode()
        self.assertIn("color:#0000FF;border:.5pt solid windowtext", out)
        self.assertIn("color:#FF0000", out)
        self.assertIn("border-bottom:1.0pt double black", out)
        self.assertIn("border-collapse:collapse", out)
        self.assertNotIn("rgb(255,0,0)", out)

    def test_span_inner_style_untouched(self):
        out = strip_cell_shading(load("xlshade_pattern_span")).decode()
        self.assertIn("<span style='color:#7030A0;font-weight:700'>", out)
        self.assertIn("font-style:italic", out)

    def test_number_format_with_escaped_semicolon_survives(self):
        src = load("xlshade_class_merged").decode()
        out = strip_cell_shading(load("xlshade_class_merged")).decode()
        fmt = re.search(r"mso-number-format:[^\r\n]*", src).group(0)
        self.assertIn(fmt, out)

    def test_cf_html_offsets_recomputed(self):
        for name in NAMES:
            with self.subTest(name):
                out = strip_cell_shading(load(name))
                h = header(out)
                self.assertEqual(h["EndHTML"], len(out))
                self.assertTrue(out[h["StartHTML"]:].lstrip().startswith(b"<html"))
                self.assertTrue(out[h["StartFragment"]:].startswith(b"\r\n<"))
                self.assertTrue(out[:h["EndFragment"]].endswith(b"\r\n") or out[h["EndFragment"]:].startswith(b"<!--EndFragment-->"))
                self.assertEqual(out[h["EndFragment"]:h["EndFragment"] + 18], b"<!--EndFragment-->")
                self.assertEqual(out[h["StartFragment"] - 20:h["StartFragment"]], b"<!--StartFragment-->")

    def test_idempotent(self):
        once = strip_cell_shading(load("xlshade_row_col"))
        out, report = strip_cell_shading_report(once)
        self.assertEqual(out, once)
        self.assertFalse(report["changed"])

    def test_no_shading_returns_original(self):
        src = load("xlshade_none")
        out, report = strip_cell_shading_report(src)
        self.assertIs(out, src)
        self.assertFalse(report["changed"])

    def test_str_input_returns_str(self):
        text = load("xlshade_class_merged").decode("utf-8")
        out = strip_cell_shading(text)
        self.assertIsInstance(out, str)
        self.assertIsNone(re.search(r"mso-pattern|background", out))

    def test_headerless_fragment(self):
        out = strip_cell_shading("<table><tr><td bgcolor=red style='color:blue;background:red'>x</td></tr></table>")
        self.assertIsNone(re.search(r"bgcolor|background", out))
        self.assertRegex(out, r"<td\s+style='color:blue'>x</td>")

    def test_fallback_on_bad_input(self):
        for bad in [None, b"", "", "plain text\tTSV", "<p>no table</p>", b"\xff\xfe\x00bad", 123]:
            with self.subTest(bad=bad):
                out, report = strip_cell_shading_report(bad)
                self.assertEqual(out, bad)
                self.assertFalse(report["changed"])

    def test_truncated_html_never_raises(self):
        for bad in ["<td bgcolor=red", b"<td style='background:red'", "<table><tr><td bgcolor=red>x"]:
            out, report = strip_cell_shading_report(bad)
            self.assertIn(report["changed"], (True, False))

    def test_fallback_when_verification_fails(self):
        src = load("xlshade_class_merged")
        with mock.patch("docfit_core.excel_html_shading._strip_tags", lambda h: (h.replace("colspan=3", ""), 1)):
            out, report = strip_cell_shading_report(src)
        self.assertIs(out, src)
        self.assertEqual(report["reason"], "구조 검증 실패")

    def test_fallback_on_exception(self):
        src = load("xlshade_class_merged")
        with mock.patch("docfit_core.excel_html_shading._strip_style_blocks", side_effect=RuntimeError):
            out, report = strip_cell_shading_report(src)
        self.assertIs(out, src)
        self.assertIn("RuntimeError", report["reason"])

    def test_existing_fixture(self):
        src = (FIX / "excel_clipboard.cf_html").read_bytes()
        out = strip_cell_shading(src)
        self.assertEqual(cells(parse_clipboard(src, clean=False)), cells(parse_clipboard(out, clean=False)))
        self.assertIsNone(re.search(rb"background:|mso-pattern", out))


class StripShadingServiceTests(unittest.TestCase):
    def test_command_rewrites_clipboard_html(self):
        written = []
        service = ExcelTableService(clipboard=lambda: (load("xlshade_class_merged"), "a\tb"),
                                    html_writer=lambda html, tsv: written.append((html, tsv)))
        result = service.command("strip_shading")
        self.assertTrue(result["ok"])
        self.assertGreater(result["removed"], 0)
        self.assertIsNone(SHADING.search(written[0][0]))
        self.assertEqual(written[0][1], "a\tb")

    def test_command_leaves_clipboard_when_nothing_to_do(self):
        written = []
        service = ExcelTableService(clipboard=lambda: (load("xlshade_none"), None),
                                    html_writer=lambda *a: written.append(a))
        result = service.command("strip_shading")
        self.assertTrue(result["ok"])
        self.assertEqual(result["removed"], 0)
        self.assertEqual(written, [])

    def test_command_without_clipboard_html(self):
        service = ExcelTableService(clipboard=lambda: (None, "x"), html_writer=lambda *a: self.fail("쓰면 안 됨"))
        self.assertFalse(service.command("strip_shading")["ok"])


if __name__ == "__main__":
    unittest.main()
