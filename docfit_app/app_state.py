"""Plain application state; never depends on widgets or GUI event loops."""
from dataclasses import dataclass, field

STAGE_ORDER = ('열기','서식','자간','줄 병합','페이지 배치','저장')


@dataclass
class AppState:
    files: list = field(default_factory=list)
    mode: str = 'all'
    range: dict = field(default_factory=lambda:{'enabled':False,'start':'1','end':'1'})
    stages: dict = field(default_factory=dict)
    closing: bool = False
