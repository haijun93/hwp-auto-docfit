"""실제 한/글 PDF 출력으로 README 비교 그림·안내 GIF/MP4를 만든다.

화면 녹화나 가상 실행 결과가 아니다. PDF 출력은 build_readme_demo.py로 먼저 만든다.
추가 의존성: Pillow, pypdfium2, imageio-ffmpeg (앱의 필수 의존성은 아님).
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import imageio_ffmpeg
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont, ImageOps

FONT = Path("C:/Windows/Fonts/malgun.ttf")
BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")
INK, MUTED, BLUE = "#172B4D", "#52657D", "#2563EB"
SIZE = (1280, 800)


def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else FONT), size)


def wrap(draw, text, width, f):
    lines, current = [], ""
    for c in text:
        if c == "\n":
            lines.append(current)
            current = ""
        elif draw.textlength(current + c, font=f) > width:
            lines.append(current)
            current = c
        else:
            current += c
    return lines + [current]


def paragraph(draw, xy, text, width, size=25, color=INK, bold=False, bottom=740):
    x, y = xy
    f = font(size, bold)
    for line in wrap(draw, text, width, f):
        if y + size + 8 > bottom:
            raise ValueError(f"설명 글 넘침: {text[:30]}")
        draw.text((x, y), line, font=f, fill=color)
        y += size + 12
    return y


def base(mode, title, step):
    image = Image.new("RGB", SIZE, "#EFF3F9")
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, 1280, 116), fill=INK)
    d.text((42, 17), f"HWP AutoDocFit  /  삼채인.txt  /  {mode}", font=font(20), fill="#B5D1FF")
    d.text((42, 49), title, font=font(34, True), fill="white")
    d.text((1162, 55), f"{step}/4", font=font(26, True), fill="#B5D1FF")
    d.rectangle((0, 753, 1280, 800), fill="white")
    d.text((40, 766), "실제 한/글 처리 결과 기반 · 단계별 안내 애니메이션 · 화면 녹화 아님", font=font(18), fill=MUTED)
    return image


def panel(image, box, title, document, crop=None):
    d = ImageDraw.Draw(image)
    x, y, w, h = box
    d.rounded_rectangle((x, y, x+w, y+h), radius=16, fill="white", outline="#CFD9E7", width=2)
    d.text((x+22, y+13), title, font=font(23, True), fill=INK)
    view = document.crop(crop) if crop else document
    fit = ImageOps.contain(view, (w-30, h-66), Image.Resampling.LANCZOS)
    image.paste(fit, (x + (w-fit.width)//2, y+54))


def render_pdf(path, work):
    pages = []
    pdf = pdfium.PdfDocument(str(path))
    texts = []
    for i in range(len(pdf)):
        page = pdf[i]
        bitmap = page.render(scale=2)
        img = bitmap.to_pil().convert("RGB")
        img.save(work / f"{path.stem}-{i+1}.png")
        pages.append(img)
        textpage = page.get_textpage()
        texts.append(textpage.get_text_range())
        textpage.close()
        bitmap.close()
        page.close()
    pdf.close()
    return pages, texts


def comparison(mode, before, after, out):
    label = "자간 정리" if mode == "spacing" else "한 번에 적용"
    canvas = base(label, "변환 직후와 실제 결과를 비교하세요", 4)
    # 같은 쪽 상단을 보여 준다. 문서 내용·서식을 재작성하지 않는다.
    before_crop = (55, 105, before.width-55, min(before.height, 950 if mode == "all" else 425))
    after_crop = (55, 105, after.width-55, min(after.height, 950 if mode == "all" else 425))
    if mode == "spacing":
        # 개요 문장을 동일 좌표로 확대한다. 전체 쪽은 재현 자료에 별도 보관한다.
        focus = (145, 244, 1045, 357)
        panel(canvas, (36, 140, 1208, 254), "전 | 줄 끝의 ‘거점(지구)’와 ‘수립하여’가 나뉨", before, focus)
        panel(canvas, (36, 416, 1208, 254), "후 | 두 단어를 각각 앞줄에 모음", after, focus)
    else:
        panel(canvas, (36, 145, 590, 534), "전 | TXT를 HWPX로 변환한 직후", before, before_crop)
        panel(canvas, (654, 145, 590, 534), f"후 | {label} 결과", after, after_crop)
    note = ("거점(지구) · 수립하여 : 줄 끝에서 나뉜 단어가 앞줄에 붙었습니다."
            if mode == "spacing" else "제목·개요 표와 기호별 글꼴·간격을 정리했습니다. 쪽 수는 달라질 수 있습니다.")
    paragraph(ImageDraw.Draw(canvas), (40, 698), note, 1200, size=23, bottom=752)
    canvas.save(out / f"{mode}-comparison.png")
    return canvas


def guide(mode, before, after, compare, output, frame_dir):
    label = "자간 정리" if mode == "spacing" else "한 번에 적용"
    if mode == "spacing":
        steps = [
            ("01  같은 예제 파일을 추가합니다", "문서 선택 → 문서 추가", "삼채인.txt를 선택합니다.\nTXT에는 편집 서식이 없으므로 먼저 작업용 HWPX로 변환됩니다.", before),
            ("02  ‘자간 정리’를 선택합니다", "기존 자간 초기화: 켬", "표 제외: 끔\n이번 예시는 기본 설정으로 실행했습니다.\n제목·보고서 양식을 입히는 작업은 아닙니다.", before),
            ("03  ‘정리 시작’ 후 기다립니다", "줄 끝 단어를 확인하세요", "실제 기록: ‘거점(지구)’는 -3%, ‘수립하여’는 -2% 자간으로 앞줄에 붙었습니다.\n처리 시간은 문서·PC마다 다릅니다.", after),
        ]
    else:
        steps = [
            ("01  원문 TXT를 다시 추가합니다", "문서 선택 → 삼채인.txt", "자간 정리 결과가 아니라 같은 원문에서 시작합니다.\n두 기능을 따로 실행한 결과를 비교하는 예제입니다.", before),
            ("02  ‘한 번에 적용’을 선택합니다", "서식: 기본 보고서 서식", "자간 조정 포함: 켬\n표 제외: 끔\n페이지 맞춤 제외: 끔\n사용자 서식 대신 기본 서식으로 시험합니다.", before),
            ("03  보고서 모양까지 정리합니다", "제목·개요·기호·표 확인", "‘제목:’, ‘개요:’ 줄을 서식 표로 바꾸고 항목기호별 모양을 적용합니다.\n박스 문자 표도 실제 표로 변환합니다.", after),
        ]
    frames = []
    for index, (title, lead, text, page) in enumerate(steps, 1):
        img = base(label, title, index)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((34, 148, 440, 714), radius=18, fill="white")
        y = paragraph(d, (60, 181), lead, 351, size=28, color=BLUE, bold=True)
        paragraph(d, (60, y+27), text, 351, size=26, bottom=695)
        crop = (50, 95, page.width-50, min(page.height, 1010))
        panel(img, (467, 148, 778, 566), "실제 문서 출력 · 첫 쪽 상단", page, crop)
        frames.append(img)
    frames.append(compare)
    frames[1].save(output / f"{mode}-poster.png")
    for i, img in enumerate(frames):
        img.save(frame_dir / f"{mode}-{i}.png")
    palette_frames = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
    palette_frames[0].save(output / f"{mode}-guide.gif", save_all=True,
                           append_images=palette_frames[1:], duration=[5000, 6000, 7000, 7000],
                           loop=0, optimize=True, disposal=2)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    # 정지 슬라이드 4장을 실제 결과 안내 영상으로 인코딩한다(클릭 녹화로 표기하지 않음).
    command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    for i in range(4):
        command += ["-loop", "1", "-t", "6", "-i", str(frame_dir / f"{mode}-{i}.png")]
    command += ["-filter_complex", "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0,format=yuv420p[v]",
                "-map", "[v]", "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-r", "15", "-movflags", "+faststart", str(output / f"{mode}-guide.mp4")]
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", type=Path)
    parser.add_argument("--output", type=Path, default=Path("docs/media/samchein"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    frames = args.runs / "media-frames"
    frames.mkdir(exist_ok=True)
    evidence = {"kind": "실제 처리 결과를 설명하는 안내 자료; UI 화면 녹화 아님", "runs": {}}
    for mode in ("spacing", "all"):
        folder = args.runs / mode
        report = json.loads((folder / "run.json").read_text(encoding="utf-8"))
        page_folder = frames / mode
        page_folder.mkdir(exist_ok=True)
        before, _ = render_pdf(folder / "before.pdf", page_folder)
        after, _ = render_pdf(folder / "after.pdf", frames / mode)
        if mode == "all":
            for index, page in enumerate(after, 1):
                page.save(args.output / f"all-page-{index}.png")
        compare = comparison(mode, before[0], after[0], args.output)
        guide(mode, before[0], after[0], compare, args.output, frames)
        evidence["runs"][mode] = {k: report[k] for k in
            ("app_version", "source_file", "source_sha256", "source_unchanged", "code_sha256",
             "git_commit", "elapsed_seconds", "options", "hwp_version", "output_hashes")}
        evidence["runs"][mode].update(before_pages=len(before), after_pages=len(after),
                                     review_count=len(report["review_items"]))
        audit = json.loads(next(folder.glob("*(최종검수).json")).read_text(encoding="utf-8"))
        evidence["runs"][mode]["evaluation"] = {k: audit.get(k) for k in ("score", "verdict", "blockers", "notes")}
    evidence["assets"] = {p.name: {"bytes": p.stat().st_size,
                                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                          for p in args.output.iterdir() if p.suffix in (".gif", ".mp4", ".png")}
    (args.output / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({mode: evidence["runs"][mode] for mode in ("spacing", "all")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
