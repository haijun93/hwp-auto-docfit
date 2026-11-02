"""엑셀 CF_HTML/TSV를 정리된 표 모델로 변환한다."""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.row, self.cell = [], None, None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'table':
            self.depth += 1
            return
        if self.depth != 1:
            return
        if tag == 'tr':
            self.row = []
        elif tag in ('td', 'th') and self.row is not None:
            style = a.get('style', '')
            self.cell = dict(text='', rowspan=_span(a.get('rowspan')), colspan=_span(a.get('colspan')),
                             align=_alignment(style, a.get('align')), bold=False,
                             fill=_color(style, 'background-color'), width=_width(style), numeric=False)
        elif self.cell is not None:
            style = a.get('style', '')
            if tag in ('b', 'strong') or re.search(r'font-weight\s*:\s*(bold|[6-9]00)', style, re.I): self.cell['bold'] = True
            if tag == 'br': self.cell['text'] += '\n'

    def handle_endtag(self, tag):
        if tag == 'table': self.depth = max(0, self.depth - 1)
        elif self.depth == 1 and tag in ('td', 'th') and self.cell is not None:
            self.cell['numeric'] = bool(re.fullmatch(r"[+-]?(?:\d[\d,]*(?:\.\d+)?|\.\d+)%?", self.cell['text'].strip()))
            if self.cell['numeric']: self.cell['align'] = 'right'
            self.row.append(self.cell); self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row); self.row = None

    def handle_data(self, data):
        if self.cell is not None: self.cell['text'] += data


def _span(v):
    try: return max(1, min(100, int(v)))
    except (ValueError, TypeError): return 1

def _alignment(style, attr):
    m = re.search(r'text-align\s*:\s*(left|center|right)', style, re.I)
    v = (m.group(1) if m else attr or '').lower()
    return v if v in ('left','center','right') else 'left'

def _color(style, key):
    m = re.search(rf'{key}\s*:\s*(#[\da-f]{{6}}|[\w]+)', style, re.I)
    return m.group(1).upper() if m and m.group(1).startswith('#') else ''

def _width(style):
    m = re.search(r'width\s*:\s*([\d.]+)\s*(px|pt|%)', style, re.I)
    return float(m.group(1)) if m else 0.0

def _clean_text(value):
    value = html.unescape(value).replace('_x000D_', '')
    value = ''.join(c for c in value if c in '\n\t' or ord(c) >= 32 and c not in '\u200b\u200c\u200d\ufeff')
    value = value.replace('\r', '').replace('\xa0', ' ').replace('\u3000', ' ')
    value = re.sub(r'\s+', ' ', value).strip()
    if value.startswith("'"): value = value[1:]
    return value

def _fragment(data):
    if isinstance(data, bytes): data = data.decode('utf-8', 'replace')
    m = re.search(r'StartFragment:\s*(\d+).*?EndFragment:\s*(\d+)', data, re.S|re.I)
    if m:
        try: return data[int(m.group(1)):int(m.group(2))]
        except Exception: pass
    m = re.search(r'<!--StartFragment-->(.*?)<!--EndFragment-->', data, re.S|re.I)
    return m.group(1) if m else data

def parse_clipboard(html_data=None, tsv=None, *, clean=True):
    """표 모델 및 정리 건수를 반환한다. 칸에는 text/merge/style 속성이 있다."""
    parser = _Parser()
    if html_data:
        parser.feed(_fragment(html_data))
    rows = parser.rows
    if not rows and tsv:
        rows = [[dict(text=x, rowspan=1, colspan=1, align='left', bold=False, fill='', width=0, numeric=False)
                 for x in line.split('\t')] for line in tsv.splitlines()]
    if not rows: raise ValueError('클립보드에서 엑셀 표를 찾지 못했습니다.')
    counts = dict(background=0, spaces=0, symbols=0)
    for row in rows:
        for cell in row:
            raw = cell['text']
            if re.search(r"^\s*'", raw): counts['symbols'] += 1
            if re.search(r'\s|&nbsp;|_x000D_|[\u200b-\u200d\ufeff]', raw): counts['spaces'] += 1
            if clean: cell['text'] = _clean_text(raw)
    while rows and all(not c['text'] for c in rows[-1]): rows.pop()
    maxcols = max((len(r) for r in rows), default=0)
    while maxcols and all(len(r) < maxcols or not r[maxcols-1]['text'] for r in rows): maxcols -= 1
    for row in rows:
        del row[maxcols:]
        while len(row) < maxcols: row.append(dict(text='', rowspan=1, colspan=1, align='left', bold=False, fill='', width=0, numeric=False))
    return {'rows': rows, 'row_count':len(rows), 'col_count':maxcols, 'cleaned':counts}
