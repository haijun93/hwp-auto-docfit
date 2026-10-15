"""Widget-free document state and processing option resolution."""
from dataclasses import dataclass, field
from typing import Literal
from .stage_selection import default_choice, stages_for_mode, without_tables


@dataclass
class RunOptions:
    mode: Literal["spacing", "unify", "format", "all"] = "all"
    include_spacing: bool = True
    reset_spacing: bool = True
    table_spacing: bool = True
    exclude_tables: bool = False
    verify_result: bool = True
    autoclose: bool = False
    developer_mode: bool = False
    page_range: str = ""

    def __post_init__(self):
        if self.mode not in ("spacing", "unify", "format", "all"):
            raise ValueError("지원하지 않는 작업 모드입니다.")

    @property
    def effective_mode(self):
        return "format" if self.mode == "all" and not self.include_spacing else self.mode

    @property
    def effective_table_spacing(self):
        return self.table_spacing and not self.exclude_tables

    def resolve_stages(self, stage_choices):
        mode = self.effective_mode
        selected = stage_choices.get(mode, {})
        result = {key: bool(selected.get(key, default_choice(key, mode)))
                  for key, _ in stages_for_mode(mode)}
        if "reset_spacing" in result:
            result["reset_spacing"] = self.reset_spacing
        if self.exclude_tables:
            result = without_tables(result)
        if not self.effective_table_spacing:
            for key in ("control_spacing", "control_short_line", "control_word_check"):
                if key in result:
                    result[key] = False
        return result


@dataclass
class AppState:
    files: list = field(default_factory=list)
    running: bool = False
    options: RunOptions = field(default_factory=RunOptions)
    profiles: dict = field(default_factory=dict)
    profile_ids: list = field(default_factory=list)
    active_profile_id: str = ""
    analyzing_format: bool = False
    analyzing_file: str = ""
    results: list = field(default_factory=list)
    stage_choices: dict = field(default_factory=dict)
    default_saved: dict = field(default_factory=dict)
