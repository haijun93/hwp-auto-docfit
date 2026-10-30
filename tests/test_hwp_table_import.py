"""한/글에서 복사한 표(클립보드 HTML) → 표그림판 그림(2.0.5)."""
import tempfile
import unittest

from docfit_app.table_sketch_service import TableSketchService
from docfit_core import table_sketch
from docfit_core.hwp_table_import import sketch_from_html

# 한/글 2020이 표를 복사할 때 넣는 HTML의 모양(칸 폭·높이 pt, 변마다 테두리, 병합, 문단 정렬).
B = "border-top:solid #000000 {t}pt;border-left:solid #000000 0.28pt;border-bottom:solid #000000 0.28pt;border-right:solid #000000 0.28pt;"
HTML = ("Version:1.0\r\nStartHTML:0000000105\r\n<html><body><!--StartFragment--><p class=\"0\"><table style=\"border-collapse:collapse\">"
        "<tr><td colspan=\"2\" style=\"width:170.08pt;height:19.84pt;" + B.format(t="1.13") + "\">"
        "<p class=\"0\" style=\"text-align:center;\"><span style=\"font-weight:bold\">구&nbsp;분</span></p></td>"
        "<td style=\"width:85.04pt;height:19.84pt;" + B.format(t="1.13") + "\"><p style=\"text-align:center;\"><b>비고</b></p></td></tr>"
        "<tr><td rowspan=\"2\" style=\"width:85.04pt;height:39.68pt;" + B.format(t="0.28") + "\"><p style=\"text-align:left;\">총괄</p></td>"
        "<td style=\"width:85.04pt;height:19.84pt;" + B.format(t="0.28") + "\"><p>첫 줄</p><p>둘째 줄</p></td>"
        "<td style=\"width:85.04pt;height:19.84pt;border:double #000000 1.5pt;\"><p></p></td></tr>"
        "<tr><td style=\"width:85.04pt;height:19.84pt;border-bottom:dashed #000000 0.28pt;\"><p>가</p></td>"
        "<td style=\"width:85.04pt;height:19.84pt;border-top:none;border-right:dotted #000000 0.28pt;\"><p>나</p></td></tr>"
        "</table></p><!--EndFragment--></body></html>")


class HwpTableImportTest(unittest.TestCase):
    def test_structure_merges_text_and_alignment_survive(self):
        sketch = sketch_from_html(HTML.encode("utf-8"))
        self.assertEqual(sketch.pop("source"), {"rows": 3, "cols": 3})
        preview = table_sketch.preview(sketch)
        self.assertTrue(preview["ok"], preview["warnings"])
        self.assertEqual((preview["rows"], preview["cols"]), (3, 3))
        spans = {(c["row"], c["col"]): (c["rowspan"], c["colspan"]) for c in preview["cells"]}
        self.assertEqual(spans[(0, 0)], (1, 2))
        self.assertEqual(spans[(1, 0)], (2, 1))
        texts = {t["text"]: t for t in sketch["texts"]}
        self.assertTrue(texts["구 분"]["bold"])
        self.assertEqual(texts["총괄"]["align"], "left")
        self.assertEqual(texts["첫 줄\n둘째 줄"]["align"], "center")
        # 30mm 칸 폭(85.04pt) = 5mm 격자 6칸.
        self.assertEqual(texts["비고"]["x"] - texts["구 분"]["x"], 12)

    def test_border_weights_and_styles_become_sketch_lines(self):
        lines = sketch_from_html(HTML)["lines"]
        widths = {line["width"] for line in lines}
        styles = {line["style"] for line in lines}
        self.assertEqual(widths, {"thin", "thick", "double"})
        self.assertTrue({"dash", "dot"} <= styles)
        top = [l for l in lines if l["y1"] == l["y2"] == 1]
        self.assertTrue(top and all(l["width"] == "thick" for l in top))

    def test_no_table_on_clipboard_is_a_clear_message(self):
        with self.assertRaisesRegex(ValueError, "한/글에서 표를 선택해 복사"):
            sketch_from_html("<html><body><p>글만</p></body></html>")

    def test_service_reads_clipboard_html_and_returns_editable_sketch(self):
        with tempfile.TemporaryDirectory() as folder:
            service = TableSketchService(folder, clipboard_html=lambda: HTML)
            result = service.command("paste_hwp", {"cell_mm": 5.0})
            self.assertTrue(result["ok"])
            self.assertEqual((result["rows"], result["cols"]), (3, 3))
            self.assertTrue(table_sketch.preview(result["sketch"])["ok"])
            empty = TableSketchService(folder, clipboard_html=lambda: None).command("paste_hwp")
            self.assertFalse(empty["ok"])
            self.assertIn("복사", empty["message"])


if __name__ == "__main__":
    unittest.main()
