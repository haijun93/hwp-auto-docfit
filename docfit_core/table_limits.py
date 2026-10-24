"""Table compression limits, independent of cell width and GUI state."""
from dataclasses import dataclass


@dataclass(frozen=True)
class TableLimits:
    line_min: int = 100
    spacing_min: int = -25

    @classmethod
    def from_settings(cls, settings):
        line = int(settings.get('table_linespacing_min', 100))
        spacing = int(settings.get('table_spacing_min', -25))
        if not 100 <= line <= 500 or not -25 <= spacing <= 0:
            raise ValueError('표 칸 줄 간격은 100~500%, 자간 하한은 -25~0%입니다.')
        return cls(line, spacing)

    def shrink_budget(self, values):
        return max(0, min(values, default=0) - self.spacing_min)


def spacing_floor(namespace, area=None):
    """Single-cell boxes retain their existing body policy (TODO decision)."""
    hwp = namespace.get('hwp')
    if hwp is None:
        return -50
    if area is None:
        area = hwp.GetPos()[0]
    single = namespace.get('한칸표_보호영역') or ()
    is_cell = namespace.get('현재_표셀인가')
    if area > 0 and area not in single and is_cell and is_cell():
        return namespace.get('표칸_자간_하한', -25)
    return -50
