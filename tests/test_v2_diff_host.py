"""T17 trust boundary and real child lifecycle tests (no HWP/COM documents)."""
import io
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from docfit_engine.diff_host import (DiffHost, MAX_LINE, ProtocolError, decode_frame,
                                    encode_frame, read_frame, sha256_file, validate_command)
from docfit_app.diff_host_service import DiffError, DiffHostService, isolate_file


def command(method='heartbeat', params=None, viewer_id='viewer', request_id='req'):
    return {'v': 1, 'id': request_id, 'viewer_id': viewer_id, 'method': method,
            'params': {} if params is None else params}


class WireTests(unittest.TestCase):
    def test_utf8_and_framing(self):
        value = command('close', {'reason': 'user'})
        self.assertEqual(decode_frame(encode_frame(value)), value)
        self.assertIsNone(read_frame(io.BytesIO()))
        for data in (b'{}', b'\xff\n', b'[]\n', b'{"v":true}\n', b'{"v":1}\nextra'):
            with self.assertRaises(ProtocolError):
                decode_frame(data)

    def test_line_boundary(self):
        prefix, suffix = b'{"v":1,"x":"', b'"}'
        body = prefix + b'x' * (MAX_LINE - len(prefix) - len(suffix)) + suffix
        self.assertEqual(len(body), MAX_LINE)
        decode_frame(body + b'\n')
        decode_frame(body + b'\r\n')
        with self.assertRaises(ProtocolError):
            decode_frame(body[:-2] + b'x"}\n')
        with self.assertRaises(ProtocolError):
            read_frame(io.BytesIO(b'x' * (MAX_LINE + 50) + b'\n'))

    def test_depth(self):
        value = 0
        for _ in range(14):
            value = [value]
        encode_frame({'v': 1, 'value': value})
        with self.assertRaises(ProtocolError):
            encode_frame({'v': 1, 'value': [[value]]})

    def test_duplicate_nonfinite(self):
        for body in ('{"v":1,"v":1}', '{"v":1,"p":{"x":1,"x":2}}',
                     '{"v":1,"n":NaN}', '{"v":1,"n":Infinity}',
                     '{"v":1,"n":-Infinity}', '{"v":1,"n":1e999}'):
            with self.assertRaises(ProtocolError):
                decode_frame(body.encode() + b'\n')

    def test_method_types(self):
        for frame in (command('eval'), command(params={'x': 1}), command('set_sync', {'enabled': 1}),
                      command('navigate', {'side': 'left', 'page': True, 'sync': True, 'navigation_seq': 1})):
            with self.assertRaises(ProtocolError):
                validate_command(frame)


class HostTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.viewer_id = str(uuid4())
        directory = self.root / self.viewer_id
        directory.mkdir()
        self.params = {'nonce': secrets.token_hex(32), 'viewer_id': self.viewer_id,
                       'parent_pid': os.getppid(), 'protocol': 1}
        for side in ('left', 'right'):
            path = directory / (side + '.hwpx')
            path.write_bytes(b'test-document')
            path.chmod(stat.S_IREAD)
            self.params[side] = {'path': str(path), 'sha256': sha256_file(path)}
        self.output = io.BytesIO()
        self.now = [0]
        self.host = DiffHost(self.output, headless=True, root=self.root, clock=lambda: self.now[0])

    def tearDown(self):
        if self.host.guard:
            self.host.guard.close()
        for path in self.root.rglob('*.hwpx'):
            path.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.tmp.cleanup()

    def bootstrap(self):
        self.host.handle(command('bootstrap', self.params, self.viewer_id))

    def test_nonce_rejection(self):
        for nonce in ('abc', 'g' * 64, None, 1):
            self.params['nonce'] = nonce
            self.bootstrap()
            frame = json.loads(self.output.getvalue().splitlines()[-1])
            self.assertEqual(frame['error']['code'], 'BOOTSTRAP_REJECTED')
            self.assertTrue(self.host.stopped)
            self.host.cache.clear()

    def test_parent_rejection(self):
        self.params['parent_pid'] = -1
        self.bootstrap()
        self.assertIn(b'PARENT_MISMATCH', self.output.getvalue())

    def test_hash_path_and_permissions_rejection(self):
        self.params['left']['sha256'] = '0' * 64
        self.bootstrap()
        self.assertIn(b'COPY_VALIDATION_FAILED', self.output.getvalue())

    def test_heartbeat_timeout_and_navigation(self):
        self.bootstrap()
        self.assertIn(b'"event":"ready"', self.output.getvalue())
        self.now[0] = 9.9
        self.assertFalse(self.host.expired())
        self.host.handle(command(viewer_id=self.viewer_id, request_id='hb'))
        self.now[0] = 20
        self.assertTrue(self.host.expired())
        self.host.handle(command('navigate', {'side': 'left', 'page': 9, 'sync': True,
                                             'navigation_seq': 2}, self.viewer_id, 'nav'))
        self.assertEqual(self.host.viewer.pages, {'left': 9, 'right': 7})
        self.host.teardown()
        self.assertIn(b'"copy_hashes_match":true', self.output.getvalue())

    def test_replay_and_id_reuse(self):
        self.bootstrap()
        frame = command('set_sync', {'enabled': False}, self.viewer_id, 'sync')
        self.host.handle(frame)
        self.host.handle(frame)
        frame['params']['enabled'] = True
        with self.assertRaises(ProtocolError):
            self.host.handle(frame)

    def test_heartbeat_during_blocked_viewer(self):
        import threading
        self.bootstrap()
        entered, release = threading.Event(), threading.Event()
        def blocked_focus():
            entered.set()
            release.wait(2)
        self.host.viewer.focus = blocked_focus
        thread = threading.Thread(target=self.host.handle,
                                  args=(command('focus', viewer_id=self.viewer_id, request_id='focus'),))
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            self.host.handle(command(viewer_id=self.viewer_id, request_id='hb'))
            self.assertIn(b'"id":"hb"', self.output.getvalue())
        finally:
            release.set()
            thread.join(2)

    def test_response_cache_bound(self):
        self.bootstrap()
        for i in range(270):
            self.host.handle(command(viewer_id=self.viewer_id, request_id=str(i)))
        self.assertEqual(len(self.host.cache), 256)

    def launch_child(self):
        env = os.environ.copy()
        # Put the fixtures beneath the canonical per-user copy root.
        actual_root = self.root / 'HwpAutoDocFit' / 'diff'
        actual_root.mkdir(parents=True)
        (self.root / self.viewer_id).rename(actual_root / self.viewer_id)
        for side in ('left', 'right'):
            self.params[side]['path'] = str(actual_root / self.viewer_id / (side + '.hwpx'))
        self.params['parent_pid'] = os.getpid()
        env['LOCALAPPDATA'] = str(self.root)
        child = subprocess.Popen([sys.executable, '-m', 'docfit_engine.diff_host', '--headless'],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        child.stdin.write(encode_frame(command('bootstrap', self.params, self.viewer_id)))
        child.stdin.flush()
        self.assertTrue(read_frame(child.stdout)['ok'])
        self.assertEqual(read_frame(child.stdout)['event'], 'ready')
        return child

    def test_pipe_eof_terminates_child(self):
        child = self.launch_child()
        try:
            child.stdin.close()
            child.wait(timeout=5)
            frames = [decode_frame(line) for line in child.stdout.readlines()]
            self.assertEqual(frames[-1]['event'], 'closed')
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(2)
            child.stdout.close()
            child.stderr.close()

    def test_missing_heartbeat_terminates_child(self):
        child = self.launch_child()
        try:
            child.wait(timeout=14)
            frames = [decode_frame(line) for line in child.stdout.readlines()]
            self.assertEqual(frames[-1]['data']['reason'], 'heartbeat_timeout')
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(2)
            child.stdin.close()
            child.stdout.close()
            child.stderr.close()


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.left, self.right = self.base / 'original.hwp', self.base / 'result.hwpx'
        self.left.write_bytes(b'left')
        self.right.write_bytes(b'right')
        self.record = {'left': self.left, 'right': self.right, 'revision': 3, 'saved_revision': 3}
        self.root = self.base / 'HwpAutoDocFit' / 'diff'
        self.service = DiffHostService(lambda d, r: dict(self.record), root=self.root, headless=True)

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def wait_state(self, viewer_id, target, timeout=10):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.service.diff_status(viewer_id, 0)
            if status['state'] == target:
                return status
            if status['state'] == 'closed' and target != 'closed':
                self.fail(str(status))
            time.sleep(.03)
        self.fail(str(self.service.diff_status(viewer_id, 0)))

    def test_isolation_and_hash(self):
        copy = self.base / 'copy.hwp'
        entry = isolate_file(self.left, copy)
        try:
            self.assertEqual(entry['sha256'], sha256_file(self.left))
            self.assertEqual(copy.read_bytes(), b'left')
            self.assertFalse(copy.stat().st_mode & 0o222)
            self.assertTrue(self.left.stat().st_mode & 0o222)
            with self.assertRaises(FileExistsError):
                isolate_file(self.left, copy)
        finally:
            copy.chmod(stat.S_IWRITE | stat.S_IREAD)

    def test_source_change(self):
        real = __import__('shutil').copyfileobj
        def mutate(src, dst, length):
            real(src, dst, length)
            self.left.write_bytes(b'changed')
        with patch('docfit_app.diff_host_service.shutil.copyfileobj', side_effect=mutate):
            with self.assertRaisesRegex(DiffError, 'SOURCE_CHANGED'):
                isolate_file(self.left, self.base / 'copy.hwp')

    def test_real_child_lifecycle(self):
        opened = self.service.open_diff('doc', 'result', 3, 'open')
        viewer_id = opened['viewer_id']
        self.assertEqual(self.service.open_diff('doc', 'result', 3, 'open'), opened)
        self.assertFalse(self.service.open_diff('other', 'result', 3, 'open')['ok'])
        status = self.wait_state(viewer_id, 'ready')
        self.assertEqual([e['data']['state'] for e in status['events'] if e['event'] == 'state'],
                         ['preparing', 'starting', 'opening', 'ready'])
        viewer = self.service.viewers[viewer_id]
        self.assertTrue(viewer.directory.is_dir())
        response = self.service.diff_navigate(viewer_id, 'left', 9, True)
        deadline = time.monotonic() + 3
        while response['request_id'] not in viewer.responses and time.monotonic() < deadline:
            time.sleep(.03)
        self.assertTrue(viewer.responses[response['request_id']]['result']['clamped'])
        self.assertEqual(self.service.open_diff('doc', 'result', 3, 'again')['viewer_id'], viewer_id)
        self.service.diff_close(viewer_id)
        status = self.wait_state(viewer_id, 'closed')
        self.assertIsNone(status['error'])
        self.assertIsNotNone(viewer.process.poll())
        self.assertFalse(viewer.directory.exists())
        self.assertEqual(self.left.read_bytes(), b'left')
        self.assertEqual(self.right.read_bytes(), b'right')

    def test_revision_and_limits(self):
        result = self.service.open_diff('doc', 'r', 2, 'bad')
        status = self.wait_state(result['viewer_id'], 'closed')
        self.assertEqual(status['error']['code'], 'UNSAVED_REVISION')
        first = self.service.open_diff('doc', 'r', 3, 'one')
        self.wait_state(first['viewer_id'], 'ready')
        self.assertEqual(self.service.open_diff('doc', 'other', 3, 'two')['error']['code'], 'VIEWER_LIMIT')
        second = self.service.open_diff('doc2', 'r', 3, 'three')
        self.wait_state(second['viewer_id'], 'ready')
        self.assertEqual(self.service.open_diff('doc3', 'r', 3, 'four')['error']['code'], 'VIEWER_LIMIT')

    def test_crashed_child_cleanup(self):
        result = self.service.open_diff('doc', 'r', 3, 'one')
        self.wait_state(result['viewer_id'], 'ready')
        viewer = self.service.viewers[result['viewer_id']]
        viewer.process.kill()
        self.wait_state(viewer.viewer_id, 'closed')
        self.assertFalse(viewer.directory.exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows Job Object')
    def test_job_close_terminates_child(self):
        result = self.service.open_diff('doc', 'r', 3, 'one')
        self.wait_state(result['viewer_id'], 'ready')
        viewer = self.service.viewers[result['viewer_id']]
        if viewer.guard.job is None:
            self.skipTest('Job Object unavailable; headless fallback active')
        viewer.guard.close()
        viewer.process.wait(timeout=3)
        self.wait_state(viewer.viewer_id, 'closed')
        self.assertFalse(viewer.directory.exists())

    def test_native_gate_fails_closed(self):
        self.service.headless = False
        result = self.service.open_diff('doc', 'r', 3, 'one')
        status = self.wait_state(result['viewer_id'], 'closed')
        self.assertIn(status['error']['code'], ('OLE_NOT_AVAILABLE', 'PROCESS_GUARD_FAILED'))


if __name__ == '__main__':
    unittest.main()
