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


NS = (f'xmlns:hp="{HP[1:-1]}" xmlns:hh="{HH[1:-1]}" xmlns:hc="{HC[1:-1]}" '
      'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"')
PNG = b"\x89PNG\r\n\x1a\n" + bytes(range(64))


def _pic(name):
    return (f'<hp:pic id="{name}"><hp:sz width="100" height="100"/>'
            f'<hc:img binaryItemIDRef="{name}" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/></hp:pic>')


def _cell(inner, bf="3", extra=""):
    return (f'<hp:tc name="" header="0" borderFillIDRef="{bf}"><hp:subList><hp:p id="0">'
            f'<hp:run charPrIDRef="0">{inner}</hp:run></hp:p></hp:subList>'
            f'<hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan {extra or 'colSpan="1" rowSpan="1"'}/></hp:tc>')


HEADER = (f'<?xml version="1.0" encoding="UTF-8"?><hh:head {NS}><hh:refList>'
          '<hh:borderFills itemCnt="3">'
          '<hh:borderFill id="1"><hh:leftBorder type="NONE"/></hh:borderFill>'
          '<hh:borderFill id="2"><hh:leftBorder type="NONE"/></hh:borderFill>'
          '<hh:borderFill id="3" threeD="0"><hh:leftBorder type="SOLID" width="0.4 mm" color="#FF0000"/>'
          '<hc:fillBrush><hc:winBrush faceColor="#FFFF00" hatchColor="#000000" alpha="0"/></hc:fillBrush>'
          '</hh:borderFill></hh:borderFills></hh:refList></hh:head>')

SECTION = (f'<?xml version="1.0" encoding="UTF-8"?><hs:sec {NS}><hp:p id="1"><hp:run><hp:tbl rowCnt="3" colCnt="2">'
           '<hp:tr>' + _cell(_pic("image1")) + _cell(_pic("image2") + "<hp:t>글</hp:t>") + '</hp:tr>'
           '<hp:tr>' + _cell(_pic("image3") + _pic("image4")) + _cell("<hp:t>문자</hp:t>") + '</hp:tr>'
           '<hp:tr>' + _cell(_pic("image5"), bf="1", extra='colSpan="2" rowSpan="1"') + _cell("") + '</hp:tr>'
           '</hp:tbl></hp:run></hp:p>'
           '<hp:p id="2"><hp:run>' + _pic("outside") + '</hp:run></hp:p></hs:sec>')


def _make_hwpx(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/hwp+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("Contents/header.xml", HEADER)
        z.writestr("Contents/section0.xml", SECTION)
        z.writestr("Contents/content.hpf", "<opf/>")
        for n in range(1, 6):
            z.writestr(f"BinData/image{n}.png", PNG + bytes([n]))


class TestCellImageBgFile(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.src = Path(self.tmp.name) / "in.hwpx"
        self.dst = Path(self.tmp.name) / "out.hwpx"
        _make_hwpx(self.src)

    def _read(self, path, name):
        with zipfile.ZipFile(path) as z:
            return z.read(name)

    def test_file_conversion_structure(self):
        before = self.src.read_bytes()
        count = cell_image_bg.convert_cell_images_to_bg_hwpx(self.src, self.dst)
        self.assertEqual(count, 2)  # 셀1 + 병합 셀5
        self.assertEqual(self.src.read_bytes(), before)  # 원본 불변

        sec_bytes = self._read(self.dst, "Contents/section0.xml")
        head_bytes = self._read(self.dst, "Contents/header.xml")
        self.assertIn(b"<hp:tbl", sec_bytes)  # 접두사 보존
        self.assertNotIn(b"ns0:", sec_bytes + head_bytes)
        sec, head = ET.fromstring(sec_bytes), ET.fromstring(head_bytes)

        tcs = list(sec.iter(HP + "tc"))
        self.assertEqual([len(list(t.iter(HP + "pic"))) for t in tcs], [0, 1, 2, 0, 0, 0])
        self.assertEqual(len(list(sec.iter(HP + "pic"))), 4)  # 셀2,셀3(2),표 밖
        # 다른 셀 속성 불변
        self.assertEqual([t.get("borderFillIDRef") for t in tcs[1:4]], ["3", "3", "3"])
        merged = tcs[4]
        self.assertEqual(merged.find(f".//{HP}cellSpan").get("colSpan"), "2")

        bfs = {b.get("id"): b for b in head.iter(HH + "borderFill")}
        self.assertEqual(len(bfs), 5)
        self.assertEqual(head.find(f".//{HH}borderFills").get("itemCnt"), "5")
        for tc, ref, base in ((tcs[0], "image1", "3"), (merged, "image5", "1")):
            bf = bfs[tc.get("borderFillIDRef")]
            self.assertNotIn(bf.get("id"), ("1", "2", "3"))
            brush = bf.find(f"{HC}fillBrush/{HC}imgBrush")
            self.assertEqual(brush.get("mode"), "TOTAL")
            self.assertEqual(brush.find(f"{HC}img").get("binaryItemIDRef"), ref)
            self.assertIsNone(bf.find(f"{HC}fillBrush/{HC}winBrush"))
            # 테두리 보존
            self.assertEqual(bf.find(f"{HH}leftBorder").get("type"), bfs[base].find(f"{HH}leftBorder").get("type"))
        self.assertEqual(bfs[tcs[0].get("borderFillIDRef")].find(f"{HH}leftBorder").get("color"), "#FF0000")
        # 기존 borderFill 불변
        self.assertIsNotNone(bfs["3"].find(f"{HC}fillBrush/{HC}winBrush"))

        # BinData·기타 항목 바이트 동일
        with zipfile.ZipFile(self.src) as a, zipfile.ZipFile(self.dst) as b:
            self.assertEqual(a.namelist(), b.namelist())
            for n in a.namelist():
                if n not in ("Contents/header.xml", "Contents/section0.xml"):
                    self.assertEqual(a.read(n), b.read(n), n)

    def test_file_idempotent_and_no_target(self):
        cell_image_bg.convert_cell_images_to_bg_hwpx(self.src, self.dst)
        second = Path(self.tmp.name) / "again.hwpx"
        self.assertEqual(cell_image_bg.convert_cell_images_to_bg_hwpx(self.dst, second), 0)
        self.assertEqual(self.dst.read_bytes(), second.read_bytes())

    def test_no_image_cells_copies_unchanged(self):
        plain = Path(self.tmp.name) / "plain.hwpx"
        with zipfile.ZipFile(plain, "w") as z:
            z.writestr("Contents/header.xml", HEADER)
            z.writestr("Contents/section0.xml", SECTION.replace("<hp:pic", "<hp:x").replace("</hp:pic", "</hp:x"))
        out = Path(self.tmp.name) / "plain_out.hwpx"
        self.assertEqual(cell_image_bg.convert_cell_images_to_bg_hwpx(plain, out), 0)
        self.assertEqual(plain.read_bytes(), out.read_bytes())

    def test_rejects_non_hwpx(self):
        bad = Path(self.tmp.name) / "x.txt"
        bad.write_text("x")
        with self.assertRaises(ValueError):
            cell_image_bg.convert_cell_images_to_bg_hwpx(bad)


if __name__ == "__main__":
    unittest.main()
