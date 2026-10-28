"""작업 규약 시험: 실제 한/글·원본 문서·프로세스 종료 없이 검증한다."""
import json
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from docfit_app.api_contract import ServiceError
from docfit_app.jobs import JobManager, legacy_event


class JobsTests(unittest.TestCase):
    def manager(self, **kwargs):
        manager = JobManager(**kwargs)
        self.addCleanup(lambda: manager.shutdown(timeout=.1))
        return manager

    def wait(self, manager, identifier):
        manager._jobs[identifier]['thread'].join(3)
        self.assertFalse(manager._jobs[identifier]['thread'].is_alive())
        return manager.status(identifier)

    def test_order_result_and_immutable_snapshots(self):
        manager = self.manager()
        def runner(report, cancelled):
            report('progress', {'file':1, 'total':1, 'percent':20, 'stage':'read'})
            report('item_done', {'source':'a', 'output':'b'})
            return {'count':1}
        identifier = manager.start('format', {}, runner)
        self.assertEqual(self.wait(manager, identifier)['state'], 'done')
        events = manager.events()['events']
        self.assertEqual([e['type'] for e in events], ['started', 'progress', 'item_done', 'done'])
        self.assertEqual([e['seq'] for e in events], [1, 2, 3, 4])
        json.dumps(events)
        events[1]['data']['stage'] = 'changed'
        self.assertEqual(manager.events()['events'][1]['data']['stage'], 'read')
        state = manager.status(identifier)
        state['progress']['percent'] = -5
        self.assertEqual(manager.status(identifier)['progress']['percent'], 100)

    def test_cooperative_cancel_waits_for_safe_point(self):
        manager = self.manager(cancel_timeout=5)
        entered, safe = threading.Event(), threading.Event()
        self.addCleanup(safe.set)
        def runner(report, cancelled):
            entered.set()
            safe.wait(3)
            self.assertTrue(cancelled())
        identifier = manager.start('spacing', {}, runner)
        self.assertTrue(entered.wait(2))
        manager.cancel(identifier)
        manager.cancel(identifier)
        self.assertEqual(manager.status(identifier)['state'], 'running')
        safe.set()
        self.assertEqual(self.wait(manager, identifier)['state'], 'cancelled')
        self.assertEqual([e['type'] for e in manager.events()['events']].count('cancelled'), 1)

    def test_timeout_cleanup_keeps_busy_until_worker_exits(self):
        cleanup_called, release, entered = threading.Event(), threading.Event(), threading.Event()
        self.addCleanup(release.set)
        manager = self.manager(cancel_timeout=.02, cleanup=lambda: cleanup_called.set())
        def runner(report, cancelled):
            entered.set()
            release.wait(3)
        identifier = manager.start('format', {}, runner)
        self.assertTrue(entered.wait(2))
        manager.cancel(identifier)
        self.assertTrue(cleanup_called.wait(2))
        with self.assertRaises(ServiceError) as error:
            manager.start('table_copy', {}, lambda report, cancelled: None)
        self.assertEqual(error.exception.code, 'JOB_RUNNING')
        self.assertEqual(manager.status(identifier)['state'], 'running')
        release.set()
        self.assertEqual(self.wait(manager, identifier)['state'], 'cancelled')

    def test_timeout_uses_owned_process_cleanup(self):
        manager = self.manager()
        identifier = manager.begin('format')
        with patch('docfit_core.hwp_process.kill_owned', return_value=[42]) as cleanup:
            manager._timeout(identifier)
        cleanup.assert_called_once_with()
        self.assertEqual(manager.events()['events'][0]['data']['owned_pids'], [42])
        manager.report(identifier, 'cancelled', {})

    def test_ring_overflow_batch_and_gap(self):
        manager = self.manager()
        identifier = manager.begin('format')
        for n in range(2100):
            manager.report(identifier, 'log', {'n':n})
        batch = manager.events(0)
        self.assertTrue(batch['gap'])
        self.assertEqual(batch['oldest_seq'], 101)
        self.assertEqual(len(batch['events']), 200)
        self.assertEqual(batch['next_seq'], 300)
        tail = manager.events(2000)
        self.assertEqual(len(tail['events']), 100)
        self.assertFalse(tail['gap'])
        self.assertEqual(manager.events(2100)['events'], [])
        manager.report(identifier, 'done', {})

    def test_concurrent_report_seq_and_light_jobs(self):
        manager = self.manager()
        identifier = manager.begin('format')
        light = manager.start('preview', {}, lambda report, cancelled: None)
        self.wait(manager, light)
        threads = [threading.Thread(target=lambda: [manager.report(identifier, 'log', {}) for _ in range(100)]) for _ in range(4)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        seq = [e['seq'] for e in manager.events()['events']]
        self.assertEqual(seq, list(range(1, 201)))
        self.assertEqual(manager.events()['latest_seq'], 402)
        manager.report(identifier, 'done', {})

    def test_failure_and_no_events_after_terminal(self):
        manager = self.manager()
        def runner(report, cancelled):
            raise ServiceError('HWP_FAILED', 'mock error')
        identifier = manager.start('format', {}, runner)
        self.assertEqual(self.wait(manager, identifier)['state'], 'failed')
        manager.report(identifier, 'done', {})
        self.assertEqual(manager.events()['events'][-1]['data']['code'], 'HWP_FAILED')
        self.assertEqual(len(manager.events()['events']), 2)

    def test_validation(self):
        manager = self.manager()
        for args in [(True, 200), (-1, 200), (0, 201), (0, 0)]:
            with self.assertRaises(ServiceError): manager.events(*args)
        with self.assertRaises(ServiceError): manager.cancel('missing')

    def test_restart_marks_orphans_and_clears_journal(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'jobs.json'
            first = JobManager(state_path=path)
            identifier = first.begin('file_format')
            second = JobManager(state_path=path)
            self.assertEqual(second.status(identifier)['state'], 'failed')
            self.assertEqual(second.events()['events'][0]['data']['code'], 'ORPHANED_JOB')
            self.assertEqual(json.loads(path.read_text()), [])

    def test_shutdown_cancels_and_rejects_new_jobs(self):
        manager = self.manager()
        identifier = manager.start('format', {}, lambda report, cancelled: None)
        self.wait(manager, identifier)
        manager.shutdown()
        with self.assertRaises(ServiceError) as error:
            manager.begin('format')
        self.assertEqual(error.exception.code, 'BACKEND_CLOSING')

    def test_legacy_adapter(self):
        manager = self.manager()
        identifier = manager.begin('unify')
        manager.report(identifier, 'started', {})
        for item in [('doc_begin', 1, 2, 'a.hwpx'), ('step', 'save'),
                     ('saved', 'a', 'b', None), ('document_error', 'c', 'bad'),
                     ('style_unify_profile_review', {'done':threading.Event()}), ('finished', 1, 1)]:
            legacy_event(manager, identifier, item)
        batch = manager.events()['events']
        self.assertIn('dialog', [e['type'] for e in batch])
        self.assertEqual(manager.status(identifier)['state'], 'done')
        json.dumps(batch)

    def test_conversion_job_runs_cleanup_before_terminal(self):
        from docfit_app.conversion_runner import start_conversion_job
        manager = self.manager()
        def conversion(files, target, output_dir, progress, stop_event, **kwargs):
            progress(('doc_begin', 1, 1, 'a'))
            progress(('saved', 'a', 'b', None))
            progress(('file_conversion_finished', 1, 0))
            self.assertNotIn('done', [e['type'] for e in manager.events()['events']])
            return [{'output':'b'}]
        with patch('docfit_app.conversion_runner.run_conversion', side_effect=conversion):
            identifier = start_conversion_job(manager, ['a'], 'pdf')
            self.assertEqual(self.wait(manager, identifier)['state'], 'done')
        self.assertEqual(manager.events()['events'][-1]['type'], 'done')

    def test_native_job_dispatch(self):
        from docfit_app.application_service import ApplicationService
        with tempfile.TemporaryDirectory() as folder:
            service = ApplicationService(Path(folder) / 'settings.json')
            with patch('docfit_app.conversion_runner.run_conversion', return_value=[]):
                identifier = service.dispatch('start_job', ['file_format', {'files':[], 'target':'pdf'}])
                self.wait(service.jobs, identifier)
            self.assertEqual(service.state()['job']['id'], identifier)
            self.assertTrue(service.dispatch('get_events', [0])['events'])
            self.assertEqual(service.dispatch('cancel_job', [identifier])['state'], 'done')

    def test_browser_exposes_job_api(self):
        from desktop_web_ui import DesktopWebBridge, _BrowserApi
        bridge = DesktopWebBridge(SimpleNamespace())
        bridge.gui._job_manager = self.manager()
        api = _BrowserApi(bridge)
        self.assertTrue(callable(api.start_job))
        self.assertEqual(api.get_events(0)['events'], [])

    def test_table_copy_job_balances_com_and_reports_result(self):
        from docfit_app.table_units_service import TableUnitsService
        manager = self.manager()
        service = TableUnitsService()
        service.command = Mock(return_value={'copied':True})
        com = SimpleNamespace(CoInitialize=Mock(), CoUninitialize=Mock())
        with patch.dict('sys.modules', {'pythoncom':com}):
            identifier = service.start_copy_job(manager, {'id':'table'})
            self.assertEqual(self.wait(manager, identifier)['state'], 'done')
        com.CoInitialize.assert_called_once()
        com.CoUninitialize.assert_called_once()
        service.command.assert_called_once_with('copy', {'id':'table'})
        self.assertEqual([e['type'] for e in manager.events()['events']], ['started', 'item_done', 'done'])

    def test_bridge_cancel_and_busy_start_without_nested_tk_dispatch(self):
        from desktop_web_ui import DesktopWebBridge
        manager = self.manager()
        gui = SimpleNamespace(_job_manager=manager, running=True, 작업중단=Mock())
        identifier = manager.begin('spacing')
        manager.report(identifier, 'started', {})
        gui._job_id = identifier
        bridge = DesktopWebBridge(gui)
        bridge._tk = lambda callback, **kwargs: callback()
        with self.assertRaises(ServiceError) as error:
            bridge.start_job('spacing')
        self.assertEqual(error.exception.code, 'JOB_RUNNING')
        self.assertTrue(bridge.cancel_job(identifier)['cancel_requested'])
        gui.작업중단.assert_called_once()
        manager.report(identifier, 'cancelled', {})

    def test_inline_copy_uses_same_slot_and_preserves_return(self):
        manager = self.manager()
        self.assertEqual(manager.run_inline('table_copy', {}, lambda report, cancelled: {'copied':True}), {'copied':True})
        self.assertEqual(manager.latest()['state'], 'done')
        identifier = manager.begin('file_format')
        with self.assertRaises(ServiceError):
            manager.run_inline('table_copy', {}, lambda report, cancelled: None)
        manager.report(identifier, 'done', {})


if __name__ == '__main__':
    unittest.main()
