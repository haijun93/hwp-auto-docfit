"""쪽 수 맞춤 고속 탐색(한/글 없이 시험할 수 있는 순수 로직).

레벨 L(0~최대레벨)은 기존 선형 방식에서 L단계까지 줄인 상태와 같다: 앞의 절반은 '문단 아래 간격',
뒤의 절반은 '문단 위 간격'을 1단계씩 줄이고, 표 셀 여백은 두 구간에 걸쳐 함께 줄인다.
레벨에 따라 쪽 수가 줄어든다고 보고 목표 쪽 수에 닿는 최소 레벨을 이분 탐색으로 찾는다.
"""


def classify_reports(reports, max_overflow_lines=4):
    """문서 유형과 1쪽에 맞출 보고서 번호를 정한다(사용자 규칙, 2026-10-09).

    reports: 보고서(제목 표 1개 + 계층체계 1개)마다 dict(start=첫 쪽, end=끝 쪽, overflow=끝 쪽에 걸린 줄 수|None).
    돌려주는 값: (유형, [1쪽에 맞출 보고서 번호]). 유형은 '1쪽 보고서'·'심화보고서'·'취합보고서'.
    끝 쪽으로 넘친 줄이 max_overflow_lines 이하인 2쪽짜리 보고서는 1쪽 보고서가 넘친 것으로 본다.
    """
    def spill(item):
        return (item['end'] == item['start'] + 1 and item.get('overflow') is not None
                and item['overflow'] <= max_overflow_lines)

    if len(reports) <= 1:
        if not reports or reports[0]['end'] <= reports[0]['start']:
            return '1쪽 보고서', []
        if spill(reports[0]):
            return '1쪽 보고서', [0]
        return '심화보고서', []
    return '취합보고서', [i for i, item in enumerate(reports) if spill(item)]


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
