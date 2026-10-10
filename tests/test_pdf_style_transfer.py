import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from defusedxml import ElementTree as ET

from docfit_core.pdf_style_transfer import pdf_font, transfer

HH = "http://www.hancom.co.kr/hwpml/2011/head"
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HC = "http://www.hancom.co.kr/hwpml/2011/core"
HEADER = f'''<?xml version="1.0" encoding="UTF-8"?>
<hh:head xmlns:hh="{HH}" xmlns:hc="{HC}"><hh:refList>
<hh:fontfaces itemCnt="1"><hh:fontface lang="HANGUL" fontCnt="1"><hh:font id="0" face="한컴돋움" type="TTF" isEmbedded="0"/></hh:fontface>
<hh:fontface lang="LATIN" fontCnt="1"><hh:font id="0" face="한컴돋움" type="TTF" isEmbedded="0"/></hh:fontface></hh:fontfaces>
<hh:borderFills itemCnt="1"><hh:borderFill id="1" threeD="0" shadow="0"><hh:leftBorder type="NONE" width="0.1 mm" color="#000000"/></hh:borderFill></hh:borderFills>
<hh:charProperties itemCnt="1"><hh:charPr id="0" height="1500" textColor="#000000" shadeColor="none" borderFillIDRef="1">
<hh:fontRef hangul="0" latin="0"/><hh:ratio hangul="100" latin="100"/><hh:bold/></hh:charPr></hh:charProperties>
</hh:refList></hh:head>'''
SECTION = f'''<?xml version="1.0" encoding="UTF-8"?>
<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="{HP}">
<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>가나<hp:lineBreak/>다라</hp:t></hp:run></hp:p>
<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:tbl><hp:tr><hp:tc borderFillIDRef="1"><hp:subList>
<hp:p paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>셀글</hp:t></hp:run></hp:p></hp:subList></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>
</hs:sec>'''


def style(font="함초롬바탕", size=15.0, bold=False, color="#000000", bg=None, ratio=100):
    return {"font": font, "size": size, "bold": bold, "color": color, "bg": bg, "ratio": ratio, "page": 1}


class PdfStyleTransferTests(unittest.TestCase):
    def make(self, folder):
        path = Path(folder) / "in.hwpx"
        with ZipFile(path, "w") as z:
            z.writestr("mimetype", "application/hwp+zip")
            z.writestr("Contents/header.xml", HEADER)
            z.writestr("Contents/section0.xml", SECTION)
        return path

    def read(self, path):
        with ZipFile(path) as z:
            return ET.fromstring(z.read("Contents/header.xml")), ET.fromstring(z.read("Contents/section0.xml"))

    def test_font_name_mapping_and_bold_from_name(self):
        self.assertEqual(pdf_font("ABCDEF+HCRBatang-Bold"), ("함초롬바탕", True))
        self.assertEqual(pdf_font("ABCDEF+MalgunGothic"), ("맑은 고딕", False))
        self.assertEqual(pdf_font("Unknown"), ("Unknown", False))

    def test_splits_runs_by_style_keeps_line_break_and_fills_cell(self):
        blue = style(color="#0000FF", bold=True)
        chars = [("가", style()), ("나", style()), ("다", blue), ("라", blue),
                 ("셀", style(bg="#E8F7FC", size=12.0)), ("글", style(bg="#E8F7FC", size=12.0))]
        with tempfile.TemporaryDirectory() as folder:
            source = self.make(folder)
            out = Path(folder) / "out.hwpx"
            stats = transfer(chars, source, out)
            header, section = self.read(out)
        self.assertEqual(stats["matched"], 6)
        self.assertEqual(stats["cells_filled"], 1)
        shapes = {e.get("id"): e for e in header.iter(f"{{{HH}}}charPr")}
        first = section.find(f"{{{HP}}}p")
        runs = first.findall(f"{{{HP}}}run")
        self.assertEqual(len(runs), 2)
        # 줄바꿈 요소는 앞 글자(검정) 조각에 남고, 글자 순서는 그대로다.
        self.assertEqual("".join(runs[0].itertext()) + "".join(runs[1].itertext()), "가나다라")
        self.assertIsNotNone(runs[0].find(f".//{{{HP}}}lineBreak"))
        black, blue_shape = shapes[runs[0].get("charPrIDRef")], shapes[runs[1].get("charPrIDRef")]
        self.assertEqual(black.get("textColor"), "#000000")
        self.assertIsNone(black.find(f"{{{HH}}}bold"))           # PDF가 굵게가 아니면 굵게를 뺀다
        self.assertEqual(blue_shape.get("textColor"), "#0000FF")
        self.assertIsNotNone(blue_shape.find(f"{{{HH}}}bold"))
        fonts = {e.get("id"): e.get("face") for e in header.iter(f"{{{HH}}}font")}
        self.assertEqual(fonts[blue_shape.find(f"{{{HH}}}fontRef").get("hangul")], "함초롬바탕")
        cell = section.find(f".//{{{HP}}}tc")
        fills = {e.get("id"): e for e in header.iter(f"{{{HH}}}borderFill")}
        brush = fills[cell.get("borderFillIDRef")].find(f".//{{{HC}}}winBrush")
        self.assertEqual(brush.get("faceColor"), "#E8F7FC")
        cell_run = cell.find(f".//{{{HP}}}run")
        self.assertEqual(shapes[cell_run.get("charPrIDRef")].get("height"), "1200")
        self.assertEqual(shapes[cell_run.get("charPrIDRef")].get("shadeColor"), "none")  # 셀 배경은 셀에서

    def test_unmatched_text_keeps_original_shape(self):
        with tempfile.TemporaryDirectory() as folder:
            source = self.make(folder)
            out = Path(folder) / "out.hwpx"
            stats = transfer([("X", style()), ("Y", style())], source, out)
            header, section = self.read(out)
        self.assertEqual(stats["matched"], 0)
        self.assertEqual({r.get("charPrIDRef") for r in section.iter(f"{{{HP}}}run")}, {"0"})


if __name__ == "__main__":
    unittest.main()
