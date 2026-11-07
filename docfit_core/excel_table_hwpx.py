"""엑셀 표 모델을 표그림판 HWPX 생성기로 한/글 표로 만든다. 표 폭은 본문 폭에 맞춘다."""
from __future__ import annotations

import zipfile

from defusedxml import ElementTree as ET

from . import table_sketch
from .hwpx import open_zip_safely

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
BODY_WIDTH_MM = 170.0
ROW_HEIGHT_MM = 7.0
MIN_COLUMN_MM = 8.0


def _column_widths(model):
    """엑셀 열 폭 비율을 본문 폭에 맞춘다(너무 좁은 열은 최소 폭 보장)."""
    raw = [w if w > 0 else 48.0 for w in model.get("widths") or [0.0] * model["col_count"]]
    total = sum(raw)
    widths = [max(MIN_COLUMN_MM, BODY_WIDTH_MM * w / total) for w in raw]
    overflow = sum(widths) - BODY_WIDTH_MM
    free = sum(w - MIN_COLUMN_MM for w in widths)
    if overflow > 0:
        if free > overflow:
            widths = [w - (w - MIN_COLUMN_MM) * overflow / free for w in widths]
        else:
            # 최소 폭의 합계조차 본문보다 크면 모든 열을 같은 폭으로 축소한다.
            widths = [BODY_WIDTH_MM / len(widths)] * len(widths)
    return widths


def _sketch(model):
    """격자 한 칸을 엑셀 칸 하나로 삼는다. 병합 칸 안쪽에는 선을 긋지 않아 한 칸이 된다."""
    lines, texts, fills = {}, [], []
    for row in model["rows"]:
        for cell in row:
            x1, y1 = cell["col"], cell["row"]
            x2, y2 = x1 + cell["colspan"], y1 + cell["rowspan"]
            for edge in ((x1, y1, x2, y1), (x1, y2, x2, y2), (x1, y1, x1, y2), (x2, y1, x2, y2)):
                lines[edge] = dict(zip(("x1", "y1", "x2", "y2"), edge))
            if cell["text"]:
                texts.append(dict(x=x1, y=y1, text=cell["text"], bold=bool(cell["bold"]), align=cell["align"], color=cell.get("color") or "#000000"))
            if cell.get("fill"):
                fills.append(dict(x1=x1, y1=y1, x2=x2, y2=y2, color=cell["fill"]))
    return dict(grid=dict(cols=model["col_count"], rows=model["row_count"], cell_mm=5.0),
                lines=list(lines.values()), texts=texts, fills=fills)


def to_hwpx(model, path):
    if model["col_count"] > 200 or model["row_count"] > 200:
        raise ValueError("표는 가로·세로 200칸까지 옮길 수 있습니다.")
    sketch = _sketch(model)
    layout = table_sketch.preview(sketch)
    document = table_sketch.to_hwpx(sketch, path)
    unit = table_sketch.UNIT_MM
    x_edges = [0]
    for width in _column_widths(model):
        x_edges.append(x_edges[-1] + round(width * unit))
    row_height = round(ROW_HEIGHT_MM * unit)

    with open_zip_safely(document) as package:
        infos = [(info, package.read(info.filename)) for info in package.infolist()]
    section_name = next(info.filename for info, _ in infos if info.filename.endswith("section0.xml"))
    root = ET.fromstring(next(data for info, data in infos if info.filename == section_name))
    table = root.find(f".//{HP}tbl")
    if table is None:
        raise ValueError("표 HWPX를 만들지 못했습니다.")
    # 생성기의 칸 번호는 실제 쓰인 선 위치 기준이라 격자 좌표로 되돌려 폭·높이를 준다.
    xs, ys = layout["x_coords"], layout["y_coords"]
    table.find(f"{HP}sz").attrib.update(width=str(x_edges[xs[-1]] - x_edges[xs[0]]),
                                        height=str(row_height * (ys[-1] - ys[0])))
    for cell in table.iter(f"{HP}tc"):
        addr, span, size = cell.find(f"{HP}cellAddr"), cell.find(f"{HP}cellSpan"), cell.find(f"{HP}cellSz")
        col, row = int(addr.get("colAddr")), int(addr.get("rowAddr"))
        col_end, row_end = col + int(span.get("colSpan", "1")), row + int(span.get("rowSpan", "1"))
        size.attrib.update(width=str(x_edges[xs[col_end]] - x_edges[xs[col]]),
                           height=str(row_height * (ys[row_end] - ys[row])))
    section = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(document, "w", zipfile.ZIP_DEFLATED) as package:
        for info, data in infos:
            package.writestr(info, section if info.filename == section_name else data)
    return document
