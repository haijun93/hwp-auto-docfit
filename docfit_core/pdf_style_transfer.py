"""PDF 원본 서식을 kordoc 변환 HWPX에 옮겨 심는다(알파, 2026-10-10).

kordoc은 PDF를 마크다운으로 바꾼 뒤 프리셋 서식으로 HWPX를 새로 만든다. 이때 원본의
글꼴·크기·굵게·글자색·셀 배경색이 사라진다(실측: 재경부 업무보고 PDF에서 색 글자 0%,
배경색 글자 1.1%, 글꼴 0.3% 일치). 이 모듈은 PDF 글자마다 서식을 읽고(pdfium),
HWPX 글자와 순서대로 짝지어 같은 서식을 HWPX에 다시 적용한다.

- 글자: 서식이 바뀌는 곳에서 run을 나누고, 원래 글자 모양을 복제해 글꼴·크기·굵게·
  글자색만 바꾼 모양을 참조한다(같은 모양은 한 번만 만든다).
- 표 셀: 셀 안 글자 아래 PDF 채움 사각형 색의 다수결로 셀 배경을 정한다(배경 없음이 다수면 채움 제거).
- 표 밖 배경(색 띠 위 글자): 글자 음영(shadeColor)으로 옮긴다.
- 짝을 찾지 못한 글자는 같은 run 안 앞 글자의 서식을 따른다. 판단할 수 없으면 바꾸지 않는다.
"""

from __future__ import annotations

from collections import Counter
import copy
import ctypes
import difflib
import io
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from defusedxml import ElementTree as ET

from .batch_format import _serialize

# PDF에 박힌 글꼴 이름(부분 글꼴 접두사 제거 후) → 한/글 글꼴 이름
FONT_MAP = {
    "HCRBatang": "함초롬바탕", "HCRDotum": "함초롬돋움", "MalgunGothic": "맑은 고딕",
    "H2hdrM": "HY헤드라인M", "HaanYGodic24": "HY견고딕", "HYcysM": "HY중고딕",
    "Haansoft Batang": "한컴바탕", "HYhaeseo": "HY해서", "HYgtrE": "HY견고딕",
    "HYGothic-Medium": "HY중고딕", "HYMyeongJo-Medium": "HY신명조", "Batang": "바탕",
    "Dotum": "돋움", "Gulim": "굴림", "Gungsuh": "궁서", "NanumGothic": "나눔고딕",
    "NanumMyeongjo": "나눔명조", "HumanMyeongjo": "휴먼명조", "HCRBatangLVT": "함초롬바탕",
}
WHITE = "#FFFFFF"


def pdf_font(name: str) -> tuple[str, bool]:
    """PDF 글꼴 이름 → (한/글 글꼴 이름, 굵게). 굵게는 이름의 Bold로 판단한다(pdfium 굵기 값은 0이 많다)."""
    base = name.split("+", 1)[-1]
    bold = bool(re.search(r"bold", base, re.I))
    base = re.sub(r"[-,]?(Bold|Regular)$", "", base, flags=re.I)
    return FONT_MAP.get(base, base), bold


def _color(getter, raw) -> str:
    r, g, b, a = (ctypes.c_uint() for _ in range(4))
    getter(raw, *(ctypes.byref(x) for x in (r, g, b, a)))
    return "#%02X%02X%02X" % (r.value, g.value, b.value)


def _skip(ch: str) -> bool:
    return ord(ch) < 33 or ch in "　 "


def pdf_characters(path: str | Path) -> list[tuple[str, dict]]:
    """PDF의 보이는 글자마다 (글자, {font, size, bold, color, bg, page}). 공백은 뺀다."""
    import pypdfium2 as pdfium
    import pypdfium2.raw as R

    doc = pdfium.PdfDocument(str(path))
    out = []
    buf = ctypes.create_string_buffer(256)
    try:
        for index in range(len(doc)):
            page = doc[index]
            rects = []
            for obj in page.get_objects(max_depth=3):
                if obj.type != R.FPDF_PAGEOBJ_PATH:
                    continue
                fill, stroke = ctypes.c_int(), ctypes.c_int()
                R.FPDFPath_GetDrawMode(obj.raw, ctypes.byref(fill), ctypes.byref(stroke))
                if not fill.value:
                    continue
                color = _color(R.FPDFPageObj_GetFillColor, obj.raw)
                x0, y0, x1, y1 = obj.get_bounds()
                if x1 - x0 > 6 and y1 - y0 > 6 and color != WHITE:
                    rects.append(((x1 - x0) * (y1 - y0), x0, y0, x1, y1, color))
            rects.sort()                     # 안쪽(작은) 사각형을 먼저 본다
            text = page.get_textpage()
            for i in range(R.FPDFText_CountChars(text)):
                ch = chr(R.FPDFText_GetUnicode(text, i))
                if _skip(ch):
                    continue
                flags = ctypes.c_int()
                n = R.FPDFText_GetFontInfo(text, i, buf, 256, ctypes.byref(flags))
                font, bold = pdf_font(buf.raw[:max(n - 1, 0)].decode("utf-8", "replace"))
                # 글자 크기: 텍스트 행렬 배율을 반영한 실제 크기(pt). 0.5pt 단위로 맞춘다.
                size, ratio = _char_size(R, page, text, i)
                r, g, b, a = (ctypes.c_uint() for _ in range(4))
                R.FPDFText_GetFillColor(text, i, *(ctypes.byref(x) for x in (r, g, b, a)))
                color = "#%02X%02X%02X" % (r.value, g.value, b.value)
                left, bottom, right, top = text.get_charbox(i)
                cx, cy = (left + right) / 2, (bottom + top) / 2
                bg = next((c for _, x0, y0, x1, y1, c in rects if x0 <= cx <= x1 and y0 <= cy <= y1), None)
                out.append((ch, {"font": font, "size": size, "bold": bold, "color": color,
                                 "bg": bg, "ratio": ratio, "page": index + 1}))
    finally:
        doc.close()
    return out


def _char_size(R, page, text, i) -> tuple[float, int]:
    """(글자 크기 pt, 장평 %). 크기는 세로 배율, 장평은 가로/세로 배율 비로 구한다."""
    obj = R.FPDFText_GetTextObject(text, i) if hasattr(R, "FPDFText_GetTextObject") else None
    size, ratio = R.FPDFText_GetFontSize(text, i), 100
    if obj:
        value = ctypes.c_float()
        if R.FPDFTextObj_GetFontSize(obj, ctypes.byref(value)):
            m = R.FS_MATRIX()
            if R.FPDFPageObj_GetMatrix(obj, ctypes.byref(m)):
                sx = (m.a * m.a + m.b * m.b) ** 0.5
                sy = (m.c * m.c + m.d * m.d) ** 0.5
                if sy > 0:
                    size = value.value * sy
                    ratio = int(round(sx / sy * 100))
    return round(size * 2) / 2, ratio


def _tag(e) -> str:
    return e.tag.rsplit("}", 1)[-1]


class _Pool:
    """글자 모양·테두리/배경 복제 저장소(같은 조합은 한 번만 만든다)."""

    def __init__(self, header):
        self.header = header
        self.char_group = next(x for x in header.iter() if _tag(x) == "charProperties")
        self.fill_group = next(x for x in header.iter() if _tag(x) == "borderFills")
        self.chars = {x.get("id"): x for x in self.char_group}
        self.fills = {x.get("id"): x for x in self.fill_group}
        self.fonts = {x.get("lang", "").lower(): x for x in header.iter() if _tag(x) == "fontface"}
        self.made_chars, self.made_fills = {}, {}
        self.new_chars = self.new_fills = 0

    @staticmethod
    def _append(group, shape, count_attr="itemCnt"):
        shape.set("id", str(1 + max((int(x.get("id")) for x in group), default=0)))
        group.append(shape)
        group.set(count_attr, str(len(group)))
        return shape.get("id")

    def font_id(self, lang, face):
        group = self.fonts.get(lang)
        if group is None or not len(group):
            return None
        found = next((x for x in group if x.get("face") == face), None)
        if found is None:
            found = copy.deepcopy(group[0])
            found.set("face", face)
            found.set("type", "TTF")
            found.set("isEmbedded", "0")
            for element in list(found):
                if _tag(element) != "typeInfo":
                    found.remove(element)
            found.set("id", str(1 + max(int(x.get("id")) for x in group)))
            group.append(found)
            group.set("fontCnt", str(len(group)))
        return found.get("id")

    def char(self, base_id, style):
        key = (base_id, style.get("font"), style.get("size"), style.get("bold"), style.get("color"),
               style.get("shade"), style.get("ratio"))
        if key in self.made_chars:
            return self.made_chars[key]
        source = self.chars.get(base_id)
        if source is None:
            return base_id
        shape = copy.deepcopy(source)
        if style.get("size"):
            shape.set("height", str(int(round(style["size"] * 100))))
        if style.get("color"):
            shape.set("textColor", style["color"])
        if style.get("ratio"):
            ratio = next((x for x in shape if _tag(x) == "ratio"), None)
            if ratio is not None:
                for lang in list(ratio.attrib):
                    ratio.set(lang, str(max(50, min(200, style["ratio"]))))
        shape.set("shadeColor", style.get("shade") or "none")
        if style.get("font"):
            ref = next((x for x in shape if _tag(x) == "fontRef"), None)
            if ref is not None:
                for lang in list(ref.attrib):
                    fid = self.font_id(lang, style["font"])
                    if fid is not None:
                        ref.set(lang, fid)
        if style.get("bold") is not None:
            bold = next((x for x in shape if _tag(x) == "bold"), None)
            if style["bold"]:
                if bold is None:
                    ns = shape.tag.rsplit("}", 1)[0] + "}"
                    pos = next((i for i, x in enumerate(shape) if _tag(x) in (
                        "italic", "underline", "strikeout", "outline", "shadow", "emboss", "engrave",
                        "supscript", "subscript")), len(shape))
                    shape.insert(pos, type(shape)(ns + "bold", {}))
                if "bold" in shape.attrib:
                    shape.set("bold", "1")
            else:
                if bold is not None:
                    shape.remove(bold)
                shape.attrib.pop("bold", None)
        probe = copy.deepcopy(shape)
        probe.set("id", base_id)
        if ET.tostring(probe) == ET.tostring(source):
            result = base_id
        else:
            result = self._append(self.char_group, shape)
            self.chars[result] = shape
            self.new_chars += 1
        self.made_chars[key] = result
        return result

    def fill(self, base_id, color):
        """base 테두리/배경을 복제해 면 색만 color(None이면 채움 없음)로 바꾼 ID."""
        key = (base_id, color)
        if key in self.made_fills:
            return self.made_fills[key]
        source = self.fills.get(base_id)
        if source is None:
            return base_id
        current = _fill_color(source)
        if current == color:
            self.made_fills[key] = base_id
            return base_id
        shape = copy.deepcopy(source)
        brush = next((x for x in shape.iter() if _tag(x) == "fillBrush"), None)
        if color is None:
            if brush is not None:
                shape.remove(brush)
        else:
            ns_core = "{http://www.hancom.co.kr/hwpml/2011/core}"
            if brush is None:
                brush = type(shape)(ns_core + "fillBrush", {})
                shape.append(brush)
            win = next((x for x in brush if _tag(x) == "winBrush"), None)
            if win is None:
                for element in list(brush):
                    brush.remove(element)
                win = type(shape)(ns_core + "winBrush", {"faceColor": color, "hatchColor": "#999999", "alpha": "0"})
                brush.append(win)
            win.set("faceColor", color)
        result = self._append(self.fill_group, shape)
        self.fills[result] = shape
        self.new_fills += 1
        self.made_fills[key] = result
        return result


def _fill_color(border_fill):
    win = next((x for x in border_fill.iter() if _tag(x) == "winBrush"), None)
    face = win.get("faceColor") if win is not None else None
    return None if face in (None, "none") or face.upper() == WHITE else face.upper()


def _collect(roots):
    """문서 순서대로 HWPX 글자 [(글자, t요소, t 안 위치, run, tc)]. 자식 요소가 있는 t는 run 전체 단위로 다룬다."""
    out = []

    def walk(e, run, cell):
        name = _tag(e)
        if name == "tc":
            cell = e
        elif name == "run":
            run = e
        if name == "t":
            for pos, ch in enumerate("".join(e.itertext())):
                if not _skip(ch):
                    out.append((ch, e, pos, run, cell))
            return
        for c in e:
            walk(c, run, cell)
    for root in roots:
        walk(root, None, None)
    return out


def _style_of(attr, in_cell):
    style = {"font": attr["font"], "size": attr["size"], "bold": attr["bold"], "color": attr["color"],
             "ratio": attr.get("ratio")}
    # 표 밖 글자의 배경 띠는 글자 음영으로 옮긴다(셀 배경은 셀에서 처리).
    style["shade"] = attr["bg"] if (attr["bg"] and not in_cell) else None
    return style


def transfer(pdf_chars: list, hwpx_in: str | Path, hwpx_out: str | Path) -> dict:
    """pdf_chars(pdf_characters 결과)의 서식을 hwpx_in에 옮겨 hwpx_out으로 저장. 통계를 돌려준다."""
    with ZipFile(hwpx_in) as z:
        infos = z.infolist()
        data = {i.filename: z.read(i.filename) for i in infos}
    names = sorted(n for n in data if re.match(r"Contents/section\d+\.xml$", n))
    header = ET.fromstring(data["Contents/header.xml"])
    roots = [ET.fromstring(data[n]) for n in names]
    pool = _Pool(header)
    chars = _collect(roots)

    a = "".join(c for c, _ in pdf_chars)
    b = "".join(c[0] for c in chars)
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    target = [None] * len(chars)
    used = [False] * len(a)
    for i, j, n in matcher.get_matching_blocks():
        for k in range(n):
            target[j + k] = pdf_chars[i + k][1]
            used[i + k] = True
    # 2차: kordoc이 순서를 옮긴 글(예: 목차 제목을 문서 앞 표로)은 1차 짝짓기에서 빠진다.
    # 짝 없는 HWPX 글자 묶음(2자 이상)을 PDF의 아직 짝 없는 글자에서 같은 글로 다시 찾는다.
    free = "".join(ch if not used[i] else " " for i, ch in enumerate(a))
    j = 0
    while j < len(chars):
        if target[j] is not None:
            j += 1
            continue
        end = j
        while end < len(chars) and target[end] is None:
            end += 1
        piece = b[j:end]
        at = free.find(piece) if len(piece) >= 2 else -1
        if at >= 0:
            for k in range(len(piece)):
                target[j + k] = pdf_chars[at + k][1]
            free = free[:at] + " " * len(piece) + free[at + len(piece):]
        j = end
    matched = sum(1 for t in target if t is not None)

    # 짝 없는 글자는 같은 run 안 앞(없으면 뒤) 글자 서식을 따른다.
    by_run = {}
    for idx, c in enumerate(chars):
        by_run.setdefault(id(c[3]), []).append(idx)
    for idxs in by_run.values():
        last = None
        for idx in idxs:
            if target[idx] is None:
                target[idx] = last
            else:
                last = target[idx]
        nxt = None
        for idx in reversed(idxs):
            if target[idx] is None:
                target[idx] = nxt
            else:
                nxt = target[idx]

    # 셀 배경: 셀 안 글자의 PDF 배경 다수결
    cell_votes = {}
    for idx, c in enumerate(chars):
        if c[4] is not None and target[idx] is not None:
            cell_votes.setdefault(id(c[4]), (c[4], Counter()))[1][target[idx]["bg"]] += 1
    cells_changed = 0
    for cell, votes in cell_votes.values():
        color, count = votes.most_common(1)[0]
        if count * 2 < sum(votes.values()):
            continue
        base = cell.get("borderFillIDRef")
        new = pool.fill(base, color)
        if new != base:
            cell.set("borderFillIDRef", new)
            cells_changed += 1

    # 글자: run마다 글자·요소 토큰으로 펼쳐 서식이 바뀌는 곳에서 run을 나눈다.
    per_run = {}
    for idx, c in enumerate(chars):
        if c[3] is not None:
            per_run.setdefault(id(c[3]), (c[3], c[4], {}))[2][(id(c[1]), c[2])] = target[idx]
    runs_split = chars_styled = 0
    for run, cell, styled in per_run.values():
        if not any(styled.values()):
            continue
        base = run.get("charPrIDRef")
        in_cell = cell is not None
        if any(_tag(x) != "t" for x in run):
            # 컨트롤(표·그림·구역 정의 등)이 든 run은 나누지 않고 다수 서식을 run 전체에 적용
            votes = Counter(tuple(sorted(_style_of(v, in_cell).items())) for v in styled.values() if v)
            run.set("charPrIDRef", pool.char(base, dict(votes.most_common(1)[0][0])))
            chars_styled += len(styled)
            continue
        # 토큰: ("c", 글자, 서식키) 또는 ("e", 요소, None). 요소(탭·줄바꿈)와 공백은 앞 글자 서식을 따른다.
        tokens = []
        for t in run:
            pos = 0
            def add_text(value):
                nonlocal pos
                for ch in value or "":
                    attr = styled.get((id(t), pos))
                    tokens.append(["c", ch, tuple(sorted(_style_of(attr, in_cell).items())) if attr else None])
                    pos += 1
            add_text(t.text)
            for child in t:
                tokens.append(["e", child, None])
                pos += len("".join(child.itertext()))
                add_text(child.tail)
        last = next((tk[2] for tk in tokens if tk[2]), None)
        for tk in tokens:
            if tk[2] is None:
                tk[2] = last
            else:
                last = tk[2]
        groups = []
        for tk in tokens:
            if groups and groups[-1][0] == tk[2]:
                groups[-1][1].append(tk)
            else:
                groups.append((tk[2], [tk]))
        if len(groups) == 1:
            run.set("charPrIDRef", pool.char(base, dict(groups[0][0])) if groups[0][0] else base)
            chars_styled += len(styled)
            continue
        parent = _parent_of(roots, run)
        if parent is None:
            continue
        index = list(parent).index(run)
        t_template = next(x for x in run if _tag(x) == "t")
        new_runs = []
        for key, items in groups:
            new = copy.deepcopy(run)
            for x in list(new):
                new.remove(x)
            t = type(t_template)(t_template.tag, dict(t_template.attrib))
            t.text = ""
            tail_target = None
            for kind, value, _ in items:
                if kind == "c":
                    if tail_target is None:
                        t.text += value
                    else:
                        tail_target.tail = (tail_target.tail or "") + value
                else:
                    element = copy.deepcopy(value)
                    element.tail = None
                    t.append(element)
                    tail_target = element
            new.append(t)
            new.set("charPrIDRef", pool.char(base, dict(key)) if key else base)
            new_runs.append(new)
        parent.remove(run)
        for offset, new in enumerate(new_runs):
            parent.insert(index + offset, new)
        runs_split += len(new_runs) - 1
        chars_styled += len(styled)

    data["Contents/header.xml"] = _serialize(header, data["Contents/header.xml"])
    for name, root in zip(names, roots):
        data[name] = _serialize(root, data[name])
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as out:
        for info in infos:
            kind = ZIP_STORED if info.filename == "mimetype" else ZIP_DEFLATED
            out.writestr(info.filename, data[info.filename], compress_type=kind)
    Path(hwpx_out).write_bytes(buffer.getvalue())
    return {"pdf_chars": len(a), "hwpx_chars": len(b), "matched": matched,
            "chars_styled": chars_styled, "runs_split": runs_split, "cells_filled": cells_changed,
            "new_char_shapes": pool.new_chars, "new_fills": pool.new_fills}


_PARENTS = {}


def _parent_of(roots, element):
    key = id(roots[0]) if roots else None
    parents = _PARENTS.get(key)
    if parents is None or element not in parents:
        parents = {c: p for root in roots for p in root.iter() for c in p}
        _PARENTS.clear()
        _PARENTS[key] = parents
    return parents.get(element)


def transfer_pdf_style(pdf_path: str | Path, hwpx_in: str | Path, hwpx_out: str | Path | None = None) -> dict:
    """PDF 서식을 읽어 HWPX에 옮긴다(hwpx_out이 없으면 덮어쓴다)."""
    return transfer(pdf_characters(pdf_path), hwpx_in, hwpx_out or hwpx_in)
