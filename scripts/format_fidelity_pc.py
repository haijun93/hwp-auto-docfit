"""서식 복사 100% 재연 시험(사용자 기준, 2026-10-16·17): 새 기능 시험과 버전 업 릴리스 때 반드시 돌린다.

사용: .venv\\Scripts\\python.exe scripts\\format_fidelity_pc.py [예시.hwpx ...] [--out 결과폴더] [--mode all]

예시를 주지 않으면 C:\\HWP_AUTODOCFIT\\테스트예시 폴더(시험 전용, 저장소에 넣지 않음)의 HWPX·HWP 전부를 쓴다. HWP 예시는 한/글로 HWPX 사본을 만들어
그 사본을 원본 A로 삼는다(HWP 원본은 읽기만 한다). 예시마다
1) 예시 A를 서식으로 복제한다(앱의 서식 분석·선택 경로: _서식_분석_시작 → _프로파일_전역반영 → _프로파일_선택).
2) A의 서식 해제본 A0을 만든다: 글·문단 순서·표 구조·개체는 두고, 모든 문단(본문·표 칸)·글자 모양을 바탕글
   모양으로, 표 테두리를 기본 실선·칸 너비를 균등·칸 높이와 여백을 기본값으로, 쪽 여백을 한/글 기본값으로 되돌린다.
3) A0에 복제한 서식으로 '한 번에 적용'(기본)을 돌린다.
4) 결과를 A와 문서 순서대로 대조한다: 글, 문단 모양(정렬·여백·간격·줄 간격·줄 나눔), 글자 모양(글꼴·크기·굵게·
   기울임·밑줄·색·음영·장평·자간·위첨자), 표(행·열·크기·칸 크기·칸 여백·테두리 내용), 쪽 설정.
불일치 0이 합격이다. 원본이 손으로 맞춘 쪽별 줄 간격·낱말 자간과 한 줄 문단의 내어쓰기는 재연 기준에서 빼고
뺀 수만 따로 적는다(2026-10-17 사용자 결정). 원본은 읽기만 하며 처리는 모두 임시 사본으로 한다. 예시마다 새 프로세스로 처리한다.
결과 폴더에 예시별 결과 HWPX·작업 로그·불일치 목록(.txt)과 summary.json을 남긴다.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
# 시험 전용 예시는 앱의 서식예시 폴더와 따로, 이 PC에만 둔다(저장소에 넣지 않음, 사용자 지시 2026-10-17).
SAMPLE_FOLDER = Path(r"C:\HWP_AUTODOCFIT\테스트예시")
H = "{http://www.hancom.co.kr/hwpml/2011/head}"
P = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


# ── 서식 해제본 ──

def _register_namespaces(data):
    """직렬화 접두사(hp·hh·hc …)를 원본과 같게 등록한다(앱의 XML_네임스페이스_등록과 같은 방식, 파싱은 defusedxml)."""
    registry = getattr(ET.tostring, "__globals__", {}).get("_namespace_map")
    if not isinstance(registry, dict):
        return
    for name, raw in data.items():
        if name.endswith(".xml"):
            for _, (prefix, uri) in ET.iterparse(io.BytesIO(raw), events=("start-ns",)):
                if prefix:
                    for old_uri, old_prefix in list(registry.items()):
                        if old_uri == uri or old_prefix == prefix:
                            del registry[old_uri]
                    registry[uri] = prefix


def _dump(root, original):
    body = ET.tostring(root, encoding="utf-8")
    if original.startswith(b"<?xml"):
        head = original[:original.find(b"?>") + 2]
        return head + (body.split(b"?>", 1)[-1] if body.startswith(b"<?xml") else body)
    return body


def strip_format(source: Path, target: Path) -> None:
    """A의 서식 해제본(위 2번)을 target에 만든다."""
    zin = zipfile.ZipFile(source)
    data = {n: zin.read(n) for n in zin.namelist()}
    _register_namespaces(data)
    header = ET.fromstring(data["Contents/header.xml"])
    style0 = next(s for s in header.iter(H + "style") if s.get("id") == "0")
    para_id, char_id = style0.get("paraPrIDRef"), style0.get("charPrIDRef")
    fills = next(header.iter(H + "borderFills"))
    sample = next(iter(fills))
    fill_id = str(1 + max(int(b.get("id")) for b in fills))
    Element = type(sample)
    fill = Element(H + "borderFill", {"id": fill_id, "threeD": "0", "shadow": "0", "centerLine": "NONE",
                                      "breakCellSeparateLine": "0"})
    for name in ("slash", "backSlash"):
        fill.append(Element(H + name, {"type": "NONE", "Crooked": "0", "isCounter": "0"}))
    for side in ("left", "right", "top", "bottom"):
        fill.append(Element(H + side + "Border", {"type": "SOLID", "width": "0.12 mm", "color": "#000000"}))
    fill.append(Element(H + "diagonal", {"type": "SOLID", "width": "0.1 mm", "color": "#000000"}))
    fills.append(fill)
    fills.set("itemCnt", str(len(fills)))
    data["Contents/header.xml"] = _dump(header, data["Contents/header.xml"])
    for name in [n for n in data if n.startswith("Contents/section") and n.endswith(".xml")]:
        root = ET.fromstring(data[name])
        for p in root.iter(P + "p"):
            p.set("paraPrIDRef", para_id)
            p.set("styleIDRef", "0")
            for cache in [c for c in p if c.tag == P + "linesegarray"]:
                p.remove(cache)
        for run in root.iter(P + "run"):
            run.set("charPrIDRef", char_id)
        for tbl in root.iter(P + "tbl"):
            tbl.set("borderFillIDRef", fill_id)
            rows, cols = int(tbl.get("rowCnt")), int(tbl.get("colCnt"))
            size = tbl.find(P + "sz")
            width = int(size.get("width"))
            inner = tbl.find(P + "inMargin")
            if inner is not None:
                inner.attrib.update(left="510", right="510", top="141", bottom="141")
            for tr in tbl.findall(P + "tr"):
                for tc in tr.findall(P + "tc"):
                    tc.set("borderFillIDRef", fill_id)
                    tc.set("hasMargin", "0")
                    span = tc.find(P + "cellSpan")
                    col_span = int(span.get("colSpan", "1")) if span is not None else 1
                    row_span = int(span.get("rowSpan", "1")) if span is not None else 1
                    cell = tc.find(P + "cellSz")
                    cell.set("width", str(round(width * col_span / cols)))
                    cell.set("height", str(1000 * row_span))
                    margin = tc.find(P + "cellMargin")
                    if margin is not None:
                        margin.attrib.update(left="510", right="510", top="141", bottom="141")
            size.set("height", str(1000 * rows))
        for page in root.iter(P + "pagePr"):
            margin = page.find(P + "margin")
            if margin is not None:
                margin.attrib.update(left="8504", right="8504", top="5668", bottom="4252", header="4252",
                                     footer="4252", gutter="0")
        data[name] = _dump(root, data[name])
    with zipfile.ZipFile(target, "w") as zout:
        for info in zin.infolist():
            zout.writestr(info, data[info.filename],
                          compress_type=zipfile.ZIP_STORED if info.filename == "mimetype" else zipfile.ZIP_DEFLATED)


# ── 대조 ──

def _attrs(e, skip=()):
    return None if e is None else tuple(sorted((k, v) for k, v in e.attrib.items() if k not in skip))


def load(path):
    """문서 순서의 (종류, …) 목록: 쪽 설정·문단(글·문단 모양·글자 모양 구간)·표."""
    z = zipfile.ZipFile(path)
    header = ET.fromstring(z.read("Contents/header.xml"))
    fonts = {ff.get("lang"): {f.get("id"): f.get("face") for f in ff.iter(H + "font")} for ff in header.iter(H + "fontface")}
    chars = {}
    for c in header.iter(H + "charPr"):
        ref = c.find(H + "fontRef")
        part = lambda name, attr="hangul": c.find(H + name).get(attr) if c.find(H + name) is not None else None
        chars[c.get("id")] = tuple(sorted({
            "font": fonts.get("HANGUL", {}).get(ref.get("hangul")) if ref is not None else None,
            "latin": fonts.get("LATIN", {}).get(ref.get("latin")) if ref is not None else None,
            "h": c.get("height"), "color": c.get("textColor"), "shade": c.get("shadeColor"),
            "bold": c.find(H + "bold") is not None, "italic": c.find(H + "italic") is not None,
            "sup": c.find(H + "supscript") is not None, "sub": c.find(H + "subscript") is not None,
            "ratio": part("ratio"), "spacing": part("spacing"), "underline": part("underline", "type")}.items()))
    fill_xml = {b.get("id"): ET.tostring(b).decode().replace('id="%s"' % b.get("id"), "")
                for b in header.iter(H + "borderFill")}
    paras = {}
    for p in header.iter(H + "paraPr"):
        values = {"align": _attrs(p.find(H + "align")), "break": _attrs(p.find(H + "breakSetting")),
                  "heading": _attrs(p.find(H + "heading"))}
        base = next(p.iter(P + "case"), p)
        margin = base.find(H + "margin")
        for child in (margin if margin is not None else ()):
            values[child.tag.split("}")[1]] = child.get("value")
        values["ls"] = _attrs(base.find(H + "lineSpacing"))
        paras[p.get("id")] = tuple(sorted(values.items()))
    items = []

    def walk(node):
        for child in node:
            if child.tag == P + "p":
                runs, text = [], ""
                for run in child.findall(P + "run"):
                    for sub in run:
                        if sub.tag == P + "t":
                            t = "".join(sub.itertext())
                            if t:
                                shape = chars.get(run.get("charPrIDRef"))
                                if runs and runs[-1][0] == shape:      # 모양이 같은 run은 나뉘어 있어도 하나로 본다
                                    runs[-1] = (shape, runs[-1][1] + t)
                                else:
                                    runs.append((shape, t))
                                text += t
                cache = child.find(P + "linesegarray")
                line_count = len(cache) if cache is not None else None
                items.append(("P", text, paras.get(child.get("paraPrIDRef")), runs, line_count))
                for run in child.findall(P + "run"):
                    walk(run)
            elif child.tag == P + "tbl":
                cells = [(_attrs(tc.find(P + "cellAddr")), _attrs(tc.find(P + "cellSpan")), _attrs(tc.find(P + "cellSz")),
                          _attrs(tc.find(P + "cellMargin")), fill_xml.get(tc.get("borderFillIDRef")))
                         for tc in child.iter(P + "tc")]
                items.append(("TBL", child.get("rowCnt"), child.get("colCnt"), _attrs(child.find(P + "sz")),
                              _attrs(child.find(P + "inMargin")), fill_xml.get(child.get("borderFillIDRef")), cells))
                for tr in child.findall(P + "tr"):
                    for tc in tr.findall(P + "tc"):
                        sub = tc.find(P + "subList")
                        if sub is not None:
                            walk(sub)
            elif child.tag not in (P + "secPr", P + "ctrl", P + "linesegarray"):
                walk(child)

    for name in sorted(n for n in z.namelist() if n.startswith("Contents/section")):
        root = ET.fromstring(z.read(name))
        for sec in root.iter(P + "secPr"):
            page = sec.find(P + "pagePr")
            items.append(("PAGE", _attrs(page), _attrs(page.find(P + "margin")) if page is not None else None))
        walk(root)
    return items


def _diff(a, b):
    da, db = dict(a or ()), dict(b or ())
    return {k: (da.get(k), db.get(k)) for k in set(da) | set(db) if da.get(k) != db.get(k)}


# 재연 기준에서 빼는 손 조정(2026-10-17 사용자 결정): 쪽마다 다른 줄 간격과 낱말 자간. 한 줄 문단의 내어쓰기는
# 화면이 같으므로 비교하지 않는다(원본의 줄 배치 정보 lineseg로 줄 수를 센다).
EXCLUDED_PARA = ("ls", "break")
EXCLUDED_CHAR = ("spacing",)
# 문단 하나에만 준 손 간격: 원본에서 같은 계층(항목기호) 대표값과 다른 문단 위·아래 간격·내어쓰기·왼쪽 여백(사용자 결정 2026-10-17).
HAND_KEYS = ("prev", "next", "intent", "left")
_MARKER_PARAGRAPH = re.compile(r"^\s*(?:[□ㅁㅇ○●◦▪▫■◆◇※*-]+|\d+[.)])\s*\S")


def _is_marker_paragraph(text):
    return bool(_MARKER_PARAGRAPH.match(text or ""))


def _group(text):
    import re
    m = re.match(r"\s*(\*{1,2}|[□■ㅁㅇ○●◦※•·▪▶◆◇☞\-–]|\d{1,2}\.|[가-하]\.|\(\d{1,2}\)|[①-⑳])", text or "")
    return {"ㅁ": "□", "○": "ㅇ"}.get(m.group(1), m.group(1)) if m else ""


_DEPTH = {"□": 1, "ㅇ": 2, "-": 3, "–": 3, "*": 4, "**": 4, "※": 4}


def _contexts(items):
    """원본 문단 번호 → 자리(계층, 계층 복귀 문단인가). 복귀는 바로 앞 항목 문장이 더 깊은 계층일 때."""
    out, previous = {}, None
    for index, x in enumerate(items):
        if x[0] != "P" or not x[1].strip():
            continue
        group = _group(x[1])
        depth = _DEPTH.get(group)
        out[index] = (group, bool(depth and previous and previous > depth))
        if depth:
            previous = depth
    return out


def _level_values(items):
    """자리별 대표값 {(계층, 복귀, 항목): 값|None}. 같은 자리 문단이 둘 이상일 때만, 최다값이 다른 값보다 많을 때만
    대표값이고 동률이면 None(대표를 정할 수 없어 그 자리 값은 모두 손 조정으로 본다)."""
    from collections import Counter, defaultdict
    seen = defaultdict(Counter)
    for index, (group, ret) in _contexts(items).items():
        for k, v in (items[index][2] or ()):
            if k in HAND_KEYS:
                seen[(group, ret, k)][v] += 1
    reps = {}
    for key, c in seen.items():
        if sum(c.values()) < 2:
            continue
        top = c.most_common(2)
        reps[key] = top[0][0] if len(top) == 1 or top[0][1] > top[1][1] else None
    return reps


def _hand_keys(x, levels, context):
    """원본 문단 x에서 손으로 준 값으로 보는 문단 모양 항목(자리 대표값과 다르거나 대표값을 정할 수 없음)."""
    if context is None:
        return set()
    group, ret = context
    return {k for k, v in (x[2] or ()) if k in HAND_KEYS and (group, ret, k) in levels
            and levels[(group, ret, k)] != v}


def _normalized(x, line_count, hand=()):
    """비교용 문단: 제외 항목을 뺀 문단 모양과, 제외 항목을 뺀 뒤 모양이 같은 run을 합친 글자 구간."""
    para = tuple((k, v) for k, v in (x[2] or ()) if k not in EXCLUDED_PARA and k not in hand
                 and not (k == "intent" and line_count is not None and line_count <= 1
                          and not _is_marker_paragraph(x[1])))
    runs = []
    for shape, text in x[3]:
        shape = tuple((k, v) for k, v in (shape or ()) if k not in EXCLUDED_CHAR)
        if runs and runs[-1][0] == shape:
            runs[-1] = (shape, runs[-1][1] + text)
        else:
            runs.append((shape, text))
    return ("P", x[1], para, runs)


def _excluded(x, y, hand=()):
    """제외한 손 조정 종류(원본 x와 결과 y가 다른 것만)."""
    found = []
    px, py = dict(x[2] or ()), dict(y[2] or ())
    if any(px.get(k) != py.get(k) for k in hand):
        found.append("문단 하나에만 준 간격·여백")
    if px.get("ls") != py.get("ls"):
        found.append("줄 간격")
    if (px.get("intent") != py.get("intent") and x[4] is not None and x[4] <= 1
            and not _is_marker_paragraph(x[1])):
        found.append("한 줄 문단 내어쓰기")
    sx = [dict(c or ()).get("spacing") for c, t in x[3] for _ in t]
    sy = [dict(c or ()).get("spacing") for c, t in y[3] for _ in t]
    if sx != sy:
        found.append("자간")
    return found


def compare(original, result):
    """(불일치 수, 사람이 읽을 목록). 손 조정 제외 항목은 따로 센다."""
    from collections import Counter
    excluded = Counter()
    a, b = load(original), load(result)
    levels = _level_values(a)
    contexts = _contexts(a)
    key = lambda x: (x[0], x[1] if x[0] == "P" else "")
    lines, count = [f"항목 수 원본 {len(a)} / 결과 {len(b)}"], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [key(x) for x in a], [key(x) for x in b],
                                                      autojunk=False).get_opcodes():
        if op != "equal":
            count += 1
            lines.append(f"[{op}] 원본 {i1}-{i2} / 결과 {j1}-{j2}")
            lines += [f"  - {x[0]} {x[1]!r:.90}" for x in a[i1:i2][:6]] + [f"  + {x[0]} {x[1]!r:.90}" for x in b[j1:j2][:6]]
            continue
        for i, j in zip(range(i1, i2), range(j1, j2)):
            x, y = a[i], b[j]
            if x[0] == "P":
                hand = _hand_keys(x, levels, contexts.get(i))
                if _is_marker_paragraph(x[1]):
                    # 항목기호/번호 문단의 들여쓰기는 수동 예외가 아니라 핵심 출력 규격이다.
                    hand.discard("intent")
                    hand.discard("left")
                excluded.update(_excluded(x, y, hand))
                x, y = _normalized(x, x[4], hand), _normalized(y, x[4], hand)
            if x == y:
                continue
            count += 1
            if x[0] == "P":
                lines.append(f"## 문단 {i} {x[1][:50]!r}")
                if x[2] != y[2]:
                    lines.append(f"  문단모양 {_diff(x[2], y[2])}")
                fa = [(ch, c) for c, t in x[3] for ch in t]
                fb = [(ch, c) for c, t in y[3] for ch in t]
                k = 0
                while k < min(len(fa), len(fb)):
                    if fa[k][1] != fb[k][1]:
                        d, e = _diff(fa[k][1], fb[k][1]), k
                        while e < len(fa) and e < len(fb) and fa[e][1] != fb[e][1] and _diff(fa[e][1], fb[e][1]) == d:
                            e += 1
                        lines.append(f"  글자 {''.join(f[0] for f in fa[k:e])[:30]!r} {d}")
                        k = e
                    else:
                        k += 1
            elif x[0] == "TBL":
                lines.append(f"## 표 {i} 행·열 {x[1:3]} / {y[1:3]}")
                if x[3] != y[3]:
                    lines.append(f"  크기 {_diff(x[3], y[3])}")
                for ca, cb in zip(x[6], y[6]):
                    if ca != cb:
                        lines.append(f"  칸 {ca[0]} {[_diff(p, q) for p, q in zip(ca[1:4], cb[1:4]) if p != q]}"
                                     + (" 테두리 다름" if ca[4] != cb[4] else ""))
            else:
                lines.append(f"## 쪽 설정 {x} / {y}")
    if excluded:
        lines.append("재연 기준에서 뺀 손 조정(문단 수): " + ", ".join(f"{k} {v}" for k, v in excluded.most_common()))
    lines.append(f"불일치 {count}")
    return count, lines


# ── 서식 복제와 적용(예시 하나, 새 프로세스) ──

def run_one(example: Path, target: Path, out: Path, mode: str) -> dict:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts"))
    os.chdir(ROOT)
    import pythoncom
    pythoncom.CoInitialize()
    import regression_pc as rp
    g = rp.앱_불러오기()
    work = Path(tempfile.mkdtemp(prefix="docfit_fidelity_"))
    log = open(out / f"{example.stem}.{mode}.log", "w", encoding="utf-8")
    g.update(로그=lambda *a: log.write(" ".join(map(str, a)) + "\n"), 진단로그=lambda *a: None,
             상태=lambda *_: None, _서식통일_최종결과_사용자확인=lambda *_: None)
    profile = g["한글파일_서식_분석"](str(example))
    # _프로파일_전역반영
    g["서식_기본값_전역_복원"]()
    g["표준서식_설정"] = copy.deepcopy(profile["format"])
    table = profile.get("table_format", {})
    for key, name in (("header_font", "표_헤더서식_헤더_폰트"), ("header_size", "표_헤더서식_헤더_크기"),
                      ("header_bold", "표_헤더서식_헤더_굵게"), ("body_font", "표_헤더서식_본문_폰트"),
                      ("body_size", "표_헤더서식_본문_크기"), ("body_bold", "표_헤더서식_본문_굵게")):
        g[name] = table.get(key, g[name])
    g["활성_정밀표_프로필"] = copy.deepcopy(profile.get("precise_tables"))
    g["활성_서식표_프로필"] = copy.deepcopy(profile.get("form_tables")) or None
    g["활성_표서식_프로필"] = copy.deepcopy(profile.get("table_style")) or None
    g["활성_머리서식_프로필"] = copy.deepcopy(profile.get("report_header")) or None
    g["활성_서식예시_파일"] = Path(example)
    g["괄호_축소_pt"] = float(profile["format"].get("괄호_축소_pt", 2) or 2)
    g["글꼴형식_등록"](profile["format"].get("글꼴형식"))
    # _프로파일_선택: 서식 옵션이 화면 값(설정)을 덮는다
    settings = g["설정_불러오기"]()
    options = profile["options"]
    for key in rp.STD_KEYS + list(rp.PARSPACE_KEYS) + ["std_title_subtitle_pt"]:
        if key in options:
            settings[key] = options[key]
    settings["paren_shrink"] = options.get("paren_shrink", True)
    settings["paren_label_bold"] = options.get("paren_label_bold", True)
    settings["label_symbols"] = {k: options.get("label_symbols", settings["label_symbols"]).get(k, True)
                                 for k in settings["label_symbols"]}
    settings["table_fonts"] = {"header": {"font": str(g["표_헤더서식_헤더_폰트"]), "size": str(g["표_헤더서식_헤더_크기"])},
                               "body": {"font": str(g["표_헤더서식_본문_폰트"]), "size": str(g["표_헤더서식_본문_크기"])}}
    if options.get("symbol_fonts"):
        settings["symbol_fonts"] = options["symbol_fonts"]
    g["기호글꼴_적용"](settings)
    g["설정_불러오기"] = lambda *a, **k: copy.deepcopy(settings)
    with open(out / f"{example.stem}.{mode}.run.log", "w", encoding="utf-8") as run_log:
        _, result, seconds, score, _ = rp.처리(g, str(target), work, mode, False, run_log)
    log.close()
    if not result:
        return {"file": example.name, "error": "결과 문서가 만들어지지 않음", "seconds": seconds}
    kept = out / f"{example.stem}.{mode}.hwpx"
    shutil.copyfile(result, kept)
    count, lines = compare(example, kept)
    (out / f"{example.stem}.{mode}.diff.txt").write_text("\n".join(lines), encoding="utf-8")
    return {"file": example.name, "mismatches": count, "seconds": seconds, "score": score,
            "version": g.get("APP_VERSION")}


def convert_hwp(source: Path, target: Path) -> None:
    """HWP 예시를 앱과 같은 방식(교정용_hwpx_준비, 독립 한/글)으로 HWPX 사본으로 만든다."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts"))
    os.chdir(ROOT)
    import pythoncom
    pythoncom.CoInitialize()
    import regression_pc as rp
    g = rp.앱_불러오기()
    with tempfile.TemporaryDirectory(prefix="fidelity_hwp_") as folder:
        copied = Path(folder) / ("src" + source.suffix.lower())
        shutil.copyfile(source, copied)
        shutil.copyfile(g["교정용_hwpx_준비"](copied, folder), target)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("examples", nargs="*", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--mode", default="all", choices=("all", "format"))
    parser.add_argument("--one", nargs=2, type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--convert", nargs=2, type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix="format_fidelity_"))
    out.mkdir(parents=True, exist_ok=True)
    if args.convert:
        convert_hwp(*args.convert)
        return 0
    if args.one:
        print(json.dumps(run_one(args.one[0], args.one[1], out, args.mode), ensure_ascii=False))
        return 0
    examples = args.examples or sorted(p for p in SAMPLE_FOLDER.iterdir() if p.suffix.lower() in (".hwpx", ".hwp"))
    # 한/글 COM 잠금은 맨 바깥(이 프로세스)에서 한 번 잡고, 하위 --one 프로세스는 환경 변수로 물려받아 그대로 통과한다.
    # 예전에는 하위의 regression_pc.처리가 바깥에서 잡힌 잠금을 다시 기다려 첫 예시에서 끝없이 멈췄다(2026-10-21).
    sys.path.insert(0, str(ROOT))
    from docfit_core.save_guard import com_test_lock
    with com_test_lock("format_fidelity_pc", ",".join(p.name for p in examples)[:120]):
        return _run_examples(examples, out, args.mode)


def _run_examples(examples, out, mode):
    results = []
    for example in examples:
        copy_dir = Path(tempfile.mkdtemp(prefix="format_fidelity_src_"))
        original = copy_dir / (example.stem + ".hwpx")          # 원본은 읽기만 한다
        if example.suffix.lower() == ".hwp":
            subprocess.run([sys.executable, __file__, "--convert", str(example), str(original)], check=True)
        else:
            shutil.copyfile(example, original)
        stripped = copy_dir / f"{example.stem}(서식해제).hwpx"
        strip_format(original, stripped)
        started = time.time()
        proc = subprocess.run([sys.executable, __file__, "--one", str(original), str(stripped), "--out", str(out),
                               "--mode", mode], capture_output=True, text=True, encoding="utf-8", errors="replace")
        line = (proc.stdout.strip().splitlines() or [""])[-1]
        try:
            item = json.loads(line)
        except ValueError:
            item = {"file": example.name, "error": (proc.stderr or proc.stdout)[-500:]}
        item["wall_seconds"] = round(time.time() - started, 1)
        results.append(item)
        print(f"{example.name}: " + (f"불일치 {item['mismatches']}" if "mismatches" in item else f"오류 {item['error'][:200]}"))
    (out / "summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    passed = all(item.get("mismatches") == 0 for item in results)
    print(f"결과 폴더: {out}\n판정: {'합격(100% 재연)' if passed else '불합격'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
