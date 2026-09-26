"""이름만 .hwpx이고 내용은 HWP 5.0 바이너리인 문서를 알아본다."""
from pathlib import Path
import runpy
import tempfile
import unittest


class MisnamedHwpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'hwp-auto-docfit.py'))

    def test_detects_ole_signature(self):
        fn = self.ns['바이너리_HWP_파일인가']
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / 'report.hwpx'
            binary.write_bytes(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'\0' * 32)
            zipped = Path(folder) / 'real.hwpx'
            zipped.write_bytes(b'PK\x03\x04' + b'\0' * 32)
            self.assertTrue(fn(binary))
            self.assertFalse(fn(zipped))
            self.assertFalse(fn(Path(folder) / 'missing.hwpx'))


if __name__ == '__main__':
    unittest.main()
