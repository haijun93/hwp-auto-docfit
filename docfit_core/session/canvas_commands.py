"""Pure canvas insertion prototypes. HWPX package emission is adapter-owned."""
from copy import deepcopy
import json
import math

from docfit_core.table_sketch import normalize, preview


def _identifier(value):
    if not isinstance(value, str) or not value or len(value) > 128:
        raise ValueError('identifier must contain 1..128 characters')
    return value


def _text(value):
    if not isinstance(value, str) or len(value) > 10000:
        raise ValueError('invalid label')
    if any(ord(c) < 32 and c not in '\n\t\r' for c in value):
        raise ValueError('invalid control character')
    return value


def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1000000:
        raise ValueError('invalid canvas coordinate')
    return value


class _InsertCanvasCommand:
    kind = None

    def __init__(self, block_id, payload, *, after_id=None):
        self.block_id = _identifier(block_id)
        self.after_id = None if after_id is None else _identifier(after_id)
        # Freeze caller-owned JSON at construction, rejecting NaN and opaque objects.
        encoded = json.dumps(payload, allow_nan=False)
        if len(encoded.encode('utf-8')) > 2 * 1024 * 1024:
            raise ValueError('canvas payload exceeds 2 MiB')
        self.payload = json.loads(encoded)

    def apply(self, draft):
        document = draft.get('document', {'schema_version': 1, 'blocks': []})
        if not isinstance(document, dict) or document.get('schema_version') != 1:
            raise ValueError('unsupported document schema')
        blocks = document.get('blocks')
        if not isinstance(blocks, list) or any(not isinstance(b, dict) or 'id' not in b for b in blocks):
            raise ValueError('invalid blocks')
        if any(b['id'] == self.block_id for b in blocks):
            raise ValueError('duplicate block id')
        index = len(blocks)
        if self.after_id is not None:
            matches = [i for i, b in enumerate(blocks) if b['id'] == self.after_id]
            if len(matches) != 1:
                raise ValueError('insertion anchor missing or ambiguous')
            index = matches[0] + 1
        content = self.compile(deepcopy(self.payload))
        updated = deepcopy(document)
        updated['blocks'].insert(index, dict(id=self.block_id, kind=self.kind,
                                            source=deepcopy(self.payload), content=content))
        draft['document'] = updated


class InsertTableSketchCommand(_InsertCanvasCommand):
    kind = 'table_sketch'

    def compile(self, payload):
        drawing, warnings = normalize(payload)
        layout = preview(drawing)
        if warnings or not layout['cells'] or layout['warnings']:
            raise ValueError('invalid or lossy table sketch')
        return {'target': 'hp:tbl', 'layout': layout}


class InsertDiagramShapeCommand(_InsertCanvasCommand):
    kind = 'diagram'

    def compile(self, payload):
        nodes, edges = payload.get('nodes'), payload.get('edges', [])
        if not isinstance(nodes, list) or not 1 <= len(nodes) <= 1000 or not isinstance(edges, list) or len(edges) > 2000:
            raise ValueError('invalid graph size')
        ids, shapes = set(), []
        for node in nodes:
            ident = _identifier(node['id'])
            if ident in ids or node.get('type', 'rect') not in ('rect', 'ellipse'):
                raise ValueError('duplicate id or unsupported shape')
            ids.add(ident)
            pos = node['position']
            width, height = _number(node.get('width', 120)), _number(node.get('height', 60))
            if min(width, height) <= 0:
                raise ValueError('shape size must be positive')
            shapes.append(dict(id=ident, target='hp:' + node.get('type', 'rect'),
                               x=_number(pos['x']), y=_number(pos['y']), width=width,
                               height=height, text=_text(node.get('data', {}).get('label', ''))))
        connectors, edge_ids = [], set()
        for edge in edges:
            ident = _identifier(edge['id'])
            if ident in edge_ids or edge['source'] not in ids or edge['target'] not in ids:
                raise ValueError('invalid edge')
            edge_ids.add(ident)
            connectors.append(dict(id=ident, source=edge['source'], target=edge['target'],
                                   target_element='hp:connectLine', text=_text(edge.get('label', ''))))
        return dict(unit='css_px_96dpi', shapes=shapes, connectors=connectors)


class InsertMindmapTreeCommand(_InsertCanvasCommand):
    kind = 'mindmap'

    def compile(self, payload):
        mode = payload.get('mode', 'outline')
        if mode not in ('outline', 'summary_table'):
            raise ValueError('invalid mindmap mode')
        seen, paragraphs = set(), []

        def visit(node, path):
            if len(path) > 32 or len(seen) >= 1000:
                raise ValueError('tree limit exceeded')
            ident = _identifier(node['id'])
            if ident in seen:
                raise ValueError('duplicate tree node')
            seen.add(ident)
            paragraphs.append(dict(id=ident, level=len(path)-1,
                                   number='.'.join(map(str, path)), text=_text(node['text'])))
            children = node.get('children', [])
            if not isinstance(children, list):
                raise ValueError('children must be an array')
            for index, child in enumerate(children, 1):
                visit(child, path + [index])

        visit(payload['root'], [1])
        return dict(target='hp:p' if mode == 'outline' else 'hp:tbl',
                    mode=mode, paragraphs=paragraphs)
