from docfit_core.semantic_units import staff_role_name_ranges
import unittest
from pathlib import Path
import runpy
import tests.test_deung_word_unit as helpers


class StaffWordUnitTests(unittest.TestCase):
    split_at = helpers.DeungWordUnitTest.split_at

    @classmethod
    def setUpClass(cls):
        cls.ns = runpy.run_path(str(Path(__file__).parents[1] / 'hwp-auto-docfit.py'))

    def test_all_interior_splits_are_one_unit(self):
        for unit in ('과(동)장: 홍길동', '팀장: 이순신', '주무관: 홍당무', '팀장 : ○○○'):
            text = '▣ 담당: ' + unit + ', ☎ 02-3153-0000'
            offset = text.index(unit)
            for split in range(offset + 1, offset + len(unit)):
                with self.subTest(unit=unit, split=split):
                    self.assertEqual(self.split_at(text[:split] + '|' + text[split:], text), unit)

    def test_commas_and_phone_are_not_merged(self):
        text = '팀장: 이순신, 주무관: 홍당무 (☎ 02-3153-0000)'
        self.assertEqual([text[a:b] for a, b in staff_role_name_ranges(text)],
                         ['팀장: 이순신', '주무관: 홍당무'])
        self.assertEqual(staff_role_name_ranges('장소: 서울, 처리부서: 공원녹지과'), [])
        self.assertIsNone(self.split_at('팀장: 이순신, |주무관: 홍당무 (☎ 02-3153-0000)', text))
