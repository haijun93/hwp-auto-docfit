"""Shared recognition and geometry for paragraphs continuing a labelled item."""
from functools import lru_cache
import copy
import re
from pathlib import Path

from defusedxml import ElementTree as ET

from .batch_format import ParagraphStyle, StylePool, plain_text, tag, _serialize
from .fidelity.package import PackageSnapshot, build_package
from .hwpx import validate_hwpx
from .marker_scheme import classify_marker


def leading_width(text):
    return len(text[:len(text) - len(text.lstrip(' \t'))].expandtabs(4))


def is_supplement(text):
    return bool(re.match(r'^\s*(?:※|\*{1,2})(?:\s|[「『(\[])', text or ''))


def is_continuation(parent_indent, text):
    """More deeply indented explanations belong to the parent, including notes."""
    if not text or not text.strip() or leading_width(text) <= parent_indent:
        return False
    if is_supplement(text):
        return True
    # Ranges such as (6~16번) are explanations, numbered lists are independent.
    return classify_marker(text) is None


def inline_item(text):
    """Return (family, marker start, body start) only for a single inline item."""
    outer = classify_marker(text)
    if not outer:
        return None
    colon = re.match(r'\s*[^:：\r\n]{1,30}[:：][ \t]+', text[outer[1]:])
    if not colon:
        return None
    start = outer[1] + colon.end()
    item = classify_marker(text[start:])
    if not item:
        return None
    family, end = item
    body = start + end
    while body < len(text) and text[body] in ' \t':
        body += 1
    # Two numbered items on one line retain the original colon alignment.
    tail = text[body:]
    for match in re.finditer(r'\S+', tail):
        if classify_marker(tail[match.start():]):
            return None
    return family, start, body


@lru_cache(maxsize=256)
def _font(face):
    from .hangul_fonts import font_file
    from PIL import ImageFont
    path = font_file(face)
    return ImageFont.truetype(str(path), 1000) if path else None


def text_width(text, shape, fonts):
    """Use the installed Hangul font's glyph advances, including ratio/spacing."""
    height = int(shape.get('height', '1300'))
    ref = next((x for x in shape if tag(x) == 'fontRef'), None)
    face = fonts.get(ref.get('hangul')) if ref is not None else None
    font = _font(face) if face else None
    ratio = next((int(x.get('hangul', '100')) for x in shape if tag(x) == 'ratio'), 100)
    spacing = next((int(x.get('hangul', '0')) for x in shape if tag(x) == 'spacing'), 0)
    if font is None:
        # HFT cannot be measured by FreeType. Keep existing geometry for that paragraph.
        raise ValueError('연속 문단 폭 측정용 글꼴을 찾을 수 없습니다: ' + str(face))
    return round(font.getlength(text) * height / 1000 * ratio / 100 + len(text) * height * spacing / 100)


def geometry(anchor, body):
    """HWPX first-line x = left + intent; subsequent lines start at left."""
    return (body, -body), (body, anchor - body)


def _chars(paragraph):
    result = []
    for run in paragraph:
        if tag(run) == 'run':
            result.extend([run.get('charPrIDRef')] * len(run[0].text or ''))
    return result


def _para(pool, base, spec):
    before = len(pool.groups['paraProperties'])
    result = pool.para(base, spec)
    group = pool.groups['paraProperties']
    if len(group) > before:
        created = group[-1]
        comparable = copy.deepcopy(created)
        for existing in list(group)[:-1]:
            comparable.set('id', existing.get('id'))
            if ET.tostring(comparable) == ET.tostring(existing):
                result = existing.get('id')
                group.remove(created)
                group.set('itemCnt', str(len(group)))
                pool.paragraphs[(base, spec.line_percent, spec.prev_pt, spec.para_extra)] = result
                break
    pool.sources['paraProperties'].update({x.get('id'): x for x in group})
    return result


def _split_soft_continuations(root):
    """A numbered manual break becomes a paragraph so it can carry its own geometry."""
    for p in list(root):
        if tag(p) != 'p' or not any(tag(x) == 'lineBreak' for x in p.iter()):
            continue
        if any(tag(x) not in ('run', 'linesegarray', 'lineseg', 't', 'lineBreak') for x in p.iter() if x is not p):
            continue
        fragments = [[]]
        for run in p:
            if tag(run) != 'run':
                continue
            for t in run:
                if t.text:
                    fragments[-1].append((run, t.text))
                for br in t:
                    fragments.append([])
                    if br.tail:
                        fragments[-1].append((run, br.tail))
        texts = [''.join(text for _, text in parts) for parts in fragments]
        inline = inline_item(texts[0]) if texts else None
        if not inline or not all(classify_marker(t) and classify_marker(t)[0] == inline[0] for t in texts[1:]):
            continue
        position = list(root).index(p)
        root.remove(p)
        for i, parts in enumerate(fragments):
            new = copy.deepcopy(p)
            for child in list(new):
                new.remove(child)
            if i:
                new.set('pageBreak', '0')
                new.set('columnBreak', '0')
            for proto, text in parts:
                run = copy.deepcopy(proto)
                for extra in list(run[0]):
                    run[0].remove(extra)
                run[0].text = text
                new.append(run)
            root.insert(position + i, new)


def _copy_roles(paragraph, text, body_id, paren_id, prototype):
    """Copy role shapes, never the parent's label shape, to the continuation."""
    for child in list(paragraph):
        paragraph.remove(child)
    ids = [body_id] * len(text)
    for match in re.finditer(r'\([^()]*\)', text):
        ids[match.start():match.end()] = [paren_id] * len(match.group())
    start = 0
    while start < len(text):
        end = start + 1
        while end < len(text) and ids[end] == ids[start]:
            end += 1
        run = copy.deepcopy(prototype)
        run.set('charPrIDRef', ids[start])
        run[0].text = text[start:end]
        for extra in list(run[0]):
            run[0].remove(extra)
        paragraph.append(run)
        start = end


def align_sections(header, sections, *, source_sections=None, rules=None, measure=text_width,
                   include_plain=False):
    """Align only direct body paragraphs; controls, pages, lists and profiles are boundaries."""
    rules = rules or {}
    pool = StylePool(header)
    chars = pool.sources['charProperties']
    fonts = {f.get('id'): f.get('face') for ff in header.iter() if tag(ff) == 'fontface'
             and ff.get('lang') == 'HANGUL' for f in ff if tag(f) == 'font'}
    changed = set()
    for name, root in sections.items():
        original_root = (source_sections or sections)[name]
        if original_root is not root:
            _split_soft_continuations(original_root)
        _split_soft_continuations(root)
        paragraphs = [p for p in root if tag(p) == 'p']
        originals = [p for p in original_root if tag(p) == 'p']
        state = None
        for index, p in enumerate(paragraphs):
            text = plain_text(p)
            original = plain_text(originals[index]) if index < len(originals) else text
            if (not text or not original or p.get('pageBreak', '0') != '0'
                    or p.get('columnBreak', '0') != '0'):
                state = None
                continue
            shape = pool.sources['paraProperties'].get(p.get('paraPrIDRef'))
            heading = next((x for x in shape.iter() if tag(x) == 'heading'), None) if shape is not None else None
            if heading is not None and heading.get('type', 'NONE') != 'NONE':
                state = None
                continue
            marker = classify_marker(text)
            family = marker[0] if marker else None
            if rules.get(family) in ('none', 'fixed', 'after_marker'):
                state = None
                continue
            inline = inline_item(text)
            if inline:
                family, start, body = inline
                ids = _chars(p)
                try:
                    anchor = sum(measure(text[i], chars[ids[i]], fonts) for i in range(start))
                    end = anchor + sum(measure(text[i], chars[ids[i]], fonts) for i in range(start, body))
                except (ValueError, OSError):
                    state = None
                    continue
                paren = re.search(r'\([^()]*\)', text[body:])
                paren_id = ids[body + paren.start()] if paren else ids[body]
                state = (family, anchor, end, p, ids[body], paren_id, index)
                first_pair, _ = geometry(anchor, end)
                spec = ParagraphStyle(text=text, para_extra=(('left', first_pair[0]), ('intent', first_pair[1])))
                p.set('paraPrIDRef', _para(pool, p.get('paraPrIDRef'), spec))
                for cache in list(p):
                    if tag(cache) == 'linesegarray':
                        p.remove(cache)
                changed.add(text)
                continue
            is_plain = (include_plain and state and state[0] is None and
                        is_continuation(state[6], original))
            if state and ((family is not None and family == state[0]) or is_plain):
                _, anchor, end, parent, body_id, paren_id, _ = state
                cleaned = text.lstrip(' \t')
                proto = next(x for x in parent if tag(x) == 'run')
                _copy_roles(p, cleaned, body_id, paren_id, proto)
                _, pair = geometry(anchor, end)
                # Same paragraph style as the parent, with geometry rebased after removing spaces.
                spec = ParagraphStyle(text=cleaned, para_extra=(('left', pair[0]), ('intent', pair[1])))
                p.set('paraPrIDRef', _para(pool, parent.get('paraPrIDRef'), spec))
                changed.add(cleaned)
                continue
            state = None
            if include_plain and marker:
                start = marker[1]
                while start < len(text) and text[start].isspace():
                    start += 1
                ids = _chars(p)
                if start >= len(ids):
                    continue
                try:
                    anchor = sum(measure(text[i], chars[ids[i]], fonts) for i in range(start))
                except (ValueError, OSError):
                    continue
                paren = re.search(r'\([^()]*\)', text[start:])
                paren_id = ids[start + paren.start()] if paren else ids[start]
                state = (None, anchor, anchor, p, ids[start], paren_id, leading_width(original))
    return changed


def align_hwpx(source, target, *, original=None, rules=None, include_plain=False):
    snapshot = PackageSnapshot.load(source)
    metadata = validate_hwpx(source)
    header = ET.fromstring(snapshot.read('Contents/header.xml'))
    sections = {n: ET.fromstring(snapshot.read(n)) for n in metadata['section_names']}
    old = PackageSnapshot.load(original) if original else snapshot
    old_sections = {n: ET.fromstring(old.read(n)) for n in metadata['section_names']}
    changed = align_sections(header, sections, source_sections=old_sections, rules=rules,
                             include_plain=include_plain)
    if changed:
        replacements = {n: _serialize(s, snapshot.read(n)) for n, s in sections.items()}
        replacements['Contents/header.xml'] = _serialize(header, snapshot.read('Contents/header.xml'))
        Path(target).write_bytes(build_package(snapshot, replacements))
        validate_hwpx(target)
    return changed
