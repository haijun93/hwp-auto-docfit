import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from docfit_app import cli
from docfit_app.conversion_runner import run_conversion


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def file(self, name='문서.hwpx'):
        path = self.folder / name
        path.write_bytes(b'fixture')
        return path

    def invoke(self, *args, **kwargs):
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(args, stdout=out, stderr=err, console=True, **kwargs)
        return code, out.getvalue(), err.getvalue()

    def test_help_version_formats(self):
        for command, token in [('help', '--to'), ('version', '.'), ('formats', 'pdfm')]:
            code, out, _ = self.invoke(command)
            self.assertEqual(code, 0)
            self.assertIn(token, out)

    def test_argument_errors(self):
        for args in [(), ('convert',), ('convert', 'absent.hwpx', '--to', 'pdf'),
                     ('convert', str(self.file()), '--to', 'bad'),
                     ('convert', str(self.file()), '--to', 'pdf', '-o', str(self.file('output.txt'))),
                     ('convert', str(self.folder / '*.none'), '--to', 'pdf')]:
            self.assertEqual(self.invoke(*args)[0], 2, args)

    def test_empty_directory_is_argument_error(self):
        self.assertEqual(self.invoke('convert', str(self.folder), '--to', 'pdf')[0], 2)

    def test_folder_wildcard_and_duplicates(self):
        a, b = self.file(), self.file('둘.pdf')
        self.file('ignored.exe')
        files = cli.expand_inputs([str(self.folder), str(self.folder / '*.pdf'), str(a)])
        self.assertEqual(set(files), {str(a.resolve()), str(b.resolve())})

    def test_same_format_has_code_three_and_no_com(self):
        path = self.file('메모.txt')
        factory = Mock(side_effect=AssertionError('COM must not run'))
        with patch('docfit_app.conversion_runner._runtime', factory):
            code, out, _ = self.invoke('convert', str(path), '--to', 'txt', '--json')
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(out)['results'][0]['status'], 'skipped')
        factory.assert_not_called()

    def test_json_errors_and_quiet(self):
        code, out, err = self.invoke('convert', 'missing.hwpx', '--to', 'pdf', '--json')
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)['exit_code'], 2)
        self.assertEqual(len(out.splitlines()), 1)
        self.assertEqual(err, '')
        self.assertEqual(self.invoke('convert', 'missing.hwpx', '--to', 'pdf', '--quiet')[1:], ('', ''))

    def test_partial_failure_and_engine_failure(self):
        path = self.file()
        for results, code in [([dict(source=str(path), output='ok.pdf', status='success', error=None),
                               dict(source='bad', output=None, status='failed', error='reason')], 1),
                              ([dict(source=str(path), output='ok.pdf', status='success', error=None)], 0)]:
            self.assertEqual(self.invoke('convert', str(path), '--to', 'pdf', runner=lambda *a, **k: results)[0], code)
        def broken(*a, **kw):
            raise RuntimeError('engine unavailable')
        self.assertEqual(self.invoke('convert', str(path), '--to', 'pdf', runner=broken)[0], 1)

    def test_real_pdf_image_merge_without_com_and_output_collision(self):
        from PIL import Image
        from pypdf import PdfWriter, PdfReader
        pdf = self.folder / '첫.pdf'
        writer = PdfWriter()
        writer.add_blank_page(100, 100)
        writer.write(str(pdf))
        image = self.folder / '둘.png'
        Image.new('RGB', (20, 20), 'red').save(image)
        output = self.folder / '결과'
        factory = Mock(side_effect=AssertionError('no COM'))
        with patch('docfit_app.conversion_runner._runtime', factory):
            for _ in range(2):
                code, text, _ = self.invoke('convert', str(pdf), str(image), '--to', 'pdfm', '-o', str(output), '--json')
                self.assertEqual(code, 0, text)
                result = json.loads(text)['results']
                self.assertEqual(len(result), 1)
                self.assertEqual(len(PdfReader(result[0]['output']).pages), 2)
        factory.assert_not_called()
        self.assertEqual(len(list(output.glob('*.pdf'))), 2)
        self.assertEqual(len(PdfReader(str(pdf)).pages), 1)

    def test_merge_single_is_argument_error(self):
        self.assertEqual(self.invoke('convert', str(self.file('one.pdf')), '--to', 'pdfm')[0], 2)

    def test_merge_failure_does_not_create_partial_pdf(self):
        results = run_conversion([self.file('bad.pdf'), self.file('bad.png')], 'pdfm')
        self.assertTrue(any(r['status'] == 'failed' for r in results))
        self.assertFalse(any(r['status'] == 'success' for r in results))
        self.assertFalse(list(self.folder.glob('*(합친 PDF)*')))

    def test_fake_com_independent_registered_and_cleaned(self):
        app, com, factory = Mock(), Mock(), Mock()
        factory.return_value = app
        runtime = dict(pythoncom=com, 한글_COM_인스턴스_생성=factory,
                       REGISTER_MODULE_NAME='FilePathCheckDLL', REGISTER_MODULE_VALUE='security')
        source = self.file()
        with patch('docfit_core.file_conversion.convert_to_pdf') as convert:
            results = run_conversion([source], 'pdf', runtime_factory=lambda: runtime)
        factory.assert_called_once_with(독립=True)
        app.RegisterModule.assert_called_once_with('FilePathCheckDLL', 'security')
        app.Clear.assert_called_with(1)
        app.Quit.assert_called_once()
        com.CoInitialize.assert_called_once()
        com.CoUninitialize.assert_called_once()
        self.assertEqual(results[0]['status'], 'success')
        convert.assert_called_once()

    def test_security_failure_is_reported_and_com_released(self):
        app, com = Mock(), Mock()
        app.RegisterModule.return_value = False
        runtime = dict(pythoncom=com, 한글_COM_인스턴스_생성=lambda **k: app,
                       REGISTER_MODULE_NAME='name', REGISTER_MODULE_VALUE='value')
        result = run_conversion([self.file()], 'pdf', runtime_factory=lambda: runtime)
        self.assertEqual(result[0]['status'], 'failed')
        self.assertIn('보안 모듈', result[0]['error'])
        com.CoUninitialize.assert_called_once()

    def test_stop_prevents_outputs(self):
        stop = threading.Event()
        stop.set()
        self.assertEqual(run_conversion([self.file('x.txt')], 'md', stop_event=stop), [])

    def test_notification_even_on_argument_error(self):
        with patch.object(cli, 'notify') as notify:
            cli.main(['convert', 'missing', '--to', 'pdf', '--notify'], console=False,
                     stdout=io.StringIO(), stderr=io.StringIO())
        self.assertIn('입력 파일', notify.call_args.args[0])

    def test_entrypoint_no_gui_or_single_instance(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, str(root / 'hwp-auto-docfit.py'), 'formats'],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('pdfm', result.stdout)
