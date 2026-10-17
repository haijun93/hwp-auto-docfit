"""Compare every catalog template with its Hancom-native clipboard round trip.

This opt-in Windows test requires Hancom Hangul COM and pypdfium2. It only reads
the catalog and creates disposable files in the system temporary directory.
"""
from __future__ import annotations

import argparse
import json
import io
import math
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docfit_app.native_table_clipboard import copy_hwpx_document
from docfit_core.format_samples import APP_HOME, LEGACY_REGISTRY_VALUE, REGISTRY_VALUE
from docfit_core.table_catalog import _scan, default_catalog_path, export_template
from defusedxml import ElementTree as SafeET

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"


def _element_signature(element):
    return (
        element.tag.split("}")[-1],
        tuple(sorted((key, value) for key, value in element.attrib.items() if key != "id")),
        tuple(_element_signature(child) for child in list(element)),
        element.text or "",
    )


def _register(app):
    app.XHwpWindows.Item(0).Visible = False
    module = REGISTRY_VALUE if (APP_HOME / "dll" / "HwpAutoDocFitSecurity.dll").is_file() else LEGACY_REGISTRY_VALUE
    if not app.RegisterModule("FilePathCheckDLL", module):
        raise RuntimeError("한/글 보안 모듈 등록에 실패했습니다.")


def _convert_to_pdf(path, output, win32_client):
    app = win32_client.DispatchEx("HwpFrame.HwpObject")
    try:
        _register(app)
        if not app.Open(str(path), "HWPX", ""):
            raise RuntimeError(f"한/글 문서 열기 실패: {path.name}")
        if not app.SaveAs(str(output), "PDF", "") or not output.is_file():
            raise RuntimeError(f"PDF 변환 실패: {path.name}")
    finally:
        try:
            app.Quit()
        except Exception:
            pass


def _bake_picture_alpha(source, target, factor, rounding="nearest", mode="alpha"):
    """Diagnostic only: bake a factor into referenced PNG alpha for clipboard tests."""
    from PIL import Image

    with zipfile.ZipFile(source) as archive:
        root = SafeET.fromstring(archive.read("Contents/section0.xml"))
        factors = {}
        for picture in root.iter(HP + "pic"):
            image = next((node for node in picture.iter()
                          if node.tag.split("}")[-1] == "img"), None)
            if image is not None and image.get("binaryItemIDRef"):
                factors[image.get("binaryItemIDRef")] = factor
        with zipfile.ZipFile(target, "w") as output:
            for info in archive.infolist():
                data = archive.read(info.filename)
                for item_id, alpha_factor in factors.items():
                    if (info.filename.startswith("BinData/") and
                            Path(info.filename).stem == item_id):
                        image = Image.open(io.BytesIO(data)).convert("RGBA")
                        if mode == "rgb":
                            rgb = image.convert("RGB")
                            white = Image.new("RGB", rgb.size, "white")
                            rgb = Image.blend(rgb, white, 1.0 - alpha_factor)
                            image = Image.merge("RGBA", (*rgb.split(), image.getchannel("A")))
                        else:
                            if rounding == "floor":
                                convert_alpha = lambda value: math.floor(value * alpha_factor)
                            elif rounding == "ceil":
                                convert_alpha = lambda value: math.ceil(value * alpha_factor)
                            else:
                                convert_alpha = lambda value: round(value * alpha_factor)
                            alpha = image.getchannel("A").point(convert_alpha)
                            image.putalpha(alpha)
                        encoded = io.BytesIO()
                        image.save(encoded, format="PNG")
                        data = encoded.getvalue()
                        break
                output.writestr(info, data)


def _paste_in_new_document(output_hwpx, output_pdf, win32_client):
    app = win32_client.DispatchEx("HwpFrame.HwpObject")
    try:
        _register(app)
        if not app.HAction.Run("FileNew"):
            raise RuntimeError("한/글 새 문서 생성 실패")
        if not app.HAction.Run("Paste"):
            raise RuntimeError("한/글 새 문서 붙여넣기 실패")
        if not app.SaveAs(str(output_hwpx), "HWPX", "") or not output_hwpx.is_file():
            raise RuntimeError("붙여넣기 HWPX 저장 실패")
        if not app.SaveAs(str(output_pdf), "PDF", "") or not output_pdf.is_file():
            raise RuntimeError("붙여넣기 PDF 변환 실패")
    finally:
        try:
            app.Quit()
        except Exception:
            pass


def _render(pdf_path, pdfium):
    document = pdfium.PdfDocument(str(pdf_path))
    try:
        return [page.render(scale=1.5).to_pil().convert("RGB") for page in document]
    finally:
        document.close()


def _table_structure(path):
    """Return editable HWPX table geometry, not a flattened image signature."""
    with zipfile.ZipFile(path) as archive:
        sections = sorted(name for name in archive.namelist()
                          if name.startswith("Contents/section") and name.endswith(".xml"))
        tables = []
        for name in sections:
            root = SafeET.fromstring(archive.read(name))
            parents = {child: parent for parent in root.iter() for child in list(parent)}
            for table in root.iter(HP + "tbl"):
                ancestor = parents.get(table)
                nested = False
                while ancestor is not None:
                    if ancestor.tag == HP + "tbl":
                        nested = True
                        break
                    ancestor = parents.get(ancestor)
                if not nested:
                    tables.append(table)
        header = SafeET.fromstring(archive.read("Contents/header.xml"))
        border_fills = {
            node.get("id"): _element_signature(node)
            for node in header.iter(HH + "borderFill")
        }
    if len(tables) != 1:
        return {"table_count": len(tables), "editable": False}
    table = tables[0]
    rows = table.findall(HP + "tr")
    cells = table.findall(".//" + HP + "tc")
    geometry = []
    for cell in cells:
        span = cell.find(HP + "cellSpan")
        size = cell.find(HP + "cellSz")
        margin = cell.find(HP + "cellMargin")
        border_ref = cell.get("borderFillIDRef")
        geometry.append((
            tuple(sorted((key, value) for key, value in cell.attrib.items()
                         if key != "borderFillIDRef")),
            tuple(sorted(span.attrib.items())) if span is not None else (),
            tuple(sorted(size.attrib.items())) if size is not None else (),
            tuple(sorted(margin.attrib.items())) if margin is not None else (),
            border_fills.get(border_ref),
        ))
    return {
        "table_count": 1,
        "editable": bool(rows and cells),
        "row_count": len(rows),
        "cell_count": len(cells),
        "rowCnt": table.get("rowCnt"),
        "colCnt": table.get("colCnt"),
        "cell_geometry": geometry,
    }


def _compare(before, after):
    from PIL import ImageChops, ImageStat

    if len(before) != len(after):
        return {"equal": False, "reason": "page_count", "before": len(before), "after": len(after)}
    total_pixels = changed = 0
    absolute_error = 0.0
    for left, right in zip(before, after):
        if left.size != right.size:
            return {"equal": False, "reason": "page_size", "before": left.size, "after": right.size}
        diff = ImageChops.difference(left, right)
        total_pixels += left.width * left.height
        changed += sum(1 for pixel in diff.get_flattened_data() if max(pixel) > 0)
        absolute_error += sum(ImageStat.Stat(diff).mean) / 3 * left.width * left.height
    mae = absolute_error / total_pixels if total_pixels else 0.0
    return {"equal": changed == 0, "changed_pixels": changed,
            "pixel_count": total_pixels, "pixel_mae": round(mae, 6)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=default_catalog_path())
    parser.add_argument("--limit", type=int, default=0, help="0 runs all templates")
    parser.add_argument("--only", help="run one template id, e.g. 9:1")
    parser.add_argument("--bake-image-alpha", type=float,
                        help="diagnostic PNG alpha multiplier used only for clipboard copy")
    parser.add_argument("--alpha-rounding", choices=("floor", "nearest", "ceil"), default="nearest")
    parser.add_argument("--bake-image-mode", choices=("alpha", "rgb"), default="alpha")
    args = parser.parse_args()
    records = _scan(args.catalog)
    if args.only:
        records = [record for record in records if record["id"] == args.only]
        if not records:
            parser.error(f"template id not found: {args.only}")
    if args.limit:
        records = records[:args.limit]
    import pythoncom
    import win32com.client
    import pypdfium2

    results = []
    with tempfile.TemporaryDirectory(prefix="docfit-table-paste-") as temporary:
        folder = Path(temporary)
        pythoncom.CoInitialize()
        try:
            for index, record in enumerate(records, 1):
                stem = f"{record['id'].replace(':', '-')}-{index}"
                source_hwpx = folder / f"{stem}-source.hwpx"
                source_pdf = folder / f"{stem}-source.pdf"
                pasted_hwpx = folder / f"{stem}-pasted.hwpx"
                pasted_pdf = folder / f"{stem}-pasted.pdf"
                export_template(record["id"], source_hwpx, args.catalog)

                _convert_to_pdf(source_hwpx, source_pdf, win32com.client)

                copy_source = source_hwpx
                if args.bake_image_alpha is not None:
                    if not 0.0 <= args.bake_image_alpha <= 1.0:
                        parser.error("--bake-image-alpha must be between 0 and 1")
                    copy_source = folder / f"{stem}-copy-source.hwpx"
                    _bake_picture_alpha(source_hwpx, copy_source, args.bake_image_alpha,
                                        args.alpha_rounding, args.bake_image_mode)
                copied = copy_hwpx_document(copy_source)
                if copied.get("format") != "hancom-native-table":
                    raise RuntimeError(f"한/글 표 클립보드 형식 확인 실패: {record['id']}")
                pythoncom.CoInitialize()
                _paste_in_new_document(pasted_hwpx, pasted_pdf, win32com.client)

                comparison = _compare(_render(source_pdf, pypdfium2), _render(pasted_pdf, pypdfium2))
                source_structure = _table_structure(source_hwpx)
                pasted_structure = _table_structure(pasted_hwpx)
                native_equal = source_structure == pasted_structure
                result = {"id": record["id"], "name": record["name"], **comparison,
                          "native_table_editable": pasted_structure.get("editable", False),
                          "native_table_structure_equal": native_equal,
                          "rows": pasted_structure.get("row_count"),
                          "cells": pasted_structure.get("cell_count")}
                results.append(result)
                if not comparison["equal"] or not native_equal or not pasted_structure.get("editable"):
                    from PIL import ImageChops
                    before = _render(source_pdf, pypdfium2)[0]
                    after = _render(pasted_pdf, pypdfium2)[0]
                    diff_path = folder / f"{stem}-diff.png"
                    ImageChops.difference(before, after).save(diff_path)
                    evidence = Path(tempfile.mkdtemp(prefix="docfit-table-mismatch-"))
                    paths = {}
                    for artifact in (source_pdf, pasted_pdf, source_hwpx, pasted_hwpx, diff_path):
                        target = evidence / artifact.name
                        shutil.copy2(artifact, target)
                        paths[artifact.suffix + artifact.stem.split("-")[-1]] = str(target)
                    result["artifacts"] = {"directory": str(evidence), "files": paths}
                    print(json.dumps({"mismatch_artifacts": result["artifacts"]}, ensure_ascii=False), flush=True)
                print(json.dumps({"completed": index, "total": len(records), **result}, ensure_ascii=False), flush=True)
        finally:
            pythoncom.CoUninitialize()
    failed = [item for item in results if not item["equal"] or
              not item["native_table_structure_equal"] or not item["native_table_editable"]]
    print(json.dumps({"total": len(results), "identical": len(results) - len(failed),
                      "failed": failed}, ensure_ascii=False), flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
