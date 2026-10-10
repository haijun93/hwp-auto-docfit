"""보고서 머리(제목·보고 주체 정보·개요)의 구성과 표기 방식을 분석·재작성한다(알파, 2026-10-10).

정부기관 보고서 서식마다 머리가 다르다.
- 제목: 1×1 상자 표(중앙부처 보고서), 2×2 표(제목+날짜·담당자 칸), 2행1열·3행1열 표, 상자 없는 제목 문단.
- 보고 주체 정보: 제목 아래 오른쪽 문단 "2026. 10. 7.  기관  부서", 내부 결재 "'26. 10. 7.(수)  /  과",
  담당자 행 "(2026. 10. 7., 과장 홍길동, ☎02-120-1234)", 제목 표 안의 날짜 칸·담당자 칸 등.
- 개요: 제목 아래 한 칸 상자 표.

``parse_info``는 보고 주체 글을 값(날짜·기관·부서·직위·이름·전화)과 표기 틀(template)로 나누고,
``render_info``는 다른 문서의 값을 이 틀로 다시 쓴다. ``detect_header``는 HWPX의 머리 구성을 읽는다.
"""

from __future__ import annotations

import copy
import datetime
import random
import re
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

WEEKDAYS = "월화수목금토일"
_RANKS = ("담당관", "센터장", "과장", "국장", "팀장", "계장", "실장", "부장", "차장", "단장", "주무관", "사무관",
          "서기관", "연구관", "연구사", "지도관", "지도사", "장학관", "장학사", "주임", "대리", "책임자", "담당자", "담당")
_DEPT_END = ("담당관", "센터", "사업소", "과", "팀", "계", "반")
_OFFICE_END = ("본부", "국", "실", "단")
_ORG_END = ("위원회", "공단", "공사", "재단", "부", "처", "청", "원", "시", "도", "군", "구")
_SEP = r"(?:\s*[/|]\s*|\s*,\s*|\s{2,})"

# 날짜: (정규식, 이름). 앞의 것부터 찾는다.
_DATE_PATTERNS = (
    re.compile(r"(?P<y>\d{4})\s*년\s*(?P<m>\d{1,2})\s*월\s*(?P<d>\d{1,2})\s*일(?:\s*\((?P<w>[월화수목금토일])\))?"),
    re.compile(r"(?P<q>[’'‘`])(?P<yy>\d{2})\s*\.\s*(?P<m>\d{1,2})\s*\.\s*(?P<d>\d{1,2})\s*\.?(?:\s*\((?P<w>[월화수목금토일])\))?"),
    re.compile(r"(?P<y>\d{4})\s*\.\s*(?P<m>\d{1,2})\s*\.\s*(?P<d>\d{1,2})\s*\.?(?:\s*\((?P<w>[월화수목금토일])\))?"),
    re.compile(r"(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})(?:\s*\((?P<w>[월화수목금토일])\))?"),
)
_PHONE = re.compile(r"(?P<label>☎\s*|전화\s*:?\s*|Tel\.?\s*:?\s*|TEL\s*:?\s*)?(?P<num>(?:0\d{1,2}[-)]\s?)?\d{3,4}-\d{4}|(?<=☎)\d{3,4}|(?<=☎ )\d{3,4})")
_PERSON = re.compile(r"(?:(?P<unit>[가-힣]{1,12}(?:과|팀|국|실|센터|단))(?P<head>장))?(?(head)|(?P<rank>" + "|".join(_RANKS)
                     + r"))\s*:?\s*(?P<name>[가-힣][○◯Ｏ]{1,2}|[○◯Ｏ]{2,3}|[가-힣]{2,4})(?![가-힣])")


def _date_format(match) -> str:
    """찾은 날짜 글에서 숫자 자리를 {Y}{y}{M}{D}{W}로 바꾼 표기 틀. 앞자리 0도 기억한다({MM}, {DD})."""
    text = match.group(0)
    out, last = [], 0
    for name in ("q", "y", "yy", "m", "d", "w"):
        if name not in match.groupdict() or match.group(name) is None:
            continue
        start, end = match.span(name)
        start -= match.start(0)
        end -= match.start(0)
        value = match.group(name)
        if name == "q":
            continue
        key = {"y": "Y", "yy": "y", "w": "W"}.get(name)
        if name == "m":
            key = "MM" if len(value) == 2 and value.startswith("0") else "M"
        if name == "d":
            key = "DD" if len(value) == 2 and value.startswith("0") else "D"
        out.append(text[last:start])
        out.append("{" + key + "}")
        last = end
    out.append(text[last:])
    return "".join(out)


def format_date(fmt: str, date: datetime.date) -> str:
    w = WEEKDAYS[date.weekday()]
    return (fmt.replace("{Y}", str(date.year)).replace("{y}", f"{date.year % 100:02d}")
            .replace("{MM}", f"{date.month:02d}").replace("{M}", str(date.month))
            .replace("{DD}", f"{date.day:02d}").replace("{D}", str(date.day)).replace("{W}", w))


def _find_date(text):
    for pattern in _DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            year = int(m.group("y")) if m.groupdict().get("y") else 2000 + int(m.group("yy"))
            try:
                value = datetime.date(year, int(m.group("m")), int(m.group("d")))
            except ValueError:
                continue
            return m, value
    return None, None


_NOT_UNIT = {"단계", "체계", "관계", "설계", "회계", "세계", "한계", "통계", "연계", "합계", "생계", "업계", "학계",
             "기관", "주관", "지원", "공원", "인원", "자원", "재원", "확대", "도입", "예정", "추진", "계획", "부처", "정부",
             "전부", "일부", "내부", "외부", "세부", "본부", "청구", "연구", "요구", "도구", "시도", "제도", "정도", "속도"}


# 중앙행정기관 이름(korean-report-hwpx 보도자료 52개 기관 + 그 밖의 기관). "국무조정실"처럼 내부 조직 끝말(실·처)로
# 끝나는 기관을 기관으로 분류한다.
_AGENCIES = frozenset((
    "개인정보보호위원회", "경찰청", "고용노동부", "공정거래위원회", "과학기술정보통신부", "관세청", "교육부", "국가교육위원회",
    "국가데이터처", "국가보훈부", "국가유산청", "국무조정실", "국민권익위원회", "국방부", "국세청", "국토교통부",
    "금융위원회", "기본사회위원회", "기상청", "기획예산처", "기후에너지환경부", "농림축산식품부", "농촌진흥청", "문화체육관광부",
    "방송미디어통신위원회", "방위사업청", "법무부", "법제처", "병무청", "보건복지부", "산림청", "산업통상부",
    "새만금개발청", "성평등가족부", "소방청", "식품의약품안전처", "외교부", "우주항공청", "원자력안전위원회", "인구전략위원회",
    "인사혁신처", "재외동포청", "재정경제부", "조달청", "중소벤처기업부", "지식재산처", "질병관리청", "통일부",
    "해양경찰청", "해양수산부", "행정안전부", "행정중심복합도시건설청", "감사원", "국가정보원", "대통령비서실", "국가안보실",
    "대통령경호처", "방송통신위원회", "행정자치부", "서울특별시",
))


def _word_kind(word: str):
    w = word.strip("()[]〔〕<>「」 ")
    if not w or len(w) < 2 or not re.fullmatch(r"[가-힣A-Za-z0-9·ㆍ]+", w) or w in _NOT_UNIT:
        return None
    if re.search(r"\d", w):
        return None
    if w in _AGENCIES:
        return "org"
    if w.endswith(_DEPT_END):
        return "dept"
    if w.endswith(_OFFICE_END):
        return "office"
    if w.endswith(_ORG_END):
        return "org"
    return None


def parse_info(text: str) -> dict | None:
    """보고 주체 글 → {'fields': 값, 'template': 틀, 'date_format': 날짜 틀}. 날짜·부서·사람 중 하나도 없으면 None.

    틀 예: "{date}  {org}  {dept}", "({date}, {rank} {name}, ☎{phone})", "{date}  /  {dept}".
    """
    if not text or not text.strip():
        return None
    fields, spans = {}, []
    m, value = _find_date(text)
    date_format = None
    if m:
        fields["date"] = value.isoformat()
        date_format = _date_format(m)
        spans.append((m.start(), m.end(), "date"))
    people, starts = 0, []
    for pm in _PERSON.finditer(text):
        anchor = pm.start("rank") if pm.group("rank") else pm.start("unit")
        if any(s <= anchor < e for s, e, _ in spans) or people >= 4:
            continue
        suffix = "" if people == 0 else str(people + 1)
        starts.append((pm.start(), suffix))
        if pm.group("unit"):
            # "문화예술과장": 부서 + 장. 직위 값은 '과장'(부서 끝 글자 + 장), 틀에는 '{dept}장'을 남긴다.
            unit = pm.group("unit")
            fields.setdefault("dept" + suffix, unit)
            spans.append((pm.start("unit"), pm.end("unit"), "dept" + suffix))
            fields["rank" + suffix] = unit[-1] + "장"
        else:
            fields["rank" + suffix] = pm.group("rank")
            spans.append((pm.start("rank"), pm.end("rank"), "rank" + suffix))
        fields["name" + suffix] = pm.group("name")
        spans.append((pm.start("name"), pm.end("name"), "name" + suffix))
        people += 1
    # 전화: 사람마다(바로 앞 사람의 번호로) 따로 둔다. 사람이 없으면 첫 번호만.
    for pm in _PHONE.finditer(text):
        a = pm.start("num") if pm.group("num") else pm.start()
        if any(s <= a < e for s, e, _ in spans):
            continue
        owner = [sfx for st, sfx in starts if st < a]
        key = "phone" + (owner[-1] if owner else "")
        if key in fields:
            continue
        fields[key] = pm.group("num").strip()
        spans.append((a, pm.end(), key))
    # 나머지 낱말: 기관·부서
    spans.sort()
    rest, cursor = [], 0
    for s, e, _ in spans:
        rest.append((cursor, s))
        cursor = e
    rest.append((cursor, len(text)))
    for s, e in rest:
        for wm in re.finditer(r"[^\s/|,·()\[\]〔〕<>「」:]+(?:\s[^\s/|,·()\[\]〔〕<>「」:]+)?", text[s:e]):
            word = wm.group(0)
            for piece_m in re.finditer(r"[^\s]+", word):
                piece = piece_m.group(0)
                kind = _word_kind(piece)
                if kind and kind not in fields and not any(s2 <= s + wm.start() + piece_m.start() < e2 for s2, e2, _ in spans):
                    a = s + wm.start() + piece_m.start()
                    fields[kind] = piece
                    spans.append((a, a + len(piece), kind))
    if not ({"date", "dept", "name"} & set(fields)):
        return None
    # 날짜·사람 없이 기관·부서 낱말만 있으면 짧은 글(부서명 줄)만 보고 주체로 본다(본문 문장 오인 방지).
    if not ({"date", "name", "phone"} & set(fields)):
        words = re.findall(r"[^\s/|,·()]+", text)
        if len(words) > 4 or len(text) > 40:
            return None
    spans.sort()
    template, cursor = [], 0
    for s, e, kind in spans:
        template.append(text[cursor:s].replace("{", "{{").replace("}", "}}"))
        template.append("{" + kind + "}")
        cursor = e
    template.append(text[cursor:].replace("{", "{{").replace("}", "}}"))
    return {"fields": fields, "template": "".join(template), "date_format": date_format}


_ORDER = ("org", "office", "dept", "rank", "name", "phone") + tuple(
    f"{k}{n}" for n in (2, 3, 4) for k in ("dept", "rank", "name", "phone"))


def render_info(template: str, date_format: str | None, fields: dict) -> str:
    """틀에 값을 채운다.

    구분자(공백 2칸 이상, /, |, 쉼표)로 나뉜 묶음 단위로 본다. 묶음의 칸이 모두 비면 묶음과 구분자를 함께 뺀다
    (예: '☎{phone}'의 ☎도 함께). 틀에 없는 값(예: 틀은 날짜·부서뿐인데 대상에 이름이 있음)은 버리지 않고
    처음 비운 묶음 자리에, 없으면 끝(닫는 괄호 앞)에 같은 구분자로 넣는다.
    """
    values = dict(fields)
    if values.get("date") and date_format:
        values["date"] = format_date(date_format, datetime.date.fromisoformat(values["date"]))
    # 이름이 없는 사람 자리('{dept}장: {name} ☎{phone}', '{rank3}: {name3} ☎{phone3}')는 통째로 뺀다. 부서 값은 남긴다.
    for sfx in ("", "2", "3", "4"):
        if values.get("name" + sfx):
            continue
        pattern = (r"(\{dept%s\}장|\{rank%s\})\s*:?\s*\{name%s\}(\s*\(?\s*☎\s*\{phone%s\}\s*\)?)?"
                   % (sfx, sfx, sfx, sfx))
        template = re.sub(pattern, lambda m, x=sfx: ("{dept%s}" % x) if "{dept" in m.group(0) and values.get("dept" + x) else "",
                          template)
    template = re.sub(r" {3,}", "  ", template).strip() if template.strip() != template else template
    # 묶음 나누기(괄호 바깥 앞뒤는 따로 둔다)
    lead = re.match(r"^\s*[(\[〔<]?", template).group(0)
    tail = re.search(r"[)\]〕>]?\s*$", template[len(lead):]).group(0)
    body = template[len(lead):len(template) - len(tail)] if tail else template[len(lead):]
    pieces = re.split("(" + _SEP + ")", body)
    groups, seps = pieces[0::2], pieces[1::2]
    used = set(re.findall(r"\{([a-z0-9]+)\}", template))
    if "{dept}장" in template and "rank" in fields:
        used.add("rank")
    # 틀에 없는 값: 조직(기관·실국·부서)과 사람(직위 이름 ☎전화) 묶음으로 만든다.
    units = [values[k] for k in ("org", "office", "dept") if k not in used and values.get(k)]
    people = []
    for sfx in ("", "2", "3", "4"):
        name, rank, phone = values.get("name" + sfx), values.get("rank" + sfx), values.get("phone" + sfx)
        if "name" + sfx in used or not name:
            if phone and "phone" + sfx not in used and not name:
                people.append("☎" + phone)
            continue
        chunk = f"{rank} {name}" if rank and "rank" + sfx not in used else name
        if phone and "phone" + sfx not in used:
            chunk += f" ☎{phone}"
        people.append(chunk)
    for sfx in ("2", "3", "4"):
        if values.get("dept" + sfx) and "dept" + sfx not in used and values.get("name" + sfx) and "name" + sfx not in used:
            idx = [x for x in ("", "2", "3", "4") if values.get("name" + x) and "name" + x not in used].index(sfx)
            people[idx] = values["dept" + sfx] + " " + people[idx]
    out, dropped_at = [], None
    for i, group in enumerate(groups):
        keys = re.findall(r"\{([a-z0-9]+)\}", group)
        if not keys and not group.strip():
            continue                     # 사람 자리를 뺀 뒤 남은 빈 묶음
        if keys and not any(values.get(k) for k in keys):
            if dropped_at is None:
                dropped_at = len(out)
            continue
        text = group
        if "{dept}장" in text and not values.get("dept") and values.get("rank"):
            text = text.replace("{dept}장", values["rank"])   # 부서 없이 직위만: '과장 홍길동'
        for k in keys:
            text = text.replace("{" + k + "}", str(values.get(k) or ""))
        out.append((seps[i - 1] if i > 0 and i - 1 < len(seps) else None, re.sub(r"\s{2,}", " ", text).strip()
                    if any(not values.get(k) for k in keys) else text))
    main_sep = max(set(seps), key=seps.count) if seps else "  "
    if units:
        at = dropped_at if dropped_at is not None else len(out)
        if values.get("org") and "org" not in used:
            for idx, (_, text) in enumerate(out):
                if values.get("dept") and values["dept"] in text:
                    at = idx
                    break
        out.insert(at, (main_sep, " ".join(units)))
    if people:
        out.append((main_sep, ", ".join(people)))
    if not any(re.search(r"[0-9가-힣A-Za-z]", text) for _, text in out):
        return ""          # 채운 값이 하나도 없으면(예: 틀은 부서뿐인데 대상에 부서가 없음) 쓰지 않는다
    result = ""
    for i, (sep, text) in enumerate(out):
        if i:
            result += sep if sep is not None else main_sep
        result += text
    return (lead + result + tail).replace("{{", "{").replace("}}", "}").strip()


# ── HWPX 머리 구성 ──

def _tag(e) -> str:
    return e.tag.rsplit("}", 1)[-1]


def _text(e) -> str:
    return "".join((t.text or "") + "".join((c.tail or "") for c in t) for t in e.iter() if _tag(t) == "t")


_META_LABELS = re.compile(r"문서번호|결재|공개여부|방침번호|보도시점|배포|수신|경유|기관 로고|^보도(참고)?자료$")
_BODY_START = re.compile(r"^\s*(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]\s*\.|[□■ㅁ❶➊①]|\d{1,2}\s*\.(?!\s*\d)|[가-하]\s*\.(?!\s*\d)|[가-하]\)|\d{1,2}\)|ㅇ\s|○\s)")


class _Header:
    def __init__(self, header):
        fonts = {}
        for face in header.iter():
            if _tag(face) == "fontface" and face.get("lang") == "HANGUL":
                fonts.update({f.get("id"): f.get("face") for f in face if _tag(f) == "font"})
        self.chars, self.paras, self.fills = {}, {}, {}
        for e in header.iter():
            name = _tag(e)
            if name == "charPr":
                ref = next((x for x in e if _tag(x) == "fontRef"), None)
                self.chars[e.get("id")] = {
                    "font": fonts.get(ref.get("hangul")) if ref is not None else None,
                    "size_pt": int(e.get("height", "1000")) / 100,
                    "bold": any(_tag(x) == "bold" for x in e) or e.get("bold") == "1",
                    "color": (e.get("textColor") or "#000000").upper()}
            elif name == "paraPr":
                align = next((x.get("horizontal") for x in e.iter() if _tag(x) == "align"), None)
                self.paras[e.get("id")] = {"align": align}
            elif name == "borderFill":
                win = next((x for x in e.iter() if _tag(x) == "winBrush"), None)
                face = win.get("faceColor") if win is not None else None
                sides = {}
                for x in e:
                    if _tag(x) in ("leftBorder", "rightBorder", "topBorder", "bottomBorder"):
                        sides[_tag(x)[:-6]] = None if x.get("type") in (None, "NONE") else (x.get("color") or "#000000").upper()
                self.fills[e.get("id")] = {"fill": None if face in (None, "none") else face.upper(), "borders": sides}

    def char_of(self, element):
        """글이 가장 긴 run의 글자 모양."""
        best, size = None, -1
        for run in (x for x in element.iter() if _tag(x) == "run"):
            n = len(_text(run).strip())
            if n > size:
                best, size = run, n
        return dict(self.chars.get(best.get("charPrIDRef"), {})) if best is not None else {}


def _cells(table):
    out = []
    for tc in (x for x in table.iter() if _tag(x) == "tc"):
        addr = next((x for x in tc if _tag(x) == "cellAddr"), None)
        out.append(((int(addr.get("rowAddr", 0)), int(addr.get("colAddr", 0))) if addr is not None else (0, 0), tc))
    return out


def _top_elements(section, limit=14):
    """구역 첫 부분의 (종류, 요소) 목록: ('p', 문단) 또는 ('tbl', 표, 문단)."""
    items = []
    for p in section:
        if _tag(p) != "p":
            continue
        tables = [x for x in p.iter() if _tag(x) == "tbl"]
        if tables:
            # 바깥 표만(셀 안 표는 바깥 표의 일부)
            inner = {id(y) for t in tables for y in t.iter() if _tag(y) == "tbl" and y is not t}
            for t in tables:
                if id(t) not in inner:
                    items.append(("tbl", t, p))
        elif _text(p).strip():
            items.append(("p", p, p))
        if len(items) >= limit:
            break
    return items


def _public(value):
    """'_'로 시작하는 요소 참조 키를 뺀 사본(JSON으로 저장할 수 있게)."""
    if isinstance(value, dict):
        return {k: _public(v) for k, v in value.items() if not k.startswith("_")}
    if isinstance(value, list):
        return [_public(v) for v in value]
    return value


def detect_header(path: str | Path) -> dict:
    """HWPX 머리 구성: {'title': {...}, 'info': [...], 'overview': {...}|None}."""
    with zipfile.ZipFile(path) as z:
        header_root = ET.fromstring(z.read("Contents/header.xml"))
        names = sorted(n for n in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n))
        section = ET.fromstring(z.read(names[0]))
    return _public(analyze(header_root, section))


def analyze(header_root, section, start: int = 0) -> dict:
    """detect_header와 같되 요소 참조(_p: 구역 바로 아래 문단, _tbl: 표, _tc: 칸, _el: 글 요소)를 함께 둔다."""
    header = _Header(header_root)
    items = _top_elements(list(section)[start:] if start else section)
    # 본문 시작(Ⅰ. □ 1. 등) 전까지가 머리다.
    head = []
    for kind, e, p in items:
        if kind == "p" and _BODY_START.match(_text(e)):
            break
        head.append((kind, e, p))
    candidates = []          # (글자 크기, 순서, 제목 정보)
    for order, (kind, e, p) in enumerate(head):
        if kind == "p":
            text = _text(e).strip()
            if parse_info(text) and len(text) < 80 and not _looks_title(text):
                continue
            ch = header.char_of(e)
            candidates.append((ch.get("size_pt", 0), -order, {
                "container": "paragraph", "text": text, "char": ch,
                "align": header.paras.get(e.get("paraPrIDRef"), {}).get("align"), "order": order,
                "_p": p, "_el": e}))
        else:
            cells = _cells(e)
            if not cells:
                continue
            rows, cols = int(e.get("rowCnt", 1)), int(e.get("colCnt", 1))
            if rows > 4 or cols > 4:
                label = next((i for i, (_, tc) in enumerate(cells) if re.fullmatch(r"제\s*목", _text(tc).strip())), None)
                if label is not None and label + 1 < len(cells):
                    addr, tc = cells[label + 1]
                    candidates.append((header.char_of(tc).get("size_pt", 0), -order, {
                        "container": f"table{rows}x{cols}", "cell": list(addr), "text": _text(tc).strip(),
                        "char": header.char_of(tc), "align": None, "box": {}, "order": order, "form": "기안문",
                        "_p": p, "_tbl": e, "_tc": tc, "_el": tc}))
                continue
            texts = [_text(tc).strip() for _, tc in cells]
            if any(_META_LABELS.search(t) for t in texts if t) and not _looks_title(max(texts, key=len)):
                continue
            # 제목 칸: 글자가 가장 큰 칸
            best = max(cells, key=lambda c: (header.char_of(c[1]).get("size_pt", 0), len(_text(c[1]))))
            text = _text(best[1]).strip()
            if not text:
                continue
            ch = header.char_of(best[1])
            fill = header.fills.get(best[1].get("borderFillIDRef"), {})
            para = next((x for x in best[1].iter() if _tag(x) == "p"), None)
            candidates.append((ch.get("size_pt", 0), -order, {
                "container": f"table{rows}x{cols}", "cell": list(best[0]), "text": text, "char": ch,
                "align": header.paras.get(para.get("paraPrIDRef") if para is not None else None, {}).get("align"),
                "box": fill, "order": order, "_p": p, "_tbl": e, "_tc": best[1], "_el": best[1]}))
    title = max(candidates, key=lambda c: (_looks_title(c[2]["text"]), "form" in c[2], c[0], c[1]))[2] if candidates else None
    # 표지가 있는 문서(표지 제목 → 본문 첫머리에 같은 제목 반복)는 본문에 가장 가까운 제목을 머리로 본다.
    # 보고 주체·개요도 그 앞 같은 제목(표지) 뒤에서만 찾는다(표지는 건드리지 않는다).
    start = 0
    if title:
        key = re.sub(r"\s+", "", title["text"])
        same = sorted((c[2] for c in candidates if re.sub(r"\s+", "", c[2]["text"]) == key), key=lambda t: t["order"])
        if len(same) > 1:
            title = same[-1]
            start = title["order"]       # 표지 줄(날짜·기관)은 보고 주체로 보지 않는다
            title["cover"] = True
    info = []
    for order, (kind, e, p) in enumerate(head):
        if order < start:
            continue
        if kind == "p":
            text = _text(e).strip()
            parsed = parse_info(text)
            if parsed and len(text) < 100 and not (title and title["container"] == "paragraph" and title["order"] == order):
                info.append({"container": "paragraph", "position": "before_title" if title and order < title["order"] else "after_title",
                             "text": text, "char": header.char_of(e), "order": order,
                             "align": header.paras.get(e.get("paraPrIDRef"), {}).get("align"), **parsed, "_p": p, "_el": e})
        else:
            for addr, tc in _cells(e):
                text = _text(tc).strip()
                if title and title.get("order") == order and list(addr) == title.get("cell"):
                    continue
                parsed = parse_info(text)
                if parsed and len(text) < 100 and not _META_LABELS.search(text):
                    para = next((x for x in tc.iter() if _tag(x) == "p"), None)
                    info.append({"container": "cell", "table_order": order, "cell": list(addr),
                                 "in_title_table": bool(title and title.get("order") == order),
                                 "text": text, "char": header.char_of(tc),
                                 "align": header.paras.get(para.get("paraPrIDRef") if para is not None else None, {}).get("align"),
                                 **parsed, "_p": p, "_tbl": e, "_tc": tc, "_el": tc})
    overview = None
    if title:
        for order, (kind, e, p) in enumerate(head):
            if order <= title["order"] or kind != "tbl" or e.get("rowCnt") != "1" or e.get("colCnt") != "1":
                continue
            cells = _cells(e)
            text = _text(cells[0][1]).strip() if cells else ""
            if text and not parse_info(text) and not re.match(r"^\s*목\s*차", text) and not re.search(r"[ⅠⅡⅢ]\s*\.", text):
                overview = {"container": "table1x1", "text": text, "char": header.char_of(cells[0][1]),
                            "box": header.fills.get(cells[0][1].get("borderFillIDRef"), {}), "order": order,
                            "_p": p, "_tbl": e, "_tc": cells[0][1], "_el": cells[0][1]}
                break
    return {"title": title, "info": info, "overview": overview}


def _looks_title(text: str) -> bool:
    """제목다운 글: 12자 이상이고 날짜·전화만으로 된 글이 아니다."""
    t = re.sub(r"\s+", "", text or "")
    if len(t) < 12 and _META_LABELS.search(t):
        return False                     # '보도자료'·'문서번호' 같은 머리 표시어
    if len(t) < 4 or re.fullmatch(r"[\d.\-()'’年月日년월일:/,☎~\s]+", t):
        return False
    parsed = parse_info(text)
    return not (parsed and {"date", "name", "phone"} & set(parsed["fields"]))


# ── 머리 서식 복사(예시 문서 → 대상 문서) ──

_ID_ATTRS = {"charPrIDRef": "charProperties", "paraPrIDRef": "paraProperties", "borderFillIDRef": "borderFills"}


# 글 위치를 차지하지 않는 쪽·구역 단위 컨트롤. 문서(보고서) 첫 문단에 흔히 붙어 있다.
_PAGE_CONTROLS = frozenset({"colPr", "pageNum", "pageNumCtrl", "pageHiding", "newNum", "header", "footer"})


def _is_page_control(child):
    return _tag(child) == "secPr" or (_tag(child) == "ctrl" and any(_tag(y) in _PAGE_CONTROLS for y in child))


def _strip_section_controls(p):
    """구역 정의(secPr)와 쪽 단위 컨트롤(단·쪽 번호·쪽 감추기·머리말 등)을 빼서 돌려준다.

    예시 문서의 것은 대상에 옮기지 않고, 대상 문서의 것은 새 머리 첫 문단에 되돌린다(실측: 쪽 번호·단 설정이
    사라져 무결성 검사가 '컨트롤이 사라졌습니다'로 알림, 2026-10-10).
    """
    removed = []
    for run in [x for x in p if _tag(x) == "run"]:
        for child in list(run):
            if _is_page_control(child):
                run.remove(child)
                removed.append(child)
    return removed


def _drop_layout_cache(element):
    for p in [x for x in element.iter() if _tag(x) == "p"]:
        for cache in [x for x in p if _tag(x) == "linesegarray"]:
            p.remove(cache)


def build_spec(header_root, section) -> dict | None:
    """예시 문서의 머리 서식 복사 자료(서식 프로필에 저장). 제목이 없으면 None."""
    found = analyze(header_root, section)
    if not found["title"]:
        return None
    blocks, seen = [], set()
    entries = [("title", found["title"])] + [("info", i) for i in found["info"] if i["container"] == "paragraph"]
    if found["overview"]:
        entries.append(("overview", found["overview"]))
    order = {id(p): i for i, p in enumerate(section)}
    for role, item in sorted(entries, key=lambda e: order.get(id(e[1]["_p"]), 0)):
        p = item["_p"]
        if id(p) in seen:
            continue
        seen.add(id(p))
        clone = copy.deepcopy(p)
        _strip_section_controls(clone)
        _drop_layout_cache(clone)
        info_index = found["info"].index(item) if role == "info" else None
        blocks.append({"role": role, "info_index": info_index, "xml": ET.tostring(clone, encoding="unicode")})
    return {"version": 1, "header_xml": ET.tostring(header_root, encoding="unicode"), "blocks": blocks,
            **_public(found)}


def _paragraphs_with_text(element):
    return [p for p in element.iter() if _tag(p) == "p" and _text(p).strip()]


def _set_text(p, text):
    """문단 글을 바꾼다: 글이 가장 긴 run 하나에 넣고 다른 run의 글은 지운다(컨트롤은 둔다)."""
    runs = [r for r in p if _tag(r) == "run"]
    text_runs = [r for r in runs if any(_tag(x) == "t" for x in r)]
    keep = max(text_runs, key=lambda r: len(_text(r)), default=None)
    if keep is None:
        if not runs:
            return False
        keep = runs[0]
    for r in text_runs:
        for t in [x for x in r if _tag(x) == "t"]:
            r.remove(t)
        if r is not keep and not len(r):
            p.remove(r)
    ns = keep.tag.rsplit("}", 1)[0] + "}"
    t = type(keep)(ns + "t", {})
    t.text = text
    keep.append(t)
    return True


_INLINE_OBJECTS = {"pic", "equation", "ole", "rect", "ellipse", "line", "arc", "polygon", "curve", "container",
                   "textart", "connectLine", "video", "chart"}


def _content_paragraphs(element):
    """글이나 글 사이 개체(그림·수식 등)가 있는 문단."""
    out = []
    for q in element.iter():
        if _tag(q) != "p":
            continue
        if _text(q).strip() or any(_tag(x) in _INLINE_OBJECTS for r in q if _tag(r) == "run" for x in r):
            out.append(q)
    return out


def _move_runs(slot, source, keep="__KEEP__"):
    """slot 문단의 run을 source 문단의 run 사본으로 바꾼다. 글자 모양은 slot의 대표(가장 긴 글) 모양으로 맞춘다.

    제목 사이 그림(축제 로고 등)·수식 같은 개체를 잃지 않게 글이 아니라 run을 옮긴다. 옮긴 run에는 keep 표시를 해
    예시 ID 변환(_remap)에서 빼지 않게 한다(글자 모양 ID는 예시 것이라 변환 대상).
    """
    runs = [r for r in slot if _tag(r) == "run"]
    text_runs = [r for r in runs if _text(r).strip()] or runs
    char = max(text_runs, key=lambda r: len(_text(r)), default=None)
    char_id = char.get("charPrIDRef") if char is not None else None
    for r in runs:
        if not any(_is_page_control(x) for x in r):
            slot.remove(r)
    for r in [x for x in source if _tag(x) == "run"]:
        clone = copy.deepcopy(r)
        for child in list(clone):
            if _tag(child) == "secPr":
                clone.remove(child)      # 구역 정의는 머리 첫 문단에 따로 되돌린다(최상위 문단의 쪽 컨트롤은 이미 뺐다)
        if not len(clone) and not (clone.text or "").strip():
            continue
        if char_id:
            clone.set("charPrIDRef", char_id)
        for inner in clone.iter():
            if inner is not clone and any(a in inner.attrib for a in _ID_ATTRS):
                inner.set(keep, "1")      # 개체 안 글상자 등: 대상 문서 ID 그대로
        slot.append(clone)


def _remap(element, maps):
    for x in element.iter():
        if x.attrib.pop("__KEEP__", None):
            continue
        for attr, group in _ID_ATTRS.items():
            if attr in x.attrib and group in maps:
                x.set(attr, maps[group].get(x.get(attr), x.get(attr)))
        if "styleIDRef" in x.attrib:
            x.set("styleIDRef", "0")
        if _tag(x) == "tbl" and x.get("id"):
            x.set("id", str(random.randint(10 ** 8, 2 * 10 ** 9)))


def squeeze_date_cells(table) -> int:
    """표 칸 중 날짜가 든 짧은 칸은 '한 줄로 입력'(lineWrap=SQUEEZE)으로 둔다(사용자 요청, 2026-10-10)."""
    count = 0
    for _, tc in _cells(table):
        text = _text(tc).strip()
        m, _ = _find_date(text)
        if m and len(text) <= 40:
            sub = next((x for x in tc if _tag(x) == "subList"), None)
            if sub is not None and sub.get("lineWrap") != "SQUEEZE":
                sub.set("lineWrap", "SQUEEZE")
                count += 1
    return count


def target_summary(header_root, section, start: int = 0) -> dict:
    """대상 문서 머리 값(제목 글·보고 주체 값·개요 글)."""
    found = analyze(header_root, section, start)
    title = found["title"]
    fields = {}
    for item in found["info"]:
        for k, v in item["fields"].items():
            fields.setdefault(k, v)
    return {"title": [_text(p).strip() for p in _paragraphs_with_text(title["_el"])] if title else [],
            "fields": fields,
            "overview": [_text(p).strip() for p in _paragraphs_with_text(found["overview"]["_el"])] if found["overview"] else []}


def apply_header(header_root, section, spec: dict, merge_refs, fit_table=None, start: int = 0) -> dict:
    """대상 문서(header_root, section)의 머리를 spec(build_spec 결과)의 구성·서식으로 다시 만든다.

    merge_refs(header_root, sample_header_root) → {'charProperties': {옛 ID: 새 ID}, ...}(앱의 제목_참조병합).
    대상의 제목 글·개요 글은 그대로 옮기고, 보고 주체 값(날짜·기관·부서·직위·이름·전화)은 예시의 표기 틀로 다시 쓴다.
    대상에 제목이 없으면 아무것도 바꾸지 않는다. 돌려주는 값: 통계.
    """
    target = analyze(header_root, section, start)
    title = target["title"]
    if not title or not spec or not spec.get("blocks"):
        return {"applied": 0, "reason": "제목 없음" if not title else "예시 머리 없음"}
    values = target_summary(header_root, section, start)
    title_sources = _content_paragraphs(title["_el"]) or [title["_el"]]
    fields = values["fields"]
    overview_lines = values["overview"]
    # 지울 대상 머리 문단(구역 바로 아래 문단)
    remove = [title["_p"]] + [i["_p"] for i in target["info"] if i["container"] == "paragraph"]
    if target["overview"]:
        remove.append(target["overview"]["_p"])
    top = list(section)
    remove = sorted({id(p): p for p in remove}.values(), key=top.index)
    at = top.index(remove[0])
    keep_controls = []
    # 글만 다시 쓰는 칸(보고 주체 칸)에 붙어 있던 컨트롤은 새 제목 칸 문단에 옮겨 잃지 않는다.
    cell_controls = []
    for item in target["info"]:
        if item["container"] == "cell":
            for q in (x for x in item["_tc"].iter() if _tag(x) == "p"):
                for r in (x for x in q if _tag(x) == "run"):
                    cell_controls += [copy.deepcopy(c) for c in r if _tag(c) == "ctrl"]
    for p in remove:
        keep_controls += _strip_section_controls(p)
        section.remove(p)
    sample_header = ET.fromstring(spec["header_xml"])
    maps = merge_refs(header_root, sample_header)
    sample_info = spec.get("info") or []
    new_blocks, written = [], {"title": 0, "info": 0, "overview": 0, "squeezed": 0}
    for block in spec["blocks"]:
        p = ET.fromstring(block["xml"])
        if block["role"] == "title":
            el = p
            if (spec.get("title") or {}).get("container", "paragraph") != "paragraph":
                tables = [x for x in p.iter() if _tag(x) == "tbl"]
                table = tables[0] if tables else None
                cell = next((tc for addr, tc in _cells(table) if list(addr) == spec["title"].get("cell")), None) \
                    if table is not None else None
                if cell is None:
                    continue
                el = cell
                # 같은 표 안의 보고 주체 칸(날짜 칸·담당자 칸)
                for info in sample_info:
                    if info.get("container") == "cell" and info.get("in_title_table"):
                        tc = next((c for a, c in _cells(table) if list(a) == info["cell"]), None)
                        paras = _paragraphs_with_text(tc) if tc is not None else []
                        text = render_info(info["template"], info.get("date_format"), fields) if fields else ""
                        if paras:
                            _set_text(paras[0], text)
                            for extra in paras[1:]:
                                _set_text(extra, "")
                            written["info"] += 1
                written["squeezed"] += squeeze_date_cells(table)
            slots = _paragraphs_with_text(el) or [x for x in el.iter() if _tag(x) == "p"][:1]
            sources = list(title_sources)
            if len(sources) > len(slots):
                # 예시 칸 문단이 더 적으면 남는 대상 문단은 마지막 칸 문단 뒤에 같은 모양으로 붙인다.
                extra = sources[len(slots) - 1:]
                sources = sources[:len(slots) - 1] + [extra]
            offset = len(slots) - len(sources)
            parents = {c: par for par in el.iter() for c in par}
            for i, slot in enumerate(slots):
                if i < offset:
                    # 예시 칸 문단이 더 많으면(부제+제목) 끝에서부터 채우고 남는 앞 문단은 지운다.
                    parent = parents.get(slot)
                    if parent is not None and len([y for y in parent if _tag(y) == "p"]) > 1:
                        parent.remove(slot)
                    else:
                        _set_text(slot, "")
                    continue
                src = sources[i - offset]
                if isinstance(src, list):
                    parent = parents.get(slot)
                    _move_runs(slot, src[0])
                    for j, more in enumerate(src[1:], 1):
                        q = copy.deepcopy(slot)
                        _move_runs(q, more)
                        if parent is not None:
                            parent.insert(list(parent).index(slot) + j, q)
                else:
                    _move_runs(slot, src)
            if cell_controls and slots:
                run = next((x for x in slots[-1] if _tag(x) == "run"), None)
                if run is not None:
                    for c in cell_controls:
                        for inner in c.iter():
                            if any(a in inner.attrib for a in _ID_ATTRS):
                                inner.set("__KEEP__", "1")
                        run.insert(0, c)
                    cell_controls = []
            written["title"] += 1
        elif block["role"] == "info":
            info = sample_info[block["info_index"]] if block.get("info_index") is not None else None
            if not info or not fields:
                continue
            text = render_info(info["template"], info.get("date_format"), fields)
            if not text:
                continue
            _set_text(p, text)
            written["info"] += 1
        elif block["role"] == "overview":
            if not overview_lines:
                continue
            tc = next((x for x in p.iter() if _tag(x) == "tc"), None)
            sub = next((x for x in tc if _tag(x) == "subList"), None) if tc is not None else None
            templates = [x for x in sub if _tag(x) == "p"] if sub is not None else []
            styled = [x for x in templates if _text(x).strip()] or templates
            if not styled:
                continue
            for x in templates:
                sub.remove(x)
            for i, line in enumerate(overview_lines):
                q = copy.deepcopy(styled[min(i, len(styled) - 1)])
                _set_text(q, line)
                sub.append(q)
            written["overview"] += 1
        _remap(p, maps)
        new_blocks.append(p)
    if target["info"] and not written["info"]:
        # 예시에 보고 주체 자리가 없거나(표지에만 있는 서식 등) 쓸 값이 없으면 대상의 보고 주체를 잃지 않게 그대로 둔다.
        # 문단은 그대로, 제목 표 칸에 있던 글은 그 칸 첫 문단 모양 그대로 제목 아래 문단으로 옮긴다.
        at_title = next((i for i, b in enumerate(new_blocks) if b is not None), 0)
        kept = []
        for item in target["info"]:
            if item["container"] == "paragraph":
                q = item["_p"]
            else:
                first = next((x for x in item["_tc"].iter() if _tag(x) == "p"), None)
                if first is None:
                    continue
                q = copy.deepcopy(first)
                for r in (x for x in q if _tag(x) == "run"):
                    for c in [x for x in r if _tag(x) == "ctrl"]:
                        r.remove(c)       # 칸 컨트롤은 이미 새 제목 칸으로 옮겼다
                _set_text(q, item["text"])
            for x in q.iter():
                if any(a in x.attrib for a in _ID_ATTRS):
                    x.set("__KEEP__", "1")
            _remap(q, {})          # 표시만 지운다(대상 문서 ID 그대로)
            kept.append(q)
        for i, q in enumerate(kept):
            new_blocks.insert(at_title + 1 + i, q)
        written["info_kept"] = len(kept)
    if target["overview"] and not any(b["role"] == "overview" for b in spec["blocks"]):
        new_blocks.append(target["overview"]["_p"])     # 예시에 개요 상자가 없으면 대상 개요는 그대로 둔다
    if not new_blocks:
        for i, p in enumerate(remove):
            section.insert(at + i, p)
        return {"applied": 0, "reason": "복사할 머리 없음"}
    if keep_controls:
        # 구역 정의는 새 첫 문단의 첫 run 앞에 되돌린다.
        first = new_blocks[0]
        run = next((x for x in first if _tag(x) == "run"), None)
        if run is None:
            ns = first.tag.rsplit("}", 1)[0] + "}"
            run = type(first)(ns + "run", {"charPrIDRef": "0"})
            first.insert(0, run)
        for i, control in enumerate(keep_controls):
            run.insert(i, control)
    for i, p in enumerate(new_blocks):
        section.insert(at + i, p)
        if fit_table is not None:
            for table in [x for x in p.iter() if _tag(x) == "tbl"]:
                fit_table(table)
    return {"applied": 1, **written}


def report_starts(section, is_title_table) -> list[int]:
    """여러 보고서를 묶은 문서에서 보고서 머리가 시작하는 구역 바로 아래 문단 번호들.

    is_title_table(표)가 참인 표(앱의 제목 표 판정)가 든 문단을 보고서 시작으로 본다. 첫 보고서는
    문서 맨 앞(0)부터 본다(제목 위 보고 주체 줄을 함께 다루려고).
    """
    starts = []
    for index, p in enumerate(section):
        if _tag(p) != "p":
            continue
        if any(_tag(t) == "tbl" and is_title_table(t) for r in p for t in r):
            starts.append(index)
    if not starts or starts[0] != 0:
        starts.insert(0, 0)          # 첫 제목이 판정되지 않은 문서(제목 위 보고 주체 줄 등)도 맨 앞부터 본다
    return starts
