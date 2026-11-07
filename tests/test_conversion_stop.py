"""Stop-timing tests for file conversion using a fake converter (no real Hancom COM)."""
import hashlib
import importlib.util
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from docfit_app.conversion_runner import run_conversion
from docfit_core import file_conversion as fc


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ConversionStopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.files = []
        for index in range(3):
            path = Path(self.tmp.name) / f'doc{index}.hwpx'
            path.write_bytes(b'original-%d' % index)
            self.files.append(path)
        self.before = {p: digest(p) for p in self.files}
        self.app = Mock()
        self.pythoncom = Mock()
        self.runtime = lambda: dict(
            pythoncom=self.pythoncom, 한글_COM_인스턴스_생성=Mock(return_value=self.app),
            REGISTER_MODULE_NAME='x', REGISTER_MODULE_VALUE='y')
        self.stop = threading.Event()
        self.events = []

    def run_job(self, converter):
        with patch.object(fc, 'convert_to_pdf', side_effect=converter) as convert:
            results = run_conversion(self.files, 'pdf', stop_event=self.stop,
                                     progress=self.events.append, runtime_factory=self.runtime)
        self.convert = convert
        return results

    def names(self):
        return [e[0] for e in self.events]

    def assert_clean(self):
        self.assertEqual({p: digest(p) for p in self.files}, self.before)   # 원본 그대로
        self.assertEqual(sorted(p.name for p in Path(self.tmp.name).iterdir() if p.suffix == '.pdf'),
                         sorted(self.written))
        self.app.Quit.assert_called_once()
        self.pythoncom.CoUninitialize.assert_called_once()

    def converter(self, stop_after=None, fail_on=None):
        self.written = []
        def convert(app, source, target):
            if fail_on is not None and source.name == self.files[fail_on].name:
                raise RuntimeError('한/글이 강제 종료됨')
            Path(target).write_bytes(b'%PDF-1.7')
            self.written.append(Path(target).name)
            if stop_after is not None and source.name == self.files[stop_after].name:
                self.stop.set()
            return target
        return convert

    def test_stop_before_start_converts_nothing(self):
        self.stop.set()
        results = self.run_job(self.converter())
        self.convert.assert_not_called()
        self.assertEqual([r['status'] for r in results], ['cancelled'])
        self.assertEqual(self.events[-1], ('file_conversion_stopped', 0, 0))
        self.assert_clean()

    def test_stop_in_middle_skips_remaining_files(self):
        results = self.run_job(self.converter(stop_after=0))
        self.assertEqual(self.convert.call_count, 1)
        self.assertEqual([r['status'] for r in results], ['success', 'cancelled'])
        self.assertEqual(self.events[-1], ('file_conversion_stopped', 1, 0))
        self.assertNotIn('file_conversion_finished', self.names())
        self.assert_clean()

    def test_stop_during_last_file_still_reports_stopped(self):
        results = self.run_job(self.converter(stop_after=2))
        self.assertEqual(self.convert.call_count, 3)
        self.assertEqual(self.events[-1], ('file_conversion_stopped', 3, 0))
        self.assertEqual(results[-1]['status'], 'cancelled')
        self.assert_clean()

    def test_forced_kill_fails_current_file_and_stops(self):
        # 강제 종료로 한/글 COM 호출이 예외로 빠져나오는 경우: 그 파일만 실패, 나머지는 처리 안 함.
        convert = self.converter(fail_on=1)
        def killing(app, source, target):
            if source.name == self.files[1].name:
                self.stop.set()
            return convert(app, source, target)
        results = self.run_job(killing)
        self.assertEqual(self.convert.call_count, 2)
        self.assertEqual(self.events[-1], ('file_conversion_stopped', 1, 1))
        self.assertEqual([r['status'] for r in results], ['success', 'failed', 'cancelled'])
        self.app.Clear.assert_called_with(1)
        self.assert_clean()

    def test_runner_can_start_again_after_stop(self):
        self.run_job(self.converter(stop_after=0))
        self.stop.clear()   # 화면의 다시 시작과 같은 동작: 중단 신호만 지우면 된다
        self.events.clear()
        # 첫 파일의 결과 PDF는 이미 있으므로 새 이름으로 만들어진다(덮어쓰지 않음).
        self.run_job(self.converter())
        self.assertEqual(self.events[-1][0], 'file_conversion_finished')


class PendingTempTests(unittest.TestCase):
    def test_save_failure_removes_temp_pdf(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'a.hwpx'
            source.write_bytes(b'orig')
            target = Path(folder) / 'a.pdf'
            app = Mock()
            def save(path, *_):
                Path(path).write_bytes(b'%PDF-partial')
                raise RuntimeError('killed')
            app.SaveAs.side_effect = save
            with self.assertRaises(RuntimeError):
                fc.convert_hwpx_to_pdf(app, source, target)
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()), ['a.hwpx'])
            self.assertEqual(source.read_bytes(), b'orig')
            self.assertEqual(fc._PENDING_TEMP_PDFS, set())

    def test_cleanup_removes_only_registered_temp_pdfs(self):
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder) / 'docfit_pdf_abc.pdf'
            other = Path(folder) / 'result.pdf'
            temp.write_bytes(b'%PDF-')
            other.write_bytes(b'%PDF-')
            fc._PENDING_TEMP_PDFS.update({temp, other})
            self.assertEqual(fc.cleanup_pending_temp_outputs(), [temp])
            self.assertFalse(temp.exists())
            self.assertTrue(other.exists())
            self.assertEqual(fc._PENDING_TEMP_PDFS, set())

    @unittest.skipUnless(importlib.util.find_spec('winreg'), 'winreg 없음(Windows 전용 hwp-auto-docfit.py) — PC에서 확인')
    def test_force_exit_cleans_pending_temp(self):
        import runpy
        ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))
        app = NS(로그표시=Mock(), _비교창_분리_후_보존=Mock(), _프로세스_종료=Mock())
        with patch.object(fc, 'cleanup_pending_temp_outputs') as cleanup, \
                patch('docfit_core.hwp_process.kill_owned'):
            ns['HwpAutoDocFitGUI']._강제_종료(app)
        cleanup.assert_called_once_with()
        app._프로세스_종료.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()
