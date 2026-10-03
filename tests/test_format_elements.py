"""서식 요소 전수 분석: 계층별·서식 표 칸별 대표값, 예시 표 보관·세부값 수정, 프로필 반영."""
import copy
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from defusedxml import ElementTree as ET

from docfit_core import format_elements as fe

NS = ('xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
      'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
      'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
      'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"')
LANGS = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")


def _fonts():
    faces = ("명조", "돋움", "헤드라인")
    return "".join(f'<hh:fontface lang="{lang.upper()}" fontCnt="3">'
                   + "".join(f'<hh:font id="{i}" face="{face}" type="TTF" isEmbedded="0"/>'
                             for i, face in enumerate(faces))
                   + "</hh:fontface>" for lang in LANGS)


def _char(char_id, font=0, height=1500, bold=False, color="#000000", italic=False, underline="NONE"):
    ref = " ".join(f'{lang}="{font}"' for lang in LANGS)
    hundred = " ".join(f'{lang}="100"' for lang in LANGS)
    zero = " ".join(f'{lang}="0"' for lang in LANGS)
    return (f'<hh:charPr id="{char_id}" height="{height}" textColor="{color}" shadeColor="none" '
            f'borderFillIDRef="1"><hh:fontRef {ref}/><hh:ratio {hundred}/><hh:spacing {zero}/>'
            f'<hh:relSz {hundred}/><hh:offset {zero}/>' + ("<hh:italic/>" if italic else "")
            + ("<hh:bold/>" if bold else "")
            + f'<hh:underline type="{underline}" shape="SOLID" color="#000000"/>'
            '<hh:strikeout shape="3D" color="#000000"/><hh:outline type="NONE"/>'
            '<hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/></hh:charPr>')


def _para(para_id, align="JUSTIFY", left=0, indent=0, prev=0, line=160):
    def margin(factor):
        return (f'<hh:margin><hc:intent value="{indent * factor}" unit="HWPUNIT"/>'
                f'<hc:left value="{left * factor}" unit="HWPUNIT"/><hc:right value="0" unit="HWPUNIT"/>'
                f'<hc:prev value="{prev * factor}" unit="HWPUNIT"/><hc:next value="0" unit="HWPUNIT"/>'
                f'</hh:margin><hh:lineSpacing type="PERCENT" value="{line}" unit="HWPUNIT"/>')
    return (f'<hh:paraPr id="{para_id}" tabPrIDRef="0"><hh:align horizontal="{align}" vertical="BASELINE"/>'
            '<hp:switch><hp:case hp:required-namespace="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar">'
            + margin(1) + '</hp:case><hp:default>' + margin(2) + '</hp:default></hp:switch>'
            '<hh:border borderFillIDRef="1"/></hh:paraPr>')


def _fill(fill_id, side="NONE", width="0.1 mm", color="none"):
    sides = "".join(f'<hh:{s}Border type="{side}" width="{width}" color="#000000"/>'
                    for s in ("left", "right", "top", "bottom"))
    return (f'<hh:borderFill id="{fill_id}" threeD="0" shadow="0">{sides}'
            f'<hc:fillBrush><hc:winBrush faceColor="{color}" hatchColor="#999999" alpha="0"/></hc:fillBrush>'
            '</hh:borderFill>')


HEADER = (f'<hh:head {NS} version="1.4"><hh:refList><hh:fontfaces itemCnt="7">{_fonts()}</hh:fontfaces>'
          f'<hh:borderFills itemCnt="4">{_fill(1)}{_fill(2, "SOLID", "0.4 mm")}{_fill(3, "SOLID", "0.12 mm", "#DFE6F7")}'
          f'{_fill(4, "DOUBLE_SLIM", "0.5 mm")}</hh:borderFills>'
          f'<hh:charProperties itemCnt="8">{_char(0)}{_char(1, bold=True)}{_char(2, height=1300)}'
          f'{_char(3, font=1)}{_char(4, font=2, height=2700, bold=True)}{_char(5, height=1200)}'
          f'{_char(6, font=1, height=1600)}{_char(7, italic=True, underline="BOTTOM")}</hh:charProperties>'
          '<hh:tabProperties itemCnt="1"><hh:tabPr id="0" autoTabLeft="0" autoTabRight="0"/></hh:tabProperties>'
          f'<hh:paraProperties itemCnt="4">{_para(0, left=1500, indent=-1310)}{_para(1, align="CENTER")}'
          f'{_para(2, prev=1000)}{_para(3, align="LEFT", left=300)}</hh:paraProperties>'
          '<hh:styles itemCnt="1"><hh:style id="0" type="PARA" name="바탕글" paraPrIDRef="0" charPrIDRef="0"/>'
          '</hh:styles></hh:refList></hh:head>')


def _p(para_id, *runs, lines=2):
    body = "".join(f'<hp:run charPrIDRef="{c}"><hp:t>{t}</hp:t></hp:run>' for c, t in runs)
    segs = "".join(f'<hp:lineseg textpos="{i}" vertpos="0" vertsize="1500" textheight="1500" baseline="1275" '
                   f'spacing="900" horzpos="0" horzsize="42520" flags="0"/>' for i in range(lines))
    return f'<hp:p paraPrIDRef="{para_id}" styleIDRef="0">{body}<hp:linesegarray>{segs}</hp:linesegarray></hp:p>'


def _cell(col, row, fill, width, text_runs, para=1, span=1, valign="CENTER"):
    paragraph = "".join(f'<hp:run charPrIDRef="{c}"><hp:t>{t}</hp:t></hp:run>' for c, t in text_runs)
    return (f'<hp:tc borderFillIDRef="{fill}" hasMargin="0"><hp:subList vertAlign="{valign}">'
            f'<hp:p paraPrIDRef="{para}" styleIDRef="0">{paragraph}</hp:p></hp:subList>'
            f'<hp:cellAddr colAddr="{col}" rowAddr="{row}"/><hp:cellSpan colSpan="{span}" rowSpan="1"/>'
            f'<hp:cellSz width="{width}" height="2000"/><hp:cellMargin left="141" right="141" top="141" bottom="141"/>'
            '</hp:tc>')


TITLE = ('<hp:tbl rowCnt="2" colCnt="2" borderFillIDRef="1"><hp:sz width="48000" height="8000"/>'
         '<hp:outMargin left="283" right="283" top="283" bottom="283"/>'
         '<hp:inMargin left="141" right="141" top="141" bottom="141"/>'
         '<hp:tr>' + _cell(0, 0, 2, 48000, [(4, "제목 문장 검토 보고")], span=2) + '</hp:tr>'
         '<hp:tr>' + _cell(0, 1, 3, 8000, [(5, "26. 10. 3.(토)")]) + _cell(1, 1, 3, 40000, [(5, "행정과장")])
         + '</hp:tr></hp:tbl>')
OVERVIEW = ('<hp:tbl rowCnt="1" colCnt="1" borderFillIDRef="1"><hp:sz width="48000" height="5000"/>'
            '<hp:outMargin left="283" right="283" top="283" bottom="283"/>'
            '<hp:inMargin left="141" right="141" top="141" bottom="141"/>'
            '<hp:tr>' + _cell(0, 0, 4, 48000, [(6, "개요 문장으로 열다섯 글자를 넘는 요지를 적습니다")], para=3)
            + '</hp:tr></hp:tbl>')
SECTION = (f'<hs:sec {NS}>'
           '<hp:p paraPrIDRef="1" styleIDRef="0"><hp:run charPrIDRef="0"><hp:secPr><hp:pagePr width="59528" '
           'height="84186"><hp:margin header="3600" footer="3600" gutter="0" left="5102" right="5102" top="3600" '
           'bottom="3600"/></hp:pagePr></hp:secPr></hp:run>'
           f'<hp:run charPrIDRef="0">{TITLE}</hp:run><hp:run charPrIDRef="0">{OVERVIEW}</hp:run></hp:p>'
           + _p(0, (1, "ㅇ"), (0, " 첫째 문장입니다 "), (2, "(참고 내용)"), (0, " 이어지는 글"))
           + _p(0, (1, "ㅇ"), (0, " 둘째 문장입니다"))
           + _p(0, (1, "ㅇ"), (0, " 셋째 문장입니다"))
           + _p(0, (1, "ㅇ"), (3, " 넷째 문장은 돋움으로 쓴 다른 서식"))
           + _p(2, (1, "□ 소제목 하나"), lines=1)
           + _p(2, (1, "□ 소제목 둘"), lines=1)
           + _p(0, (7, "ㅇ 기울임과 밑줄로 쓴 다섯째 문장"))
           + '</hs:sec>')


def classify(table):
    rows, cols = table.get("rowCnt"), table.get("colCnt")
    if (rows, cols) == ("2", "2"):
        return "title1"
    if (rows, cols) == ("1", "1"):
        return "box"
    return None


class FormatElementsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory(prefix="docfit-elements-")
        cls.path = Path(cls.folder.name) / "example.hwpx"
        with ZipFile(cls.path, "w") as archive:
            archive.writestr("mimetype", "application/hwp+zip")
            archive.writestr("Contents/header.xml", HEADER)
            archive.writestr("Contents/section0.xml", SECTION)
        cls.analysis = fe.analyze_format_elements(cls.path, classify)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def group(self, marker):
        return next(g for g in self.analysis["paragraph_groups"] if g["marker"] == marker)

    def test_marker_sentences_get_representative_values_per_element(self):
        group = self.group("ㅇ")
        self.assertEqual(group["role"], "본문")
        self.assertEqual(group["count"], 5)
        elements = group["elements"]
        self.assertEqual(elements["font"]["value"], "명조")
        self.assertEqual((elements["font"]["votes"], elements["font"]["total"]), (4, 5))
        self.assertEqual(elements["size"]["value"], 1500)
        self.assertTrue(elements["marker_bold"]["value"])
        self.assertFalse(elements["bold"]["value"])
        self.assertFalse(elements["italic"]["value"])
        self.assertEqual(elements["underline"]["value"], "NONE")
        self.assertEqual(elements["after_spaces"]["value"], 1)
        self.assertEqual(elements["lead_spaces"]["value"], 0)
        # 문장 안 괄호 부연은 본문 크기 표본에서 빼고, 본문보다 2pt 작게 쓴 관행으로 남긴다.
        self.assertEqual(elements["paren_delta"]["value"], 200)
        # 문단 여백은 hp:case(실제 HWPUNIT) 값이다(hp:default는 두 배).
        self.assertEqual(elements["left"]["value"], 1500)
        self.assertEqual(elements["indent"]["value"], -1310)
        self.assertTrue(elements["hanging"]["value"])
        box = self.group("□")
        self.assertEqual(box["elements"]["prev"]["value"], 1000)
        # 한 줄 문장은 내어쓰기가 보이지 않으므로 표본이 없다.
        self.assertNotIn("hanging", box["elements"])

    def test_title_table_cells_are_analyzed_by_address(self):
        self.assertEqual(list(self.analysis["forms"]), ["title1", "overview"])
        title = self.analysis["forms"]["title1"]
        self.assertEqual(list(title["cells"]), ["A1", "A2", "B2"])
        a1 = title["cells"]["A1"]["paras"][0]
        self.assertEqual((a1["font"]["value"], a1["size"]["value"], a1["bold"]["value"]), ("헤드라인", 2700, True))
        self.assertEqual(a1["align"]["value"], "CENTER")
        self.assertEqual(title["cells"]["A1"]["cell"]["border_top"]["value"], "SOLID|0.4 mm|#000000")
        self.assertEqual(title["cells"]["B2"]["cell"]["fill"]["value"], "#DFE6F7")
        self.assertEqual(title["cells"]["B2"]["paras"][0]["size"]["value"], 1200)
        self.assertEqual(title["table"]["out_left"]["value"], 283)
        overview = self.analysis["forms"]["overview"]["cells"]["A1"]
        self.assertEqual(overview["paras"][0]["font"]["value"], "돋움")
        self.assertEqual(overview["cell"]["border_left"]["value"], "DOUBLE_SLIM|0.5 mm|#000000")
        self.assertEqual(self.analysis["page"]["page_left"]["value"], 5102)

    def test_sample_keeps_only_used_shapes(self):
        sample = self.analysis["samples"]["title1"]
        header = ET.fromstring(sample["header_xml"].encode("utf-8"))
        chars = {e.get("id") for e in header.iter() if fe._tag(e) == "charPr"}
        self.assertEqual(chars, {"4", "5"})
        groups = {fe._tag(e) for e in header.iter()}
        self.assertTrue({"borderFills", "charProperties", "paraProperties", "tabProperties"} <= groups)
        self.assertNotIn("styles", groups)
        record = fe.sample_record(sample)
        self.assertEqual(record["cells"]["A1"]["paras"][0]["size"], 2700)

    def test_cell_edit_clones_shared_shapes(self):
        sample = self.analysis["samples"]["title1"]
        edited = fe.apply_sample_edits(sample, {"border_left": "SOLID|0.4 mm|#FF0000"}, {
            "A2": {"cell": {"fill": "#FFFF00", "valign": "TOP"},
                   "paras": {0: {"font": "돋움", "size": 1100, "color": "#0000FF", "align": "LEFT", "left": 400}}}})
        record = fe.sample_record(edited)
        a2, b2 = record["cells"]["A2"], record["cells"]["B2"]
        self.assertEqual((a2["paras"][0]["font"], a2["paras"][0]["size"]), ("돋움", 1100))
        self.assertEqual(a2["paras"][0]["color"], "#0000FF")
        self.assertEqual(a2["cell"]["fill"], "#FFFF00")
        self.assertEqual(a2["cell"]["valign"], "TOP")
        self.assertEqual(a2["paras"][0]["left"], 400)
        # B2는 A2와 같은 글자·테두리 모양을 썼지만 그대로다(고친 모양은 새 ID로 복제).
        self.assertEqual((b2["paras"][0]["font"], b2["paras"][0]["size"]), ("명조", 1200))
        self.assertEqual(b2["cell"]["fill"], "#DFE6F7")
        self.assertEqual(record["table"]["border_left"], "SOLID|0.4 mm|#FF0000")
        # hp:switch의 default에는 두 배 값을 쓴다.
        header = ET.fromstring(edited["header_xml"].encode("utf-8"))
        table = ET.fromstring(edited["table_xml"].encode("utf-8"))
        para_id = fe.cell_paragraphs(dict(fe.table_cells(table))["A2"])[0].get("paraPrIDRef")
        para = next(e for e in header.iter() if fe._tag(e) == "paraPr" and e.get("id") == para_id)
        values = [int(e.get("value")) for e in para.iter() if fe._tag(e) == "left"]
        self.assertEqual(values, [400, 800])

    def test_value_parsing_and_display(self):
        self.assertEqual(fe.parse_value("size", "15pt"), 1500)
        self.assertEqual(fe.format_value("size", 1350), "13.5pt")
        self.assertEqual(fe.parse_value("border_top", "실선 0.4 mm #ff0000"), "SOLID|0.4 mm|#FF0000")
        self.assertEqual(fe.format_value("border_top", "SOLID|0.4 mm|#FF0000"), "실선 0.4 mm #FF0000")
        self.assertEqual(fe.parse_value("border_top", "없음"), "NONE|0.1 mm|#000000")
        self.assertEqual(fe.parse_value("align", "가운데"), "CENTER")
        self.assertIs(fe.parse_value("bold", "예"), True)
        self.assertEqual(fe.parse_value("fill", "없음"), "없음")
        self.assertEqual(fe.parse_value("margin_left", "1mm"), 283)
        for key, text in (("size", "크게"), ("color", "#12"), ("align", "위쪽"), ("spacing", "80")):
            with self.assertRaises(ValueError):
                fe.parse_value(key, text)

    def test_detail_nodes_point_to_element_maps(self):
        nodes = fe.detail_nodes(self.analysis)
        labels = [label for _, _, label in nodes]
        self.assertIn("A1 칸 (제목)", labels)
        self.assertIn("B2 칸 (담당자)", labels)
        with_elements = [path for path, _, _ in nodes if fe.element_map(self.analysis, path)]
        self.assertIn(("form", "title1", "para", "A1", 0), with_elements)
        self.assertIn(("page",), with_elements)

    def test_edits_flow_into_profile_rules_and_stored_sample(self):
        analysis = copy.deepcopy(self.analysis)
        profile = {"format": {"기호_규칙": [("ㅇ", 1, "기존", 15, True, False)], "복사_문단모양": {},
                              "여백_mm": {}},
                   "options": {}, "element_analysis": analysis,
                   "form_tables": {"title1": analysis.pop("samples")["title1"]},
                   "style_hierarchy": {"styles": [{"role": "본문", "marker": "ㅇ", "count": 5,
                                                   "font": "명조", "size_pt": 15}],
                                       "variants": [{"role": "본문", "marker": "ㅇ", "count": 5,
                                                     "font": "명조", "size_pt": 15}]}}
        number = next(i for i, g in enumerate(analysis["paragraph_groups"]) if g["marker"] == "ㅇ")
        fe.set_value(analysis, ("group", number), "font", "돋움")
        fe.set_value(analysis, ("form", "title1", "para", "A1", 0), "size", 2500)
        fe.apply_to_profile(profile)
        rule = profile["format"]["기호_규칙"][0]
        self.assertEqual(rule[:5], ("ㅇ", 0, "돋움", 15, False))
        self.assertTrue(rule[5])   # 기호만 굵게
        self.assertEqual(profile["options"]["symbol_fonts"]["ㅇ"], {"font": "돋움", "size": "15"})
        self.assertEqual(profile["format"]["복사_문단모양"]["ㅇ"]["LeftMargin"], 1500)
        self.assertAlmostEqual(profile["format"]["여백_mm"]["left"], 18.0, places=1)
        record = fe.sample_record(profile["form_tables"]["title1"])
        self.assertEqual(record["cells"]["A1"]["paras"][0]["size"], 2500)
        self.assertEqual(profile["style_hierarchy"]["styles"][0]["font"], "돋움")
        item = analysis["paragraph_groups"][number]["elements"]["font"]
        self.assertEqual((item["analyzed"], item["edited"]), ("명조", True))

    def test_hierarchy_review_changes_move_into_analysis(self):
        analysis = copy.deepcopy(self.analysis)
        before = [{"role": "본문", "marker": "ㅇ", "font": "명조", "size_pt": 15}]
        profile = {"element_analysis": analysis,
                   "style_hierarchy": {"styles": [{"role": "본문", "marker": "ㅇ", "font": "명조", "size_pt": 16}]}}
        fe.sync_from_hierarchy(profile, before)
        group = next(g for g in analysis["paragraph_groups"] if g["marker"] == "ㅇ")
        self.assertEqual(group["elements"]["size"]["value"], 1600)
        self.assertNotIn("edited", group["elements"]["font"])


if __name__ == "__main__":
    unittest.main()
