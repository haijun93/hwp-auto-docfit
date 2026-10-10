"""완료창 고양이 그림(resources/black_cat.png)을 그린다. 외부 그림 없이 직접 그려 저작권 걱정이 없다.

화풍: 펜으로 그린 스케치(떨리는 선을 여러 번 겹침), 큰 동그란 눈, 나란히 앉아 귀엽게 웃는 흰 고양이와 검은 고양이(크고 동그란 눈·ω 입·볼 홍조),
바닥을 따라 길게 뻗은 꼬리(2026-10-11 사용자 요청 화풍). 같은 결과가 나오도록 난수 씨앗을 고정한다.
사용: .venv\\Scripts\\python.exe scripts\\draw_black_cat.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

S = 3                       # 그릴 때 배율(줄인 뒤 선이 매끄럽다)
W, H = 480, 300
INK = (22, 22, 22, 255)
PAPER = (255, 255, 255, 255)
rng = random.Random(20261011)


def P(x, y):
    return (x * S, y * S)


def jitter_path(points, amount=1.2):
    return [P(x + rng.uniform(-amount, amount), y + rng.uniform(-amount, amount)) for x, y in points]


def stroke(d, points, width=1.6, passes=2, amount=1.0):
    """펜 선: 조금씩 다른 선을 여러 번 겹쳐 손으로 그린 느낌을 낸다."""
    for _ in range(passes):
        d.line(jitter_path(points, amount), fill=INK, width=max(1, round(width * S)), joint="curve")


def curve(p0, p1, p2, n=24):
    """2차 베지어 곡선 점들."""
    out = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        out.append((x, y))
    return out


def ellipse_pts(cx, cy, rx, ry, n=48, a0=0, a1=360):
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
            for a in [a0 + (a1 - a0) * i / n for i in range(n + 1)]]


def cat_outline(cx, base):
    """앉은 고양이 몸 윤곽(머리·귀·몸통)의 점들. cx는 가운데, base는 바닥 y."""
    head_cy = base - 155
    pts = []
    # 왼쪽 귀 → 머리 위 → 오른쪽 귀
    pts += curve((cx - 46, head_cy - 6), (cx - 52, head_cy - 40), (cx - 40, head_cy - 62))
    pts += curve((cx - 40, head_cy - 62), (cx - 26, head_cy - 46), (cx - 16, head_cy - 38))
    pts += curve((cx - 16, head_cy - 38), (cx, head_cy - 42), (cx + 16, head_cy - 38))
    pts += curve((cx + 16, head_cy - 38), (cx + 26, head_cy - 46), (cx + 40, head_cy - 62))
    pts += curve((cx + 40, head_cy - 62), (cx + 52, head_cy - 40), (cx + 46, head_cy - 6))
    # 오른쪽 볼 → 목 → 몸통 오른쪽 → 바닥
    pts += curve((cx + 46, head_cy - 6), (cx + 50, head_cy + 22), (cx + 30, head_cy + 36))
    pts += curve((cx + 30, head_cy + 36), (cx + 46, base - 70), (cx + 40, base))
    pts += [(cx - 40, base)]
    pts += curve((cx - 40, base), (cx - 46, base - 70), (cx - 30, head_cy + 36))
    pts += curve((cx - 30, head_cy + 36), (cx - 50, head_cy + 22), (cx - 46, head_cy - 6))
    return pts, head_cy


def fur(d, cx, cy, r, count, color=INK, length=(4, 9), a0=0, a1=360):
    """윤곽 바깥으로 삐친 털 몇 가닥."""
    for _ in range(count):
        a = math.radians(rng.uniform(a0, a1))
        x0, y0 = cx + r * math.cos(a), cy + r * math.sin(a)
        ln = rng.uniform(*length)
        x1, y1 = x0 + ln * math.cos(a + rng.uniform(-0.4, 0.4)), y0 + ln * math.sin(a + rng.uniform(-0.4, 0.4))
        d.line([P(x0, y0), P(x1, y1)], fill=color, width=max(1, round(1.1 * S)))


def eyes(d, cx, cy, look=(3, -2), white_ring=False):
    for ex in (cx - 17, cx + 17):
        rx, ry = 14, 15
        d.ellipse([P(ex - rx, cy - ry), P(ex + rx, cy + ry)], fill=PAPER)
        stroke(d, ellipse_pts(ex, cy, rx, ry), width=1.8, passes=2, amount=0.6)
        px, py = ex + look[0], cy + look[1]
        d.ellipse([P(px - 4.5, py - 4.5), P(px + 4.5, py + 4.5)], fill=INK)


def whiskers(d, cx, cy, color=INK):
    for side in (-1, 1):
        for dy, tilt in ((-4, -5), (1, 0), (6, 6)):
            x0 = cx + side * 20
            stroke(d, [(x0, cy + dy), (x0 + side * 22, cy + dy + tilt * 0.6), (x0 + side * 44, cy + dy + tilt)],
                   width=0.9, passes=1, amount=0.5)


BLUSH = (255, 140, 165, 150)


def smile_face(img, cx, cy, line):
    """귀엽게 웃는 얼굴: 크고 동그란 눈(반짝이), ω 입, 볼 홍조. line은 선 색(흰 고양이는 먹색, 검은 고양이는 흰색)."""
    from PIL import ImageFilter
    blush = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(blush)
    for bx in (cx - 27, cx + 27):
        bd.ellipse([P(bx - 9, cy + 9), P(bx + 9, cy + 17)], fill=BLUSH)
    img.alpha_composite(blush.filter(ImageFilter.GaussianBlur(2.2 * S)))
    d = ImageDraw.Draw(img)
    for ex in (cx - 21, cx + 21):                  # 크고 동그란 눈: 흰자 + 큰 눈동자 + 반짝이 세 개
        ey = cy - 6
        d.ellipse([P(ex - 19, ey - 19), P(ex + 19, ey + 19)], fill=PAPER)
        stroke(d, ellipse_pts(ex, ey, 19, 19), width=1.9, passes=2, amount=0.5)
        d.ellipse([P(ex - 14, ey - 12), P(ex + 14, ey + 16)], fill=INK)
        d.ellipse([P(ex - 10, ey - 8), P(ex - 1, ey + 1)], fill=PAPER)
        d.ellipse([P(ex + 4, ey + 6), P(ex + 9, ey + 11)], fill=PAPER)
        d.ellipse([P(ex + 5, ey - 6), P(ex + 8, ey - 3)], fill=PAPER)
    d.polygon([P(cx - 3.5, cy + 14), P(cx + 3.5, cy + 14), P(cx, cy + 18)], fill=(255, 150, 170, 255))   # 분홍 코
    for side in (-1, 1):                           # ω 입
        pts = curve((cx, cy + 18), (cx + side * 3, cy + 26), (cx + side * 7, cy + 19))
        d.line([P(x, y) for x, y in pts], fill=line, width=round(1.6 * S), joint="curve")
    return d


def draw():
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ground = 272
    white_cx, black_cx = 180, 300

    # 바닥 선
    stroke(d, [(20, ground), (240, ground + 1), (460, ground)], width=1.6, passes=2, amount=0.8)
    # 흰 고양이 꼬리: 바닥을 따라 왼쪽으로 길게
    tail = curve((white_cx - 30, ground - 4), (90, ground - 2), (28, ground - 14))
    stroke(d, tail, width=1.6, passes=2, amount=0.7)
    stroke(d, curve((white_cx - 30, ground - 12), (95, ground - 10), (30, ground - 22)), width=1.6, passes=2, amount=0.7)
    d.ellipse([P(22, ground - 24), P(36, ground - 12)], outline=INK, width=round(1.4 * S))

    # 흰 고양이(윤곽만)
    pts, head_cy = cat_outline(white_cx, ground)
    d.polygon([P(x, y) for x, y in pts], fill=PAPER)
    stroke(d, pts + pts[:1], width=1.8, passes=3, amount=0.9)
    fur(d, white_cx, head_cy - 8, 47, 10, a0=150, a1=390)
    stroke(d, curve((white_cx - 34, head_cy - 50), (white_cx - 32, head_cy - 34), (white_cx - 22, head_cy - 36)), width=1, passes=1)
    stroke(d, curve((white_cx + 34, head_cy - 50), (white_cx + 32, head_cy - 34), (white_cx + 22, head_cy - 36)), width=1, passes=1)
    # 앞다리와 발
    for x in (white_cx - 12, white_cx + 12):
        stroke(d, [(x, head_cy + 50), (x - 1, ground - 10)], width=1.3, passes=2, amount=0.6)
    for x in (white_cx - 22, white_cx + 2):
        stroke(d, ellipse_pts(x + 10, ground - 5, 11, 6, a0=180, a1=360), width=1.3, passes=2, amount=0.4)
    for i in range(6):                       # 몸통 털결
        y = head_cy + 60 + i * 12
        stroke(d, [(white_cx + 26, y), (white_cx + 32, y + 6)], width=0.8, passes=1, amount=0.4)
    d = smile_face(img, white_cx, head_cy, INK)
    whiskers(d, white_cx, head_cy + 20)

    # 검은 고양이(칠함)
    pts, head_cy = cat_outline(black_cx, ground)
    d.polygon([P(x, y) for x, y in pts], fill=INK)
    stroke(d, pts + pts[:1], width=2.2, passes=3, amount=1.1)
    fur(d, black_cx, head_cy - 8, 46, 26, length=(5, 11), a0=140, a1=400)
    for side in (-1, 1):                     # 몸통 옆 삐친 털
        for i in range(7):
            y = head_cy + 50 + i * 13
            x = black_cx + side * (36 + rng.uniform(0, 6))
            d.line([P(x, y), P(x + side * rng.uniform(4, 8), y + rng.uniform(2, 6))], fill=INK, width=round(1.2 * S))
    # 꼬리: 오른쪽 아래로 짧게 말림
    stroke(d, curve((black_cx + 38, ground - 6), (black_cx + 70, ground - 4), (black_cx + 76, ground - 26)), width=6, passes=2, amount=0.8)
    d = smile_face(img, black_cx, head_cy - 2, PAPER)
    whiskers(d, black_cx, head_cy + 18)
    for x in (black_cx - 14, black_cx + 14):      # 발가락 흰 선
        for k in (-4, 0, 4):
            d.line([P(x + k, ground - 8), P(x + k, ground - 2)], fill=(90, 90, 90, 255), width=S)

    return img.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "resources" / "black_cat.png"
    draw().save(out)
    print(out)
