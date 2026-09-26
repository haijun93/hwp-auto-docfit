"""작성 보조 도구: 금액 한글화·날짜·표 계산·숫자 변환·나이·번호 매기기·회신공문.

모두 문자열만 다루는 순수 함수라 한/글 없이 쓰고 시험할 수 있다. GUI(작성 도우미)는
붙여넣은 텍스트에 이 함수를 적용해 결과를 복사하게 한다.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import calendar
import re

WEEKDAYS = "월화수목금토일"

# ----------------------------------------------------------------------------
# B1. 금액 한글화
# ----------------------------------------------------------------------------

_DIGITS = "영일이삼사오육칠팔구"
_SMALL = ("", "십", "백", "천")
_LARGE = ("", "만", "억", "조", "경")
_NUMBER = re.compile(r"(?<![\d.])(\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\d])")


def number_to_hangul(n: int, full: bool = True) -> str:
    """정수를 한글 수사로. full=True면 공문서 금액처럼 '일백', '일천'의 '일'을 쓴다."""
    if n < 0:
        return "마이너스 " + number_to_hangul(-n, full)
    if n == 0:
        return "영"
    groups = []
    index = 0
    while n:
        n, chunk = divmod(n, 10000)
        if chunk:
            text = ""
            for pos in range(3, -1, -1):
                digit = chunk // (10 ** pos) % 10
                if digit:
                    word = _DIGITS[digit]
                    if digit == 1 and pos and not full:
                        word = ""
                    text += word + _SMALL[pos]
            if chunk == 1 and index and not full:
                text = "일"
            groups.append(text + _LARGE[index])
        index += 1
    return "".join(reversed(groups))


def _to_int(text: str) -> int:
    return int(text.replace(",", ""))


def amount_with_hangul(n: int) -> str:
    """1500000 → '금1,500,000원(금일백오십만원)'"""
    return f"금{n:,}원(금{number_to_hangul(n)}원)"


def hangulize_amounts(text: str) -> str:
    """'1,500,000원'·'금 1500000원' 같은 금액에 한글 금액을 병기한다(이미 병기된 것은 건너뜀)."""
    pattern = re.compile(r"(?:금\s*)?(\d{1,3}(?:,\d{3})+|\d+)\s*원(?!\s*\(금)")
    return pattern.sub(lambda m: amount_with_hangul(_to_int(m.group(1))), text)


# ----------------------------------------------------------------------------
# B4. 숫자 표기 변환
# ----------------------------------------------------------------------------

def add_commas(text: str) -> str:
    """네 자리 이상 정수에 천 단위 쉼표(연도처럼 보이는 4자리는 건너뜀)."""
    def repl(m):
        raw = m.group(0)
        if "," in raw or "." in raw:
            return raw
        if len(raw) == 4 and 1900 <= int(raw) <= 2100:
            return raw
        return f"{int(raw):,}" if len(raw) >= 4 else raw
    return re.sub(r"(?<![\d.,])\d{4,}(?![\d.,])", repl, text)


def remove_commas(text: str) -> str:
    return re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", text)


def scale_numbers(text: str, factor: Decimal | int | str, digits: int = 0) -> str:
    """모든 숫자에 factor를 곱한다. 예: 원→천원은 factor=Decimal('0.001')."""
    factor = Decimal(str(factor))

    def repl(m):
        value = Decimal(m.group(0).replace(",", "")) * factor
        q = Decimal(1).scaleb(-digits)
        value = value.quantize(q, rounding=ROUND_HALF_UP)
        return f"{value:,.{digits}f}"
    return re.sub(r"(?<![\d.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\d.,])\d+(?:\.\d+)?", repl, text)


# ----------------------------------------------------------------------------
# B2. 날짜
# ----------------------------------------------------------------------------

def format_date(d: date, style: str = "full") -> str:
    """full: 2025. 7. 25.(금) / short: ’25. 7. 25.(금) / plain: 2025. 7. 25."""
    if style == "short":
        return f"’{d.year % 100:02d}. {d.month}. {d.day}.({WEEKDAYS[d.weekday()]})"
    if style == "plain":
        return f"{d.year}. {d.month}. {d.day}."
    return f"{d.year}. {d.month}. {d.day}.({WEEKDAYS[d.weekday()]})"


_DATE = re.compile(r"(?P<y>(?:19|20)\d{2}|[’‘']\d{2})\s*[.\-/년]\s*(?P<m>\d{1,2})\s*[.\-/월]\s*(?P<d>\d{1,2})\s*[.일]?"
                   r"(?!\s*\d)(?P<wd>\s*\(\s*[월화수목금토일]\s*\))?")


def _year(text: str) -> int:
    text = text.lstrip("’‘'")
    return int(text) + 2000 if len(text) == 2 else int(text)


def parse_date(text: str) -> date | None:
    match = _DATE.search(text or "")
    if not match:
        return None
    try:
        return date(_year(match.group("y")), int(match.group("m")), int(match.group("d")))
    except ValueError:
        return None


def add_weekdays(text: str) -> str:
    """날짜 뒤에 요일을 붙이거나 틀린 요일을 고친다: 2025. 7. 25. → 2025. 7. 25.(금)"""
    def repl(m):
        try:
            d = date(_year(m.group("y")), int(m.group("m")), int(m.group("d")))
        except ValueError:
            return m.group(0)
        body = m.group(0)[: m.start("wd") - m.start()] if m.group("wd") else m.group(0)
        body = body.rstrip()
        # 점 표기(2025. 7. 25)만 끝점을 보충하고 2025-07-25·2025/7/25 표기는 그대로 둔다.
        if not body.endswith(".") and not re.search(r"[-/]", body):
            body += "."
        return f"{body}({WEEKDAYS[d.weekday()]})"
    return _DATE.sub(repl, text)


def month_bounds(ref: date, offset: int = 0) -> tuple[date, date]:
    y, m = ref.year, ref.month + offset
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])


def weekdays_in_month(ref: date, weekday: int, offset: int = 0) -> list[date]:
    start, end = month_bounds(ref, offset)
    first = start + timedelta(days=(weekday - start.weekday()) % 7)
    return [first + timedelta(weeks=i) for i in range(6) if first + timedelta(weeks=i) <= end]


def week_of(ref: date, offset: int = 0) -> tuple[date, date]:
    monday = ref - timedelta(days=ref.weekday()) + timedelta(weeks=offset)
    return monday, monday + timedelta(days=4)


def date_range_text(start: date, end: date, style: str = "full") -> str:
    return f"{format_date(start, style)} ~ {format_date(end, style)}"


def days_between(a: date, b: date, inclusive: bool = False) -> int:
    return (b - a).days + (1 if inclusive else 0)


# ----------------------------------------------------------------------------
# B3. 표 계산
# ----------------------------------------------------------------------------

def _num(cell: str):
    cleaned = re.sub(r"[,\s원명건개%]", "", cell or "")
    try:
        return Decimal(cleaned) if re.fullmatch(r"-?\d+(?:\.\d+)?", cleaned) else None
    except InvalidOperation:
        return None


def parse_table(text: str) -> list[list[str]]:
    """한/글·엑셀에서 복사한 표(탭 구분) 또는 | 구분 표를 행 목록으로."""
    rows = []
    for line in (text or "").replace("\r\n", "\n").split("\n"):
        if not line.strip() or re.fullmatch(r"\|?[\s:\-|]+\|?", line.strip()):
            continue
        if "\t" in line:
            rows.append([c.strip() for c in line.split("\t")])
        elif "|" in line:
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        else:
            rows.append([c for c in re.split(r"\s{2,}", line.strip())])
    width = max((len(r) for r in rows), default=0)
    return [r + [""] * (width - len(r)) for r in rows]


def _fmt(value: Decimal, digits: int = 0) -> str:
    if value == value.to_integral_value():
        return f"{int(value):,}"
    q = Decimal(1).scaleb(-max(digits, 1))
    return f"{value.quantize(q, rounding=ROUND_HALF_UP):,}"


def table_to_text(rows: list[list[str]]) -> str:
    return "\n".join("\t".join(r) for r in rows)


def calc_table(rows: list[list[str]], op: str, digits: int = 1) -> list[list[str]]:
    """op: col_sum·col_avg(아래 행 추가), row_sum(오른쪽 열 추가), col_ratio(각 열 구성비 %).

    첫 행이나 첫 열에 숫자가 없으면 머리글로 보고 계산에서 뺀다.
    """
    if not rows:
        return rows
    header = 1 if all(_num(c) is None for c in rows[0][1:] if c) else 0
    label_col = 1 if all(_num(r[0]) is None for r in rows[header:] if r[0]) else 0
    body = rows[header:]
    width = len(rows[0])
    out = [list(r) for r in rows]
    if op in ("col_sum", "col_avg"):
        total = [""] * width
        if label_col:
            total[0] = "합계" if op == "col_sum" else "평균"
        for c in range(label_col, width):
            values = [v for v in (_num(r[c]) for r in body) if v is not None]
            if values:
                value = sum(values) if op == "col_sum" else sum(values) / len(values)
                total[c] = _fmt(value, 0 if op == "col_sum" else digits)
        out.append(total)
    elif op == "row_sum":
        if header:
            out[0].append("합계")
        for r in out[header:]:
            values = [v for v in (_num(x) for x in r[label_col:]) if v is not None]
            r.append(_fmt(sum(values)) if values else "")
    elif op == "col_ratio":
        for c in range(label_col, width):
            values = [_num(r[c]) for r in body]
            total = sum(v for v in values if v is not None)
            if not total:
                continue
            for r, v in zip(out[header:], values):
                if v is not None:
                    r[c] = f"{r[c]} ({_fmt(v * 100 / total, digits)}%)"
    else:
        raise ValueError(f"알 수 없는 계산: {op}")
    return out


# ----------------------------------------------------------------------------
# B5. 나이·주민등록번호
# ----------------------------------------------------------------------------

_RRN = re.compile(r"(?<!\d)(\d{2})(\d{2})(\d{2})\s*-\s*([1-8])(\d{6})(?!\d)")


def international_age(birth: date, on: date | None = None) -> int:
    on = on or date.today()
    return on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))


def rrn_birth(rrn: str) -> tuple[date, str] | None:
    """주민등록번호 앞 7자리로 생년월일과 성별. 외국인등록번호(5~8)도 받는다."""
    match = _RRN.search(rrn or "")
    if not match:
        return None
    yy, mm, dd, g = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
    century = {1: 1900, 2: 1900, 5: 1900, 6: 1900, 3: 2000, 4: 2000, 7: 2000, 8: 2000}[g]
    try:
        return date(century + yy, mm, dd), ("남" if g % 2 else "여")
    except ValueError:
        return None


def mask_rrn(text: str) -> str:
    """주민등록번호 뒷자리를 성별 자리만 남기고 가린다: 900101-1******"""
    return _RRN.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}-{m.group(4)}******", text)


def ages_for_lines(text: str, on: date | None = None) -> str:
    """줄마다 생년월일(또는 주민번호)을 찾아 '(만 N세)'를 붙인다. 주민번호는 가려서 쓴다."""
    out = []
    for line in (text or "").splitlines():
        birth = None
        info = rrn_birth(line)
        if info:
            birth = info[0]
            line = mask_rrn(line)
        else:
            birth = parse_date(line)
        out.append(f"{line} (만 {international_age(birth, on)}세)" if birth else line)
    return "\n".join(out)


def rrn_to_birth_lines(text: str) -> str:
    def repl(m):
        info = rrn_birth(m.group(0))
        if not info:
            return m.group(0)
        birth, gender = info
        return f"{birth.year}. {birth.month}. {birth.day}.({gender})"
    return _RRN.sub(repl, text)


# ----------------------------------------------------------------------------
# B6. 번호 매기기
# ----------------------------------------------------------------------------

ROMAN_UNICODE = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿"
HANGUL_ORDER = "가나다라마바사아자차카타파하"


def roman(n: int, unicode_chars: bool = True) -> str:
    if unicode_chars and 1 <= n <= len(ROMAN_UNICODE):
        return ROMAN_UNICODE[n - 1]
    out = ""
    for value, sym in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                       (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= value:
            out += sym
            n -= value
    return out


def circled(n: int) -> str:
    return CIRCLED[n - 1] if 1 <= n <= len(CIRCLED) else f"({n})"


NUMBER_STYLES = {
    "1.": lambda n: f"{n}.",
    "가.": lambda n: f"{HANGUL_ORDER[(n - 1) % len(HANGUL_ORDER)]}.",
    "1)": lambda n: f"{n})",
    "가)": lambda n: f"{HANGUL_ORDER[(n - 1) % len(HANGUL_ORDER)]})",
    "(1)": lambda n: f"({n})",
    "①": circled,
    "Ⅰ.": lambda n: f"{roman(n)}.",
}
_EXISTING_NUMBER = re.compile(r"^\s*(?:\d+[.)]|\(\d+\)|[가-하][.)]|[①-⑳㉑-㊿]|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ][.]?|[IVX]+\.)\s*")


def renumber_lines(text: str, style: str = "1.") -> str:
    """비어 있지 않은 줄마다 기존 번호를 지우고 새 번호를 붙인다."""
    make = NUMBER_STYLES[style]
    out, n = [], 0
    for line in (text or "").splitlines():
        if not line.strip():
            out.append(line)
            continue
        n += 1
        out.append(f"{make(n)} {_EXISTING_NUMBER.sub('', line).strip()}")
    return "\n".join(out)


# ----------------------------------------------------------------------------
# A5. 회신공문
# ----------------------------------------------------------------------------

def has_batchim(word: str) -> bool:
    """마지막 글자에 받침이 있는지. 한글이 아니면 숫자 읽기(1·3·6·7·8·0은 받침)로 판단."""
    word = re.sub(r"[\s)\]」』'\"”’]+$", "", word or "")
    if not word:
        return False
    last = word[-1]
    if "가" <= last <= "힣":
        return (ord(last) - 0xAC00) % 28 != 0
    return last in "1367890LMNlmn"


def josa(word: str, with_batchim: str, without: str) -> str:
    return word + (with_batchim if has_batchim(word) else without)


def reply_title(request_title: str) -> str:
    """'○○ 자료 제출 요청' → '○○ 자료 제출'"""
    title = re.sub(r"\((?:긴급|재요청|협조)\)", "", request_title or "").strip()
    title = re.sub(r"\s*(?:제출\s*)?(?:요청|협조\s*요청|협조|요구|알림)\s*$", "", title).strip()
    title = re.sub(r"\s*관련\s*$", "", title).strip()
    if not re.search(r"(제출|회신|보고)$", title):
        title = re.sub(r"\s*자료$", "", title).strip() + " 자료 제출"
    return title


def reply_document(request_title: str, sender: str = "", doc_no: str = "", doc_date: str = "",
                   attachment: str = "", contact: str = "") -> str:
    """요청 공문 정보를 받아 회신 공문 본문을 만든다(행정업무규정 표기)."""
    title = reply_title(request_title)
    source = " ".join(x for x in (sender, doc_no) if x).strip()
    if doc_date:
        d = parse_date(doc_date)
        source += f"({format_date(d, 'plain') if d else doc_date})"
    related = f"{source} 「{request_title.strip()}」" if source else f"「{request_title.strip()}」"
    subject = attachment.strip() or title.replace(" 제출", "").strip()
    ending = f"붙임과 같이 제출합니다(문의: {contact.strip()})." if contact.strip() else "붙임과 같이 제출합니다."
    lines = [
        f"제목  {title}",
        "",
        f"1. 관련: {related}",
        f"2. 위 호와 관련하여 {josa(subject, '을', '를')} {ending}",
        "",
        f"붙임  {subject} 1부.  끝.",
    ]
    return "\n".join(lines)
