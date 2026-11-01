"""파일 이름 일괄 변경 코어(순수 파이썬, UI·COM 없음).

흐름: Entry 목록 + 규칙 목록 → build_plan(읽기만) → execute_plan(rename만) → undo.
설계: docs/FILE_RENAME_DESIGN.md
"""
from .model import Entry, RuleError, split_name
from .rules import RULE_KINDS, apply_rules, validate_rules
from .numbering import natural_key
from .check import build_plan, invalid_name_reason
from .executor import PlanStaleError, execute_plan, undo
from .history import History

__all__ = [
    "Entry", "RuleError", "split_name", "RULE_KINDS", "apply_rules", "validate_rules", "natural_key",
    "build_plan", "invalid_name_reason", "PlanStaleError", "execute_plan", "undo", "History",
]
