"""Structural corrections for newly expanded report abbreviations."""
from .batch_format import tag


def join_title_overview(root, converted):
    """Move a newly generated overview into its adjacent title's host paragraph."""
    removed = set()
    for (first, kind), (second, following) in zip(converted, converted[1:]):
        if kind not in ('title1', 'title2') or following != 'overview':
            continue
        children = list(root)
        if first not in children or second not in children or children.index(second) != children.index(first) + 1:
            continue
        if second.get('pageBreak', '0') != '0' or second.get('columnBreak', '0') != '0':
            continue
        runs = [x for x in second if tag(x) == 'run']
        if not runs or any(tag(x) not in ('run', 'linesegarray') for x in second):
            continue
        if any(tag(x) not in ('tbl', 't') or (tag(x) == 't' and ((x.text or '').strip() or len(x)))
               for run in runs for x in run):
            continue
        if sum(tag(x) == 'tbl' for run in runs for x in run) != 1:
            continue
        for run in runs:
            second.remove(run)
            first.append(run)
        for cache in list(first):
            if tag(cache) == 'linesegarray':
                first.remove(cache)
        root.remove(second)
        removed.add(second)
    converted[:] = [(p, kind) for p, kind in converted if p not in removed]
    return len(removed)
