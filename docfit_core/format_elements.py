"""서식 요소 전수 분석: 대표값 산출, 서식 표 예시 보관과 세부값 수정(한/글 COM 없음).

문서의 문장을 문두기호 계층별로, 제목·개요·중제목·붙임 서식 표는 칸(A1·A2·B2 …)별로 나눠
글자·문단·칸 서식 요소마다 값을 모으고, 가장 많이 쓴 값을 대표값으로 정한다. 대표값마다
표본 수·비율·다른 값 목록을 함께 남겨 서식 세부사항 창에서 확인하고 고칠 수 있게 한다.

예시 서식 문서에서 찾은 서식 표는 그 표가 쓰는 글자·문단·테두리 모양만 남긴 header 사본과 함께
보관한다. 사용자가 세부값을 고치면 사본의 해당 모양만 새 ID로 복제해 바꾸므로, 같은 모양을 함께
쓰던 다른 칸은 그대로다.

HWPX 문단 여백·간격은 hp:switch의 hp:case 값(실제 HWPUNIT, 1pt = 100)을 읽는다. hp:default에는
두 배 값이 들어 있고, 한/글 COM ParaShape도 그 두 배 값을 쓴다(실측 2026-10-03: COM 왼쪽 여백
2000 → case 1000, 줄 시작 위치 1000).
"""

from __future__ import annotations

from collections import Counter, OrderedDict, defaultdict
import copy
import re
import unicodedata
from pathlib import Path
from zipfile import ZipFile

from defusedxml import ElementTree as ET

from .style_unify import parenthetical_spans, unify_marker

LANGS = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")
HWPUNIT_PER_MM = 7200 / 25.4

UNDERLINE_TYPES = ("NONE", "BOTTOM", "CENTER", "TOP")
ALIGN_TYPES = ("JUSTIFY", "LEFT", "RIGHT", "CENTER", "DISTRIBUTE", "DISTRIBUTE_SPACE")
LINE_TYPES = ("PERCENT", "FIXED", "BETWEEN_LINES", "AT_LEAST")
# 한글 줄 나눔 기준(breakSetting breakNonLatinWord): 어절 단위 / 글자 단위
BREAK_TYPES = ("KEEP_WORD", "BREAK_WORD")
# 내어쓰기 기준: 둘째 줄이 라벨 뒤 글 시작 / 기호 뒤 글 시작에 맞음, 고정 값, 내어쓰기 없음
HANGING_RULES = ("after_label", "after_marker", "fixed", "none")
# 쪽 번호 컨트롤(hp:pageNum)에서 복사하는 속성: 위치(BOTTOM_CENTER 등)·번호 모양(DIGIT 등)·줄표 글자('-')
PAGE_NUMBER_KEYS = ("pos", "formatType", "sideChar")
# 문두기호 역할의 깊이(작을수록 상위). 깊은 항목 다음 얕은 항목이 오면 '계층 복귀'다.
ROLE_DEPTH = {"중제목": 0, "소제목": 1, "본문": 2, "내용": 3, "부연설명": 4}
VALIGN_TYPES = ("TOP", "CENTER", "BOTTOM")
BORDER_TYPES = ("NONE", "SOLID", "DASH", "DOT", "DASH_DOT", "DASH_DOT_DOT", "LONG_DASH", "CIRCLE",
                "DOUBLE_SLIM", "SLIM_THICK", "THICK_SLIM", "SLIM_THICK_SLIM")
BORDER_WIDTHS = ("0.1 mm", "0.12 mm", "0.15 mm", "0.2 mm", "0.25 mm", "0.3 mm", "0.4 mm", "0.5 mm",
                 "0.6 mm", "0.7 mm", "1.0 mm", "1.5 mm", "2.0 mm", "3.0 mm", "4.0 mm", "5.0 mm")
CHOICE_LABELS = {
    "NONE": "없음", "BOTTOM": "아래", "CENTER": "가운데", "TOP": "위",
    "JUSTIFY": "양쪽", "LEFT": "왼쪽", "RIGHT": "오른쪽", "DISTRIBUTE": "배분", "DISTRIBUTE_SPACE": "나눔",
    "PERCENT": "글자에 따라(%)", "FIXED": "고정 값", "BETWEEN_LINES": "여백만 지정", "AT_LEAST": "최소",
    "KEEP_WORD": "어절", "BREAK_WORD": "글자",
    "after_label": "라벨 뒤 글 시작", "after_marker": "기호 뒤 글 시작", "fixed": "고정 값", "none": "없음",
    "SOLID": "실선", "DASH": "파선", "DOT": "점선", "DASH_DOT": "일점쇄선", "DASH_DOT_DOT": "이점쇄선",
    "LONG_DASH": "긴 파선", "CIRCLE": "원형 점선", "DOUBLE_SLIM": "이중 실선",
    "SLIM_THICK": "얇고 굵은 이중선", "THICK_SLIM": "굵고 얇은 이중선", "SLIM_THICK_SLIM": "삼중선",
}

# 요소 이름 → (화면 이름, 값 종류, 선택지, 수정 가능). 값 종류:
# text 글자, pt 1/100pt(글자 크기), hpt HWPUNIT를 pt로 표시(문단 여백), mm HWPUNIT를 mm로 표시,
# pct %, int 정수, bool 예/아니오, color #RRGGBB, shade #RRGGBB 또는 없음, choice 선택지,
# border '종류|굵기|색'.
ELEMENT_SPECS = OrderedDict([
    ("font", ("글꼴", "text", None, True)),
    ("font_latin", ("영문 글꼴", "text", None, True)),
    ("size", ("글자 크기", "pt", None, True)),
    ("bold", ("굵게", "bool", None, True)),
    ("italic", ("기울임", "bool", None, True)),
    ("underline", ("밑줄", "choice", UNDERLINE_TYPES, True)),
    ("strikeout", ("취소선", "bool", None, True)),
    ("color", ("글자색", "color", None, True)),
    ("shade", ("음영색", "shade", None, True)),
    ("ratio", ("장평", "pct", None, True)),
    ("spacing", ("자간", "pct", None, True)),
    ("align", ("정렬", "choice", ALIGN_TYPES, True)),
    ("left", ("왼쪽 여백", "hpt", None, True)),
    ("right", ("오른쪽 여백", "hpt", None, True)),
    ("indent", ("첫 줄 들여쓰기(−는 내어쓰기)", "hpt", None, True)),
    ("prev", ("문단 위 간격", "hpt", None, True)),
    ("next", ("문단 아래 간격", "hpt", None, True)),
    ("line_type", ("줄 간격 종류", "choice", LINE_TYPES, True)),
    ("line", ("줄 간격 값", "int", None, True)),
    ("break_word", ("줄 나눔 기준(한글)", "choice", BREAK_TYPES, True)),
    ("lead_spaces", ("기호 앞 빈칸 수", "int", None, True)),
    ("after_spaces", ("기호 뒤 빈칸 수", "int", None, True)),
    ("marker_bold", ("문두기호 굵게", "bool", None, True)),
    ("label_bold", ("괄호 라벨 굵게", "bool", None, True)),
    ("hanging", ("내어쓰기 적용(여러 줄 문장)", "bool", None, True)),
    ("paren_delta", ("괄호 안 글자 줄임", "pt", None, True)),
    ("hanging_rule", ("내어쓰기 기준", "choice", HANGING_RULES, True)),
    ("return_prev", ("상위 항목으로 돌아올 때 문단 위 간격", "hpt", None, True)),
    ("width", ("너비", "mm", None, False)),
    ("height", ("높이", "mm", None, False)),
    ("margin_left", ("안 여백 왼쪽", "mm", None, True)),
    ("margin_right", ("안 여백 오른쪽", "mm", None, True)),
    ("margin_top", ("안 여백 위", "mm", None, True)),
    ("margin_bottom", ("안 여백 아래", "mm", None, True)),
    ("valign", ("세로 정렬", "choice", VALIGN_TYPES, True)),
    ("fill", ("배경색", "shade", None, True)),
    ("border_left", ("왼쪽 테두리", "border", None, True)),
    ("border_right", ("오른쪽 테두리", "border", None, True)),
    ("border_top", ("위 테두리", "border", None, True)),
    ("border_bottom", ("아래 테두리", "border", None, True)),
    ("out_left", ("바깥 여백 왼쪽", "mm", None, True)),
    ("out_right", ("바깥 여백 오른쪽", "mm", None, True)),
    ("out_top", ("바깥 여백 위", "mm", None, True)),
    ("out_bottom", ("바깥 여백 아래", "mm", None, True)),
    ("in_left", ("칸 기본 안 여백 왼쪽", "mm", None, True)),
    ("in_right", ("칸 기본 안 여백 오른쪽", "mm", None, True)),
    ("in_top", ("칸 기본 안 여백 위", "mm", None, True)),
    ("in_bottom", ("칸 기본 안 여백 아래", "mm", None, True)),
    ("page_width", ("용지 너비", "mm", None, False)),
    ("page_height", ("용지 높이", "mm", None, False)),
    ("page_left", ("쪽 왼쪽 여백", "mm", None, True)),
    ("page_right", ("쪽 오른쪽 여백", "mm", None, True)),
    ("page_top", ("쪽 위 여백", "mm", None, True)),
    ("page_bottom", ("쪽 아래 여백", "mm", None, True)),
    ("page_header", ("머리말 여백", "mm", None, True)),
    ("page_footer", ("꼬리말 여백", "mm", None, True)),
    ("page_gutter", ("제본 여백", "mm", None, True)),
    ("page_landscape", ("가로 방향 용지", "bool", None, False)),
])
CHAR_KEYS = ("font", "font_latin", "size", "bold", "italic", "underline", "strikeout",
             "color", "shade", "ratio", "spacing")
PARA_KEYS = ("align", "left", "right", "indent", "prev", "next", "line_type", "line", "break_word")
MARKER_KEYS = ("lead_spaces", "after_spaces", "marker_bold", "label_bold", "hanging", "paren_delta",
               "hanging_rule", "return_prev")
CELL_KEYS = ("width", "height", "margin_left", "margin_right", "margin_top", "margin_bottom", "valign",
             "fill", "border_left", "border_right", "border_top", "border_bottom")
TABLE_KEYS = ("width", "height", "out_left", "out_right", "out_top", "out_bottom",
              "in_left", "in_right", "in_top", "in_bottom",
              "fill", "border_left", "border_right", "border_top", "border_bottom")
PAGE_KEYS = ("page_width", "page_height", "page_left", "page_right", "page_top", "page_bottom",
             "page_header", "page_footer", "page_gutter", "page_landscape")

FORM_KINDS = ("title1", "title2", "title3", "overview", "midtitle1", "midtitle2", "attach1", "attach2", "box")
FORM_LABELS = {
    "title1": "제목 표 (2×2, 부제 없음)", "title2": "제목 표 (2×2, 부제 있음)", "title3": "제목 표 (2행 1열)",
    "overview": "개요 표", "midtitle1": "중제목 표 (1행 3열)", "midtitle2": "중제목 표 (1행 2열)",
    "attach1": "붙임 표 (1행 3열)", "attach2": "붙임 표 (1행 2열)", "box": "한 칸 상자",
}
# 서식 표 칸의 역할 이름(화면 표시용).
CELL_ROLES = {
    "title1": {"A1": "제목", "A2": "날짜", "B2": "담당자"},
    "title2": {"A1": "부제·제목", "A2": "날짜", "B2": "담당자"},
    "title3": {"A1": "부제·제목", "A2": "담당자"},
    "overview": {"A1": "개요"},
    "midtitle1": {"A1": "번호", "B1": "빈칸", "C1": "글"},
    "midtitle2": {"A1": "번호", "B1": "글"},
    "attach1": {"A1": "붙임", "B1": "빈칸", "C1": "글"},
    "attach2": {"A1": "붙임", "B1": "글"},
    "box": {"A1": "글"},
}
# 예시 표를 보관해 서식 적용에 쓰는 종류(한 칸 상자는 분석만 한다).
# 서식 적용에 쓰려고 표 XML을 보관하는 종류. 한 칸 상자(box)도 보관한다(2026-10-04 서식 복사 전면 복제).
SAMPLE_KINDS = ("title1", "title2", "title3", "overview", "midtitle1", "midtitle2", "attach1", "attach2", "box")

_CHAR_CHILD_ORDER = ("fontRef", "ratio", "spacing", "relSz", "offset", "italic", "bold", "underline",
                     "strikeout", "outline", "shadow", "emboss", "engrave", "supscript", "subscript")
_INLINE = {"fwSpace": " ", "nbSpace": " ", "tab": "\t", "lineBreak": "\n"}
_SPACES = " \t 　"


# ----------------------------------------------------------------------------
# 값 표시·입력
# ----------------------------------------------------------------------------

def element_label(key):
    return ELEMENT_SPECS.get(key, (key,))[0]


def element_editable(key):
    return bool(ELEMENT_SPECS.get(key, (None, None, None, False))[3])


def element_choices(key):
    """선택지가 있는 요소의 (화면 글자) 목록. 없으면 ()."""
    spec = ELEMENT_SPECS.get(key)
    if not spec:
        return ()
    if spec[1] == "bool":
        return ("예", "아니오")
    if spec[1] == "choice":
        return tuple(CHOICE_LABELS.get(value, value) for value in spec[2])
    return ()


def _mm(value):
    return round(float(value) / HWPUNIT_PER_MM, 1)


def format_value(key, value):
    """요소 값을 사람이 읽는 글자로 바꾼다. 값이 없으면 '-'."""
    if value is None:
        return "-"
    kind = ELEMENT_SPECS.get(key, (None, "text"))[1]
    if kind == "pt":
        return f"{value / 100:g}pt"
    if kind == "hpt":
        return f"{value / 100:g}pt"
    if kind == "mm":
        return f"{_mm(value):g}mm"
    if kind == "pct":
        return f"{value:g}%"
    if kind == "bool":
        return "예" if value else "아니오"
    if kind == "choice":
        return CHOICE_LABELS.get(value, str(value))
    if kind == "border":
        kind_, width, color = (str(value).split("|") + ["", "", ""])[:3]
        if kind_ == "NONE":
            return "없음"
        return f"{CHOICE_LABELS.get(kind_, kind_)} {width} {color}".strip()
    return str(value)


def parse_value(key, text):
    """화면에 입력한 글자를 저장 값으로 바꾼다. 잘못된 입력이면 ValueError."""
    label, kind, choices, _ = ELEMENT_SPECS[key]
    text = str(text or "").strip()
    number = re.sub(r"\s*(pt|mm|%)$", "", text, flags=re.I)
    try:
        if kind == "text":
            if not text or len(text) > 100:
                raise ValueError
            return text
        if kind == "pt":
            value = round(float(number) * 100)
            if not 0 <= value <= 400000:
                raise ValueError
            return value
        if kind == "hpt":
            value = round(float(number) * 100)
            if abs(value) > 1_000_000:
                raise ValueError
            return value
        if kind == "mm":
            value = round(float(number) * HWPUNIT_PER_MM)
            if not 0 <= value <= 1_000_000:
                raise ValueError
            return value
        if kind == "pct":
            value = int(round(float(number)))
            limits = (-50, 50) if key == "spacing" else (1, 500)
            if not limits[0] <= value <= limits[1]:
                raise ValueError
            return value
        if kind == "int":
            value = int(round(float(number)))
            if not 0 <= value <= 100000:
                raise ValueError
            return value
        if kind == "bool":
            if text in ("예", "true", "True", "1", "켜기", "O", "o"):
                return True
            if text in ("아니오", "false", "False", "0", "끄기", "X", "x"):
                return False
            raise ValueError
        if kind == "color":
            return _parse_color(text)
        if kind == "shade":
            if text in ("", "없음", "none", "NONE", "-"):
                return "없음"
            return _parse_color(text)
        if kind == "choice":
            for value in choices:
                if text in (value, CHOICE_LABELS.get(value)):
                    return value
            raise ValueError
        if kind == "border":
            return _parse_border(text)
    except (TypeError, ValueError):
        pass
    raise ValueError(f"'{label}' 값이 올바르지 않습니다: {text or '(빈칸)'}")


def _parse_color(text):
    match = re.fullmatch(r"#?([0-9A-Fa-f]{6})", text.strip())
    if not match:
        raise ValueError
    return "#" + match.group(1).upper()


def _parse_border(text):
    """'실선 0.12 mm #000000'·'없음'·'SOLID|0.12 mm|#000000'을 '종류|굵기|색'으로."""
    text = text.strip()
    if text in ("없음", "NONE", "-"):
        return "NONE|0.1 mm|#000000"
    parts = text.split("|") if "|" in text else None
    if parts is None:
        match = re.fullmatch(r"(.+?)\s+([0-9.]+)\s*mm\s+(#?[0-9A-Fa-f]{6})", text)
        if not match:
            raise ValueError
        parts = [match.group(1), match.group(2) + " mm", match.group(3)]
    kind = next((value for value in BORDER_TYPES if parts[0].strip() in (value, CHOICE_LABELS.get(value))), None)
    width = re.sub(r"\s*mm$", "", parts[1].strip())
    if kind is None or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", width):
        raise ValueError
    width = f"{float(width):.2f}".rstrip("0").rstrip(".")
    width = width if "." in width else width + ".0"
    return f"{kind}|{width} mm|{_parse_color(parts[2])}"


# ----------------------------------------------------------------------------
# XML 읽기
# ----------------------------------------------------------------------------

def _tag(element):
    return element.tag.rsplit("}", 1)[-1]


def _ns(element):
    return element.tag[:element.tag.index("}") + 1] if element.tag.startswith("{") else ""


def _child(element, name):
    return None if element is None else next((x for x in element if _tag(x) == name), None)


def _first(element, name):
    """첫 번째 하위 요소. hp:switch가 있으면 hp:case 쪽 값을 먼저 만난다."""
    return None if element is None else next((x for x in element.iter() if _tag(x) == name), None)


def _int(value, default=0):
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def run_text(run):
    """런의 글자. 고정폭·묶음 빈칸과 탭·강제 줄바꿈도 한 글자로 센다(한/글 글자 위치와 같음)."""
    parts = []
    for t in run:
        if _tag(t) != "t":
            continue
        parts.append(t.text or "")
        for sub in t:
            parts.append(_INLINE.get(_tag(sub), ""))
            parts.append(sub.tail or "")
    return "".join(parts)


NO_COLOR = "없음"


def _shade(value):
    """음영·배경색. 'none'과 흰색은 '없음'(대표값으로 비교할 수 있게 글자로 둔다)."""
    value = (value or "none").upper()
    return NO_COLOR if value in ("NONE", "#FFFFFF") else value


class HeaderIndex:
    """header.xml의 글꼴·글자·문단·테두리 모양을 ID로 찾고, 해석값을 한 번만 계산한다."""

    def __init__(self, header):
        self.header = header
        self.fonts = {}
        self.chars, self.paras, self.fills = {}, {}, {}
        for e in header.iter():
            name = _tag(e)
            if name == "fontface":
                self.fonts[(e.get("lang") or "").upper()] = {f.get("id"): f.get("face")
                                                           for f in e if _tag(f) == "font"}
            elif name == "charPr":
                self.chars[e.get("id")] = e
            elif name == "paraPr":
                self.paras[e.get("id")] = e
            elif name == "borderFill":
                self.fills[e.get("id")] = e
        self._cache = {}

    def _cached(self, kind, key, build):
        if (kind, key) not in self._cache:
            element = getattr(self, kind).get(key)
            self._cache[(kind, key)] = None if element is None else build(element)
        return self._cache[(kind, key)]

    def char(self, char_id):
        return self._cached("chars", char_id, lambda e: char_values(e, self.fonts))

    def para(self, para_id):
        return self._cached("paras", para_id, para_values)

    def fill(self, fill_id):
        return self._cached("fills", fill_id, border_fill_values)


def char_values(char_pr, fonts):
    ref = _first(char_pr, "fontRef")

    def face(lang):
        return None if ref is None else fonts.get(lang.upper(), {}).get(ref.get(lang))

    def lang_value(name, default):
        element = _first(char_pr, name)
        return _int(element.get("hangul"), default) if element is not None else default

    underline = _first(char_pr, "underline")
    strike = _first(char_pr, "strikeout")
    return {
        "font": face("hangul"), "font_latin": face("latin"),
        "size": _int(char_pr.get("height"), 0),
        "bold": _first(char_pr, "bold") is not None,
        "italic": _first(char_pr, "italic") is not None,
        "underline": (underline.get("type") or "NONE") if underline is not None else "NONE",
        # 한/글은 취소선 없는 글자에도 shape="3D"를 저장한다(실측). 선 모양만 취소선으로 본다.
        "strikeout": strike is not None and (strike.get("shape") or "NONE") not in ("NONE", "3D"),
        "color": (char_pr.get("textColor") or "#000000").upper(),
        "shade": _shade(char_pr.get("shadeColor")),
        "ratio": lang_value("ratio", 100),
        "spacing": lang_value("spacing", 0),
    }


def para_values(para_pr):
    align = _first(para_pr, "align")
    margin = _first(para_pr, "margin")
    line = _first(para_pr, "lineSpacing")
    breaking = _first(para_pr, "breakSetting")

    def value(name):
        item = _first(margin, name)
        return _int(item.get("value"), 0) if item is not None else 0

    return {
        "align": (align.get("horizontal") or "JUSTIFY") if align is not None else "JUSTIFY",
        "left": value("left"), "right": value("right"), "indent": value("intent"),
        "prev": value("prev"), "next": value("next"),
        "line_type": line.get("type") if line is not None else None,
        "line": _int(line.get("value"), 0) if line is not None else None,
        "break_word": (breaking.get("breakNonLatinWord") or "KEEP_WORD") if breaking is not None else None,
    }


def border_fill_values(border_fill):
    values = {}
    for side in ("left", "right", "top", "bottom"):
        item = _child(border_fill, side + "Border")
        if item is None:
            values["border_" + side] = "NONE|0.1 mm|#000000"
        else:
            values["border_" + side] = (f"{item.get('type') or 'NONE'}|{item.get('width') or '0.1 mm'}|"
                                        f"{(item.get('color') or '#000000').upper()}")
    brush = _first(border_fill, "winBrush")
    gradation = _first(border_fill, "gradation")
    if brush is not None and _shade(brush.get("faceColor")) != NO_COLOR:
        values["fill"] = _shade(brush.get("faceColor"))
    elif gradation is not None:
        values["fill"] = "그러데이션"
    elif _first(border_fill, "imgBrush") is not None:
        values["fill"] = "그림"
    else:
        values["fill"] = NO_COLOR
    return values


def cell_address(col, row):
    """0부터 센 열·행 번호를 'A1'·'B2'·'AA3' 꼴 칸 주소로."""
    letters, col = "", int(col)
    while True:
        col, rest = divmod(col, 26)
        letters = chr(ord("A") + rest) + letters
        if col == 0:
            break
        col -= 1
    return f"{letters}{int(row) + 1}"


def table_cells(table):
    """표의 (칸 주소, tc) 목록(문서 순서)."""
    result = []
    for tr in (x for x in table if _tag(x) == "tr"):
        for tc in (x for x in tr if _tag(x) == "tc"):
            addr = _child(tc, "cellAddr")
            col = _int(addr.get("colAddr"), 0) if addr is not None else 0
            row = _int(addr.get("rowAddr"), 0) if addr is not None else 0
            result.append((cell_address(col, row), tc))
    return result


def cell_paragraphs(tc):
    sub = _child(tc, "subList")
    return [] if sub is None else [p for p in sub if _tag(p) == "p"]


def _paragraph_runs(p):
    return [(run, run_text(run)) for run in p if _tag(run) == "run"]


def _line_count(p):
    segs = _child(p, "linesegarray")
    return sum(1 for _ in segs) if segs is not None else 0


def _dominant(counter):
    return counter.most_common(1)[0][0] if counter else None


# ----------------------------------------------------------------------------
# 문단·칸·표 하나의 요소 값
# ----------------------------------------------------------------------------

def _label_span(text, start):
    """문두기호 뒤 '(라벨)'의 (시작, 끝). 없으면 None."""
    index = start
    while index < len(text) and text[index] in _SPACES:
        index += 1
    if index >= len(text) or text[index] not in "(（":
        return None
    depth = 0
    for position in range(index, len(text)):
        char = text[position]
        if char in "\r\n":
            return None
        if char in "(（":
            depth += 1
        elif char in ")）":
            depth -= 1
            if depth == 0:
                return index, position + 1
    return None


def _prefix_width(text, end, size, ratio=100, spacing=0):
    """text[:end]의 어림 폭(HWPUNIT). 한글·전각·애매폭 글자는 글자 크기, 반각·빈칸은 절반, 장평·자간 반영."""
    total = 0.0
    for letter in text[:end]:
        wide = unicodedata.east_asian_width(letter) in ("W", "F", "A") and letter != " "
        total += size * ((1.0 if wide else 0.5) * ratio / 100 + spacing / 100)
    return total


def hanging_rule(text, values, marker, label, after):
    """여러 줄 문단의 내어쓰기 기준: 내어쓰기 양을 기호 뒤·라벨 뒤 글 시작 폭과 비교한다.

    가까운 쪽이 허용 오차(300 HWPUNIT 또는 15%) 안이면 그 기준, 아니면 고정 값. 내어쓰기가 없으면 'none'.
    """
    amount = -int(values.get("indent") or 0)
    if amount <= 20:
        return "none"
    size = values.get("size") or 1000
    ratio, spacing = values.get("ratio") or 100, values.get("spacing") or 0
    candidates = {"after_marker": _prefix_width(text, marker[1] + after, size, ratio, spacing)}
    if label:
        end = label[1]
        while end < len(text) and text[end] in _SPACES:
            end += 1
        candidates["after_label"] = _prefix_width(text, end, size, ratio, spacing)
    rule, guess = min(candidates.items(), key=lambda item: abs(item[1] - amount))
    return rule if abs(guess - amount) <= max(300, 0.15 * amount) else "fixed"


def paragraph_values(p, index, *, with_marker=True):
    """문단 하나의 (그룹 기호, 역할, 글자, 요소 값). 글자가 없으면 None.

    글자 요소는 문단 글자 수로 가중한 최다값이다. 글자 크기는 문장 안 괄호 부연(본문보다 작게 쓰는
    관행)을 빼고 정한다.
    """
    runs = _paragraph_runs(p)
    text = "".join(t for _, t in runs)
    if not text.strip():
        return None
    values = dict(index.para(p.get("paraPrIDRef")) or {})
    group, role, raw = unify_marker(text) if with_marker else ("", "", "")
    lead = len(text) - len(text.lstrip(_SPACES))
    marker = (lead, lead + len(raw)) if raw else None
    label = _label_span(text, marker[1]) if marker else None
    asides = parenthetical_spans(text, tuple(s for s in (marker, label) if s), include_trailing=True)
    weights = defaultdict(Counter)
    aside_sizes, marker_bold, label_bold = Counter(), Counter(), Counter()
    cursor = 0
    for run, part in runs:
        char = index.char(run.get("charPrIDRef"))
        if char:
            for offset, letter in enumerate(part):
                if letter.isspace():
                    continue
                position = cursor + offset
                in_aside = any(a <= position < b for a, b in asides)
                for key in CHAR_KEYS:
                    if key != "size" or not in_aside:
                        weights[key][char[key]] += 1
                if in_aside:
                    aside_sizes[char["size"]] += 1
                if marker and marker[0] <= position < marker[1]:
                    marker_bold[char["bold"]] += 1
                if label and label[0] <= position < label[1]:
                    label_bold[char["bold"]] += 1
        cursor += len(part)
    for key in CHAR_KEYS:
        values[key] = _dominant(weights[key])
    if values.get("size") is None and aside_sizes:
        values["size"] = _dominant(aside_sizes)
    if with_marker and group:
        after = 0
        while marker[1] + after < len(text) and text[marker[1] + after] in _SPACES:
            after += 1
        values.update(lead_spaces=lead, after_spaces=after,
                      marker_bold=_dominant(marker_bold),
                      label_bold=_dominant(label_bold) if label else None,
                      # 한 줄 문장은 내어쓰기가 보이지 않으므로 표본에서 뺀다.
                      hanging=(values.get("indent", 0) < -20) if _line_count(p) > 1 else None,
                      hanging_rule=hanging_rule(text, values, marker, label, after) if _line_count(p) > 1 else None,
                      paren_delta=(values["size"] - _dominant(aside_sizes))
                      if aside_sizes and values.get("size") else None)
    return group, role, text.strip(), values


def cell_values(tc, index):
    """칸 하나의 칸 요소와 글 있는 문단별 요소."""
    values = {}
    size = _child(tc, "cellSz")
    if size is not None:
        values.update(width=_int(size.get("width")), height=_int(size.get("height")))
    margin = _child(tc, "cellMargin")
    if margin is not None:
        for side in ("left", "right", "top", "bottom"):
            values["margin_" + side] = _int(margin.get(side))
    sub = _child(tc, "subList")
    values["valign"] = (sub.get("vertAlign") or "CENTER") if sub is not None else None
    values.update(index.fill(tc.get("borderFillIDRef")) or {})
    paragraphs, texts = [], []
    for p in cell_paragraphs(tc):
        found = paragraph_values(p, index, with_marker=False)
        if found:
            paragraphs.append(found[3])
            texts.append(found[2])
    return {"cell": values, "paras": paragraphs, "texts": texts}


def table_values(table, index):
    values = {}
    size = _child(table, "sz")
    if size is not None:
        values.update(width=_int(size.get("width")), height=_int(size.get("height")))
    for name, prefix in (("outMargin", "out_"), ("inMargin", "in_")):
        margin = _child(table, name)
        if margin is not None:
            for side in ("left", "right", "top", "bottom"):
                values[prefix + side] = _int(margin.get(side))
    values.update(index.fill(table.get("borderFillIDRef")) or {})
    return values


# ----------------------------------------------------------------------------
# 대표값
# ----------------------------------------------------------------------------

def tally(values):
    """값 목록의 대표값(최다값, 동률이면 먼저 나온 값)과 표본 정보. 값이 없으면 None."""
    usable = [value for value in values if value is not None]
    if not usable:
        return None
    counts = Counter(usable)
    votes = max(counts.values())
    best = next(value for value in usable if counts[value] == votes)
    return {"value": best, "votes": votes, "total": len(usable), "share": round(votes / len(usable), 3),
            "variants": [[value, count] for value, count in counts.most_common(6)]}


def _tally_all(records, keys):
    result = OrderedDict()
    for key in keys:
        found = tally([record.get(key) for record in records])
        if found is not None:
            result[key] = found
    return result


def _summarize_tables(records):
    """같은 종류 표들의 표·칸·칸 문단 요소 대표값."""
    cells = OrderedDict()
    for record in records:
        for addr, cell in record["cells"].items():
            cells.setdefault(addr, []).append(cell)
    summary = OrderedDict()
    for addr, items in cells.items():
        depth = max((len(item["paras"]) for item in items), default=0)
        summary[addr] = {
            "cell": _tally_all([item["cell"] for item in items], CELL_KEYS),
            "paras": [_tally_all([item["paras"][i] for item in items if len(item["paras"]) > i],
                                 CHAR_KEYS + PARA_KEYS) for i in range(depth)],
            "texts": next((item["texts"] for item in items if item["texts"]), []),
        }
    return {"table": _tally_all([record["table"] for record in records], TABLE_KEYS), "cells": summary}


def _record_table(table, index):
    return {"table": table_values(table, index),
            "cells": OrderedDict((addr, cell_values(tc, index)) for addr, tc in table_cells(table))}


def _agreement(record, summary):
    """한 표가 대표값과 몇 개 요소에서 같은지(보관할 예시 표를 고를 때 쓴다)."""
    score = sum(1 for key, item in summary["table"].items() if record["table"].get(key) == item["value"])
    for addr, cell in summary["cells"].items():
        own = record["cells"].get(addr)
        if own is None:
            continue
        score += sum(1 for key, item in cell["cell"].items() if own["cell"].get(key) == item["value"])
        for i, para in enumerate(cell["paras"]):
            if i < len(own["paras"]):
                score += sum(1 for key, item in para.items() if own["paras"][i].get(key) == item["value"])
    return score


def _sections(archive):
    names = [n for n in archive.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)]
    return sorted(names, key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[-1]).group(1)))


def analyze_format_elements(path, classify=None):
    """HWPX의 서식 요소를 모두 모아 계층·서식 표·일반 표별 대표값을 만든다.

    classify(tbl)는 본문 표의 종류(FORM_KINDS 중 하나, 한 칸 표는 'box')나 None(일반 표)을 돌려준다.
    제목 표 바로 뒤의 한 칸 표는 개요 표로 본다. 결과는 JSON으로 저장할 수 있고, 보관할 서식 표
    예시는 'samples'에 header 사본과 함께 담는다.
    """
    path = Path(path)
    with ZipFile(path) as archive:
        header = ET.fromstring(archive.read("Contents/header.xml"))
        roots = [ET.fromstring(archive.read(name)) for name in _sections(archive)]
    index = HeaderIndex(header)
    pages = []
    groups = OrderedDict()
    first_paragraphs = []
    forms = defaultdict(list)
    general = {"header": [], "body": []}
    table_count = 0
    previous_kind = None
    previous_depth = None
    title_bottom = None          # 제목·개요 표 문단 마지막 줄 아래(줄 배치 정보, HWPUNIT)
    spacing_rules = {}
    page_number = None
    for root in roots:
        # 쪽 번호 모양(위치·번호 모양·줄표): 처음 나온 것을 대표로 한다.
        if page_number is None:
            found_number = next((x for x in root.iter() if _tag(x) == "pageNum"), None)
            if found_number is not None:
                page_number = {k: found_number.get(k) for k in PAGE_NUMBER_KEYS if found_number.get(k) is not None}
        # 쪽 모양은 구역마다 하나다(구역 수만큼 표본).
        page_pr = _first(root, "pagePr")
        if page_pr is not None:
            margin = _child(page_pr, "margin")
            page = {"page_width": _int(page_pr.get("width")) or None,
                    "page_height": _int(page_pr.get("height")) or None,
                    "page_landscape": page_pr.get("landscape") == "NARROWLY"}
            if margin is not None:
                page.update({"page_" + k: _int(margin.get(k))
                             for k in ("left", "right", "top", "bottom", "header", "footer", "gutter")})
            pages.append(page)
        # 본문 직속 문단만 계층 표본으로 본다(표 칸·글상자 문단은 섞지 않는다).
        for p in (x for x in root if _tag(x) == "p"):
            found = paragraph_values(p, index)
            if found:
                group, role, text, values = found
                depth = ROLE_DEPTH.get(role) if group else None
                if depth is not None:
                    # 깊은 항목 다음 얕은 항목(계층 복귀)의 문단 위 간격을 따로 모은다.
                    if previous_depth is not None and depth < previous_depth:
                        values["return_prev"] = values.get("prev")
                    previous_depth = depth
                    if title_bottom is not None and "overview_to_first" not in spacing_rules:
                        top = _first_line_top(p)
                        if top is not None and top >= title_bottom[0]:
                            spacing_rules["overview_to_first"] = max(0, top - title_bottom[1])
                        title_bottom = None
                if len(first_paragraphs) < 2:
                    first_paragraphs.append({"font": values.get("font"), "size": values.get("size"),
                                             "bold": values.get("bold"), "text": text[:60]})
                key = (group, role) if group else ("", "일반 문장")
                entry = groups.setdefault(key, {"records": [], "samples": [], "order": len(groups)})
                entry["records"].append(values)
                if len(entry["samples"]) < 2:
                    entry["samples"].append(text[:80])
            for run in (x for x in p if _tag(x) == "run"):
                for table in (x for x in run if _tag(x) == "tbl"):
                    table_count += 1
                    kind = classify(table) if classify else None
                    if kind == "box" and previous_kind and previous_kind.startswith("title"):
                        kind = "overview"
                    previous_kind = kind
                    if kind in FORM_KINDS:
                        forms[kind].append((table, _record_table(table, index)))
                        if kind.startswith("title") or kind == "overview":
                            title_bottom = _last_line_bottom(p)
                        continue
                    for addr, tc in table_cells(table):
                        values = cell_values(tc, index)
                        # 첫 행(A1·B1 …)은 머리글, 나머지는 본문 칸으로 모은다.
                        bucket = general["header" if re.fullmatch(r"[A-Z]+1", addr) else "body"]
                        merged = dict(values["cell"])
                        if values["paras"]:
                            merged.update(values["paras"][0])
                        bucket.append(merged)
    paragraph_groups = []
    for (group, role), entry in groups.items():
        records = entry["records"]
        keys = CHAR_KEYS + PARA_KEYS + (MARKER_KEYS if group else ())
        paragraph_groups.append({"key": f"{group}|{role}", "marker": group, "role": role, "count": len(records),
                                 "samples": entry["samples"], "elements": _tally_all(records, keys)})
    form_summary, samples = OrderedDict(), OrderedDict()
    for kind in FORM_KINDS:
        if not forms.get(kind):
            continue
        summary = _summarize_tables([record for _, record in forms[kind]])
        summary.update(label=FORM_LABELS[kind], count=len(forms[kind]))
        form_summary[kind] = summary
        if kind in SAMPLE_KINDS:
            table, _ = max(forms[kind], key=lambda item: _agreement(item[1], summary))
            samples[kind] = extract_sample(header, table)
    tables = OrderedDict()
    for part in ("header", "body"):
        if general[part]:
            tables[part] = _tally_all(general[part], CELL_KEYS + CHAR_KEYS + PARA_KEYS)
    return {
        "version": 1, "source": path.name, "page": _tally_all(pages, PAGE_KEYS),
        "first_paragraphs": first_paragraphs,
        "paragraph_groups": paragraph_groups,
        "forms": form_summary,
        "tables": {"count": table_count - sum(len(v) for v in forms.values()), **tables},
        "spacing_rules": spacing_rules,
        "page_number": page_number,
        "samples": samples,
    }


def _first_line_top(p):
    """문단 첫 줄의 위치(줄 배치 정보 vertpos). 없으면 None."""
    segs = _child(p, "linesegarray")
    first = next((x for x in segs if _tag(x) == "lineseg"), None) if segs is not None else None
    return _int(first.get("vertpos"), None) if first is not None else None


def _last_line_bottom(p):
    """문단 마지막 줄의 (위치, 아래 끝 = 위치 + 높이 + 줄 간격). 줄 배치 정보가 없으면 None."""
    segs = _child(p, "linesegarray")
    lines = [x for x in segs if _tag(x) == "lineseg"] if segs is not None else []
    if not lines:
        return None
    last = lines[-1]
    top = _int(last.get("vertpos"))
    return top, top + _int(last.get("vertsize")) + _int(last.get("spacing"))


# ----------------------------------------------------------------------------
# 서식 표 예시 보관과 세부값 수정
# ----------------------------------------------------------------------------

_HEADER_GROUPS = ("borderFills", "charProperties", "paraProperties", "tabProperties")
_DROP_GROUPS = ("styles", "numberings", "bullets", "memoProperties", "trackChanges", "trackChangeAuthors")


def extract_sample(header, table):
    """표 하나와, 그 표가 쓰는 모양만 남긴 header 사본을 문자열로 보관한다."""
    used = {"borderFills": set(), "charProperties": set(), "paraProperties": set(), "tabProperties": set()}
    for element in table.iter():
        if element.get("borderFillIDRef") is not None:
            used["borderFills"].add(element.get("borderFillIDRef"))
        if _tag(element) == "run" and element.get("charPrIDRef") is not None:
            used["charProperties"].add(element.get("charPrIDRef"))
        if _tag(element) == "p" and element.get("paraPrIDRef") is not None:
            used["paraProperties"].add(element.get("paraPrIDRef"))
    clone = copy.deepcopy(header)
    groups = {_tag(e): e for e in clone.iter() if _tag(e) in _HEADER_GROUPS + _DROP_GROUPS}
    # 글자·문단 모양이 참조하는 테두리·탭도 함께 남긴다.
    for name in ("charProperties", "paraProperties"):
        group = groups.get(name)
        for item in (group if group is not None else ()):
            if item.get("id") in used[name]:
                for element in item.iter():
                    if element.get("borderFillIDRef") is not None:
                        used["borderFills"].add(element.get("borderFillIDRef"))
                if item.get("tabPrIDRef") is not None:
                    used["tabProperties"].add(item.get("tabPrIDRef"))
    ref_list = next((e for e in clone.iter() if _tag(e) == "refList"), clone)
    for name in _HEADER_GROUPS:
        group = groups.get(name)
        if group is None:
            # 서식 표 적용(제목_참조병합)은 네 목록이 모두 있어야 한다.
            group = type(clone)(_ns(clone) + name, {"itemCnt": "0"})
            ref_list.append(group)
            continue
        for item in list(group):
            if item.get("id") not in used[name]:
                group.remove(item)
        group.set("itemCnt", str(len(group)))
    for name in _DROP_GROUPS:
        group = groups.get(name)
        if group is not None:
            for parent in clone.iter():
                if group in list(parent):
                    parent.remove(group)
                    break
    return {"header_xml": ET.tostring(clone, encoding="unicode"),
            "table_xml": ET.tostring(table, encoding="unicode")}


def sample_record(sample):
    """보관한 예시 표 자체의 요소 값(수정 전 기준)."""
    header = ET.fromstring(sample["header_xml"].encode("utf-8"))
    table = ET.fromstring(sample["table_xml"].encode("utf-8"))
    return _record_table(table, HeaderIndex(header))


class _SamplePool:
    """예시 표 header 사본에 고친 모양을 새 ID로 더한다(같은 모양을 쓰는 다른 칸은 그대로)."""

    def __init__(self, header):
        self.header = header
        self.groups = {name: next((e for e in header.iter() if _tag(e) == name), None) for name in _HEADER_GROUPS}
        self.fontfaces = {(e.get("lang") or "").upper(): e for e in header.iter() if _tag(e) == "fontface"}

    def item(self, group, item_id):
        return next((x for x in self.groups[group] if x.get("id") == item_id), None)

    def clone(self, group, item_id):
        source = self.item(group, item_id)
        if source is None:
            return None, item_id
        clone = copy.deepcopy(source)
        target = self.groups[group]
        clone.set("id", str(max([_int(x.get("id"), -1) for x in target] + [-1]) + 1))
        target.append(clone)
        target.set("itemCnt", str(len(target)))
        return clone, clone.get("id")

    def font_id(self, lang, face):
        group = self.fontfaces.get(lang.upper())
        if group is None:
            return None
        found = next((f for f in group if f.get("face") == face), None)
        if found is None:
            # 다른 언어 목록에 같은 글꼴이 있으면 그 형식(TTF·HFT)을 따른다.
            known = next((f for g in self.fontfaces.values() for f in g if f.get("face") == face), None)
            prototype = known if known is not None else next(iter(group), None)
            if prototype is None:
                return None
            found = copy.deepcopy(prototype)
            found.set("face", face)
            if known is None:
                found.set("type", "TTF")
                for sub in list(found):
                    found.remove(sub)
            found.set("id", str(max([_int(f.get("id"), -1) for f in group] + [-1]) + 1))
            group.append(found)
            group.set("fontCnt", str(len(group)))
        return found.get("id")


def _set_flag(char_pr, name, on):
    current = _child(char_pr, name)
    if on and current is None:
        order = _CHAR_CHILD_ORDER.index(name)
        position = next((i for i, x in enumerate(char_pr)
                         if _tag(x) in _CHAR_CHILD_ORDER and _CHAR_CHILD_ORDER.index(_tag(x)) > order), len(char_pr))
        char_pr.insert(position, type(char_pr)(_ns(char_pr) + name, {}))
    elif not on and current is not None:
        char_pr.remove(current)


def _ensure_child(parent, name, attrib):
    current = _child(parent, name)
    if current is None:
        order = _CHAR_CHILD_ORDER.index(name) if name in _CHAR_CHILD_ORDER else len(_CHAR_CHILD_ORDER)
        position = next((i for i, x in enumerate(parent)
                         if _tag(x) in _CHAR_CHILD_ORDER and _CHAR_CHILD_ORDER.index(_tag(x)) > order), len(parent))
        current = type(parent)(_ns(parent) + name, dict(attrib))
        parent.insert(position, current)
    return current


def _edit_char(pool, char_pr, key, value):
    if key in ("font", "font_latin"):
        ref = _child(char_pr, "fontRef")
        if ref is None:
            return
        langs = ("latin",) if key == "font_latin" else tuple(lang for lang in LANGS if lang != "latin")
        for lang in langs:
            font_id = pool.font_id(lang, value)
            if font_id is not None:
                ref.set(lang, font_id)
    elif key == "size":
        char_pr.set("height", str(int(value)))
    elif key in ("bold", "italic"):
        _set_flag(char_pr, key, bool(value))
    elif key == "underline":
        _ensure_child(char_pr, "underline", {"type": "NONE", "shape": "SOLID", "color": "#000000"}).set("type", value)
    elif key == "strikeout":
        _ensure_child(char_pr, "strikeout", {"shape": "NONE", "color": "#000000"}).set(
            "shape", "SOLID" if value else "NONE")
    elif key == "color":
        char_pr.set("textColor", value)
    elif key == "shade":
        char_pr.set("shadeColor", "none" if value in (None, "없음") else value)
    elif key in ("ratio", "spacing"):
        element = _ensure_child(char_pr, key, {lang: "100" if key == "ratio" else "0" for lang in LANGS})
        for lang in LANGS:
            element.set(lang, str(int(value)))


_MARGIN_TAGS = {"left": "left", "right": "right", "indent": "intent", "prev": "prev", "next": "next"}


def _edit_para(para_pr, key, value):
    if key == "align":
        align = _first(para_pr, "align")
        if align is not None:
            align.set("horizontal", value)
        return
    if key == "break_word":
        breaking = _first(para_pr, "breakSetting")
        if breaking is not None:
            breaking.set("breakNonLatinWord", value)
        return
    # hp:switch가 있으면 case는 실제 값, default는 두 배 값을 함께 고친다.
    case = next((x for x in para_pr.iter() if _tag(x) == "case"), None)
    default = next((x for x in para_pr.iter() if _tag(x) == "default"), None)
    targets = [(case, 1), (default, 2)] if case is not None else [(para_pr, 1)]
    for scope, factor in targets:
        if scope is None:
            continue
        if key in _MARGIN_TAGS:
            item = _first(_first(scope, "margin"), _MARGIN_TAGS[key])
            if item is not None:
                item.set("value", str(int(value) * factor))
        elif key in ("line_type", "line"):
            line = _first(scope, "lineSpacing")
            if line is None:
                continue
            if key == "line_type":
                line.set("type", value)
            else:
                percent = (line.get("type") or "PERCENT") == "PERCENT"
                line.set("value", str(int(value) * (1 if percent else factor)))


def _edit_fill(border_fill, key, value):
    if key.startswith("border_"):
        kind, width, color = value.split("|")
        side = _child(border_fill, key[len("border_"):] + "Border")
        if side is None:
            side = type(border_fill)(_ns(border_fill) + key[len("border_"):] + "Border", {})
            border_fill.append(side)
        side.attrib.update(type=kind, width=width, color=color)
    elif key == "fill":
        value = None if value in (None, "없음") else value
        brush = _first(border_fill, "winBrush")
        if brush is None:
            if value is None:
                return
            # fillBrush는 core 네임스페이스(hc)에 있다. 다른 hc 요소가 없으면 한/글 기본값을 쓴다.
            core = next((_ns(x) for x in border_fill.iter() if _ns(x) and "core" in _ns(x)),
                        "{http://www.hancom.co.kr/hwpml/2011/core}")
            fill = _first(border_fill, "fillBrush")
            if fill is None:
                fill = type(border_fill)(core + "fillBrush", {})
                border_fill.append(fill)
            brush = type(border_fill)(core + "winBrush", {"faceColor": "none", "hatchColor": "#999999",
                                                           "alpha": "0"})
            fill.insert(0, brush)
        brush.set("faceColor", value or "none")


def apply_sample_edits(sample, table_edits=None, cell_edits=None):
    """보관한 예시 표에 고친 요소 값을 입힌 새 예시를 돌려준다.

    table_edits = {요소: 값}, cell_edits = {칸 주소: {"cell": {요소: 값}, "paras": {문단 번호: {요소: 값}}}}.
    글꼴은 문단에서 가장 긴 글자의 모양에만, 나머지 글자 요소는 그 문단의 모든 글자 모양에 입힌다
    (제목의 따옴표처럼 일부 글자만 다른 글꼴을 쓰는 관행을 지킨다).
    """
    header = ET.fromstring(sample["header_xml"].encode("utf-8"))
    table = ET.fromstring(sample["table_xml"].encode("utf-8"))
    pool = _SamplePool(header)

    def edit_border_fill(owner, edits):
        if not edits:
            return
        clone, new_id = pool.clone("borderFills", owner.get("borderFillIDRef"))
        if clone is None:
            return
        for key, value in edits.items():
            _edit_fill(clone, key, value)
        owner.set("borderFillIDRef", new_id)

    table_edits = dict(table_edits or {})
    margin_names = {"out_": "outMargin", "in_": "inMargin"}
    for key in [k for k in table_edits if k[:3] in ("out", "in_")]:
        prefix = "out_" if key.startswith("out_") else "in_"
        element = _child(table, margin_names[prefix])
        if element is not None:
            element.set(key[len(prefix):], str(int(table_edits.pop(key))))
    edit_border_fill(table, {k: v for k, v in table_edits.items() if k == "fill" or k.startswith("border_")})
    cells = dict(table_cells(table))
    for addr, edits in (cell_edits or {}).items():
        tc = cells.get(addr)
        if tc is None:
            continue
        cell = dict(edits.get("cell") or {})
        margin = _child(tc, "cellMargin")
        for side in ("left", "right", "top", "bottom"):
            if "margin_" + side in cell and margin is not None:
                margin.set(side, str(int(cell.pop("margin_" + side))))
                tc.set("hasMargin", "1")
        if "valign" in cell:
            sub = _child(tc, "subList")
            if sub is not None:
                sub.set("vertAlign", cell.pop("valign"))
        edit_border_fill(tc, {k: v for k, v in cell.items() if k == "fill" or k.startswith("border_")})
        written = [p for p in cell_paragraphs(tc) if "".join(run_text(r) for r in p if _tag(r) == "run").strip()]
        for number, para_edits in (edits.get("paras") or {}).items():
            number = int(number)
            if number >= len(written) or not para_edits:
                continue
            p = written[number]
            para_part = {k: v for k, v in para_edits.items() if k in PARA_KEYS}
            char_part = {k: v for k, v in para_edits.items() if k in CHAR_KEYS}
            if para_part:
                clone, new_id = pool.clone("paraProperties", p.get("paraPrIDRef"))
                if clone is not None:
                    for key, value in para_part.items():
                        _edit_para(clone, key, value)
                    p.set("paraPrIDRef", new_id)
            if char_part:
                runs = _paragraph_runs(p)
                lengths = Counter()
                for run, text in runs:
                    lengths[run.get("charPrIDRef")] += len(text.strip())
                main = _dominant(lengths)
                mapping = {}
                for run, _ in runs:
                    old = run.get("charPrIDRef")
                    if old not in mapping:
                        clone, new_id = pool.clone("charProperties", old)
                        if clone is not None:
                            for key, value in char_part.items():
                                if key in ("font", "font_latin") and old != main:
                                    continue
                                _edit_char(pool, clone, key, value)
                        mapping[old] = new_id
                    run.set("charPrIDRef", mapping[old])
    return {"header_xml": ET.tostring(header, encoding="unicode"),
            "table_xml": ET.tostring(table, encoding="unicode")}


def sample_edits(sample, summary):
    """대표값(또는 사용자가 고친 값)과 예시 표 자체 값이 다른 요소만 모은 수정 목록."""
    own = sample_record(sample)
    table_edits = {key: item["value"] for key, item in summary.get("table", {}).items()
                   if element_editable(key) and own["table"].get(key) != item["value"]}
    cell_edits = {}
    for addr, cell in summary.get("cells", {}).items():
        mine = own["cells"].get(addr)
        if mine is None:
            continue
        edits = {"cell": {key: item["value"] for key, item in cell.get("cell", {}).items()
                          if element_editable(key) and mine["cell"].get(key) != item["value"]},
                 "paras": {}}
        for number, para in enumerate(cell.get("paras", [])):
            if number >= len(mine["paras"]):
                break
            changed = {key: item["value"] for key, item in para.items()
                       if element_editable(key) and mine["paras"][number].get(key) != item["value"]}
            if changed:
                edits["paras"][number] = changed
        if edits["cell"] or edits["paras"]:
            cell_edits[addr] = edits
    return table_edits, cell_edits


def refresh_sample(sample, summary):
    """대표값·수정값을 예시 표에 반영한 새 예시. 바꿀 것이 없으면 원래 예시."""
    table_edits, cell_edits = sample_edits(sample, summary)
    if not table_edits and not cell_edits:
        return sample
    return apply_sample_edits(sample, table_edits, cell_edits)


# ----------------------------------------------------------------------------
# 세부사항 창의 항목과 프로필 반영
# ----------------------------------------------------------------------------

def group_title(group):
    marker = group["marker"] or "(기호 없음)"
    return f"{marker} {group['role']}".strip()


# 요소마다 서식 적용에 쓰는 방식(세부사항 창 '적용 방식' 열, 서식 관리의 복제 범위 요약)
MODE_VALUE, MODE_RULE, MODE_SHOW = "값 복사", "규칙 복사", "표시만"
_RULE_KEYS = {"hanging_rule", "return_prev", "label_bold", "paren_delta"}
# 문장(문두기호 계층)에서 아직 적용하지 않는 요소: 기호 앞·뒤 빈칸(공백 정규화와 겹침), 내어쓰기 여부(기준으로 대신함)
_GROUP_SHOW_KEYS = {"lead_spaces", "after_spaces", "hanging"}
_PAGE_SHOW_KEYS = {"page_width", "page_height", "page_landscape"}
# 일반 표 칸: 칸 크기·칸 안 여백·문단 여백은 글에 따라 달라 복사하지 않는다(표 기본 안 여백은 복사).
_TABLE_SHOW_KEYS = {"width", "height", "margin_left", "margin_right", "margin_top", "margin_bottom",
                    "left", "right", "indent", "prev", "next"}


def element_mode(key, path):
    """경로(detail_nodes의 경로)에 있는 요소의 적용 방식: 값 복사·규칙 복사·표시만."""
    area = path[0] if path else ""
    if area == "group":
        if key in _RULE_KEYS:
            return MODE_RULE
        return MODE_SHOW if key in _GROUP_SHOW_KEYS else MODE_VALUE
    if area == "page":
        return MODE_SHOW if key in _PAGE_SHOW_KEYS else MODE_VALUE
    if area == "table":
        return MODE_SHOW if key in _TABLE_SHOW_KEYS else MODE_VALUE
    if area == "form":
        # 서식 표는 예시 표를 통째로 복사한다. 표 폭은 쪽 최대 폭에 예시 열 비율(결정 1).
        return MODE_RULE if key == "width" else MODE_VALUE
    return MODE_VALUE


def coverage(analysis):
    """서식 요소 분석에서 서식 적용에 쓰는 요소 수: {"total", "applied", "shown"}."""
    total = applied = 0
    for path, _, _ in detail_nodes(analysis or {}):
        for key in element_map(analysis, path):
            total += 1
            applied += element_mode(key, path) != MODE_SHOW
    return {"total": total, "applied": applied, "shown": total - applied}


def detail_nodes(analysis):
    """세부사항 창 왼쪽 목록: (경로, 상위 경로, 이름). 경로로 element_map을 찾는다."""
    nodes = []
    if analysis.get("page"):
        nodes.append((("page",), None, "쪽 모양·여백"))
    groups = analysis.get("paragraph_groups", [])
    if groups:
        nodes.append((("groups",), None, "문장 (문두기호 계층별)"))
        for number, group in enumerate(groups):
            nodes.append((("group", number), ("groups",), f"{group_title(group)} · {group['count']}문장"))
    forms = analysis.get("forms", {})
    if forms:
        nodes.append((("forms",), None, "서식 표"))
        for kind, form in forms.items():
            nodes.append((("form", kind), ("forms",), f"{form['label']} · {form['count']}개"))
            nodes.append((("form", kind, "table"), ("form", kind), "표 전체"))
            for addr, cell in form["cells"].items():
                role = CELL_ROLES.get(kind, {}).get(addr, "")
                nodes.append((("form", kind, "cell", addr), ("form", kind),
                              f"{addr} 칸" + (f" ({role})" if role else "")))
                for number, _ in enumerate(cell["paras"]):
                    text = cell["texts"][number] if number < len(cell["texts"]) else ""
                    nodes.append((("form", kind, "para", addr, number), ("form", kind, "cell", addr),
                                  f"{addr} 문단 {number + 1}" + (f" · {text[:14]}" if text else "")))
    tables = analysis.get("tables", {})
    if tables.get("header") or tables.get("body"):
        nodes.append((("tables",), None, f"일반 표 · {tables.get('count', 0)}개"))
        for part, label in (("header", "첫 행(머리글) 칸"), ("body", "나머지(본문) 칸")):
            if tables.get(part):
                nodes.append((("table", part), ("tables",), label))
    return nodes


def element_map(analysis, path):
    """경로가 가리키는 {요소: 대표값 정보}. 목록 제목처럼 요소가 없는 경로는 {}."""
    try:
        if path == ("page",):
            return analysis["page"]
        if path[0] == "group":
            return analysis["paragraph_groups"][path[1]]["elements"]
        if path[0] == "form" and len(path) > 2:
            form = analysis["forms"][path[1]]
            if path[2] == "table":
                return form["table"]
            if path[2] == "cell":
                return form["cells"][path[3]]["cell"]
            if path[2] == "para":
                return form["cells"][path[3]]["paras"][path[4]]
        if path[0] == "table":
            return analysis["tables"][path[1]]
    except (KeyError, IndexError, TypeError):
        pass
    return {}


def set_value(analysis, path, key, value):
    """대표값을 사용자가 고친 값으로 바꾼다(분석 표본 정보는 그대로 둔다)."""
    item = element_map(analysis, path).get(key)
    if item is None:
        raise KeyError(key)
    if item["value"] != value:
        item.setdefault("analyzed", item["value"])
        item["value"] = value
        item["edited"] = item["analyzed"] != value
        if not item["edited"]:
            item.pop("analyzed", None)


_RULE_BOLD_OPTION = {"□": "box", "ㅇ": "o", "-": "dash", "※": "note"}


def _value(elements, key, default=None):
    item = elements.get(key)
    return default if item is None else item["value"]


# 문두기호 계층마다 글꼴·크기·굵게·문단 여백 밖에 더 복사하는 요소(계층_추가서식). 값은 분석값 그대로다.
EXTRA_KEYS = ("font_latin", "italic", "underline", "strikeout", "color", "shade", "ratio", "spacing",
              "align", "break_word")
# 줄 간격 종류 → 한/글 COM LineSpacingType(실측 2026-10-04: 0 %, 1 고정, 2 여백만, 3 최소)
LINE_TYPE_CODES = {"PERCENT": 0, "FIXED": 1, "BETWEEN_LINES": 2, "AT_LEAST": 3}


def apply_to_profile(profile):
    """서식 요소 분석(사용자 수정 포함)을 서식 적용에 쓰는 프로필 값에 반영한다.

    문두기호 규칙(글꼴·크기·굵게·기호 굵게·기호 앞 빈칸), 기호별 문단 모양(여백·간격·모든 종류의 줄
    간격), 계층별 추가 서식(영문 글꼴·기울임·밑줄·취소선·글자색·음영·장평·자간·정렬·줄 나눔 기준),
    쪽 여백(제본 여백 포함)·용지 크기, 일반 표 머리글·본문 글자, 보관한 서식 표 예시를 대표값에 맞춘다.
    이미 규칙이 있는 문두기호만 고친다(새 기호 규칙은 계층 분석이 정한다). 문단 모양 값은 HWPX case
    단위(실제 HWPUNIT) 그대로 둔다.
    """
    analysis = profile.get("element_analysis")
    if not analysis:
        return profile
    fmt = profile.setdefault("format", {})
    options = profile.setdefault("options", {})
    rules = fmt.get("기호_규칙", [])
    shapes = fmt.setdefault("복사_문단모양", {})
    for group in analysis.get("paragraph_groups", []):
        marker, elements = group["marker"], group["elements"]
        if not marker:
            continue
        for index, rule in enumerate(rules):
            if rule[0] != marker:
                continue
            font = _value(elements, "font", rule[2])
            size = _value(elements, "size")
            bold = bool(_value(elements, "bold", rule[4]))
            marker_bold = _value(elements, "marker_bold")
            rules[index] = (rule[0], _value(elements, "lead_spaces", rule[1]), font,
                            size / 100 if size else rule[3], bold,
                            bool(marker_bold) and not bold if marker_bold is not None else rule[5])
            if marker in _RULE_BOLD_OPTION:
                options[f"std_symbol_{_RULE_BOLD_OPTION[marker]}_bold"] = bold
            options.setdefault("symbol_fonts", {})[marker] = {
                "font": font, "size": f"{rules[index][3]:g}"}
        if marker in shapes or any(rule[0] == marker for rule in rules):
            shape = dict(shapes.get(marker, {}))
            for key, name in (("left", "LeftMargin"), ("right", "RightMargin"), ("indent", "Indentation"),
                              ("prev", "PrevSpacing"), ("next", "NextSpacing")):
                if key in elements:
                    shape[name] = int(elements[key]["value"])
            line_type = _value(elements, "line_type")
            if line_type in LINE_TYPE_CODES and "line" in elements:
                shape.update(LineSpacingType=LINE_TYPE_CODES[line_type], LineSpacing=int(elements["line"]["value"]))
            shapes[marker] = shape
            extra = {key: elements[key]["value"] for key in EXTRA_KEYS if key in elements}
            if extra:
                fmt.setdefault("계층_추가서식", {})[marker] = extra
    _apply_rules(profile, analysis)
    page = analysis.get("page", {})
    margins = fmt.setdefault("여백_mm", {})
    for key in ("left", "right", "top", "bottom", "header", "footer", "gutter"):
        if "page_" + key in page:
            margins[key] = round(page["page_" + key]["value"] / HWPUNIT_PER_MM, 3)
    # 용지 크기·방향은 복사하지 않고, 정리할 문서와 다르면 알리는 데 쓴다(결정 3).
    if "page_width" in page and "page_height" in page:
        fmt["용지_mm"] = {"width": round(page["page_width"]["value"] / HWPUNIT_PER_MM, 1),
                         "height": round(page["page_height"]["value"] / HWPUNIT_PER_MM, 1),
                         "landscape": bool(_value(page, "page_landscape", False))}
    tables = analysis.get("tables", {})
    table_format = profile.setdefault("table_format", {})
    for part in ("header", "body"):
        elements = tables.get(part) or {}
        for key in ("font", "size", "bold"):
            if key in elements:
                value = elements[key]["value"]
                table_format[f"{part}_{key}"] = value / 100 if key == "size" else value
    forms = analysis.get("forms", {})
    stored = profile.get("form_tables") or {}
    for kind, sample in list(stored.items()):
        if kind in forms:
            stored[kind] = refresh_sample(sample, forms[kind])
    sync_hierarchy(profile)
    return profile


def _apply_rules(profile, analysis):
    """글 길이에 따라 달라지는 것은 숫자 대신 규칙으로 복사한다(서식 복사 전면 복제 3단계).

    - 내어쓰기 기준: 라벨 뒤·기호 뒤면 내어쓰기 규칙을 켜고 그 기준으로 계산하게 한다(첫 줄 값은 복사하지 않음).
      고정 값·없음이면 규칙이 손대지 않고 복사한 첫 줄 값을 쓴다.
    - 괄호·콜론 라벨 굵게: 예시에서 라벨을 굵게 쓴 계층만 굵게 한다.
    - 괄호 안 글자 줄임: 예시에서 가장 많이 쓴 줄임 폭으로 괄호 부연설명 축소를 켠다.
    - 계층 복귀 간격, 제목·개요 표와 첫 문두기호 문장 사이 간격.
    """
    fmt, options = profile["format"], profile["options"]
    shapes = fmt.setdefault("복사_문단모양", {})
    rules, label_symbols, deltas = {}, {}, Counter()
    returns = {}
    for group in analysis.get("paragraph_groups", []):
        marker, elements = group["marker"], group["elements"]
        if not marker:
            continue
        rule = _value(elements, "hanging_rule")
        if rule in HANGING_RULES:
            rules[marker] = rule
            if rule in ("after_label", "after_marker") and marker in shapes:
                shapes[marker].pop("Indentation", None)
        bold = _value(elements, "label_bold")
        if bold is not None:
            label_symbols[marker] = bool(bold)
        delta = _value(elements, "paren_delta")
        if delta:
            deltas[int(delta)] += group.get("count", 1)
        back, normal = _value(elements, "return_prev"), _value(elements, "prev")
        if back is not None and normal is not None and abs(back - normal) > max(100, 0.1 * abs(normal)):
            returns[marker] = int(back)
    fmt["내어쓰기_규칙"] = rules
    options["std_hanging_indent"] = any(r in ("after_label", "after_marker") for r in rules.values())
    if label_symbols:
        options["paren_label_bold"] = any(label_symbols.values())
        options["label_symbols"] = {**options.get("label_symbols", {}), **label_symbols}
    if deltas:
        delta = deltas.most_common(1)[0][0]
        options["paren_shrink"] = delta > 0
        fmt["괄호_축소_pt"] = round(delta / 100, 1)
    fmt["복귀_간격"] = returns
    gap = (analysis.get("spacing_rules") or {}).get("overview_to_first")
    if gap is not None:
        fmt["제목뒤_간격"] = int(gap)
    # 쪽 번호는 모양만 복사한다(정리할 문서에 쪽 번호가 없으면 넣지 않음, 결정 4).
    if analysis.get("page_number"):
        fmt["쪽번호"] = dict(analysis["page_number"])


def sync_from_hierarchy(profile, before_styles):
    """계층 검토 창에서 바꾼 대표 항목의 글꼴·크기·여백을 서식 요소 대표값에도 옮긴다.

    before_styles는 계층 검토 전의 style_hierarchy['styles']다. 바뀐 값만 옮겨, 두 분석 방식의
    계산 차이로 사용자가 고치지 않은 값까지 수정값이 되지 않게 한다.
    """
    analysis = profile.get("element_analysis") or {}
    before = {(item.get("role"), item.get("marker")): item for item in before_styles or ()}
    fields = (("font", "font", lambda v: str(v)), ("size_pt", "size", lambda v: int(round(float(v) * 100))),
              ("left_hwpunit", "left", int), ("first_line_hwpunit", "indent", int),
              ("prev_spacing_typical", "prev", int))
    for item in (profile.get("style_hierarchy") or {}).get("styles", []):
        old = before.get((item.get("role"), item.get("marker")))
        if old is None:
            continue
        for number, group in enumerate(analysis.get("paragraph_groups", [])):
            if group["marker"] != item.get("marker"):
                continue
            for field, key, convert in fields:
                if item.get(field) == old.get(field) or item.get(field) is None:
                    continue
                if key in group["elements"]:
                    set_value(analysis, ("group", number), key, convert(item[field]))


def sync_hierarchy(profile):
    """세부사항에서 고친 문두기호 글꼴·크기·여백을 계층 검토 목록의 대표 항목에도 맞춘다."""
    hierarchy = profile.get("style_hierarchy") or {}
    for group in (profile.get("element_analysis") or {}).get("paragraph_groups", []):
        edited = {key: item["value"] for key, item in group["elements"].items() if item.get("edited")}
        if not group["marker"] or not edited:
            continue
        for name in ("styles", "variants"):
            items = [item for item in hierarchy.get(name, []) if item.get("marker") == group["marker"]]
            if not items:
                continue
            primary = max(items, key=lambda item: item.get("count", 0))
            if "font" in edited:
                primary["font"] = edited["font"]
            if "size" in edited:
                primary["size_pt"] = edited["size"] / 100
            for key, field in (("left", "left_hwpunit"), ("indent", "first_line_hwpunit")):
                if key in edited:
                    primary[field] = edited[key]
            if "prev" in edited:
                primary["prev_spacing_typical" if name == "styles" else "prev_spacing_hwpunit"] = edited["prev"]


# ----------------------------------------------------------------------------
# 요약 글
# ----------------------------------------------------------------------------

def summary_lines(analysis, limit=12):
    """분석 결과의 요약 줄(서식 등록 안내·로그용)."""
    lines = []
    for group in analysis.get("paragraph_groups", [])[:limit]:
        elements = group["elements"]
        parts = [format_value(key, elements[key]["value"]) for key in ("font", "size") if key in elements]
        if elements.get("bold", {}).get("value"):
            parts.append("굵게")
        if "align" in elements:
            parts.append(format_value("align", elements["align"]["value"]))
        lines.append(f"{group_title(group)} {group['count']}문장: {' '.join(parts)}")
    for kind, form in analysis.get("forms", {}).items():
        cells = []
        for addr, cell in form["cells"].items():
            first = cell["paras"][0] if cell["paras"] else {}
            look = " ".join(format_value(key, first[key]["value"]) for key in ("font", "size") if key in first)
            role = CELL_ROLES.get(kind, {}).get(addr, "")
            cells.append(f"{addr}{'(' + role + ')' if role else ''} {look}".strip())
        lines.append(f"{form['label']} {form['count']}개: " + ", ".join(cells))
    if analysis.get("tables", {}).get("count"):
        lines.append(f"일반 표 {analysis['tables']['count']}개")
    return lines
