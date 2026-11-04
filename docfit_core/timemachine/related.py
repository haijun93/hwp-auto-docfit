"""정기 문서 계열 추정 및 작성 기준일 정렬."""
from __future__ import annotations

import ntpath
import re
from collections import Counter
from datetime import date

from .content_search import extract_reference_date_info

_STOP = {"주요", "업무", "실적", "자료", "현황", "보고", "보고서", "문서", "결과", "추진", "작성", "기준", "년도", "년", "분기", "부서", "사업"}
_TOKEN = re.compile(r"[가-힣A-Za-z0-9]{2,}")
_PERIOD = re.compile(r"(20\d{2})\s*년도?\s*([1-4])\s*분기|(20\d{2})\s*년도?\s*(상반기|하반기)")


def _tokens(text):
    return {word.casefold() for word in _TOKEN.findall(text) if word.casefold() not in _STOP}


def _period(text):
    match = _PERIOD.search(text)
    if not match:
        return None
    if match.group(1):
        return (int(match.group(1)), int(match.group(2)))
    # 반기는 분기 축으로 환산한다(상반기=2분기, 하반기=4분기).
    return (int(match.group(3)), 2 if match.group(4) == "상반기" else 4)


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
        values = shared[:8]
        reasons.append({"type": "terms", "label": "공통 업무·사업 단서", "values": values,
                        "text": "공통 업무·사업 단서: " + ", ".join(values)})
    left_type, right_type = _type(ref_text), _type(cand_text)
    if left_type and left_type == right_type:
        score += 25
        reasons.append({"type": "document_type", "label": "같은 문서 유형", "value": left_type,
                        "text": "같은 문서 유형: " + left_type})
    left_period, right_period = _period(ref_text), _period(cand_text)
    if left_period and right_period:
        distance = abs((left_period[0] * 4 + left_period[1]) - (right_period[0] * 4 + right_period[1]))
        if distance <= 4:
            score += 25 - distance * 4
            detail = "같은 기간" if distance == 0 else f"{distance}단계 차이"
            reasons.append({"type": "period_pattern", "label": "인접한 기간 패턴", "distance": distance,
                            "text": "인접한 기간 패턴: " + detail})
    if not (shared and left_type and left_type == right_type):
        return None
    if not score:
        return None
    return min(score, 100), reasons


def _selected_name(selected, path):
    """선택 문서 이름: 색인에 저장된 이름, 없으면 Windows·POSIX 구분자를 모두 처리한 파일명."""
    try:
        name = selected["name"]
    except (KeyError, IndexError):
        name = None
    return name or ntpath.basename(path)


def related_documents(index, path, *, roots=None, excluded_pairs=(), limit=100):
    """선택 문서와 연관된 색인 자료를 점수·근거와 함께 기준일 순으로 반환한다."""
    selected, candidates = index.related_candidates(path, roots=roots)
    if selected is None:
        return {"reference_date": None, "reference_date_found": False,
                "reference_date_source": None, "reference_date_text": None, "items": []}
    # DB 스키마를 바꾸지 않고 본문에서 기준일과 출처를 다시 계산한다.
    selected_info = extract_reference_date_info(selected["body"])
    selected_date = selected_info["date"]
    from .store import path_key
    excluded = {frozenset(path_key(value) for value in pair) for pair in excluded_pairs}
    reference = {"name": _selected_name(selected, path), "body": selected["body"]}
    items = []
    for candidate in candidates:
        if frozenset((path_key(path), path_key(candidate["path"]))) in excluded:
            continue
        scored = _score(reference, candidate)
        if not scored:
            continue
        score, reasons = scored
        info = extract_reference_date_info(candidate["body"])
        # 정렬·표시용 작성 기준일은 명시 기준일만 쓰고, 분기·반기 추정값은 따로 알린다.
        explicit = info["source"] == "explicit"
        ref_date = info["date"] if explicit else None
        items.append({"path": candidate["path"], "name": candidate["name"], "score": score,
                      "reasons": reasons, "reference_date": ref_date,
                      "reference_date_found": bool(ref_date),
                      "estimated_reference_date": None if explicit else info["date"],
                      "reference_date_source": info["source"],
                      "reference_date_text": info["text"]})
    items.sort(key=lambda item: (item["reference_date"] is None, -(item["score"] if item["reference_date"] is not None else 0),
                                 item["reference_date"] or "", item["name"].casefold()))
    return {"reference_date": selected_date, "reference_date_found": bool(selected_date),
            "reference_date_source": selected_info["source"], "reference_date_text": selected_info["text"],
            "items": items[:max(1, min(int(limit), 200))]}
