import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from docfit_app import instance_files


class InstanceFileTests(unittest.TestCase):
    def test_open_adds_startup_and_forwarded_files_without_starting_job(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
            document = Path(folder).resolve() / '문서.hwpx'  # CI의 짧은 이름 임시 폴더 대비
            document.write_bytes(b'fixture')
            instance_files.forward([str(document), str(document.parent / 'missing')])
            requests = list(instance_files._folder().glob('*.json'))
            self.assertEqual(len(requests), 1)
            self.assertEqual(json.loads(requests[0].read_text(encoding='utf-8')),
                             {'rename': False, 'paths': [str(document)]})
            gui = Mock(running=False)
            with patch.object(sys, 'argv', ['app', str(document)]):
                instance_files.start(gui)
            gui.파일추가.assert_called_once_with(str(document))
            poll = gui.root.after.call_args.args[1]
            poll()
            self.assertEqual(gui.파일추가.call_count, 2)
            self.assertEqual(list(instance_files._folder().glob('*.json')), [])
            gui.작업시작.assert_not_called()

    def test_bad_requests_are_quarantined_and_valid_requests_continue(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
            requests = instance_files._folder()
            requests.mkdir(parents=True)
            for name, data in [('a', b''), ('b', b'{broken'), ('c', b'\xff')]:
                (requests / (name + '.json')).write_bytes(data)
            (requests / 'z.json').write_text(json.dumps(['valid.hwpx']), encoding='utf-8')
            gui = Mock(running=False)
            with patch.object(sys, 'argv', ['app']):
                instance_files.start(gui)
            poll = gui.root.after.call_args.args[1]
            poll()
            poll()
            gui.파일추가.assert_called_once_with('valid.hwpx')
            self.assertEqual(list(requests.glob('*.json')), [])
            self.assertEqual(len(list(requests.glob('*.bad'))), 3)
            self.assertEqual(gui.root.after.call_count, 3)

    def test_busy_app_keeps_request_until_idle(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
            document = Path(folder).resolve() / '문서.hwpx'  # CI의 짧은 이름 임시 폴더 대비
            document.write_bytes(b'fixture')
            instance_files.forward([str(document)])
            gui = Mock(running=True)
            with patch.object(sys, 'argv', ['app']):
                instance_files.start(gui)
            poll = gui.root.after.call_args.args[1]
            poll()
            gui.파일추가.assert_not_called()
            gui.running = False
            poll()
            gui.파일추가.assert_called_once_with(str(document))

    def test_rename_arguments_startup_and_forward_stay_out_of_documents(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
            first = Path(folder).resolve() / 'first.txt'
            second = Path(folder).resolve() / 'second.txt'
            missing = Path(folder).resolve() / 'missing.txt'
            first.write_text('a')
            second.write_text('b')
            gui = Mock(running=False)
            with patch.object(sys, 'argv', ['app', '--rename', str(first), str(missing)]):
                instance_files.start(gui)
            self.assertEqual(gui._rename_startup_paths, [str(first), str(missing)])
            gui.파일추가.assert_not_called()

            gui._rename_startup_paths.clear()
            instance_files.forward(['--rename', str(second), str(missing)])
            poll = gui.root.after.call_args.args[1]
            poll()
            self.assertEqual(gui._rename_startup_paths, [str(second)])
            gui.파일추가.assert_not_called()

    def test_split_rename_arguments_and_ignore_missing_when_forwarding(self):
        self.assertEqual(instance_files.split_rename_arguments(['--rename', 'a', 'b']),
                         (True, ['a', 'b']))
        self.assertEqual(instance_files.split_rename_arguments(['a', 'b']), (False, ['a', 'b']))
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
            instance_files.forward(['--rename', str(Path(folder) / 'missing')])
            self.assertFalse(instance_files._folder().exists())
