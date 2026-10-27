import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from docfit_app.native_file_dialog_service import NativeFileDialogService
from docfit_app.api_contract import ServiceError

class FileDialogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.file = self.root / '한글.hwpx'
        self.file.write_bytes(b'test')
        self.now = 0
        self.calls = 0
        def dialog(*args):
            self.calls += 1
            return [str(self.file)]
        self.service = NativeFileDialogService(dialog, lambda: self.now)
    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()
    def token(self):
        return self.service.register_selection('add_files', [str(self.file)])['selection_id']
    def test_single_use_and_metadata(self):
        result = self.service.register_selection('add_files', [str(self.file)])
        self.assertEqual(result['files'], [{'name': self.file.name, 'size': 4}])
        token = result['selection_id']
        self.assertEqual(self.service.resolve_selection(token, 'add_files'), [str(self.file.resolve())])
        with self.assertRaises(ServiceError): self.service.resolve_selection(token, 'add_files')
    def test_expiry_boundary(self):
        token = self.token(); self.now = 300
        with self.assertRaises(ServiceError): self.service.resolve_selection(token, 'add_files')
    def test_purpose_binding(self):
        token = self.token()
        with self.assertRaises(ServiceError): self.service.resolve_selection(token, 'idioms')
        self.assertTrue(self.service.resolve_selection(token, 'add_files'))
        with self.assertRaises(ServiceError): self.service.register_selection('unknown', [str(self.file)])
    def test_paths(self):
        for path in ('relative.hwpx', str(self.root/'missing.hwpx'), str(self.file)+':stream', '//server/share/a.hwpx'):
            with self.subTest(path=path), self.assertRaises(ServiceError):
                self.service.register_selection('add_files', [path])
        wrong = self.root/'bad.exe'; wrong.write_bytes(b'')
        with self.assertRaises(ServiceError): self.service.register_selection('add_files', [str(wrong)])
        result = self.service.register_selection('add_files', [str(self.root/'..'/self.root.name/self.file.name)])
        self.assertEqual(self.service.resolve_selection(result['selection_id'], 'add_files'), [str(self.file)])
    def test_cancel(self):
        self.service._dialog = lambda *args: []
        self.assertEqual(self.service.select_files('cancel', 'add_files'), {'ok': True, 'cancelled': True})
    def test_concurrent_dedup(self):
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: self.service.select_files('same', 'add_files'), range(16)))
        self.assertEqual(self.calls, 1)
        self.assertTrue(all(result == results[0] for result in results))
        with self.assertRaises(ServiceError): self.service.select_files('same', 'idioms')
    def test_directory_bounds_and_recursion(self):
        child = self.root/'child'; child.mkdir(); (child/'two.hwpx').write_bytes(b'')
        paths = [str(self.root)]
        self.assertEqual(len(self.service.directory_files(paths)), 1)
        self.assertEqual(len(self.service.directory_files(paths, True)), 2)
        self.service.MAX_FILES = 1
        with self.assertRaises(ServiceError): self.service.directory_files(paths, True)
    def test_source_changed(self):
        token = self.token(); self.file.write_bytes(b'changed')
        with self.assertRaises(ServiceError): self.service.resolve_selection(token, 'add_files')
    def test_save_and_mode(self):
        result = self.service.register_selection('flow_png', [str(self.root/'new.png')])
        self.assertTrue(self.service.resolve_selection(result['selection_id'], 'flow_png'))
        with self.assertRaises(ServiceError): self.service.select_files('bad', 'flow_png')
    def test_async_pending(self):
        gate = threading.Event()
        self.service._dialog = lambda *args: (gate.wait(2) and [])
        self.service.submit_selection('pending', 'add_files')
        self.assertTrue(self.service.selection_status('pending')['pending'])
        gate.set()
        self.assertTrue(self.service.select_files('pending', 'add_files')['cancelled'])

    def test_reparse_parent_rejected(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        original = Path.lstat
        def attributes(path, *args, **kwargs):
            value = original(path, *args, **kwargs)
            if path == self.root:
                return SimpleNamespace(st_mode=value.st_mode, st_file_attributes=0x400)
            return value
        with patch.object(Path, 'lstat', attributes):
            with self.assertRaises(ServiceError): self.token()

    def test_bridge_registration_and_directory(self):
        from unittest.mock import Mock
        from desktop_web_ui import DesktopWebBridge
        bridge = DesktopWebBridge(Mock())
        bridge._file_dialogs.close()
        bridge._file_dialogs = self.service
        bridge.add_paths = Mock(return_value={'count': 1})
        selected = bridge.register_selection({'purpose': 'add_folder', 'paths': [str(self.root)]})
        self.assertEqual(bridge.add_directory(selected['selection_id']), {'count': 1})
        bridge.add_paths.assert_called_once_with([str(self.file)])
        result = bridge.select_files({'request_id': 'bridge', 'purpose': 'add_files'})
        if result.get('pending'):
            self.service.select_files('bridge', 'add_files')
            result = bridge.selection_status('bridge')
        self.assertFalse(result['cancelled'])
        self.assertNotIn(str(self.root), str(result))

    def test_conversion_selection_accepts_supported_formats(self):
        from docfit_core.file_conversion import CONVERSION_INPUTS
        files = []
        for ext in sorted(CONVERSION_INPUTS):
            sample = self.root / f"sample{ext}"
            sample.write_bytes(b"data")
            files.append(sample)
        paths = [str(f) for f in files]
        res = self.service.register_selection('add_conversion_files', paths)
        self.assertTrue(res['ok'])
        token = res['selection_id']
        resolved = self.service.resolve_selection(token, 'add_conversion_files')
        self.assertEqual(len(resolved), len(files))
        for sample in files:
            with self.subTest(ext=sample.suffix.lower()):
                self.assertIn(str(sample.resolve()), resolved)

    def test_conversion_purpose_does_not_expand_document_policy(self):
        pptx = self.root / "test.pptx"
        pptx.write_bytes(b"pptx_data")
        res = self.service.register_selection('add_conversion_files', [str(pptx)])
        self.assertTrue(res['ok'])
        resolved = self.service.resolve_selection(res['selection_id'], 'add_conversion_files')
        self.assertEqual(resolved, [str(pptx.resolve())])
        with self.assertRaises(ServiceError) as ctx:
            self.service.register_selection('add_files', [str(pptx)])
        self.assertEqual(ctx.exception.code, 'UNSUPPORTED_FORMAT')

    def test_conversion_token_is_bound_single_use_and_expires(self):
        pptx = self.root / "bound.pptx"
        pptx.write_bytes(b"bound")
        res = self.service.register_selection('add_conversion_files', [str(pptx)])
        token = res['selection_id']
        for f in res['files']:
            self.assertIn('name', f)
            self.assertNotIn('path', f)
            self.assertNotIn(str(self.root), str(f))
        with self.assertRaises(ServiceError) as ctx:
            self.service.resolve_selection(token, 'add_files')
        self.assertEqual(ctx.exception.code, 'INVALID_PURPOSE')
        resolved = self.service.resolve_selection(token, 'add_conversion_files')
        self.assertEqual(resolved, [str(pptx.resolve())])
        with self.assertRaises(ServiceError) as ctx:
            self.service.resolve_selection(token, 'add_conversion_files')
        self.assertEqual(ctx.exception.code, 'SELECTION_EXPIRED')
        res2 = self.service.register_selection('add_conversion_files', [str(pptx)])
        token2 = res2['selection_id']
        self.now = 300
        with self.assertRaises(ServiceError) as ctx:
            self.service.resolve_selection(token2, 'add_conversion_files')
        self.assertEqual(ctx.exception.code, 'SELECTION_EXPIRED')

    def test_conversion_selection_cancel_and_request_dedup(self):
        self.service._dialog = lambda *args: []
        cancel_res = self.service.select_files('conv_cancel', 'add_conversion_files')
        self.assertEqual(cancel_res, {'ok': True, 'cancelled': True})
        calls = [0]
        def counting_dialog(*args):
            calls[0] += 1
            return [str(self.file)]
        self.service._dialog = counting_dialog
        with ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(lambda _: self.service.select_files('conv_dedup', 'add_conversion_files'), range(8)))
        self.assertEqual(calls[0], 1)
        self.assertTrue(all(r == results[0] for r in results))

if __name__ == '__main__': unittest.main()
