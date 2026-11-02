"""Generate and verify the disposable DIA4 diagram through Hancom Hangul."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
REPORTS = Path(r"C:\HWP_AUTODOCFIT\reports")
HWPX = REPORTS / "DIA4.hwpx"
PDF = REPORTS / "DIA4.pdf"
PNG = REPORTS / "DIA4.png"


def _child() -> int:
    import win32com.client
    from pypdfium2 import PdfDocument
    from defusedxml import ElementTree as ET

    sys.path.insert(0, str(ROOT))
    from docfit_core.save_guard import com_test_lock
    from scripts.verify_table_catalog_paste import _register

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
    image = document[0].render(scale=1).to_pil()
    grayscale = image.convert("L")
    dark = sum(1 for pixel in grayscale.getdata() if pixel < 200)
    image.save(PNG)
    print(f"pages={len(document)} dark_pixels={dark} image={PNG}")
    expected = {"ellipse": 1, "rect": 1, "polygon": 1, "connectLine": 2}
    return 0 if dark > 100 and counts == expected else 5


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
