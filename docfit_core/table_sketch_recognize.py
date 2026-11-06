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
THRESHOLD_DELTA = 14     # 주변 평균보다 이만큼 어두우면 잉크(최소값)
STROKE_RATIO = 0.35      # 가장 진한 획 대비 이 비율보다 옅으면 잉크로 보지 않는다.
MAX_GRID = 200
PERSPECTIVE_MAX = 0.08   # 가장자리 선이 이만큼(약 4.6°)까지 기울어도 원근 보정을 시도한다.

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
    # 선 대비가 큰 그림에서는 종이 줄무늬 같은 옅은 흔적을 버리도록 문턱을 올린다.
    hist = diff.histogram()
    strong = sum(hist[THRESHOLD_DELTA + 1:])
    delta = THRESHOLD_DELTA
    if strong >= 50:
        acc, contrast = 0, 255
        for level in range(255, THRESHOLD_DELTA, -1):
            acc += hist[level]
            if acc >= strong * 0.05:
                contrast = level
                break
        delta = max(THRESHOLD_DELTA, int(contrast * STROKE_RATIO))
    return diff.point(lambda v: 255 if v > delta else 0)


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


def _edge_tilt(small, box, vertical):
    """표 가장자리 띠에서 선의 기울기 k(선 진행 방향 1칸당 가로 이동)와 가운데 높이의 위치를 찾는다.

    vertical=True면 세로선(x = pos + k*(y-cy)), False면 가로선(y = pos + k*(x-cx)).
    반환: (k, pos). 뚜렷한 기울기가 없으면 k=0.
    """
    from PIL import Image
    strip = small.crop(box)
    if not vertical:
        strip = strip.transpose(Image.Transpose.TRANSPOSE)
    w, h = strip.size
    if w < 2 or h < 8:
        return 0.0, None
    cy = h / 2

    def sheared(k):
        if not k:
            return strip
        return strip.transform((w, h), Image.AFFINE, (1, k, -k * cy, 0, 1, 0), Image.BILINEAR)

    def score(img):
        cols = img.resize((w, 1), Image.BOX).tobytes()
        return sum(v * v for v in cols)

    base = score(strip)
    best_k, best = 0.0, base
    steps = int(PERSPECTIVE_MAX / 0.01)
    for i in range(-steps, steps + 1):
        k = i * 0.01
        if k:
            sc = score(sheared(k))
            if sc > best * 1.0001:
                best_k, best = k, sc
    if best_k:
        for k in (best_k - 0.005, best_k + 0.005):
            sc = score(sheared(k))
            if sc > best * 1.0001:
                best_k, best = k, sc
    if best < base * 1.05:
        best_k = 0.0
    cols = sheared(best_k).resize((w, 1), Image.BOX).tobytes()
    peak = max(range(w), key=lambda i: cols[i])
    origin = box[0] if vertical else box[1]
    return best_k, origin + peak + 0.5


def rectify_perspective(gray, binary):
    """약한 사다리꼴(원근) 왜곡을 네 모서리를 맞춰 바로잡는다. 반환: (gray, 바로잡았는지).

    네 가장자리 선의 기울기를 따로 재서 서로 평행하지 않을 때만 쓴다(단순 회전은 기울기 보정이 맡는다).
    """
    from PIL import Image
    scale = min(1.0, 600 / max(binary.size))
    small = binary.resize((max(1, round(binary.width * scale)), max(1, round(binary.height * scale))), Image.BOX)
    mask = small.resize((max(1, small.width // 3), max(1, small.height // 3)), Image.BOX).point(lambda v: 255 if v > 60 else 0)
    bb = mask.getbbox()
    if not bb:
        return gray, False
    x0, y0, x1, y1 = (bb[0] * 3, bb[1] * 3, min(small.width, bb[2] * 3), min(small.height, bb[3] * 3))
    bw, bh = x1 - x0, y1 - y0
    if bw < 60 or bh < 60:
        return gray, False
    sx, sy = max(6, int(bw * 0.12)), max(6, int(bh * 0.12))
    kl, xl = _edge_tilt(small, (x0, y0, x0 + sx, y1), True)
    kr, xr = _edge_tilt(small, (x1 - sx, y0, x1, y1), True)
    kt, yt = _edge_tilt(small, (x0, y0, x1, y0 + sy), False)
    kb, yb = _edge_tilt(small, (x0, y1 - sy, x1, y1), False)
    if None in (xl, xr, yt, yb):
        return gray, False
    if abs(kl - kr) < 0.01 and abs(kt - kb) < 0.01:
        return gray, False
    cy, cx = (y0 + y1) / 2, (x0 + x1) / 2

    def corner(vk, vx, hk, hy):
        # x = vx + vk*(y-cy), y = hy + hk*(x-cx) 의 교점
        y = hy
        x = vx
        for _ in range(4):
            x = vx + vk * (y - cy)
            y = hy + hk * (x - cx)
        return x, y

    tl, tr = corner(kl, xl, kt, yt), corner(kr, xr, kt, yt)
    bl, br = corner(kl, xl, kb, yb), corner(kr, xr, kb, yb)
    m = 5
    quad = [(tl[0] - m, tl[1] - m), (bl[0] - m, bl[1] + m), (br[0] + m, br[1] + m), (tr[0] + m, tr[1] - m)]
    quad = [(x / scale, y / scale) for x, y in quad]
    width = round((((quad[3][0] - quad[0][0]) + (quad[2][0] - quad[1][0])) / 2))
    height = round((((quad[1][1] - quad[0][1]) + (quad[2][1] - quad[3][1])) / 2))
    if width < MIN_SIDE or height < MIN_SIDE or width > gray.width * 2 or height > gray.height * 2:
        return gray, False
    data = tuple(v for point in quad for v in point)
    out = gray.transform((width, height), Image.QUAD, data, Image.BICUBIC, fillcolor=255)
    return out, True


def _segments(binary, gap, minlen, min_run=4):
    """가로 방향 선분 (중심 y, x0, x1, 두께) 목록.

    행마다 잉크 연속 구간(min_run 미만은 잡음)을 gap 이하 간격으로 이어 선분을 만들고,
    잉크 비율 50% 이상·길이 minlen 이상만 남기고, 위아래로 겹치는 선분은 한 줄로 합친 뒤
    합친 잉크 구간이 80% 이상 덮는 것만 선으로 인정한다(글자 획 조각 배제).
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
                cur[3].append((start, end))
            else:
                if cur:
                    found.append(cur)
                cur = [start, end, end - start, [(start, end)]]
        if cur:
            found.append(cur)
        found = [(s, e, rs) for s, e, ink, rs in found if e - s >= minlen and ink * 2 >= e - s]
        if active:
            still = []
            for comp in active:
                (still if comp[3] >= y - 2 else done).append(comp)
            active = still
        for s, e, rs in found:
            for comp in active:
                overlap = min(e, comp[2]) - max(s, comp[1])
                if overlap > 0 and overlap >= 0.25 * max(e - s, comp[2] - comp[1]):
                    comp[1], comp[2], comp[3] = min(comp[1], s), max(comp[2], e), y
                    comp[4].extend(rs)
                    break
            else:
                active.append([y, s, e, y, list(rs)])  # [첫 행, x0, x1, 마지막 행, 잉크 구간들]
    done.extend(active)
    result = []
    for first, x0, x1, last, runs in done:
        thickness = last - first + 1
        if x1 - x0 >= minlen and thickness <= max(3, 0.3 * (x1 - x0)) and _covered(runs) * 5 >= 4 * (x1 - x0):
            result.append([(first + last) / 2, x0, x1, thickness])
    return _join_collinear(result, gap)


def _covered(runs):
    """잉크 구간들의 합집합 길이. 손으로 그어 흔들린 선은 행마다 끊겨도 합치면 꽉 차고,
    글자 획 조각은 글자 사이 빈틈이 어느 행에서도 비어 있다."""
    total, end = 0, -1
    for a, b in sorted(runs):
        if a > end:
            total += b - a
            end = b
        elif b > end:
            total += b - end
            end = b
    return total


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
    transposed = binary.transpose(5)  # Image.Transpose.TRANSPOSE (2는 ROTATE_90이라 위아래가 뒤집힌다)
    # 1차: 셀 크기를 가늠한다.
    gap1, min1 = max(2, int(dim * 0.03)), max(10, int(dim * 0.04))
    first_h, first_v = _segments(binary, gap1, min1), _segments(transposed, gap1, min1)
    tol1 = max(3, dim * 0.01)
    # 짧은 조각(글자 획·그림자 가장자리)이 셀 크기를 흐리지 않도록 긴 선분이 둘 이상이면 그것만 쓴다.
    long_h = [s for s in first_h if s[2] - s[1] >= dim * 0.25]
    long_v = [s for s in first_v if s[2] - s[1] >= dim * 0.25]
    use_h = long_h if len(_cluster([s[0] for s in long_h], tol1)) >= 2 else first_h
    use_v = long_v if len(_cluster([s[0] for s in long_v], tol1)) >= 2 else first_v
    spacing = _spacing(_cluster([s[0] for s in use_h], tol1)) + _spacing(_cluster([s[0] for s in use_v], tol1))
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
    warped = False
    try:
        gray, warped = rectify_perspective(gray, binary)
    except (ValueError, OSError):
        warped = False
    if warped:
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
    if warped:
        warnings.append("이미지가 비스듬히 찍혀 사다리꼴 왜곡을 바로잡았습니다.")
    if angle:
        warnings.append(f"이미지가 약 {abs(angle):g}° 기울어 있어 바로잡았습니다.")
    return dict(sketch=sketch, rows=len(ys) - 1, cols=len(xs) - 1, angle=angle, warnings=warnings)
