"""파일·COM 접근 없는 캔버스 HWPX XML 조각 생성기.

표는 Element, 다이어그램·개요는 Element 목록을 반환한다. refs는 선택적
스타일 ID 매핑이다. border_fills/para_properties에 반환한 정의는 패키지
어댑터가 header.xml에 병합하고 ID를 전역 재매핑해야 한다.
완성 패키지의 한/글 2020 재열기 검증은 별도 게이트다.
"""
from defusedxml import ElementTree as ET

from docfit_core.session.canvas_commands import (
    InsertDiagramShapeCommand, InsertMindmapTreeCommand, InsertTableSketchCommand,
)
from docfit_core.table_sketch import UNIT_MM, normalize

HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
HH = '{http://www.hancom.co.kr/hwpml/2011/head}'
HC = '{http://www.hancom.co.kr/hwpml/2011/core}'


def _element(tag, **attrs):
    # 정적 빈 요소만 파싱한다. 사용자 글/속성은 Element API가 escape한다.
    node = ET.fromstring('<fragment/>')
    node.tag = tag
    node.attrib.update({k: str(v) for k, v in attrs.items()})
    return node


def _add(parent, tag, **attrs):
    node = _element(tag, **attrs)
    parent.append(node)
    return node


def _label(value):
    if (not isinstance(value, str) or len(value) > 10000 or
            any((ord(c) < 32 and c not in '\t\n\r') or
                0xD800 <= ord(c) <= 0xDFFF or ord(c) in (0xFFFE, 0xFFFF) for c in value)):
        raise ValueError('XML에 사용할 수 없는 글입니다.')
    return value


def _paragraph(text, refs, index=0, level=0):
    para_ids = refs.get('para_pr_ids', {})
    p = _element(HP+'p', id=int(refs.get('paragraph_id_start', 0))+index,
                 paraPrIDRef=para_ids.get(level, refs.get('para_pr_id', 0)),
                 styleIDRef=refs.get('style_id', 0), pageBreak=0, columnBreak=0, merged=0)
    run = _add(p, HP+'run', charPrIDRef=refs.get('char_pr_id', 0))
    _add(run, HP+'t').text = _label(text)
    return p


def _table(rows, cols, refs, width, height):
    table = _element(HP+'tbl', id=refs.get('object_id', 0), rowCnt=rows, colCnt=cols,
                     borderFillIDRef=refs.get('border_fill_id', 0), repeatHeader=0,
                     pageBreak='CELL', cellSpacing=0, noAdjust=0)
    _add(table, HP+'sz', width=width, height=height, widthRelTo='ABSOLUTE', heightRelTo='ABSOLUTE', protect=0)
    _add(table, HP+'pos', treatAsChar=1, affectLSpacing=0, flowWithText=1, allowOverlap=0,
         holdAnchorAndSO=0, vertRelTo='PARA', horzRelTo='COLUMN', vertAlign='TOP',
         horzAlign='LEFT', vertOffset=0, horzOffset=0)
    for tag in ('inMargin', 'outMargin'):
        _add(table, HP+tag, left=0, right=0, top=0, bottom=0)
    return table


def _cell(row, r, c, rs, cs, width, height, border_id):
    tc = _add(row, HP+'tc', borderFillIDRef=border_id, hasMargin=1, header=0, protect=0, editable=0, dirty=0)
    sub = _add(tc, HP+'subList', id=0, textDirection='HORIZONTAL', lineWrap='BREAK',
               vertAlign='CENTER', linkListIDRef=0, linkListNextIDRef=0, textWidth=0, textHeight=0,
               hasTextRef=0, hasNumRef=0)
    _add(tc, HP+'cellAddr', rowAddr=r, colAddr=c)
    _add(tc, HP+'cellSpan', rowSpan=rs, colSpan=cs)
    _add(tc, HP+'cellSz', width=width, height=height)
    _add(tc, HP+'cellMargin', left=142, right=142, top=142, bottom=142)
    return sub


def _border(cell, ident):
    node = _element(HH+'borderFill', id=ident, threeD=0, shadow=0, centerLine='NONE', breakCellSeparateLine=0)
    for tag, direction in (('slash', 'slash'), ('backSlash', 'backslash')):
        _add(node, HH+tag, type='CENTER' if cell['diagonal'] in (direction, 'cross') else 'NONE', Crooked=0, isCounter=0)
    def line(tag, width, style):
        _add(node, HH+tag, type='NONE' if width == 'none' else 'DOUBLE_SLIM' if width == 'double' else
             {'solid': 'SOLID', 'dash': 'DASH', 'dot': 'DOT'}[style],
             width={'none': '0.12 mm', 'thin': '0.12 mm', 'thick': '0.4 mm', 'double': '0.5 mm'}[width], color='#000000')
    for side in ('left', 'right', 'top', 'bottom'):
        line(side+'Border', cell['borders'][side], cell['border_styles'][side])
    diagonal = max(cell['diagonal_styles'].values(), key=lambda v: ('thin', 'thick', 'double').index(v[0]), default=('thin', 'solid'))
    line('diagonal', *diagonal)
    return node


def build_table_sketch_border_fills_xml(payload, refs=None):
    """표와 함께 header/refList/borderFills에 병합할 독립 정의 목록."""
    refs = refs or {}
    layout = InsertTableSketchCommand('builder', payload).compile(payload)['layout']
    start = int(refs.get('border_fill_id_start', 1))
    return [_border(cell, start+i) for i, cell in enumerate(layout['cells'])]


def build_table_sketch_xml(payload, refs=None):
    refs = refs or {}
    layout = InsertTableSketchCommand('builder', payload).compile(payload)['layout']
    mm = normalize(payload)[0]['grid']['cell_mm']
    xs, ys = layout['x_coords'], layout['y_coords']
    ux = [round((x-xs[0])*mm*UNIT_MM) for x in xs]
    uy = [round((y-ys[0])*mm*UNIT_MM) for y in ys]
    table = _table(layout['rows'], layout['cols'], refs, ux[-1], uy[-1])
    rows = [_add(table, HP+'tr') for _ in range(layout['rows'])]
    index = 0
    for i, cell in enumerate(layout['cells']):
        r, c, rs, cs = (cell[k] for k in ('row', 'col', 'rowspan', 'colspan'))
        sub = _cell(rows[r], r, c, rs, cs, ux[c+cs]-ux[c], uy[r+rs]-uy[r],
                    int(refs.get('border_fill_id_start', 1))+i)
        for item in cell['texts'] or [dict(text='', bold=False, align='center')]:
            local = {**refs, 'char_pr_id': refs.get('char_pr_ids', {}).get(item['bold'], refs.get('char_pr_id', 0)),
                     'para_pr_id': refs.get('alignment_para_pr_ids', {}).get(item['align'], refs.get('para_pr_id', 0))}
            for line in _label(item['text']).split('\n'):
                sub.append(_paragraph(line, local, index))
                index += 1
    return table


def _shape_scaffold(node, width, height):
    node.attrib.update(zOrder='0', numberingType='NONE', textWrap='TOP_AND_BOTTOM',
                       textFlow='BOTH_SIDES', lock='0', dropcapstyle='None', href='', groupLevel='0')
    node.set('instid', node.get('id'))
    _add(node, HP+'offset', x=0, y=0)
    _add(node, HP+'orgSz', width=width, height=height)
    _add(node, HP+'curSz', width=width, height=height)
    _add(node, HP+'flip', horizontal=0, vertical=0)
    _add(node, HP+'rotationInfo', angle=0, centerX=round(width/2), centerY=round(height/2), rotateimage=1)
    rendering = _add(node, HP+'renderingInfo')
    for tag in ('transMatrix', 'scaMatrix', 'rotMatrix'):
        _add(rendering, HC+tag, e1=1, e2=0, e3=0, e4=0, e5=1, e6=0)


def _unit(px):
    return round(px * 7200 / 96)


def build_diagram_shape_xml(payload, refs=None):
    refs = refs or {}
    graph = InsertDiagramShapeCommand('builder', payload).compile(payload)
    shapes, centers, output = graph['shapes'], {}, []
    ids = {s['id'] for s in shapes}
    if any(e['id'] in ids for e in graph['connectors']):
        raise ValueError('노드와 연결선 ID가 중복됩니다.')
    for i, shape in enumerate(shapes):
        _label(shape['id'])
        node = _element(HP+{'hp:rect': 'rect', 'hp:ellipse': 'ellipse'}[shape['target']],
                        id=int(refs.get('object_id_start', 1))+i)
        x, y, w, h = (_unit(shape[k]) for k in ('x', 'y', 'width', 'height'))
        _shape_scaffold(node, w, h)
        _add(node, HP+'sz', width=w, height=h, widthRelTo='ABSOLUTE', heightRelTo='ABSOLUTE', protect=0)
        _add(node, HP+'pos', treatAsChar=0, vertRelTo='PARA', horzRelTo='COLUMN',
             vertOffset=y, horzOffset=x, vertAlign='TOP', horzAlign='LEFT')
        _add(node, HP+'lineShape', color='#000000', width=75, style='SOLID',
             endCap='FLAT', headStyle='NORMAL', tailStyle='NORMAL', headfill=1,
             tailfill=1, headSz='SMALL_SMALL', tailSz='SMALL_SMALL', outlineStyle='NORMAL', alpha=255)
        # Geometry points use the core namespace (Hancom OWPML EllipseType).
        # https://github.com/hancom-io/hwpx-owpml-model/blob/main/OWPML/Class/Para/EllipseType.cpp
        if shape['target'] == 'hp:rect':
            node.set('ratio', '0')
            for j, (px, py) in enumerate(((0, 0), (w, 0), (w, h), (0, h))):
                _add(node, HC+'pt'+str(j), x=px, y=py)
        else:
            node.attrib.update(intervalDirty='0', hasArcPr='0', arcType='NORMAL')
            cx, cy = round(w/2), round(h/2)
            for tag, px, py in (('center', cx, cy), ('ax1', w, cy), ('ax2', cx, 0),
                               ('start1', w, cy), ('end1', w, cy), ('start2', w, cy), ('end2', w, cy)):
                _add(node, HC+tag, x=px, y=py)
        text = _add(node, HP+'drawText', lastWidth=w, name='', editable=0)
        sub = _add(text, HP+'subList', textDirection='HORIZONTAL', lineWrap='BREAK', vertAlign='CENTER')
        sub.append(_paragraph(shape['text'], refs, i))
        _add(text, HP+'textMargin', left=0, right=0, top=0, bottom=0)
        # Match the shape child order in tests/fixtures/hwp_shapes_sample.hwpx.
        for point in list(node):
            if point.tag.startswith(HC) and point.tag != HC+'fillBrush':
                node.remove(point)
                node.append(point)
        for tag in ('sz', 'pos'):
            child = node.find(HP+tag)
            node.remove(child)
            node.append(child)
        _add(node, HP+'outMargin', left=0, right=0, top=0, bottom=0)
        centers[shape['id']] = (_unit(shape['x']+shape['width']/2), _unit(shape['y']+shape['height']/2))
        output.append(node)
    for i, edge in enumerate(graph['connectors'], len(shapes)):
        _label(edge['id'])
        node = _element(HP+'connectLine', id=int(refs.get('object_id_start', 1))+i, type='STRAIGHT_ONEWAY')
        _shape_scaffold(node, abs(centers[edge['target']][0]-centers[edge['source']][0]),
                        abs(centers[edge['target']][1]-centers[edge['source']][1]))
        _add(node, HP+'startPt', subjectIDRef=0, subjectIdx=0, x=centers[edge['source']][0], y=centers[edge['source']][1])
        _add(node, HP+'endPt', subjectIDRef=0, subjectIdx=0, x=centers[edge['target']][0], y=centers[edge['target']][1])
        _add(node, HP+'lineShape', color='#000000', width=75, style='SOLID', headStyle='NORMAL', tailStyle='ARROW', headfill=1, tailfill=1)
        if edge['text']:
            draw = _add(node, HP+'drawText', lastWidth=0, name='', editable=0)
            sub = _add(draw, HP+'subList', textDirection='HORIZONTAL', lineWrap='BREAK', vertAlign='CENTER')
            sub.append(_paragraph(edge['text'], refs, i))
            _add(draw, HP+'textMargin', left=0, right=0, top=0, bottom=0)
        output.append(node)
    return output


def build_mindmap_para_properties_xml(refs=None):
    """level별 0.5인치 들여쓰기 정의. 어댑터가 기존 paraPr와 병합한다."""
    refs = refs or {}
    output = []
    for level in range(32):
        node = _element(HH+'paraPr', id=refs.get('para_pr_ids', {}).get(level, level))
        margin = _add(node, HH+'margin')
        _add(margin, HC+'left', value=level*3600, unit='HWPUNIT')
        output.append(node)
    return output


def build_mindmap_xml(payload, refs=None):
    refs = refs or {}
    # Constructor validation rejects non-finite JSON and Python object cycles.
    tree = InsertMindmapTreeCommand('builder', payload).compile(payload)
    local = {**refs, 'para_pr_ids': refs.get('para_pr_ids', {i: i for i in range(32)})}
    paragraphs = []
    for i, item in enumerate(tree['paragraphs']):
        _label(item['id'])
        _label(item['text'])
        # 번호는 라벨의 10000자 제한에 포함하지 않는다.
        p = _paragraph('', local, i, item['level'])
        p.find(HP+'run/'+HP+'t').text = item['number']+'\t'+item['text']
        paragraphs.append(p)
    if tree['mode'] == 'outline':
        return paragraphs
    table = _table(1, 1, refs, refs.get('table_width', 36000), refs.get('table_height', 7200))
    sub = _cell(_add(table, HP+'tr'), 0, 0, 1, 1, refs.get('table_width', 36000),
                refs.get('table_height', 7200), refs.get('border_fill_id', 0))
    sub.extend(paragraphs)
    return table
