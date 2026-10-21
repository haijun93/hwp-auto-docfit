"""한/글 사본을 PDF·PNG로 렌더링하여 쪽별 화면 차이를 수치로 검사한다.

선택 의존성: pypdfium2, Pillow (requirements에는 추가하지 않는다).
사용: python scripts/visual_compare_pc.py --pair 이름=원본.hwpx,결과.hwpx --out 폴더
회색조 차이 > 40을 변경 픽셀로 센다. bbox는 [좌, 위, 우, 아래](우·아래 제외),
좌표는 144dpi PNG 기준이다. 자동 PASS는 사람의 최종 화면 검수를 대신하지 않는다.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def image_difference(original, result, threshold=40):
    """PNG 경로 두 개의 (차이 픽셀 비율, bbox)를 반환한다. 크기 차이도 센다."""
    from PIL import Image, ImageChops, ImageDraw

    with Image.open(original) as source, Image.open(result) as target:
        left, right = source.convert("L"), target.convert("L")
    width, height = max(left.width, right.width), max(left.height, right.height)
    if width <= 0 or height <= 0:
        raise ValueError("빈 이미지는 비교할 수 없습니다.")
    canvases = []
    for picture in (left, right):
        canvas = Image.new("L", (width, height), 255)
        canvas.paste(picture, (0, 0))
        canvases.append(canvas)
    mask = ImageChops.difference(*canvases).point(lambda value: 255 if value > threshold else 0)
    # 흰색 여백이라도 어느 한 이미지에만 존재하는 영역은 크기 차이로 기록한다.
    valid = []
    for picture in (left, right):
        area = Image.new("L", (width, height), 0)
        ImageDraw.Draw(area).rectangle((0, 0, picture.width - 1, picture.height - 1), fill=255)
        valid.append(area)
    mask = ImageChops.lighter(mask, ImageChops.difference(*valid))
    bbox = mask.getbbox()
    return mask.histogram()[255] / (width * height), list(bbox) if bbox else None


def summary_passes(summary, max_ratio=0.005):
    """쪽 수·쪽별 검사 누락·비정상 수치를 포함하여 보수적으로 판정한다."""
    if not math.isfinite(max_ratio) or not 0 <= max_ratio <= 1 or not summary:
        return False
    for item in summary.values():
        count = item["pages_original"]
        pages = item["pages"]
        if count <= 0 or count != item["pages_result"] or len(pages) != count:
            return False
        if [page["page"] for page in pages] != list(range(1, count + 1)):
            return False
        if any(not math.isfinite(page["diff_ratio"]) or
               not 0 <= page["diff_ratio"] <= max_ratio for page in pages):
            return False
    return True


def optional_dependencies():
    try:
        import pypdfium2
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "화면 대조에는 선택 의존성 pypdfium2와 Pillow가 필요합니다. "
            r"설치: .venv\Scripts\python.exe -m pip install pypdfium2 Pillow"
        ) from exc
    return pypdfium2, Image


def render_pdf(pdf_path, output_dir):
    """PDF를 144dpi PNG로 저장하며 PDFium 자원을 즉시 해제한다."""
    pdfium, _ = optional_dependencies()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    with pdfium.PdfDocument(str(pdf_path)) as document:
        for index in range(len(document)):
            page = document[index]
            try:
                bitmap = page.render(scale=2)
                try:
                    path = output_dir / f"page_{index + 1:03d}.png"
                    bitmap.to_pil().save(path)
                    paths.append(path)
                finally:
                    bitmap.close()
            finally:
                page.close()
    return paths


def export_pdfs(pairs, output_dir):
    """공용 COM 잠금 안에서 임시 사본만 열고 PDF를 만든다."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts"))
    import pythoncom
    import win32com.client
    import regression_pc
    from docfit_core.save_guard import com_test_lock

    outputs = []
    with com_test_lock("Codex", "G4 visual_compare_pc"), tempfile.TemporaryDirectory(prefix="visual_copy_") as work:
        pythoncom.CoInitialize()
        app = None
        try:
            settings = regression_pc.앱_불러오기()
            app = win32com.client.DispatchEx("HwpFrame.HwpObject")
            if app.RegisterModule(settings["REGISTER_MODULE_NAME"], settings["REGISTER_MODULE_VALUE"]) is False:
                raise RuntimeError(
                    "한/글 보안 모듈 등록에 실패했습니다. 앱의 보안 모듈 설치·등록과 "
                    "현재 실행 계정의 접근 권한을 확인하세요."
                )
            for index, (name, original, result) in enumerate(pairs, 1):
                folder = output_dir / f"pair_{index:03d}"
                folder.mkdir()
                pdfs = []
                for side, source in (("original", original), ("result", result)):
                    copy = Path(work) / f"{index}_{side}{source.suffix}"
                    shutil.copyfile(source, copy)
                    pdf = folder / f"{side}.pdf"
                    try:
                        if app.Open(str(copy), "HWPX", "forceopen:true") is False:
                            raise RuntimeError(f"한/글 사본 열기 실패: {source}")
                        if app.SaveAs(str(pdf), "PDF", "") is False or not pdf.is_file() or not pdf.stat().st_size:
                            raise RuntimeError(f"PDF 저장 실패: {source}")
                    finally:
                        app.Clear(1)
                    pdfs.append(pdf)
                outputs.append((name, *pdfs))
                print(f"{name}: PDF 사본 저장 완료", flush=True)
        finally:
            try:
                if app is not None:
                    try:
                        app.Clear(1)
                    finally:
                        app.Quit()
            finally:
                pythoncom.CoUninitialize()
    return outputs


def compare_pdfs(original, result):
    """쪽별 원본·결과 PNG와 나란히 PNG를 남긴다. 없는 쪽은 흰색으로 표시한다."""
    _, Image = optional_dependencies()
    original, result = Path(original), Path(result)
    left = render_pdf(original, original.parent / "original")
    right = render_pdf(result, result.parent / "result")
    pages = []
    for index in range(max(len(left), len(right))):
        images = []
        try:
            for paths in (left, right):
                images.append(Image.open(paths[index]).convert("RGB") if index < len(paths) else None)
            size = next(picture.size for picture in images if picture is not None)
            images = [picture if picture is not None else Image.new("RGB", size, "white") for picture in images]
            # 누락 쪽도 동일한 계산 함수로 검사할 수 있도록 비교용 PNG를 남긴다.
            paths = []
            for side, picture in zip(("original", "result"), images):
                path = original.parent / side / f"page_{index + 1:03d}.png"
                if not path.exists():
                    picture.save(path)
                paths.append(path)
            ratio, bbox = image_difference(*paths)
            combined = Image.new("RGB", (sum(p.width for p in images), max(p.height for p in images)), "white")
            try:
                combined.paste(images[0], (0, 0))
                combined.paste(images[1], (images[0].width, 0))
                combined.save(original.parent / f"side_by_side_{index + 1:03d}.png")
            finally:
                combined.close()
            pages.append({"page": index + 1, "diff_ratio": ratio, "bbox": bbox})
        finally:
            for picture in images:
                if picture is not None:
                    picture.close()
    return {"pages_original": len(left), "pages_result": len(right), "pages": pages}


def parse_pair(value):
    try:
        name, paths = value.split("=", 1)
        original, result = paths.split(",", 1)
        if not name.strip() or not original.strip() or not result.strip():
            raise ValueError
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--pair는 이름=원본.hwpx,결과.hwpx 형식이어야 합니다.") from exc
    return name, Path(original).resolve(), Path(result).resolve()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", action="append", type=parse_pair, required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-ratio", type=float, default=0.005)
    args = parser.parse_args(argv)
    if not math.isfinite(args.max_ratio) or not 0 <= args.max_ratio <= 1:
        parser.error("--max-ratio는 0 이상 1 이하의 유한수여야 합니다.")
    if len({pair[0] for pair in args.pair}) != len(args.pair):
        parser.error("--pair 이름은 중복될 수 없습니다.")
    try:
        optional_dependencies()  # COM을 시작하기 전에 선택 의존성을 확인한다.
        for _, *sources in args.pair:
            for source in sources:
                if not source.is_file() or source.suffix.lower() != ".hwpx":
                    raise ValueError(f"입력 HWPX 파일을 확인하세요: {source}")
        output = args.out.resolve()
        output.mkdir(parents=True, exist_ok=True)
        run_dir = Path(tempfile.mkdtemp(prefix="run_", dir=output))
        summary = {name: compare_pdfs(original, result)
                   for name, original, result in export_pdfs(args.pair, run_dir)}
        (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        passed = summary_passes(summary, args.max_ratio)
        for name, item in summary.items():
            ratios = [page["diff_ratio"] for page in item["pages"]]
            print(f"{name}: 쪽 {item['pages_original']} → {item['pages_result']}, 최대 diff_ratio={max(ratios, default=0):.8f}")
        print(f"{'PASS' if passed else 'FAIL'}: {output / 'summary.json'} (화면: {run_dir})")
        return 0 if passed else 1
    except Exception as exc:
        print(f"화면 대조 오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
