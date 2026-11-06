"""표 스케치 인식 열화 합성 벤치: 시나리오별 정답 격자 일치율과 처리 시간(Pillow만).

사용: python scripts/bench_sketch_degraded.py [시드수]
일치 = 열·행 수와 정규화된 선 집합이 정답과 완전히 같음.
"""
import math
import random
import sys
import time
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageChops, ImageDraw, ImageFilter  # noqa: E402

from docfit_core import table_sketch as ts  # noqa: E402
from docfit_core import table_sketch_recognize as rec  # noqa: E402

XS = [100, 300, 500, 700, 900]
YS = [100, 300, 500, 700, 900]
# 병합 칸이 있는 표: 일부 선 생략
SPEC = [("h", r, 0, 4) for r in range(5)] + [("v", c, 0, 4) for c in (0, 4)] + [("v", 2, 0, 4), ("v", 1, 0, 2), ("v", 3, 2, 4)]
SPEC = [s for s in SPEC if not (s[0] == "h" and s[1] == 1 and False)]


def base(width=3, size=(1000, 1000), wobble=0.0, rnd=None, text=False):
    img = Image.new("L", size, 255)
    d = ImageDraw.Draw(img)

    def seg(p, q):
        if not wobble:
            d.line([p, q], fill=0, width=width)
            return
        n = 12
        pts = []
        for i in range(n + 1):
            t = i / n
            x = p[0] + (q[0] - p[0]) * t + rnd.uniform(-wobble, wobble)
            y = p[1] + (q[1] - p[1]) * t + rnd.uniform(-wobble, wobble)
            pts.append((x, y))
        d.line(pts, fill=30, width=width, joint="curve")

    for k, f, a, b in SPEC:
        if k == "h":
            seg((XS[a], YS[f]), (XS[b], YS[f]))
        else:
            seg((XS[f], YS[a]), (XS[f], YS[b]))
    if text:
        for r in range(4):
            for c in range(4):
                for i in range(3):
                    x0 = XS[c] + 30 + i * 45
                    d.rectangle([x0, YS[r] + 60 + (i % 2) * 8, x0 + 30, YS[r] + 120], outline=20, width=3)
                    d.line([x0, YS[r] + 90, x0 + 30, YS[r] + 100], fill=20, width=3)
    return img


def shadow(img, rnd):
    w, h = img.size
    grad = Image.linear_gradient("L").resize((w, h)).rotate(rnd.choice((0, 45, 90, 135)))
    grad = grad.point(lambda v: 150 + v * 105 // 255)  # 150..255 곱
    out = ImageChops.multiply(img, grad)
    blob = Image.new("L", (w, h), 255)
    ImageDraw.Draw(blob).ellipse([w * .2, h * .3, w * .8, h * .9], fill=120)
    blob = blob.filter(ImageFilter.GaussianBlur(90))
    return ImageChops.multiply(out, blob)


def perspective(img, rnd):
    w, h = img.size
    s = 0.04  # 위쪽이 4% 좁은 약한 사다리꼴
    dx = w * s
    q = (0, 0, 0, h, w, h, w, 0)
    src = (dx, 0, 0, h, w, h, w - dx, 0)
    return img.transform(img.size, Image.QUAD, src, Image.BICUBIC, fillcolor=255)


def jpeg(img, rnd):
    buf = BytesIO()
    noisy = img.copy()
    px = noisy.load()
    for _ in range(40000):
        x, y = rnd.randrange(img.width), rnd.randrange(img.height)
        px[x, y] = max(0, min(255, px[x, y] + rnd.randint(-40, 40)))
    noisy.save(buf, "JPEG", quality=12)
    return Image.open(BytesIO(buf.getvalue())).convert("L")


def paper(img, rnd):
    d = ImageDraw.Draw(img)
    for y in range(40, img.height, 38):
        d.line([(0, y), (img.width, y)], fill=190, width=1)
    for x in range(60, img.width, 200):
        d.line([(x, 0), (x, 40)], fill=190, width=1)
    return img


SCENARIOS = {
    "깨끗(기준)": lambda r: base(),
    "그림자·조명": lambda r: shadow(base(), r),
    "원근 왜곡": lambda r: perspective(base(), r),
    "JPEG 잡음": lambda r: jpeg(base(), r),
    "손그림 흔들림": lambda r: base(width=4, wobble=2.5, rnd=r),
    "종이 줄무늬": lambda r: paper(base(), r),
    "칸 안 글자": lambda r: base(text=True),
    "복합(그림자+JPEG+흔들림)": lambda r: jpeg(shadow(base(width=4, wobble=2, rnd=r), r), r),
}


def expected():
    lines = [dict(x1=a, y1=f, x2=b, y2=f) if k == "h" else dict(x1=f, y1=a, x2=f, y2=b) for k, f, a, b in SPEC]
    drawing, _ = ts.normalize(dict(grid=dict(cols=4, rows=4, cell_mm=5.0), lines=lines))
    return {(l["x1"], l["y1"], l["x2"], l["y2"]) for l in drawing["lines"]}


def main(seeds=10):
    exp = expected()
    print(f"{'시나리오':<26}{'일치':>8}{'격자수 일치':>12}")
    total = 0
    for name, make in SCENARIOS.items():
        ok = dim = 0
        for seed in range(seeds):
            rnd = random.Random(seed)
            img = make(rnd)
            try:
                res = rec.recognize_image(img)
            except ValueError:
                continue
            if (res["cols"], res["rows"]) == (4, 4):
                dim += 1
                drawing, _ = ts.normalize(res["sketch"])
                if {(l["x1"], l["y1"], l["x2"], l["y2"]) for l in drawing["lines"]} == exp:
                    ok += 1
        total += ok
        print(f"{name:<26}{ok:>4}/{seeds:<3}{dim:>8}/{seeds}")
    img = base()
    t = time.perf_counter()
    for _ in range(3):
        rec.recognize_image(img)
    print(f"1000x1000 깨끗 처리시간: {(time.perf_counter() - t) / 3 * 1000:.0f} ms")
    for name in ("그림자·조명", "복합(그림자+JPEG+흔들림)"):
        img = SCENARIOS[name](random.Random(0))
        t = time.perf_counter()
        for _ in range(3):
            try:
                rec.recognize_image(img)
            except ValueError:
                pass
        print(f"1000x1000 {name} 처리시간: {(time.perf_counter() - t) / 3 * 1000:.0f} ms")
    print("합계 일치", total)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
