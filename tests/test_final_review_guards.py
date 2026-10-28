"""Reproductions for final review F1–F5: aliases, close, analysis and races."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
import os
import runpy
import json
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from desktop_web_ui import DesktopWebBridge
from docfit_app.api_contract import ServiceError
from docfit_app.flow_service import FlowService
from docfit_app.settings_service import SettingsService
from docfit_core.fidelity.package import PackageSnapshot, copy_exact, write_package
from docfit_core import kordoc_runtime as kr
from test_fidelity import make_hwpx
from test_offline_runtime import make_pack, VERSION


class PublicationTests(unittest.TestCase):
    def test_old_fixed_temporary_alias_never_modifies_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source.hwpx', Path(folder)/'result.hwpx'
            make_hwpx(source)
            original = source.read_bytes()
            os.link(source, Path(str(target)+'.tmp'))
            write_package(PackageSnapshot.load(source), {'Preview/PrvText.txt': b'changed'}, target)
            self.assertEqual(source.read_bytes(), original)
            self.assertNotEqual(target.read_bytes(), original)

    def test_existing_hardlink_or_symlink_target_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'source.hwpx'
            make_hwpx(source)
            original = source.read_bytes()
            for kind in ('hard', 'symbolic'):
                target = Path(folder)/kind
                if kind == 'hard':
                    os.link(source, target)
                else:
                    try:
                        target.symlink_to(source)
                    except OSError:
                        continue
                for writer in (lambda: copy_exact(source, target),
                               lambda: write_package(PackageSnapshot.load(source), {}, target)):
                    with self.assertRaises((FileExistsError, ValueError)):
                        writer()
                self.assertEqual(source.read_bytes(), original)

    def test_concurrent_publish_has_exactly_one_winner_and_no_private_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source', Path(folder)/'result'
            source.write_bytes(b'original')
            barrier = threading.Barrier(2)
            def write():
                barrier.wait(timeout=3)
                try:
                    copy_exact(source, target)
                    return True
                except FileExistsError:
                    return False
            with ThreadPoolExecutor(2) as pool:
                results = list(pool.map(lambda _: write(), range(2)))
            self.assertEqual(sorted(results), [False, True])
            self.assertEqual(target.read_bytes(), b'original')
            self.assertEqual(list(Path(folder).glob('.docfit-*')), [])

    def test_publication_failure_cleans_only_its_own_temporary(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder)/'source', Path(folder)/'result'
            source.write_bytes(b'original')
            with patch('docfit_core.fidelity.package.os.link', side_effect=OSError('denied')):
                with self.assertRaises(OSError):
                    copy_exact(source, target)
            self.assertEqual(list(Path(folder).iterdir()), [source])


class DiagramRevisionTests(unittest.TestCase):
    def test_delete_serializes_with_save_instead_of_resurrecting_document(self):
        with tempfile.TemporaryDirectory() as folder:
            store = SettingsService(Path(folder)/'settings.json')
            a, b = FlowService(folder, store), FlowService(folder, store)
            snapshot = {'format': 'docfit-flow', 'version': 1, 'nodes': [], 'edges': []}
            identity = 'a'*32
            first = a.save(identity, 'initial', snapshot)
            entered, release, deleting = threading.Event(), threading.Event(), threading.Event()
            original_save, original_path = a._save_locked, b._document_path
            def hold_save(*args):
                entered.set()
                if not release.wait(3):
                    raise AssertionError('test did not release writer')
                return original_save(*args)
            def path(*args):
                deleting.set()
                return original_path(*args)
            with patch.object(a, '_save_locked', side_effect=hold_save), patch.object(b, '_document_path', side_effect=path):
                with ThreadPoolExecutor(2) as pool:
                    writer = pool.submit(a.save, identity, 'updated', snapshot, first['revision'])
                    try:
                        self.assertTrue(entered.wait(3))
                        deleter = pool.submit(b.delete, identity)
                        self.assertTrue(deleting.wait(3))
                        with self.assertRaises(TimeoutError):
                            deleter.result(timeout=0.1)
                    finally:
                        release.set()
                    writer.result(timeout=3)
                    deleter.result(timeout=3)
            self.assertEqual(a.list(), [])

    def test_independent_processes_using_one_revision_have_one_winner(self):
        with tempfile.TemporaryDirectory() as folder:
            store = SettingsService(Path(folder)/'settings.json')
            service = FlowService(folder, store)
            identity = 'a'*32
            snapshot = {'format': 'docfit-flow', 'version': 1, 'nodes': [], 'edges': []}
            first = service.save(identity, 'initial', snapshot)
            code = '''
import json, sys
from pathlib import Path
from docfit_app.flow_service import FlowService
from docfit_app.settings_service import SettingsService
from docfit_app.api_contract import ServiceError
cfg = json.loads(sys.stdin.readline())
service = FlowService(cfg['folder'], SettingsService(Path(cfg['folder'])/'settings.json'))
try:
    result = service.save(cfg['id'], cfg['name'], cfg['snapshot'], cfg['revision'])
except ServiceError as exc:
    result = {'error': exc.code}
print(json.dumps(result))
'''
            children = [subprocess.Popen([sys.executable, '-c', code], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
                        for _ in range(2)]
            try:
                for index, child in enumerate(children):
                    child.stdin.write(json.dumps({'folder': folder, 'id': identity, 'name': str(index),
                                                  'snapshot': snapshot, 'revision': first['revision']})+'\n')
                    child.stdin.flush()
                results = []
                for child in children:
                    output, error = child.communicate(timeout=10)
                    self.assertEqual(child.returncode, 0, error)
                    results.append(json.loads(output))
                winner = next(r for r in results if 'revision' in r)
                self.assertIn({'error': 'DIAGRAM_CONFLICT'}, results)
                self.assertEqual(service.load(identity)['revision'], winner['revision'])
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()
                        child.communicate()

    def test_two_editors_cannot_claim_each_others_revision(self):
        for service_type in (FlowService,):
            with self.subTest(service=service_type), tempfile.TemporaryDirectory() as folder:
                store = SettingsService(Path(folder)/'settings.json')
                store.update(lambda s: s.update(developer_mode=True, diagram_editor_enabled=True))
                a, b = service_type(folder, store), service_type(folder, store)
                identity = 'a'*32
                snapshot = {'format': 'docfit-flow', 'version': 1, 'nodes': [], 'edges': []}
                first = a.save(identity, 'initial', snapshot)
                barrier = threading.Barrier(2)
                def save(service, name):
                    barrier.wait(timeout=3)
                    try:
                        return service.save(identity, name, snapshot, first['revision'])
                    except ServiceError as exc:
                        return exc.code
                with ThreadPoolExecutor(2) as pool:
                    futures = [pool.submit(save, a, 'A'), pool.submit(save, b, 'B')]
                    results = [f.result(timeout=5) for f in futures]
                winner = next(r for r in results if isinstance(r, dict))
                self.assertIn('DIAGRAM_CONFLICT', results)
                latest = a.load(identity)
                self.assertEqual((latest['name'], latest['revision']), (winner['name'], winner['revision']))
                for revision in (None, first['revision']):
                    with self.assertRaises(ServiceError) as caught:
                        a.save(identity, 'stale', snapshot, revision)
                    self.assertEqual(caught.exception.code, 'DIAGRAM_CONFLICT')
                copied = b.save('b'*32, 'recovered copy', snapshot)
                self.assertNotEqual(copied['id'], identity)
                self.assertEqual(a.load(identity)['revision'], winner['revision'])


class HostCloseTests(unittest.TestCase):
    def make_bridge(self):
        root = SimpleNamespace(winfo_exists=lambda: True)
        gui = SimpleNamespace(root=root, running=False, closing=False, 종료=Mock())
        bridge = DesktopWebBridge(gui)
        bridge._tk = lambda fn, **kw: fn()
        bridge.enable_close_guard()
        return bridge, gui

    def test_os_close_is_vetoed_and_rejected_close_keeps_app(self):
        bridge, gui = self.make_bridge()
        self.assertFalse(bridge.request_close())
        pending = bridge.get_pending_dialog()
        self.assertEqual(pending['kind'], 'app_close')
        # A second native close while the request is pending force-closes (2.0.1);
        # that path is covered by test_desktop_close_watchdog.
        gui.종료.assert_not_called()
        self.assertFalse(bridge.resolve_dialog(pending['id'], False)['accepted'])
        self.assertIsNone(bridge.get_pending_dialog())
        gui.종료.assert_not_called()

    def test_accepted_close_uses_watcher_after_original_os_veto(self):
        bridge, gui = self.make_bridge()
        gui.종료.side_effect = lambda: setattr(gui, 'closing', True)
        self.assertFalse(bridge.request_close())
        pending = bridge.get_pending_dialog()
        self.assertTrue(bridge.resolve_dialog(pending['id'], True)['accepted'])
        gui.종료.assert_called_once()
        self.assertFalse(bridge.user_closing)  # watcher must destroy the vetoed host


class DesignTableFailClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path('hwp-auto-docfit.py', run_name='guard_tests')

    def test_failed_snapshot_aborts_before_modification(self):
        fn = self.ns['서식표_보호영역_조사']
        with patch.dict(fn.__globals__, {'_제목_임시hwpx_저장': Mock(side_effect=OSError('COM failed'))}):
            for decorative_only in (True, False):
                with self.subTest(decorative_only=decorative_only), self.assertRaisesRegex(RuntimeError, '문서 수정을 중단'):
                    fn(장식만=decorative_only)

    def test_mismatched_cell_aborts_instead_of_returning_empty_protection(self):
        fn = self.ns['서식표_보호영역_조사']
        doc = Mock()
        doc.GetPos.return_value = (99, 0, 0)
        with tempfile.TemporaryDirectory() as folder, patch.dict(fn.__globals__, {
            'tempfile': Mock(mkdtemp=lambda **kw: folder), 'hwp': doc,
            '_제목_임시hwpx_저장': lambda path: path,
            '서식표_영역_목록': lambda *a, **kw: [([2, 3], (2, 0, 'title'))],
            'hwp_run': Mock(),
        }):
            for decorative_only in (True, False):
                with self.subTest(decorative_only=decorative_only), self.assertRaisesRegex(RuntimeError, '칸 위치가 일치하지 않아'):
                    fn(장식만=decorative_only)


class ConcurrentRuntimeInstallTests(unittest.TestCase):
    def test_two_first_installers_reuse_winner_without_deleting_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            pack = make_pack(folder/'pack.zip')
            barrier = threading.Barrier(2)
            def install():
                barrier.wait(timeout=3)
                return kr.install_pack(pack, VERSION, folder/'installed')
            original_replace = kr.os.replace
            published = []
            def publish(source, target):
                published.append(target)
                return original_replace(source, target)
            with patch.object(kr.os, 'replace', side_effect=publish), patch.object(kr.shutil, 'rmtree', wraps=kr.shutil.rmtree) as remove:
                with ThreadPoolExecutor(2) as pool:
                    results = list(pool.map(lambda _: install(), range(2)))
                self.assertEqual(results[0], results[1])
                self.assertEqual(len(published), 1)
                remove.assert_not_called()
                self.assertIsNotNone(kr.runtime_in(results[0], VERSION))
            self.assertFalse(list((folder/'installed').glob('.installing-*')))

    def test_failed_install_releases_lock_for_valid_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            bad = make_pack(folder/'bad.zip', node=False)
            with self.assertRaises(kr.RuntimePackError):
                kr.install_pack(bad, VERSION, folder/'installed')
            good = make_pack(folder/'good.zip')
            installed = kr.install_pack(good, VERSION, folder/'installed')
            self.assertIsNotNone(kr.runtime_in(installed, VERSION))
            self.assertFalse(list((folder/'installed').glob('.installing-*')))
