"""표 셀 내 이미지를 배경 이미지로 변경 기능 단위 시험."""

from __future__ import annotations

import io
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from defusedxml import ElementTree as ET

from docfit_core import cell_image_bg
from docfit_core.cell_image_bg import (
    convert_cell_images_to_background,
    convert_cell_images_in_archive,
    process_cell_image_to_bg,
)

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
HC = "{http://www.hancom.co.kr/hwpml/2011/core}"


class TestCellImageBg(unittest.TestCase):
    def _create_mock_header(self) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<hh:head xmlns:hh="{HH[1:-1]}" xmlns:hc="{HC[1:-1]}">
  <hh:refList>
    <hh:borderFills itemCnt="2">
      <hh:borderFill id="1" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">
        <hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>
        <hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>
        <hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>
        <hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>
      </hh:borderFill>
      <hh:borderFill id="2" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">
        <hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>
        <hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>
        <hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>
        <hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>
      </hh:borderFill>
    </hh:borderFills>
  </hh:refList>
</hh:head>
"""

    def _create_mock_section(self) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<hp:sec xmlns:hp="{HP[1:-1]}" xmlns:hc="{HC[1:-1]}">
  <hp:p id="1">
    <hp:tbl rowCnt="2" colCnt="2">
      <hp:tr>
        <!-- 셀 1: 단독 그림만 있음 (변환 대상) -->
        <hp:tc borderFillIDRef="1">
          <hp:subList>
            <hp:p id="101">
              <hp:run>
                <hp:pic id="pic1">
                  <hp:img binaryItemIDRef="image1.png"/>
                </hp:pic>
              </hp:run>
            </hp:p>
          </hp:subList>
        </hp:tc>
        <!-- 셀 2: 그림과 텍스트가 함께 있음 (건너뜀) -->
        <hp:tc borderFillIDRef="1">
          <hp:subList>
            <hp:p id="102">
              <hp:run>
                <hp:t>설명 텍스트</hp:t>
                <hp:pic id="pic2">
                  <hp:img binaryItemIDRef="image2.png"/>
                </hp:pic>
              </hp:run>
            </hp:p>
          </hp:subList>
        </hp:tc>
      </hp:tr>
      <hp:tr>
        <!-- 셀 3: 다중 그림 (건너뜀) -->
        <hp:tc borderFillIDRef="2">
          <hp:subList>
            <hp:p id="103">
              <hp:run>
                <hp:pic id="pic3">
                  <hp:img binaryItemIDRef="image3.png"/>
                </hp:pic>
                <hp:pic id="pic4">
                  <hp:img binaryItemIDRef="image4.png"/>
                </hp:pic>
              </hp:run>
            </hp:p>
          </hp:subList>
        </hp:tc>
        <!-- 셀 4: 텍스트만 있음 (건너뜀) -->
        <hp:tc borderFillIDRef="2">
          <hp:subList>
            <hp:p id="104">
              <hp:run>
                <hp:t>순수 텍스트</hp:t>
              </hp:run>
            </hp:p>
          </hp:subList>
        </hp:tc>
      </hp:tr>
    </hp:tbl>
  </hp:p>
  <!-- 표 밖의 단독 그림 (표 밖이므로 건너뜀) -->
  <hp:p id="2">
    <hp:run>
      <hp:pic id="pic_outside">
        <hp:img binaryItemIDRef="outside.png"/>
      </hp:pic>
    </hp:run>
  </hp:p>
</hp:sec>
"""

    def test_convert_single_cell_image(self):
        header_xml = self._create_mock_header()
        section_xml = self._create_mock_section()

        header_root = ET.fromstring(header_xml.encode("utf-8"))
        section_root = ET.fromstring(section_xml.encode("utf-8"))

        count = convert_cell_images_to_background(section_root, header_root)
        self.assertEqual(count, 1)

        # 셀 1은 borderFillIDRef가 새로 생성된 ID로 변경되어야 함
        tc1 = section_root.find(f".//{HP}tbl/{HP}tr[1]/{HP}tc[1]")
        self.assertIsNotNone(tc1)
        new_bf_id = tc1.get("borderFillIDRef")
        self.assertNotEqual(new_bf_id, "1")

        # 셀 1 안의 원래 hp:pic은 삭제되어야 함
        pics_in_tc1 = tc1.findall(f".//{HP}pic")
        self.assertEqual(len(pics_in_tc1), 0)

        # header에 새 borderFill이 추가되었고 mode="TOTAL" imgBrush가 존재하는지 확인
        new_bf = None
        for bf in header_root.findall(f".//{HH}borderFill"):
            if bf.get("id") == new_bf_id:
                new_bf = bf
                break
        self.assertIsNotNone(new_bf)

        img_brush = new_bf.find(f".//{HC}imgBrush")
        self.assertIsNotNone(img_brush)
        self.assertEqual(img_brush.get("mode"), "TOTAL")

        img_node = img_brush.find(f"{HC}img")
        self.assertIsNotNone(img_node)
        self.assertEqual(img_node.get("binaryItemIDRef"), "image1.png")

        # 셀 2(글자+그림)는 변경되지 않고 pic 유지 확인
        tc2 = section_root.find(f".//{HP}tbl/{HP}tr[1]/{HP}tc[2]")
        self.assertEqual(len(tc2.findall(f".//{HP}pic")), 1)

        # 셀 3(다중 그림)도 변경되지 않고 pic 2개 유지 확인
        tc3 = section_root.find(f".//{HP}tbl/{HP}tr[2]/{HP}tc[1]")
        self.assertEqual(len(tc3.findall(f".//{HP}pic")), 2)

        # 표 밖의 그림도 그대로 유지 확인
        outside_p = section_root.find(f"./{HP}p[@id='2']")
        self.assertEqual(len(outside_p.findall(f".//{HP}pic")), 1)

    def test_idempotence(self):
        header_xml = self._create_mock_header()
        section_xml = self._create_mock_section()

        header_root = ET.fromstring(header_xml.encode("utf-8"))
        section_root = ET.fromstring(section_xml.encode("utf-8"))

        count1 = convert_cell_images_to_background(section_root, header_root)
        self.assertEqual(count1, 1)

        # 두 번째 실행 시 더 이상 변환할 이미지가 없으므로 0 반환
        count2 = convert_cell_images_to_background(section_root, header_root)
        self.assertEqual(count2, 0)


if __name__ == "__main__":
    unittest.main()
