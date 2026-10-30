"""표 템플릿 화살표 그림(공문서용 이미지 화살표 5종)을 만든다: resources/arrows/<이름>.png (오른쪽 방향, 투명 바탕).

사용: python scripts/make_arrow_images.py   — 4배로 그린 뒤 줄여 가장자리를 매끄럽게 한다.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "resources" / "arrows"
S = 4                      # 슈퍼샘플링 배율
W, H = 160, 120            # 결과 크기(px)


def canvas():
    return Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))


def pts(points):
    return [(x * S, y * S) for x, y in points]


def basic():
    """기본형: 파란 원 안 흰 화살표."""
    image = canvas()
    d = ImageDraw.Draw(image)
    d.ellipse([22 * S, 2 * S, 138 * S, 118 * S], fill="#2563EB")
    d.polygon(pts([(48, 52), (82, 52), (82, 34), (114, 60), (82, 86), (82, 68), (48, 68)]), fill="white")
    return image


def emphasis():
    """강조형: 회색 굵은 블록 화살표."""
    image = canvas()
    d = ImageDraw.Draw(image)
    d.polygon(pts([(8, 40), (92, 40), (92, 14), (152, 60), (92, 106), (92, 80), (8, 80)]), fill="#6B7280")
    return image


def sleek():
    """세련된 디자인 1: 진회색 삼각 화살촉(가운데 오목)."""
    image = canvas()
    d = ImageDraw.Draw(image)
    d.polygon(pts([(30, 8), (146, 60), (30, 112), (62, 60)]), fill="#374151")
    return image


def chevron():
    """세련된 디자인 2: 남색 겹 화살촉."""
    image = canvas()
    d = ImageDraw.Draw(image)
    d.polygon(pts([(14, 8), (88, 60), (14, 112), (40, 60)]), fill="#1E3A5F")
    d.polygon(pts([(64, 8), (148, 60), (64, 112), (90, 60)]), fill="#1E3A5F")
    return image


def double():
    """이중선: 남색 두 줄 화살표."""
    image = canvas()
    d = ImageDraw.Draw(image)
    d.rectangle([6 * S, 40 * S, 112 * S, 50 * S], fill="#1E3A5F")
    d.rectangle([6 * S, 70 * S, 112 * S, 80 * S], fill="#1E3A5F")
    d.polygon(pts([(98, 22), (154, 60), (98, 98), (108, 60)]), fill="#1E3A5F")
    return image


STYLES = {"basic": basic, "emphasis": emphasis, "sleek": sleek, "chevron": chevron, "double": double}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in STYLES.items():
        draw().resize((W, H), Image.LANCZOS).save(OUT / f"{name}.png", optimize=True)
        print("wrote", OUT / f"{name}.png")


if __name__ == "__main__":
    main()
