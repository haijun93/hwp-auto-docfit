"""정기 문서 계열(시리즈) 키·기간을 제목/파일명에서 뽑는 순수 함수와 계열 묶음 생성."""
from __future__ import annotations

import re
import unicodedata
from datetime import date

_EXT = re.compile(r"\.(hwpx?|hwt|docx?|pptx?|xlsx?|pdf|txt|md)$", re.I)
_Q_NUM = r"(?:제\s*)?(?P<q>[1-4])\s*(?:/\s*4\s*)?(?:사\s*)?분\s*기"
_PERIODS = (
    # (종류, 정규식) — 앞쪽이 우선. 연도는 선택.
    ("quarter", re.compile(rf"(?:(?P<y>20\d{{2}})\s*년?\s*도?[\s_\-.]*)?{_Q_NUM}")),
    ("quarter", re.compile(r"(?:(?P<y>20\d{2})\s*년?\s*도?[\s_\-.]*Q|(?<![A-Za-z0-9])Q)(?P<q>[1-4])(?![A-Za-z0-9])", re.I)),
    ("half", re.compile(r"(?:(?P<y>20\d{2})\s*년?\s*도?[\s_\-.]*)?(?P<h>상|하)\s*반\s*기")),
    ("month", re.compile(r"(?P<y>20\d{2})\s*년\s*도?\s*(?P<m>1[0-2]|0?[1-9])\s*월")),
    ("month", re.compile(r"(?<!\d)(?P<y>20\d{2})\s*[.\-_/]\s*(?P<m>1[0-2]|0[1-9])(?![\d])(?!\s*[.\-_/]\s*\d)")),
    ("month", re.compile(r"(?<!\d)(?P<y>20\d{2})(?P<m>0[1-9]|1[0-2])(?!\d)")),
    ("month", re.compile(r"(?<![\d.])(?P<m>1[0-2]|0?[1-9])\s*월(?:\s*분)?")),
    ("round", re.compile(r"(?:(?P<y>20\d{2})\s*년?\s*도?[\s_\-.]*)?제\s*(?P<n>\d{1,3})\s*(?:차|회)")),
    ("round", re.compile(r"(?:(?P<y>20\d{2})\s*년?\s*도?[\s_\-.]*)?(?<![\d])(?P<n>\d{1,3})\s*차(?![원])")),
    ("year", re.compile(r"(?P<y>20\d{2})\s*(?:년\s*도?|학년도|회계연도)")),
    ("year", re.compile(r"(?<![\d])(?P<y>20\d{2})(?![\d])")),
)
# 계열 키에서 지우는 잡음(버전·사본·완성도 표기·괄호 날짜)
_NOISE = (
    re.compile(r"\(\s*(?:최종|수정|사본|복사본|초안|완료|제출|공유|배포)[^)]*\)"),
    re.compile(r"(?<![가-힣A-Za-z])(?:최종본?|수정본?|사본|복사본|초안|제출용|배포용)(?![가-힣A-Za-z])"),
    re.compile(r"(?<![A-Za-z0-9])v\s*\d+(?:\.\d+)*(?![A-Za-z0-9])", re.I),
    re.compile(r"(?<![\d])\d{8}(?![\d])"),
    re.compile(r"(?<!\d)(?!20\d{2}(?:0[1-9]|1[0-2])(?!\d))\d{6}(?!\d)"),
    re.compile(r"\(\s*\d+\s*\)\s*$"),
    re.compile(r"[_\-]\s*\d{1,2}\s*$"),
)
_BRACKETS = re.compile(r"[\[\]\(\)（）<>《》「」『』【】]")
_SPACE_PUNCT = re.compile(r"[\s_\-·ㆍ,.:;/~]+")
_QUARTER_END = {1: 3, 2: 6, 3: 9, 4: 12}


def _label(kind, year, value):
    if kind == "quarter":
        return f"{year}Q{value}" if year else f"Q{value}"
    if kind == "half":
        return f"{year}H{value}" if year else f"H{value}"
    if kind == "month":
        return f"{year}-{value:02d}" if year else f"{value:02d}월"
    if kind == "round":
        return f"{year}-{value}차" if year else f"{value}차"
    return str(year)


def _sort_ordinal(kind, year, value):
    """기간 말 기준 '연*12+월' 서수. 연도 없는 기간이나 차수는 비교 불가라 None(차수는 별도)."""
    if kind == "round":
        return (year or 0) * 1000 + value
    if not year:
        return None
    if kind == "quarter":
        return year * 12 + _QUARTER_END[value]
    if kind == "half":
        return year * 12 + (6 if value == 1 else 12)
    if kind == "month":
        return year * 12 + value
    return year * 12 + 12


def _normalize_title(title):
    text = unicodedata.normalize("NFC", title or "")
    # 경로 구분자만 잘라낸다. '4/4분기'처럼 숫자 사이의 슬래시는 제목의 일부다.
    text = re.split(r"\\|(?<!\d)/|/(?!\d)", text)[-1]
    return _EXT.sub("", text).strip()


def series_key(title):
    """제목·파일명에서 계열 키와 기간을 뽑는다. 기간 표기가 없거나 남는 이름이 없으면 None.

    예: '2026년도 3분기 주요업무추진실적.hwpx' ->
        {'series': '주요업무추진실적', 'period': {'kind': 'quarter', 'year': 2026, 'value': 3,
         'label': '2026Q3', 'ordinal': ...}}
    """
    text = _normalize_title(title)
    if not text:
        return None
    for pattern in _NOISE:
        text = pattern.sub(" ", text)
    period = None
    # 기간 표기를 한 종류만 기간으로 삼되, 같은 제목의 연도·분기 중복 표기는 모두 지운다.
    for kind, pattern in _PERIODS:
        match = pattern.search(text)
        if not match:
            continue
        groups = match.groupdict()
        year = int(groups["y"]) if groups.get("y") else None
        if kind == "quarter":
            value = int(groups["q"])
        elif kind == "half":
            value = 1 if groups["h"] == "상" else 2
        elif kind == "month":
            value = int(groups["m"])
        elif kind == "round":
            value = int(groups["n"])
        else:
            value = year
        if kind == "round" and not 1 <= value <= 200:
            continue
        period = {"kind": kind, "year": year, "value": value}
        text = text[:match.start()] + " " + text[match.end():]
        break
    if period is None:
        return None
    # 남은 연도·월 표기(예: 제목에 '2026년도'가 따로 있는 경우)도 계열 키에서 제외한다.
    text = re.sub(r"20\d{2}\s*(?:년\s*도?|학년도|회계연도)?", " ", text)
    if period["year"] is None and period["kind"] != "year":
        years = re.findall(r"20\d{2}", _normalize_title(title))
        if years:
            period["year"] = int(years[0])
    text = _BRACKETS.sub(" ", text)
    text = _SPACE_PUNCT.sub("", text)
    text = re.sub(r"^(?:의|및|분|도)+|(?:의)$", "", text)
    if len(text) < 2:
        return None
    period["label"] = _label(period["kind"], period["year"], period["value"])
    period["ordinal"] = _sort_ordinal(period["kind"], period["year"], period["value"])
    return {"series": text.casefold(), "series_label": text, "period": period}


def series_of_document(name, body=""):
    """파일명으로 먼저 찾고, 없으면 본문 첫 비어 있지 않은 줄(제목)로 계열 키를 찾는다."""
    found = series_key(name)
    if found:
        return found
    for line in (body or "").splitlines():
        line = line.strip()
        if line:
            return series_key(line[:120])
    return None


def build_series(selected_name, selected_body, selected_info, candidates, *, excluded=lambda c: False):
    """같은 계열 문서를 기준일 순 이전·다음 묶음으로 만든다.

    candidates: [{'name','path','body'}...]. selected_info: 선택 문서 기준일 필드(dict).
    기준일은 본문 추출값만 쓴다. 기준일이 없는 문서는 'undated'에 따로 두고 섞어 정렬하지 않는다.
    반환: None(계열을 못 찾음) 또는 {'key','label','period','previous','next','same','undated','total'}.
    """
    mine = series_of_document(selected_name, selected_body)
    if not mine:
        return None
    from .related import _date_fields  # 순환 import 방지: 호출 시점에 가져온다.
    rows = []
    for candidate in candidates:
        if excluded(candidate):
            continue
        theirs = series_of_document(candidate.get("name") or "", candidate.get("body") or "")
        if not theirs or theirs["series"] != mine["series"]:
            continue
        fields = _date_fields(candidate.get("body") or "")
        rows.append({"path": candidate["path"], "name": candidate["name"], "period": theirs["period"],
                     "period_label": theirs["period"]["label"], **fields})
    base = selected_info.get("reference_date")

    def order(item):
        ordinal = item["period"]["ordinal"]
        return (item["reference_date"], ordinal if ordinal is not None else 0, item["name"].casefold())

    dated = [r for r in rows if r["reference_date"]]
    undated = sorted((r for r in rows if not r["reference_date"]), key=lambda r: r["name"].casefold())
    previous = next_ = same = []
    if base:
        previous = sorted((r for r in dated if r["reference_date"] < base), key=order, reverse=True)
        next_ = sorted((r for r in dated if r["reference_date"] > base), key=order)
        same = sorted((r for r in dated if r["reference_date"] == base), key=order)
    else:
        # 선택 문서의 기준일을 못 찾으면 이전/다음을 가르지 않는다(수정 시각 등으로 대체하지 않음).
        undated = sorted(rows, key=lambda r: r["name"].casefold())
    public_period = {k: v for k, v in mine["period"].items() if k != "ordinal"}
    return {"key": mine["series"], "label": mine["series_label"], "period": public_period,
            "reference_date": base, "reference_date_found": bool(base),
            "previous": previous, "next": next_, "same": same, "undated": undated,
            "total": len(rows)}
