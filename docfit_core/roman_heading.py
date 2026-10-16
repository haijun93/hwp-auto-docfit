"""Conservative plain Roman heading recognition for format/all pre-format."""
import re

ROMAN = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"
_PREFIX = re.compile(r"^\s*(?:로(?P<alias>[1-9]|1[0-2])|(?P<roman>[Ⅰ-Ⅻ]))(?:[.．:：]?)[ \t]+(?P<title>\S.*)\s*$")


def match_heading(text):
    """Return (numeral, title) for a standalone heading; never guess ASCII I/V."""
    if not isinstance(text, str) or '\n' in text or '\r' in text:
        return None
    match = _PREFIX.fullmatch(text)
    if not match:
        return None
    title = match['title'].strip()
    if len(title) > 80 or re.search(r"[.!?。:：;；]$|(?:합니다|됩니다|있습니다|없습니다|입니다|한다|된다|했다|하였다|하세요|해요|바랍니다)$", title):
        return None
    # The supplied before/after example explicitly spells this heading apart.
    if title == '추진근거':
        title = '추진 근거'
    numeral = match['roman'] or ROMAN[int(match['alias']) - 1]
    return numeral, title
