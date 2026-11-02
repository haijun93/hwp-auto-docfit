"""한/글 2020에서 표그림판 화살표를 PDF 픽셀로 검증한다."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import tempfile
import time
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from defusedxml import ElementTree as ET
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
import win32com.client

from docfit_core import table_sketch as ts
from docfit_core.save_guard import com_test_lock

REPORT = ROOT / "reports" / "V224-SKETCH2.png"
COLORS = {"right": "#DC2626", "left": "#2563EB", "down": "#16A34A", "up": "#C026D3"}


def fixture():
    return {
        "grid": {"cols": 36, "rows": 28, "cell_mm": 5.0},
        "lines": [
            {"x1": 1, "y1": 1, "x2": 35, "y2": 1}, {"x1": 1, "y1": 27, "x2": 35, "y2": 27},
            {"x1": 1, "y1": 1, "x2": 1, "y2": 27}, {"x1": 35, "y1": 1, "x2": 35, "y2": 27},
            {"x1": 18, "y1": 1, "x2": 18, "y2": 27}, {"x1": 1, "y1": 14, "x2": 35, "y2": 14},
        ],
        "texts": [],
        "fills": [{"x1": 2, "y1": 2, "x2": 17, "y2": 13, "color": "#DBEAFE"}],
        "arrows": [
            {"x1": 4, "y1": 5, "x2": 14, "y2": 5, "width": "thick", "style": "solid", "color": COLORS["right"]},
            {"x1": 32, "y1": 8, "x2": 22, "y2": 8, "width": "thick", "style": "solid", "color": COLORS["left"]},
            {"x1": 6, "y1": 17, "x2": 6, "y2": 25, "width": "thick", "style": "solid", "color": COLORS["down"]},
            {"x1": 12, "y1": 25, "x2": 12, "y2": 17, "width": "thick", "style": "solid", "color": COLORS["up"]},
        ],
    }


def pixel_report(image: Image.Image):
    """표 테두리를 기준으로 색별 화살표의 실제 위치를 격자 칸으로 환산해 지정 좌표와 비교한다."""
    rgb = image.convert("RGB")
    width, height = rgb.size
    pix = rgb.load()
    dark = lambda c: sum(c) < 150
    ys = [y for y in range(height) if sum(dark(pix[x, y]) for x in range(width)) > width * .3]
    xs = [x for x in range(width) if sum(dark(pix[x, y]) for y in range(height)) > height * .2]
    if len(xs) < 2 or len(ys) < 2:
        raise RuntimeError("표 테두리 픽셀을 찾지 못했습니다.")
    left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
    data = fixture()
    report = {}
    for name, arrow in zip(COLORS, data["arrows"]):
        target = tuple(int(COLORS[name][k:k + 2], 16) for k in (1, 3, 5))
        points = [(x, y) for x in range(width) for y in range(height)
                  if sum(abs(pix[x, y][k] - target[k]) for k in range(3)) < 60]
        if not points:
            report[name] = {"합격": False, "오차": None}
            continue
        grid_x = lambda v: 1 + (v - left) / (right - left) * 34
        grid_y = lambda v: 1 + (v - top) / (bottom - top) * 26
        box = (grid_x(min(p[0] for p in points)), grid_x(max(p[0] for p in points)),
               grid_y(min(p[1] for p in points)), grid_y(max(p[1] for p in points)))
        want = (min(arrow["x1"], arrow["x2"]), max(arrow["x1"], arrow["x2"]),
                min(arrow["y1"], arrow["y2"]), max(arrow["y1"], arrow["y2"]))
        error = max(abs(a - b) for a, b in zip(box, want))
        report[name] = {"합격": error <= 0.6, "오차": round(error, 2)}
    return report


def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="v224-sketch2-") as tmp:
        source = Path(tmp) / "arrows.hwpx"
        pdf_path = Path(tmp) / "arrows.pdf"
        ts.to_hwpx(fixture(), source)
        with com_test_lock("Codex", "V224-SKETCH2 화살표 픽셀 검증"):
            app = win32com.client.DispatchEx("HWPFrame.HwpObject")
            try:
                app.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
                if not app.Open(str(source), "HWPX", "forceopen:true"):
                    raise RuntimeError("한/글에서 검증 HWPX를 열지 못했습니다.")
                app.SaveAs(str(pdf_path), "PDF", "")
                deadline = time.monotonic() + 30
                while not pdf_path.is_file() and time.monotonic() < deadline:
                    time.sleep(0.2)
                if not pdf_path.is_file():
                    raise RuntimeError("한/글 PDF 저장 결과가 없습니다.")
                pdf = pdfium.PdfDocument(str(pdf_path))
                if len(pdf) != 1:
                    raise RuntimeError(f"예상 페이지 1, 실제 {len(pdf)}")
                page=pdf[0]
                bitmap = page.render(scale=2.5)
                image = bitmap.to_pil().convert("RGB")
                page_count=len(pdf)
                measurements = pixel_report(image)
                draw = ImageDraw.Draw(image)
                summary = "  ".join(f"{k}: {v['오차']}" for k, v in measurements.items())
                draw.rectangle((0, 0, image.width, 36), fill="white")
                draw.text((10, 10), summary, fill="black")
                image.save(REPORT)
                bitmap.close(); page.close(); pdf.close()
                print(json.dumps({"판정": "합격" if all(v["합격"] for v in measurements.values()) else "불합격",
                                  "PDF페이지": page_count, "PNG": str(REPORT), "화살표": measurements}, ensure_ascii=False, indent=2))
                if not all(v["합격"] for v in measurements.values()):
                    raise SystemExit(1)
            finally:
                try:
                    app.Clear(1)
                except Exception:
                    pass
                try:
                    app.Quit()
                except Exception:
                    pass


if __name__ == "__main__":
    main()
