"""HWPX 및 클립보드 표 역변환(표그림판 모델) 단위 시험."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from defusedxml import ElementTree as ET

from docfit_core import table_import, table_sketch
from docfit_app.table_sketch_service import TableSketchService

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
HC = "{http://www.hancom.co.kr/hwpml/2011/core}"


class TestTableImport(unittest.TestCase):
    def test_import_from_xml(self):
        header_xml = f"""
        <hh:head xmlns:hh="{HH[1:-1]}" xmlns:hc="{HC[1:-1]}">
          <hh:refList>
            <hh:borderFills>
              <hh:borderFill id="1">
                <hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>
                <hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>
                <hh:topBorder type="SOLID" width="0.4 mm" color="#000000"/>
                <hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>
                <hc:fillBrush>
                  <hc:winBrush faceColor="#D9E1F2"/>
                </hc:fillBrush>
              </hh:borderFill>
              <hh:borderFill id="2">
                <hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>
                <hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>
                <hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>
                <hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>
              </hh:borderFill>
            </hh:borderFills>
            <hh:charProperties>
              <hh:charPr id="0" height="1000"/>
              <hh:charPr id="1" height="1000">
                <hh:bold/>
              </hh:charPr>
            </hh:charProperties>
            <hh:paraProperties>
              <hh:paraPr id="0"><hh:align horizontal="CENTER"/></hh:paraPr>
            </hh:paraProperties>
          </hh:refList>
        </hh:head>
        """
        header_info = {
            "borders": {
                "1": {
                    "fill": "#D9E1F2",
                    "borders": {
                        "left": {"type": "SOLID", "width": "0.12 mm", "color": "#000000"},
                        "right": {"type": "SOLID", "width": "0.12 mm", "color": "#000000"},
                        "top": {"type": "SOLID", "width": "0.4 mm", "color": "#000000"},
                        "bottom": {"type": "SOLID", "width": "0.12 mm", "color": "#000000"},
                    },
                },
                "2": {
                    "fill": "",
                    "borders": {
                        "left": {"type": "SOLID", "width": "0.12 mm", "color": "#000000"},
                        "right": {"type": "SOLID", "width": "0.12 mm", "color": "#000000"},
                        "top": {"type": "SOLID", "width": "0.12 mm", "color": "#000000"},
                        "bottom": {"type": "SOLID", "width": "0.12 mm", "color": "#000000"},
                    },
                },
            },
            "chars": {"0": {"bold": False}, "1": {"bold": True}},
            "paras": {"0": "CENTER"},
        }

        tbl_xml = f"""
        <hp:tbl xmlns:hp="{HP[1:-1]}" rowCnt="2" colCnt="2">
          <hp:tr>
            <!-- 1행 1열: 병합 셀(2열 병합), 헤더 배경색 -->
            <hp:tc borderFillIDRef="1">
              <hp:cellAddr rowAddr="0" colAddr="0"/>
              <hp:cellSpan rowSpan="1" colSpan="2"/>
              <hp:subList>
                <hp:p paraPrIDRef="0">
                  <hp:run charPrIDRef="1"><hp:t>제목 병합칸</hp:t></hp:run>
                </hp:p>
              </hp:subList>
            </hp:tc>
          </hp:tr>
          <hp:tr>
            <!-- 2행 1열 -->
            <hp:tc borderFillIDRef="2">
              <hp:cellAddr rowAddr="1" colAddr="0"/>
              <hp:cellSpan rowSpan="1" colSpan="1"/>
              <hp:subList>
                <hp:p paraPrIDRef="0">
                  <hp:run charPrIDRef="0"><hp:t>항목 A</hp:t></hp:run>
                </hp:p>
              </hp:subList>
            </hp:tc>
            <!-- 2행 2열 -->
            <hp:tc borderFillIDRef="2">
              <hp:cellAddr rowAddr="1" colAddr="1"/>
              <hp:cellSpan rowSpan="1" colSpan="1"/>
              <hp:subList>
                <hp:p paraPrIDRef="0">
                  <hp:run charPrIDRef="0"><hp:t>항목 B</hp:t></hp:run>
                </hp:p>
              </hp:subList>
            </hp:tc>
          </hp:tr>
        </hp:tbl>
        """
        table_elem = ET.fromstring(tbl_xml.encode("utf-8"))
        res = table_import.import_table_from_xml(table_elem, header_info)

        self.assertEqual(res["grid"]["rows"], 2)
        self.assertEqual(res["grid"]["cols"], 2)

        # 텍스트 추출 검증
        text_map = {(t["x"], t["y"]): t["text"] for t in res["texts"]}
        self.assertEqual(text_map.get((0, 0)), "제목 병합칸")
        self.assertEqual(text_map.get((0, 1)), "항목 A")
        self.assertEqual(text_map.get((1, 1)), "항목 B")

        # 굵은 글자 검증
        bold_texts = [t["text"] for t in res["texts"] if t.get("bold")]
        self.assertIn("제목 병합칸", bold_texts)

        # 배경색 추출 검증
        color_map = {(c["x"], c["y"]): c["color"] for c in res["cell_colors"]}
        self.assertEqual(color_map.get((0, 0)), "#D9E1F2")

        # 선분 목록 검증 (최소 둘레 및 분할선 생성)
        self.assertGreater(len(res["lines"]), 0)
        # 상단 0.4mm 굵은 선이 수집되었는지 확인
        thick_lines = [l for l in res["lines"] if l.get("width") == "thick" or l.get("width_mm") >= 0.4]
        self.assertGreater(len(thick_lines), 0)

    def test_import_from_html(self):
        html_content = """
        <table border="1" style="border-collapse: collapse;">
          <tr>
            <th colspan="2" style="background-color: #E2EFDA; font-weight: bold; text-align: center;">헤더 영역</th>
          </tr>
          <tr>
            <td style="text-align: left;">본문 1</td>
            <td style="text-align: right;">본문 2</td>
          </tr>
        </table>
        """
        res = table_import.import_table_from_html(html_content)

        self.assertEqual(res["grid"]["rows"], 2)
        self.assertEqual(res["grid"]["cols"], 2)

        text_map = {(t["x"], t["y"]): t["text"] for t in res["texts"]}
        self.assertEqual(text_map.get((0, 0)), "헤더 영역")
        self.assertEqual(text_map.get((0, 1)), "본문 1")
        self.assertEqual(text_map.get((1, 1)), "본문 2")

        # 정렬 검증
        align_map = {(t["x"], t["y"]): t.get("align") for t in res["texts"]}
        self.assertEqual(align_map.get((0, 1)), "left")
        self.assertEqual(align_map.get((1, 1)), "right")

        # 배경색 검증
        color_map = {(c["x"], c["y"]): c["color"] for c in res["cell_colors"]}
        self.assertEqual(color_map.get((0, 0)), "#E2EFDA")

    def test_service_bridge_import(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = TableSketchService(tmp_dir)
            html_snippet = "<table><tr><td>테스트</td></tr></table>"
            res = service.command("import", {"source_type": "html", "data": html_snippet})
            self.assertTrue(res.get("ok"))
            self.assertEqual(res["grid"]["rows"], 1)
            self.assertEqual(res["grid"]["cols"], 1)
            self.assertEqual(res["texts"][0]["text"], "테스트")


if __name__ == "__main__":
    unittest.main()
