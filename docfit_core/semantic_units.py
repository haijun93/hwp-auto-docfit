"""Semantic units used by both text analysis and HWP word-spacing checks."""
import re

STAFF_TITLE = r'(?:과[（(]동[)）]장|과장|동장|팀장|주무관|담당자|국장|실장|부장|차장|계장)'
STAFF_PREFIX = re.compile(STAFF_TITLE + r'[ \t]*[:：]?')
_STAFF_NAME = re.compile(r'(?<![\w가-힣])' + STAFF_TITLE +
                         r'[ \t]*[:：][ \t]*(?:[가-힣一-龥]{2,5}|[○◯]{2,5})(?![가-힣一-龥○◯])')


def staff_role_name_ranges(text):
    return [match.span() for match in _STAFF_NAME.finditer(text)]
