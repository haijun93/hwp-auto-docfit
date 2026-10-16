"""Validated editable table HTML for the Windows HTML clipboard format."""
from html import escape
from .table_builder import normalize


def table_html(spec):
    t = normalize(spec)
    styles = t.get("styles", {})

    def cell(text, role, span=1):
        s = styles.get(role, {})
        borders = t.get("borders", {})
        border = borders.get("outer") or borders.get("line") or borders.get("box") or ("SOLID", "0.3 mm", "#4C4C4C")
        kind, width, color = border
        line = ("none" if kind == "NONE" or role == "arrow" else
                "double" if kind in {"DOUBLE_SLIM", "SLIM_THICK", "THICK_SLIM", "SLIM_THICK_SLIM"} else
                "dotted" if kind in {"DOT", "CIRCLE"} else
                "dashed" if "DASH" in kind else "solid")
        width = width.replace(" ", "")
        css = (f"border:{width} {line} {color};padding:4px;text-align:center;"
               f"font-family:{escape(s.get('font', '맑은 고딕'), quote=True)};"
               f"font-size:{s.get('size', 12)}pt;color:{s.get('color', '#000000')};"
               f"background-color:{s.get('fill') or '#FFFFFF'};"
               f"font-weight:{700 if s.get('bold') else 400};")
        return f'<td colspan="{span}" style="{css}">' + escape(str(text)).replace("\n", "<br>") + "</td>"

    rows = []
    plain = []
    def row(items):
        plain.append("\t".join(str(v[0]) for v in items))
        rows.append("<tr>" + "".join(cell(*v) for v in items) + "</tr>")

    if t["kind"] == "grid":
        for i, values in enumerate(t["rows"]):
            row([(v, "head" if i < t.get("header_rows", 1) else "body") for v in values])
    elif t["kind"] == "flow":
        steps = t["steps"]
        if t["direction"] == "vertical":
            for i, step in enumerate(steps):
                if i: row([(t["arrow"], "arrow")])
                row([(step["title"], "step")])
                for text in step["details"]: row([(text, "date")])
        else:
            for r in range(t["rows"] + 1):
                items = []
                for i, step in enumerate(steps):
                    if i: items.append((t["arrow"] if r == 0 else "", "arrow"))
                    items.append((step["title"] if r == 0 else step["details"][r-1], "step" if r == 0 else "date"))
                row(items)
    elif t["kind"] == "org":
        units=t["units"]
        row([(t["root"], "root", len(units))])
        row([("↓", "detail") for _ in units])
        row([(u["title"], "unit") for u in units])
        row([(u["detail"], "detail") for u in units])
    else:
        row([(t["title"], "title"), (t["note"], "note")])
    return '<table style="border-collapse:collapse">' + "".join(rows) + "</table>", "\n".join(plain)


def cf_html(fragment):
    """UTF-8 byte offsets (including Hangul), as required by CF_HTML."""
    prefix = b"<html><body><!--StartFragment-->"
    suffix = b"<!--EndFragment--></body></html>"
    fragment = fragment.encode("utf-8")
    template = "Version:0.9\r\nStartHTML:{:010d}\r\nEndHTML:{:010d}\r\nStartFragment:{:010d}\r\nEndFragment:{:010d}\r\n"
    start = len(template.format(0, 0, 0, 0).encode("ascii"))
    header = template.format(start, start+len(prefix)+len(fragment)+len(suffix), start+len(prefix), start+len(prefix)+len(fragment))
    return header.encode("ascii") + prefix + fragment + suffix
