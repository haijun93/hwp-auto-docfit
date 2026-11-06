"""본문에서 작성 기준일·대상 기간(분기·반기·연도)을 근거와 함께 추출하는 순수 함수."""
from __future__ import annotations

import calendar
import re
from datetime import date

_Y = r"(?:20\d{2}|['’]\d{2})"
_SEP = r"\s*[.\-/]\s*"
_FULL_DATE = (rf"(?P<y>{_Y})(?:{_SEP}|\s*년\s*)(?P<m>\d{{1,2}})(?:{_SEP}|\s*월\s*)(?P<d>\d{{1,2}})\s*(?:일|\.)?"
              r"(?:\s*\([월화수목금토일]\))?")
_MONTH_DATE = rf"(?P<y>{_Y})(?:{_SEP}|\s*년\s*)(?P<m>\d{{1,2}})\s*(?:월|\.)?(?!\s*[.\-/]?\s*\d)"
_LABEL = r"(?:작\s*성\s*)?기\s*준\s*(?:일\s*자|일)"

_DAY_PATTERNS = (
    ("작성기준일 표기", re.compile(rf"{_LABEL}\s*[:：=]?\s*(?:\(\s*)?{_FULL_DATE}")),
    ("괄호 기준 표기", re.compile(rf"[\(\[（]\s*{_FULL_DATE}\s*(?:기준|현재)\s*[\)\]）]")),
    ("기준·현재 표기", re.compile(rf"{_FULL_DATE}\s*(?:기준|현재)(?![가-힣])")),
)
_MONTH_PATTERNS = (
    ("작성기준일 표기", re.compile(rf"{_LABEL}\s*[:：=]?\s*(?:\(\s*)?{_MONTH_DATE}")),
    ("기준 월 표기", re.compile(rf"{_MONTH_DATE}\s*(?:기준|현재)(?![가-힣])")),
)
_QUARTER_NUM = r"(?:제\s*)?(?P<q>[1-4])\s*(?:/\s*4\s*)?(?:사?\s*분\s*기)"
_QUARTER_PATTERNS = (
    re.compile(rf"(?P<y>20\d{{2}})\s*년?도?\s*{_QUARTER_NUM}"),
    re.compile(r"(?P<y>20\d{2})\s*년?도?\s*(?P<q>[1-4])\s*Q\b", re.I),
    re.compile(rf"(?<![\d/])(?<!20\d\d년 )(?<!20\d\d년도 ){_QUARTER_NUM}"),
)
_HALF = re.compile(r"(?P<y>20\d{2})\s*년?도?\s*(?P<h>상|하)\s*반\s*기")
_YEAR = re.compile(r"(?P<y>20\d{2})\s*년도?\s*(?:연간|연말|결산|실적|통계|현황|업무계획|사업계획|추진계획)")
_YEAR_BEFORE = re.compile(r"(20\d{2})\s*년")


def _year(token):
    token = token.strip()
    if token[0] in "'’":
        return 2000 + int(token[1:])
    return int(token)


def _month_end(year, month):
    return date(year, month, calendar.monthrange(year, month)[1])


def _snippet(match):
    return re.sub(r"\s+", " ", match.group(0)).strip()


def _result(value, precision, basis, label, match):
    return {"date": value.isoformat(), "precision": precision, "basis": basis,
            "label": label, "evidence": _snippet(match), "start": match.start()}


def extract_base_date(text):
    """본문에서 기준일을 찾아 {date, precision, basis, label, evidence}를 돌려준다. 못 찾으면 None.

    우선순위: 일 단위 명시 > 월 단위 명시 > 분기 > 반기 > 연도.
    기간(분기·반기·연도)은 해당 기간의 말일을 정렬용 날짜로 쓴다. 파일 시각은 쓰지 않는다.
    """
    if not isinstance(text, str) or not text:
        return None
    for label, pattern in _DAY_PATTERNS:
        for match in pattern.finditer(text):
            try:
                found = date(_year(match["y"]), int(match["m"]), int(match["d"]))
            except ValueError:
                continue
            return _result(found, "day", "explicit", label, match)
    for label, pattern in _MONTH_PATTERNS:
        for match in pattern.finditer(text):
            month = int(match["m"])
            if 1 <= month <= 12:
                return _result(_month_end(_year(match["y"]), month), "month", "explicit", label, match)
    for pattern in _QUARTER_PATTERNS:
        for match in pattern.finditer(text):
            year = match.groupdict().get("y")
            if year is None:
                before = _YEAR_BEFORE.findall(text[:match.start()])
                if not before:
                    continue
                year = before[-1]
            quarter = int(match["q"])
            return _result(_month_end(int(year), quarter * 3), "quarter", "period", "분기 표기", match)
    match = _HALF.search(text)
    if match:
        return _result(_month_end(int(match["y"]), 6 if match["h"] == "상" else 12),
                       "half", "period", "반기 표기", match)
    match = _YEAR.search(text)
    if match:
        return _result(date(int(match["y"]), 12, 31), "year", "period", "대상 연도 표기", match)
    return None
