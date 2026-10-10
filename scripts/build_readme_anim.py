"""README용 '전 → 후' 움직이는 비교 이미지(GIF)를 기능 그림에서 만든다.

기능 그림(docs/media/features/*.png)의 '전'·'후' 칸을 잘라, 전 칸을 보여 준 뒤 서서히 후 칸으로 바꾸고 잠시 멈추는 GIF를
docs/media/anim/에 만든다. 사용: python scripts/build_readme_anim.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC, OUT = ROOT / "docs/media/features", ROOT / "docs/media/anim"
# 칸 위치(왼, 위, 오른, 아래): 설명용 그림(1440×760)은 좌우 두 칸, 실제 문서 그림은 따로 잰 값
DIAGRAM = ((40, 137, 688, 625), (752, 137, 1400, 625))
BOXES = {
    "spacing": ((40, 180, 1760, 490), (40, 510, 1760, 820)),
    "all-in-one": ((40, 180, 880, 1170), (920, 180, 1760, 1170)),
}
NAMES = ["spacing", "all-in-one", "hanging-indent", "hanging-indent-colon", "page-fit", "page-group", "style-unify",
         "short-line", "spacing-rules", "table-convert", "table-width", "table-format", "abbreviation", "labels",
         "asterisk", "supplement", "format-copy", "original-layout"]
WIDTH = {"all-in-one": 560, "spacing": 860}


def build(name):
    image = Image.open(SRC / f"{name}.png").convert("RGB")
    before_box, after_box = BOXES.get(name, DIAGRAM)
    before, after = image.crop(before_box), image.crop(after_box)
    w = WIDTH.get(name, 640)
    scale = w / before.width
    size = (w, round(before.height * scale))
    before, after = before.resize(size, Image.LANCZOS), after.resize(size, Image.LANCZOS)

    def frame(panel):
        return panel        # 기능 제목은 README에 크게 쓰므로 GIF는 '전 | 후' 칸만 보여 준다

    frames, durations = [frame(before)], [1600]
    for i in range(1, 7):
        frames.append(frame(Image.blend(before, after, i / 7)))
        durations.append(80)
    frames.append(frame(after))
    durations.append(2400)
    for i in range(1, 4):
        frames.append(frame(Image.blend(after, before, i / 4)))
        durations.append(80)
    palette = frames[-4].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    quantized = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"{name}.gif"
    quantized[0].save(target, save_all=True, append_images=quantized[1:], duration=durations, loop=0, optimize=True)
    return target


if __name__ == "__main__":
    for name in NAMES:
        if (SRC / f"{name}.png").exists():
            t = build(name)
            print(f"{t.relative_to(ROOT)}  {t.stat().st_size // 1024}KB")
