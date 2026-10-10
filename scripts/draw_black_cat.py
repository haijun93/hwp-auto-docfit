"""완료창 고양이 그림(resources/black_cat.png)을 그린다. 외부 그림 없이 직접 그려 저작권 걱정이 없다.

화풍(2026-10-11 사용자 요청): 검은색과 흰색만 쓰는 단순한 실루엣. 고개를 갸웃한 검은 고양이, 아주 큰 흰 동그라미 눈과
작은 눈동자, 뾰족한 귀, 길게 말려 올라간 꼬리, 흰 선의 작은 웃는 입(ω). 배경은 투명이다.
사용: .venv\\Scripts\\python.exe scripts\\draw_black_cat.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

S = 4                       # 그릴 때 배율(줄인 뒤 테두리가 매끄럽다)
W, H = 360, 340
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)


def P(x, y):
    return (x * S, y * S)


def bezier(points, n=60):
    """3차 베지어 곡선 점들."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = points
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3))
    return out


def thick_line(d, pts, width):
    """둥근 끝의 굵은 선(꼬리). 선 이음새 자국이 생기지 않게 원을 촘촘히 이어 칠한다."""
    r = width / 2
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        steps = max(1, int(math.hypot(x1 - x0, y1 - y0) / 0.5))
        for i in range(steps + 1):
            x, y = x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps
            d.ellipse([P(x - r, y - r), P(x + r, y + r)], fill=BLACK)


def rotated(points, cx, cy, deg):
    a = math.radians(deg)
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a),
             cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in points]


def draw():
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 꼬리: 몸 오른쪽 아래에서 위로 길게 올라가 끝이 왼쪽으로 말린다.
    tail = (bezier([(205, 318), (300, 318), (318, 230), (282, 170)])
            + bezier([(282, 170), (258, 128), (276, 82), (306, 92)])[1:])
    thick_line(d, tail, 17)

    # 몸통: 앉은 자세의 둥근 덩어리 + 앞발 두 개
    body = (bezier([(118, 150), (78, 190), (62, 268), (86, 318)])
            + bezier([(86, 318), (130, 330), (200, 330), (232, 312)])[1:]
            + bezier([(232, 312), (250, 260), (226, 196), (178, 160)])[1:])
    d.polygon([P(x, y) for x, y in body], fill=BLACK)
    for x0 in (92, 128):
        d.rounded_rectangle([P(x0, 286), P(x0 + 30, 330)], radius=14 * S, fill=BLACK)

    # 머리: 오른쪽으로 갸웃(15도). 귀 두 개.
    hx, hy, tilt = 150, 118, 15
    head = [(hx + 74 * math.cos(math.radians(a)), hy + 64 * math.sin(math.radians(a))) for a in range(0, 360, 4)]
    d.polygon([P(x, y) for x, y in rotated(head, hx, hy, tilt)], fill=BLACK)
    left_ear = [(92, 82), (104, 22), (146, 62)]
    right_ear = [(170, 58), (226, 30), (218, 96)]
    for ear in (left_ear, right_ear):
        d.polygon([P(x, y) for x, y in rotated(ear, hx, hy, tilt)], fill=BLACK)

    # 아주 큰 흰 동그라미 눈(대각선으로 겹치듯 배치)과 작은 눈동자(위쪽을 봄)
    for ex, ey, r in ((126, 104, 31), (184, 140, 34)):
        d.ellipse([P(ex - r, ey - r), P(ex + r, ey + r)], fill=WHITE)
        d.ellipse([P(ex - 9, ey - 13), P(ex + 3, ey - 1)], fill=BLACK)

    # 흰 선의 작은 웃는 입(ω)
    mx, my = 150, 170
    for side in (-1, 1):
        arc = bezier([(mx, my), (mx + side * 1, my + 8), (mx + side * 8, my + 8), (mx + side * 9, my + 1)], n=20)
        d.line([P(x, y) for x, y in arc], fill=WHITE, width=round(2.4 * S), joint="curve")

    return img.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "resources" / "black_cat.png"
    draw().save(out)
    print(out)
