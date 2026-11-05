import tempfile
import unittest
from pathlib import Path

from docfit_app.new_document_service import create_copy


class NewDocumentServiceTests(unittest.TestCase):
    def test_copy_is_new_and_source_is_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / '서식.hwpx'
            source.write_bytes(b'original template bytes')
            before = source.read_bytes()
            target = create_copy(source, root / 'Documents', '새 문서')
            self.assertEqual(target.read_bytes(), before)
            self.assertEqual(source.read_bytes(), before)
            self.assertNotEqual(target, source)

    def test_collision_gets_non_overwriting_name(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / '서식.hwpx'
            source.write_bytes(b'template')
            docs = root / 'Documents'
            docs.mkdir()
            first = docs / '새 문서.hwpx'
            first.write_bytes(b'existing user document')
            target = create_copy(source, docs, '새 문서')
            self.assertEqual(target.name, '새 문서 (2).hwpx')
            self.assertEqual(first.read_bytes(), b'existing user document')

    def test_rejects_non_hwpx_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'template.txt'
            source.write_text('x')
            with self.assertRaises(ValueError):
                create_copy(source, Path(folder) / 'Documents')


if __name__ == '__main__':
    unittest.main()
