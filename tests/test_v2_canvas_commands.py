import unittest
from concurrent.futures import ThreadPoolExecutor

from docfit_core.session import CommandBus, DocumentSession, RevisionConflict
from docfit_core.session.canvas_commands import (
    InsertDiagramShapeCommand, InsertMindmapTreeCommand, InsertTableSketchCommand,
)


def tree(text='root'):
    return {'root': {'id': 'root', 'text': text, 'children': [{'id': 'child', 'text': 'child'}]}}


class CanvasCommandsTests(unittest.TestCase):
    def setUp(self):
        self.session = DocumentSession('doc', 'hash', 'unused.hwpx', {'opaque': {'keep': [1]}})
        self.bus = CommandBus(self.session)

    def execute(self, command):
        return self.bus.execute(command, expected_revision=self.session.revision)

    def test_table_layout(self):
        payload = {'grid': {'cols': 1, 'rows': 1}, 'lines': [
            dict(x1=a, y1=b, x2=c, y2=d) for a,b,c,d in
            [(0,0,1,0), (1,0,1,1), (1,1,0,1), (0,1,0,0)]]}
        self.execute(InsertTableSketchCommand('table', payload))
        content = self.session.state['document']['blocks'][0]['content']
        self.assertEqual(content['target'], 'hp:tbl')
        self.assertEqual(len(content['layout']['cells']), 1)

    def test_graph_and_connector(self):
        nodes = [dict(id=n, position={'x': i*100, 'y': 0}, data={'label': '<&한글'})
                 for i,n in enumerate(['a', 'b'])]
        self.execute(InsertDiagramShapeCommand('graph', dict(nodes=nodes, edges=[
            dict(id='edge', source='a', target='b')])))
        content = self.session.state['document']['blocks'][0]['content']
        self.assertEqual(content['connectors'][0]['target_element'], 'hp:connectLine')
        self.assertEqual(content['shapes'][0]['text'], '<&한글')

    def test_mindmap_modes(self):
        for mode in ('outline', 'summary_table'):
            self.execute(InsertMindmapTreeCommand(mode, {**tree(), 'mode': mode}))
        blocks = self.session.state['document']['blocks']
        self.assertEqual(blocks[0]['content']['paragraphs'][1]['number'], '1.1')
        self.assertEqual(blocks[1]['content']['target'], 'hp:tbl')

    def test_undo_redo_and_defensive_payload(self):
        payload = tree()
        command = InsertMindmapTreeCommand('one', payload)
        payload['root']['text'] = 'changed'
        self.execute(command)
        after = self.session.state
        self.assertEqual(after['document']['blocks'][0]['content']['paragraphs'][0]['text'], 'root')
        self.bus.undo(expected_revision=1)
        self.assertEqual(self.session.state, {'opaque': {'keep': [1]}})
        self.assertFalse(self.session.dirty)
        self.bus.redo(expected_revision=2)
        self.assertEqual(self.session.state, after)

    def test_anchor_and_duplicate_rollback(self):
        self.execute(InsertMindmapTreeCommand('a', tree()))
        self.execute(InsertMindmapTreeCommand('b', tree()))
        self.execute(InsertMindmapTreeCommand('c', tree(), after_id='a'))
        self.assertEqual([b['id'] for b in self.session.state['document']['blocks']], ['a','c','b'])
        before = self.session.snapshot()
        for command in (InsertMindmapTreeCommand('a', tree()),
                        InsertMindmapTreeCommand('d', tree(), after_id='missing')):
            with self.assertRaises(ValueError):
                self.execute(command)
            self.assertEqual(self.session.snapshot(), before)

    def test_batch_failure_preserves_redo(self):
        self.execute(InsertMindmapTreeCommand('a', tree()))
        self.bus.undo(expected_revision=1)
        with self.assertRaises(ValueError):
            self.bus.execute_batch([InsertMindmapTreeCommand('a', tree()),
                                    InsertTableSketchCommand('bad', {'grid': {'cols': 1, 'rows': 1}})],
                                   expected_revision=2)
        self.assertEqual(self.session.revision, 2)
        self.assertTrue(self.bus.history.can_redo)
        self.assertNotIn('document', self.session.state)

    def test_invalid_payloads_leave_session_unchanged(self):
        invalid = [InsertDiagramShapeCommand('g', {'nodes': [dict(id='a', position={'x': 0, 'y': 0})],
                                                 'edges': [dict(id='e', source='a', target='missing')]}),
                   InsertMindmapTreeCommand('m', {'root': {'id': 'r', 'text': 'x', 'children': [
                       {'id': 'r', 'text': 'duplicate'}]}})]
        for command in invalid:
            with self.assertRaises(ValueError):
                self.execute(command)
            self.assertEqual(self.session.revision, 0)
        with self.assertRaises(ValueError):
            InsertMindmapTreeCommand('nan', {'bad': float('nan')})

    def test_concurrent_revision_has_one_winner(self):
        def run(ident):
            try:
                self.bus.execute(InsertMindmapTreeCommand(ident, tree()), expected_revision=0)
                return 'ok'
            except RevisionConflict:
                return 'conflict'
        with ThreadPoolExecutor(2) as pool:
            self.assertCountEqual(list(pool.map(run, ['a', 'b'])), ['ok', 'conflict'])


if __name__ == '__main__':
    unittest.main()
