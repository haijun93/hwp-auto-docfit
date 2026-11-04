"""정기 문서 계열 추정 및 작성 기준일 정렬."""
from __future__ import annotations

import re
from collections import Counter
from datetime import date

from .content_search import extract_reference_date

_STOP = {"주요", "업무", "실적", "자료", "현황", "보고", "보고서", "문서", "결과", "추진", "작성", "기준", "년도", "년", "분기", "부서", "사업"}
_TOKEN = re.compile(r"[가-힣A-Za-z0-9]{2,}")
_PERIOD = re.compile(r"(20\d{2})\s*년도?\s*(\d)\s*분기|(20\d{2})\s*년\s*(상반기|하반기)")


def _tokens(text):
    return {word.casefold() for word in _TOKEN.findall(text) if word.casefold() not in _STOP}


def _period(text):
    match = _PERIOD.search(text)
    if not match:
        return None
    if match.group(1):
        return (int(match.group(1)), int(match.group(2)))
    return (int(match.group(3)), 1 if match.group(4) == "상반기" else 2)


def _type(text):
    folded = text.casefold()
    for label, pattern in (("업무추진실적", r"업무\s*추진\s*실적|주요업무.*실적"),
                           ("통계자료", r"통계|통계자료"), ("부서현황", r"부서.*현황"),
                           ("사업현황", r"사업.*현황"), ("회의자료", r"회의.*자료"),
                           ("계획", r"계획|추진계획"), ("보고", r"보고서|보고")):
        if re.search(pattern, folded):
            return label
    return None


def _score(reference, candidate):
    ref_dict = dict(reference) if hasattr(reference, "keys") else (reference or {})
    cand_dict = dict(candidate) if hasattr(candidate, "keys") else (candidate or {})
    ref_body = ref_dict.get("body") or ""
    cand_body = cand_dict.get("body") or ""
    ref_text = (ref_dict.get("name") or "") + "\n" + ref_body
    cand_text = (cand_dict.get("name") or "") + "\n" + cand_body
    left, right = _tokens(ref_text), _tokens(cand_text)
    shared = sorted(left & right)
    reasons = []
    score = 0
    if shared:
        score += min(50, 12 * len(shared))
        reasons.append({"type": "terms", "label": "공통 업무·사업 단서", "values": shared[:8]})
    left_type, right_type = _type(ref_text), _type(cand_text)
    if left_type and left_type == right_type:
        score += 25
        reasons.append({"type": "document_type", "label": "같은 문서 유형", "value": left_type})
    left_period, right_period = _period(ref_text), _period(cand_text)
    if left_period and right_period:
        distance = abs((left_period[0] * 4 + left_period[1]) - (right_period[0] * 4 + right_period[1]))
        if distance <= 4:
            score += 25 - distance * 4
            reasons.append({"type": "period_pattern", "label": "인접한 기간 패턴", "distance": distance})
    if not (shared and left_type and left_type == right_type):
        return None
    if not score:
        return None
    return min(score, 100), reasons


def related_documents(index, path, *, roots=None, excluded_pairs=(), limit=100):
    """선택 문서와 연관된 색인 자료를 점수·근거와 함께 기준일 순으로 반환한다."""
    selected, candidates = index.related_candidates(path, roots=roots)
    if selected is None:
        return {"reference_date": None, "reference_date_found": False, "items": []}
    selected_date = selected["reference_date"] or extract_reference_date(selected["body"])
    from .store import path_key
    excluded = {frozenset(path_key(value) for value in pair) for pair in excluded_pairs}
    items = []
    for candidate in candidates:
        if frozenset((path_key(path), path_key(candidate["path"]))) in excluded:
            continue
        scored = _score({"name": path.rsplit("/", 1)[-1], "body": selected["body"]}, candidate)
        if not scored:
            continue
        score, reasons = scored
        ref_date = candidate["reference_date"]
        # 제목의 기간은 연관성 근거로 쓰되, 작성 기준일 표시에는 본문 추출값만 사용한다.
        if ref_date and "기준일" not in candidate["body"]:
            ref_date = None
        items.append({"path": candidate["path"], "name": candidate["name"], "score": score,
                      "reasons": reasons, "reference_date": ref_date,
                      "reference_date_found": bool(ref_date)})
    items.sort(key=lambda item: (
        item["reference_date"] is None,
        -date.fromisoformat(item["reference_date"]).toordinal()
        if item["reference_date"] is not None else 0,
        -item["score"] if item["reference_date"] is not None else 0,
        item["name"].casefold(),
    ))
    return {"reference_date": selected_date, "reference_date_found": bool(selected_date), "items": items[:max(1, min(int(limit), 200))]}
