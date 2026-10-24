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


class JobsProtocolBoundaryTests(unittest.TestCase):
    def _manager(self, **kwargs):
        if 'cleanup' not in kwargs:
            kwargs['cleanup'] = Mock(return_value=[])
        manager = JobManager(**kwargs)
        self.addCleanup(manager.shutdown, timeout=0)
        return manager

    def test_cancel_after_terminal_is_idempotent(self):
        """취소 요청이 완료 뒤에 들어온 경우: done, failed, cancelled 상태에서 cancel은 무해하고 상태를 변경하지 않는다."""
        for terminal in ('done', 'failed', 'cancelled'):
            with self.subTest(terminal=terminal):
                cleanup = Mock(return_value=[])
                manager = self._manager(cleanup=cleanup)
                identifier = manager.begin('format', {})
                manager.report(identifier, 'started', {})
                manager.report(identifier, terminal, {'marker': terminal})
                before_state = manager.status(identifier)
                before_events = manager.events()
                self.assertEqual(before_state['state'], terminal)
                self.assertFalse(before_state['cancel_requested'])

                with patch('docfit_app.jobs.threading.Timer') as mock_timer:
                    ret1 = manager.cancel(identifier)
                    ret2 = manager.cancel(identifier)

                self.assertEqual(ret1, before_state)
                self.assertEqual(ret2, before_state)
                self.assertEqual(manager.status(identifier), before_state)
                self.assertFalse(manager.cancelled(identifier))
                self.assertEqual(manager.events(), before_events)
                mock_timer.assert_not_called()
                cleanup.assert_not_called()

    def test_duplicate_start_same_job_id_is_rejected(self):
        """같은 job_id 중복 시작: 이미 시작된 예약 job_id로 재차 start를 호출하면 거부되어야 한다 (P4-BUG-01)."""
        manager = self._manager()
        runner = Mock(return_value={'count': 1})
        identifier = manager.begin('format', {})
        thread_stub = Mock()
        thread_stub.is_alive.return_value = True

        with patch('docfit_app.jobs.threading.Thread', return_value=thread_stub) as mock_thread_cls:
            res_id = manager.start('format', {}, runner, job_id=identifier)
            self.assertEqual(res_id, identifier)
            manager.report(identifier, 'started', {})
            self.assertEqual(manager.thread(identifier), thread_stub)
            self.assertEqual(mock_thread_cls.call_count, 1)
            self.assertEqual(thread_stub.start.call_count, 1)
            before_state = manager.status(identifier)
            before_events = manager.events()

            try:
                with self.assertRaises(ServiceError) as ctx:
                    manager.start('format', {}, runner, job_id=identifier)
                self.assertEqual(ctx.exception.code, 'JOB_RUNNING')
                self.assertEqual(mock_thread_cls.call_count, 1)
                self.assertEqual(thread_stub.start.call_count, 1)
                self.assertEqual(manager.status(identifier), before_state)
                self.assertEqual(manager.events(), before_events)
                runner.assert_not_called()
            finally:
                thread_stub.is_alive.return_value = False
                manager.report(identifier, 'failed', {'code': 'TEST_CLEANUP'})

    def test_seq_monotonic_across_jobs_and_truncated_pages(self):
        """사건 순번(seq) 단조 증가: 복수 작업에 걸쳐 seq가 1씩 증가하며, 버퍼 절단 후에도 페이지네이션 순서가 유지된다."""
        manager = self._manager(capacity=5)
        heavy = manager.begin('format', {})
        light = manager.begin('preview', {})

        manager.report(heavy, 'started', {})
        manager.report(light, 'started', {})
        manager.report(heavy, 'progress', {'percent': 10})
        manager.report(light, 'log', {'message': 'preview'})
        manager.report(light, 'done', {'result': {'ok': True}})
        manager.report(heavy, 'item_done', {'source': 'a', 'output': 'b'})
        manager.report(heavy, 'done', {'result': {'count': 1}})

        # 종료된 작업에 추가 report 시도 시 seq가 증가하지 않아야 함
        manager.report(heavy, 'progress', {'percent': 50})
        self.assertEqual(manager.events()['latest_seq'], 7)

        # capacity=5이므로 버퍼에는 seq [3, 4, 5, 6, 7]만 남음
        p1 = manager.events(0, max=2)
        self.assertEqual([e['seq'] for e in p1['events']], [3, 4])
        self.assertEqual(p1['oldest_seq'], 3)
        self.assertEqual(p1['latest_seq'], 7)
        self.assertEqual(p1['next_seq'], 4)
        self.assertTrue(p1['gap'])

        p2 = manager.events(4, max=2)
        self.assertEqual([e['seq'] for e in p2['events']], [5, 6])
        self.assertEqual(p2['next_seq'], 6)
        self.assertFalse(p2['gap'])

        p3 = manager.events(6, max=2)
        self.assertEqual([e['seq'] for e in p3['events']], [7])
        self.assertEqual(p3['next_seq'], 7)
        self.assertFalse(p3['gap'])

        p4 = manager.events(7, max=2)
        self.assertEqual(p4['events'], [])
        self.assertEqual(p4['next_seq'], 7)
        self.assertEqual(p4['latest_seq'], 7)
        self.assertFalse(p4['gap'])

        seen = [e['seq'] for p in (p1, p2, p3) for e in p['events']]
        self.assertEqual(seen, [3, 4, 5, 6, 7])
        self.assertTrue(all(seen[i] == seen[i-1] + 1 for i in range(1, len(seen))))

        all_events = p1['events'] + p2['events'] + p3['events']
        self.assertEqual([(e['job_id'], e['type']) for e in all_events], [
            (heavy, 'progress'),
            (light, 'log'),
            (light, 'done'),
            (heavy, 'item_done'),
            (heavy, 'done'),
        ])

        p_edge = manager.events(99, max=1)
        self.assertEqual(p_edge['events'], [])
        self.assertEqual(p_edge['next_seq'], 99)
        self.assertEqual(p_edge['latest_seq'], 7)

        self.assertEqual(manager.get_events(7, max=2), p4)

    def test_restart_recovers_multiple_orphans_only_once(self):
        """재시작 시 남은 작업 정리: 복수 작업의 ORPHANED_JOB 일괄 회수 및 활성 저널 정리, 반복 재시작 시 중복 발행 없음."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'jobs.json'
            records = [
                {'id': '00000000-0000-4000-8000-000000000001', 'kind': 'format'},
                {'id': '00000000-0000-4000-8000-000000000002', 'kind': 'preview'},
                {'id': '00000000-0000-4000-8000-000000000003', 'kind': 'catalog'},
            ]
            path.write_text(json.dumps(records), encoding='utf-8')
            cleanup = Mock(return_value=[])

            with patch('docfit_app.jobs.threading.Thread') as mock_t, \
                 patch('docfit_app.jobs.threading.Timer') as mock_timer, \
                 patch('docfit_core.hwp_process.kill_owned') as mock_kill:
                recovered = self._manager(state_path=path, cleanup=cleanup)

                for r in records:
                    st = recovered.status(r['id'])
                    self.assertEqual(st['state'], 'failed')
                    self.assertEqual(st['kind'], r['kind'])
                    self.assertFalse(st['cancel_requested'])
                    self.assertIsNone(recovered.thread(r['id']))

                events = recovered.events()['events']
                self.assertEqual(len(events), 3)
                self.assertEqual([e['seq'] for e in events], [1, 2, 3])
                self.assertEqual([e['job_id'] for e in events], [r['id'] for r in records])
                self.assertEqual([e['type'] for e in events], ['failed', 'failed', 'failed'])
                for e in events:
                    self.assertEqual(e['data']['code'], 'ORPHANED_JOB')
                    self.assertTrue(bool(e['data'].get('message')))

                self.assertEqual(json.loads(path.read_text(encoding='utf-8')), [])
                mock_t.assert_not_called()
                mock_timer.assert_not_called()
                cleanup.assert_not_called()
                mock_kill.assert_not_called()

                recovered.shutdown(timeout=0)

            fresh = self._manager(state_path=path, cleanup=cleanup)
            self.assertIsNone(fresh.latest())
            self.assertEqual(fresh.events()['events'], [])
            self.assertEqual(fresh.events()['latest_seq'], 0)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), [])

            new_id = fresh.begin('format', {})
            fresh.report(new_id, 'started', {})
            fresh.report(new_id, 'done', {})
            self.assertEqual([e['seq'] for e in fresh.events()['events']], [1, 2])
            fresh.shutdown(timeout=0)

    def test_begin_rejects_invalid_kind_and_params_without_side_effects(self):
        """잘못된 입력 거부 (begin): 무효한 kind 및 params 거부 및 side-effect free 검증."""
        manager = self._manager()
        invalid_kinds = [('', {}), (None, {}), (True, {}), (7, {}), ([], {}), ({}, {})]
        invalid_params = [('format', []), ('format', 'bad'), ('format', 0), ('format', False)]

        for kind, params in invalid_kinds + invalid_params:
            with self.subTest(kind=kind, params=params):
                before_events = manager.events()
                with self.assertRaises(ServiceError) as ctx:
                    manager.begin(kind, params)
                self.assertEqual(ctx.exception.code, 'INVALID_INPUT')
                self.assertEqual(manager.events(), before_events)
                self.assertIsNone(manager.latest())

        valid_id = manager.begin('format', None)
        self.assertEqual(manager.status(valid_id)['state'], 'queued')
        self.assertEqual(manager.events()['events'], [])
        manager.report(valid_id, 'done', {})

    def test_events_rejects_invalid_cursor_and_limit_types(self):
        """잘못된 입력 거부 (events): after_seq 및 max에 대한 무효 타입(bool 구별 등) 거부 검증."""
        manager = self._manager()
        identifier = manager.begin('format', {})
        manager.report(identifier, 'started', {})
        manager.report(identifier, 'done', {})
        before_events = manager.events()

        invalid_cursors = [(False, 1), (True, 1), (0.0, 1), ('0', 1), (None, 1), (-1, 1)]
        invalid_limits = [(0, False), (0, True), (0, 1.0), (0, '1'), (0, None), (0, -1), (0, 0), (0, 201)]

        for after_seq, max_count in invalid_cursors + invalid_limits:
            with self.subTest(after_seq=after_seq, max=max_count):
                with self.assertRaises(ServiceError) as ctx:
                    manager.events(after_seq, max_count)
                self.assertEqual(ctx.exception.code, 'INVALID_INPUT')
                self.assertEqual(manager.events(), before_events)

        self.assertEqual(len(manager.events(0, max=1)['events']), 1)
        self.assertEqual(len(manager.events(0, max=200)['events']), 2)
        p_empty = manager.events(2, max=1)
        self.assertEqual(p_empty['events'], [])
        self.assertEqual(p_empty['next_seq'], 2)

    def test_report_rejects_invalid_event_shape_without_side_effects(self):
        """잘못된 입력 거부 (report): 알 수 없는 type 또는 dict가 아닌 data 거부 및 상태 불변 검증."""
        manager = self._manager()
        identifier = manager.begin('format', {})
        manager.report(identifier, 'started', {})
        before_state = manager.status(identifier)
        before_events = manager.events()

        invalid_cases = [('unknown', {}), ('', {}), (None, {}), ('progress', None), ('log', []), ('done', 'bad')]

        try:
            for ev_type, ev_data in invalid_cases:
                with self.subTest(type=ev_type, data=ev_data):
                    with self.assertRaises(ServiceError) as ctx:
                        manager.report(identifier, ev_type, ev_data)
                    self.assertEqual(ctx.exception.code, 'INVALID_INPUT')
                    self.assertEqual(manager.status(identifier), before_state)
                    self.assertEqual(manager.events(), before_events)
        finally:
            manager.report(identifier, 'done', {})
            self.assertEqual(manager.status(identifier)['state'], 'done')

    def test_unknown_job_ids_use_job_not_found(self):
        """잘못된 입력 거부 (ID): 존재하지 않거나 잘못된 ID에 대한 일관된 JOB_NOT_FOUND 반환 검증."""
        manager = self._manager()
        invalid_ids = ['missing', '', None, False, 7, []]

        for identifier in invalid_ids:
            with self.subTest(identifier=identifier):
                methods = [
                    ('status', lambda: manager.status(identifier)),
                    ('cancel', lambda: manager.cancel(identifier)),
                    ('thread', lambda: manager.thread(identifier)),
                    ('cancelled', lambda: manager.cancelled(identifier)),
                    ('report', lambda: manager.report(identifier, 'log', {})),
                ]
                with patch('docfit_app.jobs.threading.Timer') as mock_timer:
                    for name, call in methods:
                        with self.subTest(method=name):
                            with self.assertRaises(ServiceError) as ctx:
                                call()
                            self.assertEqual(ctx.exception.code, 'JOB_NOT_FOUND')
                    mock_timer.assert_not_called()

        self.assertIsNone(manager.latest())
        self.assertEqual(manager.events()['events'], [])


if __name__ == '__main__':
    unittest.main()
