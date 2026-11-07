"""IPCJOB2: 공용 job 봉투 + library_index(1단계 이관 대상). 한/글 COM 없음."""
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from docfit_app.api_contract import ServiceError
from docfit_app.job_envelope import ProgressThrottle, fit_result, job_error
from docfit_app.jobs import JobManager
from docfit_app.library_service import LibraryService

TERMINAL = {'done', 'failed', 'cancelled'}


def wait_terminal(manager, identifier, timeout=5):
    thread = manager._jobs[identifier]['thread']
    thread.join(timeout)
    assert not thread.is_alive()
    return manager.job_status(identifier)


class EnvelopeTests(unittest.TestCase):
    def test_job_error_mapping(self):
        self.assertEqual(job_error(ServiceError('HWP_FAILED', 'x', False)),
                         {'code': 'HWP_FAILED', 'message': 'x', 'recoverable': False})
        self.assertEqual(job_error(ValueError('나쁨'))['code'], 'INVALID_INPUT')
        e = job_error(RuntimeError('y' * 900))
        self.assertEqual((e['code'], e['recoverable'], len(e['message'])), ('JOB_FAILED', True, 500))

    def test_throttle_coalesces_and_flushes_last(self):
        now = [0.0]
        out = []
        t = ProgressThrottle(lambda ty, d: out.append(d), clock=lambda: now[0])
        for i in range(5):
            t({'n': i})
        self.assertEqual(out, [{'n': 0}])
        t.flush()
        self.assertEqual(out[-1], {'n': 4})
        now[0] = 1.0
        t({'n': 9})
        self.assertEqual(out[-1], {'n': 9})

    def test_fit_result_limit(self):
        self.assertEqual(fit_result({'a': 1}), {'a': 1})
        self.assertEqual(fit_result('x' * 100, limit=10)['result_omitted'], 'RESULT_TOO_LARGE')


class JobStatusTests(unittest.TestCase):
    def manager(self):
        m = JobManager()
        self.addCleanup(lambda: m.shutdown(timeout=.1))
        return m

    def test_event_order_and_result_via_job_status(self):
        m = self.manager()
        def runner(report, cancelled):
            report('progress', {'percent': 10})
            report('item_done', {'source': 'a', 'output': 'b'})
            return {'n': 1}
        jid = m.start('library_index', {}, runner)
        status = wait_terminal(m, jid)
        self.assertEqual(status['state'], 'done')
        self.assertEqual(status['result'], {'n': 1})
        types = [e['type'] for e in m.events()['events'] if e['job_id'] == jid]
        self.assertEqual(types, ['started', 'progress', 'item_done', 'done'])

    def test_error_envelope_in_event_and_status(self):
        m = self.manager()
        def runner(report, cancelled):
            raise ServiceError('HWP_FAILED', '실패', False)
        jid = m.start('library_index', {}, runner)
        status = wait_terminal(m, jid)
        self.assertEqual(status['state'], 'failed')
        expected = {'code': 'HWP_FAILED', 'message': '실패', 'recoverable': False}
        self.assertEqual(status['error'], expected)
        failed = [e for e in m.events()['events'] if e['type'] == 'failed'][0]
        self.assertEqual(failed['data'], expected)

    def test_singleton_and_two_concurrent_jobs(self):
        m = self.manager()
        gate = threading.Event()
        def slow(report, cancelled):
            gate.wait(3)
            return 'slow'
        first = m.start('library_index', {}, slow)
        with self.assertRaises(ServiceError) as ctx:
            m.begin('library_index', {})
        self.assertEqual(ctx.exception.code, 'JOB_RUNNING')
        # 문서 슬롯 작업은 자료함 색인과 동시에 실행 가능
        second = m.start('format', {}, lambda report, cancelled: report('progress', {'percent': 50}) or 'doc')
        self.assertEqual(wait_terminal(m, second)['result'], 'doc')
        self.assertEqual(m.status(first)['state'], 'running')
        gate.set()
        self.assertEqual(wait_terminal(m, first)['result'], 'slow')
        by_job = {}
        for e in m.events()['events']:
            by_job.setdefault(e['job_id'], []).append(e['type'])
        self.assertEqual(by_job[first][-1], 'done')
        self.assertEqual(by_job[second][-1], 'done')

    def test_job_status_unknown(self):
        with self.assertRaises(ServiceError) as ctx:
            self.manager().job_status('nope')
        self.assertEqual(ctx.exception.code, 'JOB_NOT_FOUND')


class LibraryIndexJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root'
        self.root.mkdir()
        self.service = LibraryService(Path(self.temp.name) / 'library.db')
        self.addCleanup(self.service.close)
        self.library = self.service.create('자료함')['id']
        self.manager = JobManager()
        self.addCleanup(lambda: self.manager.shutdown(timeout=.1))

    def run_job(self):
        jid = self.manager.start('library_index', {'library_id': self.library}, self.service.index_runner(self.library))
        return jid, wait_terminal(self.manager, jid)

    def test_matches_sync_index_and_emits_progress(self):
        for i in range(3):
            (self.root / f'f{i}.txt').write_text('x')
        self.service.add_folder(self.library, self.root)
        jid, status = self.run_job()
        self.assertEqual(status['state'], 'done')
        self.assertTrue(status['result']['ok'])
        self.assertEqual(status['result']['indexed'], 3)
        types = [e['type'] for e in self.manager.events()['events']]
        self.assertEqual(types[0], 'started')
        self.assertIn('progress', types)
        self.assertEqual(types[-1], 'done')
        progress = [e['data'] for e in self.manager.events()['events'] if e['type'] == 'progress'][0]
        self.assertTrue(progress['indeterminate'])
        # 기존 동기 경로 결과와 같다(두 번째 색인: 변경 없음)
        self.assertEqual(self.service.index(self.library)['indexed'], 0)

    def test_cancel_leaves_db_and_sources_untouched(self):
        (self.root / 'sub').mkdir()  # 취소 확인 지점이 한 번 더 오도록 하위 폴더를 둔다
        (self.root / 'a.txt').write_text('x')
        (self.root / 'sub' / 'b.txt').write_text('y')
        self.service.add_folder(self.library, self.root)
        entered, release = threading.Event(), threading.Event()
        real = self.service.index
        def slow_index(library_id, *, cancel=None, progress=None):
            def gated(found):
                entered.set()
                release.wait(3)
                progress(found)
            return real(library_id, cancel=cancel, progress=gated)
        with patch.object(self.service, 'index', slow_index):
            jid = self.manager.start('library_index', {}, self.service.index_runner(self.library))
            self.assertTrue(entered.wait(3))
            self.manager.cancel(jid)
            release.set()
            status = wait_terminal(self.manager, jid)
        self.assertEqual(status['state'], 'cancelled')
        last = [e for e in self.manager.events()['events'] if e['job_id'] == jid][-1]
        self.assertEqual(last['type'], 'cancelled')
        self.assertEqual(set(last['data']['partial']), {'success', 'failed'})
        self.assertEqual(len(self.service.search(self.library, 'txt')), 0)  # 색인 DB 미변경
        self.assertEqual((self.root / 'a.txt').read_text(), 'x')
        self.assertEqual(self.service.index(self.library)['indexed'], 2)  # 취소 때 아무것도 기록되지 않았음
        self.assertTrue(self.service._lock.acquire(blocking=False))  # 잠금 해제됨(정리)
        self.service._lock.release()

    def test_unknown_library_reports_failed_envelope(self):
        jid = self.manager.start('library_index', {}, self.service.index_runner(9999))
        status = wait_terminal(self.manager, jid)
        self.assertEqual(status['state'], 'failed')
        self.assertEqual(status['error']['code'], 'INVALID_INPUT')
        self.assertIn('recoverable', status['error'])


class ApplicationServiceWiringTests(unittest.TestCase):
    def test_start_job_library_index_and_job_status(self):
        from docfit_app.application_service import ApplicationService
        with tempfile.TemporaryDirectory() as d:
            app = ApplicationService(Path(d) / 'settings.json')
            try:
                self.assertIn('jobs.v1', app.dispatch('handshake', [])['capabilities'])
                lib = app.dispatch('library', ['create', {'name': 'x'}])['library']['id']
                root = Path(d) / 'r'
                root.mkdir()
                (root / 'a.txt').write_text('x')
                app.dispatch('library', ['add_folder', {'library_id': lib, 'path': str(root)}])
                jid = app.dispatch('start_job', ['library_index', {'library_id': lib}])
                self.assertIsInstance(jid, str)
                app.jobs._jobs[jid]['thread'].join(5)
                status = app.dispatch('job_status', [jid])
                self.assertEqual(status['state'], 'done')
                self.assertEqual(status['result']['indexed'], 1)
                with self.assertRaises(ServiceError):
                    app.dispatch('start_job', ['library_index', {'library_id': 'x'}])
                # 기존 동기 호출은 그대로
                self.assertTrue(app.dispatch('library', ['index', {'library_id': lib}])['ok'])
            finally:
                app.jobs.shutdown(timeout=.1)
                if getattr(app, '_library_service', None):
                    app._library_service.close()


if __name__ == '__main__':
    unittest.main()
