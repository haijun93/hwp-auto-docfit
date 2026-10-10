"""완료창의 귀여운 검은 고양이 그림(resources/black_cat.png)을 그린다(외부 그림 없이 직접 그려 저작권 걱정이 없다).

사용: .venv\\Scripts\\python.exe scripts\\draw_black_cat.py
4배 크기로 그린 뒤 줄여 테두리를 매끄럽게 한다. 배경은 투명이다.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

S = 4                      # 그릴 때 배율
W, H = 360, 360            # 결과 크기
BLACK = (28, 28, 34, 255)
SHINE = (70, 70, 84, 255)
PINK = (255, 150, 170, 255)
BLUSH = (255, 140, 160, 120)
EYE = (255, 214, 64, 255)
PUPIL = (20, 20, 24, 255)
WHITE = (255, 255, 255, 255)


def s(*v):
    return [round(x * S) for x in v]


def draw():
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 꼬리(몸 뒤에서 위로 말려 올라감)
    d.arc(s(220, 150, 330, 300), start=200, end=40, fill=BLACK, width=26 * S)
    d.ellipse(s(300, 140, 332, 172), fill=BLACK)
    # 몸통
    d.ellipse(s(95, 190, 265, 340), fill=BLACK)
    # 앞발
    d.ellipse(s(118, 300, 168, 342), fill=BLACK)
    d.ellipse(s(192, 300, 242, 342), fill=BLACK)
    for x in (130, 143, 156, 204, 217, 230):
        d.line(s(x, 326, x, 340), fill=SHINE, width=2 * S)
    # 귀
    d.polygon(s(78, 120, 92, 28, 160, 78), fill=BLACK)
    d.polygon(s(282, 120, 268, 28, 200, 78), fill=BLACK)
    d.polygon(s(96, 100, 102, 52, 140, 80), fill=PINK)
    d.polygon(s(264, 100, 258, 52, 220, 80), fill=PINK)
    # 머리
    d.ellipse(s(60, 55, 300, 255), fill=BLACK)
    # 머리 윤기
    d.arc(s(90, 72, 200, 150), start=200, end=260, fill=SHINE, width=6 * S)
    # 눈(크고 동그랗게, 반짝이 두 개)
    for cx in (130, 230):
        d.ellipse(s(cx - 34, 120, cx + 34, 192), fill=EYE)
        d.ellipse(s(cx - 20, 128, cx + 20, 190), fill=PUPIL)
        d.ellipse(s(cx - 14, 134, cx + 2, 152), fill=WHITE)
        d.ellipse(s(cx + 6, 166, cx + 14, 174), fill=WHITE)
    # 볼 홍조
    blush = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(blush)
    bd.ellipse(s(78, 195, 118, 220), fill=BLUSH)
    bd.ellipse(s(242, 195, 282, 220), fill=BLUSH)
    img = Image.alpha_composite(img, blush.filter(ImageFilter.GaussianBlur(4 * S)))
    d = ImageDraw.Draw(img)
    # 코와 입(ω)
    d.polygon(s(172, 198, 188, 198, 180, 208), fill=PINK)
    d.arc(s(162, 200, 182, 222), start=10, end=170, fill=PINK, width=3 * S)
    d.arc(s(178, 200, 198, 222), start=10, end=170, fill=PINK, width=3 * S)
    # 수염
    for y, dy in ((200, -8), (212, 0), (224, 8)):
        d.line(s(98, y, 40, y + dy), fill=SHINE, width=3 * S)
        d.line(s(262, y, 320, y + dy), fill=SHINE, width=3 * S)
    # 작은 하트
    d.polygon(s(300, 40, 312, 28, 324, 40, 312, 56), fill=PINK)
    d.ellipse(s(298, 26, 314, 42), fill=PINK)
    d.ellipse(s(310, 26, 326, 42), fill=PINK)
    return img.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "resources" / "black_cat.png"
    draw().save(out)
    print(out)
