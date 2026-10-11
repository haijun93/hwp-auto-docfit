"""앱 아이콘(resources/app_icon.ico)을 완료창 고양이 그림(resources/black_cat.png)으로 만든다.

검은 고양이가 어두운 작업 표시줄에서도 보이도록 흰 둥근 사각형 바탕 위에 올린다.
사용: .venv\\Scripts\\python.exe scripts\\make_app_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

크기들 = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def 아이콘_그림(고양이, 변=1024):
    """변 길이 정사각형: 흰 둥근 사각형 바탕 + 가운데 고양이(바탕의 약 84%)."""
    판 = Image.new("RGBA", (변, 변), (0, 0, 0, 0))
    ImageDraw.Draw(판).rounded_rectangle((0, 0, 변 - 1, 변 - 1), radius=변 // 5, fill=(255, 255, 255, 255))
    고양이 = 고양이.convert("RGBA")
    고양이 = 고양이.crop(고양이.getbbox() or (0, 0, *고양이.size))
    배율 = 변 * 0.84 / max(고양이.size)
    고양이 = 고양이.resize((round(고양이.width * 배율), round(고양이.height * 배율)), Image.LANCZOS)
    판.alpha_composite(고양이, ((변 - 고양이.width) // 2, (변 - 고양이.height) // 2))
    return 판


def main():
    폴더 = Path(__file__).resolve().parents[1] / "resources"
    그림 = 아이콘_그림(Image.open(폴더 / "black_cat.png"))
    out = 폴더 / "app_icon.ico"
    그림.save(out, format="ICO", sizes=[(n, n) for n in 크기들])
    print(out)


if __name__ == "__main__":
    main()
