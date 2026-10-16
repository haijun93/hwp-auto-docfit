"""Exercise the packaged engine offline, before and after frozen EXE installation."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def verify_ocr(runtime):
    from PIL import Image, ImageDraw, ImageFont
    from docfit_core.hwpx import inspect_hwpx
    from docfit_core.network_policy import offline_environment
    runtime = Path(runtime).resolve()
    node = runtime / "node/node.exe"
    cli = runtime / "app/node_modules/kordoc/dist/cli.js"
    env = offline_environment(dict(os.environ))
    env["KORDOC_MODEL_CACHE"] = str(runtime / "models")

    def run(arguments):
        result = subprocess.run([str(node), str(cli), *map(str, arguments)],
                                env=env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=180)
        if result.returncode:
            raise RuntimeError(f"kordoc OCR command failed ({result.returncode}): "
                               f"{result.stderr[-6000:]} {result.stdout[-2000:]}")

    with tempfile.TemporaryDirectory(prefix="docfit_ocr_gate_") as folder:
        work = Path(folder)
        with Image.new("RGB", (1200, 300), "white") as image:
            font = ImageFont.truetype(str(ROOT / "flutter_ui/assets/NotoSansKR.ttf"), 48)
            ImageDraw.Draw(image).text((40, 40), "공원 안내판 철거 계획", fill="black",
                                       font=font, stroke_width=1, stroke_fill="black")
            scan = work / "scan.png"
            parsed = work / "scan.md"
            image.save(scan)
            run([scan, "--ocr", "--format", "markdown", "-o", parsed, "--silent"])
            recognized = parsed.read_text(encoding="utf-8")
            if "공원" not in recognized or "계획" not in recognized:
                raise RuntimeError(f"Korean image OCR did not recognize fixture: {recognized}")
            output = work / "ocr.hwpx"
            run(["generate", parsed, "-o", output, "--preset", "report", "--silent"])
            if "공원" not in "\n".join(block.text for block in inspect_hwpx(output).blocks):
                raise RuntimeError("OCR text was lost during HWPX generation")
            pdf = work / "scan.pdf"
            pdf_md = work / "scan-pdf.md"
            image.save(pdf, "PDF", resolution=150)
            run([pdf, "--ocr", "--format", "markdown", "-o", pdf_md, "--silent"])
            pdf_text = pdf_md.read_text(encoding="utf-8")
            if "공원" not in pdf_text or "계획" not in pdf_text:
                raise RuntimeError(f"Scanned PDF OCR did not recognize fixture: {pdf_text}")
    return {"ok": True, "recognized": recognized.strip(),
            "model": "PP-OCRv5 Korean", "scanned_pdf": True}


if __name__ == "__main__":
    try:
        print(json.dumps(verify_ocr(sys.argv[1]), ensure_ascii=False))
    except Exception:
        message = traceback.format_exc().replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=Offline OCR runtime gate::{message}")
        raise
