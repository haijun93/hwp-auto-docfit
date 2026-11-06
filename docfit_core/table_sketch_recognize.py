"""표를 그린 이미지(PNG/JPEG)에서 가로·세로 선을 찾아 table_sketch sketch로 바꾼다.

Pillow와 표준 라이브러리만 쓰는 순수 함수 모음이며 COM을 쓰지 않는다.
처리 순서: 회색조 → 적응 임계 이진화 → 기울기(±3°) 추정·보정 → 행/열 단위 선분 추출
(끊긴 선 잇기·잡음 제거·두꺼운 선 합치기) → 선 위치를 격자 번호로 맞춤.
"""
from __future__ import annotations

import re
from io import BytesIO

MAX_SIDE = 1200          # 이보다 큰 이미지는 줄여서 처리한다.
MIN_SIDE = 32
MAX_PIXELS = 16_000_000
MAX_SKEW = 3.0           # 보정하는 최대 기울기(도)
GAP_RATIO = 0.20         # 끊긴 선을 잇는 최대 간격(셀 크기 대비)
THRESHOLD_DELTA = 14     # 주변 평균보다 이만큼 어두우면 잉크
MAX_GRID = 200

_RUN = re.compile(rb"\xff+")


def _open(source):
    from PIL import Image
    if isinstance(source, Image.Image):
        image = source
    else:
        if isinstance(source, (bytes, bytearray)):
            source = BytesIO(source)
        try:
            image = Image.open(source)
            if image.width * image.height > MAX_PIXELS:
                raise ValueError("표 스케치 이미지 크기를 확인해 주세요.")
            image.load()
        except (OSError, Image.DecompressionBombError) as exc:
            raise ValueError("지원하는 그림 파일을 읽지 못했습니다.") from exc
    if image.width < MIN_SIDE or image.height < MIN_SIDE:
        raise ValueError("표 스케치 이미지 크기를 확인해 주세요.")
    return image


def _to_gray(image, max_side=MAX_SIDE):
    """투명 배경은 흰색으로 깔고 회색조로 바꾼 뒤 너무 크면 줄인다."""
    from PIL import Image
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        base = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        image = Image.alpha_composite(base, rgba)
    gray = image.convert("L")
    if max(gray.size) > max_side:
        gray.thumbnail((max_side, max_side), Image.LANCZOS)
    return gray


def binarize(gray):
    """적응 임계: 주변 평균보다 어두운 점만 잉크(255), 나머지 0. 그림자·조명 얼룩에 강하다."""
    from PIL import ImageChops, ImageFilter
    radius = max(7, min(gray.size) // 16)
    local = gray.filter(ImageFilter.BoxBlur(radius))
    diff = ImageChops.subtract(local, gray)
    return diff.point(lambda v: 255 if v > THRESHOLD_DELTA else 0)


def _profile_score(image):
    from PIL import Image
    w, h = image.size
    rows = image.resize((1, h), Image.BOX).tobytes()
    cols = image.resize((w, 1), Image.BOX).tobytes()
    return sum(v * v for v in rows) + sum(v * v for v in cols)


def estimate_skew(binary, max_angle=MAX_SKEW, work=600):
    """투영이 가장 뚜렷해지는 회전 각(도, 반시계 +)을 찾는다. 줄이 없으면 0."""
    from PIL import Image
    small = binary
    if max(small.size) > work:
        scale = work / max(small.size)
        small = small.resize((max(1, round(small.width * scale)), max(1, round(small.height * scale))), Image.BOX)

    def score(angle):
        if angle == 0:
            return _profile_score(small)
        return _profile_score(small.rotate(angle, resample=Image.BILINEAR))

    base = score(0)
    if base == 0:
        return 0.0
    best_angle, best = 0.0, base
    steps = int(round(max_angle / 0.5))
    for i in range(-steps, steps + 1):
        angle = i * 0.5
        if angle == 0:
            continue
        s = score(angle)
        if s > best * 1.0001:
            best_angle, best = angle, s
    center = best_angle
    for i in range(-4, 5):
        angle = round(center + i * 0.1, 2)
        if i == 0 or abs(angle) > max_angle:
            continue
        s = score(angle)
        if s > best * 1.0001:
            best_angle, best = angle, s
    # 개선이 미미하면 기울기 없음으로 본다.
    return best_angle if best > base * 1.02 else 0.0


def _segments(binary, gap, minlen, min_run=4):
    """가로 방향 선분 (중심 y, x0, x1, 두께) 목록.

    행마다 잉크 연속 구간(min_run 미만은 잡음)을 gap 이하 간격으로 이어 선분을 만들고,
    잉크 비율 50% 이상·길이 minlen 이상만 남긴다. 위아래로 겹치는 선분은 한 줄로 합친다.
    """
    w, h = binary.size
    data = binary.tobytes()
    done, active = [], []
    for y in range(h):
        row = data[y * w:(y + 1) * w]
        if row.find(b"\xff") < 0:
            continue
        runs = [(m.start(), m.end()) for m in _RUN.finditer(row) if m.end() - m.start() >= min_run]
        found, cur = [], None
        for start, end in runs:
            if cur and start - cur[1] <= gap:
                cur[1] = end
                cur[2] += end - start
            else:
                if cur:
                    found.append(cur)
                cur = [start, end, end - start]
        if cur:
            found.append(cur)
        found = [(s, e) for s, e, ink in found if e - s >= minlen and ink * 2 >= e - s]
        if active:
            still = []
            for comp in active:
                (still if comp[3] >= y - 2 else done).append(comp)
            active = still
        for s, e in found:
            for comp in active:
                overlap = min(e, comp[2]) - max(s, comp[1])
                if overlap > 0 and overlap >= 0.25 * max(e - s, comp[2] - comp[1]):
                    comp[1], comp[2], comp[3] = min(comp[1], s), max(comp[2], e), y
                    break
            else:
                active.append([y, s, e, y])  # [첫 행, x0, x1, 마지막 행]
    done.extend(active)
    result = []
    for first, x0, x1, last in done:
        thickness = last - first + 1
        if x1 - x0 >= minlen and thickness <= max(3, 0.3 * (x1 - x0)):
            result.append([(first + last) / 2, x0, x1, thickness])
    return _join_collinear(result, gap)


def _join_collinear(segs, gap):
    """같은 높이에서 이어지는(간격 ≤ gap) 선분을 하나로 합친다(기울기 보정 잔차 대비)."""
    segs = sorted(segs, key=lambda s: (s[0], s[1]))
    merged = True
    while merged:
        merged = False
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                a, b = segs[i], segs[j]
                near = abs(a[0] - b[0]) <= max(2.0, (a[3] + b[3]) / 2)
                joined = min(a[2], b[2]) - max(a[1], b[1]) >= -gap
                if near and joined:
                    la, lb = a[2] - a[1], b[2] - b[1]
                    segs[i] = [(a[0] * la + b[0] * lb) / (la + lb), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    del segs[j]
                    merged = True
                    break
            if merged:
                break
    return segs


def _cluster(values, tol):
    values = sorted(values)
    groups = []
    for v in values:
        if groups and v - groups[-1][-1] <= tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [sum(g) / len(g) for g in groups]


def _spacing(centers):
    return [b - a for a, b in zip(centers, centers[1:])]


def _snap(value, centers):
    return min(range(len(centers)), key=lambda i: abs(centers[i] - value))


def _detect(binary):
    """(가로 선분, 세로 선분, 셀 추정 크기). 선분은 [위치, 시작, 끝, 두께]."""
    w, h = binary.size
    dim = max(w, h)
    transposed = binary.transpose(2)  # Image.Transpose.TRANSPOSE
    # 1차: 셀 크기를 가늠한다.
    gap1, min1 = max(2, int(dim * 0.03)), max(10, int(dim * 0.04))
    first_h, first_v = _segments(binary, gap1, min1), _segments(transposed, gap1, min1)
    tol1 = max(3, dim * 0.01)
    spacing = _spacing(_cluster([s[0] for s in first_h], tol1)) + _spacing(_cluster([s[0] for s in first_v], tol1))
    spacing = [d for d in spacing if d >= 6]
    cell = min(spacing) if spacing else dim * 0.1
    # 2차: 셀 크기에 맞춘 간격·길이 기준으로 다시 찾는다.
    gap = max(2, int(cell * GAP_RATIO))
    minlen = max(10, int(cell * 0.6), int(dim * 0.03))
    return _segments(binary, gap, minlen), _segments(transposed, gap, minlen), cell


def recognize_image(source):
    """이미지에서 표 선을 찾는다. 반환: dict(sketch, rows, cols, angle, warnings).

    source: bytes / 파일 객체 / 경로 / PIL.Image. 선을 충분히 못 찾으면 ValueError.
    """
    gray = _to_gray(_open(source))
    binary = binarize(gray)
    angle = estimate_skew(binary)
    if angle:
        from PIL import Image
        gray = gray.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=255)
        binary = binarize(gray)
    hs, vs, cell = _detect(binary)
    if len(hs) < 2 or len(vs) < 2:
        raise ValueError("표의 가로·세로 선을 충분히 찾지 못했습니다. 선이 선명한 정면 이미지를 사용해 주세요.")
    tol = max(3.0, cell * 0.25)
    ys = _cluster([s[0] for s in hs], tol)
    xs = _cluster([s[0] for s in vs], tol)
    if len(xs) < 2 or len(ys) < 2:
        raise ValueError("표의 가로·세로 선을 충분히 찾지 못했습니다. 선이 선명한 정면 이미지를 사용해 주세요.")
    if len(xs) - 1 > MAX_GRID or len(ys) - 1 > MAX_GRID:
        raise ValueError("찾은 선이 너무 많습니다. 더 단순한 표 그림을 사용해 주세요.")
    thicknesses = sorted(s[3] for s in hs + vs)
    median = thicknesses[len(thicknesses) // 2]

    def width(t):
        return "thick" if len(thicknesses) >= 3 and t >= max(2 * median, median + 3) else "thin"

    lines, seen = [], set()
    for pos, a, b, t in hs:
        r, c1, c2 = _snap(pos, ys), _snap(a, xs), _snap(b, xs)
        if c1 != c2 and ("h", r, c1, c2) not in seen:
            seen.add(("h", r, c1, c2))
            lines.append(dict(x1=c1, y1=r, x2=c2, y2=r, width=width(t)))
    for pos, a, b, t in vs:
        c, r1, r2 = _snap(pos, xs), _snap(a, ys), _snap(b, ys)
        if r1 != r2 and ("v", c, r1, r2) not in seen:
            seen.add(("v", c, r1, r2))
            lines.append(dict(x1=c, y1=r1, x2=c, y2=r2, width=width(t)))
    sketch = dict(grid=dict(cols=len(xs) - 1, rows=len(ys) - 1, cell_mm=5.0), lines=lines, texts=[])
    warnings = []
    if angle:
        warnings.append(f"이미지가 약 {abs(angle):g}° 기울어 있어 바로잡았습니다.")
    return dict(sketch=sketch, rows=len(ys) - 1, cols=len(xs) - 1, angle=angle, warnings=warnings)
