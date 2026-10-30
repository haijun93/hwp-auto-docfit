"""표 템플릿 화살표 바꾸기(2.0.6): 추진절차·신구대조표처럼 칸 사이에 화살표 기호·그림이 있는 표에서 사용자가 화살표 종류를 고른다.

- 화살표 칸 찾기: 칸 글이 화살표 기호 한 글자이거나, 글 없이 그림·도형만 든 좁은 칸(표 폭의 15% 이하 또는 높이의 20% 이하).
  칸마다 원래 방향(기호의 방향, 없으면 칸 모양: 세로로 길면 오른쪽, 납작하면 아래)을 기억한다.
- 기호 화살표: 칸 안 그림·도형을 지우고 고른 기호를 넣는다(칸 글자 서식은 그대로). 오른쪽 기호(⇨ 등)는 칸 방향대로
  돌린 짝(⇩ 등)을 쓴다 — 추진절차(가로세로)처럼 오른쪽·아래 화살표가 섞인 표.
- 그림 화살표(공문서용 5종): resources/arrows/<이름>.png를 방향대로 돌려 한/글 그림(hp:pic, 글자처럼 취급)으로 넣는다.
  그림 파일은 BinData/docfitArrow<방향>.png로 문서에 넣고 content.hpf 목록에 올린다.
- 칸 바탕에 그림을 깐 화살표(신구대조표 모양 1)는 바탕 그림을 뺀 테두리/배경으로 바꾼다.
정보단위를 늘리기 전 원본 표에 적용하므로 늘어난 칸(복제된 화살표 칸)도 같은 화살표가 된다.
"""
from __future__ import annotations

import base64
import copy
import io
from pathlib import Path

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
HC = "{http://www.hancom.co.kr/hwpml/2011/core}"
HH = "{http://www.hancom.co.kr/hwpml/2011/head}"

ARROW_SYMBOLS = ("⇒", "⇔", "➡", "⇨", "⇦", "⇧", "⇩", "▷", "◀", "→", "➜", "▶")
_KNOWN = set(ARROW_SYMBOLS) | set("➤►≫▼↓▽⬇⇓←⇐◁↑⇑▲△↔⇄⬅⬆")
IMAGE_STYLES = {"basic": "기본형", "emphasis": "강조형", "sleek": "세련된 디자인 1", "chevron": "세련된 디자인 2",
                "double": "이중선"}
SIZES_MM = {"small": 4.5, "medium": 6.5, "large": 9.0}
DIRECTIONS = {"right": 0, "down": -90, "left": 180, "up": 90}
_ORDER = ("right", "down", "left", "up")
# 오른쪽 기호의 방향별 짝. 오른쪽이 아닌 기호(⇦·⇧ 등)는 고른 그대로 쓴다.
_TURN = {"⇒": "⇒⇓⇐⇑", "⇨": "⇨⇩⇦⇧", "➡": "➡⬇⬅⬆", "→": "→↓←↑", "➜": "➜↓←↑", "▶": "▶▼◀▲", "▷": "▷▽◁△",
         "⇔": "⇔⇕⇔⇕"}
_CHAR_DIRECTION = {**{c: "down" for c in "▼↓▽⬇⇓⇩"}, **{c: "up" for c in "↑⇑⇧▲△⬆"},
                   **{c: "left" for c in "←⇐⇦◀◁⬅"}}
BIN_ID = "docfitArrow"
_DRAW_TAGS = {"pic", "rect", "polygon", "line", "ellipse", "container", "arc", "curve", "connectLine", "textart"}
_HWPUNIT_PER_MM = 7200 / 25.4


def arrow_root() -> Path:
    import sys
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / "resources" / "arrows"


def bin_id(direction: str) -> str:
    return f"{BIN_ID}{direction.capitalize()}"


def _flat(meta):
    return [c for row in meta for c in (row if isinstance(row, list) else [row])]


def detect(record) -> dict:
    """원본 표의 화살표 칸 {(행, 열): 원래 방향}."""
    cells = _flat(record.get("cell_meta") or [])
    if not cells:
        return {}
    widths, heights = {}, {}
    for cell in cells:
        if cell.get("colSpan", 1) == 1:
            widths[cell["col"]] = max(widths.get(cell["col"], 0), float(cell.get("width") or 0))
        if cell.get("rowSpan", 1) == 1:
            heights[cell["row"]] = max(heights.get(cell["row"], 0), float(cell.get("height") or 0))
    total_w, total_h = sum(widths.values()) or 1, sum(heights.values()) or 1
    found = {}
    for cell in cells:
        text = "".join(str(cell.get("text") or "").split())
        width, height = float(cell.get("width") or 0), float(cell.get("height") or 0)
        narrow = width <= total_w * 0.15 or height <= total_h * 0.2
        key = (int(cell["row"]), int(cell["col"]))
        if len(text) == 1 and text in _KNOWN:
            found[key] = _CHAR_DIRECTION.get(text, "right")
        elif not text and cell.get("shapes") and narrow:
            # 도형에 방향이 있으면 그것을, 없으면 칸 모양을 따른다.
            marked = next((s.get("direction") for s in cell["shapes"] if s.get("direction") in DIRECTIONS), None)
            found[key] = marked or ("right" if height * 1.2 >= width else "down")
    return found


def _turned(symbol, direction):
    variants = _TURN.get(symbol)
    return variants[_ORDER.index(direction)] if variants else symbol


def validate(spec):
    """사용자가 고른 화살표: {"kind": "symbol"|"image", "value": …, "direction": auto|…, "size": …}. 없으면 None."""
    if spec in (None, "", {}):
        return None
    if not isinstance(spec, dict):
        raise ValueError("화살표 선택 정보가 올바르지 않습니다.")
    kind, value = spec.get("kind"), spec.get("value")
    if kind == "symbol" and value in ARROW_SYMBOLS:
        return {"kind": "symbol", "value": value}
    if kind == "image" and value in IMAGE_STYLES:
        direction = spec.get("direction", "auto")   # auto: 칸마다 원래 화살표 방향
        size = spec.get("size", "medium")
        if (direction != "auto" and direction not in DIRECTIONS) or size not in SIZES_MM:
            raise ValueError("화살표 방향·크기를 확인해 주세요.")
        return {"kind": "image", "value": value, "direction": direction, "size": size}
    raise ValueError("화살표 종류를 확인해 주세요.")


def image_png(style: str, direction: str = "right") -> bytes:
    from PIL import Image
    with Image.open(arrow_root() / f"{style}.png") as opened:
        image = opened.convert("RGBA")
    angle = DIRECTIONS[direction]
    if angle:
        image = image.rotate(angle, expand=True)
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()


def image_data_url(style: str, direction: str = "right") -> str:
    return "data:image/png;base64," + base64.b64encode(image_png(style, direction)).decode("ascii")


def catalog() -> dict:
    """화면에 보일 선택지(그림 화살표는 미리보기 그림 포함)."""
    return {"symbols": list(ARROW_SYMBOLS),
            "images": [{"value": key, "label": label, "src": image_data_url(key)} for key, label in IMAGE_STYLES.items()],
            "directions": [["auto", "원래 방향"], ["right", "오른쪽"], ["down", "아래"], ["left", "왼쪽"], ["up", "위"]],
            "sizes": [["small", "작게"], ["medium", "보통"], ["large", "크게"]]}


def _child(element, name):
    return next((x for x in element if x.tag == HP + name), None)


def _make(parent, tag, **attrs):
    child = type(parent)(tag, {k: str(v) for k, v in attrs.items()})
    parent.append(child)
    return child


def _strip(cell):
    """칸 안 그림·도형과 글을 지우고 첫 문단의 첫 run을 돌려준다."""
    first_run = None
    for p in cell.iter(HP + "p"):
        for cache in p.findall(HP + "linesegarray"):
            p.remove(cache)
        for run in p.findall(HP + "run"):
            if first_run is None:
                first_run = run
            for item in list(run):
                if item.tag.rsplit("}", 1)[-1] in _DRAW_TAGS:
                    run.remove(item)
                elif item.tag == HP + "t":
                    item.text = ""
                    for sub in list(item):
                        item.remove(sub)
    if first_run is None:
        p = next(cell.iter(HP + "p"), None)
        if p is None:
            raise ValueError("화살표 칸 구조를 읽지 못했습니다.")
        first_run = _make(p, HP + "run", charPrIDRef="0")
    return first_run


def _picture(run, cell, spec, direction, ids):
    """칸 크기에 맞춘 글자처럼 취급하는 그림(hp:pic)."""
    from PIL import Image
    size = cell.find(HP + "cellSz")
    margin = cell.find(HP + "cellMargin")
    cell_w = int(size.get("width")) if size is not None else 3000
    cell_h = int(size.get("height")) if size is not None else 3000
    pad_w = int(margin.get("left", 141)) + int(margin.get("right", 141)) if margin is not None else 282
    pad_h = int(margin.get("top", 141)) + int(margin.get("bottom", 141)) if margin is not None else 282
    with Image.open(io.BytesIO(image_png(spec["value"], direction))) as image:
        px_w, px_h = image.size
    longest = SIZES_MM[spec["size"]] * _HWPUNIT_PER_MM
    width, height = (longest, longest * px_h / px_w) if px_w >= px_h else (longest * px_w / px_h, longest)
    scale = min(1.0, max(cell_w - pad_w, 300) / width, max(cell_h - pad_h, 300) / height)
    width, height = int(width * scale), int(height * scale)
    org_w, org_h = px_w * 75, px_h * 75   # 96dpi 픽셀 → HWPUNIT(1px = 75)
    # 그림마다 다른 id·instid(문서 안 다른 개체와 겹치지 않게 표의 가장 큰 값 다음부터, Codex 검토 2026-10-30).
    pic = _make(run, HP + "pic", id=next(ids), zOrder="30", numberingType="PICTURE", textWrap="TOP_AND_BOTTOM",
                textFlow="BOTH_SIDES", lock="0", dropcapstyle="None", href="", groupLevel="0", instid=next(ids),
                reverse="0")
    _make(pic, HP + "offset", x="0", y="0")
    _make(pic, HP + "orgSz", width=org_w, height=org_h)
    _make(pic, HP + "curSz", width=width, height=height)
    _make(pic, HP + "flip", horizontal="0", vertical="0")
    _make(pic, HP + "rotationInfo", angle="0")
    rendering = _make(pic, HP + "renderingInfo")
    _make(rendering, HC + "transMatrix", e1="1", e2="0", e3="0", e4="0", e5="1", e6="0")
    _make(rendering, HC + "scaMatrix", e1=f"{width / org_w:.6f}", e2="0", e3="0", e4="0", e5=f"{height / org_h:.6f}", e6="0")
    _make(rendering, HC + "rotMatrix", e1="1", e2="0", e3="0", e4="0", e5="1", e6="0")
    rect = _make(pic, HP + "imgRect")
    for index, (x, y) in enumerate(((0, 0), (org_w, 0), (org_w, org_h), (0, org_h))):
        _make(rect, HC + f"pt{index}", x=x, y=y)
    _make(pic, HP + "imgClip", left="0", right=org_w, top="0", bottom=org_h)
    _make(pic, HP + "inMargin", left="0", right="0", top="0", bottom="0")
    _make(pic, HP + "imgDim", dimwidth=org_w, dimheight=org_h)
    _make(pic, HC + "img", binaryItemIDRef=bin_id(direction), bright="0", contrast="0", effect="REAL_PIC", alpha="0")
    _make(pic, HP + "effects")
    _make(pic, HP + "sz", width=width, widthRelTo="ABSOLUTE", height=height, heightRelTo="ABSOLUTE", protect="0")
    _make(pic, HP + "pos", treatAsChar="1", affectLSpacing="0", flowWithText="1", allowOverlap="1", holdAnchorAndSO="0",
          vertRelTo="PARA", horzRelTo="COLUMN", vertAlign="TOP", horzAlign="LEFT", vertOffset="0", horzOffset="0")
    _make(pic, HP + "outMargin", left="0", right="0", top="0", bottom="0")
    _make(run, HP + "t")


def _plain_border(header_root, border_id, cache):
    """바탕 그림이 있는 테두리/배경이면 그림을 뺀 복제 ID(머리글에 더한다). 그림이 없으면 그대로."""
    if header_root is None:
        return border_id
    if border_id in cache:
        return cache[border_id]
    fills = next((x for x in header_root.iter() if x.tag == HH + "borderFills"), None)
    source = next((x for x in (fills if fills is not None else []) if x.get("id") == border_id), None)
    if source is None or not any(x.tag == HC + "imgBrush" for x in source.iter()):
        cache[border_id] = border_id
        return border_id
    clone = copy.deepcopy(source)
    for brush in [x for x in clone if x.tag == HC + "fillBrush"]:
        for image in [x for x in brush if x.tag == HC + "imgBrush"]:
            brush.remove(image)
        if not len(brush):
            clone.remove(brush)
    new_id = str(max(int(x.get("id")) for x in fills if (x.get("id") or "").isdigit()) + 1)
    clone.set("id", new_id)
    fills.append(clone)
    fills.set("itemCnt", str(len(fills)))
    cache[border_id] = new_id
    return new_id


def apply(table, cells, spec, header_root=None) -> dict:
    """table(원본 표 XML)의 cells({(행, 열): 원래 방향})에 화살표를 넣는다. 그림이면 문서에 더할 파일 {이름: 바이트}."""
    spec = validate(spec)
    if spec is None or not cells:
        return {}
    wanted = dict(cells) if isinstance(cells, dict) else {key: "right" for key in cells}
    cache, used = {}, set()
    import itertools
    highest = max([int(v) for el in table.iter() for k, v in el.attrib.items()
                   if k in ("id", "instid") and str(v).isdigit() and int(v) < 2_000_000_000] + [1_000_000])
    ids = (str(n) for n in itertools.count(highest + 1))
    for tc in table.iter(HP + "tc"):
        addr = tc.find(HP + "cellAddr")
        key = (int(addr.get("rowAddr", -1)), int(addr.get("colAddr", -1))) if addr is not None else None
        if key not in wanted:
            continue
        run = _strip(tc)
        tc.set("borderFillIDRef", _plain_border(header_root, tc.get("borderFillIDRef"), cache))
        if spec["kind"] == "symbol":
            t = run.find(HP + "t")
            if t is None:
                t = _make(run, HP + "t")
            t.text = _turned(spec["value"], wanted[key])
        else:
            direction = wanted[key] if spec["direction"] == "auto" else spec["direction"]
            used.add(direction)
            _picture(run, tc, spec, direction, ids)
    return {f"BinData/{bin_id(d)}.png": image_png(spec["value"], d) for d in sorted(used)}


def add_to_manifest(content_hpf: bytes, names) -> bytes:
    """content.hpf 목록에 화살표 그림 항목들을 더한다(이미 있으면 그대로)."""
    import re
    text = content_hpf.decode("utf-8")
    # 목록 이름공간 접두어는 문서마다 다를 수 있다(opf: 등, 없을 수도 있음, Codex 검토 2026-10-30).
    match = re.search(r"</(?:([A-Za-z_][\w.-]*):)?manifest>", text)
    if not match:
        raise ValueError("문서 목록(content.hpf)을 읽지 못했습니다.")
    prefix = f"{match.group(1)}:" if match.group(1) else ""
    for name in names:
        item_id = Path(name).stem
        if f'id="{item_id}"' not in text:
            item = f'<{prefix}item id="{item_id}" href="{name}" media-type="image/png" isEmbeded="1"/>'
            at = text.rfind(match.group(0))
            text = text[:at] + item + text[at:]
    return text.encode("utf-8")
