from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import time
import struct
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from docfit_app.settings_service import SettingsService
from docfit_core.ai_answer import ai_answer_to_outline_text, looks_like_ai_answer
from docfit_core.pasted_text import clean_pasted_text
from docfit_core.fidelity.package import PackageSnapshot
from docfit_core.hwpx import HwpxLimits, HwpxSecurityError


class ContentPreservationTests(unittest.TestCase):
    def test_decimal_versions_are_not_numbered_lists(self):
        text = '1.74 버전을 사용합니다.\n2.50 금액입니다.'
        self.assertFalse(looks_like_ai_answer(text))
        result = ai_answer_to_outline_text(text)
        self.assertIn('1.74', result)
        self.assertIn('2.50', result)

    def test_real_numbered_parent_child_and_return(self):
        result = ai_answer_to_outline_text('1. 상위\n1.1 하위\n2. 상위 복귀')
        self.assertIn('□ 상위', result)
        self.assertIn('ㅇ 하위', result)
        self.assertIn('□ 상위 복귀', result)

    def test_code_indices_markup_and_html_are_preserved(self):
        self.assertEqual(clean_pasted_text('`items[1]`'), 'items[1]')
        self.assertEqual(clean_pasted_text('```python\nprint(". - x")\n```'), 'print(". - x")')
        result = ai_answer_to_outline_text('## 코드\n```python\nitems[1]\nx = 2**3**4\n<strong>내용</strong>\n```')
        for literal in ('items[1]', '2**3**4', '<strong>내용</strong>'):
            self.assertIn(literal, result)

    def test_formal_contact_sentence_is_preserved_by_default(self):
        sentence = '더 궁금하신 사항은 담당자에게 문의해 주세요.'
        text = '## 안내\n- 정비를 추진합니다.\n\n' + sentence
        self.assertIn(sentence, ai_answer_to_outline_text(text))
        self.assertNotIn(sentence, ai_answer_to_outline_text(text, strip_chat_frame=True))


class SettingsConcurrencyTests(unittest.TestCase):
    def test_independent_services_preserve_both_updates(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            path.write_text('{"base":true}', encoding='utf-8')
            services = [SettingsService(path), SettingsService(path)]
            barrier = Barrier(2)
            def write(index):
                barrier.wait(timeout=5)
                def change(settings):
                    time.sleep(0.02)
                    settings[str(index)] = True
                services[index].update(change)
            with ThreadPoolExecutor(2) as executor:
                list(executor.map(write, range(2)))
            self.assertEqual(services[0].read(), {'base': True, '0': True, '1': True})


class SnapshotLimitsTests(unittest.TestCase):
    def test_compression_ratio_is_rejected_at_snapshot_entry(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'compressed.zip'
            with ZipFile(path, 'w', ZIP_DEFLATED) as archive:
                archive.writestr('data', b'A' * (4 * 1024 * 1024))
            with self.assertRaises(HwpxSecurityError):
                PackageSnapshot.load(path)

    def test_declared_member_size_limit(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'large.zip'
            with ZipFile(path, 'w') as archive:
                archive.writestr('data', b'12345')
            with self.assertRaises(HwpxSecurityError):
                PackageSnapshot.load(path, limits=HwpxLimits(max_file_size=4))

    def test_forged_small_size_cannot_trigger_unbounded_inflate(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'forged.zip'
            with ZipFile(path, 'w', ZIP_DEFLATED) as archive:
                archive.writestr('data', b'A' * 4096)
            data = bytearray(path.read_bytes())
            central = data.index(b'PK\x01\x02')
            struct.pack_into('<I', data, 22, 1)
            struct.pack_into('<I', data, central + 24, 1)
            path.write_bytes(data)
            snapshot = PackageSnapshot.load(path)
            with self.assertRaises(HwpxSecurityError):
                snapshot.read('data')
