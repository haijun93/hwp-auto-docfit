"""쪽 수 맞춤 고속 탐색(한/글 없이 시험할 수 있는 순수 로직).

레벨 L(0~최대레벨)은 기존 선형 방식에서 L단계까지 줄인 상태와 같다: 앞의 절반은 '문단 아래 간격',
뒤의 절반은 '문단 위 간격'을 1단계씩 줄이고, 표 셀 여백은 두 구간에 걸쳐 함께 줄인다.
레벨에 따라 쪽 수가 줄어든다고 보고 목표 쪽 수에 닿는 최소 레벨을 이분 탐색으로 찾는다.
"""


def level_amounts(level, half=10, step_pt=1.0):
    """레벨 → (아래 간격 줄임 pt, 위 간격 줄임 pt, 표 셀 여백 축소 비율)."""
    level = max(0, int(level))
    below = min(level, half) * step_pt
    above = max(0, level - half) * step_pt
    ratio = min(1.0, min(level, half) / float(half)) if half > 0 else 0.0
    return below, above, ratio


def search_level(measure, target, max_level, bundle_split=None, extra_levels=4):
    """목표 쪽 수에 닿는 레벨을 찾는다.

    measure(level) -> 마지막 쪽 번호(None이면 측정 실패), bundle_split(level) -> 쪽 경계에 걸린 묶음이 있는가.
    돌려주는 값: dict(status, level, measured)
      status: 'fail'(최대 레벨로도 못 닿음), 'ok'(묶음까지 지킴), 'bundle_moved'(닿았지만 묶음이 걸려
      처음 닿은 레벨로 둠), 'error'(측정 실패). measured는 측정한 {레벨: 쪽} 기록.
    """
    measured = {}

    def pages(level):
        if level not in measured:
            measured[level] = measure(level)
        return measured[level]

    top = pages(max_level)
    if top is None:
        return {'status': 'error', 'level': None, 'measured': measured}
    if top > target:
        return {'status': 'fail', 'level': None, 'measured': measured}
    lo, hi = 1, max_level          # hi는 항상 목표에 닿는 레벨
    while lo < hi:
        mid = (lo + hi) // 2
        value = pages(mid)
        if value is None:
            return {'status': 'error', 'level': None, 'measured': measured}
        if value <= target:
            hi = mid
        else:
            lo = mid + 1
    first = hi
    if bundle_split is None:
        return {'status': 'ok', 'level': first, 'measured': measured}
    # 기존 방식과 같이 처음 닿은 레벨에서 묶음을 보고, 걸리면 목표에 닿는 레벨을 최대 extra_levels개 더 본다.
    level, tried = first, 0
    while True:
        value = pages(level)
        if value is None:
            return {'status': 'error', 'level': None, 'measured': measured}
        if value <= target:
            if not bundle_split(level):
                return {'status': 'ok', 'level': level, 'measured': measured}
            if level != first:
                tried += 1
        if tried >= extra_levels or level >= max_level:
            break
        level += 1
    return {'status': 'bundle_moved', 'level': first, 'measured': measured}
