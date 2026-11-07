"""표 칸 줄 간격·자간 하한(TCELL231). 본문 한도(linespacing_min 등)와 섞이지 않는다.

설정 `table_linespacing_min`(기본 100)·`table_spacing_min`(기본 -25)을 읽어 엔진이 하한으로 쓴다.
설정이 없거나 숫자가 아니면 기본값, 범위를 벗어나면 가까운 한도로 맞춘다(작업을 멈추지 않는다).
"""
from dataclasses import dataclass

DEFAULT_LINE_MIN = 100
DEFAULT_SPACING_MIN = -25
LINE_RANGE = (100, 500)       # 표 칸 줄 간격 하한(%)
SPACING_RANGE = (-50, 0)      # 자간 하한(%): 한/글 자간 한계 -50

BODY_SPACING_FLOOR = -50      # 표 칸이 아닌 곳의 자간 하한(한/글 한계)


def _number(value, default, low, high):
    try:
        number = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


@dataclass(frozen=True)
class TableLimits:
    line_min: int = DEFAULT_LINE_MIN
    spacing_min: int = DEFAULT_SPACING_MIN

    @classmethod
    def from_settings(cls, settings):
        settings = settings or {}
        return cls(
            _number(settings.get('table_linespacing_min'), DEFAULT_LINE_MIN, *LINE_RANGE),
            _number(settings.get('table_spacing_min'), DEFAULT_SPACING_MIN, *SPACING_RANGE),
        )


def spacing_floor(namespace, in_table_cell=None):
    """현재 위치의 자간 하한. 여러 칸 표의 칸이면 표 칸 하한, 그 밖(본문·한 칸 표)은 -50."""
    floor = namespace.get('표칸_자간_하한', DEFAULT_SPACING_MIN)
    if in_table_cell is None:
        in_table_cell = _in_multi_cell_table(namespace)
    return floor if in_table_cell else BODY_SPACING_FLOOR


def line_floor(namespace, body_floor, in_table_cell=None):
    """현재 위치의 줄 간격 하한. 여러 칸 표의 칸이면 표 칸 하한, 그 밖은 본문 하한(body_floor)."""
    if in_table_cell is None:
        in_table_cell = _in_multi_cell_table(namespace)
    return namespace.get('표칸_줄간격_하한', DEFAULT_LINE_MIN) if in_table_cell else body_floor


def _in_multi_cell_table(namespace):
    hwp = namespace.get('hwp')
    is_cell = namespace.get('현재_표셀인가')
    if hwp is None or is_cell is None:
        return False
    try:
        area = hwp.GetPos()[0]
        single = namespace.get('한칸표_보호영역') or ()
        return area > 0 and area not in single and bool(is_cell())
    except Exception:
        return False
