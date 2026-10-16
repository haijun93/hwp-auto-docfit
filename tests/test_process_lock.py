import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class ProcessLockTests(unittest.TestCase):
    def test_two_process_updates_preserve_independent_fields(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)/'settings.json';path.write_text('{}')
            script='''import sys,time
from docfit_app.settings_service import SettingsService
def change(settings):
    time.sleep(0.1)
    settings[sys.argv[2]]=True
SettingsService(sys.argv[1]).update(change)
'''
            children=[subprocess.Popen([sys.executable,'-c',script,str(path),key],cwd=Path(__file__).parents[1])
                      for key in ('a','b')]
            try:
                for child in children:self.assertEqual(child.wait(timeout=10),0)
                self.assertEqual(json.loads(path.read_text()),{'a':True,'b':True})
            finally:
                for child in children:
                    if child.poll() is None:child.kill();child.wait(timeout=5)
