"""Executable integration contracts for workspace adapter authors."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from docfit_core.session import (
    CommandBus, DocumentSession, HistoryService, RevisionConflict,
    StyleDefinition, StyleResolver,
)


class SetValue:
    def __init__(self, value):
        self.value = value

    def apply(self, draft):
        draft['value'] = self.value
        self.draft = draft


class Fail:
    def apply(self, draft):
        draft['nested']['items'].append('bad')
        raise ValueError('failed')


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.session = DocumentSession('doc', 'hash', 'copy.hwpx',
                                       {'value': 0, 'nested': {'items': []}})
        self.bus = CommandBus(self.session)

    def test_initial_identity_and_defensive_state(self):
        self.assertEqual(self.session.document_id, 'doc')
        self.assertEqual(self.session.original_hash, 'hash')
        self.assertTrue(self.session.working_copy_path.is_absolute())
        self.assertEqual(self.session.revision, 0)
        self.assertFalse(self.session.dirty)
        self.session.state['nested']['items'].append(1)
        self.assertEqual(self.session.state['nested']['items'], [])
        with self.assertRaises(AttributeError):
            self.session.revision = 10

    def test_open_preserves_original_and_refuses_overwrite(self):
        with TemporaryDirectory() as directory:
            original = Path(directory) / 'original.hwpx'
            working = Path(directory) / 'working.hwpx'
            original.write_bytes(b'original')
            session = DocumentSession.open(original, working)
            self.assertEqual(session.original_hash, sha256(b'original').hexdigest())
            self.assertEqual(working.read_bytes(), original.read_bytes())
            CommandBus(session).execute(SetValue(2), expected_revision=0)
            self.assertEqual(original.read_bytes(), b'original')
            with self.assertRaises(FileExistsError):
                DocumentSession.open(original, working)
            with self.assertRaises(ValueError):
                DocumentSession.open(original, original)

    def test_invalid_identity(self):
        for identity, digest in [('', 'hash'), ('id', '')]:
            with self.assertRaises(ValueError):
                DocumentSession(identity, digest, 'copy')
        with self.assertRaises(TypeError):
            DocumentSession('id', 'hash', 'copy', [])

    def test_save_snapshot_rejects_intervening_edit(self):
        revision, model = self.session.snapshot()
        model['nested']['items'].append('external')
        self.bus.execute(SetValue(1), expected_revision=revision)
        with self.assertRaises(RevisionConflict):
            self.session.mark_saved(expected_revision=revision)
        self.assertTrue(self.session.dirty)
        self.assertEqual(self.session.state['nested']['items'], [])

    def test_execute_undo_redo_and_dirty(self):
        self.assertEqual(self.bus.execute(SetValue(1), expected_revision=0), 1)
        self.assertTrue(self.session.dirty)
        self.assertEqual(self.bus.undo(expected_revision=1), 2)
        self.assertFalse(self.session.dirty)
        self.assertEqual(self.bus.redo(expected_revision=2), 3)
        self.assertEqual(self.session.state['value'], 1)
        self.session.mark_saved(expected_revision=3)
        self.assertFalse(self.session.dirty)
        self.bus.undo(expected_revision=3)
        self.assertTrue(self.session.dirty)
        self.bus.redo(expected_revision=4)
        self.assertFalse(self.session.dirty)

    def test_atomic_batch_failure_and_redo_preserved(self):
        self.bus.execute(SetValue(1), expected_revision=0)
        self.bus.undo(expected_revision=1)
        with self.assertRaises(ValueError):
            self.bus.execute_batch([SetValue(2), Fail()], expected_revision=2)
        self.assertEqual(self.session.state, {'value': 0, 'nested': {'items': []}})
        self.assertEqual(self.session.revision, 2)
        self.assertFalse(self.session.dirty)
        self.assertEqual(self.bus.history.redo_count, 1)
        self.bus.redo(expected_revision=2)

    def test_batch_is_single_history_entry(self):
        self.bus.execute_batch([SetValue(1), SetValue(2)], expected_revision=0)
        self.assertEqual(self.bus.history.undo_count, 1)
        self.assertEqual(self.session.state['value'], 2)
        self.bus.undo(expected_revision=1)
        self.assertEqual(self.session.state['value'], 0)

    def test_new_edit_clears_redo(self):
        self.bus.execute(SetValue(1), expected_revision=0)
        self.bus.undo(expected_revision=1)
        self.bus.execute(SetValue(2), expected_revision=2)
        self.assertFalse(self.bus.history.can_redo)
        with self.assertRaises(IndexError):
            self.bus.redo(expected_revision=3)

    def test_revision_conflicts_on_all_operations(self):
        self.bus.execute(SetValue(1), expected_revision=0)
        for operation in [lambda: self.bus.execute(SetValue(2), expected_revision=0),
                          lambda: self.bus.undo(expected_revision=0),
                          lambda: self.bus.redo(expected_revision=0),
                          lambda: self.session.mark_saved(expected_revision=0)]:
            with self.assertRaises(RevisionConflict):
                operation()
        self.assertEqual(self.session.revision, 1)
        self.assertEqual(self.bus.history.undo_count, 1)

    def test_retained_command_reference_is_detached(self):
        command = SetValue(1)
        self.bus.execute(command, expected_revision=0)
        command.draft['value'] = 99
        self.assertEqual(self.session.state['value'], 1)
        self.bus.undo(expected_revision=1)
        self.bus.redo(expected_revision=2)
        self.assertEqual(self.session.state['value'], 1)

    def test_empty_history_and_batch(self):
        for operation in [lambda: self.bus.undo(expected_revision=0),
                          lambda: self.bus.redo(expected_revision=0)]:
            with self.assertRaises(IndexError):
                operation()
        with self.assertRaises(ValueError):
            self.bus.execute_batch([], expected_revision=0)
        self.assertEqual(self.session.revision, 0)

    def test_nested_execution_rejected_and_rolled_back(self):
        bus = self.bus

        class Nested:
            def apply(self, draft):
                bus.execute(SetValue(3), expected_revision=0)

        with self.assertRaises(RuntimeError):
            bus.execute(Nested(), expected_revision=0)
        self.assertEqual(self.session.revision, 0)
        self.assertFalse(bus.history.can_undo)

    def test_divergent_bus_and_history_reuse_rejected(self):
        other = CommandBus(self.session)
        self.bus.execute(SetValue(1), expected_revision=0)
        with self.assertRaises(RevisionConflict):
            other.execute(SetValue(2), expected_revision=1)
        with self.assertRaises(ValueError):
            CommandBus(self.session, self.bus.history)

    def test_concurrent_same_revision_has_one_winner(self):
        def run(value):
            try:
                self.bus.execute(SetValue(value), expected_revision=0)
                return 'ok'
            except RevisionConflict:
                return 'conflict'

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, [1, 2]))
        self.assertCountEqual(results, ['ok', 'conflict'])
        self.assertEqual(self.session.revision, 1)


class StyleTests(unittest.TestCase):
    def test_all_six_precedence_levels_and_sources(self):
        names = ['app_defaults', 'agency_profile', 'document_theme',
                 'parent_style:body', 'table_role_conditions:0', 'direct_formatting']
        layers = [{str(key): index for key in range(index, 6)}
                  for index in range(6)]
        resolver = StyleResolver(layers[0], {'body': StyleDefinition(layers[3])})
        result = resolver.resolve(agency_profile=layers[1], document_theme=layers[2],
                                  parent_style='body', table_role_conditions=[layers[4]],
                                  direct_formatting=layers[5])
        for index in range(6):
            self.assertEqual(result.properties[str(index)], index)
            self.assertEqual(result.sources[str(index)], names[index])

    def test_parent_chain_and_role_order(self):
        resolver = StyleResolver(styles={
            'root': StyleDefinition({'font': 'A', 'bold': True}),
            'child': StyleDefinition({'font': 'B'}, 'root'),
        })
        result = resolver.resolve(parent_style='child', table_role_conditions=[
            {'fill': 'band'}, {'fill': 'header'}, {'fill': 'total'}])
        self.assertEqual(result.properties, {'font': 'B', 'bold': True, 'fill': 'total'})

    def test_explicit_clear_false_zero(self):
        result = StyleResolver({'bold': True, 'spacing': 10, 'color': 'red'}).resolve(
            direct_formatting={'bold': False, 'spacing': 0, 'color': None})
        self.assertEqual(result.properties, {'bold': False, 'spacing': 0, 'color': None})

    def test_cycles_and_missing_parent(self):
        for styles in [
            {'a': StyleDefinition({}, 'a')},
            {'a': StyleDefinition({}, 'b'), 'b': StyleDefinition({}, 'a')},
        ]:
            with self.assertRaises(ValueError):
                StyleResolver(styles=styles).resolve(parent_style='a')
        with self.assertRaises(KeyError):
            StyleResolver(styles={'a': StyleDefinition({}, 'missing')}).resolve(
                parent_style='a')

    def test_no_mutation_or_shared_results(self):
        defaults = {'custom': [1]}
        resolver = StyleResolver(defaults)
        defaults['custom'].append(2)
        result = resolver.resolve()
        result.properties['custom'].append(3)
        self.assertEqual(resolver.resolve().properties, {'custom': [1]})
        self.assertEqual(StyleResolver().resolve().properties, {})


if __name__ == '__main__':
    unittest.main()
