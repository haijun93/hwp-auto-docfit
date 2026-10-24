"""다이어그램(흐름도) -> 한/글 도형 HWPX 변환 단위 시험."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from docfit_core import diagram_shapes

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"
HC = "{http://www.hancom.co.kr/hwpml/2011/core}"


class TestDiagramShapes(unittest.TestCase):
    def test_diagram_to_hwpx_structure(self):
        snapshot = {
            "format": "docfit-flow",
            "version": 1,
            "nodes": [
                {
                    "id": "node1",
                    "type": "rect",
                    "position": {"x": 50, "y": 50},
                    "data": {"label": "시작 단계", "width": 120, "height": 60},
                    "style": {"background": "#D9E1F2", "borderColor": "#002060", "borderRadius": 10},
                },
                {
                    "id": "node2",
                    "type": "diamond",
                    "position": {"x": 250, "y": 50},
                    "data": {"label": "조건 판정", "width": 100, "height": 60},
                    "style": {"background": "#FFF2CC", "borderColor": "#D6B656"},
                },
                {
                    "id": "node3",
                    "type": "circle",
                    "position": {"x": 450, "y": 50},
                    "data": {"label": "종료", "width": 80, "height": 60},
                    "style": {"background": "#E2EFDA", "borderColor": "#385723"},
                },
            ],
            "edges": [
                {
                    "id": "edge1",
                    "source": "node1",
                    "target": "node2",
                    "markerEnd": {"type": "arrow"},
                },
                {
                    "id": "edge2",
                    "source": "node2",
                    "target": "node3",
                    "markerEnd": {"type": "arrow"},
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "shapes_test.hwpx"
            res_path = diagram_shapes.diagram_to_hwpx(snapshot, out_path)
            self.assertTrue(res_path.is_file())

            # 생성된 HWPX 문서의 section0.xml 검증
            with zipfile.ZipFile(res_path, "r") as archive:
                self.assertIn("Contents/section0.xml", archive.namelist())
                self.assertIn("Contents/header.xml", archive.namelist())

                section_root = ET.fromstring(archive.read("Contents/section0.xml"))

                # hp:container 확인
                container = section_root.find(f".//{HP}container")
                self.assertIsNotNone(container, "hp:container 요소가 생성되어야 합니다.")
                self.assertEqual(container.get("groupLevel"), "0")

                # 사각형, 마름모(다각형), 타원 확인
                rects = container.findall(f"./{HP}rect")
                polygons = container.findall(f"./{HP}polygon")
                ellipses = container.findall(f"./{HP}ellipse")
                lines = container.findall(f"./{HP}line")

                self.assertEqual(len(rects), 1)
                self.assertEqual(len(polygons), 1)
                self.assertEqual(len(ellipses), 1)
                self.assertEqual(len(lines), 2)

                # 사각형 라운드 속성 확인
                self.assertEqual(rects[0].get("ratio"), "20")

                # 글자 확인 (drawText)
                texts = [t.text for t in container.iter(f"{HP}t")]
                self.assertIn("시작 단계", texts)
                self.assertIn("조건 판정", texts)
                self.assertIn("종료", texts)

                # 채우기 색상 확인
                brushes = container.findall(f".//{HC}winBrush")
                face_colors = [b.get("faceColor") for b in brushes]
                self.assertIn("#D9E1F2", face_colors)
                self.assertIn("#FFF2CC", face_colors)
                self.assertIn("#E2EFDA", face_colors)

                # 화살표 스타일 확인
                line_shapes = container.findall(f"./{HP}line/{HP}lineShape")
                for ls in line_shapes:
                    self.assertEqual(ls.get("headStyle"), "ARROW")

    def test_invalid_snapshot_handling(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "empty.hwpx"
            with self.assertRaises(ValueError):
                diagram_shapes.diagram_to_hwpx({"nodes": []}, out_path)


if __name__ == "__main__":
    unittest.main()
