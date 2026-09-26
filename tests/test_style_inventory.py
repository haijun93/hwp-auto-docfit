"""문서 스타일 전수 분석과 예시 서식 HWPX 생성."""
from pathlib import Path
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from docfit_core.style_inventory import analyze_style_inventory, build_style_sample, inventory_markdown

NS = ('xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
      'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
      'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
      'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"')


def char(cid, height, bold=False, color="#000000", sup=False, spacing=0, strike="NONE", shade="none"):
    return (f'<hh:charPr id="{cid}" height="{height}" textColor="{color}" shadeColor="{shade}" borderFillIDRef="1">'
            '<hh:fontRef hangul="0" latin="0" hanja="0"/><hh:ratio hangul="100"/>'
            f'<hh:spacing hangul="{spacing}"/><hh:relSz hangul="100"/><hh:offset hangul="0"/>'
            + ("<hh:bold/>" if bold else "") + ("<hh:supscript/>" if sup else "")
            + f'<hh:underline type="NONE"/><hh:strikeout shape="{strike}"/><hh:outline type="NONE"/>'
            '<hh:shadow type="NONE"/></hh:charPr>')


def para(pid, indent=0, line=160):
    return (f'<hh:paraPr id="{pid}"><hh:align horizontal="JUSTIFY"/><hh:heading type="NONE" level="0"/>'
            f'<hh:margin><hc:intent value="{indent}"/><hc:left value="0"/><hc:right value="0"/>'
            f'<hc:prev value="0"/><hc:next value="0"/></hh:margin>'
            f'<hh:lineSpacing type="PERCENT" value="{line}"/></hh:paraPr>')


HEADER = (f'<?xml version="1.0" encoding="UTF-8"?><hh:head {NS} secCnt="1"><hh:refList>'
          '<hh:fontfaces><hh:fontface lang="HANGUL"><hh:font id="0" face="함초롬바탕"/></hh:fontface></hh:fontfaces>'
          '<hh:borderFills><hh:borderFill id="1"><hh:leftBorder type="NONE" width="0.1 mm" color="#000000"/>'
          '</hh:borderFill></hh:borderFills><hh:charProperties>'
          + char(0, 1500, bold=True) + char(1, 1500) + char(2, 1500, bold=True)
          + char(3, 1500, sup=True) + char(4, 1500, color="#0000FF") + char(5, 1500, spacing=-8)
          + char(6, 1500, strike="3D") + char(7, 1500, shade="#FFFF00") + char(8, 1500, shade="#FFFFFF")
          + '</hh:charProperties><hh:paraProperties>'
          + para(0) + para(1, -2948) + para(2, -2948, 150)
          + '</hh:paraProperties><hh:styles><hh:style id="0" type="PARA" name="바탕글" paraPrIDRef="0" charPrIDRef="1"/>'
          '</hh:styles></hh:refList></hh:head>').encode()


def p(pid, *runs):
    body = "".join(f'<hp:run charPrIDRef="{c}"><hp:t>{t}</hp:t></hp:run>' for c, t in runs)
    return f'<hp:p paraPrIDRef="{pid}" styleIDRef="0">{body}<hp:linesegarray/></hp:p>'


SECTION = (f'<?xml version="1.0" encoding="UTF-8"?><hs:sec {NS}>'
           '<hp:p paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="1"><hp:secPr><hp:pagePr width="59528" '
           'height="84186" landscape="WIDELY"><hp:margin left="5669" right="5669" top="2834" bottom="2834" '
           'header="2834" footer="2834" gutter="0"/></hp:pagePr></hp:secPr><hp:t/></hp:run></hp:p>'
           + p(0, (0, "□ 추진 배경"))
           + "".join(p(1, (2, "ㅇ (현황) "), (1, f"본문 문장 {i}번입니다")) for i in range(10))
           + p(2, (1, "ㅇ 줄간격만 다른 본문"), (3, "*"))
           + p(1, (5, "ㅇ 자간을 줄인 본문"), (4, "강조"))
           + p(1, (6, "ㅇ 3D 모양 값"))
           + p(1, (1, "ㅇ 일부만 "), (7, "노란 음영"), (8, " 흰 음영"))
           + p(0, (7, "□ 전체 음영 제목"))
           + '<hp:p paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="1"><hp:tbl colCnt="1" rowCnt="1" '
           'borderFillIDRef="1"><hp:sz width="48000"/><hp:tr><hp:tc borderFillIDRef="1"><hp:subList>'
           + p(0, (0, "표 제목")) + '</hp:subList></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>'
           + '</hs:sec>').encode()


def make_hwpx(path):
    with ZipFile(path, "w", ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/hwp+zip")
        z.writestr("Contents/header.xml", HEADER)
        z.writestr("Contents/section0.xml", SECTION)


class StyleInventoryTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.source = Path(self.folder.name) / "doc.hwpx"
        make_hwpx(self.source)
        self.inv = analyze_style_inventory(self.source)

    def tearDown(self):
        self.folder.cleanup()

    def test_groups_by_visible_style_not_line_fitting(self):
        # 줄간격·자간만 다른 ㅇ 문단은 한 유형으로 묶이고 범위로 보고된다.
        types = {(t["marker"], t["main_char"]): t for t in self.inv["types"]}
        body = next(t for t in self.inv["types"] if t["marker"] == "ㅇ")
        self.assertEqual(len([t for t in self.inv["types"] if t["marker"] == "ㅇ"]), 1)
        self.assertEqual(body["count"], 14)
        self.assertEqual(body["line"], {"mode": 160, "min": 150, "max": 160})
        self.assertEqual(body["spacing"]["min"], -8)
        self.assertIn(("□", "0"), types)

    def test_superscript_and_font_color_are_style_elements(self):
        body = next(t for t in self.inv["types"] if t["marker"] == "ㅇ")
        self.assertEqual(body["effects"].get("위첨자"), 1)
        self.assertEqual(body["effects"].get("글자색 #0000FF"), 1)
        self.assertEqual(body["effects"].get("굵게"), 10)
        self.assertIn("위첨자", self.inv["inline_effects"])
        report = inventory_markdown(self.inv)
        self.assertIn("부분 글자 서식", report)
        self.assertIn("글자색 #0000FF", report)
        self.assertNotIn("취소선", report)  # shape="3D"는 취소선이 아니다

    def test_shade_color_is_style_element(self):
        # 부분 음영은 부분 서식, 문단 전체 음영은 별도 스타일 유형, 흰색은 음영 없음
        self.assertEqual(list(self.inv["shade_colors"]), ["#FFFF00"])
        self.assertEqual(self.inv["shade_colors"]["#FFFF00"]["runs"], 2)
        body = next(t for t in self.inv["types"] if t["marker"] == "ㅇ")
        self.assertEqual(body["effects"].get("음영 #FFFF00"), 1)
        self.assertEqual(len([t for t in self.inv["types"] if t["marker"] == "□"]), 2)
        report = inventory_markdown(self.inv)
        self.assertIn("글자 음영색", report)
        self.assertIn("음영 #FFFF00", report)
        self.assertNotIn("음영 #FFFFFF", report)

    def test_counts_definitions_and_usage(self):
        s = self.inv["summary"]
        self.assertEqual(s["chars_defined"], 9)
        self.assertEqual(s["paras_used"], 3)
        self.assertEqual(s["table_types"], 1)
        self.assertEqual(self.inv["page"]["margin_mm"]["left"], 20.0)

    def test_sample_keeps_page_setup_effects_and_tables(self):
        target = Path(self.folder.name) / "sample.hwpx"
        stats = build_style_sample(self.source, target, self.inv, budget=4)
        with ZipFile(target) as z:
            section = z.read("Contents/section0.xml").decode("utf-8")
            self.assertEqual(z.read("Contents/header.xml"), HEADER)
        self.assertIn("secPr", section)
        self.assertIn("□ 추진 배경", section)
        self.assertIn("표 제목", section)
        self.assertIn('charPrIDRef="3"', section)  # 위첨자 문단
        self.assertIn('charPrIDRef="4"', section)  # 글자색 문단
        self.assertIn('charPrIDRef="7"', section)  # 음영 문단
        self.assertNotIn("linesegarray", section)
        self.assertNotIn("ns0:", section)
        self.assertLess(section.count("본문 문장"), 10)
        self.assertEqual(stats["tables"], 1)


if __name__ == "__main__":
    unittest.main()
