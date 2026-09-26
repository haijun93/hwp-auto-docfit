"""HWPX 문서 스타일 전수 분석과 예시 서식 문서 생성.

``hwpx_서식_분석``은 서식 복제를 위해 기호별 *대표값* 하나만 고른다. 이 모듈은
문서에 정의된 모든 서식 요소(글꼴·문자 모양·문단 모양·스타일·테두리/배경·번호·탭)를
해석하고, 본문·표·머리말에서 실제로 쓰인 횟수와 예문을 붙여 전체 목록을 만든다.

본문 문단은 "문두기호 + 문단 모양 + 문자 모양 순서" 조합으로 묶는다. 같은 조합이면
한/글에서 같은 모양으로 보이므로, 조합 목록이 곧 문서가 쓰는 스타일 목록이다.

``build_style_sample``은 원본 header.xml을 그대로 두고 본문만 조합별 대표 문단과
모양이 다른 표 하나씩으로 줄인 HWPX를 만든다. 문서 순서를 유지하므로 이 파일을
서식 예시로 분석해도 제목·대표 서식이 원본과 같게 잡힌다.
"""

from __future__ import annotations

from collections import Counter, OrderedDict, defaultdict
import copy
import io
import math
from pathlib import Path
import re
import xml.etree.ElementTree as StdET
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from defusedxml import ElementTree as ET

from .hwpx import validate_hwpx
from .style_hierarchy import leading_marker

HWPUNIT_PER_MM = 7200 / 25.4
LANGS = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")
ALIGN_LABELS = {"JUSTIFY": "양쪽", "LEFT": "왼쪽", "RIGHT": "오른쪽", "CENTER": "가운데",
                "DISTRIBUTE": "배분", "DISTRIBUTE_SPACE": "나눔"}
# 예시 문서에 남길 본문 문단 수(대략)와 유형별 상한. 유형별 문단 수를 원본 빈도에
# 비례시켜야 예시를 다시 분석해도 대표 본문·기호별 대표 서식이 원본과 같게 나온다.
SAMPLE_BUDGET = 50
SAMPLES_PER_TYPE = 20
# 문단 텍스트가 필요 없는 머리말·꼬리말·쪽 번호 등 쪽 단위 컨트롤
PAGE_CONTROLS = {"header", "footer", "pageNum", "pageHiding", "newNum", "autoNum"}


def _tag(e) -> str:
    return e.tag.rsplit("}", 1)[-1]


def _first(e, name):
    """hp:switch가 있으면 hp:case(HwpUnitChar) 값을 먼저 만난다(기존 분석기와 동일)."""
    if e is None:
        return None
    return next((x for x in e.iter() if _tag(x) == name), None)


def _mm(value) -> float:
    try:
        return round(float(value) / HWPUNIT_PER_MM, 1)
    except (TypeError, ValueError):
        return 0.0


def _text_of(e) -> str:
    parts = []
    for x in e.iter():
        name = _tag(x)
        if name == "t":
            parts.append(x.text or "")
            for sub in x:
                if _tag(sub) in ("fwSpace", "nbSpace", "tab"):
                    parts.append(" ")
                parts.append(sub.tail or "")
    return "".join(parts)


def _run_text(run) -> str:
    return "".join(_text_of(t) for t in run if _tag(t) == "t")


# ----------------------------------------------------------------------------
# header.xml 정의 해석
# ----------------------------------------------------------------------------

def _parse_fonts(header):
    fonts = {}
    for face in header.iter():
        if _tag(face) == "fontface":
            lang = (face.get("lang") or "").lower()
            fonts[lang] = {f.get("id"): f.get("face") for f in face if _tag(f) == "font"}
    return fonts


def _lang_values(e, cast=int):
    if e is None:
        return {}
    out = {}
    for lang in LANGS:
        if e.get(lang) is not None:
            try:
                out[lang] = cast(e.get(lang))
            except ValueError:
                out[lang] = e.get(lang)
    return out


def _shade(value):
    """글자 음영색. 'none'과 흰색은 음영 없음(None)으로 본다."""
    value = (value or "none").upper()
    return None if value in ("NONE", "#FFFFFF") else value


def _parse_char(e, fonts):
    ref = _lang_values(_first(e, "fontRef"), str)
    underline = _first(e, "underline")
    strike = _first(e, "strikeout")
    outline = _first(e, "outline")
    shadow = _first(e, "shadow")
    return {
        "id": e.get("id"),
        "font": {lang: fonts.get(lang, {}).get(ref.get(lang))
                 for lang in ("hangul", "latin", "hanja")},
        "size_pt": int(e.get("height", "0")) / 100,
        "color": e.get("textColor", "#000000"),
        "shade": _shade(e.get("shadeColor")),
        "bold": _first(e, "bold") is not None,
        "italic": _first(e, "italic") is not None,
        "underline": underline.get("type", "NONE") if underline is not None else "NONE",
        "strikeout": strike.get("shape", "NONE") if strike is not None else "NONE",
        "outline": outline.get("type", "NONE") if outline is not None else "NONE",
        "shadow": shadow.get("type", "NONE") if shadow is not None else "NONE",
        "superscript": _first(e, "supscript") is not None,
        "subscript": _first(e, "subscript") is not None,
        "ratio": _lang_values(_first(e, "ratio")).get("hangul", 100),
        "spacing": _lang_values(_first(e, "spacing")).get("hangul", 0),
        "rel_size": _lang_values(_first(e, "relSz")).get("hangul", 100),
        "offset": _lang_values(_first(e, "offset")).get("hangul", 0),
        "border_fill": e.get("borderFillIDRef"),
    }


def _parse_para(e):
    align = _first(e, "align")
    heading = _first(e, "heading")
    brk = _first(e, "breakSetting")
    margin = _first(e, "margin")
    ls = _first(e, "lineSpacing")
    border = _first(e, "border")

    def m(name):
        item = _first(margin, name)
        return int(item.get("value", "0")) if item is not None else 0

    return {
        "id": e.get("id"),
        "align": (align.get("horizontal") if align is not None else "JUSTIFY"),
        "heading": ({"type": heading.get("type"), "level": int(heading.get("level", "0")),
                     "numbering": heading.get("idRef")}
                    if heading is not None and heading.get("type", "NONE") != "NONE" else None),
        "left": m("left"), "right": m("right"), "indent": m("intent"),
        "prev": m("prev"), "next": m("next"),
        "line_spacing": ({"type": ls.get("type"), "value": int(float(ls.get("value", "0")))}
                         if ls is not None else None),
        "tab": e.get("tabPrIDRef"),
        "border_fill": border.get("borderFillIDRef") if border is not None else None,
        "keep_with_next": brk is not None and brk.get("keepWithNext") == "1",
        "keep_lines": brk is not None and brk.get("keepLines") == "1",
        "page_break_before": brk is not None and brk.get("pageBreakBefore") == "1",
        "widow_orphan": brk is not None and brk.get("widowOrphan") == "1",
        "break_word": (brk.get("breakNonLatinWord") if brk is not None else None),
        "snap_to_grid": e.get("snapToGrid") == "1",
        "condense": int(e.get("condense", "0") or 0),
    }


def _parse_border_fill(e):
    sides = {}
    for side in ("leftBorder", "rightBorder", "topBorder", "bottomBorder", "diagonal"):
        x = _first(e, side)
        if x is not None:
            sides[side.replace("Border", "")] = {"type": x.get("type"), "width": x.get("width"),
                                                 "color": x.get("color")}
    fill = None
    win = _first(e, "winBrush")
    grad = _first(e, "gradation")
    if win is not None and win.get("faceColor") not in (None, "none"):
        fill = {"kind": "단색", "color": win.get("faceColor")}
    elif grad is not None:
        fill = {"kind": "그러데이션", "colors": [c.get("value") for c in grad if _tag(c) == "color"]}
    return {"id": e.get("id"), "borders": sides, "fill": fill}


def _parse_numbering(e):
    levels = []
    for head in e:
        if _tag(head) == "paraHead":
            levels.append({"level": int(head.get("level", "0")), "format": head.get("numFormat"),
                           "text": head.text or "", "start": head.get("start")})
    return {"id": e.get("id"), "start": e.get("start"), "levels": levels}


def _parse_tab(e):
    items = [{"pos_mm": _mm(t.get("pos")), "type": t.get("type"), "leader": t.get("leader")}
             for t in e.iter() if _tag(t) == "tabItem"]
    return {"id": e.get("id"), "auto_left": e.get("autoTabLeft") == "1",
            "auto_right": e.get("autoTabRight") == "1", "items": items}


def parse_header(header) -> dict:
    fonts = _parse_fonts(header)
    defs = {"fonts": fonts, "chars": OrderedDict(), "paras": OrderedDict(),
            "styles": OrderedDict(), "border_fills": OrderedDict(),
            "numberings": OrderedDict(), "bullets": OrderedDict(), "tabs": OrderedDict()}
    for e in header.iter():
        name = _tag(e)
        if name == "charPr":
            defs["chars"][e.get("id")] = _parse_char(e, fonts)
        elif name == "paraPr":
            defs["paras"][e.get("id")] = _parse_para(e)
        elif name == "style":
            defs["styles"][e.get("id")] = {
                "id": e.get("id"), "type": e.get("type"), "name": e.get("name"),
                "eng_name": e.get("engName"), "para": e.get("paraPrIDRef"),
                "char": e.get("charPrIDRef"), "next": e.get("nextStyleIDRef")}
        elif name == "borderFill":
            defs["border_fills"][e.get("id")] = _parse_border_fill(e)
        elif name == "numbering":
            defs["numberings"][e.get("id")] = _parse_numbering(e)
        elif name == "bullet":
            defs["bullets"][e.get("id")] = {"id": e.get("id"), "char": e.get("char")}
        elif name == "tabPr":
            defs["tabs"][e.get("id")] = _parse_tab(e)
    return defs


# ----------------------------------------------------------------------------
# 본문 사용 현황
# ----------------------------------------------------------------------------

def _sections(z: ZipFile):
    names = [n for n in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)]
    return sorted(names, key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[-1]).group(1)))


def _walk(element, context, out):
    """모든 문단을 (문단, 문맥) 순서로 모은다. 문맥: 본문/표/머리말·꼬리말/주석/글상자."""
    for child in element:
        name = _tag(child)
        if name == "p":
            out.append((child, context))
            _walk(child, context, out)
        elif name == "tbl":
            _walk(child, "표", out)
        elif name in ("header", "footer"):
            _walk(child, "머리말·꼬리말", out)
        elif name in ("footNote", "endNote"):
            _walk(child, "각주·미주", out)
        elif name in ("rect", "ellipse", "polygon", "curve", "container", "drawText"):
            _walk(child, "글상자" if context == "본문" else context, out)
        else:
            _walk(child, context, out)


def _paragraph_runs(para):
    return [run for run in para if _tag(run) == "run"]


def _char_signature(runs, chars):
    """글자가 있는 런의 문자 모양 순서(연속 중복 제거)와 대표(가장 긴) 문자 모양."""
    seq, lengths = [], Counter()
    for run in runs:
        text = _run_text(run)
        if not text.strip():
            continue
        cid = run.get("charPrIDRef")
        lengths[cid] += len(text.strip())
        if not seq or seq[-1] != cid:
            seq.append(cid)
    main = lengths.most_common(1)[0][0] if lengths else None
    return tuple(seq), main


def _table_signature(tbl, chars=None):
    """표 종류 판정: 테두리/배경, 열 수, 첫 행 글자 겉모습, 본문 폭 여부.

    자간·너비 미세값처럼 줄 맞춤으로 달라지는 값은 넣지 않는다.
    """
    chars = chars or {}
    cells = [c for c in tbl.iter() if _tag(c) == "tc"]
    rows = [r for r in tbl.iter() if _tag(r) == "tr"]
    first_row = [c for c in rows[0] if _tag(c) == "tc"] if rows else []

    def look(cid):
        c = chars.get(cid)
        return (c["font"].get("hangul"), c["size_pt"], c["bold"], c["color"].upper()) if c else cid

    # 번호 글자처럼 몇 글자만 다른 모양은 무시하고 첫 행의 주된 글자 모양만 본다.
    looks = Counter()
    for r in (r for c in first_row for r in c.iter() if _tag(r) == "run"):
        looks[look(r.get("charPrIDRef"))] += len(_run_text(r).strip())
    first_row_chars = _mode(+looks)
    cell_fills = tuple(sorted({c.get("borderFillIDRef") for c in cells}))
    sz = _first(tbl, "sz")
    wide = sz is not None and _mm(sz.get("width")) > 120
    return (tbl.get("colCnt"), tbl.get("borderFillIDRef"), cell_fills, first_row_chars, wide)


def _table_info(tbl, chars):
    cells = [c for c in tbl.iter() if _tag(c) == "tc"]
    rows = [r for r in tbl.iter() if _tag(r) == "tr"]
    sz = _first(tbl, "sz")
    cm = Counter()
    for c in cells:
        m = next((x for x in c if _tag(x) == "cellMargin"), None)
        if m is not None:
            cm[tuple(_mm(m.get(k)) for k in ("left", "right", "top", "bottom"))] += 1
    first = rows[0] if rows else None
    head_chars, body_chars = Counter(), Counter()
    for index, row in enumerate(rows):
        bucket = head_chars if index == 0 else body_chars
        for run in (r for r in row.iter() if _tag(r) == "run"):
            text = _run_text(run).strip()
            if text:
                bucket[run.get("charPrIDRef")] += len(text)
    return {
        "rows": int(tbl.get("rowCnt", len(rows)) or len(rows)),
        "cols": int(tbl.get("colCnt", 0) or 0),
        "width_mm": _mm(sz.get("width")) if sz is not None else None,
        "table_border_fill": tbl.get("borderFillIDRef"),
        "cell_border_fills": dict(Counter(c.get("borderFillIDRef") for c in cells)),
        "cell_margin_mm": list(cm.most_common(1)[0][0]) if cm else None,
        "header_chars": [cid for cid, _ in head_chars.most_common()],
        "body_chars": [cid for cid, _ in body_chars.most_common()],
        "first_row": " | ".join(_text_of(c).strip() for c in first if _tag(c) == "tc")[:120]
        if first is not None else "",
    }


def _marker_class(marker: str) -> str:
    """번호만 다른 문두기호(1. 2. / 가. 나. / ① ②)는 같은 기호로 본다."""
    if not marker:
        return "(없음)"
    if re.match(r"[①-⑳]", marker):
        return "①"
    if re.match(r"[㉠-㉻]", marker):
        return "㉠"
    marker = re.sub(r"\d+", "1", marker)
    return re.sub(r"^[가-하]", "가", marker)


def inline_effects(main, other):
    """주 문자 모양과 다른 부분 서식: 위첨자·아래첨자·글자색·굵게 등."""
    if not main or not other:
        return set()
    out = set()
    if other["superscript"]:
        out.add("위첨자")
    if other["subscript"]:
        out.add("아래첨자")
    if other["color"].upper() != main["color"].upper():
        out.add(f"글자색 {other['color'].upper()}")
    if other["shade"] and other["shade"] != main["shade"]:
        out.add(f"음영 {other['shade']}")
    if other["bold"] and not main["bold"]:
        out.add("굵게")
    if other["italic"] and not main["italic"]:
        out.add("기울임")
    if other["underline"] != "NONE" and main["underline"] == "NONE":
        out.add("밑줄")
    return out


def paragraph_style_type(para, defs):
    """본문 문단의 스타일 유형 키와 측정값. 글자가 없으면 None.

    자간·줄간격·내어쓰기 미세값은 줄 맞춤(자간 조정·쪽 맞춤) 흔적이라 키에서 빼고
    측정값으로만 돌려준다.
    """
    runs = _paragraph_runs(para)
    text = "".join(_run_text(r) for r in runs)
    if not text.strip():
        return None
    chars, paras = defs["chars"], defs["paras"]
    seq, main = _char_signature(runs, chars)
    c, p = chars.get(main), paras.get(para.get("paraPrIDRef"))
    if c is None or p is None:
        return None
    marker, role = leading_marker(text)
    emphasis = any(chars.get(cid, {}).get("bold") for cid in seq) and not c["bold"]
    effects = set()
    for cid in seq:
        if cid != main:
            effects |= inline_effects(c, chars.get(cid))
    key = (_marker_class(marker), c["font"].get("hangul"), c["size_pt"], c["bold"], c["italic"],
           c["underline"], c["color"].upper(), c["shade"], c["ratio"], p["align"], round(_mm(p["left"])))
    ls = p["line_spacing"]
    return key, {
        "marker": _marker_class(marker), "role": role, "main_char": main,
        "para": para.get("paraPrIDRef"), "style": para.get("styleIDRef"), "char_seq": seq,
        "spacing": c["spacing"], "indent_mm": _mm(p["indent"]), "prev_pt": p["prev"] / 100,
        "line": ls["value"] if ls and ls["type"] == "PERCENT" else None,
        "emphasis": emphasis, "effects": tuple(sorted(effects)), "text": text.strip(),
    }


def _mode(counter, default=None):
    return counter.most_common(1)[0][0] if counter else default


def analyze_style_inventory(path) -> dict:
    """HWPX 파일에 정의·사용된 모든 스타일 요소를 분석한다."""
    path = Path(path)
    validate_hwpx(path)
    with ZipFile(path) as z:
        header = ET.fromstring(z.read("Contents/header.xml"))
        defs = parse_header(header)
        chars, paras = defs["chars"], defs["paras"]
        page = None
        char_use = defaultdict(lambda: {"chars": 0, "runs": 0, "contexts": Counter(), "sample": ""})
        para_use = defaultdict(lambda: {"count": 0, "contexts": Counter(), "sample": ""})
        style_use = Counter()
        border_use = defaultdict(set)
        combos = OrderedDict()
        types = OrderedDict()
        effects_use = OrderedDict()
        shade_use = OrderedDict()
        tables = OrderedDict()
        total_paragraphs = 0

        for name in _sections(z):
            root = ET.fromstring(z.read(name))
            if page is None:
                pp = _first(root, "pagePr")
                if pp is not None:
                    margin = _first(pp, "margin")
                    page = {"width_mm": _mm(pp.get("width")), "height_mm": _mm(pp.get("height")),
                            "orientation": "가로" if pp.get("landscape") == "NARROWLY" else "세로",
                            "margin_mm": {k: _mm(margin.get(k)) for k in
                                          ("left", "right", "top", "bottom", "header", "footer", "gutter")}
                            if margin is not None else {}}
            items = []
            _walk(root, "본문", items)
            for para, context in items:
                total_paragraphs += 1
                pid, sid = para.get("paraPrIDRef"), para.get("styleIDRef")
                runs = _paragraph_runs(para)
                text = "".join(_run_text(r) for r in runs)
                use = para_use[pid]
                use["count"] += 1
                use["contexts"][context] += 1
                if text.strip() and not use["sample"]:
                    use["sample"] = text.strip()[:60]
                style_use[sid] += 1
                if paras.get(pid, {}).get("border_fill"):
                    border_use[paras[pid]["border_fill"]].add("문단 테두리")
                for run in runs:
                    rt = _run_text(run)
                    shade = chars.get(run.get("charPrIDRef"), {}).get("shade")
                    if shade and rt.strip():
                        su = shade_use.setdefault(shade, {"runs": 0, "chars": 0, "char_ids": set(),
                                                          "contexts": Counter(), "samples": []})
                        su["runs"] += 1
                        su["chars"] += len(rt.strip())
                        su["char_ids"].add(run.get("charPrIDRef"))
                        su["contexts"][context] += 1
                        if len(su["samples"]) < 3:
                            su["samples"].append({"part": rt.strip()[:20], "text": text.strip()[:60]})
                    cu = char_use[run.get("charPrIDRef")]
                    cu["runs"] += 1
                    cu["chars"] += len(rt.strip())
                    if rt.strip():
                        cu["contexts"][context] += len(rt.strip())
                        if not cu["sample"]:
                            cu["sample"] = rt.strip()[:40]
                    for tbl in (x for x in run if _tag(x) == "tbl"):
                        sig = _table_signature(tbl, chars)
                        info = tables.get(sig)
                        if info is None:
                            info = _table_info(tbl, chars)
                            info["count"] = 0
                            info["context"] = context
                            tables[sig] = info
                        info["count"] += 1
                        border_use[tbl.get("borderFillIDRef")].add("표")
                        for c in tbl.iter():
                            if _tag(c) == "tc":
                                border_use[c.get("borderFillIDRef")].add("표 셀")
                seq_all, main_all = _char_signature(runs, chars)
                for run in runs:
                    rt = _run_text(run).strip()
                    cid = run.get("charPrIDRef")
                    if not rt or cid == main_all:
                        continue
                    for effect in inline_effects(chars.get(main_all), chars.get(cid)):
                        e = effects_use.setdefault(effect, {"runs": 0, "chars": 0, "contexts": Counter(), "samples": []})
                        e["runs"] += 1
                        e["chars"] += len(rt)
                        e["contexts"][context] += 1
                        if len(e["samples"]) < 3:
                            e["samples"].append({"part": rt[:20], "text": text.strip()[:60]})
                if context != "본문" or not text.strip():
                    continue
                seq, main = _char_signature(runs, chars)
                marker, role = leading_marker(text)
                key = (marker, pid, sid, seq)
                combo = combos.get(key)
                if combo is None:
                    combo = combos[key] = {"marker": marker or "(없음)", "role": role or "",
                                           "para": pid, "style": sid, "char_seq": list(seq),
                                           "main_char": main, "count": 0, "samples": []}
                combo["count"] += 1
                if len(combo["samples"]) < 2:
                    combo["samples"].append(text.strip()[:80])
                typed = paragraph_style_type(para, defs)
                if typed is None:
                    continue
                tkey, m = typed
                t = types.get(tkey)
                if t is None:
                    t = types[tkey] = {"marker": m["marker"], "role": m["role"], "main_char": m["main_char"],
                                       "count": 0, "variants": set(), "spacing": Counter(),
                                       "indent_mm": Counter(), "line": Counter(), "prev_pt": Counter(),
                                       "paras": Counter(), "styles": Counter(), "emphasis": 0, "effects": Counter(),
                                       "samples": []}
                t["count"] += 1
                t["variants"].add(key)
                t["spacing"][m["spacing"]] += 1
                t["indent_mm"][m["indent_mm"]] += 1
                t["prev_pt"][m["prev_pt"]] += 1
                t["paras"][m["para"]] += 1
                t["styles"][m["style"]] += 1
                if m["line"] is not None:
                    t["line"][m["line"]] += 1
                t["emphasis"] += m["emphasis"]
                t["effects"].update(m["effects"])
                if len(t["samples"]) < 2:
                    t["samples"].append(m["text"][:80])
        for cid, info in chars.items():
            if info["border_fill"] and cid in char_use and char_use[cid]["chars"]:
                border_use[info["border_fill"]].add("글자 테두리")

    used_chars = {cid for cid, u in char_use.items() if u["chars"]}
    used_paras = set(para_use)
    used_fonts = Counter()
    for cid in used_chars:
        font = chars.get(cid, {}).get("font", {}).get("hangul")
        if font:
            used_fonts[font] += char_use[cid]["chars"]

    def plain(counter):
        return dict(counter.most_common())

    return {
        "source": path.name,
        "page": page,
        "definitions": defs,
        "summary": {
            "paragraphs": total_paragraphs,
            "fonts_defined": sum(len(v) for v in defs["fonts"].values()),
            "fonts_used": len(used_fonts),
            "chars_defined": len(chars), "chars_used": len(used_chars),
            "paras_defined": len(paras), "paras_used": len(used_paras),
            "styles_defined": len(defs["styles"]),
            "styles_used": len([s for s in style_use if s in defs["styles"]]),
            "border_fills_defined": len(defs["border_fills"]),
            "border_fills_used": len([b for b in border_use if b]),
            "tables": sum(t["count"] for t in tables.values()),
            "table_types": len(tables),
            "combos": len(combos),
            "types": len(types),
            "shade_colors": len(shade_use),
        },
        "used_fonts": plain(used_fonts),
        "char_usage": {cid: {**{k: v for k, v in u.items() if k != "contexts"},
                             "contexts": plain(u["contexts"])}
                       for cid, u in sorted(char_use.items(), key=lambda kv: -kv[1]["chars"])
                       if u["chars"]},
        "para_usage": {pid: {**{k: v for k, v in u.items() if k != "contexts"},
                             "contexts": plain(u["contexts"])}
                       for pid, u in sorted(para_use.items(), key=lambda kv: -kv[1]["count"])},
        "style_usage": plain(style_use),
        "border_fill_usage": {bid: sorted(v) for bid, v in border_use.items() if bid},
        "combos": list(combos.values()),
        "types": [_finish_type(t) for t in types.values()],
        "shade_colors": {k: {**v, "char_ids": sorted(v["char_ids"]), "contexts": plain(v["contexts"])}
                         for k, v in shade_use.items()},
        "inline_effects": {k: {**v, "contexts": plain(v["contexts"])} for k, v in effects_use.items()},
        "tables": list(tables.values()),
    }


def _finish_type(t):
    def stats(counter):
        if not counter:
            return None
        values = sorted(counter)
        return {"mode": _mode(counter), "min": values[0], "max": values[-1]}
    return {"marker": t["marker"], "role": t["role"], "main_char": t["main_char"], "count": t["count"],
            "variants": len(t["variants"]), "spacing": stats(t["spacing"]),
            "indent_mm": stats(t["indent_mm"]), "line": stats(t["line"]), "prev_pt": stats(t["prev_pt"]),
            "para": _mode(t["paras"]), "style": _mode(t["styles"]),
            "emphasis": t["emphasis"], "effects": dict(t["effects"].most_common()),
            "samples": t["samples"]}


# ----------------------------------------------------------------------------
# 보고서(Markdown)
# ----------------------------------------------------------------------------

def _char_label(c) -> str:
    if not c:
        return "?"
    parts = [f"{c['font'].get('hangul') or '?'} {c['size_pt']:g}pt"]
    if c["ratio"] != 100:
        parts.append(f"장평 {c['ratio']}%")
    if c["spacing"]:
        parts.append(f"자간 {c['spacing']}%")
    flags = [n for n, on in (("굵게", c["bold"]), ("기울임", c["italic"]),
                             ("위첨자", c["superscript"]), ("아래첨자", c["subscript"])) if on]
    if c["underline"] != "NONE":
        flags.append("밑줄")
    # 한/글이 취소선 없는 글자에도 shape="3D"를 저장하는 경우가 있어 선 모양만 취소선으로 본다.
    if c["strikeout"] not in ("NONE", "3D", None):
        flags.append("취소선")
    if c["outline"] != "NONE":
        flags.append("외곽선")
    if c["shadow"] != "NONE":
        flags.append("그림자")
    if c["color"].upper() != "#000000":
        flags.append(f"글자색 {c['color']}")
    if c.get("shade"):
        flags.append(f"음영 {c['shade']}")
    return ", ".join(parts + flags)


def _para_label(p) -> str:
    if not p:
        return "?"
    ls = p["line_spacing"]
    parts = [ALIGN_LABELS.get(p["align"], p["align"])]
    if p["left"]:
        parts.append(f"왼쪽 {_mm(p['left'])}mm")
    if p["indent"]:
        parts.append(("내어쓰기 " if p["indent"] < 0 else "들여쓰기 ") + f"{abs(_mm(p['indent']))}mm")
    if p["right"]:
        parts.append(f"오른쪽 {_mm(p['right'])}mm")
    if p["prev"]:
        parts.append(f"위 {p['prev'] / 100:g}pt")
    if p["next"]:
        parts.append(f"아래 {p['next'] / 100:g}pt")
    if ls:
        parts.append(f"줄간격 {ls['value']}%" if ls["type"] == "PERCENT" else f"줄간격 {ls['type']} {ls['value']}")
    if p["heading"]:
        parts.append(f"개요/번호 {p['heading']['type']} {p['heading']['level'] + 1}수준")
    if p["keep_with_next"]:
        parts.append("다음 문단과 함께")
    if p["keep_lines"]:
        parts.append("문단 보호")
    return ", ".join(parts)


def _border_label(b) -> str:
    if not b:
        return "?"
    lines = []
    for side, v in b["borders"].items():
        if side != "diagonal" and v["type"] not in ("NONE", None):
            lines.append(f"{side} {v['type']} {v['width']} {v['color']}")
    fill = b["fill"]
    fill_text = (f"배경 {fill['color']}" if fill and fill["kind"] == "단색"
                 else f"그러데이션 {'→'.join(fill['colors'])}" if fill else "배경 없음")
    return ("; ".join(lines) or "테두리 없음") + " / " + fill_text


def _cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def inventory_markdown(inv: dict) -> str:
    d = inv["definitions"]
    chars, paras, styles, bfs = d["chars"], d["paras"], d["styles"], d["border_fills"]
    s = inv["summary"]
    out = [f"# 문서 스타일 분석: {inv['source']}", ""]
    out += ["## 1. 요약", "",
            "| 요소 | 정의 | 사용 |", "|---|---:|---:|",
            f"| 글꼴(한글) | {len(d['fonts'].get('hangul', {}))} | {s['fonts_used']} |",
            f"| 문자 모양 | {s['chars_defined']} | {s['chars_used']} |",
            f"| 문단 모양 | {s['paras_defined']} | {s['paras_used']} |",
            f"| 스타일 | {s['styles_defined']} | {s['styles_used']} |",
            f"| 테두리/배경 | {s['border_fills_defined']} | {s['border_fills_used']} |",
            f"| 표 (종류) | – | {s['tables']} ({s['table_types']}종) |",
            f"| 본문 스타일 유형 | – | {s['types']} (변형 {s['combos']}) |", "",
            f"전체 문단 {s['paragraphs']}개(표·머리말 안 문단 포함). 정의만 있고 쓰이지 않는 모양은 "
            "한/글이 복사·붙여넣기 과정에서 누적한 것이므로 예시 서식에는 영향이 없습니다.", ""]
    p = inv["page"] or {}
    if p:
        m = p.get("margin_mm", {})
        out += ["## 2. 쪽 설정", "",
                f"- 용지: {p['width_mm']}×{p['height_mm']}mm ({p['orientation']})",
                f"- 여백: 왼쪽 {m.get('left')} · 오른쪽 {m.get('right')} · 위 {m.get('top')} · "
                f"아래 {m.get('bottom')} · 머리말 {m.get('header')} · 꼬리말 {m.get('footer')} mm", ""]
    out += ["## 3. 사용 글꼴", "", "| 글꼴 | 글자 수 |", "|---|---:|"]
    out += [f"| {_cell(f)} | {n:,} |" for f, n in inv["used_fonts"].items()]
    def rng(st, unit="", fmt="{:g}"):
        if not st:
            return "-"
        mode = fmt.format(st["mode"]) + unit
        return mode if st["min"] == st["max"] else f"{mode} ({fmt.format(st['min'])}~{fmt.format(st['max'])})"

    out += ["", "## 4. 본문 스타일 유형", "",
            "본문(표 밖) 문단을 문두기호·글꼴·크기·굵게·색·장평·정렬·왼쪽 여백으로 묶었습니다. "
            "자간·줄간격·내어쓰기는 문단마다 줄 맞춤으로 조금씩 달라서 최빈값(범위)으로 적습니다. "
            f"문단 모양 ID까지 따지면 {s['combos']}개 변형입니다.", "",
            "| # | 기호 | 역할 | 글자 | 정렬 | 내어쓰기 mm | 줄간격 % | 자간 % | 문단 위 pt | 부분 서식(문단 수) | 문단 수(변형) | 예문 |",
            "|---:|:---:|---|---|---|---|---|---|---|---|---:|---|"]
    for i, t in enumerate(inv["types"], 1):
        c = chars.get(t["main_char"]) or {}
        glyph = _char_label({**c, "spacing": 0}) if c else "?"
        align = ALIGN_LABELS.get(paras.get(t["para"], {}).get("align"), "")
        left = paras.get(t["para"], {}).get("left", 0)
        if left:
            align += f", 왼쪽 {_mm(left)}mm"
        out.append(f"| {i} | {_cell(t['marker'])} | {t['role']} | {_cell(glyph)} | {align} | "
                   f"{rng(t['indent_mm'])} | {rng(t['line'])} | {rng(t['spacing'])} | {rng(t['prev_pt'])} | "
                   f"{_cell(', '.join(f'{k} {v}' for k, v in t['effects'].items()) or '-')} | {t['count']} ({t['variants']}) | {_cell(t['samples'][0][:36])} |")
    if inv.get("inline_effects"):
        out += ["", "### 4-1. 부분 글자 서식 (위첨자·글자색·강조 등)", "",
                "문단의 주 문자 모양과 다르게 일부 글자에만 준 서식입니다(표·머리말 포함).", "",
                "| 부분 서식 | 적용 부분 | 글자 수 | 위치 | 예 |", "|---|---:|---:|---|---|"]
        for name, e in sorted(inv["inline_effects"].items(), key=lambda kv: -kv[1]["runs"]):
            ctx = ", ".join(f"{k} {v}" for k, v in e["contexts"].items())
            ex = e["samples"][0]
            out.append(f"| {_cell(name)} | {e['runs']} | {e['chars']:,} | {ctx} | "
                       f"‘{_cell(ex['part'])}’ ← {_cell(ex['text'][:36])} |")
    out += ["", "### 4-2. 글자 음영색", ""]
    if inv.get("shade_colors"):
        out += ["| 음영색 | 적용 부분 | 글자 수 | 문자 모양 ID | 위치 | 예 |", "|---|---:|---:|---|---|---|"]
        for color, e in sorted(inv["shade_colors"].items(), key=lambda kv: -kv[1]["chars"]):
            ctx = ", ".join(f"{k} {v}" for k, v in e["contexts"].items())
            ex = e["samples"][0]
            out.append(f"| {color} | {e['runs']} | {e['chars']:,} | {', '.join(e['char_ids'])} | {ctx} | "
                       f"‘{_cell(ex['part'])}’ ← {_cell(ex['text'][:36])} |")
    else:
        out.append("글자 음영을 쓴 곳이 없습니다(흰색 음영은 음영 없음으로 봅니다).")
    out += ["", "## 5. 표", "",
            "| # | 크기 | 너비 | 셀 안쪽 여백(좌·우·위·아래 mm) | 머리글 글자 | 본문 글자 | 셀 테두리/배경 | 개수 | 첫 행 |",
            "|---:|---|---:|---|---|---|---|---:|---|"]
    for i, t in enumerate(inv["tables"], 1):
        fills = "; ".join(f"#{b}: {_border_label(bfs.get(b))}" for b, _ in
                          sorted(t["cell_border_fills"].items(), key=lambda kv: -kv[1])[:3])
        out.append(f"| {i} | {t['rows']}×{t['cols']} | {t['width_mm']}mm | {t['cell_margin_mm']} | "
                   f"{_cell(_char_label(chars.get(t['header_chars'][0])) if t['header_chars'] else '-')} | "
                   f"{_cell(_char_label(chars.get(t['body_chars'][0])) if t['body_chars'] else '-')} | "
                   f"{_cell(fills)} | {t['count']} | {_cell(t['first_row'][:40])} |")
    out += ["", "## 6. 사용된 문자 모양", "",
            "| ID | 문자 모양 | 글자 수 | 위치 | 예 |", "|---:|---|---:|---|---|"]
    for cid, u in inv["char_usage"].items():
        ctx = ", ".join(f"{k} {v}" for k, v in u["contexts"].items())
        out.append(f"| {cid} | {_cell(_char_label(chars.get(cid)))} | {u['chars']:,} | {ctx} | {_cell(u['sample'][:24])} |")
    out += ["", "## 7. 사용된 문단 모양", "",
            "| ID | 문단 모양 | 문단 수 | 위치 | 예 |", "|---:|---|---:|---|---|"]
    for pid, u in inv["para_usage"].items():
        ctx = ", ".join(f"{k} {v}" for k, v in u["contexts"].items())
        out.append(f"| {pid} | {_cell(_para_label(paras.get(pid)))} | {u['count']} | {ctx} | {_cell(u['sample'][:24])} |")
    out += ["", "## 8. 스타일 목록", "",
            "| ID | 이름 | 종류 | 문단 모양 | 문자 모양 | 사용 문단 |", "|---:|---|---|---|---|---:|"]
    for sid, st in styles.items():
        out.append(f"| {sid} | {_cell(st['name'])} | {st['type']} | {_cell(_para_label(paras.get(st['para'])))} | "
                   f"{_cell(_char_label(chars.get(st['char'])))} | {inv['style_usage'].get(sid, 0)} |")
    out += ["", "## 9. 사용된 테두리/배경", "", "| ID | 쓰는 곳 | 모양 |", "|---:|---|---|"]
    for bid, where in sorted(inv["border_fill_usage"].items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0):
        out.append(f"| {bid} | {', '.join(where)} | {_cell(_border_label(bfs.get(bid)))} |")
    if d["numberings"] or d["bullets"]:
        out += ["", "## 10. 번호·글머리표 정의", ""]
        for n in d["numberings"].values():
            levels = ", ".join(f"{l['level']}:{l['text']}({l['format']})" for l in n["levels"])
            out.append(f"- 번호 #{n['id']}: {levels}")
        for b in d["bullets"].values():
            out.append(f"- 글머리표 #{b['id']}: {b['char']}")
    if d["tabs"]:
        out += ["", "## 11. 탭 정의", ""]
        for t in d["tabs"].values():
            items = ", ".join(f"{i['pos_mm']}mm {i['type']}" for i in t["items"]) or "사용자 탭 없음"
            out.append(f"- 탭 #{t['id']}: {items}")
    return "\n".join(out) + "\n"


# ----------------------------------------------------------------------------
# 예시 서식 HWPX 생성
# ----------------------------------------------------------------------------

def _register_namespaces(xml_bytes: bytes):
    for prefix, uri in re.findall(rb'xmlns:([A-Za-z0-9_]+)="([^"]+)"', xml_bytes[:8192]):
        StdET.register_namespace(prefix.decode(), uri.decode())


def _strip_layout(e):
    """줄 배치 캐시(linesegarray)는 한/글이 열 때 다시 계산하므로 지운다."""
    for parent in list(e.iter()):
        for child in list(parent):
            if _tag(child) == "linesegarray":
                parent.remove(child)


def _has(e, names):
    return any(_tag(x) in names for x in e.iter())


def _para_shape(measure, defs):
    p = defs["paras"].get(measure["para"], {})
    return (p.get("left"), p.get("indent"), p.get("prev"), p.get("next"),
            (p.get("line_spacing") or {}).get("value"))


def build_style_sample(source, target, inventory: dict | None = None,
                       budget: int = SAMPLE_BUDGET, per_type: int = SAMPLES_PER_TYPE) -> dict:
    """본문을 스타일 조합별 대표 문단과 표 종류별 대표 표로 줄인 예시 HWPX를 만든다.

    원본 header.xml과 쪽 설정(secPr)·머리말·꼬리말은 그대로 둬 ID 참조가 유지된다.
    """
    source, target = Path(source), Path(target)
    validate_hwpx(source)
    inventory = inventory or analyze_style_inventory(source)
    chars = inventory["definitions"]["chars"]
    with ZipFile(source) as z:
        sections = _sections(z)
        first_name = sections[0]
        payload = z.read(first_name)
        _register_namespaces(payload)
        _register_namespaces(z.read("Contents/header.xml"))
        root = StdET.fromstring(payload)
        # 여러 구역이면 나머지 구역의 문단도 순서대로 후보에 넣는다.
        body = [p for p in root if _tag(p) == "p"]
        for name in sections[1:]:
            _register_namespaces(z.read(name))
            body += [p for p in StdET.fromstring(z.read(name)) if _tag(p) == "p"]

        defs = inventory["definitions"]
        type_stats = {}
        typed = {}
        for index, para in enumerate(body):
            if index and not _has(para, {"secPr", "tbl", "pic", "ole", "equation"}):
                result = paragraph_style_type(para, defs)
                if result:
                    typed[index] = result
                    # 최빈 문단 모양은 기존 서식 분석(hwpx_서식_분석)처럼 문두기호 단위로 센다.
                    type_stats.setdefault(result[1]["marker"], Counter())[_para_shape(result[1], defs)] += 1

        def score(index):
            key, m = typed[index]
            # 최빈 문단 모양(줄간격·여백)이고 줄 맞춤 자간이 적은 문단이 대표다.
            return (10 * (_para_shape(m, defs) != _mode(type_stats[m["marker"]])) + abs(m["spacing"]), index)

        counts = Counter(key for key, _ in typed.values())
        total = sum(counts.values()) or 1
        # 큰 문서는 유형이 많아 50문단으로는 기호별 비율이 흐트러진다: 본문의 15%(최대 400)까지 늘린다.
        budget = max(budget, min(400, total * 15 // 100))
        per_type = max(per_type, budget // 4)
        quota = {key: min(per_type, max(1, math.ceil(n * budget / total))) for key, n in counts.items()}
        chosen = defaultdict(list)
        # 유형별 첫 문단은 항상 남겨 제목·일자 등 문서 앞부분 순서를 원본과 같게 한다.
        for index in sorted(typed):
            key = typed[index][0]
            if not chosen[key]:
                chosen[key].append(index)
        # 본문 첫 두 문단(제목·일자/담당자 자리)은 유형이 같아도 남긴다.
        for index in sorted(typed)[:2]:
            key = typed[index][0]
            if index not in chosen[key]:
                chosen[key].append(index)
        for index in sorted(typed, key=score):
            key = typed[index][0]
            if len(chosen[key]) < quota[key] and index not in chosen[key]:
                chosen[key].append(index)
        # 위첨자·글자색 같은 부분 서식은 유형마다 최소 한 문단은 남긴다.
        covered = {(typed[i][0], e) for picks in chosen.values() for i in picks for e in typed[i][1]["effects"]}
        for index in sorted(typed):
            key, m = typed[index]
            missing = [e for e in m["effects"] if (key, e) not in covered]
            if missing:
                chosen[key].append(index)
                covered.update((key, e) for e in m["effects"])
        picked = {i for picks in chosen.values() for i in picks}

        kept, table_seen = [], set()
        stats = {"paragraphs": len(picked), "tables": 0, "page_controls": 0}
        for index, para in enumerate(body):
            runs = _paragraph_runs(para)
            text = "".join(_run_text(r) for r in runs)
            tbls = [x for r in runs for x in r if _tag(x) == "tbl"]
            if index == 0 or _has(para, {"secPr"}):
                kept.append(para)  # 쪽 설정·단 설정
            elif tbls:
                sigs = [_table_signature(t, defs['chars']) for t in tbls]
                if any(sig not in table_seen for sig in sigs):
                    table_seen.update(sigs)
                    kept.append(para)
                    stats["tables"] += len(tbls)
            elif _has(para, PAGE_CONTROLS) and not text.strip():
                kept.append(para)  # 머리말·꼬리말·쪽 번호
                stats["page_controls"] += 1
            elif index in picked:
                kept.append(para)

        for child in list(root):
            root.remove(child)
        for para in kept:
            para = copy.deepcopy(para)
            _strip_layout(para)
            root.append(para)
        section_bytes = (b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
                         + StdET.tostring(root, encoding="utf-8", xml_declaration=False))

        drop = set(sections[1:])
        buffer = io.BytesIO()
        with ZipFile(buffer, "w") as out:
            for info in z.infolist():
                if info.filename in drop:
                    continue
                data = section_bytes if info.filename == first_name else z.read(info.filename)
                if info.filename == "Contents/content.hpf" and drop:
                    text = data.decode("utf-8")
                    for name in drop:
                        stem = name.rsplit("/", 1)[-1][:-4]
                        text = re.sub(rf'<opf:item [^>]*id="{stem}"[^>]*/>', "", text)
                        text = re.sub(rf'<opf:itemref [^>]*idref="{stem}"[^>]*/>', "", text)
                    data = text.encode("utf-8")
                if info.filename == "Contents/header.xml" and drop:
                    data = re.sub(rb'secCnt="\d+"', b'secCnt="1"', data, count=1)
                compress = ZIP_STORED if info.filename == "mimetype" else ZIP_DEFLATED
                out.writestr(info.filename, data, compress_type=compress)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(buffer.getvalue())
    validate_hwpx(target)
    stats["types"] = len(chosen)
    stats["table_types"] = len(table_seen)
    return stats
