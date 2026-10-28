"""PoC의 사용자 문서 보호·잠금 실패 경계를 COM 없이 검증한다."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('livelink_poc', Path(__file__).parents[1] / 'scripts/livelink_poc.py')
poc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(poc)


class LiveLinkSafetyTests(unittest.TestCase):
    def test_watchdog_terminates_venv_launcher_tree(self):
        import psutil
        import time
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        try:
            time.sleep(.3)
            descendants = psutil.Process(child.pid).children(recursive=True)
            poc.terminate_worker(child)
            self.assertIsNotNone(child.poll())
            self.assertFalse(any(member.is_running() for member in descendants))
        finally:
            if child.poll() is None:
                poc.terminate_worker(child)

    def test_foreign_copy_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            sample = Path(folder) / 'scratch.hwpx'
            obj = SimpleNamespace(XHwpDocuments=SimpleNamespace(
                Active_XHwpDocument=SimpleNamespace(FullName=str(Path(folder) / 'user.hwpx'))))
            with self.assertRaisesRegex(RuntimeError, '사본 경로'):
                poc.verify_copy(obj, sample, 123, {123})

    def test_dead_owned_pid_does_not_read_document(self):
        class NeverRead:
            @property
            def XHwpDocuments(self):
                raise AssertionError('COM에 접근하면 안 됨')
        with self.assertRaisesRegex(RuntimeError, '소유 PID'):
            poc.verify_copy(NeverRead(), Path('scratch.hwpx'), 123, {456})

    def test_existing_lock_is_never_stolen(self):
        with tempfile.TemporaryDirectory() as folder:
            lock = Path(folder) / '.com-test.lock'
            lock.write_text('Claude active test', encoding='utf-8')
            with patch.object(poc, 'LOCK', lock):
                with self.assertRaises(TimeoutError):
                    with poc.test_lock(0):
                        self.fail('기존 잠금을 빼앗음')
            self.assertEqual(lock.read_text(encoding='utf-8'), 'Claude active test')

    def test_exception_releases_only_own_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            lock = Path(folder) / '.com-test.lock'
            with patch.object(poc, 'LOCK', lock):
                with self.assertRaisesRegex(ValueError, 'probe failed'):
                    with poc.test_lock(0):
                        raise ValueError('probe failed')
                self.assertFalse(lock.exists())
                with poc.test_lock(0):
                    lock.write_text('new owner', encoding='utf-8')
                self.assertEqual(lock.read_text(encoding='utf-8'), 'new owner')


if __name__ == '__main__':
    unittest.main()
