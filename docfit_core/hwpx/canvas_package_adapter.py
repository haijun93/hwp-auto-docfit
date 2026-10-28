"""Copy-on-write canvas package merging (structural validation, no COM)."""
from copy import deepcopy
from io import BytesIO
import os
from pathlib import Path
import re
import tempfile
import zlib
from zipfile import ZipFile, BadZipFile

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from docfit_core.hwpx import HwpxLimits, _safe_member_name
from docfit_core.hwpx.canvas_hwpx_builder import (
    HP, HH, HC, _element, build_table_sketch_xml,
    build_table_sketch_border_fills_xml, build_diagram_shape_xml,
    build_mindmap_xml, build_mindmap_para_properties_xml,
)


def _read_package(data):
    try:
        with ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            limits = HwpxLimits()
            names, total = set(), 0
            if len(infos) > limits.max_entries:
                raise ValueError('too many ZIP entries')
            for info in infos:
                _safe_member_name(info)
                name = info.filename.replace('\\', '/')
                total += info.file_size
                if (name in names or info.flag_bits & 1 or
                        info.file_size > limits.max_file_size or
                        total > limits.max_total_size or
                        info.file_size > max(info.compress_size, 1)*limits.max_compression_ratio):
                    raise ValueError('unsafe ZIP entry')
                names.add(name)
            members = {i.filename: archive.read(i) for i in infos}
            roots = {name: ET.fromstring(value, forbid_dtd=True)
                     for name, value in members.items() if name.endswith('.xml')}
            if (roots['Contents/header.xml'].tag != HH+'head' or
                    roots['Contents/section0.xml'].tag != '{http://www.hancom.co.kr/hwpml/2011/section}sec'):
                raise ValueError('invalid HWPX root')
            return infos, members, roots
    except (BadZipFile, KeyError, ET.ParseError, DefusedXmlException,
            RuntimeError, NotImplementedError, EOFError, zlib.error) as exc:
        raise ValueError('invalid HWPX package') from exc


def _ids(container):
    values = [int(n.attrib['id']) for n in container]
    if any(v < 0 for v in values) or len(values) != len(set(values)):
        raise ValueError('invalid or duplicate header ID')
    return values


def merge_canvas_block_into_hwpx(hwpx_bytes_or_path, block_data, output_path=None):
    """Return merged ZIP bytes; optionally atomically publish to a distinct path.

    Blocks use session kind/source (payload is also accepted). Optional after_id
    or anchor_id identifies a direct section0 paragraph; omission appends.
    Schema conformance and Hancom rendering remain separate integration gates.
    """
    source = None if isinstance(hwpx_bytes_or_path, (bytes, bytearray)) else Path(hwpx_bytes_or_path)
    target = Path(output_path) if output_path is not None else None
    if source is not None and target is not None:
        if source.resolve() == target.resolve() or (target.exists() and os.path.samefile(source, target)):
            raise ValueError('output must differ from original')
    data = source.read_bytes() if source is not None else bytes(hwpx_bytes_or_path)
    infos, members, roots = _read_package(data)
    header, section = roots['Contents/header.xml'], roots['Contents/section0.xml']
    ref_list = header.find(HH+'refList')
    if ref_list is None:
        raise ValueError('missing refList')
    pools = {}
    for name in ('borderFills', 'charProperties', 'paraProperties', 'styles'):
        pool = ref_list.find(HH+name)
        if pool is None or not len(pool):
            raise ValueError('missing style pool: '+name)
        _ids(pool)
        pools[name] = pool
    paragraphs = list(section.findall(HP+'p'))
    anchor = block_data.get('after_id', block_data.get('anchor_id'))
    index = len(section)
    base_p = paragraphs[0] if paragraphs else None
    if anchor is not None:
        matches = [p for p in paragraphs if p.get('id') == str(anchor)]
        if len(matches) != 1:
            raise ValueError('insertion anchor missing or ambiguous')
        base_p = matches[0]
        index = list(section).index(base_p)+1
    refs = dict(border_fill_id=_ids(pools['borderFills'])[0],
                char_pr_id=_ids(pools['charProperties'])[0],
                para_pr_id=_ids(pools['paraProperties'])[0], style_id=_ids(pools['styles'])[0])
    if base_p is not None:
        for attr, key in (('paraPrIDRef', 'para_pr_id'), ('styleIDRef', 'style_id')):
            refs[key] = int(base_p.get(attr, refs[key]))
        run = base_p.find(HP+'run')
        if run is not None:
            refs['char_pr_id'] = int(run.get('charPrIDRef', refs['char_pr_id']))
    sections = [r for n, r in roots.items() if re.fullmatch(r'Contents/section\d+\.xml', n)]
    maximum = max((int(n.get(a)) for r in sections for n in r.iter()
                   for a in ('id', 'instid') if (n.get(a) or '').isdigit()), default=0)
    refs.update(object_id=maximum+1, object_id_start=maximum+1, paragraph_id_start=maximum+1)

    def clone(pool_name, ident):
        pool = pools[pool_name]
        original = next((n for n in pool if n.get('id') == str(ident)), None)
        if original is None:
            raise ValueError('missing style reference')
        node = deepcopy(original)
        node.set('id', str(max(_ids(pool))+1))
        pool.append(node)
        return node

    kind, payload = block_data.get('kind'), block_data.get('source', block_data.get('payload'))
    if kind == 'table_sketch':
        refs['border_fill_id_start'] = max(_ids(pools['borderFills']))+1
        refs['char_pr_ids'] = {}
        for bold in (False, True):
            node = clone('charProperties', refs['char_pr_id'])
            for child in list(node.findall(HH+'bold')):
                node.remove(child)
            if bold:
                node.append(_element(HH+'bold'))
            refs['char_pr_ids'][bold] = int(node.get('id'))
        refs['alignment_para_pr_ids'] = {}
        for align in ('left', 'center', 'right'):
            node = clone('paraProperties', refs['para_pr_id'])
            alignment = node.find(HH+'align')
            if alignment is None:
                alignment = _element(HH+'align', vertical='BASELINE')
                node.insert(0, alignment)
            alignment.set('horizontal', align.upper())
            refs['alignment_para_pr_ids'][align] = int(node.get('id'))
        elements = [build_table_sketch_xml(payload, refs)]
        pools['borderFills'].extend(build_table_sketch_border_fills_xml(payload, refs))
    elif kind == 'diagram':
        elements = build_diagram_shape_xml(payload, refs)
    elif kind == 'mindmap':
        start = max(_ids(pools['paraProperties']))+1
        refs['para_pr_ids'] = {i: start+i for i in range(32)}
        for definition in build_mindmap_para_properties_xml(refs):
            node = clone('paraProperties', refs['para_pr_id'])
            node.set('id', definition.get('id'))
            margin = node.find(HH+'margin')
            if margin is None:
                margin = _element(HH+'margin')
                node.append(margin)
            left = margin.find(HC+'left')
            if left is not None:
                margin.remove(left)
            margin.append(deepcopy(definition.find(HH+'margin/'+HC+'left')))
        result = build_mindmap_xml(payload, refs)
        elements = result if isinstance(result, list) else [result]
    else:
        raise ValueError('unsupported canvas block kind')
    if elements and elements[0].tag != HP+'p':
        wrapper = _element(HP+'p', paraPrIDRef=refs['para_pr_id'], styleIDRef=refs['style_id'], pageBreak=0, columnBreak=0, merged=0)
        run = _element(HP+'run', charPrIDRef=refs['char_pr_id'])
        run.extend(elements)
        wrapper.append(run)
        elements = [wrapper]
    next_id = maximum+1
    for root in elements:
        for node in root.iter():
            if node.tag == HP+'p' or 'id' in node.attrib:
                node.set('id', str(next_id))
                if 'instid' in node.attrib:
                    node.set('instid', str(next_id))
                next_id += 1
    reference_pools = {'borderFillIDRef': 'borderFills', 'charPrIDRef': 'charProperties',
                       'paraPrIDRef': 'paraProperties', 'styleIDRef': 'styles'}
    valid_refs = {attr: set(_ids(pools[name])) for attr, name in reference_pools.items()}
    # Check source and generated style references before publishing anything.
    for root in [header, *sections, *elements]:
        for node in root.iter():
            for attr, ids in valid_refs.items():
                if attr in node.attrib and int(node.get(attr)) not in ids:
                    raise ValueError('dangling style reference: '+attr)
    for offset, element in enumerate(elements):
        section.insert(index+offset, element)
    for pool in pools.values():
        pool.set('itemCnt', str(len(pool)))
    for name, root in (('Contents/header.xml', header), ('Contents/section0.xml', section)):
        members[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    output = BytesIO()
    with ZipFile(output, 'w') as archive:
        for info in infos:
            archive.writestr(info, members[info.filename])
    merged = output.getvalue()
    _read_package(merged)
    if target is not None:
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.'+target.name+'.', suffix='.tmp', delete=False) as temp:
                temp_name = temp.name
                temp.write(merged)
                temp.flush()
                os.fsync(temp.fileno())
            _read_package(Path(temp_name).read_bytes())
            os.replace(temp_name, target)
        finally:
            if temp_name is not None and os.path.exists(temp_name):
                os.unlink(temp_name)
    return merged
