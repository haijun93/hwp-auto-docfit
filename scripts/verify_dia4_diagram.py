"""Generate and visually verify the disposable DIA5 diagram through Hancom Hangul."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
REPORTS = Path(r"C:\HWP_AUTODOCFIT\v1803\reports")
HWPX = REPORTS / "DIA5.hwpx"
PDF = REPORTS / "DIA5.pdf"
PNG = REPORTS / "DIA5.png"


def _child() -> int:
    import win32com.client
    from pypdfium2 import PdfDocument
    from defusedxml import ElementTree as ET

    sys.path.insert(0, str(ROOT))
    from docfit_core.hwpx.canvas_package_adapter import merge_canvas_block_into_hwpx
    from docfit_core.save_guard import com_test_lock
    from scripts.verify_table_catalog_paste import _register

    payload = {
        "nodes": [
            {"id": "start", "type": "ellipse", "position": {"x": 50, "y": 55}, "width": 100, "height": 60, "data": {"label": "START"}},
            {"id": "process", "type": "rect", "position": {"x": 220, "y": 55}, "width": 120, "height": 60, "data": {"label": "PROCESS"}},
            {"id": "end", "type": "diamond", "position": {"x": 410, "y": 40}, "width": 100, "height": 90, "data": {"label": "END"}},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "process", "markerEnd": {"type": "arrow"}},
            {"id": "e2", "source": "process", "target": "end", "markerEnd": {"type": "arrow"}},
        ],
    }
    fixture = ROOT / "tests" / "fixtures" / "hwp_shapes_text_sample.hwpx"
    HWPX.write_bytes(merge_canvas_block_into_hwpx(fixture, {"kind": "diagram", "source": payload, "replace_sample_shapes": True}))

    with com_test_lock("dia4", "open generated diagram and render PDF", timeout_sec=180):
        app = win32com.client.DispatchEx("HwpFrame.HwpObject")
        try:
            _register(app)
            opened = bool(app.Open(str(HWPX), "HWPX", ""))
            print(f"open={opened}")
            if not opened:
                return 2
            saved = bool(app.SaveAs(str(PDF), "PDF", ""))
            print(f"pdf_saved={saved}")
            if not saved:
                return 3
        finally:
            try:
                app.Quit()
            except Exception:
                pass

    hp = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
    with ZipFile(HWPX) as package:
        section = ET.fromstring(package.read("Contents/section0.xml"))
    diagram = section[-1]
    counts = {name: sum(1 for node in section.iter() if node.tag == hp + name)
              for name in ("ellipse", "rect", "polygon", "connectLine")}
    counts = {name: sum(1 for node in diagram.iter() if node.tag == hp + name)
              for name in counts}
    print(f"objects={counts}")

    document = PdfDocument(str(PDF))
    if len(document) != 1:
        print(f"pages={len(document)}")
        return 4
    from PIL import ImageChops
    import math

    image = document[0].render(scale=2).to_pil().convert("L")
    image.save(PNG)
    print(f"pages={len(document)} image={PNG}")
    shapes = {node.get("id"): node for node in diagram.iter() if node.tag in (hp+"ellipse", hp+"rect", hp+"polygon")}
    connectors = [node for node in diagram.iter() if node.tag == hp+"connectLine"]
    xoff=lambda n:int(n.find(hp+"pos").get("horzOffset"))/50
    yoff=lambda n:int(n.find(hp+"pos").get("vertOffset"))/50
    width=lambda n:int(n.find(hp+"orgSz").get("width"))/50
    height=lambda n:int(n.find(hp+"orgSz").get("height"))/50
    dark=lambda x,y: image.getpixel((int(round(x)),int(round(y))))<200
    def ratio(a,b,count=100):
        return sum(dark(a[0]+(b[0]-a[0])*i/(count-1),a[1]+(b[1]-a[1])*i/(count-1)) for i in range(count))/count

    diamond=next(n for n in shapes.values() if n.tag==hp+"polygon")
    dx,dy,dw,dh=xoff(diamond),yoff(diamond),width(diamond),height(diamond)
    sides=[((dx+dw/2,dy+1),(dx+dw-1,dy+dh/2)),((dx+dw-1,dy+dh/2),(dx+dw/2,dy+dh-1)),((dx+dw/2,dy+dh-1),(dx+1,dy+dh/2)),((dx+1,dy+dh/2),(dx+dw/2,dy+1))]
    side_ratios=[]
    for a,b in sides:
        samples=100; hits=0
        for i in range(samples):
            x=a[0]+(b[0]-a[0])*i/(samples-1); y=a[1]+(b[1]-a[1])*i/(samples-1)
            hits+=any(dark(x+ox,y+oy) for ox in (-2,-1,0,1,2) for oy in (-2,-1,0,1,2))
        side_ratios.append(hits/samples)
    print(f"diamond_side_dark_ratios={[round(v,3) for v in side_ratios]}")
    connector_ratios=[]; arrow_pixels=[]
    for edge in connectors:
        pos,start,end=edge.find(hp+"pos"),edge.find(hp+"startPt"),edge.find(hp+"endPt")
        ax=int(pos.get("horzOffset"))/50; ay=int(pos.get("vertOffset"))/50
        bx=ax+int(end.get("x"))/50; by=ay+int(end.get("y"))/50
        if math.hypot(bx-ax,by-ay)<5: continue
        length=math.hypot(bx-ax,by-ay); fraction=min(8/length,.18)
        tipx,tipy=bx-(bx-ax)*fraction,by-(by-ay)*fraction
        connector_ratios.append(sum(any(dark(ax+(tipx-ax)*i/99+ox,ay+(tipy-ay)*i/99+oy)
                                        for ox in (-2,-1,0,1,2) for oy in (-2,-1,0,1,2))
                                    for i in range(100))/100)
        arrow_pixels.append(sum(dark(bx+ox,by+oy) for ox in range(-12,13) for oy in range(-12,13) if ox*ox+oy*oy<=144))
    print(f"connector_path_dark_ratios={[round(v,3) for v in connector_ratios]}")
    print(f"arrowhead_dark_pixels={arrow_pixels}")

    text_errors=[]
    for node in shapes.values():
        draw=node.find(hp+"drawText")
        if draw is None or not "".join(draw.itertext()).strip(): continue
        x0,y0,w0,h0=xoff(node),yoff(node),width(node),height(node)
        crop=image.crop((int(x0+3),int(y0+3),int(x0+w0-3),int(y0+h0-3)))
        pix=crop.load(); seen=set(); xx_list=[]
        for yy in range(crop.height):
            for xx in range(crop.width):
                if pix[xx,yy]>=200 or (xx,yy) in seen: continue
                stack=[(xx,yy)]; seen.add((xx,yy)); comp=[]
                while stack:
                    cx,cy=stack.pop(); comp.append((cx,cy))
                    for nx,ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
                        if 0<=nx<crop.width and 0<=ny<crop.height and (nx,ny) not in seen and pix[nx,ny]<200:
                            seen.add((nx,ny)); stack.append((nx,ny))
                if len(comp)>=2: xx_list.extend(x for x,y in comp)
        center=(min(xx_list)+max(xx_list))/2+x0+3 if xx_list else float("inf")
        if xx_list: text_errors.append(abs(center-(x0+w0/2))/w0)
    print(f"text_horizontal_center_error_width_ratio={[round(v,3) for v in text_errors]}")

    allowed=ImageChops.difference(image,image).convert("1"); mask=allowed.load()
    for node in shapes.values():
        x0,y0,w0,h0=xoff(node),yoff(node),width(node),height(node)
        for yy in range(max(0,int(y0)-15),min(image.height,int(y0+h0)+16)):
            for xx in range(max(0,int(x0)-15),min(image.width,int(x0+w0)+16)): mask[xx,yy]=1
    for edge in connectors:
        pos,start,end=edge.find(hp+"pos"),edge.find(hp+"startPt"),edge.find(hp+"endPt")
        ax=int(pos.get("horzOffset"))/50; ay=int(pos.get("vertOffset"))/50
        bx=ax+int(end.get("x"))/50; by=ay+int(end.get("y"))/50
        for i in range(101):
            x=ax+(bx-ax)*i/100; y=ay+(by-ay)*i/100
            for oy in range(-2,3):
                for ox in range(-2,3):
                    if 0<=int(x+ox)<image.width and 0<=int(y+oy)<image.height: mask[int(x+ox),int(y+oy)]=1
    outside_dark=sum(1 for y in range(image.height) for x in range(image.width) if dark(x,y) and not mask[x,y])
    print(f"outside_dark_pixels={outside_dark}")
    passed=(counts=={"ellipse":1,"rect":1,"polygon":1,"connectLine":2} and all(v>=.80 for v in side_ratios)
            and len(connector_ratios)==2 and all(v>=.80 for v in connector_ratios)
            and len(arrow_pixels)==2 and all(v>=3 for v in arrow_pixels)
            and len(text_errors)==3 and all(v<=.10 for v in text_errors) and outside_dark<=20)
    return 0 if passed else 5


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    if "--child" in sys.argv:
        return _child()
    result = subprocess.run(
        [r"C:\HWP_AUTODOCFIT\venv315\Scripts\python.exe",
         str(Path(__file__).resolve()), "--child"],
        cwd=ROOT,
        check=False,
        timeout=180,
    )
    if result.returncode in (-9, 137):
        print(f"child_terminated={result.returncode}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

