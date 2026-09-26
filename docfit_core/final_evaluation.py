"""Goal-based final evaluation for a completed document-processing run."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


MODE_LABELS = {
    "spacing": "문서의 자간과 줄 배치를 정리하고 읽기 좋은 결과물을 생성",
    "format": "선택한 표준 서식을 적용한 결과물을 생성",
    "unify": "문두기호별로 문서 안에서 가장 많이 쓴 스타일로 맞춘 결과물을 생성",
    "all": "자간·줄 배치와 표준 서식을 함께 정리한 결과물을 생성",
}


# 저장한 결과물을 다시 열어 규칙 준수를 검사하는 기능이 있는 세부 작업.
# 이 작업들의 검사 결과가 없거나 실패하면 판정을 막는다. 그 밖의 작업은
# 결과 검사 기능 자체가 없으므로 '미검사'를 문제로 보지 않고 참고로만 알린다.
RESULT_CHECKED_STAGES = frozenset({"page_group", "word_check", "control_word_check"})


def build_work_goal(mode, source_count, selected_stages=None):
    """Build an explicit, serializable goal from the user's run settings."""
    if mode not in MODE_LABELS:
        raise ValueError(f"지원하지 않는 작업 모드입니다: {mode}")
    selected = [key for key, enabled in (selected_stages or {}).items() if enabled]
    return {
        "mode": mode,
        "summary": MODE_LABELS[mode],
        "source_count": max(0, int(source_count)),
        "selected_stages": selected,
        "success_conditions": [
            "요청한 모든 문서를 오류 없이 처리",
            "처리된 문서마다 열 수 있는 HWPX 결과물 생성",
            "측정 가능한 세부 작업에서 미해결 항목 최소화",
            "상세 검수를 실행한 경우 문서 무결성 유지",
        ],
    }


def _criterion(key, label, weight, score, evidence, applicable=True):
    score = max(0.0, min(100.0, float(score))) if applicable else None
    return {"key": key, "label": label, "weight": weight, "applicable": applicable,
            "score": None if score is None else round(score, 1), "evidence": evidence}


def evaluate_work(goal, documents, item_stats=None, unresolved=None, verification_enabled=False):
    """Evaluate artifacts against the declared goal without modifying documents."""
    documents = list(documents or [])
    item_stats = dict(item_stats or {})
    unresolved = list(unresolved or [])
    expected = int(goal.get("source_count", len(documents)))
    succeeded = sum(1 for item in documents if item.get("success"))
    failed = max(0, expected - succeeded)

    completion_score = 100 if expected == 0 else succeeded / expected * 100
    outputs = [item for item in documents if item.get("success")]
    valid_outputs = sum(1 for item in outputs
                        if item.get("output") and Path(item["output"]).is_file())
    artifact_score = 100 if not outputs and expected == 0 else (
        valid_outputs / max(1, expected) * 100)

    attempted = max(0, int(item_stats.get("attempted", 0)))
    item_succeeded = max(0, int(item_stats.get("succeeded", 0)))
    item_applicable = attempted > 0
    item_score = item_succeeded / attempted * 100 if item_applicable else 0

    verified = [item for item in documents if item.get("integrity_ok") is not None]
    quality_applicable = bool(verification_enabled)
    integrity_passed = sum(1 for item in verified if item.get("integrity_ok") is True)
    if quality_applicable:
        integrity_score = integrity_passed / max(1, succeeded) * 100
        unresolved_score = max(0.0, 100.0 - len(unresolved) * 10.0)
        quality_score = integrity_score * .7 + unresolved_score * .3
    else:
        quality_score = 0

    criteria = [
        _criterion("completion", "요청 문서 처리 완료", 35, completion_score,
                   {"requested": expected, "succeeded": succeeded, "failed": failed}),
        _criterion("artifacts", "결과물 생성 확인", 25, artifact_score,
                   {"expected": expected, "existing_hwpx": valid_outputs}),
        _criterion("task_effectiveness", "세부 작업 목표 달성", 25, item_score,
                   {"attempted": attempted, "succeeded": item_succeeded,
                    "failed": max(0, attempted - item_succeeded)}, item_applicable),
        _criterion("quality", "상세 검수 및 무결성", 15, quality_score,
                   {"verification_enabled": bool(verification_enabled),
                    "verified": len(verified), "integrity_passed": integrity_passed,
                    "unresolved_count": len(unresolved)}, quality_applicable),
    ]
    applicable = [item for item in criteria if item["applicable"]]
    weight = sum(item["weight"] for item in applicable)
    score = sum(item["score"] * item["weight"] for item in applicable) / weight if weight else 0

    blockers = []
    notes = []
    # 작업 시도 통계는 결과 규칙 검사 증거가 아니다. 실제 검사 범위를 별도 공개한다.
    selected = set(goal.get('selected_stages') or [])
    required = selected & RESULT_CHECKED_STAGES
    not_checkable = sorted(selected - RESULT_CHECKED_STAGES)
    coverage = []
    for item in outputs:
        checks = item.get('rule_checks') or {}
        missing = sorted(key for key in required if key not in checks)
        bad = sorted(key for key in required if key in checks
                     and checks[key].get('status') != 'passed')
        coverage.append({'output': item.get('output'), 'unchecked': missing,
                         'not_checkable': not_checkable,
                         'failed_or_incomplete': bad, 'checks': checks})
        if missing:
            blockers.append(f"결과 규칙 미검사 {len(missing)}개: {', '.join(missing)}")
        if bad:
            blockers.append(f"결과 규칙 검사 실패 또는 미완료: {', '.join(bad)}")
    # 어떤 조정으로도 풀 수 없어 규칙 적용에서 뺀 항목은 문제가 아니라 참고로 적는다.
    def exempt_count(*keys):
        return sum(len((item.get('rule_checks') or {}).get(key, {}).get('exempt') or [])
                   for item in outputs for key in keys)
    groups = exempt_count('page_group')
    if groups:
        notes.append(f"한 쪽보다 긴 묶음 {groups}개는 쪽 배치 규칙 적용 제외(한 쪽에 모을 수 없음)")
    numbers = sum(len((item.get('rule_checks') or {}).get('number_check', {}).get('review') or [])
                  for item in outputs)
    if numbers:
        notes.append(f"숫자 대조: 표 가까이 본문 수치 중 표에서 찾지 못한 {numbers}개는 확인 필요(자동 수정 안 함)")
    words = exempt_count('word_check', 'control_word_check')
    if words:
        notes.append(f"칸 폭보다 긴 단어 {words}개는 단어 분리 규칙 적용 제외(줄 첫머리부터 넘침)")
    if outputs and not_checkable:
        notes.append(f"결과 검사 기능이 없는 세부 작업 {len(not_checkable)}개"
                     f"(수행 여부만 확인): {', '.join(not_checkable)}")
    if not verification_enabled or not selected:
        blockers.append('최종 규칙 검수 범위가 확인되지 않음')
    if failed:
        blockers.append(f"처리하지 못한 문서 {failed}개")
    if valid_outputs < succeeded:
        blockers.append(f"확인할 수 없는 결과물 {succeeded - valid_outputs}개")
    integrity_failed = sum(1 for item in verified if item.get("integrity_ok") is False)
    if integrity_failed:
        blockers.append(f"무결성 확인이 필요한 문서 {integrity_failed}개")
    if unresolved:
        blockers.append(f"미해결 검수 항목 {len(unresolved)}건")

    if score >= 100 and not blockers:
        verdict = "달성"
    elif score >= 70 and not failed and valid_outputs == succeeded:
        verdict = "부분 달성"
    else:
        verdict = "확인 필요"
    return {
        "version": 1,
        "evaluated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "goal": goal,
        "score": round(score, 1),
        "score_meaning": "작업 수행 지표이며 모든 결과 규칙의 준수율을 뜻하지 않음",
        "verification_coverage": coverage,
        "verdict": verdict,
        "criteria": criteria,
        "blockers": blockers,
        "notes": notes,
        "unresolved": unresolved,
        "documents": documents,
    }


def write_evaluation_report(report, path):
    """Persist the final evaluation as UTF-8 JSON and return its path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
