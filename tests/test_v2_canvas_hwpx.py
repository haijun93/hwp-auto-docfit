"""순수 캔버스 XML 빌더의 구조·단위·입력 경계 회귀 시험."""
import copy
import unittest
from unittest.mock import patch

from defusedxml import ElementTree as ET
from docfit_core.hwpx.canvas_hwpx_builder import (
    HP, HH, HC, build_table_sketch_xml, build_table_sketch_border_fills_xml,
    build_diagram_shape_xml, build_mindmap_xml, build_mindmap_para_properties_xml,
)


def sketch():
    return {'grid': {'cols': 2, 'rows': 2, 'cell_mm': 5}, 'lines': [
        dict(x1=a, y1=b, x2=c, y2=d) for a, b, c, d in
        [(0, 0, 2, 0), (2, 0, 2, 2), (2, 2, 0, 2), (0, 2, 0, 0),
         (0, 1, 2, 1), (1, 1, 1, 2)]],
        'texts': [dict(x=0, y=0, text='<&한글', bold=True, align='left')]}


def graph():
    return {'nodes': [dict(id='a', type='rect', position={'x': -1.5, 'y': 2.5}, width=3, height=5,
                           data={'label': '<&한글'}),
                      dict(id='b', type='ellipse', position={'x': 96, 'y': 48}, width=120, height=60)],
            'edges': [dict(id='e', source='a', target='b', label='연결')]}


def tree():
    return {'root': {'id': 'r', 'text': 'root', 'children': [
        {'id': 'a', 'text': 'A', 'children': [{'id': 'b', 'text': 'B'}]},
        {'id': 'c', 'text': 'C'}]}}


class CanvasHwpxTests(unittest.TestCase):
    def test_table_structure_spans_text_and_cumulative_size(self):
        table = build_table_sketch_xml(sketch())
        self.assertEqual(table.tag, HP+'tbl')
        self.assertEqual(table.get('rowCnt'), '2')
        rows = table.findall(HP+'tr')
        self.assertEqual([len(r.findall(HP+'tc')) for r in rows], [1, 2])
        cells = table.findall('.//'+HP+'tc')
        self.assertEqual(cells[0].find(HP+'cellSpan').get('colSpan'), '2')
        self.assertEqual(cells[2].find(HP+'cellAddr').attrib, {'rowAddr': '1', 'colAddr': '1'})
        sizes = [c.find(HP+'cellSz') for c in cells]
        self.assertEqual(int(sizes[1].get('width'))+int(sizes[2].get('width')), int(sizes[0].get('width')))
        self.assertIn('<&한글', list(table.itertext()))
        ET.fromstring(ET.tostring(table))

    def test_table_border_definitions_and_refs(self):
        refs = {'border_fill_id_start': 81, 'char_pr_ids': {True: 7}, 'alignment_para_pr_ids': {'left': 9}}
        before = copy.deepcopy(refs)
        table = build_table_sketch_xml(sketch(), refs)
        borders = build_table_sketch_border_fills_xml(sketch(), refs)
        self.assertEqual([c.get('borderFillIDRef') for c in table.findall('.//'+HP+'tc')], ['81', '82', '83'])
        self.assertEqual([b.get('id') for b in borders], ['81', '82', '83'])
        self.assertEqual(borders[0].find(HH+'leftBorder').get('type'), 'SOLID')
        self.assertEqual(table.find('.//'+HP+'run').get('charPrIDRef'), '7')
        self.assertEqual(table.find('.//'+HP+'p').get('paraPrIDRef'), '9')
        self.assertEqual(refs, before)

    def test_table_rejects_lossy_or_empty_layout(self):
        for payload in ({'grid': {'cols': 1, 'rows': 1}},
                        {**sketch(), 'texts': [dict(x=0, y=0, text='bad\x00')]}):
            with self.assertRaises(ValueError):
                build_table_sketch_xml(payload)

    def test_diagram_exact_units_and_center_arrows(self):
        elements = build_diagram_shape_xml(graph(), {'object_id_start': 20})
        self.assertEqual([e.tag for e in elements], [HP+'rect', HP+'ellipse', HP+'connectLine'])
        self.assertEqual([e.get('id') for e in elements], ['20', '21', '22'])
        self.assertEqual(elements[0].find(HP+'pos').get('horzOffset'), str(round(-1.5*7200/96)))
        self.assertEqual(elements[0].find(HP+'pos').get('vertOffset'), str(round(2.5*7200/96)))
        self.assertEqual(elements[0].find(HP+'sz').get('width'), '225')
        self.assertEqual(elements[1].find(HP+'pos').get('horzOffset'), '7200')
        self.assertEqual(elements[2].find(HP+'startPt').attrib, {'subjectIDRef': '0', 'subjectIdx': '0', 'x': '0', 'y': '375'})
        self.assertEqual(elements[2].find(HP+'endPt').attrib, {'subjectIDRef': '0', 'subjectIdx': '0', 'x': '11700', 'y': '5850'})
        self.assertEqual(elements[2].find(HP+'lineShape').get('tailStyle'), 'ARROW')
        self.assertEqual(elements[0].find(HC+'pt2').attrib, {'x': '225', 'y': '375'})
        self.assertEqual(elements[1].find(HC+'center').attrib, {'x': '4500', 'y': '2250'})
        for element in elements:
            ET.fromstring(ET.tostring(element))
            self.assertEqual(element.findall('.//'+HP+'lineseg'), [])

    def test_diagram_rejects_invalid_geometry(self):
        for key, value in [('width', 0), ('height', -1), ('width', float('nan')),
                           ('height', float('inf')), ('type', 'triangle')]:
            payload = graph()
            payload['nodes'][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                build_diagram_shape_xml(payload)
        for value in (float('nan'), float('-inf'), True, 1000001):
            payload = graph()
            payload['nodes'][0]['position']['x'] = value
            with self.assertRaises(ValueError):
                build_diagram_shape_xml(payload)

    def test_diagram_rejects_duplicate_ids_missing_endpoints_and_limits(self):
        for mutate in (lambda p: p['nodes'][1].update(id='a'),
                       lambda p: p['edges'].append(copy.deepcopy(p['edges'][0])),
                       lambda p: p['edges'][0].update(id='a'),
                       lambda p: p['edges'][0].update(target='absent'),
                       lambda p: p.update(nodes=p['nodes']*501),
                       lambda p: p.update(edges=p['edges']*2001)):
            payload = graph()
            mutate(payload)
            with self.assertRaises(ValueError):
                build_diagram_shape_xml(payload)

    def test_diagram_inclusive_graph_limits(self):
        nodes = [dict(id=str(i), position={'x': i, 'y': 0}) for i in range(1000)]
        edges = [dict(id='e'+str(i), source='0', target='999') for i in range(2000)]
        self.assertEqual(len(build_diagram_shape_xml({'nodes': nodes, 'edges': edges})), 3000)

    def test_mindmap_rejects_nonfinite_json(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.assertRaises(ValueError):
                build_mindmap_xml({**tree(), 'unused': value})

    def test_mindmap_preorder_numbers_tabs_and_indents(self):
        paragraphs = build_mindmap_xml(tree())
        self.assertEqual([''.join(p.itertext()) for p in paragraphs],
                         ['1\troot', '1.1\tA', '1.1.1\tB', '1.2\tC'])
        self.assertEqual([p.get('paraPrIDRef') for p in paragraphs], ['0', '1', '2', '1'])
        definitions = build_mindmap_para_properties_xml()
        self.assertEqual(definitions[2].find(HH+'margin/'+HC+'left').get('value'), '7200')
        self.assertFalse(any(p.findall('.//'+HP+'lineseg') for p in paragraphs))

    def test_mindmap_summary_table(self):
        table = build_mindmap_xml({**tree(), 'mode': 'summary_table'})
        self.assertEqual((table.get('rowCnt'), table.get('colCnt')), ('1', '1'))
        self.assertEqual(len(table.findall(HP+'tr/'+HP+'tc')), 1)
        self.assertEqual([''.join(p.itertext()) for p in table.findall('.//'+HP+'p')],
                         ['1\troot', '1.1\tA', '1.1.1\tB', '1.2\tC'])

    def test_mindmap_duplicate_and_python_cycle(self):
        payload = tree()
        payload['root']['children'][0]['id'] = 'r'
        with self.assertRaises(ValueError):
            build_mindmap_xml(payload)
        payload = tree()
        payload['root']['children'].append(payload['root'])
        with self.assertRaises(ValueError):
            build_mindmap_xml(payload)

    def test_mindmap_depth_and_count_boundaries(self):
        root = {'id': '0', 'text': ''}
        tail = root
        for i in range(1, 32):
            child = {'id': str(i), 'text': ''}
            tail['children'] = [child]
            tail = child
        self.assertEqual(len(build_mindmap_xml({'root': root})), 32)
        tail['children'] = [{'id': '33', 'text': ''}]
        with self.assertRaises(ValueError):
            build_mindmap_xml({'root': root})
        payload = {'root': {'id': 'root', 'text': '', 'children': [
            {'id': str(i), 'text': ''} for i in range(999)]}}
        self.assertEqual(len(build_mindmap_xml(payload)), 1000)
        payload['root']['children'].append({'id': '1000', 'text': ''})
        with self.assertRaises(ValueError):
            build_mindmap_xml(payload)

    def test_controls_and_label_limits(self):
        for value in ['bad'+chr(i) for i in range(32) if chr(i) not in '\t\r\n'] + ['x'*10001, '\ud800', '\ufffe']:
            for builder, payload in ((build_mindmap_xml, {'root': {'id': 'r', 'text': value}}),
                                     (build_diagram_shape_xml, {'nodes': [dict(id='a', position={'x': 0, 'y': 0}, data={'label': value})]}),
                                     (build_table_sketch_xml, {**sketch(), 'texts': [dict(x=0, y=0, text=value)]})):
                with self.subTest(builder=builder.__name__, value=repr(value[:10])), self.assertRaises(ValueError):
                    builder(payload)
        for value in ('<&\t\n\r한글', 'x'*10000):
            p = build_mindmap_xml({'root': {'id': 'r', 'text': value}})[0]
            restored = ET.fromstring(ET.tostring(p))
            self.assertEqual(''.join(restored.itertext()), '1\t'+value.replace('\r', '\n'))

    def test_builders_do_not_write_and_preserve_inputs(self):
        for builder, payload in ((build_table_sketch_xml, sketch()), (build_diagram_shape_xml, graph()),
                                 (build_mindmap_xml, tree())):
            original = copy.deepcopy(payload)
            with patch('builtins.open', side_effect=AssertionError('file IO')):
                builder(payload)
            self.assertEqual(payload, original)


if __name__ == '__main__':
    unittest.main()
