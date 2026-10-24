"""표 템플릿 T형 디자인 및 컨테이너·중첩표 도형/서식 보존 단위 시험."""

from __future__ import annotations

import unittest
from defusedxml import ElementTree as ET

from docfit_core import table_catalog as catalog

HP = catalog._HP
HH = catalog._HH
HC = catalog._HC


class TestTableTemplateTShape(unittest.TestCase):
    def test_container_and_nested_tbl_drawing_roots(self):
        """컨테이너(묶음) 및 중첩 표 내부의 자식 도형들이 재귀적으로 누락 없이 탐색되는지 확인."""
        xml_data = f"""
        <hp:tc xmlns:hp="{HP[1:-1]}" xmlns:hc="{HC[1:-1]}">
          <hp:subList>
            <hp:p>
              <!-- 컨테이너 안에 묶인 도형들 -->
              <hp:container id="1">
                <hp:rect id="2"/>
                <hp:ellipse id="3"/>
              </hp:container>
              <!-- 중첩 표 안의 셀에 있는 도형 -->
              <hp:tbl>
                <hp:tr>
                  <hp:tc>
                    <hp:subList>
                      <hp:p>
                        <hp:line id="4"/>
                      </hp:p>
                    </hp:subList>
                  </hp:tc>
                </hp:tr>
              </hp:tbl>
            </hp:p>
          </hp:subList>
        </hp:tc>
        """
        node = ET.fromstring(xml_data.encode("utf-8"))
        drawings = list(catalog._drawing_roots(node))
        tags = [catalog._tag(d) for d in drawings]

        # container 자체와 내부의 rect, ellipse가 모두 포함되어야 함
        self.assertIn("container", tags)
        self.assertIn("rect", tags)
        self.assertIn("ellipse", tags)
        # 중첩 표 안의 line도 누락 없이 탐색되어야 함
        self.assertIn("line", tags)

    def test_cell_meta_preserves_outer_fill_and_borders_with_sub_tc(self):
        """셀 내부에 중첩 sub_tc가 있어도 바깥 셀의 배경색 및 테두리가 빈 서식으로 덮여 사라지지 않는지 확인."""
        header_xml = f"""
        <hh:head xmlns:hh="{HH[1:-1]}" xmlns:hc="{HC[1:-1]}">
          <hh:refList>
            <hh:borderFills>
              <!-- 바깥 셀 서식: 노란 배경색 (#FFFF00) -->
              <hh:borderFill id="10">
                <hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>
                <hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>
                <hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>
                <hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>
                <hc:fillBrush>
                  <hc:winBrush faceColor="#FFFF00"/>
                </hc:fillBrush>
              </hh:borderFill>
              <!-- 내부 sub_tc 서식: 배경색 없음 (투명) -->
              <hh:borderFill id="20">
                <hh:leftBorder type="NONE"/>
                <hh:rightBorder type="NONE"/>
                <hh:topBorder type="NONE"/>
                <hh:bottomBorder type="NONE"/>
              </hh:borderFill>
            </hh:borderFills>
          </hh:refList>
        </hh:head>
        """
        header_info = catalog._header_lookup(ET.fromstring(header_xml.encode("utf-8")))

        tc_xml = f"""
        <hp:tc xmlns:hp="{HP[1:-1]}" borderFillIDRef="10">
          <hp:cellAddr rowAddr="1" colAddr="0"/>
          <hp:cellSpan rowSpan="1" colSpan="2"/>
          <hp:cellSz width="10000" height="3000"/>
          <hp:subList>
            <hp:p>
              <hp:tbl>
                <hp:tr>
                  <hp:tc borderFillIDRef="20">
                    <hp:subList>
                      <hp:p>
                        <hp:run><hp:t>하단 디자인 내용</hp:t></hp:run>
                      </hp:p>
                    </hp:subList>
                  </hp:tc>
                </hp:tr>
              </hp:tbl>
            </hp:p>
          </hp:subList>
        </hp:tc>
        """
        tc_node = ET.fromstring(tc_xml.encode("utf-8"))
        meta = catalog._cell_meta(tc_node, 1, 0, "하단 디자인 내용", header_info)

        # sub_tc의 투명 배경이 아니라 원래 바깥 셀의 fill 색상(#FFFF00)이 유지되어야 함
        self.assertEqual(meta["style"]["fill"], "#FFFF00")
        # 병합 정보도 보존되어야 함
        self.assertEqual(meta["rowSpan"], 1)
        self.assertEqual(meta["colSpan"], 2)


if __name__ == "__main__":
    unittest.main()
